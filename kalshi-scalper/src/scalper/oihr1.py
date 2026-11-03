"""OIHR1 (workers/OIHR1_REGISTRATION.md): the OICORE shape on the hourly Bitcoin ladder KXBTCD. Research only; places no order.
    PYTHONPATH=src python -m scalper.oihr1 counts   (outcome-free: eligible events, trigger counts, thirds; reads NO result)
    PYTHONPATH=src python -m scalper.oihr1 score    (once: W1, W2; W3 only if both pass; refuses a second run)
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from collections import defaultdict
from statistics import mean

from . import gen6
from .calibration import cluster_mean_z
from .paths import DATA_DIR

DB = DATA_DIR / "conf2_lad.sqlite"
LOOK, BACK, FILL = 1200, 1800, 1140
LO, HI = 0.03, 0.30
MIN_STRIKES, MIN_TRAIL, TRAIL_S = 6, 12, 24 * 3600
FLOOR_N, C = 150, 10
OUT = DATA_DIR / "oihr1_score.json"


def p90(vals):
    s = sorted(vals)
    return s[math.ceil(0.9 * len(s)) - 1]


def oi_stat(ev):
    """ev: {strike: {offset_s: (bid, ask, oi)}}. S = sum oi(look)/sum oi(back) - 1 over strikes with oi at both; None if not eligible."""
    a = b = 0.0
    n = 0
    for k, cs in ev.items():
        l, bk = cs.get(LOOK), cs.get(BACK)
        if l is None or bk is None or l[2] is None or bk[2] is None:
            continue
        a += l[2]; b += bk[2]; n += 1
    if n < MIN_STRIKES or b <= 0:
        return None
    return a / b - 1


def centre(ev, off):
    """Strike where the YES mid crosses 0.5, linear interpolation; None without a crossing."""
    pts = []
    for k, cs in ev.items():
        c = cs.get(off)
        if c is None or c[0] is None or c[1] is None or not c[1] > c[0]:
            continue
        pts.append((k, (c[0] + c[1]) / 2))
    pts.sort()
    for (k1, m1), (k2, m2) in zip(pts, pts[1:]):
        if m1 >= 0.5 >= m2 and m1 > m2:
            return k1 + (k2 - k1) * (m1 - 0.5) / (m1 - m2)
    return None


def lean(ev):
    c0, c1 = centre(ev, BACK), centre(ev, LOOK)
    if c0 is None or c1 is None or c1 == c0:
        return None
    return "up" if c1 > c0 else "down"


def ask(c, side):
    return c[1] if side == "yes" else round(1 - c[0], 6)


def pick(ev, mode):
    """Return (strike, side, fill) or None. mode 'A' lean side, 'B' cheaper side. Quotes only."""
    cen = centre(ev, LOOK)
    cands = []
    if mode == "A":
        d = lean(ev)
        if d is None or cen is None:
            return None
        side = "yes" if d == "up" else "no"
        for k, cs in ev.items():
            c = cs.get(LOOK)
            if c is None or c[0] is None or c[1] is None or not c[1] > c[0]:
                continue
            if (side == "yes" and k > cen) or (side == "no" and k < cen):
                a = ask(c, side)
                if LO - 1e-9 <= a <= HI + 1e-9:
                    cands.append((a, k, side))
    else:
        for k, cs in ev.items():
            c = cs.get(LOOK)
            if c is None or c[0] is None or c[1] is None or not c[1] > c[0]:
                continue
            ay, an = ask(c, "yes"), ask(c, "no")
            side, a = ("yes", ay) if ay <= an else ("no", an)
            if LO - 1e-9 <= a <= HI + 1e-9:
                cands.append((a, k, side))
    if not cands:
        return None
    a, k, side = max(cands, key=lambda t: (t[0], t[1]))
    f = ev[k].get(FILL)
    if f is None or f[0] is None or f[1] is None or not f[1] > f[0]:
        return None
    fill = ask(f, side)
    if not 0 < fill <= HI + 1e-9:
        return None
    return k, side, float(fill)


def net_cents(fill, win, m=1.0):
    """Cents per contract after the rounded fee."""
    return ((1.0 if win else 0.0) - fill - gen6.fee(fill, C, m)) * 100


def load():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    mk = {}
    for t, close, res, strike in c.execute("select ticker, close_ts, result, strike from market where series='KXBTCD' and result in ('yes','no')"):
        mk[t] = (close, res, strike)
    evs = defaultdict(dict)
    res = {}
    for t, end, bc, ac, oi in c.execute("select ticker, end_ts, bid_c, ask_c, oi from candle where series='KXBTCD'"):
        m = mk.get(t)
        if m is None:
            continue
        close, r, strike = m
        evs[close].setdefault(strike, {})[close - end] = (bc, ac, oi)
        res[(close, strike)] = r
    return evs, res


def classify(evs):
    """List of (close, S, trigger) for eligible events, trailing-24h p90 on events closed in the 24 hours before this look."""
    stats = {}
    for close, ev in evs.items():
        s = oi_stat(ev)
        if s is not None:
            stats[close] = s
    out = []
    for close in sorted(stats):
        look_t = close - LOOK
        trail = [s for c2, s in stats.items() if look_t - TRAIL_S <= c2 <= look_t]
        if len(trail) < MIN_TRAIL:
            continue
        out.append((close, stats[close], stats[close] > p90(trail)))
    return out


def thirds(events):
    n = len(events)
    a, b = n // 3, 2 * n // 3
    return {"W1": events[:a], "W2": events[a:b], "W3": events[b:]}


def trades(evs, res, events, mode, trig):
    rows = []
    for close, s, t in events:
        if t != trig:
            continue
        p = pick(evs[close], mode)
        if p is None:
            continue
        k, side, fill = p
        win = res[(close, k)] == side
        rows.append({"close": close, "strike": k, "side": side, "fill": fill, "win": win,
                     "net": net_cents(fill, win), "net12": net_cents(fill, win, 1.2)})
    return rows


def summ(rows):
    if not rows:
        return {"n": 0}
    w = [r for r in rows if r["win"]]
    l = [r for r in rows if not r["win"]]
    gw = sum(r["net"] + 0 for r in rows if r["net"] > 0)
    gl = -sum(r["net"] for r in rows if r["net"] < 0)
    gw12 = sum(r["net12"] for r in rows if r["net12"] > 0)
    gl12 = -sum(r["net12"] for r in rows if r["net12"] < 0)
    z = cluster_mean_z([(str(r["close"] // 86400), r["net"]) for r in rows])[2] if len(rows) > 2 else None
    return {"n": len(rows), "win": len(w) / len(rows), "avg_fill": mean(r["fill"] for r in rows),
            "pf": (gw / gl if gl else None), "pf12": (gw12 / gl12 if gl12 else None),
            "mean_c": mean(r["net"] for r in rows), "z": z,
            "avg_win_c": mean(r["net"] for r in w) if w else None, "avg_loss_c": mean(r["net"] for r in l) if l else None}


def counts():
    evs, res = load()
    ev = classify(evs)
    th = thirds(ev)
    out = {"events_with_candles": len(evs), "eligible": len(ev), "triggers": sum(1 for e in ev if e[2])}
    for w, lst in th.items():
        out[w] = {"eligible": len(lst), "triggers": sum(1 for e in lst if e[2]),
                  "first": lst[0][0] if lst else None, "last": lst[-1][0] if lst else None}
        for mode in "AB":
            out[w]["A_B_pickable_trigger_" + mode] = sum(1 for e in lst if e[2] and pick(evs[e[0]], mode))
            out[w]["pickable_control_" + mode] = sum(1 for e in lst if not e[2] and pick(evs[e[0]], mode))
    return out


def score():
    if OUT.exists():
        sys.exit("oihr1 score already run; refusing")
    evs, res = load()
    ev = classify(evs)
    th = thirds(ev)
    r = {}
    for mode in "AB":
        for w in ("W1", "W2"):
            r[f"{mode}_{w}_trig"] = summ(trades(evs, res, th[w], mode, True))
            r[f"{mode}_{w}_ctrl"] = summ(trades(evs, res, th[w], mode, False))
        tp = trades(evs, res, th["W1"] + th["W2"], mode, True)
        r[f"{mode}_pooled_trig"] = summ(tp)
        r[f"{mode}_pooled_ctrl"] = summ(trades(evs, res, th["W1"] + th["W2"], mode, False))
    OUT.write_text(json.dumps(r, indent=1, default=str))
    return r


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "counts"
    print(json.dumps(counts() if cmd == "counts" else score(), indent=1, default=str))
