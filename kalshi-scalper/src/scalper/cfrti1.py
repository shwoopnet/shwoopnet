"""CFRTI1 (workers/CFRTI1_PROTOCOL.md). Development only; held-out third not read here."""
import gzip, csv, glob, math, os, sys, bisect, collections
sys.path.insert(0, "src/scalper")
import leg1
from statistics import NormalDist
Phi = NormalDist().cdf
Q = os.environ["QROOT"]
ASSET = {"KXBTC15M": "BTC", "KXETH15M": "ETH", "KXXRP15M": "XRP", "KXSOL15M": "SOL", "KXDOGE15M": "DOGE"}
def rd(p):
    with gzip.open(p, "rt") as f: return list(csv.DictReader(f))
def fee(p): return 0.07 * p * (1 - p)
rows = []  # (day, event, series, side, ask, model_p_side, win)
for d in sorted(glob.glob(Q + "/quotes/*/*")):
    try: res = {r["ticker"]: r for r in rd(d + "/results.csv.gz")}
    except Exception: continue
    try: spot = rd(d + "/spot.csv.gz"); qs = rd(d + "/quotes.csv.gz")
    except Exception: continue
    ser = collections.defaultdict(lambda: collections.defaultdict(list))  # asset->venue->[(t,price)]
    for r in spot:
        try: ser[r["asset"]][r["exchange"]].append((int(r["t_recv_ms"]), float(r["price"])))
        except Exception: pass
    for a in ser:
        for v in ser[a]: ser[a][v].sort()
    qb = collections.defaultdict(list)
    for r in qs:
        try: qb[r["ticker"]].append((int(r["t_send_ms"]), r))
        except Exception: pass
    def idx(a, t):
        ps = []
        for v, L in ser[a].items():
            i = bisect.bisect_right(L, (t, 1e18)) - 1
            if i >= 0 and t - L[i][0] <= 10000: ps.append(L[i][1])
        return sum(ps) / len(ps) if ps else None
    for tk, r in res.items():
        s = tk.split("-")[0]
        if s not in ASSET or r["result"] not in ("yes", "no") or tk not in qb: continue
        a = ASSET[s]
        import datetime
        ct = int(datetime.datetime.strptime(r["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)
        t0 = ct - 120000
        L = qb[tk]; i = bisect.bisect_right(L, (t0, {})) - 1 if False else max([j for j, x in enumerate(L) if x[0] <= t0] or [-1])
        if i < 0 or t0 - L[i][0] > 3000: continue
        q = L[i][1]
        try: yb, ya, k = float(q["yes_bid"]), float(q["yes_ask"]), float(q["strike"])
        except Exception: continue
        if ya <= yb or ya - yb > 0.03 or q["status"] != "active": continue
        p0 = idx(a, t0)
        if not p0: continue
        xs = [idx(a, t0 - 10000 * j) for j in range(0, 61)]
        lr = [math.log(xs[j] / xs[j + 1]) for j in range(60) if xs[j] and xs[j + 1]]
        if len(lr) < 30: continue
        m = sum(lr) / len(lr); sd = math.sqrt(sum((x - m) ** 2 for x in lr) / (len(lr) - 1)) * math.sqrt(8)
        if sd <= 0: continue
        py = Phi(math.log(p0 / k) / sd)
        yes_win = r["result"] == "yes"
        # cheap side
        if 0.03 <= ya <= 0.30: rows.append((d.split("/")[-2], tk, s, "yes", ya, py, yes_win))
        elif 0.03 <= 1 - yb <= 0.30: rows.append((d.split("/")[-2], tk, s, "no", 1 - yb, 1 - py, not yes_win))
days = sorted({r[0] for r in rows}); cut = days[2 * len(days) // 3]
dev = [r for r in rows if r[0] < cut]
print("rows", len(rows), "days", len(days), "dev rows", len(dev), "cut", cut)
def rep(name, rs):
    if not rs: print(name, "n 0"); return
    pnl = [((1 if w else 0) - a - fee(a)) for _, _, _, _, a, _, w in rs]
    gw = sum(x for x in pnl if x > 0); gl = -sum(x for x in pnl if x < 0)
    n, ne, mean, z = leg1.clustered([(r[1], x) for r, x in zip(rs, pnl)])
    print("%-28s n %4d ev %4d PF %.2f mean %+.4f z %+.2f win %.1f%%" % (name, n, ne, gw / gl if gl else 9, mean, z, 100 * sum(1 for r in rs if r[6]) / len(rs)))
rep("baseline cheap side", dev)
sel = [r for r in dev if r[5] - r[4] >= 0.05]
rep("model edge >= 0.05", sel)
for s in sorted({r[2] for r in dev}):
    rep(" base " + s, [r for r in dev if r[2] == s]); rep(" edge " + s, [r for r in sel if r[2] == s])
