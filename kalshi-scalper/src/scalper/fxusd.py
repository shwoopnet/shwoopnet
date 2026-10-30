"""FXUSD: one US dollar factor across five Kalshi FX 15 minute series (workers/FXUSD_REGISTRATION.md).

Usage (from kalshi-scalper/, PYTHONPATH=src):
  python -m scalper.fxusd counts   calendar counts only; never reads a result or a price
  python -m scalper.fxusd fetch    1 minute candles for the five series (public, no key) -> data/fxusd/candles.sqlite
  python -m scalper.fxusd score [--holdout]   the registered read (run once)
Market listings come from data/newh15/mk_<SERIES>.json (NEWH15 inventory step).
"""
from __future__ import annotations

import json
import math
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
LON = ZoneInfo("Europe/London")
UTC = timezone.utc
DB = "data/fxusd/candles.sqlite"
PAIRS = {  # pair: side of the Kalshi market that wins when the USD RISES against the foreign currency
    "EURUSD": "no", "GBPUSD": "no", "AUDUSD": "no",   # USD is the quote currency: USD up = pair down
    "USDJPY": "yes", "USDCAD": "yes",                 # USD is the base currency: USD up = pair up
}
LO, HI = 0.20, 0.80
Z_BAR = 5.27
N_PREV = 728662


def load_windows():
    w = []
    for p, up in PAIRS.items():
        for m in json.load(open(f"data/newh15/mk_KX{p}15M.json")):
            o = int(datetime.fromisoformat(m["open_time"].replace("Z", "+00:00")).timestamp())
            c = int(datetime.fromisoformat(m["close_time"].replace("Z", "+00:00")).timestamp())
            ev = m.get("expiration_value")
            k = m.get("floor_strike")
            tie = ev is not None and k is not None and abs(float(ev) - float(k)) < 1e-12
            w.append(dict(pair=p, ticker=m["ticker"], open=o, close=c, result=m["result"], tie=tie,
                          up_side=up, cdate=datetime.fromtimestamp(o, UTC).astimezone(CT).strftime("%Y-%m-%d")))
    w.sort(key=lambda x: (x["open"], x["pair"]))
    return w


def tag_moments(w):
    """Calendar facts only (chosen before any data): returns a list of moment names per window."""
    by = defaultdict(list)
    for x in w:
        by[x["pair"]].append(x)
    for p, lst in by.items():
        lst.sort(key=lambda x: x["open"])
        prev_close = None
        for i, x in enumerate(lst):
            x["moments"] = []
            lt = datetime.fromtimestamp(x["open"], UTC).astimezone(CT)
            # (a) FIX_PRE: the window that closes at 16:00 London (the WM/Reuters 4 PM fix print), Mon to Fri London
            fl = datetime.fromtimestamp(x["close"], UTC).astimezone(LON)
            if fl.hour == 16 and fl.minute == 0 and fl.weekday() < 5:
                x["moments"].append("FIX_PRE")
                x["fix_regime"] = "UKUS_MISMATCH" if (LON.utcoffset(fl) != timedelta(hours=1)) != (CT.utcoffset(lt) != timedelta(hours=-5)) else "ALIGNED"
            # (b) RELEASE: windows starting 7:30 and 8:00 Central on Mon to Fri (8:30 Eastern release at the first)
            if lt.weekday() < 5 and lt.hour == 7 and lt.minute == 30:
                x["moments"].append("REL_0730")
            if lt.weekday() < 5 and lt.hour == 8 and lt.minute == 0:
                x["moments"].append("REL_0800")
            # (c) WEEK_OPEN: first window after a gap of 12 hours or more in the listing (not the first window of the history)
            if prev_close is not None and x["open"] - prev_close >= 12 * 3600:
                x["moments"].append("WEEK_OPEN")
            prev_close = x["close"]
    return w


