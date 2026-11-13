"""NC15 depth-cell wheel REPLAY SCORER (Desk A, Nov 13 2026), built to DESK_A_FROZEN_WHEEL_DEFINITIONS_NOV13.md v4 (commit 8679f760, 2026-11-13T00:23:49Z), sections 0 and 2. Offline, reads only a folder of run folders <date>/<HHMM>/{book,coverage}.csv.gz (the nc15 shape), sends nothing.
  python3 -I nc15_wheel_replay.py <root> [--series KXCOPPER15M,...] [--since ISO]     DEFAULT-CLOSED: refuses a folder without MADE_UP_DATA unless WHEEL_BLOCK_READ=1 is set (a block read, on the Head's word); HELDOUT_ paths refused.
Per series (the admitted seven by default: copper, WTI, natural gas, HYPE, BNB, silver, USD/CAD; EUR/USD, GBP/USD, USD/JPY and AUD/USD are withdrawn by the sheet), one decision per window: D = close - 600 s exact, exchange time; signal poll = the last poll with exchange time in [D-10, D]; exchange time = t_recv/1000 + offset, offset = median over the 120 most recent rows of the SAME run folder (any ticker, by receive time, at or before the poll, readable Date header only) of (Date header seconds + 0.5 - t_recv/1000); imb5 = (sum YES bid sizes - sum NO bid sizes)/total over the recorded levels; in the cell if |imb5| >= 0.50 (1e-9 tolerance); imb5 > 0 buys YES, < 0 buys NO; implied ask (YES: 1 - NO bid 1, NO: 1 - YES bid 1) in 0.10..0.90 inclusive (1e-9) else no signal; 10 contracts, limit = ask + 0.01; ladder = the levels the order meets (YES buy meets NO bids: ask = 1 - bid price, sorted by ask), 'offers 10' = sizes at or under limit + 1e-9 sum to 10 or more; walked price = size-weighted average ask of the first 10 contracts; second poll = the NEXT poll of the same ticker (same run folder) and at most 6 s after the signal poll, else 'not fill-checked' (not counted toward a block); fillable = both polls offer 10; fill price = the HIGHER of the two walked prices; fee = fee_up_order(p) = ceil(0.07 x 10 x p x (1 - p) x 100 - 1e-9)/100; cash = 10 x (win - p) - fee, hold to settlement; result = the coverage row's `result` (yes or no); missing = PENDING (listed for the kalshi-pull result job); 7 days after the close still without a yes or no = VOID (price refunded, fee kept: cash = -fee). Counts from the sheet's commit time: a decision instant earlier is not counted (default --since 2026-11-13T00:23:49Z). Missing items are 'no signal', counted by reason."""
import sys, os, csv, gzip, io, math, bisect, statistics, collections, time, glob, calendar, re
from pathlib import Path
SHEET_COMMIT_TS = calendar.timegm(time.strptime("2026-11-13T00:23:49", "%Y-%m-%dT%H:%M:%S"))
ADMITTED = ("KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXHYPE15M", "KXBNB15M", "KXUSDCAD15M", "KXNATGAS15M")
EPS = 1e-9; SIZE = 10; LOOK_S = 600; EARLY_S = 10; SECOND_MAX_S = 6; SLIP = 0.01; IMB_MIN = 0.50; BAND = (0.10, 0.90); VOID_AFTER_S = 7 * 86400; OFFSET_ROWS = 120
def fee_up_order(p, contracts=SIZE): return math.ceil(0.07 * contracts * p * (1 - p) * 100 - 1e-9) / 100
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
def ladder(row, side):
    """levels the order meets: YES buy meets the NO bids, NO buy the YES bids; [(ask, size)] sorted by ask; only levels with a readable price and size."""
    pre = "no_bid" if side == "yes" else "yes_bid"; out = []
    for i in range(1, 6):
        p, s = _f(row.get("%s_px_%d" % (pre, i))), _f(row.get("%s_sz_%d" % (pre, i)))
        if p is not None and s is not None and s > 0: out.append((1 - p, s))
    return sorted(out)
def offers(lad, limit): return sum(s for a, s in lad if a <= limit + EPS) >= SIZE - 1e-12
def walked(lad):
    need = float(SIZE); cost = 0.0
    for a, s in lad:
        t = min(s, need); cost += a * t; need -= t
        if need <= 1e-12: break
    return cost / SIZE
def imb5(row):
    y = sum(s for s in (_f(row.get("yes_bid_sz_%d" % i)) for i in range(1, 6)) if s is not None); n = sum(s for s in (_f(row.get("no_bid_sz_%d" % i)) for i in range(1, 6)) if s is not None)
    return (y - n) / (y + n) if y + n > 0 else None
