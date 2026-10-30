"""NEWH11: gold's opening quote against COMEX, and the CME weekend gap on Bitcoin (research only).

Registration: workers/NEWH11_REGISTRATION.md (pushed before any scoring).

    PYTHONPATH=src python -m scalper.newh11 counts    (windows per arm and stage by clock, data coverage, strike structure;
                                                       no Kalshi quote and no result read)
    PYTHONPATH=src python -m scalper.newh11 dv        (discovery and validation, scored once)
    PYTHONPATH=src python -m scalper.newh11 holdout NAME...   (frozen holdout, read once, only for rules that passed dv)

Tries (3): GOLDOPEN, CMEGAP-W, CMEGAP-R. Information look (1, counted): strike structure (strikes only, no outcome).
Extra spot files (Binance spot BTCUSDT 1 minute, 2026-10-27 to 10-29, public) are read from SPOT_EXTRA if present.
"""
from __future__ import annotations

import csv
import io
import json
import math
import sqlite3
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

from .paths import DATA_DIR
from . import newh9
from .newh9 import day, fee, net, pf, dayz, summ, fmt, zbar

N01 = NormalDist()
N_RUNNING_BEFORE = 627_852            # ledger after NEWH10
N_THIS = 4                            # 3 tries + 1 information look (registered)

GOLD, BTC = "KXGOLD15M", "KXBTC15M"
SIG, FIL = -840, -780                 # signal candle ends 840 s before the close (first minute), fill candle the next one
SPOT_EXTRA = Path("/tmp/claude-0/-home-user-shwoopnet/026f6e8f-6dc4-5e3b-8c3b-e0089b12fb94/scratchpad/bv")


def _ts(y, m, d, h=0):
    return int(datetime(y, m, d, h, tzinfo=timezone.utc).timestamp())


def _utc(ts):
    return datetime.fromtimestamp(ts, timezone.utc)


# ---------------------------------------------------------------- windows (by close time, UTC), fixed in the registration

G_START, G_DISC, G_VAL, G_END = _ts(2026, 10, 1), _ts(2026, 10, 11), _ts(2026, 10, 20), _ts(2026, 10, 29, 15)
B_START, B_DISC, B_VAL, B_END = newh9.START, newh9.DISC_END, newh9.VAL_END, newh9.END


def gstage(c):
    return "disc" if c < G_DISC else ("val" if c < G_VAL else "hold")


def bstage(c):
    return "disc" if c < B_DISC else ("val" if c < B_VAL else "hold")


# ---------------------------------------------------------------- GOLDOPEN: gold's first-minute quote against COMEX (GC=F)

EDGE = 0.05
G_BAND = (0.10, 0.90)
MAX_JUMP = 0.005


def load_gc():
    b = json.load(open(DATA_DIR / "gc1m.json"))["bars"]
    return {int(k): v for k, v in b.items() if v and v[3] is not None}


def gold_model(gc, close):
    """p(YES) from COMEX: d = close of the bar starting at the open O (it ends at the signal time) minus close of the bar
    starting O - 60 (the strike minute); sigma from the 1 minute changes of the 60 bars before O. None with a reason."""
    O = close - 900
    b0, b1 = gc.get(O - 60), gc.get(O)
    if b0 is None or b1 is None:
        return None, "gc gap"
    ch = []
    for s in range(O - 3660, O - 60, 60):
        x, y = gc.get(s), gc.get(s + 60)
        if x is not None and y is not None:
            ch.append(y[3] - x[3])
            if abs(y[3] / x[3] - 1) > MAX_JUMP:
                return None, "jump"
    d = b1[3] - b0[3]
    if abs(b1[3] / b0[3] - 1) > MAX_JUMP:
        return None, "jump"
    if len(ch) < 45:
        return None, "sigma bars"
    sd = statistics.pstdev(ch)
    if sd <= 0:
        return None, "sigma bars"
    return N01.cdf(d / (sd * math.sqrt(14))), "ok"


