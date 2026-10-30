"""NEWH10: does the hourly ladders' width follow the clock? (research only)

Registration: workers/NEWH10_REGISTRATION.md (pushed before any scoring).

    PYTHONPATH=src python -m scalper.newh10 counts    (events per arm and stage by clock only; no quote, no result)
    PYTHONPATH=src python -m scalper.newh10 dv        (discovery and validation, scored once, plus the two information looks)
    PYTHONPATH=src python -m scalper.newh10 holdout NAME...   (frozen holdout, read once, only for rules that passed dv)

Tries (4): WKNDWIDE btc, USNARROW btc, ASIAWIDE gold, USNARROW gold. Information looks (2, counted): I1 weekday twin of
WKNDWIDE; I2 macro release hour on the Bitcoin ladder.
"""
from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from statistics import NormalDist

from .paths import DATA_DIR
from . import newh9
from .newh9 import stage, day, fee, net, pf, dayz, summ, fmt, zbar, load_ladder, START, END

N01 = NormalDist()
N_RUNNING_BEFORE = 627_846            # ledger after LADFADE
N_THIS = 6                            # 4 tries + 2 information looks (registered)

US_HOLIDAYS = {"2026-09-07"}          # Labor Day (US cash equities and the COMEX day session closed)
CAL = DATA_DIR.parent / "studies" / "EVENT_CALENDAR_2026.csv"
MACRO = {"CPI", "PPI", "JOBS", "GDP", "PCE", "RETAIL", "CLAIMS"}

# rule constants (fixed in the registration)
WING = (0.20, 0.40)       # the cheap side's mid at the signal candle
TARGET = 0.30             # the wing strike is the one whose cheap-side mid is closest to this
MAX_SPREAD = 0.03         # at the signal candle
EXP_BAND = (0.58, 0.82)   # fill band when the rule buys the expensive side
CHEAP_BAND = (0.18, 0.42) # fill band when the rule buys the cheap side
BTC_LEAD, GOLD_LEAD = 2700, 840   # signal candle ends this many seconds before the close; the fill candle 60 s later
MACRO_LEAD = 2100                 # I2: signal candle ending 12:25 UTC for the 13:00 UTC close (before the 12:30 UTC release)


def _utc(ts):
    return datetime.fromtimestamp(ts, timezone.utc)


# ---------------------------------------------------------------- arms by clock (close time of the hourly event)

def weekend(close):
    """Close on Saturday or Sunday UTC (Friday 7 PM to Sunday 7 PM Central)."""
    return _utc(close).weekday() >= 5


def weekday_btc(close):
    return _utc(close).weekday() < 5


def us_hours(close):
    """Hourly closes 14:00 to 20:00 UTC (9 AM to 3 PM Central, the US cash session), UTC Monday to Friday, not Labor Day."""
    d = _utc(close)
    return d.weekday() < 5 and day(close) not in US_HOLIDAYS and 14 <= d.hour <= 20 and d.minute == 0


def asia_hours(close):
    """Hourly closes 01:00 to 08:00 UTC (8 PM to 3 AM Central), Beijing date Monday to Friday (UTC + 8 h)."""
    d = _utc(close)
    bj = _utc(close + 8 * 3600)
    return bj.weekday() < 5 and 1 <= d.hour <= 8 and d.minute == 0


def macro_days():
    """UTC dates with a verified or rule-based 8:30 ET (12:30 UTC) US macro release in the calendar."""
    out = set()
    for r in csv.DictReader(open(CAL)):
        if r["event"] in MACRO and r["status"] in ("verified", "rule") and r["release_utc"].endswith("T12:30Z"):
            out.add(r["release_utc"][:10])
    return out


def macro_close(close, days, want):
    d = _utc(close)
    if not (d.weekday() < 5 and d.hour == 13 and d.minute == 0 and day(close) not in US_HOLIDAYS):
        return False
    return (day(close) in days) == want


# ---------------------------------------------------------------- the wing rule

