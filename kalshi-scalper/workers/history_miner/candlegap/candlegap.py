#!/usr/bin/env python3
"""CANDLEGAP (History Miner, Nov 13, 2026): what a missing one-minute candle means on KXCS2GAME. Zero-try measurement; design in CANDLEGAP_DESIGN.md, fixed before the candles were pulled.
Reads the wheel book recorder's run folder and the CANDLEGAP_CS2 pull folder. Prints counts only: no result is read (the list answers are used for close_time only), no price is analysed."""
import calendar, csv, glob, gzip, json, os, re, sys
from datetime import datetime, timezone

SERIES = "KXCS2GAME"
TOL = 0.0101   # within 1c


def eastern_offset(y, mo, d, h, mi):
    """UTC offset in seconds of US Eastern local time (daylight saving from the second Sunday of March 02:00 to the first Sunday of November 02:00)."""
    def nth_sunday(y, mo, n):
        first = calendar.weekday(y, mo, 1)
        return 1 + (6 - first) % 7 + 7 * (n - 1)
    a = (mo, d, h) >= (3, nth_sunday(y, 3, 2), 2)
    b = (mo, d, h) < (11, nth_sunday(y, 11, 1), 2)
    return -4 * 3600 if (a and b) else -5 * 3600


MON = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}


def start_of(ticker):
    m = re.match(r"^[A-Z0-9]+-(\d\d)([A-Z]{3})(\d\d)(\d\d)(\d\d)", ticker)
    if not m:
        return None
    y, mo, d, h, mi = 2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3)), int(m.group(4)), int(m.group(5))
    return calendar.timegm((y, mo, d, h, mi, 0)) - eastern_offset(y, mo, d, h, mi)


def iso(s):
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load(run, pull):
    rd = lambda f: list(csv.DictReader(gzip.open(os.path.join(run, f), "rt")))
    cov = [r for r in rd("coverage.csv.gz") if r["series"] == SERIES]
    tickers = sorted(r["ticker"] for r in cov)
    first_seen = {r["ticker"]: int(r["first_seen_ms"]) / 1000.0 for r in cov}
    rows = {t: [] for t in tickers}
    for f in ("book_fast.csv.gz", "book_slow.csv.gz"):
        for r in rd(f):
            if r["ticker"] in rows:
                rows[r["ticker"]].append(r)
    for t in rows:
        rows[t].sort(key=lambda r: int(r["t_recv_ms"]))
    polls = rd("polls.csv.gz")
    fast_polls = sorted(int(p["t_recv_ms"]) / 1000.0 for p in polls if p["tier"] == "fast")
    run_end = max(int(p["t_recv_ms"]) for p in polls) / 1000.0
    # the market's own close: close_time in the recorder's settled or closed list reads (a time; the result field is not read)
    close = {}
    man = json.load(open(os.path.join(run, "answers", "manifest.json")))
    for f in man["files"]:
        if f.get("path") != "/markets":
            continue
        body = json.load(gzip.open(os.path.join(run, "answers", f["file"]), "rt"))
        for m in (body.get("markets") or []):
            if m.get("ticker") in rows and m.get("close_time"):
                c = iso(m["close_time"])
                close[m["ticker"]] = min(c, close.get(m["ticker"], c))
    # candles
    cand = {t: {} for t in tickers}
    for d in pull:
        pm = json.load(open(os.path.join(d, "manifest.json")))
        for r in pm.get("rows", []):
            if r.get("status") != 200 or not r.get("file"):
                continue
            body = json.load(gzip.open(os.path.join(d, r["file"]), "rt"))
            for m in body.get("markets") or []:
                t = m.get("market_ticker") or m.get("ticker")
                if t in cand:
                    for c in m.get("candlesticks") or []:
                        cand[t][int(c["end_period_ts"])] = c
    return tickers, first_seen, rows, fast_polls, run_end, close, cand


def top(r):
    yb = fnum(r["yes_bid_px_1"]) if r else None
    nb = fnum(r["no_bid_px_1"]) if r else None
    return yb, (None if nb is None else round(1 - nb, 4))


def measure(run, pull):
    tickers, first_seen, rows, fast_polls, run_end, close, cand = load(run, pull)
    keys = ["1_present_changed", "2_present_unchanged", "3_missing_unchanged_twosided", "4_missing_unchanged_empty_or_onesided", "5_missing_changed"]
    out = {split: {basis: dict.fromkeys(keys, 0) for basis in ("rows", "top")} for split in ("before_close", "after_close")}
    match = {split: {"present": 0, "with_bid_ask": 0, "bid_within_1c": 0, "ask_within_1c": 0, "both_within_1c": 0} for split in ("before_close", "after_close")}
    per_ticker_minutes = {}
    import bisect
    for t in tickers:
        s = start_of(t)
        rs = rows[t]
        if not rs or s is None:
            continue
        times = [int(r["t_recv_ms"]) / 1000.0 for r in rs]
        lo = max(s, first_seen[t], times[0])
        m0 = int(-(-lo // 60) * 60)
        n = 0
        for m in range(m0, int(run_end // 60 * 60) - 59, 60):
            if m + 60 > run_end:
                break
            # the minute must contain a fast poll
            i = bisect.bisect_left(fast_polls, m)
            if i >= len(fast_polls) or fast_polls[i] >= m + 60:
                continue
            j_prev = bisect.bisect_left(times, m) - 1          # last row before the minute
            j_end = bisect.bisect_left(times, m + 60) - 1       # last row before the minute's end
            if j_prev < 0:
                continue
            changed = j_end > j_prev
            top_changed = changed and top(rs[j_end]) != top(rs[j_prev])
            book = rs[j_end]
            yb, ya = top(book)
            two = yb is not None and ya is not None and yb < ya
            split = "after_close" if (t in close and m + 60 > close[t]) else "before_close"
            c = cand[t].get(m + 60)
            for basis, ch in (("rows", changed), ("top", top_changed)):
                if c is not None:
                    k = "1_present_changed" if ch else "2_present_unchanged"
                elif ch:
                    k = "5_missing_changed"
                else:
                    k = "3_missing_unchanged_twosided" if two else "4_missing_unchanged_empty_or_onesided"
                out[split][basis][k] += 1
            if c is not None:
                mt = match[split]; mt["present"] += 1
                cb = fnum(((c.get("yes_bid") or {}).get("close_dollars")))
                ca = fnum(((c.get("yes_ask") or {}).get("close_dollars")))
                if cb is not None and ca is not None and yb is not None and ya is not None:
                    mt["with_bid_ask"] += 1
                    okb, oka = abs(cb - yb) <= TOL, abs(ca - ya) <= TOL
                    mt["bid_within_1c"] += okb; mt["ask_within_1c"] += oka; mt["both_within_1c"] += okb and oka
            n += 1
        per_ticker_minutes[t] = n
    return {"tickers": len(tickers), "tickers_with_candles": sum(1 for t in tickers if cand[t]), "markets_closed_in_lists": len(close),
            "market_minutes": sum(per_ticker_minutes.values()), "counts": out, "candle_vs_book": match}


if __name__ == "__main__":
    run = sys.argv[1]; pull = sys.argv[2:]
    for p in [run] + pull:
        if "HELDOUT_" in os.path.realpath(p) or "HELDOUT_" in os.path.abspath(p):
            sys.exit("refused: HELDOUT_ path")
    print(json.dumps(measure(run, pull), indent=1))
