"""SINGLELEG1: calibration of single legs by series and price band (workers/SINGLELEG1_PROTOCOL.md).
Research only. Reads the local sqlite caches (no network). `cells` counts cells WITHOUT reading any outcome; `score` reads dev outcomes only;
`holdout` reads the last third for the pre-registered shortlist, once.
"""
import math, os, sys, sqlite3
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "..", "data")
SOURCES = [  # (file, market table, time column, result column, candle table)
    ("sports.sqlite", "market", "close_ts", "result", "candle"),
    ("sports1.sqlite", "market", "close_ts", "result", "candle"),
    ("nflcombo1.sqlite", "km", "close_ts", "result", "candle"),
    ("nflpc1.sqlite", "km", "close_ts", "result", "candle"),
]
LEAD = 4 * 3600
OPEN_MODE = False
MAX_SPREAD = 0.05
BANDS = [(0.05, 0.10), (0.10, 0.20), (0.20, 0.30), (0.30, 0.40), (0.40, 0.50), (0.50, 0.60), (0.60, 0.70), (0.70, 0.80), (0.80, 0.90), (0.90, 0.971)]
MIN_MARKETS = 100
MIN_CLUSTERS = 30
EDGE_MIN = 0.02       # dollars per contract after fee
N_PRIOR = 160
N_EXTRA = 0          # SINGLELEG2: hypotheses already counted before this run (600 after SINGLELEG1, plus earlier leads)


def fee_per_contract(p, c=10):
    return np.ceil(0.07 * c * p * (1 - p) * 100 - 1e-9) / c / 100.0   # dollars per contract


def load_markets():
    seen, out = set(), []
    for f, mt, tc, rc, ct in SOURCES:
        path = os.path.join(D, f)
        if not os.path.exists(path):
            continue
        db = sqlite3.connect(path)
        cols = [r[1] for r in db.execute("pragma table_info(%s)" % mt)]
        rows = db.execute("select ticker, series, %s, %s from %s where %s in ('yes','no')" % (tc, rc, mt, rc)).fetchall()
        # decision quote: last candle at least LEAD before the close, both sides quoted, spread <= MAX_SPREAD
        for tk, ser, t, res in rows:
            if tk in seen:
                continue
            if OPEN_MODE:
                r = db.execute("select bid_c, ask_c from %s where ticker=? and end_ts<? and bid_c>0 and ask_c<1 and ask_c-bid_c<=? order by end_ts asc limit 1" % ct, (tk, t, MAX_SPREAD)).fetchone()
            else:
                r = db.execute("select bid_c, ask_c from %s where ticker=? and end_ts<=? order by end_ts desc limit 1" % ct, (tk, t - LEAD)).fetchone()
            if not r or r[0] is None or r[1] is None:
                continue
            b, a = float(r[0]), float(r[1])
            if b <= 0 or a >= 1 or a - b > MAX_SPREAD or a <= b - 1e-9:
                continue
            seen.add(tk)
            ev = tk.rsplit("-", 1)[0]
            out.append((ser, tk, ev, t, b, a, res))
        db.close()
    return out


def cells_of(rows, subset=None):
    """cell -> list of (event, net dollars) for both sides; cell = (series, side, band)."""
    cells = defaultdict(list)
    for ser, tk, ev, t, b, a, res in rows:
        if subset is not None and not subset(ser, t):
            continue
        for side, price, won in (("yes", a, res == "yes"), ("no", 1 - b, res == "no")):
            for lo, hi in BANDS:
                if lo <= price < hi:
                    net = (1.0 if won else 0.0) - price - float(fee_per_contract(price))
                    cells[(ser, side, (lo, hi))].append((ev, net))
    return cells


def split_time(rows):
    by = defaultdict(list)
    for r in rows:
        by[r[0]].append(r[3])
    cut = {s: np.quantile(ts, 2 / 3.0) for s, ts in by.items()}
    return cut


