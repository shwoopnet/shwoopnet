#!/usr/bin/env python3
"""60-day tape, 1 minute bar builder, BUILD 2 (Testing Desk, Nov 17, 2026), blind from Desk A's PERPS_TAPE60_AMENDMENT_NOV17.md at be97878d7 (sha256 fe3d8144a845303571cad5cb53dc82fdfd681a06dcea029b20c684d6914f7e71): sections 2 and 6 (bars, readings T1 to T18) as changed by sections 7 and 8 (one file per UTC date holding all tickers, no trade_id, dedupe by the six fields and the earliest t_recv_ms, ties by reverse file order). Pure functions on rows; the file reader below checks an allow line.
Rows: dicts with file, t_recv_ms, ticker, created_time, price, count, taker_side, is_block_trade (strings as stored)."""
import calendar, collections, csv, glob, gzip, hashlib, os, re, sys
from decimal import Decimal, InvalidOperation

TIME_RE = re.compile(r"^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.(\d{1,9}))?(?:Z|\+00:00)$")
COLS = ("t_recv_ms", "ticker", "created_time", "price", "count", "taker_side", "is_block_trade")      # server_date_header is not used
SIX = ("ticker", "created_time", "price", "count", "taker_side", "is_block_trade")
BAR_COLS = ("ticker", "end_ts", "open", "high", "low", "close", "volume", "n_trades", "buy_volume", "sell_volume", "block_volume", "block_count")
NS = 10 ** 9


def parse_ns(s):
    """T1: ISO 8601 UTC (Z or +00:00) with 0 to 9 fraction digits -> exact integer nanoseconds since the epoch; anything else raises"""
    m = TIME_RE.match(s)
    if not m: raise ValueError("bad created_time %r" % s)
    y, mo, d, h, mi, se = (int(m.group(i)) for i in range(1, 7)); frac = (m.group(7) or "").ljust(9, "0")
    return calendar.timegm((y, mo, d, h, mi, se, 0, 0, 0)) * NS + int(frac)


