"""Task 5: taker cost for the hourly Bitcoin ladder (KXBTCD), from the recorded order book (quote-data book/).

Measurement only. No rule scored, no result read (this recorder stores none). No network.
usage: python3 -I ladder.py <data_root> <out_json> <date> [<date> ...]
  data_root/book/<date>/<HHMM>/{book,trades,coverage}.csv.gz
Same definitions as fifteen.py (two-sided instant, asks from the opposite bid, the haircut at the first two-sided poll
at least 2000 and 6000 ms later, tolerance 4000 ms). Each of the 7 recorded strikes is polled about every 3 s.
"""
import sys, os, glob, json
import numpy as np
import pandas as pd

ROOT, OUT, DATES = sys.argv[1], sys.argv[2], sys.argv[3:]
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
PXY = ["yes_bid_px_%d" % i for i in range(1, 6)]; PXN = ["no_bid_px_%d" % i for i in range(1, 6)]
SZY = ["yes_bid_sz_%d" % i for i in range(1, 6)]; SZN = ["no_bid_sz_%d" % i for i in range(1, 6)]
SPANS = {"look_30min_1830_1770s": (1770.0, 1830.0), "look_6min_400_330s": (330.0, 400.0)}
HS = (2000, 6000); TOL = 4000; EPS = 1e-9
rng = np.random.default_rng(20261112)
fee = lambda p: 0.07 * p * (1.0 - p)


def q(v, qs=(50, 75)):
    v = np.asarray(v, float); v = v[v == v]
    return [round(float(x), 5) for x in np.percentile(v, qs)] if len(v) else None


def cl_share(flag, w):
    flag = np.asarray(flag, float); w = np.asarray(w)
    if len(flag) == 0:
        return None
    u, inv = np.unique(w, return_inverse=True)
    num = np.bincount(inv, flag); den = np.bincount(inv, np.ones(len(flag)))
    pick = rng.integers(0, len(u), (1000, len(u)))
    bs = num[pick].sum(1) / np.maximum(den[pick].sum(1), 1e-12)
    return [round(float(num.sum() / den.sum()), 4), round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)]


dirs = sorted(d for dt in DATES for d in glob.glob(os.path.join(ROOT, "book", dt, "*")) if os.path.isdir(d))
bp, tp, cp = [], [], []
for d in dirs:
    f = os.path.join(d, "book.csv.gz")
    if os.path.exists(f) and os.path.getsize(f) > 0:
        b = pd.read_csv(f, usecols=["poll_ts_local_ms", "ticker", "strike", "close_time"] + PXY + SZY + PXN + SZN)
        b["close_ms"] = ((pd.to_datetime(b["close_time"], utc=True) - EPOCH) / pd.Timedelta(milliseconds=1)).astype("int64")
        left = (b["close_ms"] - b["poll_ts_local_ms"]) / 1000.0
        bp.append(b[((left <= 1840) & (left >= 1750)) | ((left <= 410) & (left >= 310))])
    f = os.path.join(d, "trades.csv.gz")
    if os.path.exists(f) and os.path.getsize(f) > 0:
        tp.append(pd.read_csv(f, usecols=["ticker", "created_time", "count_fp", "trade_id"], dtype={"trade_id": str}))
    f = os.path.join(d, "coverage.csv.gz")
    if os.path.exists(f) and os.path.getsize(f) > 0:
        cp.append(pd.read_csv(f))
books = pd.concat(bp, ignore_index=True).drop_duplicates(subset=["ticker", "poll_ts_local_ms"]).sort_values(["ticker", "poll_ts_local_ms"]).reset_index(drop=True)
books["event"] = books["ticker"].str.rsplit("-", n=1).str[0]
cov = pd.concat(cp, ignore_index=True).drop_duplicates(subset=["close_time"])
tr = pd.concat(tp, ignore_index=True).drop_duplicates(subset=["trade_id"])
tr["event"] = tr["ticker"].str.rsplit("-", n=1).str[0]
vol_tk = tr.groupby("ticker")["count_fp"].sum(); vol_ev = tr.groupby("event")["count_fp"].sum()

out = {"label": "hourly Bitcoin ladder KXBTCD", "dates": DATES, "run_dirs": [os.path.relpath(d, ROOT) for d in dirs],
       "note": "dollars (0.01 = 1 cent); no result column exists in this recorder; volume is the tape of the 7 recorded strikes over the recorded 55 minutes only",
       "events": {"hourly_closes_in_coverage": int(len(cov)), "closes_per_date": {k: int(v) for k, v in pd.to_datetime(cov["close_time"], utc=True).dt.strftime("%Y-%m-%d %a").value_counts().sort_index().items()},
                  "strikes_recorded_per_close_median": q(cov["tickers"], (50,))[0], "settlement_delay": "not recorded",
                  "tape_contracts_per_strike_55min_median_p25_p75": q(vol_tk, (50, 25, 75)), "tape_strikes_n": int(len(vol_tk)),
                  "tape_contracts_per_event_7_strikes_55min_median_p25_p75": q(vol_ev, (50, 25, 75)), "tape_events_n": int(len(vol_ev))},
       "looks": {}}

