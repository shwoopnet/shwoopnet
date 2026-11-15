"""XRPFAV6 and XRPFAV10 haircut recompute reader (Desk A, Nov 15 2026), built to XRPFAV_HAND_CASE_NOV15.md (expected figures committed first at 88f952e3b). Offline; reads one SQLite extract (market, candle) and sends nothing.
  XRPFAV_READ=1 python3 -I xrpfav_haircut.py <XRPFAV_extract.sqlite>     DEFAULT-CLOSED: refuses without XRPFAV_READ=1. Prints raw, +1c and +2c for both rules.
Rule: research branch src/scalper/regime_b2.py rows XRPFAV6 and XRPFAV10 (see the hand case). Drops every candle ending after its market's close. Label: "upper bound, not fill-checked; fee mode per-order rounded"."""
import sys, os, math, sqlite3, collections, json
SIZE = 10; HAIRCUTS = (0.0, 0.01, 0.02); EPS = 1e-9
RULES = {"XRPFAV6": dict(lo=0.88, hi=0.92, left_hi=400, left_lo=330, maxspread=0.02), "XRPFAV10": dict(lo=0.88, hi=0.92, left_hi=640, left_lo=570, maxspread=None)}
def fee_up_order(p, contracts=SIZE): return math.ceil(0.07 * contracts * p * (1 - p) * 100 - 1e-9) / 100
def _num(x):
    try: v = float(x)
    except (TypeError, ValueError): return None
    return v if v == v else None
def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 and w > 0 else (w / l if l else float("nan"))
def decide(rule, candles, close_ts):
    """candles: end_ts -> (bid, ask). Returns ('trade', side, p) or ('skip', why)."""
    R = RULES[rule]; cs = {t: v for t, v in candles.items() if t <= close_ts}          # standing reader rule: drop candles after the close
    pick = None
    for t in sorted(cs):
        if R["left_lo"] <= close_ts - t <= R["left_hi"]: pick = t                       # the LAST candle in the range (as regime_b2)
    if pick is None: return ("skip", "no_candle")
    b, a = _num(cs[pick][0]), _num(cs[pick][1])
    if b is None or a is None or b <= 0 or a >= 1 or a <= b: return ("skip", "bad_quote")
    tol = 0
    if R["maxspread"] is not None:
        if a - b > R["maxspread"] + EPS: return ("skip", "spread")
        tol += a - b > R["maxspread"]                                                    # traded here only because of the 1e-9 tolerance (regime_b2 skips it)
    ysp, nsp = a, 1 - b
    side, p = ("yes", ysp) if ysp >= nsp else ("no", nsp)
    if not (R["lo"] - EPS <= p <= R["hi"] + EPS): return ("skip", "band")
    tol += not (R["lo"] <= p <= R["hi"])
    return ("trade", side, p, bool(tol))
def cash(side, result, p, h):
    price = min(0.99, p + h); win = 1 if result == side else 0
    return SIZE * (win - price) - fee_up_order(price)
def run(db):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    mk = c.execute("select ticker, close_ts, result from market where series='KXXRP15M' order by close_ts").fetchall()
    cand = collections.defaultdict(dict)
    for tk, e, b, a in c.execute("select ticker,end_ts,bid_c,ask_c from candle"): cand[tk][int(e)] = (b, a)
    out = {"label": "upper bound, not fill-checked; fee mode per-order rounded; CUT-WINDOW RECOMPUTE, not a reproduction of 481 / 358", "differences_from_regime_b2": "(1) picks the last candle in range THEN skips it if incomplete (regime_b2 drops incomplete candles first); (2) 1e-9 tolerance on spread and band (regime_b2 plain comparisons); (3) no n_candles filter", "excluded_tickers_dropped": "0 of the 28 (none present)"}
    for rule in RULES:
        trades, cnt = [], collections.Counter()
        for tk, close_ts, result in mk:
            if result not in ("yes", "no"): cnt["no_result"] += 1; continue
            d = decide(rule, cand.get(tk, {}), int(close_ts))
            if d[0] == "trade": trades.append((int(close_ts), d[1], d[2], result)); cnt["trade"] += 1; cnt["trade_on_1e-9_tolerance"] += d[3]
            else: cnt[d[1]] += 1
        trades.sort(); res = {"n": len(trades), "counts": dict(cnt)}
        for h in HAIRCUTS:
            xs = [cash(s, r, p, h) for _, s, p, r in trades]; half = len(xs) // 2
            res["h%.2f" % h] = {"net": round(sum(xs), 6), "pf": pf(xs), "wins": sum(x > 0 for x in xs), "losses": sum(x < 0 for x in xs), "half1": {"n": half, "pf": pf(xs[:half]), "net": round(sum(xs[:half]), 6)}, "half2": {"n": len(xs) - half, "pf": pf(xs[half:]), "net": round(sum(xs[half:]), 6)}}
        out[rule] = res
    return out
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: sys.exit(__doc__)
    if os.environ.get("XRPFAV_READ") != "1": sys.exit("REFUSED: XRPFAV_READ=1 is not set (reading starts only when the Head or Auditor B clears it)")
    print(json.dumps(run(a[0]), indent=1, default=str))