def wing_trade(ev, close, lead, buy):
    """One trade per event. Signal candle ends `lead` s before the close: among strikes with 0 < bid < ask < 1 and
    spread <= MAX_SPREAD, take the cheap side mid c = min(m, 1 - m); keep c in WING; pick c closest to TARGET (ties: the lower
    strike). buy = "exp" buys the side whose mid is above 0.5, "cheap" the other. Fill: that side's ask on the candle ending
    lead - 60 s before the close, inside the band. Returns (trade or None, reason)."""
    e = ev[close]
    q = e["q"].get(close - lead)
    if not q:
        return None, "gap"
    best = None
    for k in sorted(q):
        b, a, v = q[k]
        if not (0 < b < a < 1) or a - b > MAX_SPREAD + 1e-9:
            continue
        m = (b + a) / 2
        c = min(m, 1 - m)
        if not (WING[0] - 1e-9 <= c <= WING[1] + 1e-9):
            continue
        d = abs(c - TARGET)
        if best is None or d < best[0] - 1e-12:
            best = (d, k, m)
    if best is None:
        return None, "no wing"
    _, k, m = best
    exp_side = "yes" if m > 0.5 else "no"
    side = exp_side if buy == "exp" else ("no" if exp_side == "yes" else "yes")
    f = e["q"].get(close - lead + 60, {}).get(k)
    if f is None:
        return None, "no fill"
    fa = f[1] if side == "yes" else round(1 - f[0], 6)
    if not (0 < fa < 1):
        return None, "no fill"
    lo, hi = EXP_BAND if buy == "exp" else CHEAP_BAND
    if not (lo - 1e-9 <= fa <= hi + 1e-9):
        return None, "band"
    res = e["res"][k]
    return {"close": close, "stage": stage(close), "legs": [fa], "payoff": 1 if res == side else 0,
            "zv": q[k][2] <= 0 or f[2] <= 0, "side": side, "strike": k, "sig_mid": m}, "ok"


def run_rule(ev, keep, lead, buy):
    tr, info = [], defaultdict(int)
    for close in sorted(ev):
        if close < START or close >= END or not keep(close):
            continue
        info["events"] += 1
        t, why = wing_trade(ev, close, lead, buy)
        info[why] += 1
        if t:
            tr.append(t)
    return tr, dict(info)


def probit_s(q, nmin=3):
    """Width of the ladder at one candle: s of P(above K) = Phi((mu - K) / s), least squares of Phi^-1(mid) on K."""
    xs, zs = [], []
    for k, (b, a, v) in q.items():
        if 0 < b < a < 1:
            m = (b + a) / 2
            if 0.03 <= m <= 0.97:
                xs.append(k)
                zs.append(N01.inv_cdf(m))
    if len(xs) < nmin:
        return None
    mx, mz = statistics.fmean(xs), statistics.fmean(zs)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    bb = sum((x - mx) * (z - mz) for x, z in zip(xs, zs)) / sxx
    if bb >= 0:
        return None
    return -1.0 / bb


# ---------------------------------------------------------------- build

def loads():
    EVB = load_ladder("conf2_lad.sqlite", "lad2.sqlite")
    EVG = load_ladder("newh2_goldh.sqlite")
    return EVB, EVG


ARMS = {
    "WKNDWIDE btc": ("B", weekend, BTC_LEAD, "exp"),
    "USNARROW btc": ("B", us_hours, BTC_LEAD, "cheap"),
    "ASIAWIDE gold": ("G", asia_hours, GOLD_LEAD, "exp"),
    "USNARROW gold": ("G", us_hours, GOLD_LEAD, "cheap"),
}


