"""Task 5: taker cost summaries for the families recorded as market-list quotes (politics, combos, sports in-game, weather, daily watchlist, perps).
Measurement only: no rule scored, no result VALUE used (results files are read only for close and settle times). No network.
usage: python3 -I listcosts.py <data_root> <out_json>
"""
import sys, os, glob, json
import numpy as np
import pandas as pd
ROOT, OUT = sys.argv[1], sys.argv[2]
fee = lambda p: 0.07 * p * (1 - p)


def q(v, qs=(50, 75)):
    v = pd.to_numeric(pd.Series(v), errors="coerce").dropna().to_numpy()
    return [round(float(x), 4) for x in np.percentile(v, qs)] if len(v) else None


def cost_block(D, bid="yes_bid", ask="yes_ask", size_cols=(), vol="volume", key="ticker"):
    """D: quote rows. Two-sided = bid > 0 and ask < 1 and ask > bid."""
    D = D.copy()
    D[bid] = pd.to_numeric(D[bid], errors="coerce"); D[ask] = pd.to_numeric(D[ask], errors="coerce")
    D = D.dropna(subset=[bid, ask])
    two = D[(D[bid] > 0) & (D[ask] < 1) & (D[ask] > D[bid])]
    o = {"quote_rows": int(len(D)), "markets": int(D[key].nunique()), "share_rows_two_sided": round(len(two) / len(D), 4) if len(D) else None,
         "markets_ever_two_sided": int(two[key].nunique())}
    if len(two) == 0:
        return o
    sp = two[ask] - two[bid]; mid = (two[ask] + two[bid]) / 2; cheap = np.minimum(mid, 1 - mid)
    hold = sp / 2 + fee(mid); rt = sp + fee(two[ask]) + fee(two[bid])
    o.update({"spread_median_p75_p90": q(sp, (50, 75, 90)), "mid_median": q(mid, (50,))[0], "cheap_side_price_median": q(cheap, (50,))[0],
              "fee_at_mid_median": q(fee(mid), (50,))[0], "hold_cost_median_p75": q(hold), "round_trip_median_p75": q(rt),
              "round_trip_over_cheap_side_price_median": q(rt / cheap.clip(lower=0.005), (50,))[0]})
    # near the money only (mid 20c to 80c): where a card would usually trade
    nm = two[(mid >= 0.2) & (mid <= 0.8)]
    if len(nm):
        sp2 = nm[ask] - nm[bid]; m2 = (nm[ask] + nm[bid]) / 2
        o["mid_20_80c"] = {"rows": int(len(nm)), "markets": int(nm[key].nunique()), "spread_median_p75_p90": q(sp2, (50, 75, 90)),
                           "hold_cost_median_p75": q(sp2 / 2 + fee(m2)), "round_trip_median_p75": q(sp2 + fee(nm[ask]) + fee(nm[bid]))}
    for c in size_cols:
        if c in two:
            o["touch_" + c + "_median_p25"] = q(two[c], (50, 25))
    if vol in D:
        last = D.sort_values(D.columns[0]).groupby(key)[vol].last()
        o["volume_per_market_median_p75"] = q(last); o["markets_with_zero_volume_share"] = round(float((pd.to_numeric(last, errors="coerce").fillna(0) <= 0).mean()), 4)
    return o


def rd(pattern, **kw):
    fs = sorted(glob.glob(os.path.join(ROOT, pattern), recursive=True))
    return (pd.concat([pd.read_csv(f, **kw).assign(_file=os.path.relpath(f, ROOT)) for f in fs], ignore_index=True) if fs else pd.DataFrame()), fs


out = {"note": "dollars (0.01 = 1 cent); list quotes are a copy up to about 11 s old; result values never used"}

