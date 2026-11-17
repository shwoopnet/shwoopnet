#!/usr/bin/env python3
"""60-day tape, 1 minute bar builder, BUILD 2 (Testing Desk, Nov 17, 2026), blind from Desk A's PERPS_TAPE60_AMENDMENT_NOV17.md at be97878d7 (sha256 fe3d8144a845303571cad5cb53dc82fdfd681a06dcea029b20c684d6914f7e71): sections 2 and 6 (bars, readings T1 to T18) as changed by sections 7 and 8 (one file per UTC date holding all tickers, no trade_id, dedupe by the six fields and the earliest t_recv_ms, ties by reverse file order). Pure functions on rows; the file reader below checks an allow line.
Rows: dicts with file, t_recv_ms, ticker, created_time, price, count, taker_side, is_block_trade (strings as stored)."""
import calendar, collections, csv, fnmatch, glob, gzip, hashlib, json, os, re, sys, time
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


def time_date(t_ns): return time.strftime("%Y-%m-%d", time.gmtime(t_ns // NS))


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


def build(rows, wall, held=None):
    """Amendment sections 7 and 8. rows: dicts in FILE ORDER (sorted path order, then the row order of each file) with file, t_recv_ms, ticker, created_time, price, count, taker_side, is_block_trade (strings as stored).
    The wall first (other tickers are counted, never parsed). The same six fields with DIFFERENT t_recv_ms are one trade seen on two pages: only the rows with the EARLIEST t_recv_ms are kept (merged_by_repeat counts the dropped rows); the same six fields with the SAME t_recv_ms are real repeated prints, all kept (kept_same_recv counts the kept rows beyond the first).
    Inside a bar: exact created_time ascending, ties by REVERSE file order (the last row of the file first). -> (bars, summary {(file, ticker): Counter}, ticks {(file, ticker): Decimal})"""
    summ = collections.defaultdict(collections.Counter); groups = {}; order = []
    for i, r in enumerate(rows):
        tk = r["ticker"]; fk = (r["file"], tk)
        if tk not in wall: summ[(r["file"], "_outside_wall")]["rows"] += 1; continue
        summ[fk]["rows_read"] += 1; t_ns = parse_ns(r["created_time"])
        if time_date(t_ns) != r["file"][:10]: summ[fk]["rows_other_date"] += 1; continue          # Amendment 4 (3): the trade belongs to the file of its own date
        if held is not None and held(tk, t_ns // NS): summ[fk]["rows_held"] += 1; continue          # Amendment 4 (2): holds and the default deny
        recv = int(r["t_recv_ms"]); key = tuple(r[c] for c in SIX)
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
        if len(b["files"]) > 1: raise RuntimeError("a bar in two date files: %s %s" % (r["ticker"], end_ts_of(t_ns)))
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
    """one line per (file, ticker) sorted: file,ticker,rows_read,rows_kept,merged_by_repeat,kept_same_recv,block_rows,unknown_side_trades,bars_written,bars_only_block,block_volume_in_those,tick,rows_other_date,rows_held"""
    L = []
    for fk in sorted(k for k in summ if k[1] != "_outside_wall"):
        s = summ[fk]; tick = ticks.get(fk)
        L.append(",".join([fk[0], fk[1]] + [str(s[k]) for k in ("rows_read", "rows_kept", "merged_by_repeat", "kept_same_recv", "block_rows", "unknown_side_trades", "bars_written", "bars_only_block", "block_volume_in_those")] + ["" if tick is None else f17(tick)] + [str(s["rows_other_date"]), str(s["rows_held"])]))
    return ["file,ticker,rows_read,rows_kept,merged_by_repeat,kept_same_recv,block_rows,unknown_side_trades,bars_written,bars_only_block,block_volume_in_those,tick,rows_other_date,rows_held"] + L


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


DEV = ("2026-09-18", "2026-10-27"); HELD = ("2026-10-28", "2026-11-15"); CUT_DATE = "2026-11-16"; DENY_FROM = 1794787200


def load_holds(path, pinned_sha256):
    """the pinned HOLDS.json (sha256 checked): a function held(ticker, t_seconds). A cell is held if its time is at or after forward_default_deny_from, or in [from, to) of a row with status OPEN or FROZEN whose ticker pattern matches (fnmatch; '*' matches anything; 'to' null is open ended); rows with any scope key, or kind clearance, do not apply to perps tape rows (Desk A, Nov 17)."""
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != pinned_sha256: raise SystemExit("REFUSED: the holds file does not match the pinned sha256")
    d = json.loads(raw); deny = d["forward_default_deny_from"]; rows = [r for r in d["rows"] if r["status"] in ("OPEN", "FROZEN") and "scope" not in r and r.get("kind") != "clearance"]
    def held(ticker, t):
        if t >= deny: return True
        return any(r["from"] <= t and (r["to"] is None or t < r["to"]) and any(fnmatch.fnmatchcase(ticker, p) for p in r["tickers"]) for r in rows)
    return held


def check_range(date_from, date_to):
    for d in (date_from, date_to):
        if not re.match(r"^\d{4}-\d\d-\d\d$", d): raise SystemExit("REFUSED: bad date %r" % d)
    if date_from > date_to: raise SystemExit("REFUSED: from is after to")
    if date_to >= CUT_DATE: raise SystemExit("REFUSED: a range reaching 2026-11-16 or later")
    for lo, hi in (DEV, HELD):
        if lo <= date_from and date_to <= hi: return
    raise SystemExit("REFUSED: the range is not wholly inside development (%s to %s) or held-out (%s to %s)" % (DEV + HELD))


def build_from_files(root, wall, allow_file, date_from, date_to, holds_path=None, holds_sha=None, mark="readable ONLY by the Testing Desk's tape bar builder"):
    """REFUSES unless the allow-list file has a line with the mark naming this file's sha256 and the range is legal; lists, hashes and opens ONLY the <root>/tape/YYYY-MM-DD.csv.gz files inside [date_from, date_to], in sorted path order"""
    text = open(allow_file, encoding="utf-8").read(); me = sha(open(os.path.abspath(__file__)).read())
    line = [l for l in text.splitlines() if mark in l]
    if not line or "tape_bars_second.py" not in line[0] or me not in line[0]: raise SystemExit("REFUSED: no allow-list line naming tape_bars_second.py with sha256 %s" % me)
    check_range(date_from, date_to)
    held = load_holds(holds_path, holds_sha) if holds_path else None
    paths = sorted(p for p in glob.glob(os.path.join(root, "tape", "*.csv.gz")) if re.match(r"^\d{4}-\d\d-\d\d\.csv\.gz$", os.path.basename(p)) and date_from <= os.path.basename(p)[:10] <= date_to)
    man = sorted((os.path.relpath(p, root), hashlib.sha256(open(p, "rb").read()).hexdigest()) for p in paths); rows = []
    for p in paths: rows.extend(read_file(p, set(wall)))
    bars, summ, ticks = build(rows, set(wall), held); return bars, summ, ticks, man
