"""PIN1, ROUND1, AVG1 (workers/PIN1_ROUND1_AVG1_PROTOCOL.md). Development only; held-out is read only for survivors."""
import gzip, csv, glob, math, os, sys, bisect, collections, sqlite3, datetime
sys.path.insert(0, "src/scalper")
import leg1
from statistics import NormalDist
N01 = NormalDist(); Phi = N01.cdf
Q = os.environ["QROOT"]
BARS = (5.34, 4.39)
def fee(p): return 0.07 * p * (1 - p)
UTC = datetime.timezone.utc
def rd(p):
    with gzip.open(p, "rt") as f: return list(csv.DictReader(f))
def stat(rows):  # rows: (event, pnl, win)
    if not rows: return None
    gw = sum(x for _, x, _ in rows if x > 0); gl = -sum(x for _, x, _ in rows if x < 0)
    n, ne, mean, z = leg1.clustered([(e, x) for e, x, _ in rows])
    return dict(n=n, ev=ne, pf=(gw / gl if gl else 99.0), mean=mean, z=z, win=sum(w for *_, w in rows) / n)
def fmt(s):
    if s is None: return "n 0 NOT_ENOUGH_DATA"
    tag = "NOT_ENOUGH_DATA" if s["n"] < 100 else ("SURVIVOR" if s["pf"] >= 1.5 and s["z"] > BARS[0] else "no")
    return "n %4d ev %4d PF %5.2f mean %+.4f z %+.2f win %.1f%% -> %s" % (s["n"], s["ev"], s["pf"], s["mean"], s["z"], 100 * s["win"], tag)
def pnl(a, w): return (1.0 if w else 0.0) - a - fee(a)
BAND = {"cheap": (0.04, 0.30), "mid": (0.30, 0.88)}

# ---- Binance spot 1m
def load_bin(sym):
    d = {}
    for f in sorted(glob.glob("data/hist_binance/%sUSDT_spot_1m/2026-*.csv.gz" % sym)):
        with gzip.open(f, "rt") as fh:
            for l in fh:
                p = l.split(",")
                try: d[int(p[0])] = float(p[4])
                except Exception: pass
    return d
BIN = {"BTC": load_bin("BTC"), "ETH": load_bin("ETH")}
def bclose(a, t_end): return BIN[a].get(t_end - 60)
def sig1m(a, t_end, n=60):
    xs = [bclose(a, t_end - 60 * j) for j in range(n + 1)]
    lr = [math.log(xs[j] / xs[j + 1]) for j in range(n) if xs[j] and xs[j + 1]]
    if len(lr) < 30: return None
    m = sum(lr) / len(lr); return math.sqrt(sum((x - m) ** 2 for x in lr) / (len(lr) - 1))
# PINNED CUTS (Nov 12, 2026): the values the Nov 11 development run used, as constants. The old split() took two thirds of whatever
# events existed at run time, which moves as data grows. Development = strictly before the cut; held-out = on or after it.
PIN1_CUT = 1789434000        # 2026-09-15T01:00:00Z, hourly close, epoch seconds (2,544 of 3,816 events then held)
ROUND1_CUT = 1792422000      # 2026-10-19T15:00:00Z, hourly close, epoch seconds
AVG1_CUT_MS = 1794060000000  # 2026-11-07T14:00:00Z, hourly close, epoch milliseconds (161 development events then)
def split(evs, cut):
    return cut
print("== PIN1 census")
cen = {}
for a, M in (("BTC", 500), ("ETH", 50)):
    ts = sorted(t for t in BIN[a] if t % 3600 == 3540 and t >= 1780272000)  # open_time of the last minute bar of each hour, from 2026-06-01
    ev = [(t + 60, BIN[a][t]) for t in ts]
    cut = split([e for e, _ in ev], PIN1_CUT); dev = [(e, A) for e, A in ev if e < cut]
    hit = sum(1 for e, A in dev if abs(A / M - round(A / M)) <= 0.05)
    n = len(dev); p0 = 0.10; z = (hit - n * p0) / math.sqrt(n * p0 * (1 - p0))
    cen[a] = z
    print(a, "M", M, "events", len(ev), "dev", n, "hits", hit, "share %.3f vs 0.100 z %+.2f" % (hit / n, z))
    print("   PIN1 pricing", "RUN" if z >= 3.0 else "NOT RUN (census z < 3.0)")