def split_days(w):
    days = sorted({x["cdate"] for x in w})
    n = len(days)
    a, b = int(round(0.6 * n)), int(round(0.8 * n))
    sp = {}
    for i, d in enumerate(days):
        sp[d] = "disc" if i < a else ("val" if i < b else "hold")
    return days, sp


def fee(p, c=10, m=1.0):
    return math.ceil(round(0.07 * c * p * (1 - p) * m * 100, 9)) / 100


def pf(v):
    g = sum(x for x in v if x > 0)
    l = -sum(x for x in v if x < 0)
    return float("inf") if l == 0 and g > 0 else (g / l if l else float("nan"))


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 2
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def cmd_counts():
    w = tag_moments(load_windows())
    days, sp = split_days(w)
    print("windows", len(w), Counter(x["pair"] for x in w))
    print("days", len(days), days[0], days[-1])
    for s in ("disc", "val", "hold"):
        ds = [d for d in days if sp[d] == s]
        print(s, ds[0], ds[-1], len(ds), "days")
    for m in ("FIX_PRE", "REL_0730", "REL_0800", "WEEK_OPEN"):
        sel = [x for x in w if m in x["moments"]]
        print(m, "windows", len(sel), dict(Counter(sp[x["cdate"]] for x in sel)), dict(Counter(x["pair"] for x in sel)))
        if m == "FIX_PRE":
            print("  regime", dict(Counter(x["fix_regime"] for x in sel)))
            print("  fix open (CT) by regime:", sorted({(x["fix_regime"], datetime.fromtimestamp(x["open"], UTC).astimezone(CT).strftime("%H:%M")) for x in sel}))
    print("all-pair weekday dates in FIX_PRE with CT times:", sorted({datetime.fromtimestamp(x['open'], UTC).astimezone(CT).strftime('%m-%d %H:%M') for x in w if 'FIX_PRE' in x['moments']})[:60])
    wk = sorted({datetime.fromtimestamp(x['open'], UTC).astimezone(CT).strftime('%a %m-%d %H:%M') for x in w if 'WEEK_OPEN' in x['moments']})
    print("WEEK_OPEN starts (CT):", wk)


def cmd_fetch():
    from . import newh15_fetch as nf
    nf.DB = DB
    nf.run  # noqa
    for p in PAIRS:
        nf.run(f"KX{p}15M")


def candle_map():
    c = sqlite3.connect(DB)
    d = {}
    for tk, end, bo, ao, vol in c.execute("select ticker,end_ts,bid_o,ask_o,volume from candle"):
        d[(tk, end)] = (bo, ao, vol)
    return d


def fill_for(x, side, cm):
    k = cm.get((x["ticker"], x["open"] + 120))
    if not k:
        return None, "no_candle"
    bo, ao, vol = k
    if side == "yes":
        p = ao
    else:
        p = None if bo is None else round(1 - bo, 6)
    if p is None:
        return None, "no_quote"
    if not (LO <= p <= HI):
        return None, "price_band"
    return (p, vol), "ok"


def trades_for(sel, side_of, cm):
    tr, why = [], Counter()
    for x in sel:
        side = side_of(x)
        f, st = fill_for(x, side, cm)
        why[st] += 1
        if f is None:
            continue
        tr.append(dict(x, side=side, fill=f[0], vol=f[1], won=(x["result"] == side)))
    return tr, why


def net(t, c=10, m=1.0):
    return c * ((1.0 if t["won"] else 0.0) - t["fill"]) - fee(t["fill"], c, m)


def dayz(tr):
    d = defaultdict(float)
    for t in tr:
        d[t["cdate"]] += net(t)
    v = list(d.values())
    if len(v) < 3:
        return float("nan")
    sd = statistics.stdev(v)
    return statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else float("nan")


def usd_up(x):
    """Did the USD rise against the foreign currency in this window? Ties settle YES, so for the
    USD-quote pairs a tie reads 'USD not up' and for the USD-base pairs a tie reads 'USD up'
    (as Kalshi settles). Strict version excludes ties."""
    return x["result"] == x["up_side"]


