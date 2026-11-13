"""NC15DEPTH1 scorer (Desk A, Nov 13 2026), built to workers/NC15DEPTH1_POOLED_REGISTRATION.md (c6a97613, counts 9605dcd7). Offline, sends nothing, reads only a folder of run folders <date>/<HHMM>/{book,coverage}.csv.gz (the nc15 shape).
  python3 -I nc15depth1.py <root>      DEFAULT-CLOSED: refuses a folder without MADE_UP_DATA unless NC15DEPTH1_READ=1 is set (the real read, on the Head's word, from 2026-11-19); HELDOUT_ paths and runs listed in HELDOUT_PULL_RUNS.md are refused (heldout_guard_v2).
One pooled cell over the eleven nc15 series: look = the last poll with exchange time in [D-10, D], D = close - 600 s (exchange time: rolling median of the last 120 readable Date headers + 0.5 s - t_recv); imb5 = (sum of five YES bid sizes - sum of five NO bid sizes) / their total; in the cell if abs(imb5) >= 0.50; imb5 > 0 buys YES, < 0 buys NO. Trade: 1 contract at the best ask (YES: 1 - best NO bid; NO: 1 - best YES bid) read at the FIRST poll with exchange time >= look + 1.0 s and <= look + 20 s, ask 0.10 to 0.90 inclusive (1e-9 slack) and at least 1 contract displayed at it; else no trade (counted). Held to settlement. Fee 0.07 p (1-p) rounded UP to the cent per order (1 contract); stress fee = 1.2 x that rounded fee.
Scoring: only windows closing at or after SCORE_FROM = 2026-11-19T00:00:00Z. Earlier windows are never scored. Result from coverage.csv.gz (yes / no); a final value that is neither yes nor no is booked void AT ONCE (fee only); an empty result is pending, and after 7 days past the close UNRESOLVED: left out of n, never booked, reported with its count and dates (proposed, F2, pending the Head's ruling).
Definitions the registration leaves open (the exchange-time offset is a ROLLING median of the last 120 readable Date headers at each row, where the registration says 'median over the run'; fill polls are searched only in the look poll's own run folder, so a look at the end of a folder whose fill poll is in the next folder is lost and counted as 'no entry poll'), fixed here and frozen with this file's hash: thirds and halves = contiguous groups of US Central dates (ceil(n_days/3), ceil(n_days/2)); z = day-clustered mean daily net over its standard error (sample sd, days >= 3, one-sided); US Central date = America/Chicago of the close; cash PF = gross wins / gross losses (infinity with no loss).
Minimum: nothing but the scored count is printed below 3,400 scored cell trades (registered). Labels (registered): 'no evidence at n = x' under 100; FALSIFIED on cash PF under 1.0 pooled with n >= 1,000; the bar: n >= 3,400, cash PF >= 1.5 pooled and in each third, both halves > 1.0, mean net > 0 at fee x1.2, z >= 5.46; otherwise 'keep recording'. Never called a research-bar pass."""
import sys, os, csv, gzip, math, statistics, collections, time, glob, calendar, re, datetime
from pathlib import Path
SERIES = ("KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M", "KXAUDUSD15M", "KXUSDCAD15M", "KXNATGAS15M")
SCORE_FROM = calendar.timegm(time.strptime("2026-11-19", "%Y-%m-%d"))
EPS, LOOK_S, EARLY_S, FILL_MIN_S, FILL_MAX_S, IMB_MIN, BAND, VOID_AFTER_S, OFFSET_ROWS = 1e-9, 600, 10, 1.0, 20.0, 0.50, (0.10, 0.90), 7 * 86400, 120
MIN_N, Z_BAR = 3400, 5.46
def fee_up(p): return math.ceil(0.07 * p * (1 - p) * 100 - 1e-9) / 100
def pf(v):
    """cash PF; None for NO trades (an empty group fails every bar test); infinity only for wins and no loss"""
    if not v: return None
    a = sum(x for x in v if x > 0); b = -sum(x for x in v if x < 0); return a / b if b else float("inf")
def ge(x, bar): return x is not None and x >= bar
def gt(x, bar): return x is not None and x > bar
def ptxt(x): return "n/a (no trades)" if x is None else "%.2f" % x
def _f(x):
    try:
        v = float(x); return v if v == v else None
    except (TypeError, ValueError): return None