def clustered(vals):
    by = defaultdict(float)
    cnt = defaultdict(int)
    for ev, x in vals:
        by[ev] += x
        cnt[ev] += 1
    n = sum(cnt.values())
    mean = sum(by.values()) / n
    # cluster-robust se of the mean (events are the clusters)
    se = math.sqrt(sum((by[e] - mean * cnt[e]) ** 2 for e in by)) / n
    return n, len(by), mean, (mean / se if se > 0 else 0.0)


def cmd_cells():
    rows = load_markets()
    cut = split_time(rows)
    dev = cells_of(rows, lambda s, t: t <= cut[s])
    series = sorted({r[0] for r in rows})
    print("markets with a usable decision quote:", len(rows), "series:", len(series))
    nz = {k: len(v) for k, v in dev.items() if len(v) >= MIN_MARKETS}
    print("cells (series x side x band) with at least %d dev markets: %d" % (MIN_MARKETS, len(nz)))
    print("potential cells:", len(series) * 2 * len(BANDS))
    return len(series) * 2 * len(BANDS), len(nz)


def cmd_score():
    rows = load_markets()
    cut = split_time(rows)
    dev = cells_of(rows, lambda s, t: t <= cut[s])
    pot = len({r[0] for r in rows}) * 2 * len(BANDS)
    N = N_PRIOR + N_EXTRA + pot
    z_bar = {1000: 3.72}.get(1000)
    # one-sided normal quantile for alpha = 0.05 / N
    from statistics import NormalDist
    z_bar = NormalDist().inv_cdf(1 - 0.05 / N)
    print("N = %d (160 prior + %d earlier + %d cells), z bar %.2f" % (N, N_EXTRA, pot, z_bar))
    short = []
    allc = []
    for k, v in dev.items():
        if len(v) < MIN_MARKETS:
            continue
        n, ncl, mean, z = clustered(v)
        allc.append((mean, k, n, ncl, z))
        if ncl >= MIN_CLUSTERS and mean >= EDGE_MIN and z >= z_bar:
            short.append((mean, k, n, ncl, z))
    allc.sort(reverse=True)
    print("top 12 dev cells by net edge (dollars per contract, after C=10 fee):")
    for mean, k, n, ncl, z in allc[:12]:
        print("  %-12s %-3s %.2f-%.2f  n %5d events %4d  net %+0.3f  z %.2f" % (k[0], k[1], k[2][0], k[2][1], n, ncl, mean, z))
    print("SHORTLIST (edge >= 2c, z >= bar, >= %d events): %d" % (MIN_CLUSTERS, len(short)))
    for mean, k, n, ncl, z in sorted(short, reverse=True):
        print("  ", k, n, ncl, round(mean, 4), round(z, 2))
    return short


def cmd_holdout(shortlist):
    rows = load_markets()
    cut = split_time(rows)
    ho = cells_of(rows, lambda s, t: t > cut[s])
    print("HOLDOUT read once for the shortlist:")
    for mean, k, n, ncl, z in shortlist:
        v = ho.get(k, [])
        if len(v) < 20:
            print("  ", k, "dev net %+0.3f" % mean, "holdout n", len(v), "NOT_ENOUGH_DATA")
        else:
            hn, hc, hm, hz = clustered(v)
            print("  ", k, "dev net %+0.3f" % mean, "holdout n %d events %d net %+0.3f z %.2f" % (hn, hc, hm, hz))


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "cells"
    for a in sys.argv[2:]:
        if a.startswith("--lead="):
            v = a.split("=", 1)[1]
            if v == "open":
                OPEN_MODE = True
            else:
                LEAD = int(v)
        if a.startswith("--prior="):
            N_EXTRA = int(a.split("=", 1)[1])
    if c == "cells":
        cmd_cells()
    elif c == "score":
        sl = cmd_score()
        if "--holdout" in sys.argv and sl:
            cmd_holdout(sl)
