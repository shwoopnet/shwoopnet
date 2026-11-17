"""Perps trade tape to 1 minute bars, Desk A's build (Nov 17, 2026), to PERPS_TAPE60_AMENDMENT_NOV17.md sections 2, 6, 7 and 8 (the CURRENT text: Main's per-date files with all tickers, no trade_id).
  python3 -I tape_bars.py <tape dir holding YYYY-MM-DD.csv.gz> <ticker list file, one per line> <out bars.csv> <out summary.csv> --from YYYY-MM-DD --to YYYY-MM-DD [--no-allow]
Only the files dated in [from, to] are listed, hashed and opened; a range must lie wholly in DEVELOPMENT (2026-09-18 to 2026-10-27) or wholly in HELD-OUT (2026-10-28 to 2026-11-15); a range across the boundary is REFUSED, and any file dated 2026-11-16 or later is REFUSED (HOLDS forward_default_deny_from). A row whose created_time is not on its file's own date is counted and dropped (it is taken from the file of its own date). The shared MECH1 HOLDS check (pinned version) drops and counts any held ticker-time.
Allow line (HELDOUT_PULL_RUNS.md above this folder): mark, "tape_bars.py", this file's sha256 and the sha256 of the sorted "<file name> <sha256>" list of the files read. The wall: the ticker column is read FIRST and a row of another ticker is counted and never parsed further.
Row: t_recv_ms, server_date_header, ticker, created_time, price, count, taker_side, is_block_trade. Bar end = first whole minute STRICTLY after created_time. Block trades are out of OHLC, volume, n_trades and the side volumes (block_volume and block_count only). Order in a bar: exact created_time, ties by REVERSE FILE ORDER. Dedupe: same six fields with DIFFERENT t_recv_ms = one trade seen twice (earliest t_recv_ms kept); same t_recv_ms rows are all kept."""
import sys, os, csv, gzip, re, hashlib, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mech"))
import mech1_generate as G                                      # the shared HOLDS check (load_holds, held)
DEV = ("2026-09-18", "2026-10-27"); HELD = ("2026-10-28", "2026-11-15")
from decimal import Decimal
HERE = os.path.dirname(os.path.abspath(__file__)); ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md"); ALLOW_MARK = "readable ONLY by Desk A's tape bar builder"
TS = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(?:Z|\+00:00)$")
def parse_ns(s):
    m = TS.match(s)
    if not m: raise ValueError("bad created_time %r" % s)
    import calendar
    y, mo, d, h, mi, se = (int(m.group(i)) for i in range(1, 7)); frac = (m.group(7) or "").ljust(9, "0")
    return calendar.timegm((y, mo, d, h, mi, se)) * 10 ** 9 + int(frac)
def fmt(x): return "%.17g" % x
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def list_sha(files): return hashlib.sha256("\n".join("%s %s" % (os.path.basename(p), sha(p)) for p in sorted(files)).encode()).hexdigest()
def refuse_unless_allowed(files):
    me = sha(os.path.abspath(__file__)); ls = list_sha(files)
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow file cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "tape_bars.py" in line and me in line and ls in line: return ls
    raise SystemExit("REFUSED: no allow line names tape_bars.py sha256 %s and the file list sha256 %s" % (me, ls))
