"""COUNT2: Kalshi KXTORNADO monthly tornado-count thresholds against SPC daily storm reports (see workers/COUNT2_REGISTRATION.md).
Usage: python -m scalper.count2 spc | calib | fetch | run   (cache outside the repo; frozen-third months and candles are never fetched)."""
from __future__ import annotations
import json, math, os, sys, time, calendar
import urllib.request, urllib.error
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from . import api
from .candlefield import quote_close

ET = ZoneInfo("America/New_York")
CACHE = Path(os.environ.get("COUNT2_CACHE", "/tmp/count2_cache")); CACHE.mkdir(parents=True, exist_ok=True)
SPC_DIR = CACHE / "spc"; SPC_DIR.mkdir(parents=True, exist_ok=True)
RATIO, HARD, LOW, MAXPER = 3.0, 0.30, 0.03, 2
CLIM_YEARS = range(2015, 2023)
SPC = "https://www.spc.noaa.gov/climo/reports/%s_rpts.csv"


def fee(p, C=10):
    return math.ceil(round(0.07 * C * p * (1 - p) * 100, 9)) / 100 / C


def nb_pmf(mu, r, kmax):
    if mu <= 1e-12:
        return [1.0] + [0.0] * kmax
    p = r / (r + mu)
    return [math.exp(math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1) + r * math.log(p) + k * math.log1p(-p)) for k in range(kmax + 1)]


def parse_tornado_rows(text):
    """Number of rows in the tornado section (after the 'Time,F_Scale' header, before the next 'Time,' header)."""
    n, on = 0, False
    for ln in text.splitlines():
        if ln.startswith("Time,"):
            on = ln.startswith("Time,F")
            continue
        if on and ln.strip():
            n += 1
    return n


def strike_of(m):
    """floor_strike; six KXTORNADO-25JAN markets have none, so the number after 'above' in rules_primary is used (implementation detail)."""
    if m.get("floor_strike") is not None: return m["floor_strike"]
    import re
    return float(re.search(r"above ([\d.]+)", m["rules_primary"]).group(1))


def strike_prob(m, c, pmf):
    lo = strike_of(m)
    return sum(q for k, q in enumerate(pmf) if c + k > lo)


def month_bounds(y, mo):
    a = datetime(y, mo, 1, tzinfo=ET)
    b = datetime(y + (mo == 12), mo % 12 + 1, 1, tzinfo=ET)
    return a.astimezone(timezone.utc), b.astimezone(timezone.utc)


def look_of(y, mo):
    a, b = month_bounds(y, mo)
    return a + (b - a) / 2


def usable(d, look):
    """File date d is usable when d + 2 days at 00:00 ET is at or before the look."""
    return datetime(d.year, d.month, d.day + 0, tzinfo=ET).replace(tzinfo=None) + timedelta(days=2) <= look.astimezone(ET).replace(tzinfo=None)


