"""BFLY2 (workers/BFLY2_PROTOCOL.md). Reads quote-data via git; `fetch` mode reads Kalshi public event results (GET only, slow)."""
import csv, gzip, io, subprocess, collections, itertools, datetime as dt, statistics, sys, json, os, time, math, pickle, urllib.request, urllib.error
REPO = "/home/user/shwoopnet"
SCR = "/tmp/claude-0/-home-user-shwoopnet/026f6e8f-6dc4-5e3b-8c3b-e0089b12fb94/scratchpad"
def git(*a): return subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, check=True).stdout
def rd(path):
    try: return list(csv.DictReader(io.StringIO(gzip.decompress(git("show", "origin/quote-data:" + path)).decode())))
    except Exception: return []
def f(x):
    try: return float(x)
    except Exception: return None
def ms(ct): return int(dt.datetime.fromisoformat(ct.replace("Z", "+00:00")).timestamp() * 1000)
def load():
    cache = SCR + "/bfly2_snaps.pkl"
    if os.path.exists(cache) and "--fresh" not in sys.argv: return pickle.load(open(cache, "rb"))
    files = git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split("\n")
    ev = collections.defaultdict(list); last_t = 0
    for p in files:
        if p.startswith("book/") and p.endswith("book.csv.gz"):
            for r in rd(p):
                t = int(r["poll_ts_local_ms"]); last_t = max(last_t, t); k = f(r["strike"])
                bids = []; nbs = []
                for i in range(1, 6):
                    b, bs, n, ns = f(r["yes_bid_px_%d" % i]), f(r["yes_bid_sz_%d" % i]), f(r["no_bid_px_%d" % i]), f(r["no_bid_sz_%d" % i])
                    if b is not None and bs is not None and b > 0: bids.append((b, bs))
                    if n is not None and ns is not None and n > 0: nbs.append((n, ns))
                if not bids or not nbs or k is None: continue
                ev[r["close_time"]].append((t, k, r["ticker"].rsplit("-T", 1)[0], r["ticker"], bids, nbs))
    snaps = {}; evt = {}
    for ct, rows in ev.items():
        rows.sort(key=lambda x: x[:2]); out = []; cur = None; t0 = None; last = None
        for t, k, et, tk, bids, nbs in rows:
            if cur is None or t - last > 1500 or t - t0 > 2000:
                if cur: out.append((t0, cur))
                cur = {}; t0 = t
            cur[k] = (bids, nbs, tk); last = t; evt[ct] = et
        if cur: out.append((t0, cur))
        snaps[ct] = out
    d = (snaps, evt, last_t); pickle.dump(d, open(cache, "wb")); return d
# ---- fill model
def ceilc(x): return math.ceil(round(x * 100, 6)) / 100.0
def walk(levels, n):
    """levels: list of (price, size) best first; buy/sell n contracts; returns (avg price, filled)"""
    need = n; cost = 0.0
    for p, s in levels:
        take = min(need, s); cost += take * p; need -= take
        if need <= 0: break
    if need > 0: return None
    return cost / n
def sell_yes(strike_snap, n):  # sell YES = hit YES bids
    return walk(strike_snap[0], n)
def buy_yes(strike_snap, n):  # buy YES at 1 - no bid
    lv = [(1 - p, s) for p, s in strike_snap[1]]
    return walk(lv, n)
SPACING = 100.0; WIN_LO, WIN_HI = 10 * 60 * 1000, 55 * 60 * 1000; THRESH = 0.01
def legs(s, k1, k2, k3):
    a1, b2, a3 = buy_yes(s[k1], 1), sell_yes(s[k2], 2), buy_yes(s[k3], 1)
    return a1, b2, a3
def net(a1, b2, a3, rounded):
    fe = (lambda c, p: ceilc(0.07 * c * p * (1 - p))) if rounded else (lambda c, p: 0.07 * c * p * (1 - p))
    return 2 * b2 - a1 - a3 - fe(1, a1) - fe(2, b2) - fe(1, a3)
def pick(snapsE, i, T):
    """first qualifying snapshot logic: returns (k1,k2,k3, decision net rounded) at snapshot i or None"""
    t, s = snapsE[i]
    if not (WIN_LO <= T - t <= WIN_HI): return None
    ks = sorted(s); best = None
    for a, b, c in zip(ks, ks[1:], ks[2:]):
        if abs((b - a) - SPACING) > 0.011 or abs((c - b) - SPACING) > 0.011: continue
        a1, b2, a3 = legs(s, a, b, c)
        if None in (a1, b2, a3): continue
        n = net(a1, b2, a3, True)
        if n >= THRESH - 1e-9 and (best is None or n > best[3] + 1e-12): best = (a, b, c, n)
    return best
def episodes(snaps):
    out = {}
    for ct in sorted(snaps):
        T = ms(ct); S = snaps[ct]
        for i in range(len(S)):
            q = pick(S, i, T)
            if q:
                a, b, c, n = q; t, s = S[i]
                # haircut: worse of this and the next snapshot per leg
                nxt = S[i + 1] if i + 1 < len(S) and S[i + 1][0] - t <= 6000 and all(k in S[i + 1][1] for k in (a, b, c)) else None
                A = legs(s, a, b, c); B = legs(nxt[1], a, b, c) if nxt else A
                if None in B: B = A
                a1, a3 = max(A[0], B[0]), max(A[2], B[2]); b2 = min(A[1], B[1])
                out[ct] = dict(ct=ct, t=t, K=(a, b, c), dec=n, leg=(a1, b2, a3), net_r=net(a1, b2, a3, True), net_u=net(a1, b2, a3, False),
                               nohair=net(*A, True), haircut_available=nxt is not None, tk=tuple(s[k][2] for k in (a, b, c)))
                break
    return out
def eligible(snaps, last_t):
    return sorted(ct for ct in snaps if ms(ct) <= last_t - 1800 * 1000)  # event closed and data ran on past it
if __name__ == "__main__":
    mode = sys.argv[1]
    snaps, evt, last_t = load()
    el = eligible(snaps, last_t)
    inwin = [ct for ct in el if any(WIN_LO <= ms(ct) - t <= WIN_HI for t, _ in snaps[ct])]
    if mode == "count":
        print("events total", len(snaps), "eligible (closed, data ran 30 min past)", len(el), "with a snapshot in the 55-10 min window", len(inwin))
        print("first", inwin[0], "last", inwin[-1], "data ends", dt.datetime.utcfromtimestamp(last_t / 1000))
        sp = collections.Counter(round(b - a, 2) for ct in inwin for t, s in snaps[ct][:1] for a, b in zip(sorted(s), sorted(s)[1:]))
        print("strike gaps in first snapshots", sp.most_common(4))
        n = len(inwin); print("two thirds index", (2 * n) // 3, "cutoff event", inwin[(2 * n) // 3 - 1], "first held-out event", inwin[(2 * n) // 3])
        print("last 12 events", inwin[-12:])
