"""RESIL1 scorer (workers/RESIL1_REGISTRATION.md). Idea Desk A, written Nov 12 2026 BEFORE any event was built from the data.
  python3 -I resil1.py selftest
  python3 -I resil1.py dev  <folder holding book15r6/>      development: closes 2026-10-29T22:15Z to before 2026-11-05T00:00Z
  python3 -I resil1.py heldout <folder holding book15r6/>   ONE read; refused before 2026-11-14T12:00Z and after a marker line; the held-out folders are opened only here
Rule: sweep = taker prints of ONE side at >= 2 distinct prices within one whole second (tape, exchange time), first one 12 to 4 minutes before the close;
refilled = the swept side's best ask is at or below its pre-sweep value (last poll >= 0.25 s before the first print) at the first poll >= 2 s after the event AND at the last
poll <= 6 s after it; trade only when NOT refilled: buy the swept side at its ask at the first poll >= 60 s after the event (ask 0.10 to 0.90, size >= 1), hold, fee 0.07 p (1-p)."""
import gzip, csv, glob, sys, os, bisect, collections, datetime, math, tempfile
from email.utils import parsedate_to_datetime
from statistics import median
HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = os.path.join(HERE, "..", "RESIL1_REGISTRATION.md")
LO = datetime.datetime(2026, 10, 29, 22, 15, tzinfo=datetime.timezone.utc).timestamp()
CUT = datetime.datetime(2026, 11, 5, tzinfo=datetime.timezone.utc).timestamp()
READ_NOT_BEFORE = datetime.datetime(2026, 11, 14, 12, tzinfo=datetime.timezone.utc).timestamp()
SERIES = ("KXGOLD15M", "KXBTC15M", "KXETH15M", "KXDOGE15M", "KXXRP15M")
def fee(p): return 0.07 * p * (1 - p)
def pf(v):
    a = sum(x for x in v if x > 0); b = -sum(x for x in v if x < 0); return a / b if b else float("inf")
def fl(x): return float(x) if x not in (None, "") else None
def rd(p):
    with gzip.open(p, "rt") as f: return list(csv.DictReader(f))
def ts(iso): return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
def ask_of(poll, side):
    """poll = (t, yes_bid_px, yes_bid_sz, no_bid_px, no_bid_sz); YES ask = 1 - best NO bid (size = that bid's), NO ask = 1 - best YES bid"""
    if side == "yes": return (1 - poll[3], poll[4]) if poll[3] is not None else (None, None)
    return (1 - poll[1], poll[2]) if poll[1] is not None else (None, None)
def one_window(polls, trades, close, result):
    """-> (status, arm, pnl). polls sorted by exchange time; trades = [(t, price, count, taker_side)]"""
    sw = collections.defaultdict(set)
    first = {}
    for t, p, c, side in trades:
        k = (int(t), side); sw[k].add(round(p, 4)); first[k] = min(first.get(k, t), t)
    ev = sorted((k for k, v in sw.items() if len(v) >= 2 and close - 720 <= k[0] + 1 <= close - 240), key=lambda k: k[0])
    if not ev: return "no sweep", None, None
    sec, side = ev[0]; t_ev = sec + 1; t_first = first[(sec, side)]
    times = [p[0] for p in polls]
    i = bisect.bisect_right(times, t_first - 0.25) - 1
    if i < 0 or t_first - 0.25 - times[i] > 6: return "no pre-sweep poll", None, None
    pre, _ = ask_of(polls[i], side)
    j1 = bisect.bisect_left(times, t_ev + 2); j2 = bisect.bisect_right(times, t_ev + 6) - 1
    if j1 >= len(polls) or j2 < j1 or times[j1] > t_ev + 6: return "no post-sweep polls", None, None
    a1, _ = ask_of(polls[j1], side); a2, _ = ask_of(polls[j2], side)
    if pre is None or a1 is None or a2 is None: return "no valid ask", None, None
    arm = "refilled" if (a1 <= pre + 1e-9 and a2 <= pre + 1e-9) else "not refilled"
    k = bisect.bisect_left(times, t_ev + 60)
    if k >= len(polls) or times[k] - t_ev - 60 > 30: return "no entry poll", arm, None
    a, sz = ask_of(polls[k], side)
    if a is None or sz is None or sz < 1 or not 0.10 <= a <= 0.90: return "entry ask out of band or empty", arm, None
    win = (result == "yes") == (side == "yes")
    return "trade", arm, (1 if win else 0) - a - fee(a)
