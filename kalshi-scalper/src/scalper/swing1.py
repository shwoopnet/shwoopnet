"""SWING1: in-play swing overreaction, cheap side, held to settlement.

Registration: workers/SWING1_REGISTRATION.md (sha256 prefix 3092cee9eabff7e9).
Reads data/espn1.sqlite only (no network).  python -m scalper.swing1 score
"""
from __future__ import annotations

import math
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "data" / "espn1.sqlite"
CAP = {"KXNCAAFGAME": 16200, "KXMLBGAME": 14400}
W2_START = int(datetime(2026, 9, 13, 1, tzinfo=timezone.utc).timestamp())
W3_START = int(datetime(2026, 10, 3, 16, tzinfo=timezone.utc).timestamp())
SWING, CTRL_DROP, LO, HI, C = 0.25, 0.10, 0.05, 0.30, 10
PHASES = 3


def fee(p: float, c: int = C) -> float:
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win: bool, ask: float, mult: float = 1.0) -> float:
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def valid(q):
    return q is not None and 0 <= q[0] < q[1] <= 1 and q[1] - q[0] <= 0.10


def mid(q):
    return (q[0] + q[1]) / 2


def drop(cand, t):
    """Highest mid over valid candles ending t-300..t-60 minus mid at t; None if t invalid or no look-back."""
    q = cand.get(t)
    if not valid(q):
        return None
    ms = [mid(cand[s]) for s in range(t - 300, t, 60) if s in cand and valid(cand[s])]
    if not ms:
        return None
    return max(ms) - mid(q)


def scan_game(series, start, ca, cb, res_a):
    """Return (swing_trade or None, [control rows]). ca, cb: {end_ts: (bid, ask)}; res_a: True if A settled yes."""
    cap = CAP[series]
    sw, ctrls, swung = None, [], False
    for t in sorted(set(ca) | set(cb)):
        if t - 300 < start or t + 60 > start + cap:
            continue
        if (t + 60) not in ca or (t + 60) not in cb:
            continue
        da, db = drop(ca, t), drop(cb, t)
        if da is None or db is None:
            continue
        nxt = {"A": ca[t + 60], "B": cb[t + 60]}
        if not (valid(nxt["A"]) and valid(nxt["B"])):
            continue
        phase = min(PHASES - 1, int((t + 60 - start) / cap * PHASES))
        if da >= SWING or db >= SWING:
            swung = True
            if sw is None:
                f = "A" if da >= SWING else "B"
                ask = nxt[f][1]
                if LO <= ask <= HI:
                    win = res_a if f == "A" else (not res_a)
                    sw = dict(t=t, ask=ask, win=win, phase=phase)
        elif not swung and da < CTRL_DROP and db < CTRL_DROP:
            f = "A" if mid(ca[t]) <= mid(cb[t]) else "B"
            ask = nxt[f][1]
            if LO <= ask <= HI:
                win = res_a if f == "A" else (not res_a)
                ctrls.append(dict(t=t, ask=ask, win=win, phase=phase))
    return sw, ctrls


def band(ask):
    return min(4, int((ask - LO) / 0.05 + 1e-9))


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf")


def cluster_z(vals, days):
    """z of the mean with day clusters (sum per day)."""
    by = defaultdict(list)
    for v, d in zip(vals, days):
        by[d].append(v)
    n = len(vals)
    if n < 2 or len(by) < 2:
        return 0.0
    m = sum(vals) / n
    s = sum((sum(x - m for x in v)) ** 2 for v in by.values())
    se = math.sqrt(s) / n
    return m / se if se > 0 else 0.0


def load():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    res = {t: r == "yes" for t, r in c.execute("select ticker,result from kmarket")}
    games = c.execute(
        """select m.series,e.start_ts,m.home_ticker,m.away_ticker from match m
           join egame e on e.id=m.egame and e.series=m.series
           where m.series in ('KXNCAAFGAME','KXMLBGAME')""").fetchall()
    out = []
    for s, st, ha, aw in games:
        if ha not in res or aw not in res:
            continue
        cs = []
        for tk in (ha, aw):
            cs.append({t: (b, a) for t, b, a in c.execute(
                "select end_ts,bid,ask from candle where ticker=? and bid is not null and ask is not null", (tk,))})
        out.append((s, st, cs[0], cs[1], res[ha]))
    return out


def window(st):
    return 1 if st < W2_START else 2 if st < W3_START else 3


def summarize(trades, ctrl_cells, name, mult=1.0):
    xs = [net(t["win"], t["ask"], mult) for t in trades]
    ex = []
    for t, x in zip(trades, xs):
        cm = ctrl_cells.get((t["phase"], band(t["ask"])))
        if cm:
            ex.append(x - cm)
        else:
            ex.append(None)
    n = len(xs)
    if not n:
        return f"{name}: n 0"
    exv = [e for e in ex if e is not None]
    exd = [t["day"] for t, e in zip(trades, ex) if e is not None]
    return (f"{name}: n {n}, win {sum(t['win'] for t in trades)/n:.3f} vs mean ask {sum(t['ask'] for t in trades)/n:.3f}, "
            f"mean net {sum(xs)/n*100:+.2f}c, PF {pf(xs):.2f}, "
            f"excess {sum(exv)/max(1,len(exv))*100:+.2f}c (n {len(exv)}, z {cluster_z(exv, exd):+.2f})")


def main(mode="score"):
    games = load()
    trades, ctrls = [], []
    for s, st, ca, cb, ra in games:
        sw, cs = scan_game(s, st, ca, cb, ra)
        day = datetime.fromtimestamp(st, timezone.utc).date().isoformat()
        w = window(st)
        if sw:
            sw.update(day=day, w=w, series=s, st=st)
            trades.append(sw)
        # one control mean per game and cell
        g = defaultdict(list)
        for r in cs:
            g[(r["phase"], band(r["ask"]))].append(net(r["win"], r["ask"]))
        for k, v in g.items():
            ctrls.append((w, k, sum(v) / len(v), len(v)))
    dev = [t for t in trades if t["w"] in (1, 2)]
    cells = defaultdict(list)
    for w, k, m, n in ctrls:
        if w in (1, 2):
            cells[k].append(m)
    cc = {k: sum(v) / len(v) for k, v in cells.items()}
    print(f"games {len(games)}, swing trades W1 {sum(t['w']==1 for t in trades)} W2 {sum(t['w']==2 for t in trades)} (W3 not read)")
    lines = []
    for w in (1, 2):
        lines.append(summarize([t for t in dev if t["w"] == w], cc, f"W{w}"))
    lines.append(summarize(dev, cc, "W1+W2"))
    lines.append(summarize(dev, cc, "W1+W2 fees x1.2", 1.2))
    dv = sorted(dev, key=lambda t: t["st"])
    h = len(dv) // 2
    lines.append(summarize(dv[:h], cc, "half 1"))
    lines.append(summarize(dv[h:], cc, "half 2"))
    for s in CAP:
        lines.append(summarize([t for t in dev if t["series"] == s], cc, s))
    cn = [net(r[2] > -9 and True, 0) for r in []]
    ctl = [(m, n) for w, k, m, n in ctrls if w in (1, 2)]
    lines.append(f"control cells (game-cell means) n {len(ctl)}, mean net {sum(m for m,_ in ctl)/max(1,len(ctl))*100:+.2f}c")
    print("\n".join(lines))
    return lines


if __name__ == "__main__":
    main(*sys.argv[1:2])
