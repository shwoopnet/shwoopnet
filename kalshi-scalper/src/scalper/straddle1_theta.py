"""STRADDLE1 ThetaData fetch: end of day bid/ask of the ATM straddle at the entry and exit closes. Infrastructure only.

Tested with mocks (tests/test_straddle1_theta.py); NEVER run against the live service here: it needs the owner's key.
Written against `thetadata` 1.0.17 (pip install thetadata; Python >= 3.12; gRPC to mdds-01.thetadata.us:443), calls read
from thetadata/client.py: ThetaClient(api_key=|email=,password=|creds_file=), option_list_expirations(symbol),
option_list_strikes(symbol, expiration), option_history_eod(start_date, end_date, symbol, expiration, strike, right).
Credential: env THETADATA_API_KEY, else THETADATA_EMAIL + THETADATA_PASSWORD. Never printed or logged by this file.
UNVERIFIED until a real key exists (no login was attempted): the exact EOD column names. v3 documents bid, ask, close,
created plus symbol/expiration/strike/right; `_pick` matches case-insensitively and raises ThetaShapeError naming the
columns it saw, so a mismatch fails loudly with the real header list (no secret in it). Free tier: EOD from 2023-06-01,
1 day delay, 30 requests/minute: `RATE_SLEEP` keeps under it. Per event: 2 list calls + 1 EOD call (entry..exit, both
legs, one strike) = 3 requests.
"""
import datetime as dt
import os
import time

RATE_SLEEP = 2.2  # seconds between requests: under 30 a minute
FIELD_ALIASES = {"bid": ("bid",), "ask": ("ask",), "date": ("created", "date", "timestamp", "trade_date"),
                 "right": ("right",), "strike": ("strike",), "expiration": ("expiration", "expiry")}


class ThetaCredentialError(RuntimeError):
    pass


class ThetaShapeError(RuntimeError):
    pass


def make_client(env=None, client_factory=None):
    """Build a ThetaClient from the environment, or raise ThetaCredentialError saying which variables to set."""
    env = os.environ if env is None else env
    key = env.get("THETADATA_API_KEY")
    email, pw = env.get("THETADATA_EMAIL"), env.get("THETADATA_PASSWORD")
    if not key and not (email and pw):
        raise ThetaCredentialError("No ThetaData credential: set THETADATA_API_KEY, or both THETADATA_EMAIL and "
                                   "THETADATA_PASSWORD, as Claude environment secrets (never in chat or a file).")
    if client_factory is None:
        from thetadata import ThetaClient  # imported late so tests and the event list need no package
        client_factory = lambda **kw: ThetaClient(dataframe_type="pandas", **kw)
    return client_factory(api_key=key) if key else client_factory(email=email, password=pw)


def rows(df):
    """DataFrame (pandas or polars) or list of dicts -> list of dicts with lower-case keys."""
    if hasattr(df, "to_dicts"):
        r = df.to_dicts()
    elif hasattr(df, "to_dict"):
        r = df.to_dict("records")
    else:
        r = list(df)
    return [{str(k).lower(): v for k, v in x.items()} for x in r]


def _pick(row, field):
    for a in FIELD_ALIASES[field]:
        if a in row:
            return row[a]
    raise ThetaShapeError(f"column for {field!r} not found; saw {sorted(row)}")


def _date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v)[:10])


def third_friday(d):
    first = d.replace(day=1)
    f = first + dt.timedelta(days=(4 - first.weekday()) % 7)
    return f + dt.timedelta(days=14)


def is_monthly(exp):
    """Standard monthly: third Friday, or the Thursday before when that Friday is an exchange holiday (Good Friday)."""
    tf = third_friday(exp)
    return exp == tf or exp == tf - dt.timedelta(days=1)


def choose_expiration(expirations, exit_date, min_days=7, monthly_only=False):
    c = sorted(e for e in (_date(x) for x in expirations) if (e - exit_date).days >= min_days)
    if monthly_only:
        c = [e for e in c if is_monthly(e)]
    return c[0] if c else None


def choose_strike(strikes, underlying_close):
    s = [float(x) for x in strikes]
    return min(s, key=lambda k: (abs(k - underlying_close), k)) if s else None


def fetch_straddle(symbol, entry_date, exit_date, underlying_close, client=None, min_days=7, monthly_only=False, sleep=time.sleep):
    """Return dict(expiration, strike, entry={call_bid,call_ask,put_bid,put_ask}, exit={...}) or a dict with 'skip' reason.
    entry_date / exit_date are the closes; underlying_close is the entry-close stock price used to pick the strike.
    Fills are NOT applied here: the registered rule (buy ask, sell bid, fee) lives in straddle1.event_return."""
    client = client or make_client()
    sleep(RATE_SLEEP)
    exps = [_pick(r, "expiration") for r in rows(client.option_list_expirations(symbol))]
    exp = choose_expiration(exps, exit_date, min_days, monthly_only)
    if exp is None:
        return {"skip": "no expiration"}
    sleep(RATE_SLEEP)
    strike = choose_strike([_pick(r, "strike") for r in rows(client.option_list_strikes(symbol, exp))], underlying_close)
    if strike is None:
        return {"skip": "no strikes"}
    sleep(RATE_SLEEP)
    data = rows(client.option_history_eod(entry_date, exit_date, symbol, exp, strike=str(strike), right="both"))
    got = {}
    for r in data:
        d, side = _date(_pick(r, "date")), str(_pick(r, "right")).lower()[:1]
        if side in ("c", "p") and d in (entry_date, exit_date):
            got[(d, side)] = (float(_pick(r, "bid")), float(_pick(r, "ask")))
    out = {"expiration": exp.isoformat(), "strike": strike}
    for tag, d in (("entry", entry_date), ("exit", exit_date)):
        if (d, "c") not in got or (d, "p") not in got:
            return {"skip": f"missing {tag} quote", "expiration": exp.isoformat(), "strike": strike}
        (cb, ca), (pb, pa) = got[(d, "c")], got[(d, "p")]
        out[tag] = dict(call_bid=cb, call_ask=ca, put_bid=pb, put_ask=pa)
    return out
