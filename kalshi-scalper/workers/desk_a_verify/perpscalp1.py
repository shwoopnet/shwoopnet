"""PERPSCALP1 reader (Desk A, Nov 15 2026), built to PERPSCALP1_HAND_CASE_NOV15.md (committed first at a620e1726). Offline; reads 1 minute perp candle files and sends nothing.
  PERPSCALP_READ=1 python3 -I perpscalp1.py <out.json> <file.csv.gz> [<file.csv.gz> ...]      DEFAULT-CLOSED. Files: perp-data kalshi1m/<date>.csv.gz (columns ticker, end_period_ts, bid_close, ask_close, ...). Names: the tight six. Label: "upper bound, not fill-checked"; fee 12 bps a leg is an ASSUMPTION (docs/PERPS_THEORY.md, not confirmed against Kalshi's fee page)."""
import sys, os, csv, gzip, io, json, math, time, collections
NAMES = ("KXSPYPERP", "KXQQQPERP", "KXUS500PERP", "KXUSTECH100PERP", "KXNVDAPERP", "KXAAPLPERP")
FEE = 0.0012; HAIRCUTS = (0.0, 0.0001, 0.0002); WIN = 60; MIN_RET = 40; LAG = 300; HOLD = 600; PAUSE = 900; MAXSPREAD = 0.003
H0, H1 = 14 * 3600 + 35 * 60, 20 * 3600 + 45 * 60
def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 and w > 0 else (w / l if l else float("nan"))
def in_hours(t):
    g = time.gmtime(t)
    return g.tm_wday < 5 and H0 <= g.tm_hour * 3600 + g.tm_min * 60 + g.tm_sec <= H1
def signals(cs):
    """cs: sorted [(end_ts, bid, ask)] of one name (complete quotes only). Yields (index, direction +1/-1, sigma5, mid) per entry candle (the pause and hours rules applied)."""
    idx = {t: i for i, (t, b, a) in enumerate(cs)}; last = None
    for i, (t, b, a) in enumerate(cs):
        if not in_hours(t) or (last is not None and t < last + PAUSE): continue
        j = idx.get(t - LAG)
        if j is None: continue
        mid = (b + a) / 2
        if (a - b) / mid > MAXSPREAD: continue
        rs = []                                                         # 1 minute log returns of the 60 candles ending LAG before t
        end = t - LAG
        for k in range(WIN - 1):
            t1, t0 = end - 60 * k, end - 60 * (k + 1)
            if t1 in idx and t0 in idx:
                m1 = (cs[idx[t1]][1] + cs[idx[t1]][2]) / 2; m0 = (cs[idx[t0]][1] + cs[idx[t0]][2]) / 2; rs.append(math.log(m1 / m0))
        if len(rs) < MIN_RET: continue
        mu = sum(rs) / len(rs); sd = math.sqrt(sum((x - mu) ** 2 for x in rs) / (len(rs) - 1)); s5 = sd * math.sqrt(5)
        mj = (cs[j][1] + cs[j][2]) / 2; mv = math.log(mid / mj)
        if s5 > 0 and abs(mv) >= 3 * s5: last = t; yield i, (1 if mv > 0 else -1), s5, mid
def trade(cs, i, side, s5, mid, h):
    """side +1 long, -1 short. Returns (entry, exit, kind)."""
    t, b, a = cs[i]
    entry = a * (1 + h) if side > 0 else b * (1 - h)
    tgt, stp = (mid * (1 + s5), mid * (1 - s5)) if side > 0 else (mid * (1 - s5), mid * (1 + s5))
    last = None
    for k in range(i + 1, len(cs)):
        tk, bk, ak = cs[k]
        if tk > t + HOLD: break
        last = k
        if side > 0 and (bk >= tgt or bk <= stp): return entry, bk * (1 - h), "target" if bk >= tgt else "stop"
        if side < 0 and (ak <= tgt or ak >= stp): return entry, ak * (1 + h), "target" if ak <= tgt else "stop"
    if last is None: return None
    tk, bk, ak = cs[last]
    return entry, (bk * (1 - h) if side > 0 else ak * (1 + h)), "time"
def net(entry, ex, side): return ((ex - entry) / entry if side > 0 else (entry - ex) / entry) - 2 * FEE
def load(paths):
    q = collections.defaultdict(dict)
    for p in paths:
        with gzip.open(p, "rt", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("ticker") in NAMES:
                    try: b, a = float(r["bid_close"]), float(r["ask_close"])
                    except (ValueError, KeyError, TypeError): continue
                    if b > 0 and a > 0 and a >= b: q[r["ticker"]][int(float(r["end_period_ts"]))] = (b, a)
    return {k: sorted((t, b, a) for t, (b, a) in v.items()) for k, v in q.items()}
def day_z(rows):                                                           # rows: [(entry_ts, net)] -> day-clustered z of the mean net, None under 2 days or sd 0
    by = collections.defaultdict(float)
    for t, x in rows: by[time.strftime("%Y-%m-%d", time.gmtime(t))] += x
    d = list(by.values()); n = len(d)
    if n < 2: return None
    m = sum(d) / n; sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    return None if sd == 0 else m / (sd / math.sqrt(n))
def run(series):
    out = {"label": "upper bound, not fill-checked; fee 12 bps a leg ASSUMED (not confirmed); haircut in bp of price as a stand-in for 1c and 2c; funding not booked", "names": {}, "tries": 0}
    for nm in NAMES:
        cs = series.get(nm)
        if not cs: out["names"][nm] = {"no_data": True}; continue
        sigs = list(signals(cs)); out["tries"] += 2
        out["names"][nm] = {"signals": len(sigs), "arms": {}}
        for arm, sgn in (("T", 1), ("R", -1)):
            res = {}
            for h in HAIRCUTS:
                rows = []
                for i, d, s5, mid in sigs:
                    tr = trade(cs, i, d * sgn, s5, mid, h)
                    if tr: rows.append((cs[i][0], net(tr[0], tr[1], d * sgn)))
                xs = [x for _, x in rows]; half = len(xs) // 2
                res["h%dbp" % round(h * 1e4)] = {"n": len(xs), "pf": pf(xs), "net_sum": sum(xs), "half1_pf": pf(xs[:half]), "half2_pf": pf(xs[half:]), "day_z": day_z(rows), "trade_days": len({time.strftime("%Y-%m-%d", time.gmtime(t)) for t, _ in rows}), "evidence": "ok" if len(xs) >= 100 else "no evidence at n = %d" % len(xs)}
            out["names"][nm]["arms"][arm] = res
    return out
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) < 2: sys.exit(__doc__)
    if os.environ.get("PERPSCALP_READ") != "1": sys.exit("REFUSED: PERPSCALP_READ=1 is not set (reading starts only after Auditor B's quick check)")
    json.dump(run(load(a[1:])), open(a[0], "w"), indent=1, default=str); print("wrote", a[0])