# ---- ROUND1 (ladl1)
mk = {}; qd = {}
for f in ["data/ladl1.sqlite"] + sorted(glob.glob("data/ladl1_KX*_?.sqlite")):
    c = sqlite3.connect(f)
    for tk, ser, ct, res in c.execute("select ticker,series,close_ts,result from mk"): mk[tk] = (ser, ct, res)
    for tk, l, b, a in c.execute("select ticker,look,bid,ask from q"): qd[(tk, l)] = (b, a)
AS = {"KXBTCD": "BTC", "KXETHD": "ETH"}
def strike(tk): return float(tk.rsplit("-T", 1)[1])
def isround(a, K, cls):
    M = {("BTC", "strict"): 1000, ("BTC", "loose"): 500, ("ETH", "strict"): 100, ("ETH", "loose"): 50}[(a, cls)]
    return abs(round(K) % M) == 0 or (M - round(K) % M) == 0
rr = []  # (asset, look, event, K, side, ask, win, pmodel)
for (tk, L), (b, a) in qd.items():
    if tk not in mk or mk[tk][0] not in AS or mk[tk][2] not in ("yes", "no"): continue
    if not (a > b and a - b <= 0.05 and 0 < a <= 1): continue
    ser, ct, res = mk[tk]; A = AS[ser]; K = strike(tk)
    S = bclose(A, ct - L); sg = sig1m(A, ct - L)
    if not S or not sg: continue
    py = Phi(math.log(S / K) / (sg * math.sqrt(L / 60 + 1 / 3)))
    yes = res == "yes"
    rr.append((A, L, ct, K, "yes", a, yes, py))
    rr.append((A, L, ct, K, "no", 1 - b, not yes, 1 - py))
cut = split([r[2] for r in rr], ROUND1_CUT); print("\n== ROUND1 rows", len(rr), "events", len({r[2] for r in rr}), "cut", datetime.datetime.fromtimestamp(cut, UTC))
def pick(rs):  # one side per market: YES if both in band
    seen = {}
    for r in rs:
        k = (r[0], r[1], r[2], r[3])
        if k not in seen or (r[4] == "yes" and seen[k][4] == "no"): seen[k] = r
    return list(seen.values())
dev = [r for r in rr if r[2] < cut]
res1 = []
for A in ("BTC", "ETH"):
    for L in (600, 360):
        for band in ("cheap", "mid"):
            lo, hi = BAND[band]
            base = [r for r in dev if r[0] == A and r[1] == L and lo <= r[5] <= hi]
            for cls in ("strict", "loose"):
                sel = pick([r for r in base if isround(A, r[3], cls)])
                non = pick([r for r in base if not isround(A, r[3], cls)])
                s = stat([(r[2], pnl(r[5], r[6]), r[6]) for r in sel]); sn = stat([(r[2], pnl(r[5], r[6]), r[6]) for r in non])
                print("ROUND1 %s L%d %-5s %-6s: %s | nonround %s" % (A, L, band, cls, fmt(s), "PF %.2f n %d" % (sn["pf"], sn["n"]) if sn else "n 0"))
                res1.append((A, L, band, cls, s))
# descriptive: realised minus model by class, near the money
for A in ("BTC", "ETH"):
    for cls in ("strict", "loose"):
        near = [r for r in dev if r[0] == A and r[4] == "yes" and 0.1 <= r[7] <= 0.9]
        for nm, f in (("round", lambda r: isround(A, r[3], cls)), ("nonround", lambda r: not isround(A, r[3], cls))):
            x = [r for r in near if f(r)]
            if x: print("  desc %s %s %-8s n %4d realised-minus-model %+.3f realised-minus-ask %+.3f" % (A, cls, nm, len(x), sum(r[6] for r in x) / len(x) - sum(r[7] for r in x) / len(x), sum(r[6] for r in x) / len(x) - sum(r[5] for r in x) / len(x)))

# ---- AVG1
print("\n== AVG1")
ser = collections.defaultdict(lambda: collections.defaultdict(set))
for d in sorted(glob.glob(Q + "/quotes/*/*")):
    try:
        for r in rd(d + "/spot.csv.gz"):
            try: ser[r["asset"]][r["exchange"]].add((int(r["t_recv_ms"]), float(r["price"])))
            except Exception: pass
    except Exception: pass
