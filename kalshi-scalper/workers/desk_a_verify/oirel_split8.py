"""OIREL 8c-or-more split (Desk A, Nov 15 2026), built to OIREL_SPLIT8_HAND_CASE_NOV15.md (committed first at 261377938). Reuses oirel_haircut.decide and .cash unchanged; reads one SQLite extract; sends nothing. Information only, no new try.
  OIREL_READ=1 python3 -I oirel_split8.py <OIREL_extract.sqlite>     DEFAULT-CLOSED. Prints the full 5c to 50c band and the subset whose FILL price (the ask of the bought side on the candle ending 120 s before the close) is 0.08 or more (1e-9 tolerance).
Label: "upper bound, not fill-checked; fee mode per-order rounded"."""
import sys, os, json, sqlite3, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import oirel_haircut as R
FLOOR = 0.08
def summarize(trades):
    out = {"n": len(trades)}
    for h in R.HAIRCUTS:
        xs = [R.cash(s, r, a, h)[0] for _, _, s, a, r in trades]; half = len(xs) // 2
        out["h%.2f" % h] = {"net": round(sum(xs), 6), "pf": R.pf(xs), "wins": sum(x > 0 for x in xs), "losses": sum(x < 0 for x in xs), "half1": {"n": half, "pf": R.pf(xs[:half]), "net": round(sum(xs[:half]), 6)}, "half2": {"n": len(xs) - half, "pf": R.pf(xs[half:]), "net": round(sum(xs[half:]), 6)}}
    return out
def run(db):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    mk = c.execute("select ticker, close_ts, result from market where series='KXBTC15M' order by close_ts").fetchall()
    cand = collections.defaultdict(dict)
    for tk, e, b, a, v, oi in c.execute("select ticker,end_ts,bid_c,ask_c,volume,oi from candle"): cand[tk][int(e)] = (b, a, v, oi)
    trades = []
    for tk, cl, res in mk:
        if res not in ("yes", "no"): continue
        d = R.decide(cand.get(tk, {}), int(cl))
        if d[0] == "trade": trades.append((d[3], int(cl), d[1], d[2], res))
    trades.sort()
    return {"label": "upper bound, not fill-checked; fee mode per-order rounded; information only, no new try; split on the FILL price (ask of the bought side on the candle ending 120 s before the close)", "full_band": summarize(trades), "fill_price_0.08_or_more": summarize([t for t in trades if t[3] >= FLOOR - 1e-9]), "fill_price_under_0.08": summarize([t for t in trades if t[3] < FLOOR - 1e-9])}
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: sys.exit(__doc__)
    if os.environ.get("OIREL_READ") != "1": sys.exit("REFUSED: OIREL_READ=1 is not set")
    print(json.dumps(run(a[0]), indent=1, default=str))
