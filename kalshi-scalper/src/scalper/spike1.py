"""SPIKE1 (workers/SPIKE1_REGISTRATION.md): mean reversion after a contract-implied spike on the 15 minute markets that are NOT crypto and NOT
gold. Research only; nothing here places an order, reads a key or decides anything live.
    PYTHONPATH=src python -m scalper.spike1 counts   (outcome-free: spikes and eligible trades per series and third; the result is NOT read)
    PYTHONPATH=src python -m scalper.spike1 score    (once: W1 and W2; W3 only if the screen passes; refuses a second run)
Spike: on the contract's own 1 minute YES mid (no outside spot is used, see the registration), the change over 2 minutes, in units of the
trailing 60 minute sd of 1 minute mid changes of the same series, is at least 3 (scaled by sqrt 2) and at least 5c.
Trade: the cheap side (ask 0.05 to 0.30 on the signal candle), fill at that side's ask on the NEXT candle, hard limit 0.30, held, C = 10,
fee 7% x C x p x (1-p) rounded up (gen6.fee).
"""
from __future__ import annotations

import bisect
import json
import math
import sqlite3
import statistics
import sys
from collections import defaultdict

from . import event1
from .calibration import cluster_mean_z
from .event1 import day_of, net_c, pf, side_ask, third_of, LO_TS, END_TS
from .oicorex1 import ALT_FILES
from .paths import DATA_DIR

SERIES = ["KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXAUDUSD15M", "KXUSDCAD15M", "KXSILVER15M", "KXCOPPER15M", "KXWTI15M",
          "KXNATGAS15M", "KXPLATINUM15M", "KXPALLADIUM15M"]
OUT = DATA_DIR / "spike1_score.json"
STEP = 900
Z_SPIKE = 3.0
MIN_JUMP = 0.05            # the 2 minute mid change must also be at least 5c
SD_FLOOR = 0.01            # trailing sd floor, so a quiet hour cannot turn a 1c wiggle into a "3 sd" event
MIN_CHG = 40               # trailing 1 minute changes needed (of at most 56)
LOOKS = tuple(range(720, 239, -60))   # signal candle ends 720, 660, ..., 240 s before the close; fill on the next candle (<= 180 s)
LO, HI = 0.05, 0.30
MAX_SPREAD = 0.10
Z_CTRL = 2.0               # control windows: |z| below this at the same look
FLOOR_N = 150
HALF_FLOOR = 40
Z_BAR = 5.27
CTRL_MIN = 5


