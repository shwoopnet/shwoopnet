"""The book-replay line for Desk A's CFRTI-K development rows on the part R6 covers. Fills from results/CFRTI_K_DEV_REPLAY_GRID.csv (cfrti_dev_replay_grid.py:
1 contract, walk the levels to the limit, first poll at least 2 s / 6 s after the decision and within 4 s of that); outcome = the R6 coverage result
(closes before 2026-11-05 only). Fee 0.07 p (1-p) unrounded, as CFRTI-K registered. The same test's rows, a fill line beside its figure; no new try.
usage: python3 -I cfrti_k_replay_line.py <r6_root> <grid_csv> <out_json>
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, r6load as R
R6, GRID, OUT = sys.argv[1:4]
G = pd.read_csv(GRID)
assert (pd.to_datetime(G["t0_utc"], utc=True) < pd.Timestamp("2026-11-05T00:00:00Z")).all()
parts = []
for d in R.run_dirs(R6):
    f = os.path.join(d, "coverage.csv.gz")
    if os.path.exists(f):
        c = pd.read_csv(f, dtype={"ticker": str, "result": str}, usecols=["ticker", "result"]); parts.append(c[c["ticker"].isin(set(G["ticker"]))])
res = pd.concat(parts).dropna().drop_duplicates("ticker").set_index("ticker")["result"]
G["result"] = G["ticker"].map(res); G = G[G["result"].isin(["yes", "no"])].copy()
G["win"] = (G["result"] == G["side"]).astype(float)
fee = lambda p: 0.07 * p * (1 - p)
def line(p, m):
    p = p[m]; w = G["win"][m]; v = (w - p - fee(p)).to_numpy()
    g, l = v[v > 0].sum(), -v[v < 0].sum()
    return {"n": int(m.sum()), "wins": int(w.sum()), "pf": round(float(g / l), 3) if l > 0 else None, "mean_c": round(float(v.mean() * 100), 2) if len(v) else None, "mean_price": round(float(p.mean()), 4) if len(p) else None}
rep = G["status"] == "replayed"
out = {"rows_given": int(len(pd.read_csv(GRID))), "rows_with_result": int(len(G)), "rows_with_an_r6_book": int(rep.sum()),
       "paper_at_the_candle_ask_all_rows": line(G["ask_seen"], G["ask_seen"].notna()),
       "paper_at_the_candle_ask_rows_with_a_book": line(G["ask_seen"], rep),
       "book_ask_at_the_decision_minus_candle_ask_c": {"mean": round(float((G["r6_ask_at_t0"] - G["ask_seen"])[rep].mean() * 100), 2), "share_within_1c": round(float(((G["r6_ask_at_t0"] - G["ask_seen"])[rep].abs() <= 0.01 + 1e-9).mean()), 3)}}
for d in (2, 6, 10):
    for L in (0, 1):
        f = rep & (G["fill1_L%d_%ds" % (L, d)] == 1)
        o = line(pd.to_numeric(G["px1_L%d_%ds" % (L, d)], errors="coerce"), f); o["filled_of"] = "%d of %d" % (int(f.sum()), int(rep.sum()))
        out["book_replay_%ds_limit_%s" % (d, "at_the_ask_seen" if L == 0 else "plus_1c")] = o
        miss = rep & (G["fill1_L%d_%ds" % (L, d)] != 1)
        out["missed_%ds_limit_%s_paper_result" % (d, "at_the_ask_seen" if L == 0 else "plus_1c")] = line(G["ask_seen"], miss)
json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(out, indent=1))