def load(root, keep):
    polls, trades, res = collections.defaultdict(set), collections.defaultdict(set), {}
    for d in sorted(glob.glob(root + "/book15r6/*/*")):
        try: bk = [x for x in rd(d + "/book.csv.gz") if x["series"] in SERIES]; tr = rd(d + "/trades.csv.gz"); cov = rd(d + "/coverage.csv.gz")
        except Exception: continue
        offs = []
        for x in bk:
            if x.get("server_date_header"):
                try: offs.append(parsedate_to_datetime(x["server_date_header"]).timestamp() + 0.5 - int(x["t_recv_ms"]) / 1000)
                except Exception: pass
        if not offs: continue
        off = median(offs)
        closes = {c["ticker"]: ts(c["close_time"]) for c in cov}
        for c in cov:
            if c["result"] in ("yes", "no") and keep(ts(c["close_time"])): res[c["ticker"]] = (ts(c["close_time"]), c["result"])
        for x in bk:
            if x["ticker"] in res:
                polls[x["ticker"]].add((int(x["t_recv_ms"]) / 1000 + off, fl(x["yes_bid_px_1"]), fl(x["yes_bid_sz_1"]), fl(x["no_bid_px_1"]), fl(x["no_bid_sz_1"])))
        for x in tr:
            tk = x["ticker"]
            if tk in res:
                trades[tk].add((ts(x["created_time"]), float(x["yes_price_dollars"]), float(x["count_fp"]), x["taker_outcome_side"]))
    return res, polls, trades
def score(res, polls, trades):
    why, arms = collections.Counter(), collections.defaultdict(list)
    for tk, (close, r) in res.items():
        P = sorted(polls.get(tk, []))
        if not P: why["no book"] += 1; continue
        st, arm, pnl = one_window(P, sorted(trades.get(tk, [])), close, r)
        why[st] += 1
        if st == "trade": arms[arm].append(pnl)
    return why, arms
def report(why, arms, final):
    L = ["RESIL1 | windows %d | %s" % (sum(why.values()), dict(why))]
    for arm in ("not refilled", "refilled"):
        v = arms.get(arm, []); n = len(v)
        L.append("%s arm%s: n %d | cash PF %s | mean %s | wins %d" % (arm, " (THE REGISTERED RULE)" if arm == "not refilled" else " (descriptive, no try)", n, "%.2f" % pf(v) if n else "n/a", "%+.2fc" % (100 * sum(v) / n) if n else "n/a", sum(1 for x in v if x > 0)))
    v = arms.get("not refilled", []); n = len(v)
    if final: lab = "RE-TEST lead (not a research-bar pass)" if n >= 100 and pf(v) >= 1.3 and sum(v) > 0 else ("FALSIFIED" if n >= 100 and pf(v) < 1.0 else "no evidence at n = %d" % n)
    else: lab = "FALSIFIED on development (cash PF under 1.0)" if n >= 100 and pf(v) < 1.0 else ("no evidence at n = %d" % n if n < 100 else "carried to the held-out")
    L.append("LABEL: " + lab)
    return L