def build_file(path, tickers, file_date):
    """-> (bars {ticker: {end_ts: row}}, summary {ticker: counters}) for ONE date file."""
    rows = collections.defaultdict(list); other = 0; dr = collections.Counter()
    with gzip.open(path, "rt", newline="") as fh:
        rd = csv.reader(fh); head = next(rd); ix = {c: i for i, c in enumerate(head)}
        for need in ("t_recv_ms", "ticker", "created_time", "price", "count", "taker_side", "is_block_trade"):
            if need not in ix: raise SystemExit("missing column " + need)
        for n, r in enumerate(rd):
            tk = r[ix["ticker"]]                                              # the wall: ticker first
            if tk not in tickers: other += 1; continue
            rows.setdefault(tk, []); dr[(tk, "rows_read")] += 1
            t_ns = parse_ns(r[ix["created_time"]]); sec = t_ns // 10 ** 9
            if G.day_of(sec) != file_date: dr[(tk, "rows_other_date")] += 1; continue          # taken from the file of its own date
            if G.held(tk, sec): dr[(tk, "rows_held")] += 1; continue
            rows[tk].append((n, r, ix))
    bars = {}; summ = {}
    for tk, items in rows.items():
        S = collections.Counter(); S["rows_read"] = dr[(tk, "rows_read")]; S["rows_other_date"] = dr[(tk, "rows_other_date")]; S["rows_held"] = dr[(tk, "rows_held")]
        groups = collections.defaultdict(list)
        for n, r, ix in items:
            key = tuple(r[ix[c]] for c in ("ticker", "created_time", "price", "count", "taker_side", "is_block_trade")); groups[key].append((n, r, ix, int(r[ix["t_recv_ms"]])))
        kept = []
        for key, g in groups.items():
            m0 = min(x[3] for x in g); keep = [x for x in g if x[3] == m0]
            S["merged_by_repeat"] += len(g) - len(keep); S["kept_same_recv"] += len(keep) - 1       # a repeat on a later page is dropped; equal t_recv_ms rows are real repeated prints
            kept += [(x[0], x[1], x[2], key, x[3]) for x in keep]
        S["rows_kept"] = len(kept); prices = set(); per = collections.defaultdict(list)
        for n, r, ix, key, tr in kept:
            t_ns = parse_ns(r[ix["created_time"]]); end = (t_ns // (60 * 10 ** 9) + 1) * 60
            blk = r[ix["is_block_trade"]].strip().lower()
            if blk not in ("true", "false"): raise SystemExit("bad is_block_trade %r" % r[ix["is_block_trade"]])
            cnt_s = r[ix["count"]]
            if not re.fullmatch(r"\d+", cnt_s): raise ValueError("bad count %r" % cnt_s)
            px = Decimal(r[ix["price"]])
            if not px > 0: raise ValueError("bad price")
            per[end].append((t_ns, -n, px, int(cnt_s), r[ix["taker_side"]], blk == "true"))
        out = {}
        for end, L in per.items():
            L.sort(key=lambda x: (x[0], x[1]))                                 # exact time, ties by REVERSE file order (a later file row printed first)
            nb = [x for x in L if not x[5]]; bl = [x for x in L if x[5]]
            S["block_rows"] += len(bl)
            if not nb: S["bars_only_block"] += 1; S["block_volume_in_those"] += sum(x[3] for x in bl); continue
            for x in nb: prices.add(x[2]); 
            unk = sum(1 for x in nb if x[4] not in ("buy", "sell")); S["unknown_side_trades"] += unk
            out[end] = [tk, end, nb[0][2], max(x[2] for x in nb), min(x[2] for x in nb), nb[-1][2], sum(x[3] for x in nb), len(nb), sum(x[3] for x in nb if x[4] == "buy"), sum(x[3] for x in nb if x[4] == "sell"), sum(x[3] for x in bl), len(bl)]
        S["bars_written"] = len(out); sp = sorted(prices); S["tick"] = min((b - a for a, b in zip(sp, sp[1:])), default=None)
        bars[tk] = out; summ[tk] = S
    return bars, summ
def main(tape_dir, tickers_file, out_bars, out_summ, d_from, d_to, check_allow=True):
    tickers = {l.strip() for l in open(tickers_file) if l.strip()}
    if not ((DEV[0] <= d_from <= d_to <= DEV[1]) or (HELD[0] <= d_from <= d_to <= HELD[1])): raise SystemExit("REFUSED: the range %s to %s is not wholly in development %s or wholly in held-out %s" % (d_from, d_to, DEV, HELD))
    files = sorted(os.path.join(tape_dir, f) for f in os.listdir(tape_dir) if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.csv\.gz", f) and d_from <= f[:10] <= d_to)
    ls = refuse_unless_allowed(files) if check_allow else "no-allow-check (invented fixture)"
    G.load_holds()
    allbars = {}; lines_s = ["file,ticker,rows_read,rows_kept,merged_by_repeat,kept_same_recv,block_rows,unknown_side_trades,bars_written,bars_only_block,block_volume_in_those,tick,rows_other_date,rows_held"]
    for p in files:
        bars, summ = build_file(p, tickers, os.path.basename(p)[:10])
        for tk, rws in bars.items():
            for end, row in rws.items():
                if (tk, end) in allbars: raise SystemExit("a bar appears in two date files: " + tk + " " + str(end))
                allbars[(tk, end)] = row
        for tk in sorted(summ):
            S = summ[tk]; lines_s.append(",".join([os.path.basename(p), tk] + [str(S[k]) if k != "tick" else ("" if S[k] is None else fmt(float(S[k]))) for k in ("rows_read", "rows_kept", "merged_by_repeat", "kept_same_recv", "block_rows", "unknown_side_trades", "bars_written", "bars_only_block", "block_volume_in_those", "tick")] + [str(S["rows_other_date"]), str(S["rows_held"])]))
    lines = ["ticker,end_ts,open,high,low,close,volume,n_trades,buy_volume,sell_volume,block_volume,block_count"]
    for k in sorted(allbars):
        r = allbars[k]; lines.append(",".join([r[0], str(r[1])] + [fmt(float(x)) for x in r[2:6]] + [str(x) for x in r[6:]]))
    open(out_bars, "w").write("\n".join(lines) + "\n"); open(out_summ, "w").write("\n".join(lines_s) + "\n")
    print("bars", len(allbars), "bars sha256", sha(out_bars), "summary sha256", sha(out_summ), "list", ls)
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--no-allow"]
    if len(a) != 8 or a[4] != "--from" or a[6] != "--to": sys.exit(__doc__)
    main(a[0], a[1], a[2], a[3], a[5], a[7], check_allow="--no-allow" not in sys.argv)
