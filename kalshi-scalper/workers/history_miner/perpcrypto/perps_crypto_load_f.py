"""perps_crypto_load_f.py: FORWARD-window copy of perps_crypto_load.py 2dc46483 (FUNDX2-F, 2026-11-17); ONLY the windows and the file name differ. Original: wall functions of the PERPCRYPTO1 loader (History Miner, Nov 16, 2026). Card PERPCRYPTO1_CARD_NOV16.md (Amendments 1 and 2).
Every source has its own wall; the time column is read FIRST, then the ticker or product wall, then only the columns named. File-level loading refuses unless HELDOUT_PULL_RUNS.md names this file's sha256 (no flag, no env var).
No function here opens a file by itself: the readers pass rows in (tests use invented rows)."""
import calendar, collections, hashlib, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
T = lambda *a: calendar.timegm(a + (0,) * (6 - len(a)))
SNAP_START, DEV_END = T(2026, 11, 17), T(2026, 12, 15)        # hourly snapshots: development window; Nov 17 on is the forward window, read per the signed spec
BTC_START = T(2026, 11, 17)                                      # PERPBTC1M and Coinbase BTC hourly history start
TICKERS = ("KXBTCPERP", "KXETHPERP", "KXSOLPERP", "KXXRPPERP", "KXDOGEPERP", "KXHYPEPERP")
SNAP_COLS = ("ts_utc", "ticker", "bid", "ask", "price", "reference_price", "funding_cap")
PRODUCTS = {"BTC-USD": "KXBTCPERP", "ETH-USD": "KXETHPERP", "SOL-USD": "KXSOLPERP", "XRP-USD": "KXXRPPERP", "DOGE-USD": "KXDOGEPERP"}
ALLOW_FILE = os.path.join(HERE, "..", "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the History Miner's perps crypto loader"


def self_sha():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


def refuse_unless_allowed():
    try:
        text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "perps_crypto_load_f.py" in line and self_sha() in line:
            return
    raise SystemExit("REFUSED: no allow line names perps_crypto_load_f.py with this file's sha256 %s" % self_sha())


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v == v else None


def iso(s):
    try:
        return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return None


def snapshot_rows(rows, cnt):
    """perp-data perps/ hourly rows (dict-like): ts_utc FIRST, the window, then the ticker wall, then ONLY the columns in SNAP_COLS (any other raises in the test's poisoned rows).
    -> {ticker: [(ts, bid, ask, price, reference_price, funding_cap)]}; a row with a missing reference or price is KEPT here (the plugin skips it and counts it)."""
    out = collections.defaultdict(list)
    for r in rows:
        t = iso(r["ts_utc"]) if isinstance(r["ts_utc"], str) else None
        if t is None or not SNAP_START <= t < DEV_END:
            cnt["snapshot row outside the window (dropped)"] += 1; continue
        tk = r["ticker"]
        if tk not in TICKERS:
            cnt["snapshot ticker outside the wall (dropped)"] += 1; continue
        out[tk].append((t, num(r["bid"]), num(r["ask"]), num(r["price"]), num(r["reference_price"]), num(r["funding_cap"])))
    return {k: sorted(v) for k, v in out.items()}


def btc_candle_rows(candles, cnt, top_of_hour_only=True):
    """PERPBTC1M candlesticks (dicts): end_period_ts FIRST, the window, then only bid.close and ask.close. KXBTCPERP only (the run is one ticker). -> [(ts, bid, ask, None, None, None)] at the top of each hour."""
    out = []
    for c in candles:
        t = c["end_period_ts"]
        if not isinstance(t, int) or not BTC_START <= t < DEV_END:
            cnt["btc candle outside the window (dropped)"] += 1; continue
        if top_of_hour_only and t % 3600:
            cnt["btc candle not at the top of an hour (not used)"] += 1; continue
        out.append((t, num(c["bid"]["close"]), num(c["ask"]["close"]), None, None, None))
    return sorted(out)


def spot_rows(arrays, product, cnt):
    """Coinbase candles [start, low, high, open, close, volume]: product wall first, then the START time (index 0), the window, then ONLY the close (index 4). -> {start: close}"""
    if product not in PRODUCTS:
        cnt["spot product outside the wall (dropped)"] += 1; return {}
    out = {}
    for a in arrays:
        s = a[0]
        if not isinstance(s, int) or not BTC_START <= s < DEV_END:
            cnt["spot candle outside the window (dropped)"] += 1; continue
        out[s] = num(a[4])
    return out


def spot_at(spot, t):
    """The spot value for a perp row at time t: the close of the last COMPLETED hourly candle (start s with s + 3600 <= t), i.e. start = floor(t / 3600) * 3600 - 3600 for t on the hour. Never a candle that closes after t."""
    s = (t // 3600) * 3600 - 3600
    return spot.get(s)


def funding_rows(rows, cnt):
    """funding history rows (dict-like). A BLANK ticker REFUSES the whole file (a ticker is never inferred from the mark price); then the time wall; then the rate."""
    out = collections.defaultdict(list)
    for r in rows:
        tk = r["ticker"]
        if not tk:
            raise SystemExit("REFUSED: a funding row has a blank ticker (not labelled): the pull must be labelled, a ticker is never inferred from mark_price")
        if tk not in TICKERS:
            cnt["funding ticker outside the wall (dropped)"] += 1; continue
        t = iso(r["funding_time"]) if isinstance(r["funding_time"], str) else None
        if t is None or not BTC_START <= t < DEV_END:
            cnt["funding print outside the window (dropped)"] += 1; continue
        out[tk].append((t, num(r["funding_rate"])))
    return {k: sorted(v) for k, v in out.items()}
