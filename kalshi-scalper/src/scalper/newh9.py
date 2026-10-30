"""NEWH9: four new mechanisms on Kalshi's gold and Bitcoin 15 minute markets and their hourly ladders (research only).

Registration: workers/NEWH9_REGISTRATION.md (pushed before any scoring).

    PYTHONPATH=src python -m scalper.newh9 counts    (windows and events loaded per stage; no quote after a signal, no result)
    PYTHONPATH=src python -m scalper.newh9 dv        (discovery and validation, scored once)
    PYTHONPATH=src python -m scalper.newh9 holdout   (the frozen holdout, read once, only for rules that passed discovery and validation)

Tries (6): LADLOCK btc, LADLOCK gold, LADLEAN btc, ASIAGOLD, NYGOLD, BTC10AM.
"""
from __future__ import annotations

import math
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from statistics import NormalDist

from .paths import DATA_DIR
from . import newh8

GOLD, BTC = "KXGOLD15M", "KXBTC15M"
FILES15 = {BTC: ("l1b", "book", "fresh"), GOLD: ("l1b", "book", "fresh", "five")}


def _ts(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


START = _ts(2026, 8, 6)
DISC_END = _ts(2026, 9, 21)
VAL_END = _ts(2026, 10, 18)
END = _ts(2026, 10, 30)
US_HOLIDAYS = {"2026-09-07"}          # Labor Day (NYSE and COMEX day session closed); nothing else in the sample

N_RUNNING_BEFORE = 627_838            # ledger after GEN8 (GEN9's own count lands separately)
N_THIS = 7                            # 6 tries + 1 information look (registered)


def stage(close):
    if close < DISC_END:
        return "disc"
    if close < VAL_END:
        return "val"
    return "hold"


def day(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- data

def load15(series):
    newh8.FILES[series] = FILES15[series]
    return newh8.load(series, START, END)


def load_ladder(*fnames):
    """{close: {"res": {strike: result}, "q": {end_ts: {strike: (bid, ask, vol)}}}} for settled markets.
    Several files: the first file that holds a close wins that close (files are not mixed within one event)."""
    out = {}
    for fname in fnames:
        db = sqlite3.connect(DATA_DIR / fname)
        mk = {}
        for tk, close, res, k in db.execute("select ticker, close_ts, result, strike from market where close_ts>=? and close_ts<?",
                                            (START, END)):
            if res in ("yes", "no") and k is not None and close not in out:
                mk[tk] = (close, float(k), res)
        ev = defaultdict(lambda: {"res": {}, "q": defaultdict(dict)})
        for tk, (close, k, res) in mk.items():
            ev[close]["res"][k] = res
        for tk, e, b, a, v in db.execute("select ticker, end_ts, bid_c, ask_c, volume from candle"):
            m = mk.get(tk)
            if m is None or b is None or a is None:
                continue
            ev[m[0]]["q"][e][m[1]] = (b, a, v or 0.0)
        out.update(ev)
    return out


# ---------------------------------------------------------------- fees and scoring (multi-leg trades)

def fee(p, c=10, m=1.0):
    return math.ceil(round(0.07 * c * p * (1 - p) * m * 100, 9)) / 100


def net(t, c=10, m=1.0):
    return c * (t["payoff"] - sum(t["legs"])) - sum(fee(p, c, m) for p in t["legs"])


def pf(v):
    g = sum(x for x in v if x > 0)
    l = -sum(x for x in v if x < 0)
    return float("inf") if l == 0 else (g / l if g or l else float("nan"))


def dayz(tr):
    d = defaultdict(float)
    for t in tr:
        d[day(t["close"])] += net(t)
    v = list(d.values())
    if len(v) < 3:
        return float("nan")
    sd = statistics.stdev(v)
    return statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else float("nan")


def summ(tr):
    if not tr:
        return {"n": 0}
    n10 = [net(t) for t in tr]
    return {"n": len(tr), "pf10": pf(n10), "pf1": pf([net(t, 1) for t in tr]), "pfx": pf([net(t, 10, 1.2) for t in tr]),
            "net10": sum(n10), "netx": sum(net(t, 10, 1.2) for t in tr), "z": dayz(tr), "days": len({day(t["close"]) for t in tr}),
            "win": sum(t["payoff"] > sum(t["legs"]) for t in tr) / len(tr), "cost": statistics.mean(sum(t["legs"]) for t in tr),
            "pf10_nz": pf([net(t) for t in tr if not t["zv"]]), "n_zv": sum(t["zv"] for t in tr)}


def fmt(s):
    if s["n"] == 0:
        return "n 0"
    return (f"n {s['n']} ({s['days']} d) PF10 {s['pf10']:.2f} PF1 {s['pf1']:.2f} PFx1.2 {s['pfx']:.2f} net10 ${s['net10']:.2f} "
            f"netx1.2 ${s['netx']:.2f} win {s['win']:.1%} cost/set {s['cost']:.3f} day z {s['z']:.2f} | zero-vol {s['n_zv']}, "
            f"PF10 without {s['pf10_nz']:.2f}")


def zbar(n):
    return NormalDist().inv_cdf(1 - 0.05 / n)


# ---------------------------------------------------------------- LADLOCK: adjacent-strike monotonicity lock on an hourly ladder

LOCK_MIN = 0.01      # per contract, after the C = 10 per-order fees


def ladlock(ev, label):
    """One trade per event: the first candle where YES(K1) + NO(K2) on adjacent strikes K1 < K2 locks >= 1c after fees;
    filled at the NEXT candle's asks of both legs (whatever they are), held. Payoff = [K1 yes] + [K2 no] (always >= 1)."""
    out, nofill, signals = [], 0, 0
    for close, e in sorted(ev.items()):
        ks = sorted(e["res"])
        nxt = {ks[i]: ks[i + 1] for i in range(len(ks) - 1)}
        done = False
        for t in sorted(e["q"]):
            if done or t > close - 120:
                break
            q = e["q"][t]
            for k1 in ks:
                k2 = nxt.get(k1)
                if k2 is None or k1 not in q or k2 not in q:
                    continue
                a1 = q[k1][1]
                a2 = round(1 - q[k2][0], 6)
                if not (0 < a1 < 1 and 0 < a2 < 1):
                    continue
                lock = 1 - a1 - a2 - (fee(a1) + fee(a2)) / 10
                if lock < LOCK_MIN - 1e-9:
                    continue
                signals += 1
                done = True
                f = e["q"].get(t + 60, {})
                if k1 not in f or k2 not in f:
                    nofill += 1
                    break
                f1, f2 = f[k1][1], round(1 - f[k2][0], 6)
                if not (0 < f1 < 1 and 0 < f2 < 1):
                    nofill += 1
                    break
                payoff = (e["res"][k1] == "yes") + (e["res"][k2] == "no")
                zv = min(q[k1][2], q[k2][2], f[k1][2], f[k2][2]) <= 0
                out.append({"close": close, "stage": stage(close), "legs": [f1, f2], "payoff": payoff, "zv": zv,
                            "sig_lock": lock, "rule": "LADLOCK " + label})
                break
    return out, {"events": len(ev), "signals": signals, "no fill": nofill}


# ---------------------------------------------------------------- LADLEAN: the hourly ladder's lean at the 15 minute open

LEAN = 0.05
BAND = (0.30, 0.70)
MAX_GAP = 200.0


def ladder_p(q, k15):
    """Linear interpolation of the YES mids of the adjacent quoted strikes bracketing k15 (K_lo <= k15 < K_hi)."""
    ks = sorted(k for k, (b, a, v) in q.items() if 0 <= b < a <= 1 and a > 0)
    lo = [k for k in ks if k <= k15]
    hi = [k for k in ks if k > k15]
    if not lo or not hi:
        return None
    klo, khi = lo[-1], hi[0]
    if khi - klo > MAX_GAP + 1e-6:
        return None
    mlo = (q[klo][0] + q[klo][1]) / 2
    mhi = (q[khi][0] + q[khi][1]) / 2
    w = (k15 - klo) / (khi - klo)
    return mlo + (mhi - mlo) * w


def ladlean(W, ev):
    out = {"gap": 0, "flat": 0, "band": 0, "nofill": 0}
    tr = []
    for close, w in sorted(W.items()):
        if close % 3600 not in (1800, 2700):
            continue
        H = close - close % 3600 + 3600
        if H not in ev:
            out["gap"] += 1
            continue
        c = w["c"]
        if c.get(-840) is None or c.get(-780) is None or w["strike"] is None:
            out["gap"] += 1
            continue
        q = ev[H]["q"].get(close - 840)
        if not q:
            out["gap"] += 1
            continue
        p = ladder_p(q, float(w["strike"]))
        if p is None:
            out["gap"] += 1
            continue
        if p >= 0.5 + LEAN - 1e-9:
            side = "yes"
        elif p <= 0.5 - LEAN + 1e-9:
            side = "no"
        else:
            out["flat"] += 1
            continue
        a = newh8.side_ask(c[-780], side)
        if a is None:
            out["nofill"] += 1
            continue
        if not (BAND[0] - 1e-9 <= a <= BAND[1] + 1e-9):
            out["band"] += 1
            continue
        tr.append({"close": close, "stage": stage(close), "legs": [a], "payoff": 1 if w["result"] == side else 0,
                   "zv": c[-840][2] <= 0 or c[-780][2] <= 0, "p": p, "side": side, "rule": "LADLEAN"})
    return tr, out


# ---------------------------------------------------------------- session rules: a fixed side at the window's open

SBAND = (0.35, 0.65)


def session_rule(W, side, keep):
    out = {"gap": 0, "band": 0, "nofill": 0, "kept": 0}
    tr = []
    for close, w in sorted(W.items()):
        op = close - 900
        if not keep(op):
            continue
        out["kept"] += 1
        c = w["c"]
        if c.get(-840) is None or c.get(-780) is None:
            out["gap"] += 1
            continue
        a = newh8.side_ask(c[-780], side)
        if a is None:
            out["nofill"] += 1
            continue
        if not (SBAND[0] - 1e-9 <= a <= SBAND[1] + 1e-9):
            out["band"] += 1
            continue
        tr.append({"close": close, "stage": stage(close), "legs": [a], "payoff": 1 if w["result"] == side else 0,
                   "zv": c[-840][2] <= 0 or c[-780][2] <= 0, "side": side})
    return tr, out


def _utc(ts):
    return datetime.fromtimestamp(ts, timezone.utc)


def keep_asia(op):
    """Shanghai Gold Exchange day session, 09:00 to 15:30 Beijing (01:00 to 07:30 UTC), Beijing Monday to Friday."""
    d = _utc(op)
    bj = datetime.fromtimestamp(op + 8 * 3600, timezone.utc)
    mins = d.hour * 60 + d.minute
    return bj.weekday() < 5 and 60 <= mins < 450


def keep_ny(op):
    """COMEX gold day session 08:20 to 13:30 ET; windows opening 12:30 to 17:15 UTC (EDT all sample), US weekdays."""
    d = _utc(op)
    mins = d.hour * 60 + d.minute
    return d.weekday() < 5 and day(op) not in US_HOLIDAYS and 750 <= mins < 1050


def keep_10am(op):
    """US cash open to 10:30 ET: windows opening 13:30, 13:45, 14:00, 14:15 UTC (EDT), US equity trading days."""
    d = _utc(op)
    mins = d.hour * 60 + d.minute
    return d.weekday() < 5 and day(op) not in US_HOLIDAYS and 810 <= mins < 870


# ---------------------------------------------------------------- run

def build():
    W = {BTC: load15(BTC), GOLD: load15(GOLD)}
    EVB = load_ladder("conf2_lad.sqlite", "lad2.sqlite")
    EVG = load_ladder("newh2_goldh.sqlite")
    rules = {}
    rules["LADLOCK btc"] = ladlock(EVB, "btc")
    rules["LADLOCK gold"] = ladlock(EVG, "gold")
    rules["LADLEAN btc"] = ladlean(W[BTC], EVB)
    rules["ASIAGOLD"] = session_rule(W[GOLD], "yes", keep_asia)
    rules["NYGOLD"] = session_rule(W[GOLD], "no", keep_ny)
    rules["BTC10AM"] = session_rule(W[BTC], "no", keep_10am)
    return W, EVB, EVG, rules


def counts():
    W = {BTC: load15(BTC), GOLD: load15(GOLD)}
    EVB = load_ladder("conf2_lad.sqlite", "lad2.sqlite")
    EVG = load_ladder("newh2_goldh.sqlite")
    for s, w in W.items():
        print(s, {st: sum(stage(c) == st for c in w) for st in ("disc", "val", "hold")})
    for n, e in (("KXBTCD", EVB), ("KXGOLDH", EVG)):
        print(n, "events", {st: sum(stage(c) == st for c in e) for st in ("disc", "val", "hold")})
    for n, kp, s in (("ASIAGOLD", keep_asia, GOLD), ("NYGOLD", keep_ny, GOLD), ("BTC10AM", keep_10am, BTC)):
        print(n, "windows kept by clock", {st: sum(stage(c) == st and kp(c - 900) for c in W[s]) for st in ("disc", "val", "hold")})


def verdict_dv(d, v):
    if d["n"] < 100:
        return "NOT_ENOUGH_DATA"
    if d["pf10"] < 1.5 or d["netx"] <= 0:
        return "FALSIFIED"
    if v["n"] < 50:
        return "NOT_ENOUGH_DATA"
    if v["pf10"] < 1.5 or v["netx"] <= 0:
        return "FALSIFIED"
    return "PASSED_DV"


def dv():
    W, EVB, EVG, rules = build()
    N = N_RUNNING_BEFORE + N_THIS
    print(f"NEWH9 dv (once). running N {N:,}; deflated one-sided z bar {zbar(N):.2f}\n")
    for name, (tr, info) in rules.items():
        d = summ([t for t in tr if t["stage"] == "disc"])
        v = summ([t for t in tr if t["stage"] == "val"])
        print(f"{name}: {info}")
        print(f"  disc: {fmt(d)}")
        print(f"  val : {fmt(v)}")
        print(f"  holdout entries (count only, not scored): {sum(t['stage'] == 'hold' for t in tr)}")
        print(f"  VERDICT after discovery and validation: {verdict_dv(d, v)}\n")
    # information look I1 (registered): LADLEAN, the 15 minute market's own first-candle mid against the ladder's p
    tr, _ = rules["LADLEAN btc"]
    print("I1 LADLEAN information: mean ladder p for YES leans and NO leans, the 15 minute YES mid at -840, and the outcome rate")
    for st in ("disc", "val"):
        for side in ("yes", "no"):
            x = [t for t in tr if t["stage"] == st and t["side"] == side]
            if not x:
                continue
            m15 = statistics.mean((W[BTC][t["close"]]["c"][-840][0] + W[BTC][t["close"]]["c"][-840][1]) / 2 for t in x)
            pr = statistics.mean(t["p"] for t in x)
            yr = statistics.mean(1 if W[BTC][t["close"]]["result"] == "yes" else 0 for t in x)
            print(f"  {st} {side}-lean n {len(x)}: ladder p {pr:.3f}, 15m YES mid {m15:.3f}, YES outcome rate {yr:.3f}")


def holdout(names):
    W, EVB, EVG, rules = build()
    N = N_RUNNING_BEFORE + N_THIS
    for name in names:
        tr, info = rules[name]
        h = summ([t for t in tr if t["stage"] == "hold"])
        allz = dayz(tr)
        print(f"{name} holdout: {fmt(h)}; pooled day z over all three windows {allz:.2f} against bar {zbar(N):.2f}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "counts":
        counts()
    elif cmd == "dv":
        dv()
    elif cmd == "holdout":
        holdout(sys.argv[2:])
