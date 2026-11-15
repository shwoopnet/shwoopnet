"""SEARCH1 chosen-combination haircut recompute reader (Desk A, Nov 15 2026), built to SEARCH1_HAND_CASE_NOV15.md (expected figures committed first at 64003ee47). Offline; reads one SQLite extract and sends nothing.
  SEARCH1_READ=1 python3 -I search1_haircut.py <SEARCH1_extract.sqlite> --cut=<unix ts of the original confirmation start>   DEFAULT-CLOSED. Prints raw, +1c, +2c for all days, for days before --cut (discovery: where the combination was chosen, information only) and for days from --cut (the surviving confirmation days).
Label: "upper bound, not fill-checked; fee mode per-order rounded"."""
import sys, os, math, sqlite3, collections, json
SIZE = 10; HAIRCUTS = (0.0, 0.01, 0.02); LEFT = 420; BAND = (0.97, 0.995); SL = 0.50; END_BEFORE = 30; MAXSPREAD = 0.10
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
def bid_of(c, side): return c[1] if side == "yes" else round(1 - c[2], 4)       # c = (end_ts, bid, ask)
def decide(candles, close_ts):
    """candles: end_ts -> (bid, ask) of one market (candles ending after the close dropped). Returns ('skip', why) or ('trade', side, entry, exit_bid_or_None)."""
    cs = sorted((t, v[0], v[1]) for t, v in candles.items() if t <= close_ts)
    if any(b is None or a is None for _, b, a in cs): return ("skip", "incomplete_market")
    x = next((c for c in cs if c[0] == close_ts - LEFT), None)
    if x is None: return ("skip", "no_candle")
    fv = favorite(x[1], x[2])
    if fv is None: return ("skip", "band_or_quote")
    side, price = fv
    ex = None
    for c in cs:
        if close_ts - LEFT < c[0] <= close_ts - END_BEFORE and bid_of(c, side) <= SL: ex = bid_of(c, side); break
    return ("trade", side, price, ex)
def cash(side, result, entry, ex, h):
    p = min(0.99, entry + h)
    if ex is None: return SIZE * ((1 if result == side else 0) - p) - fee_up_order(p)
    q = max(0.01, ex - h)
    return SIZE * (q - p) - fee_up_order(p) - fee_up_order(q)
def summarize(trades):
    out = {"n": len(trades), "exits": sum(t[4] is not None for t in trades)}
    for h in HAIRCUTS:
        xs = [cash(s, r, e, x, h) for _, s, e, r, x in trades]; half = len(xs) // 2
        out["h%.2f" % h] = {"net": round(sum(xs), 6), "pf": pf(xs), "wins": sum(v > 0 for v in xs), "losses": sum(v < 0 for v in xs), "half1": {"n": half, "pf": pf(xs[:half]), "net": round(sum(xs[:half]), 6)}, "half2": {"n": len(xs) - half, "pf": pf(xs[half:]), "net": round(sum(xs[half:]), 6)}}
    return out
def run(db, cut=None):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    mk = c.execute("select ticker, close_ts, result from market where series in ('KXBTC15M','KXETH15M') order by close_ts").fetchall()
    cand = collections.defaultdict(dict)
    for tk, e, b, a in c.execute("select ticker,end_ts,bid_c,ask_c from candle"): cand[tk][int(e)] = (b, a)
    trades, cnt = [], collections.Counter()
    for tk, cl, res in mk:
        if res not in ("yes", "no"): cnt["no_result"] += 1; continue
        d = decide(cand.get(tk, {}), int(cl))
        if d[0] == "trade": trades.append((int(cl), d[1], d[2], res, d[3])); cnt["trade"] += 1
        else: cnt[d[1]] += 1
    trades.sort()
    out = {"label": "upper bound, not fill-checked; fee mode per-order rounded; cut-window recompute, not a reproduction of confirmation n 361 PF 1.31; 2c primary (exit can fall in the last 2 minutes)", "counts": dict(cnt), "all_days": summarize(trades)}
    if cut is not None:
        out["before_cut_days_(discovery, where the combination was chosen: information only)"] = summarize([t for t in trades if t[0] < cut])
        out["from_cut_days_(surviving confirmation days)"] = summarize([t for t in trades if t[0] >= cut])
    return out
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: sys.exit(__doc__)
    if os.environ.get("SEARCH1_READ") != "1": sys.exit("REFUSED: SEARCH1_READ=1 is not set (reading starts only when the Head or Auditor B clears it)")
    cut = next((float(x.split("=", 1)[1]) for x in sys.argv[1:] if x.startswith("--cut=")), None)
    print(json.dumps(run(a[0], cut), indent=1, default=str))
