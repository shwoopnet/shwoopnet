"""OIREL-X reader (Desk A, Nov 15 2026), built to OIRELX_HAND_CASE_NOV15.md (committed first at 2bea3f885). Offline; reads one SQLite extract and sends nothing. Reuses oirel_haircut.decide and .cash UNCHANGED; loops over series, one market (series) at a time, no refit.
  OIRELX_READ=1 python3 -I oirelx.py <OIRELX_extract.sqlite>     DEFAULT-CLOSED. Prints a table per series and the try count. Label: "upper bound, not fill-checked; fee mode per-order rounded"."""
import sys, os, json, sqlite3, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import oirel_haircut as R
C11 = {"KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXNATGAS15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXAUDUSD15M", "KXUSDCAD15M", "KXHYPE15M", "KXBNB15M", "KXINX15M"}
FLOOR = 0.08; MIN_N = 100
def pf_halves(xs):
    half = len(xs) // 2
    return R.pf(xs), R.pf(xs[:half]), R.pf(xs[half:])
def stats(trades):
    out = {"n": len(trades)}
    for h in R.HAIRCUTS:
        xs = [R.cash(s, r, a, h)[0] for _, _, s, a, r in trades]; p, p1, p2 = pf_halves(xs)
        out["h%.2f" % h] = {"net": round(sum(xs), 6), "pf": p, "half1_pf": p1, "half2_pf": p2, "wins": sum(x > 0 for x in xs), "losses": sum(x < 0 for x in xs)}
    return out
def flags(st, c11):
    n = st["n"]
    if n < MIN_N: return {"pass_standard": None, "pass_c11": None, "evidence": "no evidence at n = %d" % n}
    a, b = st["h0.01"], st["h0.02"]
    std = a["pf"] >= 1.3 and a["half1_pf"] >= 1.0 and a["half2_pf"] >= 1.0 and b["pf"] >= 1.0
    c = b["pf"] >= 1.3 and b["half1_pf"] >= 1.0 and b["half2_pf"] >= 1.0
    return {"pass_standard": bool(std), "pass_c11": bool(c), "applicable": "pass_c11" if c11 else "pass_standard", "evidence": "n = %d" % n}
def run(db, series_list=None):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    cand = collections.defaultdict(dict)
    for tk, e, b, a, v, oi in c.execute("select ticker,end_ts,bid_c,ask_c,volume,oi from candle"): cand[tk][int(e)] = (b, a, v, oi)
    rows = collections.defaultdict(list)
    srcs = collections.defaultdict(collections.Counter)
    for tk, ser, cl, res, src in c.execute("select ticker, series, close_ts, result, src from market order by close_ts"): rows[ser].append((tk, int(cl), res)); srcs[ser][src] += 1
    out = {"label": "upper bound, not fill-checked; fee mode per-order rounded; rule frozen as OIREL1, no refit; each series is one try", "series": {}}
    for ser in sorted(rows):
        if series_list and ser not in series_list: continue
        trades, cnt = [], collections.Counter()
        for tk, cl, res in rows[ser]:
            if res not in ("yes", "no"): cnt["no_result"] += 1; continue
            d = R.decide(cand.get(tk, {}), cl); cnt[d[0]] += 1
            if d[0] == "trade": trades.append((d[3], cl, d[1], d[2], res))
        trades.sort()
        st = stats(trades); hi = [t for t in trades if t[3] >= FLOOR - 1e-9]; lo = [t for t in trades if t[3] < FLOOR - 1e-9]
        home = ser == "KXBTC15M"                                  # the rule's home market (the threshold is Bitcoin's discovery quantile): in-sample, never a try
        out["series"][ser] = {"in_sample_home_market_not_a_try": home, "counts": dict(cnt), "sources_of_kept_markets": dict(srcs[ser]), "all": st, "fill_0.08_or_more": stats(hi), "fill_under_0.08": stats(lo), "c11_series": ser in C11, "flags": flags(st, ser in C11)}
    out["tries"] = sum(1 for v in out["series"].values() if not v["in_sample_home_market_not_a_try"])
    out["note"] = "each series is one try (the count above); the Head sets the bar for a pooled pass; any claim across series needs day-clustered statistics; platinum and palladium are standard series here but thin non-crypto books: both flags printed, the Head decides which governs"
    return out
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: sys.exit(__doc__)
    if os.environ.get("OIRELX_READ") != "1": sys.exit("REFUSED: OIRELX_READ=1 is not set (reading starts only when Auditor B has cleared it)")
    print(json.dumps(run(a[0]), indent=1, default=str))