def spc_count(d):
    p = SPC_DIR / (d.strftime("%y%m%d") + ".json")
    if p.exists():
        return json.loads(p.read_text())
    for i in range(6):
        try:
            req = urllib.request.Request(SPC % d.strftime("%y%m%d"), headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                v = {"n": parse_tornado_rows(r.read().decode("latin-1")), "missing": False}
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                v = {"n": 0, "missing": True}; break
            time.sleep(3 * (i + 1))
        except Exception:
            time.sleep(3 * (i + 1))
    else:
        raise RuntimeError("SPC fetch failed " + str(d))
    p.write_text(json.dumps(v)); time.sleep(0.2)
    return v


def daily(d):
    return spc_count(d)["n"]


def climatology(excl_year=None):
    """mean tornado rows per file date for each calendar month over CLIM_YEARS (optionally leaving a year out)."""
    out = {}
    for mo in range(1, 13):
        tot = days = 0
        for y in CLIM_YEARS:
            if y == excl_year: continue
            for dd in range(1, calendar.monthrange(y, mo)[1] + 1):
                tot += daily(date(y, mo, dd)); days += 1
        out[mo] = tot / days
    return out


def month_state(y, mo):
    """(c, n_rem, trail) at the midpoint look from SPC files."""
    look = look_of(y, mo)
    nd = calendar.monthrange(y, mo)[1]
    c = k = 0
    for dd in range(1, nd + 1):
        d = date(y, mo, dd)
        if usable(d, look): c += daily(d); k += 1
    last = date(y, mo, max(k, 1)) if k else date(y, mo, 1) - timedelta(days=1)
    vals = [daily(last - timedelta(days=i)) for i in range(14)]
    return look, c, nd - k, sum(vals) / 14.0


def model(y, mo, clim, r):
    look, c, nrem, trail = month_state(y, mo)
    rate = 0.5 * trail + 0.5 * clim[mo]
    mu = nrem * rate
    return look, c, mu, nb_pmf(mu, r, int(mu * 8 + 200))


def month_total(y, mo):
    return sum(daily(date(y, mo, dd)) for dd in range(1, calendar.monthrange(y, mo)[1] + 1))


def calib_r():
    num = den = 0.0; rows = []
    for y in CLIM_YEARS:
        clim = climatology(excl_year=y)
        for mo in range(1, 13):
            look, c, nrem, trail = month_state(y, mo)
            mu = nrem * (0.5 * trail + 0.5 * clim[mo])
            R = month_total(y, mo) - c
            num += mu * mu; den += (R - mu) ** 2 - mu; rows.append((y, mo, round(mu, 1), R))
    r = num / den if den > 0 else 20.0
    return min(20.0, max(0.5, r)), rows


def event_period(L):
    t = min(m["close_time"] for m in L)       # 03:59Z / 04:59Z on the 1st after the month
    dt = datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(ET) - timedelta(minutes=5)
    return dt.year, dt.month


def split_events(markets):
    ev = {}
    for m in markets: ev.setdefault(m["event_ticker"], []).append(m)
    keyed = sorted(((event_period(L), e, L) for e, L in ev.items()), key=lambda x: x[0])
    k = (2 * len(keyed)) // 3
    return keyed[:k], keyed[k:]


def load_markets():
    return json.loads((CACHE / "c_KXTORNADO.json").read_text())


def cmd_spc():
    dev, hold = split_events(load_markets())
    for (y, mo), e, L in dev:
        for dd in range(1, calendar.monthrange(y, mo)[1] + 1): spc_count(date(y, mo, dd))
        for i in range(1, 15): spc_count(date(y, mo, 1) - timedelta(days=i))
    for y in CLIM_YEARS:
        for mo in range(1, 13):
            for dd in range(1, calendar.monthrange(y, mo)[1] + 1): spc_count(date(y, mo, dd))
        print("spc", y, flush=True)
    for i in range(1, 15): spc_count(date(2015, 1, 1) - timedelta(days=i))
    print("spc done", len(dev), "dev", len(hold), "frozen unread", flush=True)


def cmd_calib():
    out = CACHE / "count2_r.json"
    if out.exists(): print("exists", out.read_text()); return
    r, rows = calib_r()
    out.write_text(json.dumps({"r": r, "rows": rows})); print("r =", r)


def cmd_fetch():
    dev, hold = split_events(load_markets())
    cp = CACHE / "candles_tornado.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    for (y, mo), e, L in dev:
        look = look_of(y, mo)
        if any(datetime.fromisoformat(m["open_time"].replace("Z", "+00:00")) > look - timedelta(minutes=60) for m in L):
            continue
        for m in L:
            tk = m["ticker"]
            if tk in have: continue
            src = "/historical/markets/%s/candlesticks" % tk if m["close_time"] < "2026-09-04" else "/series/KXTORNADO/markets/%s/candlesticks" % tk
            a, b = int((look - timedelta(minutes=60)).timestamp()), int((look + timedelta(minutes=15)).timestamp())
            try:
                d = api._get(src, {"start_ts": a, "end_ts": b, "period_interval": 1})
                have[tk] = [(c["end_period_ts"], quote_close(c.get("yes_ask")), quote_close(c.get("yes_bid"))) for c in d.get("candlesticks", [])]
            except Exception:
                have[tk] = None
            time.sleep(0.5)
        cp.write_text(json.dumps(have)); print("fetched", e, flush=True)
    print("fetched all", flush=True)


def fills(cand, look, side):
    """(signal ask, fill ask) of a side ('yes'/'no') or None."""
    lt = int(look.timestamp())
    def ask(c):
        if side == "yes": return c[1]
        return None if c[2] is None else round(1 - c[2], 4)
    sig = [ask(c) for c in cand if c[0] <= lt and ask(c) is not None and lt - c[0] <= 3600]
    fil = [ask(c) for c in cand if lt < c[0] <= lt + 900 and ask(c) is not None]
    if not sig or not fil: return None
    return sig[-1], fil[0]


def select(rows):
    """rows: [(key, p_model, ask)] -> up to MAXPER by p/ask meeting the rule."""
    ok = [r for r in rows if LOW <= r[2] <= HARD and r[1] >= RATIO * r[2]]
    ok.sort(key=lambda r: -r[1] / r[2])
    return ok[:MAXPER]


def stats(ts):
    if not ts: return {"n": 0}
    w = [x for x in ts if x > 0]; l = [-x for x in ts if x <= 0]
    return {"n": len(ts), "mean": sum(ts) / len(ts), "win": len(w) / len(ts), "pf": (sum(w) / sum(l)) if l else None}


def cmd_run(r_mult=1.0):
    out = CACHE / "count2_result.json"
    if out.exists() and not os.environ.get("COUNT2_RERUN"):
        print("Refusing to run again:", out); return
    r = json.loads((CACHE / "count2_r.json").read_text())["r"]
    cand = json.loads((CACHE / "candles_tornado.json").read_text())
    dev, hold = split_events(load_markets()); clim = climatology()
    trades, ctrl, srcall, srcexact = [], [], [], []
    notopen = skip = 0; scored = 0; sens = {}
    for mult in (0.5, 1.0, 2.0):
        sens[mult] = []
    for idx, ((y, mo), e, L) in enumerate(dev):
        half = 0 if idx < len(dev) // 2 else 1
        look = look_of(y, mo)
        tot = month_total(y, mo)
        ok_all = all((m["result"] == "yes") == (tot > strike_of(m)) for m in L if m["result"] in ("yes", "no"))
        srcall.append(ok_all)
        yes = sorted(strike_of(m) for m in L if m["result"] == "yes")
        no = sorted(strike_of(m) for m in L if m["result"] == "no")
        srcexact.append(bool(yes or no) and (not yes or tot > max(yes)) and (not no or tot <= min(no)))
        if any(datetime.fromisoformat(m["open_time"].replace("Z", "+00:00")) > look - timedelta(minutes=60) for m in L):
            notopen += 1; continue
        scored += 1
        for mult in (0.5, 1.0, 2.0):
            _, c, mu, pmf = model(y, mo, clim, r * mult)
            rows = []
            for m in L:
                for side in ("yes", "no"):
                    q = fills(cand.get(m["ticker"]) or [], look, side)
                    if not q: skip += 1; continue
                    pm = strike_prob(m, c, pmf); pm = pm if side == "yes" else 1 - pm
                    pay = 1.0 if (m["result"] == "yes") == (side == "yes") else 0.0
                    rows.append(((m["ticker"], side), pm, q[1], pay))
                    if mult == 1.0 and LOW <= q[1] <= HARD: ctrl.append((half, pay - q[1] - fee(q[1])))
            sel = select([(x[0], x[1], x[2]) for x in rows])
            for key, pm, ask in sel:
                pay = [x[3] for x in rows if x[0] == key][0]
                v = (half, pay - ask - fee(ask), key, pm, ask)
                sens[mult].append(v)
                if mult == 1.0: trades.append(v)
    res = {"r": r, "dev_events": len(dev), "frozen_events": len(hold), "scored_events": scored, "markets_not_open_at_look": notopen, "skipped_sides": skip,
           "rule": stats([x[1] for x in trades]), "rule_h1": stats([x[1] for x in trades if x[0] == 0]), "rule_h2": stats([x[1] for x in trades if x[0] == 1]),
           "control": stats([x[1] for x in ctrl]), "control_h1": stats([x[1] for x in ctrl if x[0] == 0]), "control_h2": stats([x[1] for x in ctrl if x[0] == 1]),
           "source_consistent_all_markets": sum(srcall) / len(srcall), "source_exact_bracket": sum(srcexact) / len(srcexact), "source_n": len(srcall),
           "mean_model_p": (sum(x[3] for x in trades) / len(trades)) if trades else None, "mean_ask": (sum(x[4] for x in trades) / len(trades)) if trades else None,
           "sens_n": {str(k): len(v) for k, v in sens.items()}, "sens_mean": {str(k): (sum(x[1] for x in v) / len(v) if v else None) for k, v in sens.items()},
           "trades": [(x[2], round(x[3], 3), x[4], round(x[1], 3)) for x in trades]}
    out.write_text(json.dumps(res)); print(json.dumps({k: v for k, v in res.items() if k != "trades"}, indent=1)); print(res["trades"])


if __name__ == "__main__":
    {"spc": cmd_spc, "calib": cmd_calib, "fetch": cmd_fetch, "run": cmd_run}[sys.argv[1]]()
