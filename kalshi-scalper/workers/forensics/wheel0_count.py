"""WHEEL0 count (Forensics desk, 2026-11-12): how many fill-checked signals, 60-blocks and block pairs the R6 books hold.
BOOKS ONLY. No result is loaded: the coverage file's result column is never read (usecols leaves it out). Nothing is scored. Zero tries.
Design constants are the Head of R&D's (message of 19:53Z); this file chooses none of them except the one flagged LOOK_TOL_S.
usage: python3 -I wheel0_count.py <root holding book15r6/> <out.json>
"""
import sys, os, json, glob
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r6load as R

ROOT, OUT = sys.argv[1], sys.argv[2]
SERIES = ["KXGOLD15M", "KXXRP15M", "KXDOGE15M"]                 # rule (h): Bitcoin and Ethereum are not read from books at all
BEFORE = pd.Timestamp("2026-11-13T00:00:00Z")
LOOKS = [600, 360, 180]
BANDS = {"cheap": [("05-20", 0.05, 0.20, "[)"), ("20-35", 0.20, 0.35, "[)"), ("35-50", 0.35, 0.50, "[]")],
         "fav": [("50-65", 0.50, 0.65, "(]"), ("65-80", 0.65, 0.80, "(]"), ("80-88", 0.80, 0.88, "()")]}
FAV_HI = ("88-97", 0.88, 0.97, "[]")                          # the third line, reported apart
SPREAD_MAX, SLIP, SIZE, FILL_WITHIN_MS, BLOCK = 0.04, 0.01, 10, 4000, 60
LOOK_TOL_S = 10          # FLAGGED, not in the Head's text: the look poll must arrive within 10 s of close minus L, else the window has no look at that L
EPS = 1e-9

def inband(a, lo, hi, kind):
    left = a >= lo - EPS if kind[0] == "[" else a > lo + EPS
    right = a <= hi + EPS if kind[1] == "]" else a < hi - EPS
    return left and right

# coverage WITHOUT the result column
parts = []
for d in R.run_dirs(ROOT):
    f = os.path.join(d, "coverage.csv.gz")
    if os.path.exists(f):
        c = pd.read_csv(f, dtype={"ticker": str}, usecols=["close_time", "series", "ticker", "max_gap_ms"])
        parts.append(c[c["ticker"].notna() & c["series"].isin(SERIES)])
cov = pd.concat(parts, ignore_index=True)
cov["close_ts"] = pd.to_datetime(cov["close_time"], utc=True)
cov = cov.groupby("ticker").agg(series=("series", "first"), close_ts=("close_ts", "first")).query("close_ts < @BEFORE")
cov["close_ms"] = ((cov["close_ts"] - R.EPOCH) / pd.Timedelta(milliseconds=1)).astype("int64")
close_ms = cov["close_ms"].to_dict()
books = R.load_books(ROOT, cov.index, min_left_s=min(LOOKS) - LOOK_TOL_S - 6, max_left_s=max(LOOKS) + 1, close_ms=close_ms)
px = books[R.PX].to_numpy(float); sz = books[R.SZ].to_numpy(float); tt = books["t_recv_ms"].to_numpy("int64")
starts = {tk: (i0, i1) for tk, (i0, i1) in zip(*[books["ticker"].drop_duplicates().tolist(), zip(np.r_[0, np.flatnonzero(books["ticker"].to_numpy()[1:] != books["ticker"].to_numpy()[:-1]) + 1],
                                                                                                    np.r_[np.flatnonzero(books["ticker"].to_numpy()[1:] != books["ticker"].to_numpy()[:-1]) + 1, len(books)])])}

def walk(bid_px, bid_sz, limit):
    """Buy SIZE of a side: take the OTHER side's bids best first while the implied ask (1 - bid) is at or under the limit. -> average price or None."""
    need, cost = SIZE, 0.0
    for p, s in zip(bid_px, bid_sz):
        if not (p == p) or not (s == s) or s <= 0: continue
        a = 1.0 - p
        if a > limit + EPS: break
        take = min(need, s); cost += take * a; need -= take
        if need <= EPS: return cost / SIZE
    return None