def load(series, with_result=False):
    """[{tk, ct, cs, res}] sorted by ct. First file wins per ticker. res is None unless with_result (the column is not even selected)."""
    seen, out = set(), []
    cols = "ticker, close_ts, result" if with_result else "ticker, close_ts, 'x'"
    for name in ALT_FILES:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        try:
            mk = db.execute(f"select {cols} from market where series=? and close_ts>=? and close_ts<?", (series, LO_TS, END_TS)).fetchall()
        except sqlite3.Error:
            continue
        for tk, ct, res in mk:
            if tk in seen:
                continue
            cs = {r[0]: (r[1], r[2], r[3] or 0.0) for r in db.execute(
                "select end_ts, bid_c, ask_c, volume from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if not cs:
                continue
            if with_result and res not in ("yes", "no"):
                continue
            seen.add(tk)
            out.append({"tk": tk, "ct": ct, "cs": cs, "res": res if with_result else None})
    out.sort(key=lambda w: w["ct"])
    return out


def mid(q):
    """YES mid of a candle, or None when one-sided, crossed, settled or wider than MAX_SPREAD."""
    if q is None or q[0] is None or q[1] is None or not 0 < q[0] < q[1] < 1 or q[1] - q[0] > MAX_SPREAD + 1e-9:
        return None
    return (q[0] + q[1]) / 2


def trailing_sd(by_ct, ct):
    """RMS of 1 minute YES mid changes in the (up to) four windows closing at ct-900 ... ct-3600; candles ending at or before their close - 60
    (the settlement candle is excluded). None if fewer than MIN_CHG changes. Looks only at earlier windows: no look-ahead."""
    ch = []
    for j in range(1, 5):
        w = by_ct.get(ct - STEP * j)
        if w is None:
            continue
        c = w["ct"]
        prev = None
        for e in range(c - 840, c - 59, 60):
            m = mid(w["cs"].get(e))
            if m is not None and prev is not None:
                ch.append(m - prev)
            prev = m
    if len(ch) < MIN_CHG:
        return None
    return max(math.sqrt(sum(x * x for x in ch) / len(ch)), SD_FLOOR)


def spike_z(cs, ct, look, sd):
    """(z, delta) at the signal candle ending ct-look; z = delta / (sd sqrt 2) with delta the YES mid change over 2 minutes. None if a mid is missing."""
    a, b = mid(cs.get(ct - look - 120)), mid(cs.get(ct - look))
    if a is None or b is None or sd is None:
        return None
    d = b - a
    return d / (sd * math.sqrt(2)), d


def cheap_side(q):
    return next((sd for sd in ("yes", "no") if LO - 1e-9 <= side_ask(q, sd) <= HI + 1e-9), None)


def fill_for(cs, ct, look, side):
    f = cs.get(ct - look + 60)
    if f is None or f[0] is None or f[1] is None or not 0 < f[0] < f[1] < 1:
        return None
    p = side_ask(f, side)
    return float(p) if 0 < p <= HI + 1e-9 else None


def window_events(w, by_ct):
    """For one window: the FIRST look with |z| >= Z_SPIKE and |delta| >= MIN_JUMP that has a cheap side (ask LO..HI) and a fill within the
    limit -> ('spike', kind, trade); plus the control candidate list (looks with |z| < Z_CTRL and a cheap side and a fill).
    kind is 'rev' when the cheap side is AGAINST the spike direction, 'cont' when it is WITH it. Quotes only."""
    cs, ct = w["cs"], w["ct"]
    sd = trailing_sd(by_ct, ct)
    if sd is None:
        return None, [], False
    trig, ctrl = None, []
    for look in LOOKS:
        r = spike_z(cs, ct, look, sd)
        if r is None:
            continue
        z, d = r
        sig = cs.get(ct - look)
        sdd = cheap_side(sig)
        if sdd is None:
            continue
        fill = fill_for(cs, ct, look, sdd)
        if fill is None:
            continue
        tr = {"side": sdd, "fill": fill, "look": look, "z": z, "delta": d}
        if abs(z) >= Z_SPIKE and abs(d) >= MIN_JUMP:
            if trig is None:
                up = d > 0
                tr["kind"] = "rev" if (sdd == "no") == up else "cont"
                trig = tr
        elif abs(z) < Z_CTRL:
            ctrl.append(tr)
    return trig, ctrl, True


def any_spike(w, by_ct):
    """True if the window has a 3 sd, 5c spike at some look regardless of any cheap side (the trigger rate before the price rule)."""
    sd = trailing_sd(by_ct, w["ct"])
    if sd is None:
        return None
    for look in LOOKS:
        r = spike_z(w["cs"], w["ct"], look, sd)
        if r is not None and abs(r[0]) >= Z_SPIKE and abs(r[1]) >= MIN_JUMP:
            return True
    return False


def hour_of(ct):
    return (ct // 3600) % 24


def build(series=SERIES, with_result=False):
    """{series: {'rev': [...], 'cont': [...], 'ctrl': [...], 'nwin', 'nsd', 'nspike'}}"""
    out = {}
    for sr in series:
        wins = load(sr, with_result)
        by_ct = {w["ct"]: w for w in wins}
        d = {"rev": [], "cont": [], "ctrl": [], "nwin": defaultdict(int), "nsd": defaultdict(int), "nspike": defaultdict(int)}
        for w in wins:
            th = third_of(w["ct"])
            d["nwin"][th] += 1
            trig, ctrl, ok = window_events(w, by_ct)
            if not ok:
                continue
            d["nsd"][th] += 1
            if any_spike(w, by_ct):
                d["nspike"][th] += 1
            row = lambda tr: dict(series=sr, ct=w["ct"], day=day_of(w["ct"]), third=th, hour=hour_of(w["ct"]), tr=tr,
                                  win=((w["res"] == "yes") == (tr["side"] == "yes")) if with_result else None)
            if trig:
                d[trig["kind"]].append(row(trig))
            for tr in ctrl:
                d["ctrl"].append(row(tr))
        out[sr] = d
    return out


def spread_median(series):
    """Median YES spread over signal-look candles (quotes only)."""
    v = []
    for w in load(series)[:3000]:
        for look in LOOKS:
            q = w["cs"].get(w["ct"] - look)
            if q and q[0] is not None and q[1] is not None and 0 < q[0] < q[1] < 1:
                v.append(q[1] - q[0])
    return statistics.median(v) if v else None


def counts():
    B = build()
    print("series | windows W1/W2/W3 | with sd W1/W2/W3 | any-spike W1/W2/W3 | rev W1/W2/W3 | cont W1/W2/W3 | ctrl W1/W2/W3 | median spread")
    for sr, d in B.items():
        t = lambda k: "/".join(str(sum(1 for r in d[k] if r["third"] == i)) for i in (1, 2, 3))
        g = lambda m: "/".join(str(m[i]) for i in (1, 2, 3))
        print(sr, "|", g(d["nwin"]), "|", g(d["nsd"]), "|", g(d["nspike"]), "|", t("rev"), "|", t("cont"), "|", t("ctrl"), "|", spread_median(sr))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "counts":
        counts()
    else:
        print(__doc__)
