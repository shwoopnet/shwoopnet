"""Task 5: taker cost table for 15 minute series, from recorded order books (R6 book15r6/ or NC15 nc15/).

A measurement only. No rule is scored. The coverage file's result column is read ONLY as present or empty
(never its value). No network. Public recorded market data only.

usage: python3 -I fifteen.py <data_root> <folder> <out_json> <close_from_iso> <close_before_iso> <tol_ms> [label]
  data_root/<folder>/<date>/<HHMM>/{book,coverage}.csv.gz

Definitions (the fill haircut is the one in the forensics desk's fillhaircut1.py / goldhaircut1.py):
  two-sided instant: best YES bid and best NO bid both present and YES bid < 1 - NO bid.
  YES ask = 1 - best NO bid; NO ask = 1 - best YES bid. Size at the YES ask = size of the best NO bid, and the reverse.
  haircut: a 1 contract buy with limit = the ask seen at poll i. j = the first TWO-SIDED poll at least H ms later
           (H = 2000, 6000) and no more than H + tol ms later. Filled when ask_j <= limit ("L0"), or <= limit + 1c ("L1").
           Each two-sided instant gives two buys (YES side and NO side). "cheap" = the side whose ask is <= 0.50.
  strict variant: j = the first poll of ANY state at least H ms later; no ask on our side there counts as a miss.
"""
import sys, os, glob, json
import numpy as np
import pandas as pd

ROOT, FOLDER, OUT, C_FROM, C_BEFORE, TOL = sys.argv[1], sys.argv[2], sys.argv[3], pd.Timestamp(sys.argv[4]), pd.Timestamp(sys.argv[5]), int(sys.argv[6])
LABEL = sys.argv[7] if len(sys.argv) > 7 else FOLDER
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
PXY = ["yes_bid_px_%d" % i for i in range(1, 6)]; PXN = ["no_bid_px_%d" % i for i in range(1, 6)]
SZY = ["yes_bid_sz_%d" % i for i in range(1, 6)]; SZN = ["no_bid_sz_%d" % i for i in range(1, 6)]
SPANS = {"look_6min_400_330s": (330.0, 400.0), "look_2to3min_180_120s": (120.0, 180.0)}
HS = (2000, 6000)
EPS = 1e-9
rng = np.random.default_rng(20261112)


def fee(p):
    return 0.07 * p * (1.0 - p)


def run_dirs():
    return sorted(d for d in glob.glob(os.path.join(ROOT, FOLDER, "*", "*")) if os.path.isdir(d))


def q(v, qs=(50, 75)):
    v = np.asarray(v, float); v = v[v == v]
    return [round(float(x), 5) for x in np.percentile(v, qs)] if len(v) else None


def cl_share(flag, w):
    """[share, lo, hi]: 95% interval by resampling whole windows."""
    flag = np.asarray(flag, float); w = np.asarray(w)
    if len(flag) == 0:
        return None
    u, inv = np.unique(w, return_inverse=True)
    num = np.bincount(inv, flag); den = np.bincount(inv, np.ones(len(flag)))
    pick = rng.integers(0, len(u), (1000, len(u)))
    bs = num[pick].sum(1) / np.maximum(den[pick].sum(1), 1e-12)
    return [round(float(num.sum() / den.sum()), 4), round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)]


# ---- coverage: windows, volume, result presence (never its value) ----
parts = []
for d in run_dirs():
    f = os.path.join(d, "coverage.csv.gz")
    if os.path.exists(f) and os.path.getsize(f) > 0:
        c = pd.read_csv(f, dtype={"ticker": str, "result": str, "note": str})
        c["run"] = os.path.relpath(d, ROOT)
        parts.append(c)
cov_all = pd.concat(parts, ignore_index=True)
cov_all["close_ts"] = pd.to_datetime(cov_all["close_time"], utc=True)
cov_all = cov_all[(cov_all["close_ts"] >= C_FROM) & (cov_all["close_ts"] < C_BEFORE)].copy()
cov_all["has_result"] = cov_all["result"].notna() & (cov_all["result"].astype(str).str.strip() != "")
cov_all = cov_all.drop(columns=["result"])          # the value is never used
cov_all["has_ticker"] = cov_all["ticker"].notna() & (cov_all["ticker"].astype(str) != "")
series_list = sorted(cov_all["series"].dropna().unique())