# ---- politics ----
P, fs = rd("pol-data/polrec/*/*/quotes.csv.gz", dtype={"ticker": str})
if len(P):
    P["close"] = pd.to_datetime(P["close_time"], utc=True); P["t"] = pd.to_datetime(P["t_recv_ms"], unit="ms", utc=True)
    P["days_to_close"] = (P["close"] - P["t"]) / pd.Timedelta(days=1)
    blk = cost_block(P, size_cols=("yes_bid_size", "yes_ask_size"))
    blk.update({"snapshots": len(fs), "files": [os.path.relpath(f, ROOT) for f in fs], "series": int(P["series"].nunique()), "events_open": int(P["event_ticker"].nunique()),
                "days_to_close_median_p25_p75": q(P.drop_duplicates("ticker")["days_to_close"], (50, 25, 75)), "open_interest_per_market_median": q(P.groupby("ticker")["open_interest"].last(), (50,))[0]})
    per = {}
    for s, G in P.groupby("series"):
        b = cost_block(G, size_cols=("yes_ask_size",))
        per[s] = {k: b.get(k) for k in ("markets", "share_rows_two_sided", "spread_median_p75_p90", "round_trip_median_p75", "volume_per_market_median_p75", "mid_20_80c")}
        per[s]["events_open"] = int(G["event_ticker"].nunique())
    blk["per_series"] = per
    Rz, _ = rd("pol-data/polrec/*/*/results.csv.gz", dtype={"ticker": str})
    if len(Rz):
        Rz = Rz.drop(columns=["result", "expiration_value"]).drop_duplicates("ticker")
        Rz["close"] = pd.to_datetime(Rz["close_time"], utc=True)
        blk["settled_in_results_files"] = {"markets": int(len(Rz)), "events": int(Rz["event_ticker"].nunique()),
                                           "events_by_series": Rz.groupby("series")["event_ticker"].nunique().sort_values(ascending=False).head(15).to_dict(),
                                           "close_span": [str(Rz["close"].min()), str(Rz["close"].max())]}
    out["politics"] = blk

# ---- combos ----
C, fs = rd("combo-data/combo/*/*/quotes.csv.gz", dtype={"ticker": str})
if len(C):
    blk = cost_block(C, size_cols=("yes_bid_size", "yes_ask_size"))
    for c in ("yes_bid", "yes_ask", "no_bid", "no_ask"):
        C[c] = pd.to_numeric(C[c], errors="coerce")
    blk.update({"snapshots": len(fs), "files": [os.path.relpath(f, ROOT) for f in fs], "legs_median_p25_p75": q(C["legs"], (50, 25, 75)),
                "share_with_a_yes_ask_under_1": round(float((C["yes_ask"] < 1).mean()), 4), "share_with_a_yes_bid_above_0": round(float((C["yes_bid"] > 0).mean()), 4),
                "yes_ask_median_when_posted": q(C.loc[C["yes_ask"] < 1, "yes_ask"], (50,))[0] if (C["yes_ask"] < 1).any() else None})
    cov, _ = rd("combo-data/combo/*/*/coverage.csv.gz")
    blk["coverage_rows"] = cov.drop(columns=["_file"]).to_dict("records") if len(cov) else None
    T, _ = rd("combo-data/combo/*/*/trades.csv.gz", dtype={"ticker": str})
    blk["trades_rows"] = int(len(T)); blk["trade_price_median"] = q(T["yes_price_dollars"], (50,))[0] if len(T) else None
    out["combos"] = blk

# ---- sports in-game ----
Sx, fs = rd("sports-data/ingame/*/*/obs.csv.gz", dtype={"ticker": str})
if len(Sx):
    Sx["sport"] = Sx["event"].str.extract(r"^KX(NBA|NHL|NFL)")[0]
    Sx["game"] = Sx["event"].str.replace(r"^KX(NBA|NHL|NFL)(GAME|SPREAD|TOTAL)-", "", regex=True)
    blk = {"files": len(fs), "days": sorted({f.split("/")[2] for f in [os.path.relpath(x, ROOT) for x in fs]}), "by_sport_and_kind": {}}
    for (sp_, kind), G in Sx.groupby(["sport", "kind"]):
        b = cost_block(G, size_cols=("bid_size", "ask_size"))
        b["games"] = int(G["game"].nunique())
        blk["by_sport_and_kind"]["%s %s" % (sp_, kind)] = b
    blk["games_by_sport"] = Sx.groupby("sport")["game"].nunique().to_dict()
    gap = Sx.sort_values("t_recv_ms").groupby("ticker")["t_recv_ms"].diff() / 1000.0
    blk["seconds_between_polls_median_p25_p75"] = q(gap, (50, 25, 75))
    out["sports_in_game"] = blk

# ---- weather ----
for nm, sub in (("weather_high", "quotes"), ("weather_low", "quotes_low")):
    W, fs = rd("quote-data/wxens/%s/*/*.csv.gz" % sub, dtype={"ticker": str})
    if len(W):
        blk = cost_block(W)
        blk.update({"files": len(fs), "cities": int(W["city"].nunique()), "events": int(W["event_ticker"].nunique()), "target_dates": int(W["target_date"].nunique()),
                    "brackets_per_event_median": q(W.groupby("event_ticker")["ticker"].nunique(), (50,))[0], "sizes": "not recorded"})
        out[nm] = blk
