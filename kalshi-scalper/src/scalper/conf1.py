"""CONF1 (README, Pre-registration: CONF1): confluence filters on L1's entries (ladder, twin, tape). Research only.
Usage: python -m scalper.conf1 run (once)
"""
from __future__ import annotations

import math
import sqlite3
import sys
from collections import defaultdict

from .calibration import cluster_mean_z
from .gen1 import _norm_ppf
from .paths import DATA_DIR

RESULT = DATA_DIR / "conf1_result.txt"
TWIN = {"KXBTC15M": "KXETH15M", "KXETH15M": "KXBTC15M", "KXGOLD15M": "KXSILVER15M", "KXSILVER15M": "KXGOLD15M"}
LEFT, BAND = 360, (0.88, 0.97)
N_PRIOR = 438_613


def fee(p, c=1, m=1.0):
    return math.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def entries():
    from . import feat1 as F
    from .flat_r import load_rep
    from .fwd_reads import load_fresh
    from .hs1 import load
    mk = {}
    for m in load() + load_fresh() + load_rep():
        if m[1].endswith("15M") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), LEFT)
    out = []
    for r in rows:
        p = r["price"]; won = r["net"] + p + 0.07 * p * (1 - p)
        out.append({"series": r["series"], "close": r["close_ts"], "side": r["side"], "p": p, "won": round(won), "strike": None})
    return out


def quotes_at():
    """(series, close, t) -> (yes bid, yes ask) from every 15 minute candle file."""
    from .gen2 import load_all
    M = load_all()
    Q = {}
    for tk, (series, strike, close, cs, res) in M.items():
        for t in (close - LEFT, close - LEFT - 900):
            q = cs.get(t)
            if q:
                Q[(series, close, t)] = (q[0], q[1])
    return Q


def ladder_quotes():
    """(close, strike) -> (bid, ask) at 6 minutes before the close, Bitcoin hourly ladder (look-ahead-free file)."""
    out = defaultdict(list)
    try:
        db = sqlite3.connect(DATA_DIR / "lad2.sqlite")
        for tk, close, strike in db.execute("select ticker, close_ts, strike from market"):
            r = db.execute("select bid_c, ask_c from candle where ticker=? and end_ts=?", (tk, close - LEFT)).fetchone()
            if r and r[0] is not None and r[1] is not None:
                out[close].append((strike, r[0], r[1]))
    except sqlite3.OperationalError:
        pass
    return out


def main():
    if RESULT.exists():
        print("Refusing to run again"); return
    E = entries(); Q = quotes_at(); LQ = ladder_quotes()
    spot_strike = {}
    db5 = sqlite3.connect(DATA_DIR / "search5k.sqlite")
    btc = {ts // 1000: c for c, ts in db5.execute("select c, ts from bar where cur='BTC'")}
    closes = sorted({e["close"] for e in E}); cut = (closes[len(closes) // 3], closes[2 * len(closes) // 3])
    win = lambda c: 0 if c < cut[0] else (1 if c < cut[1] else 2)

    def side_price(q, side):
        return q[1] if side == "yes" else round(1 - q[0], 4)

    def keep_twin(e):
        tw = TWIN.get(e["series"])
        q = Q.get((tw, e["close"], e["close"] - LEFT)) if tw else None
        return None if q is None else BAND[0] <= side_price(q, e["side"]) <= BAND[1]

    # market-wide move: precompute per close the YES-mid change over the previous 15 minutes for every series
    move = defaultdict(dict)
    for (s, c, t), q in Q.items():
        if t == c - LEFT and (s, c, t - 900) in Q:
            a, b = q, Q[(s, c, t - 900)]
            move[c][s] = (a[0] + a[1]) / 2 - (b[0] + b[1]) / 2

    def keep_tape2(e):
        others = [v for s, v in move.get(e["close"], {}).items() if s != e["series"]]
        if not others:
            return None
        m = sum(others) / len(others)
        return (m if e["side"] == "yes" else -m) > 0

    def keep_ladder(e):
        if e["series"] != "KXBTC15M" or e["close"] % 3600 != 0 or e["close"] not in LQ:
            return None
        s = btc.get(e["close"] - 900 - 60)  # the 15 minute strike is the average before the window opened; nearest spot used as its proxy
        if s is None:
            return None
        k, b, a = min(LQ[e["close"]], key=lambda x: abs(x[0] - s))
        return side_price((b, a), e["side"]) >= 0.88

    zbar = _norm_ppf(1 - 0.05 / (N_PRIOR + 3))
    pfv = lambda xs: (sum(x for x in xs if x > 0) / -sum(x for x in xs if x < 0)) if any(x < 0 for x in xs) else 99.0
    net = lambda e, m=1.0: e["won"] - e["p"] - fee(e["p"], m=m)
    lines = [f"CONF1: {len(E)} L1 entries, {len(closes)} closes; Bonferroni z bar {zbar:.2f}"]
    for name, fn in (("LADDER", keep_ladder), ("TWIN", keep_twin), ("TAPE", keep_tape2)):
        ok_all = True; parts = []
        for w in range(3):
            ew = [e for e in E if win(e["close"]) == w]
            dec = [(e, fn(e)) for e in ew]
            base = [net(e) for e, k in dec if k is not None]
            kept = [e for e, k in dec if k]; rem = [e for e, k in dec if k is False]
            kv = [net(e) for e in kept]; rv = [net(e) for e in rem]; ks = [net(e, 1.2) for e in kept]
            nc = len({e["close"] for e in kept})
            _, _, z = cluster_mean_z([(e["close"] // 86400, net(e)) for e in kept]) if len(kept) > 1 else (0, 0, 0.0)
            pk = pfv(kv) if kv else 0.0
            parts.append(f"{['discovery', 'validation', 'holdout'][w]}: parent (where defined) PF {pfv(base) if base else 0:.2f} n={len(base)} | kept PF {pk:.2f} n={len(kept)} closes {nc} stress {pfv(ks) if ks else 0:.2f} z {z:+.2f} | removed PF {pfv(rv) if rv else 0:.2f} n={len(rem)} net {100 * sum(rv) / max(len(rv), 1):+.2f}c")
            ok_all = ok_all and nc >= 30 and pk >= 1.5 and (pfv(ks) if ks else 0) >= 1.2 and (w != 1 or z >= zbar)
            if nc < 30 and name == "LADDER":
                ok_all = None if ok_all is not False else ok_all
        v = "NOT_YET_FALSIFIED" if ok_all else ("NOT_ENOUGH_DATA" if ok_all is None else "FALSIFIED")
        lines.append(f"  {name} {v}")
        lines += ["    " + p for p in parts]
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main() if len(sys.argv) > 1 and sys.argv[1] == "run" else print(__doc__)
