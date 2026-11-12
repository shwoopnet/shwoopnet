"""CFRTI-B (workers/CFRTI_B_REGISTRATION.md): CFRTI1-BTC's spot model, but signal AND price from the R6 order book. Lines B3 (three-venue index) and BK (Kraken only).
DEVELOPMENT only: closes from 2026-10-29T22:15Z to before 2026-11-05T00:00Z that have an R6 book. Idea Desk A, Nov 12 2026.
usage: python3 -I cfrti_b.py <folder holding quotes/> <folder holding book15r6/>"""
import os, gzip, csv, glob, math, sys, bisect, collections, datetime
from email.utils import parsedate_to_datetime
from statistics import NormalDist, median
Phi = NormalDist().cdf
FIRST_CLOSE = datetime.datetime(2026, 10, 29, 22, 15, tzinfo=datetime.timezone.utc).timestamp()
CUTOFF = datetime.datetime(2026, 11, 5, tzinfo=datetime.timezone.utc).timestamp()
def rd(p):
    with gzip.open(p, "rt") as f: return list(csv.DictReader(f))
def fee(p): return 0.07 * p * (1 - p)
def fl(x): return float(x) if x not in (None, "") else None
# ---- R6 books: ticker -> sorted [(t_exchange_s, yb, ybs, nb, nbs)]
book = collections.defaultdict(list)
def load_book(R6, before=None):
  sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import heldout_guard; heldout_guard.refuse_heldout(R6, "cfrti_b.load_book")      # standing rule (h)
  book.clear()
  for f in sorted(glob.glob(R6 + "/book15r6/*/*/book.csv.gz")):
      if before and f.split("/")[-3] >= before: continue                                  # folders dated at or after `before` are never opened
      rows = [x for x in rd(f) if x["series"] == "KXBTC15M"]
      offs = []
      for x in rows:
          if x.get("server_date_header"):
              try: offs.append(parsedate_to_datetime(x["server_date_header"]).timestamp() + 0.5 - int(x["t_recv_ms"]) / 1000)
              except Exception: pass
      if not offs: continue
      off = median(offs)
      for x in rows:
          lv = lambda pre: tuple((fl(x["%s_px_%d" % (pre, i)]), fl(x["%s_sz_%d" % (pre, i)])) for i in range(1, 6) if fl(x["%s_px_%d" % (pre, i)]) is not None and fl(x["%s_sz_%d" % (pre, i)]) is not None)
          book[x["ticker"]].append((int(x["t_recv_ms"]) / 1000 + off, fl(x["yes_bid_px_1"]), fl(x["yes_bid_sz_1"]), fl(x["no_bid_px_1"]), fl(x["no_bid_sz_1"]), lv("yes_bid"), lv("no_bid")))
  for t in book: book[t] = sorted(set(book[t]))
def fill_ioc(B, side, limit, t0, delay):
    """THE BOOK-REPLAY CONVENTION (ruling of the Head of R&D, Nov 12, fixed before any held-out row is opened): an immediate-or-cancel buy of 1 contract in total, walking the book's levels
    (up to 5) at or below the limit; only the FIRST poll within 4 s after t0 + delay counts (no poll in that span is no trade); not enough size at or below the limit is no trade.
    Returns the average price paid, or None. B = polls sorted by time, each (t, yb1, ybs1, nb1, nbs1, yes_bid_levels, no_bid_levels)."""
    times = [p[0] for p in B]
    j = bisect.bisect_left(times, t0 + delay)
    if j >= len(B) or times[j] - t0 - delay > 4: return None
    p = B[j]
    lv = p[6] if side == "yes" else p[5]                  # a YES buy meets the NO bids (ask = 1 - NO bid price); a NO buy meets the YES bids
    asks = sorted(((1 - px, sz) for px, sz in lv), key=lambda x: x[0])
    need, cost = 1.0, 0.0
    for a, sz in asks:
        if a > limit + 1e-9: break
        take = min(need, sz); cost += take * a; need -= take
        if need <= 1e-12: return cost / 1.0
    return None
def side_ask(p, side):
    # YES ask = 1 - best NO bid (size = that NO bid's size); NO ask = 1 - best YES bid
    return ((1 - p[3], p[4]) if side == "yes" else (1 - p[1], p[2])) if (p[3] is not None if side == "yes" else p[1] is not None) else (None, None)
def build(Q, venues, keep_day, lo, hi):
    out, lost, seen_tk = [], collections.Counter(), set()
    for d in sorted(glob.glob(Q + "/quotes/*/*")):
        day = d.split("/")[-2]
        if not keep_day(day): continue
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
            if close < lo or close >= hi: continue
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
            fill = lambda delay: fill_ioc(B, side, ask, t0, delay)
            out.append(dict(day=day, tk=tk, side=side, ask=ask, edge=chance - ask, win=win, f2=fill(2), f6=fill(6)))
    return out, lost
def pf(v):
    a = sum(x for x in v if x > 0); b = -sum(x for x in v if x < 0); return a / b if b else float("inf")
def label(n, pfv, mean):
    if n >= 50 and pfv >= 1.3 and mean > 0: return "RE-TEST lead (not a result)"
    if n >= 30 and pfv < 1.0: return "FALSIFIED"
    return "no evidence at n = %d" % n
def lines(Q, R6, keep_day, lo, hi, final=False):
    load_book(R6); out = []
    for name, venues in (("B3 (three-venue spot)", None), ("BK (Kraken-only spot)", {"kraken"})):
        rows, lost = build(Q, venues, keep_day, lo, hi)
        sel = [r for r in rows if r["edge"] >= 0.05]
        out.append("== %s | cheap rows with an R6 book and a model %d | lost: %s | edge rows %d" % (name, len(rows), dict(lost), len(sel)))
        for lab, k in (("fill +6 s (judges)", "f6"), ("fill +2 s", "f2")):
            got = [r for r in sel if r[k] is not None]
            pnl = [(1 if r["win"] else 0) - r[k] - fee(r[k]) for r in got]
            p_, mean = (pf(pnl) if pnl else 0), (100 * sum(pnl) / len(pnl) if pnl else 0)
            out.append("   %-22s filled %2d of %2d | cash PF %.2f | mean %+.2fc | wins %d | %s" % (lab, len(got), len(sel), p_, mean, sum(1 for r in got if r["win"]), label(len(got), p_, mean / 100) if (final and k == "f6") else "no evidence at n = %d" % len(got) if not final else "(2 s line, no label)"))
        allp = [(1 if r["win"] else 0) - r["ask"] - fee(r["ask"]) for r in sel]
        out.append("   (for scale: the same edge rows at the book ask seen, no delay: n %d, cash PF %.2f)" % (len(sel), pf(allp) if allp else 0))
    return out
if __name__ == "__main__":
    print("\n".join(lines(sys.argv[1], sys.argv[2], lambda d: d < "2026-11-05", FIRST_CLOSE, CUTOFF)))