# ---- books ----
bparts = []
for d in run_dirs():
    f = os.path.join(d, "book.csv.gz")
    if os.path.exists(f) and os.path.getsize(f) > 0:
        b = pd.read_csv(f, usecols=["t_recv_ms", "ticker", "series", "close_time"] + PXY + SZY + PXN + SZN)
        b["close_ms"] = ((pd.to_datetime(b["close_time"], utc=True) - EPOCH) / pd.Timedelta(milliseconds=1)).astype("int64")
        b = b[(b["close_ms"] >= int((C_FROM - EPOCH) / pd.Timedelta(milliseconds=1))) & (b["close_ms"] < int((C_BEFORE - EPOCH) / pd.Timedelta(milliseconds=1)))]
        left = (b["close_ms"] - b["t_recv_ms"]) / 1000.0
        b = b[(left <= 410) & (left >= 60)]           # all that either span plus the later polls needs
        bparts.append(b.drop(columns=["close_time"]))
books = pd.concat(bparts, ignore_index=True).drop_duplicates(subset=["ticker", "t_recv_ms"]).sort_values(["ticker", "t_recv_ms"]).reset_index(drop=True)

out = {"label": LABEL, "folder": FOLDER, "closes_from": str(C_FROM), "closes_before": str(C_BEFORE), "later_poll_tolerance_ms": TOL,
       "note": "prices in dollars (0.01 = 1 cent); shares as fractions; [share, 2.5%, 97.5%] by resampling whole windows; result values never read",
       "run_dirs": [os.path.relpath(d, ROOT) for d in run_dirs()], "series": {}}

