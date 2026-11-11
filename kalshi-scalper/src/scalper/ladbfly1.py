"""LADBFLY1 and XSER1 (workers/LADBFLY1_XSER1_PROTOCOL.md). Reads quote-data via git; no network."""
import csv, gzip, io, subprocess, collections, itertools, datetime as dt, statistics
REPO = "/home/user/shwoopnet"
def git(*a): return subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, check=True).stdout
def rd(path):
    try: return list(csv.DictReader(io.StringIO(gzip.decompress(git("show", "origin/quote-data:" + path)).decode())))
    except Exception: return []
def f(x):
    try: return float(x)
    except Exception: return None
fee = lambda p: 0.07 * p * (1 - p)
files = git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split("\n")
# ---- ladder books
ev = collections.defaultdict(list)
for p in files:
    if p.startswith("book/") and p.endswith("book.csv.gz"):
        for r in rd(p):
            bid, bsz, nb, nsz = f(r["yes_bid_px_1"]), f(r["yes_bid_sz_1"]), f(r["no_bid_px_1"]), f(r["no_bid_sz_1"])
            if None in (bid, bsz, nb, nsz) or bid <= 0 or nb <= 0: continue
            ev[r["close_time"]].append((int(r["poll_ts_local_ms"]), f(r["strike"]), bid, bsz, 1 - nb, nsz))
snaps = {}  # close -> list of (t, {strike:(bid,bsz,ask,asz)})
for ct, rows in ev.items():
    rows.sort(); out = []; cur = None; t0 = None; last = None
    for t, k, b, bs, a, as_ in rows:
        if cur is None or t - last > 1500 or t - t0 > 2000:
            if cur: out.append((t0, cur))
            cur = {}; t0 = t
        cur[k] = (b, bs, a, as_); last = t
    if cur: out.append((t0, cur))
    snaps[ct] = out
def outcome(ct):
    if not snaps[ct]: return {}
    o = {}
    for k, (b, bs, a, as_) in snaps[ct][-1][1].items():
        o[k] = True if b >= 0.85 else (False if a <= 0.15 else None)
    lo, hi = min(o), max(o)
    class D(dict):
        def get(self, k, d=None):
            if k in self: return dict.get(self, k)
            if k < lo and o[lo] is True: return True
            if k > hi and o[hi] is False: return False
            if lo < k < hi:
                if o[lo] is False: return False
                if o[hi] is True: return True
            return None
    return D(o)
cnt = collections.Counter(); days = collections.defaultdict(collections.Counter)
A = []; B = []; crossed = 0; nsnap = 0
open_a = {}; open_b = {}
for ct in sorted(snaps):
    out = outcome(ct); day = ct[:10]; prevA = set(); prevB = set()
    for t, s in snaps[ct]:
        ks = sorted(s); nsnap += 1
        for k in ks:
            if s[k][0] + (1 - s[k][2]) >= 1 - 1e-9: crossed += 1
        curA = set()
        for i, j in itertools.combinations(ks, 2):
            ask_i, bid_j = s[i][2], s[j][0]
            if ask_i < bid_j - 1e-9:
                net = bid_j - ask_i - fee(ask_i) - fee(bid_j)
                size = min(s[i][3], s[j][1]); oi, oj = out.get(i), out.get(j)
                cash = None
                if oi is not None and oj is not None: cash = net + (1 if oi else 0) - (1 if oj else 0)
                curA.add((i, j)); A.append(dict(ct=ct, day=day, key=(i, j), new=(i, j) not in prevA, net=net, size=size, cash=cash))
        prevA = curA; curB = set()
        for a_, b_, c_ in zip(ks, ks[1:], ks[2:]):
            credit = 2 * s[b_][0] - s[a_][2] - s[c_][2]
            if credit > 0:
                net = credit - fee(s[a_][2]) - 2 * fee(s[b_][0]) - fee(s[c_][2])
                size = min(s[a_][3], s[b_][1] / 2, s[c_][3]); o = (out.get(a_), out.get(b_), out.get(c_))
                cash = None
                if None not in o: cash = credit - fee(s[a_][2]) - 2 * fee(s[b_][0]) - fee(s[c_][2]) + o[0] - 2 * o[1] + o[2]
                curB.add((a_, b_, c_)); B.append(dict(ct=ct, day=day, key=(a_, b_, c_), new=(a_, b_, c_) not in prevB, net=net, size=size, cash=cash, raw=credit))
        prevB = curB
nd = len({c[:10] for c in snaps})
print("events", len(snaps), "days", nd, "snapshots", nsnap, "crossed strikes", crossed)
def rep(name, L):
    pos = [x for x in L if x["net"] > 0]; ep = [x for x in pos if x["new"]]
    print(name, "violations(book, snapshots)", len(L), "episodes(book)", len([x for x in L if x["new"]]), "| after fees snapshots", len(pos), "episodes", len(ep), "per day %.2f" % (len(ep) / nd))
    if ep:
        sz = [x["size"] for x in ep]; print("  size median %.1f max %.1f | net per contract mean %.4f max %.4f" % (statistics.median(sz), max(sz), statistics.mean(x["net"] for x in ep), max(x["net"] for x in ep)))
        c = [x["cash"] for x in ep if x["cash"] is not None]
        if c: print("  cash per episode (inferred settle, n=%d) mean %.4f min %.4f total %.2f" % (len(c), statistics.mean(c), min(c), sum(c)))
        print("  by day:", dict(collections.Counter(x["day"] for x in ep)))
        print("  top:", sorted(ep, key=lambda x: -x["net"])[:3])