def report_look(name, sel, sp, out):
    out.append(f"\n### {name}")
    for s in ("disc", "val", "hold", "all"):
        if s == "hold" and "--holdout" not in sys.argv:
            continue
        r = [x for x in sel if s == "all" or sp[x["cdate"]] == s]
        if s == "all" and "--holdout" not in sys.argv:
            r = [x for x in sel if sp[x["cdate"]] in ("disc", "val")]
        n = len(r)
        nt = [x for x in r if not x["tie"]]
        up = sum(1 for x in nt if usd_up(x))
        upall = sum(1 for x in r if usd_up(x))
        lo, hi = wilson(up, len(nt))
        out.append(f"- {s if not(s=='all' and '--holdout' not in sys.argv) else 'disc+val'}: n {n}, ties {n-len(nt)} ({(n-len(nt))/n:.1%} )," if n else f"- {s}: n 0")
        if n:
            out[-1] += (f" USD-up share (ties out) {up/len(nt):.3f} [{lo:.3f},{hi:.3f}] n {len(nt)};"
                        f" as settled (ties as Kalshi) {upall/n:.3f}")


def report_trades(name, sel, side_of, sp, cm, out):
    out.append(f"\n### {name} trades (buy the registered side at the next candle's ask, C = 10, 20c to 80c)")
    res = {}
    for s in ("disc", "val", "hold"):
        if s == "hold" and "--holdout" not in sys.argv:
            continue
        r = [x for x in sel if sp[x["cdate"]] == s]
        tr, why = trades_for(r, side_of, cm)
        v10 = [net(t) for t in tr]
        v12 = [net(t, 10, 1.2) for t in tr]
        v1 = [net(t, 1) for t in tr]
        wr = sum(t["won"] for t in tr) / len(tr) if tr else float("nan")
        tv = [t for t in tr if (t["vol"] or 0) > 0]
        pfv = pf([net(t) for t in tv]) if tv else float("nan")
        res[s] = (len(tr), pf(v10) if tr else float("nan"))
        out.append(f"- {s}: windows {len(r)}, trades {len(tr)} (skipped {dict(why)}), hit {wr:.3f}, mean fill {statistics.mean(t['fill'] for t in tr) if tr else float('nan'):.3f},"
                   f" PF C10 {pf(v10) if tr else float('nan'):.2f}, PF x1.2 {pf(v12) if tr else float('nan'):.2f}, PF C1 {pf(v1) if tr else float('nan'):.2f},"
                   f" net C10 ${sum(v10):.2f}, day z {dayz(tr):.2f}; volume>0 candles only: n {len(tv)} PF {pfv:.2f}")
    return res


def cmd_score():
    w = tag_moments(load_windows())
    days, sp = split_days(w)
    cm = candle_map()
    out = ["# FXUSD scoring output (generated by src/scalper/fxusd.py score)\n"]
    allh = "--holdout" in sys.argv
    out.append(f"holdout read: {allh}")
    base = [x for x in w if not x["moments"]]
    report_look("BASELINE (windows in no registered moment): USD drift of the sample", base, sp, out)
    fix = [x for x in w if "FIX_PRE" in x["moments"]]
    report_look("A FIX_PRE (window closing at the 4 PM London fix)", fix, sp, out)
    for r in ("ALIGNED", "UKUS_MISMATCH"):
        report_look(f"A FIX_PRE regime {r}", [x for x in fix if x["fix_regime"] == r], sp, out)
    resA = report_trades("A FIX_PRE buy USD-up", fix, lambda x: x["up_side"], sp, cm, out)
    for m in ("REL_0730", "REL_0800", "WEEK_OPEN"):
        report_look(f"{m} (count only, no trade)", [x for x in w if m in x["moments"]], sp, out)
    # information: which side the registered USD-up bet would be per pair (tie handicap)
    print("\n".join(out))


if __name__ == "__main__":
    {"counts": cmd_counts, "fetch": cmd_fetch, "score": cmd_score}[sys.argv[1]]()
