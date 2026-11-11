"""OI1 (workers/OI1_PROTOCOL.md): cheap side after an open-interest surge. Development only (first two thirds of each series by close time); held-out is not read here."""
import sqlite3, collections, math, sys
sys.path.insert(0, "src/scalper")
import leg1
def fee(p): return 0.07 * p * (1 - p)
SRC = [("BTC", "data/hist15/KXBTC15M.sqlite", None), ("ETH", "data/hist15/KXETH15M.sqlite", None), ("XRP", "data/alts2.sqlite", "KXXRP15M")]
N = 5206
from statistics import NormalDist
zb = NormalDist().inv_cdf(1 - 0.05 / N); print("N %d z bar %.2f" % (N, zb))
for name, db, ser in SRC:
    c = sqlite3.connect(db)
    q = "select ticker,close_ts,result from market where result in ('yes','no') and n_candles>0" + (" and series='%s'" % ser if ser else "")
    mk = {t: (ct, r) for t, ct, r in c.execute(q)}
    by = collections.defaultdict(list)
    cq = "select ticker,end_ts,bid_c,ask_c,oi from candle" + (" where series='%s'" % ser if ser else "")
    for tk, ts, b, a, oi in c.execute(cq):
        if tk in mk and b is not None and a is not None and oi is not None: by[tk].append((ts, b, a, oi))
    order = sorted(mk, key=lambda t: mk[t][0]); dev = set(order[:2 * len(order) // 3])
    cells = {"SURGE": collections.defaultdict(list), "CONTROL": collections.defaultdict(list)}
    for tk in dev:
        v = sorted(by.get(tk, []))
        ct, res = mk[tk]
        pick = None
        for x in v:
            if 570 <= ct - x[0] <= 640: pick = x
        if not pick: continue
        ts, b, a, oi = pick
        if b <= 0 or a >= 1 or a <= b or a - b > 0.03: continue
        prev = [x for x in v if abs((ts - 180) - x[0]) <= 8]
        if not prev: continue
        oi_prev = min(prev, key=lambda x: abs((ts - 180) - x[0]))[3]
        grp = "SURGE" if (oi_prev >= 100 and oi >= 1.10 * oi_prev) else "CONTROL"
        ya, na = a, 1 - b
        side, p = (("yes", ya) if ya <= na else ("no", na))
        if not (0.04 <= p <= 0.30): continue
        band = (0.04, 0.12) if p < 0.12 else (0.12, 0.30)
        cells[grp][band].append((tk, (1.0 if res == side else 0.0) - p - fee(p)))
    for grp in ("SURGE", "CONTROL"):
        for band, v in sorted(cells[grp].items()):
            if len(v) < 5: print(name, grp, band, "n", len(v), "too few"); continue
            n, ncl, m, z = leg1.clustered(v); x = [y for _, y in v]; w = sum(t for t in x if t > 0); l = -sum(t for t in x if t < 0)
            print("%-4s %-8s %.2f-%.2f n %4d PF %.2f mean %+.2fc z %.2f" % (name, grp, band[0], band[1], n, w / l if l > 0 else 99, 100 * m, z))