def selftest():
    close = 10_000_000.0
    # book: YES ask = 1 - no_bid; polls every 2 s. Sweep at close-600 (yes side, prices 0.40 and 0.41).
    def mk(refill):
        P = []
        for k in range(-400, 200):
            t = close - 700 + 2 * k // 1
            ask_yes = 0.40 if t < close - 599.5 else (0.40 if refill and t < close - 590 else 0.50)
            P.append((t, 0.30, 5.0, 1 - ask_yes, 5.0))
        tr = [(close - 599.7, 0.40, 3, "yes"), (close - 599.2, 0.41, 3, "yes")]
        return sorted(P), tr
    P, tr = mk(False); st, arm, pnl = one_window(P, tr, close, "yes")
    assert (st, arm) == ("trade", "not refilled"), (st, arm); assert abs(pnl - (1 - 0.50 - fee(0.50))) < 1e-12, pnl
    P, tr = mk(True); st, arm, pnl = one_window(P, tr, close, "no")
    assert arm == "refilled", arm
    assert one_window(P, [(close - 599.7, 0.40, 3, "yes")], close, "yes")[0] == "no sweep"          # one price is not a sweep
    assert one_window(P, [(close - 100.7, 0.40, 3, "yes"), (close - 100.2, 0.41, 3, "yes")], close, "yes")[0] == "no sweep"   # outside 12 to 4 minutes
    assert one_window(P, [(close - 599.7, 0.40, 3, "yes"), (close - 599.2, 0.41, 3, "no")], close, "yes")[0] == "no sweep"    # two sides in one second is not a one-sided sweep
    # cutoff guard: a window closing on/after the cutoff is dropped by the dev filter
    d = tempfile.mkdtemp(); os.makedirs(d + "/book15r6/2026-11-04/2000")
    H = "t_send_ms,t_recv_ms,server_date_header,ticker,series,close_time,yes_bid_px_1,yes_bid_px_2,yes_bid_px_3,yes_bid_px_4,yes_bid_px_5,yes_bid_sz_1,yes_bid_sz_2,yes_bid_sz_3,yes_bid_sz_4,yes_bid_sz_5,no_bid_px_1,no_bid_px_2,no_bid_px_3,no_bid_px_4,no_bid_px_5,no_bid_sz_1,no_bid_sz_2,no_bid_sz_3,no_bid_sz_4,no_bid_sz_5\n"
    row = lambda tk, cl: '1,1000000,"Thu, 01 Jan 1970 00:16:40 GMT",%s,KXBTC15M,%s,0.3,,,,,5,,,,,0.5,,,,,5,,,,\n' % (tk, cl)
    with gzip.open(d + "/book15r6/2026-11-04/2000/book.csv.gz", "wt") as f: f.write(H + row("KXBTC15M-A", "2026-11-04T23:45:00Z") + row("KXBTC15M-B", "2026-11-05T00:00:00Z"))
    with gzip.open(d + "/book15r6/2026-11-04/2000/trades.csv.gz", "wt") as f: f.write("ticker,created_time,yes_price_dollars,count_fp,taker_outcome_side\n")
    with gzip.open(d + "/book15r6/2026-11-04/2000/coverage.csv.gz", "wt") as f: f.write("close_time,series,ticker,result\n2026-11-04T23:45:00Z,KXBTC15M,KXBTC15M-A,yes\n2026-11-05T00:00:00Z,KXBTC15M,KXBTC15M-B,yes\n")
    res, _, _ = load(d, lambda c: LO <= c < CUT); assert list(res) == ["KXBTC15M-A"], res
    print("\n".join(report(*score(*_mk_empty()), final=False))); print("SELFTEST OK (sweep, refill, entry, window rules, cutoff)")
def _mk_empty(): return {}, {}, {}
if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "selftest": selftest()
    elif mode == "dev": print("\n".join(report(*score(*load(sys.argv[2], lambda c: LO <= c < CUT)), final=False)))
    elif mode == "heldout":
        import time
        if time.time() < READ_NOT_BEFORE: sys.exit("Refusing: first allowed 2026-11-14T12:00Z (after DEPTH1's read).")
        if "RESIL1 READ ON" in open(MARKER).read(): sys.exit("Refusing: already read.")
        print("\n".join(report(*score(*load(sys.argv[2], lambda c: c >= CUT)), final=True)))
        print("COMMIT THIS LINE into workers/RESIL1_REGISTRATION.md: RESIL1 READ ON %s" % datetime.date.today())
    else: sys.exit(__doc__)