rows = []
cnt = {"windows_in_coverage": int(len(cov)), "windows_with_any_book_row": 0}
for tk, (i0, i1) in starts.items():
    cnt["windows_with_any_book_row"] += 1
    T = close_ms[tk]; t = tt[i0:i1]; ser = cov.at[tk, "series"]; day = cov.at[tk, "close_ts"].strftime("%Y-%m-%d")
    for L in LOOKS:
        k = int(np.searchsorted(t, T - L * 1000, side="left"))
        if k >= len(t) or t[k] > T - L * 1000 + LOOK_TOL_S * 1000:
            rows.append((ser, day, tk, L, "no_look", "", "")); continue
        r = i0 + k
        yb, nb = px[r, 0], px[r, 5]
        if not (yb == yb and nb == nb and yb > 0 and nb > 0):
            rows.append((ser, day, tk, L, "one_sided", "", "")); continue
        ya, na = 1.0 - nb, 1.0 - yb
        if ya - yb > SPREAD_MAX + EPS:
            rows.append((ser, day, tk, L, "spread_wide", "", "")); continue
        if abs(ya - na) < EPS:
            rows.append((ser, day, tk, L, "equal_asks", "", "")); continue
        sides = {"cheap": ("yes", ya) if ya < na else ("no", na), "fav": ("yes", ya) if ya > na else ("no", na)}
        # fill poll: the first poll AFTER the look and within 4 s of it
        j = k + 1
        fill_row = i0 + j if (j < len(t) and t[j] - t[k] <= FILL_WITHIN_MS) else None
        for kind, (side, ask) in sides.items():
            band = next((b[0] for b in BANDS[kind] if inband(ask, b[1], b[2], b[3])), None)
            if band is None and kind == "fav" and inband(ask, FAV_HI[1], FAV_HI[2], FAV_HI[3]): band = FAV_HI[0]
            if band is None:
                rows.append((ser, day, tk, L, "out_of_band", kind, "")); continue
            if fill_row is None:
                rows.append((ser, day, tk, L, "no_fill_poll", kind, band)); continue
            cols = slice(5, 10) if side == "yes" else slice(0, 5)           # buying YES takes NO bids, buying NO takes YES bids
            avg = walk(px[fill_row, cols], sz[fill_row, cols], ask + SLIP)
            rows.append((ser, day, tk, L, "filled" if avg is not None else "missed", kind, band))
df = pd.DataFrame(rows, columns=["series", "day", "ticker", "L", "status", "kind", "band"])
out = {"note": "books only; no result loaded; nothing scored", "series": SERIES, "closes_before": str(BEFORE), "first_close": str(cov["close_ts"].min()), "last_close": str(cov["close_ts"].max()),
       "days_with_a_window": int(cov["close_ts"].dt.strftime("%Y-%m-%d").nunique()), "counts": cnt, "flag": "LOOK_TOL_S = %d s is this desk's addition" % LOOK_TOL_S,
       "windows_by_series": cov["series"].value_counts().to_dict(), "status_by_series_L": {}, "templates": [], "fav_88_97": []}
for (ser, L), g in df.groupby(["series", "L"]):
    out["status_by_series_L"]["%s L%d" % (ser, L)] = g["status"].value_counts().to_dict()
sig = df[df["status"].isin(["filled", "missed", "no_fill_poll"])]
tot_blocks = tot_pairs = 0
for (ser, L, kind, band), g in sig.groupby(["series", "L", "kind", "band"]):
    n_sig, n_fill = int(len(g)), int((g["status"] == "filled").sum())
    row = {"series": ser, "L": int(L), "side": kind, "band": band, "signals_at_look": n_sig, "filled": n_fill, "fill_share": round(n_fill / n_sig, 3) if n_sig else None,
           "blocks_of_60": n_fill // BLOCK, "pairs": max(0, n_fill // BLOCK - 1), "days": int(g.loc[g["status"] == "filled", "day"].nunique())}
    if band == FAV_HI[0]: out["fav_88_97"].append(row)
    else:
        out["templates"].append(row); tot_blocks += row["blocks_of_60"]; tot_pairs += row["pairs"]
out["total_blocks_18_templates_x_3_series"] = tot_blocks; out["total_pairs"] = tot_pairs
out["hot_pairs_if_8_percent_of_first_blocks_are_hot"] = round(0.08 * tot_pairs, 1)
json.dump(out, open(OUT, "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ("templates", "fav_88_97", "status_by_series_L")}, indent=1))
t = pd.DataFrame(out["templates"]); print(t.to_string(index=False))
print(pd.DataFrame(out["fav_88_97"]).to_string(index=False))
