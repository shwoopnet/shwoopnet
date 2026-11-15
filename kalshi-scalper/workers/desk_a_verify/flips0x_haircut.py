"""FLIPS0-X haircut recompute reader (Desk A, Nov 15 2026), built to FLIPS0X_HAND_CASE_NOV15.md (expected figures committed first at 8d4b616d0). Offline; reads one SQLite extract (market, candle) and sends nothing.
  FLIPS0X_READ=1 python3 -I flips0x_haircut.py <FLIPS0X_extract.sqlite>     DEFAULT-CLOSED. Prints raw, +1c, +2c pooled and per series (per series is information only).
Rule: research branch flips0x.py / ideas100.py FLIPS_0 at the 6 minute entry (see the hand case). Label: "upper bound, not fill-checked; fee mode per-order rounded"."""
import sys, os, math, sqlite3, collections, json
SIZE = 10; HAIRCUTS = (0.0, 0.01, 0.02); LEFT = 360; BAND = (0.88, 0.97); MAXSPREAD = 0.10; MINMOVE = 0.004
SERIES = ("KXXRP15M", "KXDOGE15M", "KXGOLD15M", "KXBNB15M", "KXHYPE15M", "KXNEAR15M", "KXZEC15M", "KXSILVER15M", "KXPLATINUM15M", "KXPALLADIUM15M", "KXCOPPER15M", "KXWTI15M", "KXNATGAS15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M")
def fee_up_order(p, contracts=SIZE): return math.ceil(0.07 * contracts * p * (1 - p) * 100 - 1e-9) / 100
def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 and w > 0 else (w / l if l else float("nan"))
def valid_quote(b, a): return b is not None and a is not None and b >= 0.001 and a <= 0.999 and a >= b and a - b <= MAXSPREAD + 1e-12
def favorite(b, a):
    if not valid_quote(b, a): return None
    lo, hi = BAND
    if lo <= a <= hi: return ("yes", a)
    no = round(1 - b, 4)
    if lo <= no <= hi: return ("no", no)
    return None
def side_mid(c, side): return (c[1] + c[2]) / 2 if side == "yes" else 1 - (c[1] + c[2]) / 2       # c = (end, bid, ask)
def flips(path):
    ch = [b - a for a, b in zip(path, path[1:])]; mv = [x for x in ch if abs(x) > MINMOVE]
    return sum(1 for a, b in zip(mv, mv[1:]) if (a > 0) != (b > 0))
def decide(candles, close_ts):
    """candles: end_ts -> (bid, ask); candles with a missing side and candles after the close are dropped first. Returns ('skip', why) or ('trade', side, price)."""
    cs = sorted((t, v[0], v[1]) for t, v in candles.items() if t <= close_ts and v[0] is not None and v[1] is not None)
    i = next((k for k, c in enumerate(cs) if c[0] == close_ts - LEFT), None)
    if i is None: return ("skip", "no_candle")
    c, e = cs[i], cs[:i]
    fv = favorite(c[1], c[2])
    if fv is None: return ("skip", "band_or_quote")
    side, price = fv
    if len(e) < 4: return ("skip", "fewer_than_4_earlier")
    if flips([side_mid(x, side) for x in e] + [side_mid(c, side)]) != 0: return ("skip", "flips")
    return ("trade", side, price)
def cash(side, result, p0, h):
    p = min(0.99, p0 + h); win = 1 if result == side else 0
    return SIZE * (win - p) - fee_up_order(p)
def summarize(trades):
    out = {"n": len(trades)}
    for h in HAIRCUTS:
        xs = [cash(s, r, p, h) for _, s, p, r, _ in trades]; half = len(xs) // 2
        out["h%.2f" % h] = {"net": round(sum(xs), 6), "pf": pf(xs), "wins": sum(v > 0 for v in xs), "losses": sum(v < 0 for v in xs), "half1": {"n": half, "pf": pf(xs[:half]), "net": round(sum(xs[:half]), 6)}, "half2": {"n": len(xs) - half, "pf": pf(xs[half:]), "net": round(sum(xs[half:]), 6)}}
    return out
def run(db):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    mk = c.execute("select ticker, series, close_ts, result from market order by close_ts").fetchall()
    cand = collections.defaultdict(dict)
    for tk, e, b, a in c.execute("select ticker,end_ts,bid_c,ask_c from candle"): cand[tk][int(e)] = (b, a)
    trades, cnt = [], collections.Counter()
    for tk, ser, cl, res in mk:
        if ser not in SERIES: continue
        if res not in ("yes", "no"): cnt["no_result"] += 1; continue
        d = decide(cand.get(tk, {}), int(cl))
        if d[0] == "trade": trades.append((int(cl), d[1], d[2], res, ser)); cnt["trade"] += 1
        else: cnt[d[1]] += 1
    trades.sort()
    out = {"label": "upper bound, not fill-checked; fee mode per-order rounded; cut-window recompute, NOT a reproduction of n 536; unadjusted cash (the printed raw PF 1.77), not the series-adjusted mean; 1c primary (entry 360 s before the close)", "counts": dict(cnt), "pooled": summarize(trades), "per_series_information_only": {}}
    for s in SERIES:
        ts = [t for t in trades if t[4] == s]
        if ts: out["per_series_information_only"][s] = summarize(ts)
    return out
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: sys.exit(__doc__)
    if os.environ.get("FLIPS0X_READ") != "1": sys.exit("REFUSED: FLIPS0X_READ=1 is not set (reading starts only when the Head or Auditor B clears it)")
    print(json.dumps(run(a[0]), indent=1, default=str))