def end_ts_of(t_ns): return (t_ns // (60 * NS) + 1) * 60                                   # T2: strictly after


def parse_price(s):
    try: v = Decimal(s)
    except InvalidOperation: raise ValueError("bad price %r" % s)
    if not v.is_finite() or v <= 0: raise ValueError("bad price %r" % s)
    return v


def parse_count(s):
    if not re.match(r"^\d+$", s): raise ValueError("bad count %r" % s)                  # T8: negative or non-integer raises
    return int(s)


def parse_block(s):
    v = s.strip().lower()
    if v == "true": return True
    if v == "false": return False
    raise ValueError("bad is_block_trade %r" % s)


def build(rows, wall):
    """Amendment sections 7 and 8. rows: dicts in FILE ORDER (sorted path order, then the row order of each file) with file, t_recv_ms, ticker, created_time, price, count, taker_side, is_block_trade (strings as stored).
    The wall first (other tickers are counted, never parsed). The same six fields with DIFFERENT t_recv_ms are one trade seen on two pages: only the rows with the EARLIEST t_recv_ms are kept (merged_by_repeat counts the dropped rows); the same six fields with the SAME t_recv_ms are real repeated prints, all kept (kept_same_recv counts the kept rows beyond the first).
    Inside a bar: exact created_time ascending, ties by REVERSE file order (the last row of the file first). -> (bars, summary {(file, ticker): Counter}, ticks {(file, ticker): Decimal})"""
    summ = collections.defaultdict(collections.Counter); groups = {}; order = []
    for i, r in enumerate(rows):
        tk = r["ticker"]; fk = (r["file"], tk)
        if tk not in wall: summ[(r["file"], "_outside_wall")]["rows"] += 1; continue
        summ[fk]["rows_read"] += 1; recv = int(r["t_recv_ms"]); key = tuple(r[c] for c in SIX)
        g = groups.setdefault(key, []); g.append((recv, i, r))
    kept = []
    for key, g in groups.items():
        m = min(x[0] for x in g); keep = [x for x in g if x[0] == m]; fk = (g[0][2]["file"], g[0][2]["ticker"])
        summ[fk]["merged_by_repeat"] += len(g) - len(keep)
        if len(keep) > 1: summ[fk]["kept_same_recv"] += len(keep) - 1
        kept.extend(keep)
    bars = {}
    for recv, i, r in kept:
        fk = (r["file"], r["ticker"]); summ[fk]["rows_kept"] += 1
        t_ns = parse_ns(r["created_time"]); price = parse_price(r["price"]); count = parse_count(r["count"]); block = parse_block(r["is_block_trade"]); side = r["taker_side"]
        b = bars.setdefault((r["ticker"], end_ts_of(t_ns)), {"trades": [], "block_volume": 0, "block_count": 0, "files": set()}); b["files"].add(r["file"])
        if block: b["block_volume"] += count; b["block_count"] += 1; summ[fk]["block_rows"] += 1
        else:
            b["trades"].append((t_ns, -i, price, count, side, r["file"]))
            if side not in ("buy", "sell"): summ[fk]["unknown_side_trades"] += 1
    out = {}; prices = collections.defaultdict(set)
    for (tk, e), b in sorted(bars.items()):
        fl = sorted(b["files"])[0]; s = summ[(fl, tk)]
        if not b["trades"]:
            s["bars_only_block"] += 1; s["block_volume_in_those"] += b["block_volume"]; continue
        tr = sorted(b["trades"], key=lambda x: (x[0], x[1])); ps = [x[2] for x in tr]
        for x in tr: prices[(x[5], tk)].add(x[2])
        out[(tk, e)] = {"ticker": tk, "end_ts": e, "open": ps[0], "high": max(ps), "low": min(ps), "close": ps[-1], "volume": sum(x[3] for x in tr), "n_trades": len(tr),
                        "buy_volume": sum(x[3] for x in tr if x[4] == "buy"), "sell_volume": sum(x[3] for x in tr if x[4] == "sell"), "block_volume": b["block_volume"], "block_count": b["block_count"]}
        s["bars_written"] += 1
    ticks = {}
    for fk, ps in prices.items():
        v = sorted(ps); d = [y - x for x, y in zip(v, v[1:])]; ticks[fk] = min(d) if d else None
    return out, summ, ticks


def f17(x): return "%.17g" % float(x)


def bar_line(b): return ",".join([b["ticker"], str(b["end_ts"]), f17(b["open"]), f17(b["high"]), f17(b["low"]), f17(b["close"]), str(b["volume"]), str(b["n_trades"]), str(b["buy_volume"]), str(b["sell_volume"]), str(b["block_volume"]), str(b["block_count"])])


def bar_text(bars): return ",".join(BAR_COLS) + "\n" + "".join(bar_line(bars[k]) + "\n" for k in sorted(bars))             # header line first


def summary_lines(summ, ticks):
    """one line per (file, ticker) sorted: file,ticker,rows_read,rows_kept,merged_by_repeat,kept_same_recv,block_rows,unknown_side_trades,bars_written,bars_only_block,block_volume_in_those,tick"""
    L = []
    for fk in sorted(k for k in summ if k[1] != "_outside_wall"):
        s = summ[fk]; tick = ticks.get(fk)
        L.append(",".join([fk[0], fk[1]] + [str(s[k]) for k in ("rows_read", "rows_kept", "merged_by_repeat", "kept_same_recv", "block_rows", "unknown_side_trades", "bars_written", "bars_only_block", "block_volume_in_those")] + ["null" if tick is None else f17(tick)]))
    return ["file,ticker,rows_read,rows_kept,merged_by_repeat,kept_same_recv,block_rows,unknown_side_trades,bars_written,bars_only_block,block_volume_in_those,tick"] + L


def sha(text): return hashlib.sha256(text.encode()).hexdigest()


def read_file(path, wall):
    """one date file (gzip CSV with a header; columns by name; extra columns ignored; a missing required column raises). The ticker column is checked FIRST: a row of another ticker keeps only its ticker."""
    rows = []; name = os.path.basename(path)
    with gzip.open(path, "rt", newline="") as fh:
        r = csv.reader(fh); h = next(r, None)
        if h is None: raise ValueError("empty file %s" % path)
        idx = {n: i for i, n in enumerate(h)}
        for c in COLS:
            if c not in idx: raise ValueError("%s lacks column %s" % (path, c))
        ti = idx["ticker"]
        for row in r:
            if row[ti] not in wall: rows.append({"file": name, "ticker": row[ti]}); continue
            d = {c: row[idx[c]] for c in COLS}; d["file"] = name; rows.append(d)
    return rows


def build_from_files(root, wall, allow_file, mark="readable ONLY by the Testing Desk's tape bar builder"):
    """REFUSES unless the allow-list file has a line with the mark naming this file's sha256; reads <root>/tape/YYYY-MM-DD.csv.gz in sorted path order"""
    text = open(allow_file, encoding="utf-8").read(); me = sha(open(os.path.abspath(__file__)).read())
    line = [l for l in text.splitlines() if mark in l]
    if not line or "tape_bars_second.py" not in line[0] or me not in line[0]: raise SystemExit("REFUSED: no allow-list line naming tape_bars_second.py with sha256 %s" % me)
    paths = sorted(p for p in glob.glob(os.path.join(root, "tape", "*.csv.gz")) if re.match(r"^\d{4}-\d\d-\d\d\.csv\.gz$", os.path.basename(p)))
    man = sorted((os.path.relpath(p, root), hashlib.sha256(open(p, "rb").read()).hexdigest()) for p in paths); rows = []
    for p in paths: rows.extend(read_file(p, set(wall)))
    bars, summ, ticks = build(rows, set(wall)); return bars, summ, ticks, man