for s in series_list:
    cs = cov_all[cov_all["series"] == s]
    g = cs[cs["has_ticker"]].groupby("ticker").agg(close_ts=("close_ts", "first"), volume_fp=("volume_fp", "max"), tape_sum=("tape_sum_count", "max"),
                                                    has_result=("has_result", "max"), max_gap_ms=("max_gap_ms", "max"), polls=("ok_polls", "max"))
    slots = cs.groupby("close_ts")["has_ticker"].max()                 # one per recorded window slot
    by_day = g.groupby(g["close_ts"].dt.strftime("%Y-%m-%d %a")).size()
    slot_day = slots.groupby(slots.index.strftime("%Y-%m-%d %a")).agg(["size", "sum"])
    vol = pd.to_numeric(g["volume_fp"], errors="coerce")
    ev = {"window_slots_recorded": int(len(slots)), "slots_with_an_open_market": int(slots.sum()), "distinct_markets": int(len(g)),
          "first_close": str(g["close_ts"].min()) if len(g) else None, "last_close": str(g["close_ts"].max()) if len(g) else None,
          "markets_per_utc_day": {k: int(v) for k, v in by_day.items()},
          "slots_per_utc_day_recorded_and_open": {k: [int(r["size"]), int(r["sum"])] for k, r in slot_day.iterrows()},
          "result_present_at_post_close_read_share": round(float(g["has_result"].mean()), 4) if len(g) else None,
          "result_present_n": int(g["has_result"].sum()), "volume_contracts_median_per_window": q(vol, (50,))[0] if vol.notna().any() else None,
          "volume_contracts_p25_p75": q(vol, (25, 75)) if vol.notna().any() else None, "volume_n": int(vol.notna().sum()),
          "tape_sum_count_median": q(pd.to_numeric(g["tape_sum"], errors="coerce"), (50,))[0] if len(g) else None}
    res = {"events": ev, "looks": {}}
    bs = books[books["series"] == s]
    for span_name, (lo, hi) in SPANS.items():
        rows = []          # one per two-sided instant
        hc = []            # one per (instant, side) buy
        n_all = n_two = n_yes_only = n_no_only = n_empty = n_crossed = 0
        wins_all, wins_two = set(), set()
        for tk, gb in bs.groupby("ticker", sort=False):
            t = gb["t_recv_ms"].to_numpy(); T = int(gb["close_ms"].iloc[0])
            left = (T - t) / 1000.0
            yb = gb[PXY].to_numpy(float); nb = gb[PXN].to_numpy(float)
            ybs = np.nan_to_num(gb[SZY].to_numpy(float)); nbs = np.nan_to_num(gb[SZN].to_numpy(float))
            hy = yb[:, 0] == yb[:, 0]; hn = nb[:, 0] == nb[:, 0]
            usable = hy & hn & (yb[:, 0] < 1 - nb[:, 0] - EPS)
            insp = (left >= lo) & (left <= hi)
            if not insp.any():
                continue
            wins_all.add(tk)
            n_all += int(insp.sum()); n_two += int((insp & usable).sum())
            n_yes_only += int((insp & hy & ~hn).sum()); n_no_only += int((insp & ~hy & hn).sum()); n_empty += int((insp & ~hy & ~hn).sum())
            n_crossed += int((insp & hy & hn & ~usable).sum())
            uidx = np.flatnonzero(usable); ut = t[uidx]
            ask_y = 1 - nb; ask_n = 1 - yb
            for i in np.flatnonzero(insp & usable):
                wins_two.add(tk)
                ya, na, ybid, nbid = ask_y[i, 0], ask_n[i, 0], yb[i, 0], nb[i, 0]
                spread = ya - ybid; mid = (ya + ybid) / 2
                fav_yes = mid >= 0.5
                rows.append((tk, spread, mid, max(mid, 1 - mid), nbs[i, 0], ybs[i, 0],          # size at YES ask, size at NO ask
                             (nbs[i, 0] if fav_yes else ybs[i, 0]), (ybs[i, 0] if fav_yes else nbs[i, 0]),
                             spread / 2 + fee(mid), spread + fee(ya) + fee(ybid), fee(mid)))
                for side, a0, px, sz in (("yes", ya, ask_y, nbs), ("no", na, ask_n, ybs)):
                    rec = {"w": tk, "side": side, "a0": float(a0), "cheap": bool(a0 <= 0.5 + EPS)}
                    for H in HS:
                        k = np.searchsorted(ut, t[i] + H, side="left")
                        if k < len(uidx) and ut[k] <= t[i] + H + TOL and left[uidx[k]] > 0:
                            j = int(uidx[k])
                            rec["lag_%d" % H] = (t[j] - t[i]) / 1000.0
                            rec["L0_%d" % H] = float(px[j, 0] <= a0 + EPS)
                            rec["L1_%d" % H] = float(px[j, 0] <= a0 + 0.01 + EPS)
                            okp0 = px[j] <= a0 + EPS; okp1 = px[j] <= a0 + 0.01 + EPS
                            rec["L0sz_%d" % H] = float(sz[j][okp0].sum() >= 1 - 1e-6)
                            rec["L1sz_%d" % H] = float(sz[j][okp1].sum() >= 1 - 1e-6)
                        # strict: the first poll of any state
                        k2 = np.searchsorted(t, t[i] + H, side="left")
                        if k2 < len(t) and t[k2] <= t[i] + H + TOL and left[k2] > 0:
                            has_ask = (hn[k2] if side == "yes" else hy[k2])
                            rec["S0_%d" % H] = float(bool(has_ask) and px[k2, 0] <= a0 + EPS)
                            rec["S1_%d" % H] = float(bool(has_ask) and px[k2, 0] <= a0 + 0.01 + EPS)
                    hc.append(rec)
        look = {"instants_all": n_all, "instants_two_sided": n_two, "share_two_sided": round(n_two / n_all, 4) if n_all else None,
                "instants_yes_bids_only": n_yes_only, "instants_no_bids_only": n_no_only, "instants_empty_book": n_empty, "instants_crossed_or_locked": n_crossed,
                "windows_with_any_poll": len(wins_all), "windows_with_two_sided": len(wins_two)}
        if rows:
            R = pd.DataFrame(rows, columns=["w", "spread", "mid", "favpx", "sz_yes_ask", "sz_no_ask", "sz_fav_ask", "sz_cheap_ask", "hold", "rt", "fee_mid"])
            wm = R.groupby("w")["spread"].median()
            look.update({
                "spread_median_p75": q(R["spread"]), "spread_mean": round(float(R["spread"].mean()), 5), "spread_p90": q(R["spread"], (90,))[0],
                "spread_median_of_window_medians": q(wm, (50,))[0], "spread_p75_of_window_medians": q(wm, (75,))[0],
                "mid_median": q(R["mid"], (50,))[0], "favourite_price_median_p25_p75": q(R["favpx"], (50, 25, 75)),
                "touch_size_fav_ask_median": q(R["sz_fav_ask"], (50,))[0], "touch_size_cheap_ask_median": q(R["sz_cheap_ask"], (50,))[0],
                "touch_size_both_asks_median": q(np.concatenate([R["sz_yes_ask"].to_numpy(), R["sz_no_ask"].to_numpy()]), (50,))[0],
                "touch_size_both_asks_p25": q(np.concatenate([R["sz_yes_ask"].to_numpy(), R["sz_no_ask"].to_numpy()]), (25,))[0],
                "fee_at_mid_median": q(R["fee_mid"], (50,))[0], "fee_at_mid_p25_p75": q(R["fee_mid"], (25, 75)),
                "hold_cost_half_spread_plus_fee_median_p75": q(R["hold"]), "round_trip_spread_plus_two_fees_median_p75": q(R["rt"]),
                "round_trip_over_cheap_side_price_median": q(R["rt"] / (1 - R["favpx"]).clip(lower=0.005), (50,))[0],
                "round_trip_over_favourite_price_median": q(R["rt"] / R["favpx"], (50,))[0],
            })
            HC = pd.DataFrame(hc)
            hair = {}
            for nm, G in (("both_sides", HC), ("cheap_side_ask_le_50c", HC[HC["cheap"]]), ("favourite_side_ask_gt_50c", HC[~HC["cheap"]]),
                          ("check_favourite_ask_88_97c", HC[(HC["a0"] >= 0.88 - EPS) & (HC["a0"] <= 0.97 + EPS)]),
                          ("check_cheap_ask_05_30c", HC[(HC["a0"] >= 0.05 - EPS) & (HC["a0"] <= 0.30 + EPS)])):
                if len(G) == 0:
                    continue
                o = {"buys": int(len(G)), "windows": int(G["w"].nunique())}
                for H in HS:
                    if "L0_%d" % H not in G:
                        continue
                    gg = G[G["L0_%d" % H].notna()]
                    o["h%d" % H] = {"buys_with_later_two_sided_poll": int(len(gg)), "median_lag_s": round(float(gg["lag_%d" % H].median()), 2) if len(gg) else None,
                                     "filled_at_ask_seen": cl_share(gg["L0_%d" % H], gg["w"]), "filled_at_ask_plus_1c": cl_share(gg["L1_%d" % H], gg["w"]),
                                     "filled_at_ask_seen_size_ge_1": round(float(gg["L0sz_%d" % H].mean()), 4) if len(gg) else None,
                                     "filled_at_ask_plus_1c_size_ge_1": round(float(gg["L1sz_%d" % H].mean()), 4) if len(gg) else None}
                    if "S0_%d" % H in G:
                        gs = G[G["S0_%d" % H].notna()]
                        o["h%d" % H].update({"strict_buys_with_any_later_poll": int(len(gs)),
                                              "strict_filled_at_ask_seen": round(float(gs["S0_%d" % H].mean()), 4) if len(gs) else None,
                                              "strict_filled_at_ask_plus_1c": round(float(gs["S1_%d" % H].mean()), 4) if len(gs) else None})
                hair[nm] = o
            look["haircut"] = hair
        res["looks"][span_name] = look
    out["series"][s] = res

json.dump(out, open(OUT, "w"), indent=1, default=float)
for s, r in out["series"].items():
    e = r["events"]
    print(s, "markets", e["distinct_markets"], "vol_med", e["volume_contracts_median_per_window"], "res_share", e["result_present_at_post_close_read_share"])
    for ln, L in r["looks"].items():
        h = L.get("haircut", {}).get("both_sides", {})
        print("  ", ln, "inst", L["instants_all"], "two", L["share_two_sided"], "win", L["windows_with_two_sided"], "spr", L.get("spread_median_p75"), "sz", L.get("touch_size_both_asks_median"),
              "fee", L.get("fee_at_mid_median"), "hold", L.get("hold_cost_half_spread_plus_fee_median_p75"), "rt", L.get("round_trip_spread_plus_two_fees_median_p75"),
              "| h2", (h.get("h2000") or {}).get("filled_at_ask_seen"), (h.get("h2000") or {}).get("filled_at_ask_plus_1c"), "lag", (h.get("h2000") or {}).get("median_lag_s"),
              "| h6", (h.get("h6000") or {}).get("filled_at_ask_seen"), (h.get("h6000") or {}).get("filled_at_ask_plus_1c"), "lag", (h.get("h6000") or {}).get("median_lag_s"))