SP = {a: {v: sorted(s) for v, s in ser[a].items()} for a in ("BTC", "ETH")}
def idx(a, t):
    ps = []
    for v, L in SP[a].items():
        i = bisect.bisect_right(L, (t, 1e18)) - 1
        if i >= 0 and t - L[i][0] <= 10000: ps.append(L[i][1])
    return sum(ps) / len(ps) if ps else None
lad = collections.defaultdict(dict)  # ticker -> {t_send: row}
for d in sorted(glob.glob(Q + "/quotes/*/*")):
    try: rs = rd(d + "/ladder.csv.gz")
    except Exception: continue
    for r in rs:
        if r["ticker"].startswith(("KXBTCD", "KXETHD")) and r["status"] == "active":
            lad[r["ticker"]][int(r["t_send_ms"])] = r
rows = []  # (event, asset, k, side, ask, edge, win, ctms)
amb = 0
for tk, qs in lad.items():
    A = "BTC" if tk.startswith("KXBTCD") else "ETH"
    cts = {r["close_time"] for r in qs.values()}
    if len(cts) != 1: continue
    ct = int(datetime.datetime.strptime(cts.pop(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC).timestamp() * 1000)
    K = float(next(iter(qs.values()))["strike"])
    # outcome proxy: mean of the per-second index over the last 60 s
    fin = [idx(A, ct - 60000 + 1000 * j) for j in range(60)]
    if sum(x is not None for x in fin) < 45: continue
    fv = [x for x in fin if x]; Abar = sum(fv) / len(fv)
    if abs(Abar - K) / K < 0.0002: amb += 1; continue
    yes_win = Abar > K
    ts = sorted(qs)
    for k in (0, 20, 40):
        t = ct - 60000 + 1000 * k
        i = bisect.bisect_right(ts, t) - 1
        if i < 0 or t - ts[i] > 3000: continue
        q = qs[ts[i]]; yb, ya = float(q["yes_bid"]), float(q["yes_ask"])
        if not (ya > yb and ya - yb <= 0.05): continue
        S = idx(A, t)
        if not S: continue
        xs = [idx(A, t - 10000 * j) for j in range(61)]
        lr = [math.log(xs[j] / xs[j + 1]) for j in range(60) if xs[j] and xs[j + 1]]
        if len(lr) < 30: continue
        m = sum(lr) / len(lr); sd10 = math.sqrt(sum((x - m) ** 2 for x in lr) / (len(lr) - 1)); ss = sd10 / math.sqrt(10) * S
        u = 60 - k
        fx = [x for x in (idx(A, ct - 60000 + 1000 * j) for j in range(k)) if x] if k else []
        if k and len(fx) < k * 0.7: continue
        fixed = (sum(fx) / len(fx) * k / 60) if k else 0.0
        mean = fixed + u * S / 60; sd = ss * math.sqrt(u * (u + 1) * (2 * u + 1) / 6) / 60
        py = Phi((mean - K) / sd) if sd > 0 else (1.0 if mean > K else 0.0)
        for side, ask, p, w in (("yes", ya, py, yes_win), ("no", 1 - yb, 1 - py, not yes_win)):
            rows.append((ct, A, k, side, ask, p - ask, w, tk))
print("ladder markets", len(lad), "ambiguous outcome dropped", amb, "rows", len(rows), "events", len({r[0] for r in rows}))
if rows:
    cut = split([r[0] for r in rows], AVG1_CUT_MS); print("cut", datetime.datetime.fromtimestamp(cut / 1000, UTC), "dev events", len({r[0] for r in rows if r[0] < cut}), "dev rows", len([r for r in rows if r[0] < cut]))
    devA = [r for r in rows if r[0] < cut]
    for k in (0, 20, 40):
        for band in ("cheap", "mid"):
            lo, hi = BAND[band]
            base = [r for r in devA if r[2] == k and lo <= r[4] <= hi]
            print("AVG1 k%d %-5s baseline: %s" % (k, band, fmt(stat([(r[0], pnl(r[4], r[6]), r[6]) for r in base]))))
            for e in (0.05, 0.10):
                sel = [r for r in base if r[5] >= e]
                print("AVG1 k%d %-5s edge>=%.2f: %s" % (k, band, e, fmt(stat([(r[0], pnl(r[4], r[6]), r[6]) for r in sel]))))