def goldopen(win, gc):
    tr, info = [], Counter()
    for close in sorted(win):
        if not (G_START <= close < G_END):
            continue
        info["windows"] += 1
        w = win[close]
        p, why = gold_model(gc, close)
        if p is None:
            info[why] += 1
            continue
        q = w["c"].get(SIG)
        if not q or not (0 < q[0] < q[1] < 1):
            info["no signal quote"] += 1
            continue
        ey, en = p - q[1], q[0] - p
        side, e = ("yes", ey) if ey >= en else ("no", en)
        if e < EDGE - 1e-9:
            info["no edge"] += 1
            continue
        f = w["c"].get(FIL)
        fa = None if f is None else newh9.newh8.side_ask(f, side)
        if fa is None:
            info["no fill"] += 1
            continue
        if not (G_BAND[0] - 1e-9 <= fa <= G_BAND[1] + 1e-9):
            info["band"] += 1
            continue
        info["ok"] += 1
        tr.append({"close": close, "stage": gstage(close), "legs": [fa], "payoff": 1 if w["result"] == side else 0,
                   "zv": q[2] <= 0 or f[2] <= 0, "side": side, "p": p})
    return tr, dict(info)


# ---------------------------------------------------------------- CMEGAP: Bitcoin toward the CME Friday close

GAP = 0.005
B_BAND = (0.30, 0.70)


def load_spot():
    """{minute start (s): (high, low, close)} from Binance spot BTCUSDT 1 minute klines (open time in microseconds)."""
    out = {}
    files = sorted((DATA_DIR / "binance").glob("spot_BTCUSDT-*.zip"))
    if SPOT_EXTRA.exists():
        files += sorted(SPOT_EXTRA.glob("spot_BTCUSDT-*.zip"))
    for f in files:
        z = zipfile.ZipFile(f)
        for name in z.namelist():
            for r in csv.reader(io.TextIOWrapper(z.open(name))):
                if not r or not r[0].isdigit():
                    continue
                t = int(r[0])
                t = t // 1_000_000 if t > 10**14 else t // 1000
                out[t] = (float(r[2]), float(r[3]), float(r[4]))
    return out


def cme_anchor(O):
    """For a window opening at O: (arm, friday_close_ts, reopen_ts) or None. CME Bitcoin futures: weekly close Friday 16:00 CT
    = 21:00 UTC, reopen Sunday 17:00 CT = 22:00 UTC (CDT all sample). W: O in [Fri 21:00, Sun 22:00); R: [Sun 22:00, Mon 21:00)."""
    d = _utc(O)
    # most recent Friday 21:00 UTC at or before O
    days_back = (d.weekday() - 4) % 7
    fri = _ts(d.year, d.month, d.day) - days_back * 86400 + 21 * 3600
    if fri > O:
        fri -= 7 * 86400
    reopen = fri + 2 * 86400 + 3600          # Sunday 22:00 UTC
    mon_end = fri + 3 * 86400                # Monday 21:00 UTC
    if fri <= O < reopen:
        return "W", fri, reopen
    if reopen <= O < mon_end:
        return "R", fri, reopen
    return None


def cmegap(win, spot, arm):
    tr, info = [], Counter()
    for close in sorted(win):
        if not (B_START <= close < B_END):
            continue
        O = close - 900
        a = cme_anchor(O)
        if a is None or a[0] != arm:
            continue
        info["windows"] += 1
        _, fri, reopen = a
        F = spot.get(fri - 60)
        D = close + SIG
        x = spot.get(D - 60)
        if F is None or x is None:
            info["spot gap"] += 1
            continue
        F, xc = F[2], x[2]
        g = F / xc - 1
        if abs(g) < GAP:
            info["small gap"] += 1
            continue
        if arm == "R":
            filled, missing = False, 0
            for s in range(reopen, D, 60):
                m = spot.get(s)
                if m is None:
                    missing += 1
                    continue
                if (F > xc and m[0] >= F) or (F < xc and m[1] <= F):
                    filled = True
                    break
            if filled:
                info["filled"] += 1
                continue
        side = "yes" if F > xc else "no"
        w = win[close]
        q = w["c"].get(SIG)
        f = w["c"].get(FIL)
        fa = None if f is None else newh9.newh8.side_ask(f, side)
        if fa is None:
            info["no fill"] += 1
            continue
        if not (B_BAND[0] - 1e-9 <= fa <= B_BAND[1] + 1e-9):
            info["band"] += 1
            continue
        info["ok"] += 1
        zv = f[2] <= 0 or (q is not None and q[2] <= 0)
        tr.append({"close": close, "stage": bstage(close), "legs": [fa], "payoff": 1 if w["result"] == side else 0,
                   "zv": zv, "side": side, "gap": g})
    return tr, dict(info)


