#!/usr/bin/env python3
"""60-day tape, 1 minute bar builder, BUILD 2 (Testing Desk, Nov 17, 2026), blind from Desk A's PERPS_TAPE60_AMENDMENT_NOV17.md at 207f46fa5 (sha256 d7e94090df1f4635c6fc25b84bc7629ff4e426dfb4497c47a8ae848c4048b37e), sections 1, 2 and 6 (settled readings T1 to T18). Pure functions on rows; the file reader below checks an allow line.
Rows: dicts with ticker, trade_id, created_time, price, count, taker_side, is_block_trade (strings as stored)."""
import calendar, collections, csv, glob, gzip, hashlib, os, re, sys
from decimal import Decimal, InvalidOperation

TIME_RE = re.compile(r"^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.(\d{1,9}))?(?:Z|\+00:00)$")
COLS = ("ticker", "trade_id", "created_time", "price", "count", "taker_side", "is_block_trade")
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
    """rows in file order (sorted path order over files); wall = set of tickers. -> (bars {(ticker, end_ts): dict}, summary {ticker: counts and tick})"""
    seen = {}; bars = {}; summ = {}
    for r in rows:
        tk = r["ticker"]
        if tk not in wall: summ.setdefault("_outside_wall", collections.Counter())["rows"] += 1; continue          # the wall: nothing else of the row is parsed
        s = summ.setdefault(tk, collections.Counter()); s["rows_read"] += 1
        key = (tk, r["trade_id"])
        if key in seen:
            s["duplicates_dropped"] += 1
            if tuple(r[c] for c in COLS) != seen[key]: s["duplicate_differs"] += 1
            continue
        seen[key] = tuple(r[c] for c in COLS); s["rows_kept"] += 1
        t_ns = parse_ns(r["created_time"]); price = parse_price(r["price"]); count = parse_count(r["count"]); block = parse_block(r["is_block_trade"]); side = r["taker_side"]
        b = bars.setdefault((tk, end_ts_of(t_ns)), {"trades": [], "block_volume": 0, "block_count": 0})
        if block: b["block_volume"] += count; b["block_count"] += 1; s["block_rows"] += 1
        else:
            b["trades"].append((t_ns, r["trade_id"], price, count, side))
            if side not in ("buy", "sell"): s["unknown_side_trades"] += 1
    out = {}; prices = collections.defaultdict(set)
    for (tk, e), b in sorted(bars.items()):
        s = summ[tk]
        if not b["trades"]:
            s["bars_only_block"] += 1; s["block_volume_in_those"] += b["block_volume"]; continue
        tr = sorted(b["trades"], key=lambda x: (x[0], x[1])); ps = [x[2] for x in tr]
        for x in tr: prices[tk].add(x[2])
        out[(tk, e)] = {"ticker": tk, "end_ts": e, "open": ps[0], "high": max(ps), "low": min(ps), "close": ps[-1], "volume": sum(x[3] for x in tr), "n_trades": len(tr),
                        "buy_volume": sum(x[3] for x in tr if x[4] == "buy"), "sell_volume": sum(x[3] for x in tr if x[4] == "sell"), "block_volume": b["block_volume"], "block_count": b["block_count"]}
        s["bars_written"] += 1
    ticks = {}
    for tk, ps in prices.items():
        v = sorted(ps); d = [b - a for a, b in zip(v, v[1:])]; ticks[tk] = min(d) if d else None
    return out, summ, ticks


def f17(x): return "%.17g" % float(x)


def bar_line(b): return ",".join([b["ticker"], str(b["end_ts"]), f17(b["open"]), f17(b["high"]), f17(b["low"]), f17(b["close"]), str(b["volume"]), str(b["n_trades"]), str(b["buy_volume"]), str(b["sell_volume"]), str(b["block_volume"]), str(b["block_count"])])


def bar_text(bars): return "".join(bar_line(bars[k]) + "\n" for k in sorted(bars))


def summary_lines(summ, ticks):
    """one line per ticker (sorted): ticker,rows_read,rows_kept,duplicates_dropped,duplicate_differs,block_rows,unknown_side_trades,bars_written,bars_only_block,block_volume_in_those,tick"""
    L = []
    for tk in sorted(k for k in summ if k != "_outside_wall"):
        s = summ[tk]; tick = ticks.get(tk); L.append(",".join([tk] + [str(s[k]) for k in ("rows_read", "rows_kept", "duplicates_dropped", "duplicate_differs", "block_rows", "unknown_side_trades", "bars_written", "bars_only_block", "block_volume_in_those")] + ["null" if tick is None else f17(tick)]))
    return L


def sha(text): return hashlib.sha256(text.encode()).hexdigest()


def read_file(path, wall):
    """one tape file (gzip CSV, header, columns by name; extra columns ignored; a missing required column raises) -> rows; the ticker column is checked first and rows of other tickers are returned as a bare ticker (never parsed)"""
    rows = []
    with gzip.open(path, "rt", newline="") as fh:
        r = csv.reader(fh); h = next(r, None)
        if h is None: raise ValueError("empty file %s" % path)
        idx = {n: i for i, n in enumerate(h)}
        for c in COLS:
            if c not in idx: raise ValueError("%s lacks column %s" % (path, c))
        ti = idx["ticker"]
        for row in r:
            if row[ti] not in wall: rows.append({"ticker": row[ti]}); continue
            rows.append({c: row[idx[c]] for c in COLS})
    return rows


def build_from_files(root, wall, allow_file, mark="readable ONLY by the Testing Desk's tape bar builder"):
    """REFUSES unless the allow-list file has a line with the mark naming this file's sha256; reads <root>/tape/<UTC date>/<ticker>.csv.gz for wall tickers only, in sorted path order"""
    text = open(allow_file, encoding="utf-8").read(); me = sha(open(os.path.abspath(__file__)).read())
    line = [l for l in text.splitlines() if mark in l]
    if not line or "tape_bars_second.py" not in line[0] or me not in line[0]: raise SystemExit("REFUSED: no allow-list line naming tape_bars_second.py with sha256 %s" % me)
    paths = sorted(p for t in wall for p in glob.glob(os.path.join(root, "tape", "*", t + ".csv.gz"))); man = sorted((os.path.relpath(p, root), hashlib.sha256(open(p, "rb").read()).hexdigest()) for p in paths)
    rows = []
    for p in sorted(paths, key=lambda p: (os.path.relpath(p, root))): rows.extend(read_file(p, set(wall)))
    bars, summ, ticks = build(rows, set(wall)); return bars, summ, ticks, man
