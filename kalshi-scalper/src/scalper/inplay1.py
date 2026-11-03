"""INPLAY1: ESPN in-play win probability vs Kalshi cheap-side ask at fixed looks.

Registration: workers/INPLAY1_REGISTRATION.md.  Reads data/espn1.sqlite only.
Cheap side only; no favourite-side result is computed.  python -m scalper.inplay1 score
"""
from __future__ import annotations

import bisect
import math
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "data" / "espn1.sqlite"
SERIES = ("KXNCAAFGAME", "KXMLBGAME")
W2_START = int(datetime(2026, 9, 13, 1, tzinfo=timezone.utc).timestamp())
CUT = int(datetime(2026, 10, 3, 16, tzinfo=timezone.utc).timestamp())
LOOKS = (3600, 5400, 7200)
D, LO, HI, RATIO, C = 180, 0.03, 0.30, 3.0, 10


def fee(p, c=C):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win, ask, mult=1.0):
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def valid(q):
    return q is not None and 0 <= q[0] < q[1] <= 1 and q[1] - q[0] <= 0.10


def prob_at(rows, t):
    """rows sorted [(wall_ts, home_p, tie_p)]; last row with wall_ts <= t, or None."""
    i = bisect.bisect_right([r[0] for r in rows], t)
    return rows[i - 1] if i else None


def scan_game(start, rows, ca, cb, res_a):
    """ca/cb {end_ts:(bid,ask)} for home/away; returns (trade or None, [control rows])."""
    trade, ctrl = None, []
    for k in LOOKS:
        L = start + k
        r = prob_at(rows, L - D)
        if r is None or L - D - r[0] > 600:
            continue
        ph = r[1]
        pa = 1 - r[1] - r[2]
        for q, pe, win in ((ca.get(L), ph, res_a), (cb.get(L), pa, not res_a)):
            if not valid(q) or not (LO <= q[1] <= HI):
                continue
            row = dict(k=k, ask=q[1], pe=pe, mid=(q[0] + q[1]) / 2, win=win)
            ctrl.append(row)
            if trade is None and pe >= RATIO * q[1]:
                trade = row
    return trade, ctrl


def band(a):
    return min(4, int((a - LO) / 0.054 + 1e-9))


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf")


def cluster_z(vals, days):
    by = defaultdict(list)
    for v, d in zip(vals, days):
        by[d].append(v)
    n = len(vals)
    if n < 2 or len(by) < 2:
        return 0.0
    m = sum(vals) / n
    s = sum(sum(x - m for x in v) ** 2 for v in by.values())
    se = math.sqrt(s) / n
    return m / se if se > 0 else 0.0


def load():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    res = {t: r == "yes" for t, r in c.execute("select ticker,result from kmarket")}
    games = c.execute(
        """select m.series,m.egame,e.start_ts,m.home_ticker,m.away_ticker from match m
           join egame e on e.id=m.egame and e.series=m.series
           where m.series in ('KXNCAAFGAME','KXMLBGAME') and e.start_ts < ?""", (CUT,)).fetchall()
    out = []
    for s, eg, st, ha, aw in games:
        if ha not in res or aw not in res:
            continue
        rows = c.execute("select wall_ts,home_p,tie_p from erow where egame=? and wall_ts is not null order by wall_ts", (eg,)).fetchall()
        if not rows:
            continue
        cs = [{t: (b, a) for t, b, a in c.execute(
            "select end_ts,bid,ask from candle where ticker=? and bid is not null and ask is not null", (tk,))} for tk in (ha, aw)]
        out.append((s, st, rows, cs[0], cs[1], res[ha]))
    return out


def brier(rows):
    if not rows:
        return "n 0"
    n = len(rows)
    e = sum((r["pe"] - r["win"]) ** 2 for r in rows) / n
    m = sum((r["mid"] - r["win"]) ** 2 for r in rows) / n
    return f"n {n}, Brier ESPN {e:.4f} vs Kalshi mid {m:.4f}"


def summ(name, tr, mult=1.0):
    n = len(tr)
    if not n:
        return f"{name}: n 0"
    xs = [net(t["win"], t["ask"], mult) for t in tr]
    return (f"{name}: n {n}, win {sum(t['win'] for t in tr)/n:.3f} vs ask {sum(t['ask'] for t in tr)/n:.3f} "
            f"vs ESPN {sum(t['pe'] for t in tr)/n:.3f}, mean net {sum(xs)/n*100:+.2f}c, PF {pf(xs):.2f}, "
            f"z {cluster_z(xs, [t['day'] for t in tr]):+.2f}")


def main():
    games = load()
    trades, ctrl = [], []
    for s, st, rows, ca, cb, ra in games:
        day = datetime.fromtimestamp(st, timezone.utc).date().isoformat()
        w = 1 if st < W2_START else 2
        tr, cs = scan_game(st, rows, ca, cb, ra)
        if tr:
            tr.update(day=day, w=w, st=st, series=s)
            trades.append(tr)
        for r in cs:
            r.update(day=day, w=w)
            ctrl.append(r)
    print(f"games {len(games)} (before cut), cheap-side rows {len(ctrl)}, treated trades {len(trades)} "
          f"(W1 {sum(t['w']==1 for t in trades)}, W2 {sum(t['w']==2 for t in trades)})")
    out = []
    for w in (1, 2):
        out.append(summ(f"W{w}", [t for t in trades if t["w"] == w]))
    out.append(summ("W1+W2", trades))
    out.append(summ("W1+W2 fees x1.2", trades, 1.2))
    dv = sorted(trades, key=lambda t: t["st"])
    h = len(dv) // 2
    out.append(summ("half 1", dv[:h]))
    out.append(summ("half 2", dv[h:]))
    for s in SERIES:
        out.append(summ(s, [t for t in trades if t["series"] == s]))
    out.append(summ("control (all cheap sides at the looks)", ctrl))
    out.append("control by ask band: " + "; ".join(
        f"band{b}: n {sum(1 for r in ctrl if band(r['ask'])==b)} net "
        f"{(lambda xs: sum(xs)/len(xs)*100 if xs else 0)([net(r['win'], r['ask']) for r in ctrl if band(r['ask'])==b]):+.2f}c" for b in range(5)))
    out.append("calibration cheap-side rows: " + brier(ctrl))
    n_ratio_rows = [r for r in ctrl if r["pe"] >= RATIO * r["ask"]]
    out.append(f"rows with ratio >= 3 (any look): {len(n_ratio_rows)}; " + brier(n_ratio_rows))
    nm = len({(t['st']) for t in trades})
    span = (max(t["st"] for t in trades) - min(t["st"] for t in trades)) / 2592000 if trades else 0
    out.append(f"trades per month of file span ~{len(trades)/max(span,1e-9):.1f}" if trades else "no trades")
    print("\n".join(out))
    return out


if __name__ == "__main__":
    main()
