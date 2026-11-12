"""REMATCH shared helpers. Committed Nov 12, 2026, before any e-soccer list or candle was pulled.
Constants are the registered ones (REMATCH_REGISTRATION.md with Amendments 1 and 2)."""
import gzip
import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
SERIES = "KXESOCCERGAME"
GAP_MIN_S, GAP_MAX_S = 20 * 60, 120 * 60      # later scheduled start minus earlier scheduled start
A_CLOSE_PLUS_S = 300                          # the earlier match's close plus this must be at or before the decision minute
BEFORE_S = 2 * 60                             # reference minute: candle ending at A's S minus 2 minutes (in B's market)
DECISION_S = 6 * 60                           # decision minute: candle ending at B's S minus 6 minutes
ENTRY_S = 5 * 60                              # entry: close of the candle ending at B's S minus 5 minutes
FALL, QUIET = 0.05, 0.02
ASK_BAND, SPREAD_MAX, SLIP = (0.20, 0.80), 0.04, 0.01
COST_KILL_ONE_WAY = 0.04
STAGE1_FROM, STAGE1_BEFORE = "2026-10-15T00:00:00Z", "2026-10-23T00:00:00Z"
HELDOUT_FROM = "2026-10-23T00:00:00Z"
DEV_DAYS = 41                                 # development window, 2026-09-12 to before 2026-10-23
LABEL = "candle freshness measured on Bitcoin 15 minute only, not on sports"


def ts(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def start_from_ticker(event_ticker):
    """Scheduled start from the ticker clock, read as US Eastern. None if the key has no clock."""
    m = re.match(r"(\d{2})([A-Z]{3})(\d{2})(\d{2})(\d{2})", event_ticker.split("-", 1)[1] if "-" in event_ticker else "")
    if not m or m.group(2) not in MON:
        return None
    yy, mon, dd, hh, mi = m.groups()
    try:
        return int(datetime(2000 + int(yy), MON[mon], int(dd), int(hh), int(mi), tzinfo=ET).timestamp())
    except ValueError:
        return None


CARRY_S = 5 * 60                              # a missing candle: the last present candle at or before the instant, no more than this much earlier
DROPS = {"not_two_team_codes": 0, "no_ticker_clock": 0, "market_without_close_time": 0}   # filled by read_events, printed by the reader


def refuse_heldout(path):
    """Standing rule (h): a folder whose real path has a part starting HELDOUT_ is refused unless REMATCH_HELDOUT=READ-ONCE is set
    for the one approved read. The real path is tested, so a link with an innocent name does not get past."""
    real = os.path.realpath(path)
    if any(part.upper().startswith("HELDOUT_") for part in real.split(os.sep)) and os.environ.get("REMATCH_HELDOUT") != "READ-ONCE":
        raise SystemExit("REFUSED: %s resolves into a HELDOUT_ folder (standing rule (h))" % path)


def quote_at(q, t):
    """The quote standing at instant t: the candle ending exactly at t, else the last present candle ending at or before t and
    no more than CARRY_S earlier. Never a later candle. Returns (quote or None, 'exact' | 'carried' | 'none')."""
    if t in q:
        return q[t], "exact"
    for back in range(60, CARRY_S + 1, 60):
        if t - back in q:
            return q[t - back], "carried"
    return None, "none"


def read_events(run):
    """Events of the series from a lists run: tickers, close times and the raw market rows (results are NOT looked at here)."""
    refuse_heldout(run)
    for k in DROPS:
        DROPS[k] = 0
    man = json.load(open(os.path.join(run, "manifest.json")))
    events = {}
    for row in man.get("rows", []):
        if row.get("status") != 200 or row.get("params", {}).get("series_ticker") != SERIES:
            continue
        body = json.load(gzip.open(os.path.join(run, row["file"]), "rt"))
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            ev, tk = m.get("event_ticker", ""), m.get("ticker", "")
            if not ev.startswith(SERIES + "-") or not tk.startswith(ev + "-"):
                continue
            e = events.setdefault(ev, {"event": ev, "markets": {}})
            e["markets"][tk[len(ev) + 1:]] = m
    out = []
    for e in events.values():
        codes = sorted(c for c in e["markets"] if c != "TIE")
        s = start_from_ticker(e["event"])
        closes = []
        for m in e["markets"].values():
            try:
                closes.append(ts(m["close_time"]))
            except (KeyError, ValueError, TypeError, AttributeError):
                pass
        if len(codes) != 2:
            DROPS["not_two_team_codes"] += 1
            continue
        if s is None:
            DROPS["no_ticker_clock"] += 1
            continue
        if len(closes) != len(e["markets"]):
            DROPS["market_without_close_time"] += 1
            continue
        out.append({"event": e["event"], "codes": codes, "S": s, "close": max(closes), "markets": e["markets"]})
    return out


def pairs_by_schedule(events):
    """(A, B): B is the NEXT meeting of the same two codes after A, B's scheduled start 20 to 120 minutes after A's.
    Uses scheduled starts only."""
    by = {}
    for e in events:
        by.setdefault(tuple(e["codes"]), []).append(e)
    pairs = []
    for rs in by.values():
        rs.sort(key=lambda r: (r["S"], r["event"]))
        for a, b in zip(rs, rs[1:]):
            if GAP_MIN_S <= b["S"] - a["S"] <= GAP_MAX_S:
                pairs.append((a, b))
    pairs.sort(key=lambda p: (p[1]["S"], p[1]["event"]))
    return pairs


def fee(price):
    """0.07 x p x (1 - p), rounded UP to the next whole cent, one contract."""
    import math
    return math.ceil(0.07 * price * (1 - price) * 100 - 1e-9) / 100.0