def counts():
    EVB, EVG = loads()
    md = macro_days()
    for name, (src, keep, lead, buy) in ARMS.items():
        ev = EVB if src == "B" else EVG
        print(name, "events by clock", {st: sum(stage(c) == st and keep(c) and START <= c < END for c in ev)
                                       for st in ("disc", "val", "hold")})
    print("I1 weekday twin", {st: sum(stage(c) == st and weekday_btc(c) for c in EVB) for st in ("disc", "val", "hold")})
    for want in (True, False):
        print("I2 13:00 UTC close, release day" if want else "I2 13:00 UTC close, other weekdays",
              {st: sum(stage(c) == st and macro_close(c, md, want) for c in EVB) for st in ("disc", "val", "hold")})
    print("macro release days in calendar:", len(md))


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


def dv_only(tr):
    return [t for t in tr if t["stage"] in ("disc", "val")]


def dv():
    EVB, EVG = loads()
    N = N_RUNNING_BEFORE + N_THIS
    print(f"NEWH10 dv (once). running N {N:,}; deflated one-sided z bar {zbar(N):.2f}\n")
    for name, (src, keep, lead, buy) in ARMS.items():
        ev = EVB if src == "B" else EVG
        tr, info = run_rule(ev, keep, lead, buy)
        tr_h = sum(t["stage"] == "hold" for t in tr)
        tr = dv_only(tr)
        d = summ([t for t in tr if t["stage"] == "disc"])
        v = summ([t for t in tr if t["stage"] == "val"])
        print(f"{name}: {info} (funnel includes holdout events; holdout trades not scored: {tr_h})")
        print(f"  disc: {fmt(d)}")
        print(f"  val : {fmt(v)}")
        for st in ("disc", "val"):
            x = [t for t in tr if t["stage"] == st]
            if x:
                print(f"  {st} mean price paid {statistics.mean(t['legs'][0] for t in x):.3f}, win rate "
                      f"{statistics.mean(t['payoff'] for t in x):.3f}")
        print(f"  VERDICT after discovery and validation: {verdict_dv(d, v)}\n")

    # I1: weekday twin of WKNDWIDE (information, counted, never a rule)
    tr, info = run_rule(EVB, weekday_btc, BTC_LEAD, "exp")
    tr = dv_only(tr)
    print(f"I1 weekday twin of WKNDWIDE (information): {info}")
    for st in ("disc", "val"):
        print(f"  {st}: {fmt(summ([t for t in tr if t['stage'] == st]))}")

    # I2: macro release hour on the Bitcoin ladder (information, counted)
    md = macro_days()
    print("\nI2 Bitcoin ladder, 13:00 UTC close, signal 12:25 UTC (before the 12:30 UTC release): width and the cheap wing")
    for want in (True, False):
        lab = "release days" if want else "other weekdays"
        tr, info = run_rule(EVB, lambda c: macro_close(c, md, want), MACRO_LEAD, "cheap")
        tr = dv_only(tr)
        ss = [probit_s(EVB[c]["q"].get(c - MACRO_LEAD, {})) for c in EVB
              if stage(c) in ("disc", "val") and macro_close(c, md, want)]
        ss = [s for s in ss if s]
        s_med = statistics.median(ss) if ss else float("nan")
        x = tr
        wr = statistics.mean(t["payoff"] for t in x) if x else float("nan")
        pp = statistics.mean(t["legs"][0] for t in x) if x else float("nan")
        print(f"  {lab}: {info}; ladder width s median ${s_med:,.0f} on {len(ss)} events; cheap wing disc+val {fmt(summ(x))}; "
              f"win {wr:.3f} vs price {pp:.3f}")


def holdout(names):
    EVB, EVG = loads()
    N = N_RUNNING_BEFORE + N_THIS
    for name in names:
        src, keep, lead, buy = ARMS[name]
        ev = EVB if src == "B" else EVG
        tr, info = run_rule(ev, keep, lead, buy)
        h = summ([t for t in tr if t["stage"] == "hold"])
        print(f"{name} holdout: {fmt(h)}; pooled day z over all three windows {dayz(tr):.2f} against bar {zbar(N):.2f}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "counts":
        counts()
    elif cmd == "dv":
        dv()
    elif cmd == "holdout":
        holdout(sys.argv[2:])