def _iso(s):
    try: return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None
def _hdr(s):
    try:
        from email.utils import parsedate_to_datetime; return parsedate_to_datetime(s).timestamp()
    except Exception: return None
def rows_of(path):
    with gzip.open(path, "rt", newline="") as f: yield from csv.DictReader(f)
def imb5(row):
    y = sum(s for s in (_f(row.get("yes_bid_sz_%d" % i)) for i in range(1, 6)) if s is not None); n = sum(s for s in (_f(row.get("no_bid_sz_%d" % i)) for i in range(1, 6)) if s is not None)
    return (y - n) / (y + n) if y + n > 0 else None
class Run:
    def __init__(self, path):
        rows = [r for r in rows_of(os.path.join(path, "book.csv.gz")) if _f(r.get("t_recv_ms")) is not None]
        rows.sort(key=lambda r: float(r["t_recv_ms"])); self.rows = rows; buf = collections.deque(maxlen=OFFSET_ROWS); self.by = collections.defaultdict(list)
        for i, r in enumerate(rows):
            h = _hdr(r.get("server_date_header") or "")
            if h is not None: buf.append(h + 0.5 - float(r["t_recv_ms"]) / 1000)
            if buf: self.by[r.get("ticker")].append((float(r["t_recv_ms"]) / 1000 + statistics.median(buf), i))
def load_coverage(runs):
    cov = {}
    for p in runs:
        f = os.path.join(p, "coverage.csv.gz")
        if os.path.exists(f):
            for r in rows_of(f):
                if r.get("ticker"):
                    old = cov.get(r["ticker"])
                    if old is None or (r.get("result") in ("yes", "no") and old.get("result") not in ("yes", "no")): cov[r["ticker"]] = r
    return cov