for nm, sub in (("weather_high_settle", "results"), ("weather_low_settle", "results_low")):
    Rw, fs = rd("quote-data/wxens/%s/*/*.csv.gz" % sub, dtype={"ticker": str})
    if len(Rw):
        Rw = Rw.drop(columns=["result", "expiration_value"]).sort_values("seen_ts").drop_duplicates("ticker")
        d = (Rw["seen_ts"] - (pd.to_datetime(Rw["close_time"], utc=True) - pd.Timestamp("1970-01-01", tz="UTC")) / pd.Timedelta(seconds=1)) / 3600.0
        out[nm] = {"markets": int(len(Rw)), "hours_from_close_to_first_seen_settled_median_p25_p75": q(d, (50, 25, 75)), "note": "an upper bound: the result is looked for only a few times a day"}

# ---- daily watchlist ----
Dq, fs = rd("quote-data/daily/quotes/*/*.csv.gz", dtype={"ticker": str})
if len(Dq):
    blk = {"files": len(fs), "per_series": {}}
    for s, G in Dq.groupby("series"):
        b = cost_block(G)
        blk["per_series"][s] = {k: b.get(k) for k in ("quote_rows", "markets", "share_rows_two_sided", "spread_median_p75_p90", "cheap_side_price_median", "hold_cost_median_p75",
                                                         "round_trip_median_p75", "volume_per_market_median_p75", "mid_20_80c")}
        blk["per_series"][s]["events"] = int(G["event_ticker"].nunique()); blk["per_series"][s]["tests"] = sorted(set(G["tests"].dropna().astype(str)))[:3]
        blk["per_series"][s]["mins_to_close_median"] = q(G["mins_to_close"], (50,))[0]
    out["daily_watchlist"] = blk
Dr, _ = rd("quote-data/daily/results/*/*.csv.gz", dtype={"ticker": str})
if len(Dr):
    Dr = Dr.drop(columns=["result", "expiration_value"]).drop_duplicates("ticker")
    d = (pd.to_datetime(Dr["settlement_ts"], utc=True, errors="coerce") - pd.to_datetime(Dr["close_time"], utc=True, errors="coerce")) / pd.Timedelta(minutes=1)
    Dr["settle_min"] = d
    out["daily_watchlist_settle"] = {"markets": int(len(Dr)), "minutes_close_to_settlement_median_p25_p75": q(d, (50, 25, 75)),
                                     "per_series_median_minutes": Dr.groupby("series")["settle_min"].median().round(1).dropna().to_dict(),
                                     "events_per_series": Dr.groupby("series")["event_ticker"].nunique().to_dict()}

# ---- perps ----
for nm, pat in (("perps_30s_close_window", "perp-data/perps30/*/*.csv.gz"), ("perps_hourly", "perp-data/perps/perps-2026-11-1*.csv")):
    Pp, fs = rd(pat, dtype={"ticker": str})
    if len(Pp):
        for c in ("bid", "ask", "price", "bid_size", "ask_size", "volume_24h"):
            Pp[c] = pd.to_numeric(Pp[c], errors="coerce")
        A = Pp[(Pp["status"] == "active") & (Pp["bid"] > 0) & (Pp["ask"] > Pp["bid"])]
        A = A.assign(bps=(A["ask"] - A["bid"]) / ((A["ask"] + A["bid"]) / 2) * 1e4)
        blk = {"files": len(fs), "rows": int(len(Pp)), "markets": int(Pp["ticker"].nunique()), "share_rows_active_two_sided": round(len(A) / len(Pp), 4), "by_asset_class": {}}
        for k, G in A.groupby("asset_class"):
            pm = G.groupby("ticker")["bps"].median()
            blk["by_asset_class"][k] = {"markets": int(G["ticker"].nunique()), "spread_bps_median_of_market_medians": q(pm, (50,))[0], "spread_bps_p25_p75_across_markets": q(pm, (25, 75)),
                                        "volume_24h_median_across_markets": q(G.groupby("ticker")["volume_24h"].median(), (50,))[0]}
        out[nm] = blk
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps({k: (v if k in ("note",) else {kk: vv for kk, vv in v.items() if kk not in ("per_series", "files", "by_sport_and_kind", "by_asset_class", "per_series_median_minutes", "events_per_series")}) for k, v in out.items()}, indent=1, default=float))