rep("LADBFLY1(a)", A); rep("LADBFLY1(b)", B)
# ---- XSER1
res = {}
for p in files:
    if p.startswith("quotes/") and p.endswith("results.csv.gz"):
        for r in rd(p): res[r["ticker"]] = r
q15 = collections.defaultdict(list)
for p in files:
    if p.startswith("quotes/") and p.endswith("quotes.csv.gz"):
        for r in rd(p):
            if r["ticker"].startswith("KXBTC15M"): q15[r["ticker"]].append(r)
import bisect
rows = []; allv = []; considered = 0; gaps = []
for tk, qs in q15.items():
    if tk not in res: continue
    ct = res[tk]["close_time"]
    if not ct.endswith(":00:00Z") or ct not in snaps: continue
    T = int(dt.datetime.fromisoformat(ct.replace("Z", "+00:00")).timestamp() * 1000)
    st = snaps[ct]; ts = [t for t, _ in st]; pairs = []
    for r in qs:
        k15, yb, ya, tr = f(r["strike"]), f(r["yes_bid"]), f(r["yes_ask"]), int(r["t_recv_ms"])
        if None in (k15, yb, ya) or r["status"] != "active": continue
        i = bisect.bisect_left(ts, tr); c = [x for x in (i - 1, i) if 0 <= x < len(ts)]
        if not c: continue
        j = min(c, key=lambda x: abs(ts[x] - tr))
        if abs(ts[j] - tr) > 3000 or tr > T - 5000: continue
        s = st[j][1]; K = min(s, key=lambda k: (abs(k - k15), k))
        pairs.append((tr, k15, yb, ya, K, s[K], r))
    if not pairs: continue
    considered += 1
    def chk(p):
        tr, k15, yb, ya, K, (lb, lbs, la, las), r = p
        if K <= k15: v = la < yb; net = yb - la - fee(la) - fee(yb); size = min(las, f(r['bid_size']) or 0)
        else: v = ya < lb; net = lb - ya - fee(ya) - fee(lb); size = min(lbs, f(r['ask_size']) or 0)
        return v, net, size
    last = max(pairs); tr, k15, yb, ya, K, L, _r = last
    mid15 = (yb + ya) / 2; midL = (L[0] + L[2]) / 2
    gaps.append((abs(K - k15), midL - mid15, K <= k15))
    v, net, size = chk(last); rows.append((tk, v, net, K - k15, size, ct))
    for p in pairs:
        v, net, size = chk(p); allv.append((v, net))
print("XSER1 windows considered", considered, "| last-sample violations(book)", sum(1 for r in rows if r[1]), "after fees", sum(1 for r in rows if r[1] and r[2] > 0))
print("  all-sample pairs", len(allv), "violations(book)", sum(1 for v, n in allv if v), "after fees", sum(1 for v, n in allv if v and n > 0))
if gaps:
    for lo, hi in ((0, 50), (50, 150), (150, 1e9)):
        g = [x for x in gaps if lo <= x[0] < hi]
        if g: print("  |K-K15| %d-%d: n %d mean (ladder mid - 15m mid) %.3f, share with expected sign wrong %.2f" % (lo, hi, len(g), statistics.mean(x[1] for x in g), sum(1 for x in g if (x[1] < 0 if x[2] else x[1] > 0)) / len(g)))
print("  viol rows", [r for r in rows if r[1]][:5])

print("last gap to close (s):", sorted({(int(dt.datetime.fromisoformat(c.replace("Z","+00:00")).timestamp()*1000)-snaps[c][-1][0])//1000 for c in snaps})[:3], "..", sorted({(int(dt.datetime.fromisoformat(c.replace("Z","+00:00")).timestamp()*1000)-snaps[c][-1][0])//1000 for c in snaps})[-3:])
print("outcomes unknown share", sum(1 for c in snaps for v in outcome(c).values() if v is None)/sum(len(outcome(c)) for c in snaps))
ep=[x for x in B if x["new"] and x["net"]>0]
print("B ep", len(ep), "with cash", sum(1 for x in ep if x["cash"] is not None))
c=[x["cash"] for x in ep if x["cash"] is not None]
if c: print("B cash mean %.4f total %.1f; wins %d of %d; net-at-book mean %.4f" % (statistics.mean(c), sum(c), sum(1 for v in c if v>0), len(c), statistics.mean(x["net"] for x in ep if x["cash"] is not None)))
ev_=collections.defaultdict(float)
for x in ep:
    if x["cash"] is not None: ev_[x["day"]]+=x["cash"]
print("B cash by day", {k:round(v,1) for k,v in sorted(ev_.items())})
import math
byev=collections.defaultdict(list)
for x in ep:
    if x["cash"] is not None: byev[x["ct"]].append(x["cash"])
m=[sum(v)/len(v) for v in byev.values()]; n=len(m)
print("B events with cash", n, "mean of event-mean %.4f sd %.4f t %.2f; events with any loss %d; losses (eps) %d" % (statistics.mean(m), statistics.stdev(m), statistics.mean(m)/(statistics.stdev(m)/math.sqrt(n)), sum(1 for v in byev.values() if min(v)<0), sum(1 for x in ep if x["cash"] is not None and x["cash"]<0)))
print("B first-episode-per-event only:", end=" ")
first={}
for x in ep:
    if x["cash"] is not None and x["ct"] not in first: first[x["ct"]]=x
fc=[x["cash"] for x in first.values()]
print(len(fc), "mean %.4f wins %d size med %.0f" % (statistics.mean(fc), sum(1 for v in fc if v>0), statistics.median([x["size"] for x in first.values()])))
