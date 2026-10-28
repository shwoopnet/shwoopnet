"""SCALP1 and SCALP2 (README, Pre-registration: SCALP1 and SCALP2). Research only; nothing here means trade.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.scalp12 run   (once; a second run is refused)
"""
from __future__ import annotations

import math
import sqlite3
import sys
from datetime import datetime, timezone

from .calibration import cluster_mean_z
from .paths import DATA_DIR

RESULT = DATA_DIR / "scalp12_result.txt"
SOURCES = ["book", "l1b", "fresh"]
SERIES = ("KXBTC15M", "KXETH15M", "KXGOLD15M")
CUR = {"KXBTC15M": "BTC", "KXETH15M": "ETH"}
FIRST, LAST, FLAT = 600, 300, 120
TARGET, STOP = 0.08, 0.06
EDGE, LO1, HI1 = 0.08, 0.15, 0.70
DROP, LO2, HI2 = 0.15, 0.15, 0.40
MIN_N, MIN_DAYS, BAR_PF, BAR_Z = 300, 40, 1.20, 2.0
BASE, UNIT, LOSS_STOP = 500.0, 11, 0.05


def fee(p: float, m: float = 1.0) -> float:
    return m * 0.07 * p * (1 - p)


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def load():
    spot = {}
    db = sqlite3.connect(DATA_DIR / "search5k.sqlite")
    for cur, ts, c in db.execute("select cur, ts, c from bar"):
        spot[(cur, ts // 1000)] = c
    M = {}
    for name in SOURCES:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        by = {}
        for tk, series, strike, close_ts, res in db.execute("select ticker, series, strike, close_ts, result from market where series in (?,?,?)", SERIES):
            by[tk] = (series, strike, close_ts, res)
        for tk, (series, strike, close_ts, res) in by.items():
            if tk in M:
                continue
            cs = {r[0]: (r[1], r[2]) for r in db.execute("select end_ts, bid_c, ask_c from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if cs:
                M[tk] = (series, strike, close_ts, cs)
    return M, spot


def side_quotes(q, side):
    bid_c, ask_c = q
    return (bid_c, ask_c) if side == "yes" else (round(1 - ask_c, 4), round(1 - bid_c, 4))  # (bid, ask)


def sigma1(spot, cur, t):
    rs = []
    prev = spot.get((cur, t - 60))
    for k in range(1, 61):
        cur_p = spot.get((cur, t - 60 - 60 * k))
        if prev is None or cur_p is None or cur_p <= 0:
            return None
        rs.append(math.log(prev / cur_p)); prev = cur_p
    mu = sum(rs) / len(rs)
    return math.sqrt(sum((r - mu) ** 2 for r in rs) / (len(rs) - 1))


def exit_trade(cs, side, e, t, close_ts):
    last = None
    for k in sorted(k for k in cs if t < k <= close_ts - FLAT):
        b = side_quotes(cs[k], side)[0]
        last = b
        if b >= e + TARGET - 1e-9 or b <= e - STOP + 1e-9:
            return b
    return last


def trades(M, spot):
    out = {"S1": [], "S2": []}
    for tk, (series, strike, close_ts, cs) in M.items():
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        done1 = done2 = False
        for t in range(close_ts - FIRST, close_ts - LAST + 1, 60):
            q = cs.get(t)
            if q is None:
                continue
            if series in CUR and not done1:
                cur = CUR[series]; s = spot.get((cur, t - 60)); sg = sigma1(spot, cur, t)
                if s and sg and strike:
                    mins = (close_ts - t) / 60
                    pyes = phi(math.log(s / strike) / (sg * math.sqrt(mins)))
                    best = None
                    for side, fair in (("yes", pyes), ("no", 1 - pyes)):
                        ask = side_quotes(q, side)[1]
                        if LO1 <= ask <= HI1 and fair - ask >= EDGE and (best is None or fair - ask > best[0]):
                            best = (fair - ask, side, ask)
                    if best:
                        _, side, e = best; b = exit_trade(cs, side, e, t, close_ts)
                        if b is not None:
                            out["S1"].append((day, close_ts, series, e, b)); done1 = True
            if not done2:
                p = cs.get(t - 120)
                if p is not None:
                    best = None
                    for side in ("yes", "no"):
                        drop = side_quotes(p, side)[0] - side_quotes(q, side)[0]; ask = side_quotes(q, side)[1]
                        if drop >= DROP and LO2 <= ask <= HI2 and (best is None or drop > best[0]):
                            best = (drop, side, ask)
                    if best:
                        _, side, e = best; b = exit_trade(cs, side, e, t, close_ts)
                        if b is not None:
                            out["S2"].append((day, close_ts, series, e, b)); done2 = True
    return out


def stats(rows, m=1.0):
    nets = [(d, b - e - fee(e, m) - fee(b, m)) for d, _, _, e, b in rows]
    if not nets:
        return None
    days = sorted({d for d, _ in nets}); cut = days[len(days) // 2]
    def pf(xs):
        w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0); return w / l if l else 99.0
    mean, _, z = cluster_mean_z(nets)
    allx = [x for _, x in nets]
    h1 = [x for d, x in nets if d < cut]; h2 = [x for d, x in nets if d >= cut]
    loss = sum(1 for x in allx if x < 0) / len(allx)
    return {"n": len(nets), "days": len(days), "mean": mean, "z": z, "pf": pf(allx), "pf1": pf(h1), "pf2": pf(h2), "loss": loss, "stress_pf": None}


def account(rows):
    bal = BASE; stopped = {}; pnl_day = {}
    for d, ts, _, e, b in sorted(rows, key=lambda r: (r[0], r[1])):
        if pnl_day.get(d, 0) <= -LOSS_STOP * BASE:
            continue
        pnl = UNIT * (b - e - fee(e) - fee(b)); pnl_day[d] = pnl_day.get(d, 0) + pnl; bal += pnl
    return bal


def main(argv):
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    M, spot = load(); T = trades(M, spot)
    lines = [f"SCALP1/SCALP2: {len(M)} markets"]
    verdicts = {}
    for name, rows in T.items():
        s = stats(rows); st = stats(rows, 1.2)
        if not s:
            verdicts[name] = "NOT_ENOUGH_DATA"; lines.append(f"{name}: no entries"); continue
        ok = s["n"] >= MIN_N and s["days"] >= MIN_DAYS and st["pf"] >= 1.0 and s["pf"] >= BAR_PF and s["pf1"] > 1 and s["pf2"] > 1 and s["z"] >= BAR_Z
        v = "NOT_YET_FALSIFIED" if ok else ("NOT_ENOUGH_DATA" if s["n"] < MIN_N or s["days"] < MIN_DAYS else "FALSIFIED")
        verdicts[name] = v
        lines.append(f"{name} {v}: PF {s['pf']:.2f} (halves {s['pf1']:.2f}/{s['pf2']:.2f}, stressed {st['pf']:.2f}) over {s['days']} days, n={s['n']}, loss rate {100 * s['loss']:.0f}%, net {100 * s['mean']:+.2f}c per contract, z {s['z']:+.2f}; $500 account with 11 contracts ends at ${account(rows):.2f}")
        for series in SERIES:
            r = [x for x in rows if x[2] == series]
            q = stats(r)
            if q:
                lines.append(f"    {series}: PF {q['pf']:.2f}, n={q['n']}, loss rate {100 * q['loss']:.0f}%, net {100 * q['mean']:+.2f}c")
    lines.insert(1, f"VERDICTS {verdicts}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
