"""CFRTI-B (workers/CFRTI_B_REGISTRATION.md): CFRTI1-BTC's spot model, but signal AND price from the R6 order book. Lines B3 (three-venue index) and BK (Kraken only).
DEVELOPMENT only: closes from 2026-10-29T22:15Z to before 2026-11-05T00:00Z that have an R6 book. Idea Desk A, Nov 12 2026.
usage: python3 -I cfrti_b.py <folder holding quotes/> <folder holding book15r6/>"""
import gzip, csv, glob, math, sys, bisect, collections, datetime
from email.utils import parsedate_to_datetime
from statistics import NormalDist, median
Phi = NormalDist().cdf
Q, R6 = sys.argv[1], sys.argv[2]
FIRST_CLOSE = datetime.datetime(2026, 10, 29, 22, 15, tzinfo=datetime.timezone.utc).timestamp()
CUTOFF = datetime.datetime(2026, 11, 5, tzinfo=datetime.timezone.utc).timestamp()
def rd(p):
    with gzip.open(p, "rt") as f: return list(csv.DictReader(f))
def fee(p): return 0.07 * p * (1 - p)
def fl(x): return float(x) if x not in (None, "") else None
# ---- R6 books: ticker -> sorted [(t_exchange_s, yb, ybs, nb, nbs)]
book = collections.defaultdict(list)
for f in sorted(glob.glob(R6 + "/book15r6/*/*/book.csv.gz")):
    rows = [x for x in rd(f) if x["series"] == "KXBTC15M"]
    offs = []
    for x in rows:
        if x.get("server_date_header"):
            try: offs.append(parsedate_to_datetime(x["server_date_header"]).timestamp() + 0.5 - int(x["t_recv_ms"]) / 1000)
            except Exception: pass
    if not offs: continue
    off = median(offs)
    for x in rows:
        book[x["ticker"]].append((int(x["t_recv_ms"]) / 1000 + off, fl(x["yes_bid_px_1"]), fl(x["yes_bid_sz_1"]), fl(x["no_bid_px_1"]), fl(x["no_bid_sz_1"])))
for t in book: book[t] = sorted(set(book[t]))
def side_ask(p, side):
    # YES ask = 1 - best NO bid (size = that NO bid's size); NO ask = 1 - best YES bid
    return ((1 - p[3], p[4]) if side == "yes" else (1 - p[1], p[2])) if (p[3] is not None if side == "yes" else p[1] is not None) else (None, None)
def build(venues):
    out, lost, seen_tk = [], collections.Counter(), set()
    for d in sorted(glob.glob(Q + "/quotes/*/*")):
        day = d.split("/")[-2]
        if day >= "2026-11-05": continue
        try: res = {r["ticker"]: r for r in rd(d + "/results.csv.gz")}; spot = rd(d + "/spot.csv.gz"); qs = rd(d + "/quotes.csv.gz")
        except Exception: continue
        strike = {}
        for r in qs:
            if r["ticker"] not in strike and r["strike"]: strike[r["ticker"]] = float(r["strike"])
        ser = collections.defaultdict(list)
        for r in spot:
            if r["asset"] != "BTC" or (venues and r["exchange"] not in venues): continue
            try: ser[r["exchange"]].append((int(r["t_recv_ms"]), float(r["price"])))
            except Exception: pass
        for v in ser: ser[v].sort()
        def idx(t):
            ps = []
            for v, L in ser.items():
                i = bisect.bisect_right(L, (t, 1e18)) - 1
                if i >= 0 and t - L[i][0] <= 10000: ps.append(L[i][1])
            return sum(ps) / len(ps) if ps else None
        for tk, r in res.items():
            if not tk.startswith("KXBTC15M-") or r["result"] not in ("yes", "no") or tk in seen_tk or tk not in strike: continue
            close = datetime.datetime.strptime(r["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()
            if close < FIRST_CLOSE or close >= CUTOFF: continue
            B = book.get(tk)
            if not B: lost["no R6 book"] += 1; continue
            t0 = close - 120
            ts = [b[0] for b in B]; i = bisect.bisect_right(ts, t0 - 0.25) - 1
            if i < 0 or t0 - 0.25 - ts[i] > 4: lost["no R6 poll within 4 s before t0"] += 1; continue
            p = B[i]
            ya, _ = side_ask(p, "yes"); yb = p[1]
            if ya is None or yb is None or ya <= yb or ya - yb > 0.03: lost["no valid book or spread over 3c"] += 1; continue
            side = "yes" if 0.05 <= ya <= 0.30 else ("no" if 0.05 <= 1 - yb <= 0.30 else None)
            if side is None: continue
            t0ms = int(t0 * 1000); p0 = idx(t0ms)
            if not p0: lost["no trade in 10 s"] += 1; continue
            xs = [idx(t0ms - 10000 * j) for j in range(61)]
            lr = [math.log(xs[j] / xs[j + 1]) for j in range(60) if xs[j] and xs[j + 1]]
            if len(lr) < 30: lost["under 30 changes"] += 1; continue
            m = sum(lr) / len(lr); sd = math.sqrt(sum((x - m) ** 2 for x in lr) / (len(lr) - 1)) * math.sqrt(8)
            if sd <= 0: continue
            py = Phi(math.log(p0 / strike[tk]) / sd)
            seen_tk.add(tk)
            ask = ya if side == "yes" else 1 - yb
            chance = py if side == "yes" else 1 - py
            win = (r["result"] == "yes") == (side == "yes")
            def fill(delay):
                j = bisect.bisect_left(ts, t0 + delay)
                if j >= len(ts) or ts[j] - t0 - delay > 30: return None
                a, sz = side_ask(B[j], side)
                return a if a is not None and sz is not None and sz >= 1 and a <= ask + 1e-9 else None
            out.append(dict(day=day, tk=tk, side=side, ask=ask, edge=chance - ask, win=win, f2=fill(2), f6=fill(6)))
    return out, lost
def pf(v):
    a = sum(x for x in v if x > 0); b = -sum(x for x in v if x < 0); return a / b if b else float("inf")
for name, venues in (("B3 (three-venue spot)", None), ("BK (Kraken-only spot)", {"kraken"})):
    rows, lost = build(venues)
    sel = [r for r in rows if r["edge"] >= 0.05]
    print("==", name, "| cheap rows with an R6 book and a model", len(rows), "| lost:", dict(lost), "| edge rows", len(sel))
    for lab, k in (("fill +6 s (judges)", "f6"), ("fill +2 s", "f2")):
        got = [r for r in sel if r[k] is not None]
        pnl = [(1 if r["win"] else 0) - r[k] - fee(r[k]) for r in got]
        print("   %-22s filled %2d of %2d | cash PF %.2f | mean %+.2fc | wins %d | no evidence at n = %d" % (lab, len(got), len(sel), pf(pnl) if pnl else 0, 100 * sum(pnl) / len(pnl) if pnl else 0, sum(1 for r in got if r["win"]), len(got)))
    allp = [(1 if r["win"] else 0) - r["ask"] - fee(r["ask"]) for r in sel]
    print("   (for scale: the same edge rows at the book ask seen, no delay: n %d, cash PF %.2f)" % (len(sel), pf(allp) if allp else 0))
