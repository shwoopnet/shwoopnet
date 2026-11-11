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
def split(snaps, last_t):
    el = eligible(snaps, last_t)
    inwin = [ct for ct in el if any(WIN_LO <= ms(ct) - t <= WIN_HI for t, _ in snaps[ct])]
    n = len(inwin); return inwin[:(2 * n) // 3], inwin[(2 * n) // 3:]
def fetch(cts, evt):
    path = SCR + "/bfly2_true.json"; got = json.load(open(path)) if os.path.exists(path) else {}
    for ct in cts:
        if ct in got: continue
        url = "https://api.elections.kalshi.com/trade-api/v2/events/%s?with_nested_markets=true" % evt[ct]
        try: d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-readonly"}), timeout=30))
        except urllib.error.HTTPError as e:
            print("HTTP", e.code, "at", ct, "stopping, resume later"); break
        except Exception as e:
            print("error", e, "stopping"); break
        got[ct] = {m["ticker"]: dict(result=m.get("result"), status=m.get("status"), floor=m.get("floor_strike"), exp=m.get("expiration_value")) for m in d["event"]["markets"]}
        json.dump(got, open(path, "w")); time.sleep(3.0)
    return got

def cp_upper(k, n, alpha=0.05):
    """one-sided exact upper bound for a binomial rate (bisection)"""
    if k >= n: return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(60):
        m = (lo + hi) / 2
        cdf = sum(math.comb(n, i) * m ** i * (1 - m) ** (n - i) for i in range(k + 1))
        if cdf > alpha: lo = m
        else: hi = m
    return hi
def score(cts, snaps, evt, got, label):
    ep = episodes({c: snaps[c] for c in cts}); rows = []; excl = 0; mism = []
    for ct in cts:
        if ct not in got: excl += 1; continue
        tru = got[ct]; e = ep.get(ct)
        # inferred vs true over the last snapshot's strikes
        S = snaps[ct][-1][1]
        for k, (bids, nbs, tk) in S.items():
            tr = tru.get(tk, {}).get("result")
            inf = True if bids[0][0] >= 0.85 else (False if 1 - nbs[0][0] <= 0.15 else None)
            if tr in ("yes", "no") and inf is not None and (tr == "yes") != inf: mism.append((ct, tk, tr, inf))
        if not e: continue
        r = [tru.get(t, {}).get("result") for t in e["tk"]]
        if any(x not in ("yes", "no") for x in r): excl += 1; continue
        y = [1 if x == "yes" else 0 for x in r]
        pay = y[0] - 2 * y[1] + y[2]
        rows.append(dict(ct=ct, pay=pay, cash_r=e["net_r"] + pay, cash_u=e["net_u"] + pay, cash_nh=e["nohair"] + pay, hc=e["haircut_available"], K=e["K"], dec=e["dec"]))
    n = len(rows); print("==", label, "events in split", len(cts), "with an episode", len(ep), "scored", n, "excluded (no true result)", excl)
    for key in ("cash_r", "cash_u", "cash_nh"):
        c = [x[key] for x in rows]
        if not c: continue
        w = sum(v for v in c if v > 0); l = -sum(v for v in c if v < 0); losses = [v for v in c if v < 0]
        pf = w / l if l else float("inf"); mean = statistics.mean(c)
        sd = statistics.stdev(c) if n > 1 else float("nan"); t = mean / (sd / math.sqrt(n)) if sd else float("inf")
        wins = [v for v in c if v > 0]; be = None
        if losses and wins: mw = statistics.mean(wins); ml = -statistics.mean(losses); be = mw / (mw + ml)
        ub = cp_upper(len(losses), n)
        print("%s: mean %.4f total %.2f PF %.2f t %.2f | losing events %d worst %.3f worst-loss share of gross loss %s | loss rate %.4f upper95 %.4f break-even loss rate %s | mean win %.4f" % (
            key, mean, sum(c), pf, t, len(losses), min(c), ("%.2f" % (-min(c) / l)) if l else "n/a", len(losses) / n, ub, ("%.4f" % be) if be else "n/a", statistics.mean(wins) if wins else 0))
    print("payoff counts", collections.Counter(x["pay"] for x in rows), "| decision-net (no haircut, rounded) mean %.4f | haircut unavailable %d" % (statistics.mean(x["dec"] for x in rows) if rows else 0, sum(1 for x in rows if not x["hc"])))
    print("inferred vs true outcome mismatches over all strikes of the last snapshots:", len(mism), mism[:10])
    print("by day:", {d: round(sum(x["cash_r"] for x in rows if x["ct"][:10] == d), 2) for d in sorted({x["ct"][:10] for x in rows})})
    print("losing events:", [(x["ct"], x["K"], round(x["cash_r"], 3)) for x in rows if x["cash_r"] < 0])
    return rows

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
    if mode == "fetchdev":
        dev, ho = split(snaps, last_t); g = fetch(dev, evt); print("dev events", len(dev), "fetched", sum(1 for c in dev if c in g))
    if mode == "scoredev":
        dev, ho = split(snaps, last_t); g = json.load(open(SCR + "/bfly2_true.json")); score(dev, snaps, evt, g, "DEVELOPMENT")