# ---------------------------------------------------------------- information look: strike structure (no outcome)

def strike_structure():
    for series, files in ((BTC, ("l1b", "book", "fresh")), (GOLD, ("l1b", "book", "fresh", "five"))):
        ks = []
        for f in files:
            db = sqlite3.connect(DATA_DIR / f"{f}.sqlite")
            ks += [k for (k,) in db.execute("select strike from market where series=? and strike is not null", (series,))]
        n = len(ks)
        cents = Counter(round((k * 100) % 100) for k in ks)
        print(f"{series}: {n} strikes; whole dollars {sum(abs(k - round(k)) < 1e-6 for k in ks) / n:.1%}; multiples of $10 "
              f"{sum(abs(k / 10 - round(k / 10)) < 1e-6 for k in ks) / n:.1%}; of $100 {sum(abs(k / 100 - round(k / 100)) < 1e-6 for k in ks) / n:.1%}; "
              f"distinct cent endings {len(cents)}; example {ks[:3]}")
    db = sqlite3.connect(DATA_DIR / "lad2.sqlite")
    gaps = Counter()
    ev = defaultdict(list)
    for close, k in db.execute("select close_ts, strike from market where strike is not null"):
        ev[close].append(k)
    for ks in ev.values():
        ks = sorted(set(ks))
        gaps.update(round(b - a, 2) for a, b in zip(ks, ks[1:]))
    print("KXBTCD (lad2) adjacent strike spacing, most common:", gaps.most_common(4))


# ---------------------------------------------------------------- run

def loads():
    gwin = newh9.load15(GOLD)
    bwin = newh9.load15(BTC)
    return gwin, bwin, load_gc(), load_spot()


def counts():
    gwin, bwin, gc, spot = loads()
    print("GOLDOPEN windows by clock:", Counter(gstage(c) for c in gwin if G_START <= c < G_END),
          "; GC bars", len(gc), _utc(min(gc)), _utc(max(gc)))
    for arm in ("W", "R"):
        cnt = Counter()
        for c in bwin:
            a = cme_anchor(c - 900)
            if B_START <= c < B_END and a and a[0] == arm:
                cnt[bstage(c)] += 1
        print(f"CMEGAP-{arm} windows by clock:", dict(cnt))
    print("spot minutes", len(spot), _utc(min(spot)), _utc(max(spot)))
    strike_structure()


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


def rules(gwin, bwin, gc, spot):
    return {"GOLDOPEN": goldopen(gwin, gc), "CMEGAP-W": cmegap(bwin, spot, "W"), "CMEGAP-R": cmegap(bwin, spot, "R")}


def dv():
    gwin, bwin, gc, spot = loads()
    N = N_RUNNING_BEFORE + N_THIS
    print(f"NEWH11 dv (once). running N {N:,}; deflated one-sided z bar {zbar(N):.2f}\n")
    for name, (tr, info) in rules(gwin, bwin, gc, spot).items():
        th = sum(t["stage"] == "hold" for t in tr)
        d = summ([t for t in tr if t["stage"] == "disc"])
        v = summ([t for t in tr if t["stage"] == "val"])
        print(f"{name}: {info} (funnel includes holdout windows; holdout trades not scored: {th})")
        print(f"  disc: {fmt(d)}")
        print(f"  val : {fmt(v)}")
        for st in ("disc", "val"):
            x = [t for t in tr if t["stage"] == st]
            if x:
                print(f"  {st} mean price paid {statistics.mean(t['legs'][0] for t in x):.3f}, win rate "
                      f"{statistics.mean(t['payoff'] for t in x):.3f}, yes share {statistics.mean(t['side'] == 'yes' for t in x):.2f}")
        print(f"  VERDICT after discovery and validation: {verdict_dv(d, v)}\n")


def holdout(names):
    gwin, bwin, gc, spot = loads()
    N = N_RUNNING_BEFORE + N_THIS
    R = rules(gwin, bwin, gc, spot)
    for name in names:
        tr, info = R[name]
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