def iso(t): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
def central_day(ts): return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).astimezone(__import__("zoneinfo").ZoneInfo("America/Chicago")).date()
def replay(root, now=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import heldout_guard_v2 as G; G.refuse_heldout(str(root), "nc15depth1")
    runs = sorted(os.path.dirname(f) for f in glob.glob(os.path.join(root, "*", "*", "book.csv.gz")))
    cov = load_coverage(runs); now = time.time() if now is None else now
    R = {p: Run(p) for p in runs}; tick_runs = collections.defaultdict(set)
    for p, run in R.items():
        for tk in run.by: tick_runs[tk].add(p)
    recs, why = [], collections.Counter()
    for tk, rs in sorted(tick_runs.items()):
        ser = tk.split("-")[0]
        if ser not in SERIES: continue
        close = None
        for p in sorted(rs):
            for _, i in R[p].by[tk][:1]: close = _iso(R[p].rows[i].get("close_time") or "")
            if close: break
        if not close: why["no close time"] += 1; continue
        if close < SCORE_FROM: why["closes before 2026-11-19 (never scored)"] += 1; continue
        D = close - LOOK_S
        cand = [(t, p, i, pos) for p in sorted(rs) for pos, (t, i) in enumerate(R[p].by[tk]) if D - EARLY_S - EPS <= t <= D + EPS]
        if not cand: why["no look poll"] += 1; continue
        t0, p0, i0, pos0 = max(cand, key=lambda c: (c[0], c[1])); run = R[p0]; im = imb5(run.rows[i0])
        if im is None: why["no book sizes"] += 1; continue
        if abs(im) < IMB_MIN - EPS: why["not in the cell"] += 1; continue
        side = "yes" if im > 0 else "no"
        fill = next(((t, i) for t, i in run.by[tk][pos0 + 1:] if t >= t0 + FILL_MIN_S - EPS), None)
        if fill is None or fill[0] > t0 + FILL_MAX_S + EPS: why["no entry poll in 1 s to 20 s"] += 1; continue
        row = run.rows[fill[1]]
        px, sz = (_f(row.get("no_bid_px_1")), _f(row.get("no_bid_sz_1"))) if side == "yes" else (_f(row.get("yes_bid_px_1")), _f(row.get("yes_bid_sz_1")))
        if px is None or sz is None: why["no best ask"] += 1; continue
        ask = 1 - px
        if not (BAND[0] - EPS <= ask <= BAND[1] + EPS) or sz < 1 - 1e-12: why["ask outside 0.10 to 0.90 or under 1 contract displayed"] += 1; continue
        res = (cov.get(tk) or {}).get("result"); fee = fee_up(ask)
        rec = dict(ticker=tk, close=close, side=side, p=ask, fee=fee, day=central_day(close))
        if res in ("yes", "no"): rec.update(result="scored", win=1 if res == side else 0)
        elif res not in (None, ""): rec.update(result="void", win=0)
        else: rec.update(result="pending" if now - close < VOID_AFTER_S else "unresolved")      # F2 (proposed, pending the Head's ruling): an empty result is never booked; after 7 days it is UNRESOLVED, left out of n and listed
        if rec["result"] in ("scored", "void"):
            rec["cash"] = (rec["win"] - ask - fee) if rec["result"] == "scored" else -fee
            rec["cash12"] = (rec["win"] - ask - 1.2 * fee) if rec["result"] == "scored" else -1.2 * fee
        recs.append(rec)
    return recs, why
def zscore(trades):
    d = collections.defaultdict(float)
    for t in trades: d[t["day"]] += t["cash"]
    v = list(d.values())
    if len(v) < 3: return float("nan")
    m = sum(v) / len(v); s = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    return m / (s / math.sqrt(len(v))) if s > 0 else float("inf")
def groups(trades, k):
    days = sorted({t["day"] for t in trades}); n = len(days); c = math.ceil(n / k); out = []
    for i in range(k): out.append([t for t in trades if t["day"] in set(days[i * c:(i + 1) * c])])
    return out
def report(recs, why):
    sc = [t for t in recs if t["result"] in ("scored", "void")]; pend = sum(1 for t in recs if t["result"] == "pending"); unres = sorted(t["close"] for t in recs if t["result"] == "unresolved")
    L = ["NC15DEPTH1 | cell trades with a result %d (pending %d, UNRESOLVED after 7 days %d%s) | windows lost: %s" % (len(sc), pend, len(unres), (": closes %s to %s" % (iso(unres[0]), iso(unres[-1]))) if unres else "", dict(why))]
    n = len(sc)
    if n < MIN_N: L.append("no evidence at n = %d. BELOW THE REGISTERED MINIMUM (%d scored cell trades needed): no figure is read" % (n, MIN_N)); return L
    cash = [t["cash"] for t in sc]; c12 = [t["cash12"] for t in sc]; th = groups(sc, 3); hv = groups(sc, 2); z = zscore(sc)
    L.append("n %d | cash PF %.2f | mean %+.2fc | win %.1f%% | days %d | z %.2f (bar %.2f)" % (n, pf(cash), 100 * sum(cash) / n, 100 * sum(t["win"] for t in sc) / n, len({t["day"] for t in sc}), z, Z_BAR))
    L.append("thirds by date: " + " / ".join("n %d PF %s" % (len(x), ptxt(pf([t["cash"] for t in x]))) for x in th))
    L.append("halves by date: " + " / ".join("n %d PF %s" % (len(x), ptxt(pf([t["cash"] for t in x]))) for x in hv))
    L.append("fee x1.2: mean %+.2fc | cash PF %.2f" % (100 * sum(c12) / n, pf(c12)))
    clear = n >= MIN_N and ge(pf(cash), 1.5) and all(ge(pf([t["cash"] for t in x]), 1.5) for x in th) and all(gt(pf([t["cash"] for t in x]), 1.0) for x in hv) and sum(c12) > 0 and z >= Z_BAR
    L.append("LABEL: " + ("FALSIFIED (cash PF under 1.0 pooled, n >= 1,000)" if pf(cash) is not None and pf(cash) < 1.0 and n >= 1000 else ("cleared its registered bar (never called a research-bar pass)" if clear else "keep recording")))
    return L
if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    root = Path(sys.argv[1]).resolve()
    if not (root / "MADE_UP_DATA").exists() and os.environ.get("NC15DEPTH1_READ") != "1": sys.exit("REFUSED: %s has no MADE_UP_DATA; the real read needs NC15DEPTH1_READ=1 on the Head's word (from 2026-11-19)" % root)
    import heldout_guard_v2 as G; print(G.list_line())
    print("\n".join(report(*replay(str(root)))))