for span_name, (lo, hi) in SPANS.items():
    rows, hc = [], []
    n_all = n_two = n_yo = n_no = n_e = n_x = 0
    tk_all, tk_two, ev_two = set(), set(), set()
    for tk, gb in books.groupby("ticker", sort=False):
        t = gb["poll_ts_local_ms"].to_numpy(); T = int(gb["close_ms"].iloc[0]); ev = gb["event"].iloc[0]
        left = (T - t) / 1000.0
        yb = gb[PXY].to_numpy(float); nb = gb[PXN].to_numpy(float)
        ybs = np.nan_to_num(gb[SZY].to_numpy(float)); nbs = np.nan_to_num(gb[SZN].to_numpy(float))
        hy = yb[:, 0] == yb[:, 0]; hn = nb[:, 0] == nb[:, 0]
        usable = hy & hn & (yb[:, 0] < 1 - nb[:, 0] - EPS)
        insp = (left >= lo) & (left <= hi)
        if not insp.any():
            continue
        tk_all.add(tk)
        n_all += int(insp.sum()); n_two += int((insp & usable).sum()); n_yo += int((insp & hy & ~hn).sum()); n_no += int((insp & ~hy & hn).sum())
        n_e += int((insp & ~hy & ~hn).sum()); n_x += int((insp & hy & hn & ~usable).sum())
        uidx = np.flatnonzero(usable); ut = t[uidx]
        ask_y = 1 - nb; ask_n = 1 - yb
        for i in np.flatnonzero(insp & usable):
            tk_two.add(tk); ev_two.add(ev)
            ya, na, ybid = ask_y[i, 0], ask_n[i, 0], yb[i, 0]
            spread = ya - ybid; mid = (ya + ybid) / 2
            rows.append((ev, tk, spread, mid, max(mid, 1 - mid), nbs[i, 0], ybs[i, 0], spread / 2 + fee(mid), spread + fee(ya) + fee(ybid), fee(mid)))
            for side, a0, px, sz in (("yes", ya, ask_y, nbs), ("no", na, ask_n, ybs)):
                rec = {"w": ev, "side": side, "a0": float(a0), "mid": float(mid)}
                for H in HS:
                    k = np.searchsorted(ut, t[i] + H, side="left")
                    if k < len(uidx) and ut[k] <= t[i] + H + TOL and left[uidx[k]] > 0:
                        j = int(uidx[k])
                        rec["lag_%d" % H] = (t[j] - t[i]) / 1000.0
                        rec["L0_%d" % H] = float(px[j, 0] <= a0 + EPS); rec["L1_%d" % H] = float(px[j, 0] <= a0 + 0.01 + EPS)
                hc.append(rec)
    look = {"instants_all": n_all, "instants_two_sided": n_two, "share_two_sided": round(n_two / n_all, 4) if n_all else None,
            "instants_yes_bids_only": n_yo, "instants_no_bids_only": n_no, "instants_empty_book": n_e, "instants_crossed_or_locked": n_x,
            "strike_markets_with_any_poll": len(tk_all), "strike_markets_two_sided": len(tk_two), "hourly_events_two_sided": len(ev_two)}
    if rows:
        R = pd.DataFrame(rows, columns=["ev", "tk", "spread", "mid", "favpx", "sz_yes_ask", "sz_no_ask", "hold", "rt", "fee_mid"])

        def block(G):
            both = np.concatenate([G["sz_yes_ask"].to_numpy(), G["sz_no_ask"].to_numpy()])
            return {"instants": int(len(G)), "strike_markets": int(G["tk"].nunique()), "events": int(G["ev"].nunique()),
                    "spread_median_p75": q(G["spread"]), "spread_mean": round(float(G["spread"].mean()), 5), "mid_median": q(G["mid"], (50,))[0],
                    "favourite_price_median_p25_p75": q(G["favpx"], (50, 25, 75)), "touch_size_both_asks_median": q(both, (50,))[0], "touch_size_both_asks_p25": q(both, (25,))[0],
                    "fee_at_mid_median": q(G["fee_mid"], (50,))[0], "hold_cost_half_spread_plus_fee_median_p75": q(G["hold"]),
                    "round_trip_spread_plus_two_fees_median_p75": q(G["rt"]),
                    "round_trip_over_cheap_side_price_median": q(G["rt"] / (1 - G["favpx"]).clip(lower=0.005), (50,))[0]}
        look["all_recorded_strikes"] = block(R)
        look["near_money_mid_30_70c"] = block(R[(R["mid"] >= 0.30) & (R["mid"] <= 0.70)]) if ((R["mid"] >= 0.30) & (R["mid"] <= 0.70)).any() else None
        look["wings_mid_outside_30_70c"] = block(R[(R["mid"] < 0.30) | (R["mid"] > 0.70)]) if ((R["mid"] < 0.30) | (R["mid"] > 0.70)).any() else None
        HC = pd.DataFrame(hc); hair = {}
        for nm, G in (("both_sides_all_strikes", HC), ("both_sides_near_money_mid_30_70c", HC[(HC["mid"] >= 0.30) & (HC["mid"] <= 0.70)]),
                      ("cheap_side_ask_le_50c", HC[HC["a0"] <= 0.5 + EPS]), ("favourite_side_ask_gt_50c", HC[HC["a0"] > 0.5 + EPS])):
            if len(G) == 0:
                continue
            o = {"buys": int(len(G)), "events": int(G["w"].nunique())}
            for H in HS:
                gg = G[G["L0_%d" % H].notna()] if "L0_%d" % H in G else G.iloc[0:0]
                o["h%d" % H] = {"buys_with_later_two_sided_poll": int(len(gg)), "median_lag_s": round(float(gg["lag_%d" % H].median()), 2) if len(gg) else None,
                                 "filled_at_ask_seen": cl_share(gg["L0_%d" % H], gg["w"]) if len(gg) else None,
                                 "filled_at_ask_plus_1c": cl_share(gg["L1_%d" % H], gg["w"]) if len(gg) else None}
            hair[nm] = o
        look["haircut"] = hair
    out["looks"][span_name] = look
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float)[:6000])