class Run:
    """one run folder: rows by receive time with the exchange offset at each row (rolling median of the last 120 readable headers at or before that row)."""
    def __init__(self, path):
        self.path = path; rows = [r for r in rows_of(os.path.join(path, "book.csv.gz"))]
        rows = [r for r in rows if _f(r.get("t_recv_ms")) is not None]; rows.sort(key=lambda r: float(r["t_recv_ms"])); self.rows = rows; self.off = []
        buf = collections.deque(maxlen=OFFSET_ROWS)
        for r in rows:
            h = _hdr(r.get("server_date_header") or "")
            if h is not None: buf.append(h + 0.5 - float(r["t_recv_ms"]) / 1000)
            self.off.append(statistics.median(buf) if buf else None)
        self.by = collections.defaultdict(list)
        for i, r in enumerate(rows):
            if self.off[i] is not None: self.by[r.get("ticker")].append((float(r["t_recv_ms"]) / 1000 + self.off[i], i))
    def polls(self, tk): return self.by.get(tk, [])
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
def replay(root, series=ADMITTED, since=SHEET_COMMIT_TS, now=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import heldout_guard; heldout_guard.refuse_heldout(str(root), "nc15 wheel replay")      # standing rule (h): on every entry point, not only the command line
    runs = sorted(os.path.dirname(f) for f in glob.glob(os.path.join(root, "*", "*", "book.csv.gz")))
    cov = load_coverage(runs); now = time.time() if now is None else now
    closes = {}; tick_runs = collections.defaultdict(set)
    R = {}
    for p in runs:
        run = R[p] = Run(p)
        for tk in run.by:
            tick_runs[tk].add(p)
    recs = []; reasons = collections.Counter()
    for tk, rs in sorted(tick_runs.items()):
        ser = tk.split("-")[0]
        if ser not in series: continue
        # close time: the row's close_time column (exchange time); first readable
        close = None
        for p in sorted(rs):
            for _, i in R[p].polls(tk)[:1]:
                close = _iso(R[p].rows[i].get("close_time") or "")
            if close: break
        if not close: reasons["no close time"] += 1; continue
        D = close - LOOK_S
        if D < since - 1e-9: reasons["before the sheet's commit time"] += 1; continue
        cand = []                                              # (exchange time, run, row index, position in that run's ticker list)
        for p in sorted(rs):
            lst = R[p].polls(tk)
            for pos, (t, i) in enumerate(lst):
                if D - EARLY_S - EPS <= t <= D + EPS: cand.append((t, p, i, pos))
        if not cand: reasons["no signal poll"] += 1; continue
        t0, p0, i0, pos0 = max(cand, key=lambda c: (c[0], c[1])); run = R[p0]; row = run.rows[i0]
        im = imb5(row)
        yb, nb = _f(row.get("yes_bid_px_1")), _f(row.get("no_bid_px_1"))
        if im is None or yb is None or nb is None: reasons["missing side of the book"] += 1; continue
        if abs(im) < IMB_MIN - EPS: reasons["not in the cell"] += 1; continue
        side = "yes" if im > 0 else "no"; ask = (1 - nb) if side == "yes" else (1 - yb)
        if not (BAND[0] - EPS <= ask <= BAND[1] + EPS): reasons["ask outside 0.10 to 0.90"] += 1; continue
        limit = ask + SLIP; lad0 = ladder(row, side)
        lst = run.polls(tk); nxt = lst[pos0 + 1] if pos0 + 1 < len(lst) else None
        rec = dict(ticker=tk, series=ser, close=close, signal_t=t0, side=side, ask=ask, limit=limit, imb5=im)
        if nxt is None or nxt[0] - t0 > SECOND_MAX_S + EPS: rec.update(status="not fill-checked"); recs.append(rec); reasons["not fill-checked"] += 1; continue
        row2 = run.rows[nxt[1]]; lad1 = ladder(row2, side)
        if not (offers(lad0, limit) and offers(lad1, limit)): rec.update(status="miss"); recs.append(rec); reasons["miss (a poll does not offer 10)"] += 1; continue
        p = max(walked(lad0), walked(lad1)); rec.update(status="fillable", price=p, fee=fee_up_order(p))
        res = (cov.get(tk) or {}).get("result")
        if res in ("yes", "no"): rec["win"] = 1 if res == side else 0; rec["cash"] = SIZE * (rec["win"] - p) - rec["fee"]; rec["result"] = "scored"
        elif res not in (None, "") and res not in ("yes", "no"): rec["cash"] = -rec["fee"]; rec["win"] = 0; rec["result"] = "void"      # a final value that is neither yes nor no (for example void) is booked void AT ONCE (sheet section 0); an empty result is missing
        elif now - close >= VOID_AFTER_S: rec["cash"] = -rec["fee"]; rec["win"] = 0; rec["result"] = "void"
        else: rec["result"] = "pending"
        recs.append(rec)
    return recs, reasons
def report(recs, reasons):
    out = []
    for ser in sorted({r["series"] for r in recs}):
        rs = [r for r in recs if r["series"] == ser]; f = [r for r in rs if r["status"] == "fillable"]; sc = [r for r in f if r["result"] in ("scored", "void")]
        w = sum(r["cash"] for r in sc if r["cash"] > 0); l = -sum(r["cash"] for r in sc if r["cash"] < 0)
        out.append("%s: signals %d | fillable %d | miss %d | not fill-checked %d | scored %d (void %d) pending %d | net $%.2f | cash PF %s" % (ser, len(rs), len(f), sum(r["status"] == "miss" for r in rs), sum(r["status"] == "not fill-checked" for r in rs), len(sc), sum(r["result"] == "void" for r in sc), sum(r["result"] == "pending" for r in f), sum(r["cash"] for r in sc), ("%.2f" % (w / l)) if l else ("inf" if w else "n/a")))
    out.append("no signal, by reason: %s" % dict(reasons)); out.append("pending tickers for the result job: %s" % sorted({r["ticker"] for r in recs if r.get("result") == "pending"})[:50])
    return out
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: sys.exit(__doc__)
    root = Path(a[0]).resolve(); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import heldout_guard; heldout_guard.refuse_heldout(str(root), "nc15 wheel replay")
    if not (root / "MADE_UP_DATA").exists() and os.environ.get("WHEEL_BLOCK_READ") != "1": sys.exit("REFUSED: not a made-up folder and WHEEL_BLOCK_READ=1 is not set (a block read is on the Head's word)")
    ser = ADMITTED; since = SHEET_COMMIT_TS
    for x in sys.argv[1:]:
        if x.startswith("--series="): ser = tuple(x.split("=", 1)[1].split(","))
        if x.startswith("--since="): since = _iso(x.split("=", 1)[1])
    recs, reasons = replay(str(root), ser, since); print("\n".join(report(recs, reasons)))
