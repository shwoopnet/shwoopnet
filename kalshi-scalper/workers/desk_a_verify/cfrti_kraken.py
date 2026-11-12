"""CFRTI1-BTC with the index built from chosen venues (workers/CFRTI1_BTC_KRAKEN_REGISTRATION.md). Idea Desk A, Nov 12 2026.
A port of the DEVELOPMENT path of V2's src/scalper/cfrti1.py with one added filter (which venues feed the index).
DEVELOPMENT ONLY: reads run folders dated before HELDOUT_FIRST_DAY and has no held-out mode. Bitcoin only.
usage: python3 -I cfrti_kraken.py <folder holding quotes/>"""
import gzip, csv, glob, math, os, sys, bisect, collections, datetime
from statistics import NormalDist
Phi = NormalDist().cdf
Q = sys.argv[1]
HELDOUT_FIRST_DAY = "2026-11-05"
def rd(p):
    with gzip.open(p, "rt") as f: return list(csv.DictReader(f))
def fee(p): return 0.07 * p * (1 - p)
def build(venues):
    rows = []; lost = collections.Counter(); folders = 0
    for d in sorted(glob.glob(Q + "/quotes/*/*")):
        day = d.split("/")[-2]
        if day >= HELDOUT_FIRST_DAY: continue          # held-out folders are never opened
        try: res = {r["ticker"]: r for r in rd(d + "/results.csv.gz")}
        except Exception: continue
        try: spot = rd(d + "/spot.csv.gz"); qs = rd(d + "/quotes.csv.gz")
        except Exception: continue
        folders += 1
        ser = collections.defaultdict(list)
        for r in spot:
            if r["asset"] != "BTC" or (venues and r["exchange"] not in venues): continue
            try: ser[r["exchange"]].append((int(r["t_recv_ms"]), float(r["price"])))
            except Exception: pass
        for v in ser: ser[v].sort()
        qb = collections.defaultdict(list)
        for r in qs:
            try: qb[r["ticker"]].append((int(r["t_send_ms"]), r))
            except Exception: pass
        def idx(t):
            ps = []
            for v, L in ser.items():
                i = bisect.bisect_right(L, (t, 1e18)) - 1
                if i >= 0 and t - L[i][0] <= 10000: ps.append(L[i][1])
            return sum(ps) / len(ps) if ps else None
        for tk, r in res.items():
            if tk.split("-")[0] != "KXBTC15M" or r["result"] not in ("yes", "no") or tk not in qb: continue
            ct = int(datetime.datetime.strptime(r["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)
            t0 = ct - 120000
            L = qb[tk]; i = max([j for j, x in enumerate(L) if x[0] <= t0] or [-1])
            if i < 0 or t0 - L[i][0] > 3000: continue
            q = L[i][1]
            try: yb, ya, k = float(q["yes_bid"]), float(q["yes_ask"]), float(q["strike"])
            except Exception: continue
            if ya <= yb or ya - yb > 0.03 or q["status"] != "active": continue
            cheap = (0.03 <= ya <= 0.30) or (0.03 <= 1 - yb <= 0.30)
            p0 = idx(t0)
            if not p0:
                lost["no trade in 10 s" + ("" if cheap else " (not a cheap row)")] += 1; continue
            xs = [idx(t0 - 10000 * j) for j in range(0, 61)]
            lr = [math.log(xs[j] / xs[j + 1]) for j in range(60) if xs[j] and xs[j + 1]]
            if len(lr) < 30:
                lost["under 30 changes" + ("" if cheap else " (not a cheap row)")] += 1; continue
            m = sum(lr) / len(lr); sd = math.sqrt(sum((x - m) ** 2 for x in lr) / (len(lr) - 1)) * math.sqrt(8)
            if sd <= 0: continue
            py = Phi(math.log(p0 / k) / sd); yes_win = r["result"] == "yes"
            if 0.03 <= ya <= 0.30: rows.append((day, tk, "yes", ya, py, yes_win, d))
            elif 0.03 <= 1 - yb <= 0.30: rows.append((day, tk, "no", 1 - yb, 1 - py, not yes_win, d))
    return rows, lost, folders
def rep(name, rs):
    if not rs: print("%-34s n 0" % name); return
    pnl = [((1 if r[5] else 0) - r[3] - fee(r[3])) for r in rs]
    gw = sum(x for x in pnl if x > 0); gl = -sum(x for x in pnl if x < 0)
    days = sorted({r[0] for r in rs}); h = len(rs) // 2
    def pf(v):
        a = sum(x for x in v if x > 0); b = -sum(x for x in v if x < 0); return a / b if b else float("inf")
    print("%-34s n %4d days %2d | cash PF %.2f | mean %+.2fc | win %.1f%% | mean ask %.3f | halves PF %.2f / %.2f | wins %d" % (name, len(rs), len(days), gw / gl if gl else 9, 100 * sum(pnl) / len(pnl), 100 * sum(1 for r in rs if r[5]) / len(rs), sum(r[3] for r in rs) / len(rs), pf(pnl[:h]), pf(pnl[h:]), sum(1 for r in rs if r[5])))
out = {}
for name, venues in (("three venues (as registered)", None), ("kraken only", {"kraken"}), ("coinbase only (information)", {"coinbase"}), ("bitstamp only (information)", {"bitstamp"})):
    rows, lost, folders = build(venues)
    sel = [r for r in rows if r[4] - r[3] >= 0.05]
    out[name] = {(r[6], r[1]): r for r in sel}
    print("==", name, "| run folders", folders, "| cheap rows with a model", len(rows), "| lost:", dict(lost))
    rep("  baseline cheap side", rows); rep("  model edge >= 0.05", sel)
A = out["three venues (as registered)"]; K = out["kraken only"]
print("three-venue trades", len(A), "| kraken-only trades", len(K), "| in both", len(set(A) & set(K)), "| three-venue only", len(set(A) - set(K)), "| kraken-only extra", len(set(K) - set(A)))
rep("  kept (in both), kraken stats", [K[k] for k in sorted(set(A) & set(K))])
rep("  dropped from three-venue", [A[k] for k in sorted(set(A) - set(K))])
rep("  added by kraken only", [K[k] for k in sorted(set(K) - set(A))])
