"""OIREL haircut recompute reader (Desk A, Nov 15 2026), built to OIREL_HAND_CASE_NOV15.md (expected figures committed first at ec5de230a). Offline; reads one SQLite extract (market, candle tables of Forensics' OIREL extract) and sends nothing.
  OIREL_READ=1 python3 -I oirel_haircut.py <extract.sqlite> [--split=<unix ts for the discovery/validation pair>]     DEFAULT-CLOSED: refuses without OIREL_READ=1 (the Head's or Auditor B's clearance). Prints raw, +1c and +2c.
Rule: research branch src/scalper/oirel.py decide(): see the hand case. Drops every candle ending after its market's close. Label of every line: "upper bound, not fill-checked; fee mode per-order rounded"."""
import sys, os, math, sqlite3, collections
RTHR = 0.26764675317954373; LOOK, BACK, FILL = 180, 360, 120; LO, HI = 0.05, 0.50; SIZE = 10; EPS = 1e-9
HAIRCUTS = (0.0, 0.01, 0.02)
def fee_up_order(p, contracts=SIZE): return math.ceil(0.07 * contracts * p * (1 - p) * 100 - 1e-9) / 100
def _num(x):
    try: v = float(x)
    except (TypeError, ValueError): return None
    return v if v == v else None
def side_ask(bid, ask, side): return ask if side == "yes" else round(1 - bid, 6)
def decide(candles, close_ts):
    """candles: end_ts -> (bid_c, ask_c, volume, oi) of ONE market. Returns ('trade', side, fill_ask, fill_ts) | ('nofire',) | ('noside',) | ('nodata', why)."""
    cs = {t: v for t, v in candles.items() if t <= close_ts}                 # standing reader rule: drop candles ending after the close
    s, p, f = cs.get(close_ts - LOOK), cs.get(close_ts - BACK), cs.get(close_ts - FILL)
    if s is None or p is None: return ("nodata", "candle_missing")
    so, po = _num(s[3]), _num(p[3])
    if not so or not po or po <= 0: return ("nodata", "open_interest_missing_or_0")
    if not (so - po) / po > RTHR: return ("nofire",)
    sb, sa = _num(s[0]), _num(s[1])
    if sb is None or sa is None or not (0 < sb < sa < 1): return ("nodata", "signal_not_two_sided")
    side = next((sd for sd in ("yes", "no") if LO - EPS <= side_ask(sb, sa, sd) <= HI + EPS), None)
    if side is None: return ("noside",)
    if f is None: return ("nodata", "candle_missing")
    fb, fa = _num(f[0]), _num(f[1])
    if fb is None or fa is None or not (0 < fb < fa < 1): return ("nodata", "fill_not_two_sided")
    ask = side_ask(fb, fa, side)
    if not 0 < ask < 1: return ("nodata", "fill_ask_out_of_range")
    return ("trade", side, ask, close_ts - FILL)
def cash(side, result, ask, h):
    p = min(0.99, ask + h); win = 1 if result == side else 0
    return SIZE * (win - p) - fee_up_order(p), p, win
def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 and w > 0 else (w / l if l else float("nan"))
def run(db, split=None):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    mk = c.execute("select ticker, close_ts, result from market where series='KXBTC15M' order by close_ts").fetchall()
    cand = collections.defaultdict(dict)
    for tk, e, b, a, v, oi in c.execute("select ticker,end_ts,bid_c,ask_c,volume,oi from candle"): cand[tk][int(e)] = (b, a, v, oi)
    trades, cnt, why = [], collections.Counter(), collections.Counter()
    for tk, close_ts, result in mk:
        if result not in ("yes", "no"): cnt["no result"] += 1; continue
        d = decide(cand.get(tk, {}), int(close_ts)); cnt[d[0]] += 1
        if d[0] == "nodata": why[d[1]] += 1
        if d[0] == "trade": trades.append((d[3], int(close_ts), d[1], d[2], result))
    trades.sort()
    out = {"counts": dict(cnt), "nodata_reasons": {k: v for k, v in why.items() if v}, "note": "this reader counts a one-sided or crossed signal or fill quote, and a fill ask outside (0,1), as NoData; oirel.py does not, so n can differ from the printed n for that reason (counted apart from candle_missing), as well as for the cut and the per-order fee", "excluded_tickers_dropped": "0 of the 28 (none present; extract checked by Auditor B)", "n": len(trades), "label": "upper bound, not fill-checked; fee mode per-order rounded"}
    for h in HAIRCUTS:
        xs = [cash(s, r, a, h)[0] for _, _, s, a, r in trades]; half = len(xs) // 2
        row = {"net": round(sum(xs), 6), "pf": pf(xs), "wins": sum(x > 0 for x in xs), "losses": sum(x < 0 for x in xs), "half1": {"n": half, "pf": pf(xs[:half]), "net": round(sum(xs[:half]), 6)}, "half2": {"n": len(xs) - half, "pf": pf(xs[half:]), "net": round(sum(xs[half:]), 6)}}
        if split is not None:
            a1 = [cash(s, r, a, h)[0] for _, cl, s, a, r in trades if cl < split]; a2 = [cash(s, r, a, h)[0] for _, cl, s, a, r in trades if cl >= split]
            row["discovery"] = {"n": len(a1), "pf": pf(a1)}; row["validation"] = {"n": len(a2), "pf": pf(a2)}
        out["h%.2f" % h] = row
    return out
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: sys.exit(__doc__)
    if os.environ.get("OIREL_READ") != "1": sys.exit("REFUSED: OIREL_READ=1 is not set (reading starts only when the Head or Auditor B clears the extract)")
    sp = next((float(x.split("=", 1)[1]) for x in sys.argv[1:] if x.startswith("--split=")), None)
    import json; print(json.dumps(run(a[0], sp), indent=1, default=str))
