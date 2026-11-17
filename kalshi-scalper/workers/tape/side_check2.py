"""taker_side check, second pre-registered read, to TAKER_SIDE_CHECK2_PROTOCOL_NOV17.md (rules fixed before any look). python3 -I side_check2.py <root holding perplive/2026-11-17/HHMM/{book,book_fast,tape}.csv.gz and tape/2026-11-17/HHMM/tape.csv.gz> <out.txt> [--no-allow]
Reads tape.csv.gz (both trees), book.csv.gz and book_fast.csv.gz of 2026-11-17 only. Prices and quotes only. The quote window is 3000 ms (the first check used 10000)."""
import sys, os, csv, gzip, hashlib, bisect, collections, calendar, re
HERE = os.path.dirname(os.path.abspath(__file__)); ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md"); ALLOW_MARK = "readable ONLY by Desk A's taker side check 2"
DAY = "2026-11-17"; T8 = ["KXBTCPERP", "KXETHPERP", "KXGOLDPERP", "KXSILVERPERP", "KXUS500PERP", "KXUSTECH100PERP", "KXHYPEPERP", "KXBNBPERP"]
TS = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?Z$")
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def ms_of(s):
    m = TS.match(s)
    if not m: raise ValueError("bad created_time %r" % s)
    y, mo, d, h, mi, se = (int(m.group(i)) for i in range(1, 7)); return calendar.timegm((y, mo, d, h, mi, se)) * 1000 + int((m.group(7) or "").ljust(9, "0")[:9]) // 10 ** 6, "%04d-%02d-%02d" % (y, mo, d)
def files_of(root):
    out = []
    for top, names in (("perplive", ("tape.csv.gz", "book.csv.gz", "book_fast.csv.gz")), ("tape", ("tape.csv.gz",))):
        base = os.path.join(root, top, DAY)
        if not os.path.isdir(base): continue
        for hh in sorted(os.listdir(base)):
            for f in names:
                p = os.path.join(base, hh, f)
                if os.path.exists(p): out.append(p)
    return out
def list_sha(root, files): return hashlib.sha256("\n".join("%s %s" % (os.path.relpath(p, root), sha(p)) for p in sorted(files)).encode()).hexdigest()
def refuse_unless_allowed(root, files):
    me = sha(os.path.abspath(__file__)); ls = list_sha(root, files)
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow file cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "side_check2.py" in line and me in line and ls in line: return ls
    raise SystemExit("REFUSED: no allow line names side_check2.py sha256 %s and the file list sha256 %s" % (me, ls))
def run(root, out, check_allow=True):
    files = files_of(root); ls = refuse_unless_allowed(root, files) if check_allow else "no-allow-check (invented fixture)"
    books = collections.defaultdict(list)                                     # ticker -> [(t_send_ms, bid1, ask1)]
    trades = {}; N = collections.Counter()
    for p in files:
        name = os.path.basename(p)
        with gzip.open(p, "rt", newline="") as fh:
            rd = csv.reader(fh); head = next(rd); ix = {c: i for i, c in enumerate(head)}
            for r in rd:
                if name.startswith("book"):
                    try: b, a = float(r[ix["bid_px_1"]]), float(r[ix["ask_px_1"]])
                    except ValueError: continue
                    books[r[ix["ticker"]]].append((int(r[ix["t_send_ms"]]), b, a))
                else:
                    t_ms, day = ms_of(r[ix["created_time"]])
                    if day != DAY: N["trade_other_date"] += 1; continue
                    if r[ix["is_block_trade"]].strip().lower() != "false": N["block_rows_left_out"] += 1; continue
                    if r[ix["taker_side"]] not in ("bid", "ask"): N["other_string"] += 1; continue
                    key = (r[ix["ticker"]], r[ix["created_time"]], r[ix["price"]], r[ix["count"]], r[ix["taker_side"]], r[ix["is_block_trade"]]); tr = int(r[ix["t_recv_ms"]])
                    trades.setdefault(key, []).append((tr, t_ms))
    for tk in books: books[tk].sort()
    C = collections.defaultdict(collections.Counter)
    for key, g in trades.items():
        m0 = min(x[0] for x in g); keep = [x for x in g if x[0] == m0]; tk, _, px, _, side, _ = key; px = float(px); t_ms = keep[0][1]
        for _ in keep:
            bk = books.get(tk, []); i = bisect.bisect_right(bk, (t_ms, float("inf"), float("inf"))) - 1
            if i < 0 or t_ms - bk[i][0] > 3000 or not bk[i][1] < bk[i][2]: N["no_quote"] += 1; continue
            cls = "above_ask" if px >= bk[i][2] else ("below_bid" if px <= bk[i][1] else "inside")
            for grp in ("ALL", tk if tk in T8 else "OTHER"): C[(grp, side)][cls] += 1
    L = ["side_check output; files %d; list sha256 %s" % (len(files), ls), "counts " + str(dict(N))]
    for grp in ["ALL"] + T8 + ["OTHER"]:
        for side in ("bid", "ask"):
            c = C[(grp, side)]; n = sum(c.values()); L.append("%s %s n=%d above_ask=%d below_bid=%d inside=%d shares %s" % (grp, side, n, c["above_ask"], c["below_bid"], c["inside"], " ".join("%.3f" % (c[k] / n) if n else "na" for k in ("above_ask", "below_bid", "inside"))))
    def sh(g, s, k): c = C[(g, s)]; n = sum(c.values()); return (c[k] / n if n else 0.0), n
    ba, nb = sh("ALL", "bid", "above_ask"); ab, na = sh("ALL", "ask", "below_bid"); bb, _ = sh("ALL", "bid", "below_bid"); aa, _ = sh("ALL", "ask", "above_ask")
    verdict = "NO MAPPING"
    if nb >= 1000 and na >= 1000:
        if ba >= 0.80 and ab >= 0.80: verdict = "MAPPING A: bid = taker bought (buy), ask = taker sold (sell)"
        elif bb >= 0.80 and aa >= 0.80: verdict = "MAPPING B: bid = sell, ask = buy"
    ok = 0; q = 0
    for tk in T8:
        cb, ca = C[(tk, "bid")], C[(tk, "ask")]
        if sum(cb.values()) >= 100 and sum(ca.values()) >= 100:
            q += 1
            if verdict.startswith("MAPPING A") and cb["above_ask"] / sum(cb.values()) >= 0.8 and ca["below_bid"] / sum(ca.values()) >= 0.8: ok += 1
            if verdict.startswith("MAPPING B") and cb["below_bid"] / sum(cb.values()) >= 0.8 and ca["above_ask"] / sum(ca.values()) >= 0.8: ok += 1
    L.append("verdict (fixed threshold 0.80, at least 1000 per side): " + verdict); L.append("tickers qualifying (100+ each side) %d, with the same pattern at 0.80: %d (6 of 8 needed if 6 or more qualify)" % (q, ok))
    open(out, "w").write("\n".join(L) + "\n"); print("output sha256", sha(out), "list", ls)
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--no-allow"]
    if len(a) != 2: sys.exit(__doc__)
    run(a[0], a[1], check_allow="--no-allow" not in sys.argv)
