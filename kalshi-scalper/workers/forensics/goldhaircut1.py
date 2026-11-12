"""GOLDHAIRCUT1: the fill haircut for the gold 15 minute market at the favourite look (FILLHAIRCUT1 with gold constants).

Registration: GOLDHAIRCUT1_REGISTRATION.md (committed before anything was computed).
A measurement: no rule is scored, no settlement result is loaded, zero tries.
Public recorded market data only (R6 books and tape). No network, no account data.

usage: python3 -I goldhaircut1.py <data_root> <out_json> [A|B|AB]
"""
import sys, os, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import r6load as R

ROOT, OUT = sys.argv[1], sys.argv[2]
SERIES = "KXGOLD15M"
# Period constants (registration and Amendment 1): A = closes Oct 29 to Nov 8; B = closes Nov 9 to Nov 11; AB = both.
PERIODS = {"A": ("2026-10-29T00:00:00Z", "2026-11-09T00:00:00Z"), "B": ("2026-11-09T00:00:00Z", "2026-11-12T00:00:00Z"),
           "AB": ("2026-10-29T00:00:00Z", "2026-11-12T00:00:00Z")}
PERIOD = sys.argv[3] if len(sys.argv) > 3 else "A"
FROM, BEFORE = (pd.Timestamp(x) for x in PERIODS[PERIOD])
SPAN = (330.0, 400.0)                 # seconds before the close
BAND = (0.88, 0.97)
QBIG = 15
BUCKETS = [("88-91c", 0.88, 0.91), ("91-94c", 0.91, 0.94), ("94-97c", 0.94, 0.97 + 1e-6)]
HS = (1, 2, 5, 10)
EPS = 1e-9
rng = np.random.default_rng(20261112)

# coverage without the result column
parts = []
for d in R.run_dirs(ROOT):
    f = os.path.join(d, "coverage.csv.gz")
    if os.path.exists(f):
        c = pd.read_csv(f, dtype={"ticker": str}, usecols=["close_time", "series", "ticker", "max_gap_ms"])
        parts.append(c[c["ticker"].notna() & (c["series"] == SERIES)])
cov = pd.concat(parts, ignore_index=True)
cov["close_ts"] = pd.to_datetime(cov["close_time"], utc=True)
cov = cov.groupby("ticker").agg(close_ts=("close_ts", "first"), max_gap_ms=("max_gap_ms", "max"))
cov = cov[(cov["close_ts"] >= FROM) & (cov["close_ts"] < BEFORE)]
n_listed = len(cov)
cov = cov[cov["max_gap_ms"] <= 15000]
cov["close_ms"] = ((cov["close_ts"] - R.EPOCH) / pd.Timedelta(milliseconds=1)).astype("int64")
close_ms = cov["close_ms"].to_dict()
books = R.load_books(ROOT, cov.index, min_left_s=290, max_left_s=406, close_ms=close_ms)
tape = R.load_trades(ROOT, cov.index, close_ms, 316, 402)
tape_by = {tk: g for tk, g in tape.groupby("ticker", sort=False)}

inst, trd = [], []          # one dict per decision instant; one per taker trade
wid = 0
for tk, g in books.groupby("ticker", sort=False):
    wid += 1
    T = close_ms[tk]
    t = g["t_recv_ms"].to_numpy()
    yb = g[R.PX[:5]].to_numpy(float); nb = g[R.PX[5:]].to_numpy(float)
    ybs = np.nan_to_num(g[R.SZ[:5]].to_numpy(float)); nbs = np.nan_to_num(g[R.SZ[5:]].to_numpy(float))
    usable = (yb[:, 0] == yb[:, 0]) & (nb[:, 0] == nb[:, 0]) & (yb[:, 0] < 1 - nb[:, 0] - EPS)
    uidx = np.flatnonzero(usable); ut = t[uidx]
    if len(uidx) == 0:
        continue
    left = (T - t) / 1000.0
    ask_y, ask_n = 1 - nb, 1 - yb                         # ask ladders (level k of YES ask = 1 - NO bid k)
    cheap_yes = (ask_y[:, 0] >= BAND[0] - EPS) & (ask_y[:, 0] <= BAND[1] + EPS)      # here "cheap" means the chosen side: the favourite in the band
    cheap_no = ~cheap_yes & (ask_n[:, 0] >= BAND[0] - EPS) & (ask_n[:, 0] <= BAND[1] + EPS)
    a0_all = np.where(cheap_yes, ask_y[:, 0], np.where(cheap_no, ask_n[:, 0], np.nan))
    tr = tape_by.get(tk)
    if tr is not None:
        tms = tr["ms"].to_numpy(); typ = tr["yes_price_dollars"].to_numpy(float); tc = tr["count_fp"].to_numpy(float)
        tyes = (tr["taker_outcome_side"].to_numpy() == "yes")
    else:
        tms = np.array([], dtype="int64"); typ = tc = np.array([]); tyes = np.array([], dtype=bool)

    def first_at(ms, tol_ms):
        k = np.searchsorted(ut, ms, side="left")
        return int(uidx[k]) if k < len(uidx) and ut[k] <= ms + tol_ms else None

    def ladder(j, yes_side):
        return (ask_y[j], nbs[j]) if yes_side else (ask_n[j], ybs[j])

    for i in uidx:
        if not (SPAN[0] <= left[i] <= SPAN[1]):
            continue
        a0 = a0_all[i]
        if not (a0 == a0) or not (BAND[0] - EPS <= a0 <= BAND[1] + EPS):
            continue
        ys = bool(cheap_yes[i])
        px0, sz0 = ladder(i, ys)
        bid0 = (yb if ys else nb)[i, 0]
        row = {"w": wid, "a0": float(a0), "spread": float(a0 - bid0), "sz_touch": float(sz0[0]),
               "sz_le_a0": float(sz0[px0 <= a0 + EPS].sum())}
        # the cheaper side's taker buys after this poll: taker bought our side at or below a0
        if len(tms):
            paid = typ if ys else 1 - typ
            mine = (tyes == ys) & (tms > t[i]) & (paid <= a0 + 1e-6)
        for h in HS:
            j = first_at(t[i] + h * 1000, 4000)
            if j is None or left[j] < SPAN[0] - 20:
                continue
            pxh, szh = ladder(j, ys)
            row["ask_%d" % h] = float(pxh[0])
            row["szle_%d" % h] = float(szh[pxh <= a0 + EPS].sum())
            row["lag_%d" % h] = (t[j] - t[i]) / 1000.0
            for lim_name, lim in (("L0", a0), ("L1", a0 + 0.01)):
                ok = pxh <= lim + EPS
                avail = szh[ok]; apx = pxh[ok]
                for Q in (1, QBIG):
                    got = 0.0; cost = 0.0
                    for p, s in zip(apx, avail):
                        q = min(Q - got, s)
                        if q <= 0:
                            break
                        got += q; cost += q * p
                    row["fill_%s_Q%d_d%d" % (lim_name, Q, h)] = got / Q
                    if got > 0:
                        row["px_%s_Q%d_d%d" % (lim_name, Q, h)] = cost / got
            if len(tms):
                row["taken_%d" % h] = float(tc[mine & (tms <= t[i] + h * 1000)].sum())
        j30 = first_at(t[i] + 30000, 4000)
        if j30 is not None:
            ysb = yb if ys else nb
            mid0 = (bid0 + a0) / 2
            row["mid30"] = float((ysb[j30, 0] + (ask_y if ys else ask_n)[j30, 0]) / 2 - mid0)
        inst.append(row)

    # Part 2: taker buys of the cheaper side, against the ask at least 2 s earlier
    if len(tms):
        tl = (T - tms) / 1000.0
        inspan = (tl >= SPAN[0]) & (tl <= SPAN[1])
        k = np.searchsorted(ut, tms - 2000, side="right") - 1
        okref = inspan & (k >= 0)
        kk = np.clip(k, 0, len(uidx) - 1); ri = uidx[kk]
        okref &= (tms - t[ri] <= 6000)
        a_ref = a0_all[ri]; ys_ref = cheap_yes[ri]
        okref &= (a_ref == a_ref) & (a_ref >= BAND[0] - EPS) & (a_ref <= BAND[1] + EPS) & (tyes == ys_ref)
        paid = np.where(ys_ref, typ, 1 - typ)
        for a, p, c in zip(a_ref[okref], paid[okref], tc[okref]):
            trd.append((wid, float(a), float(p - a), float(c)))

I = pd.DataFrame(inst)
TR = pd.DataFrame(trd, columns=["w", "a_ref", "slip", "count"])


def cl_mean(v, w, wt=None):
    """[mean, lo, hi] with a 95% interval from resampling whole windows; v may hold NaN (dropped)."""
    v = np.asarray(v, float); w = np.asarray(w)
    wt = np.ones(len(v)) if wt is None else np.asarray(wt, float)
    ok = v == v
    v, w, wt = v[ok], w[ok], wt[ok]
    if len(v) == 0:
        return None
    u, inv = np.unique(w, return_inverse=True)
    num = np.bincount(inv, v * wt); den = np.bincount(inv, wt)
    pick = rng.integers(0, len(u), (2000, len(u)))
    bs = num[pick].sum(1) / np.maximum(den[pick].sum(1), 1e-12)
    return [round(float(num.sum() / den.sum()), 4), round(float(np.percentile(bs, 2.5)), 4), round(float(np.percentile(bs, 97.5)), 4)]


def pct(v, qs=(50, 75, 90, 95)):
    v = np.asarray(v, float); v = v[v == v]
    return [round(float(x), 4) for x in np.percentile(v, qs)] if len(v) else None


def part1(G):
    o = {}
    for h in HS:
        a = G["ask_%d" % h]; ok = a.notna()
        g = G[ok]; mv = (g["ask_%d" % h] - g["a0"]).to_numpy()
        still = (mv <= EPS)
        gone = g[~still]
        o["h%d" % h] = {
            "instants": int(len(g)), "median_lag_s": round(float(g["lag_%d" % h].median()), 2) if len(g) else None,
            "ask_still_at_or_below_a0": cl_mean(still.astype(float), g["w"]),
            "ask_at_or_below_a0_plus_1c": cl_mean((mv <= 0.01 + EPS).astype(float), g["w"]),
            "size_le_a0_median_then": round(float(g["szle_%d" % h].median()), 1) if len(g) else None,
            "share_size_ge_1": cl_mean((g["szle_%d" % h] >= 1 - EPS).astype(float), g["w"]),
            "share_size_ge_15": cl_mean((g["szle_%d" % h] >= QBIG - EPS).astype(float), g["w"]),
            "ask_move_mean": cl_mean(mv, g["w"]), "ask_move_pct_50_75_90_95": pct(mv),
            "when_gone_move_mean": cl_mean((gone["ask_%d" % h] - gone["a0"]).to_numpy(), gone["w"]) if len(gone) else None,
            "when_gone_move_pct_50_75_90_95": pct((gone["ask_%d" % h] - gone["a0"]).to_numpy()) if len(gone) else None,
        }
    return o


def part2_share(G):
    o = {}
    for h in HS:
        if "taken_%d" % h not in G:
            continue
        g = G[G["taken_%d" % h].notna() & (G["sz_le_a0"] > 0)]
        r = (g["taken_%d" % h] / g["sz_le_a0"]).to_numpy()
        o["h%d" % h] = {"instants": int(len(g)), "share_with_any_take": cl_mean((r > 0).astype(float), g["w"]),
                         "ratio_median": round(float(np.median(r)), 4) if len(r) else None, "ratio_p90": round(float(np.percentile(r, 90)), 4) if len(r) else None,
                         "share_ratio_ge_1": cl_mean((r >= 1 - EPS).astype(float), g["w"])}
    return o


def part3(G):
    o = {}
    for lim in ("L0", "L1"):
        for Q in (1, QBIG):
            for d in HS:
                fc, pc = "fill_%s_Q%d_d%d" % (lim, Q, d), "px_%s_Q%d_d%d" % (lim, Q, d)
                if fc not in G:
                    continue
                g = G[G[fc].notna()]
                full = (g[fc] >= 1 - 1e-6)
                x = {"instants": int(len(g)), "filled_in_full": cl_mean(full.astype(float), g["w"]), "filled_at_all": cl_mean((g[fc] > 0).astype(float), g["w"])}
                if pc in g and g[pc].notna().any():
                    gf = g[g[pc].notna()]
                    x["paid_minus_a0_on_filled"] = cl_mean((gf[pc] - gf["a0"]).to_numpy(), gf["w"], gf[fc].to_numpy())
                if "mid30" in g:
                    x["mid_move_30s_if_full"] = cl_mean(g.loc[full, "mid30"].to_numpy(), g.loc[full, "w"])
                    x["mid_move_30s_if_not_full"] = cl_mean(g.loc[~full, "mid30"].to_numpy(), g.loc[~full, "w"]) if (~full).any() else None
                o["%s_Q%d_d%d" % ({"L0": "limit_a0", "L1": "limit_a0_plus_1c", "L2": "limit_a0_plus_2c"}[lim], Q, d)] = x
    return o


def part2_slip(X):
    def one(x):
        if len(x) == 0:
            return {"trades": 0}
        s = x["slip"].to_numpy(); c = x["count"].to_numpy()
        return {"trades": int(len(x)), "windows": int(x["w"].nunique()), "contracts": round(float(c.sum()), 1),
                "slip_mean_per_trade": cl_mean(s, x["w"]), "slip_mean_per_contract": cl_mean(s, x["w"], c),
                "slip_pct_50_75_90_95": pct(s), "share_paid_above_ref_ask": cl_mean((s > 1e-6).astype(float), x["w"]),
                "share_paid_below_ref_ask": cl_mean((s < -1e-6).astype(float), x["w"]),
                "share_paid_more_than_1c_above": cl_mean((s > 0.01 + 1e-6).astype(float), x["w"])}
    o = {"all": one(X)}
    for nm, lo, hi in (("under_2_contracts", 0, 2), ("2_to_under_20", 2, 20), ("20_or_more", 20, 1e18)):
        o[nm] = one(X[(X["count"] >= lo) & (X["count"] < hi)])
    return o


out = {"test": "GOLDHAIRCUT1", "period": PERIOD, "series": SERIES, "closes_from": str(FROM), "closes_before": str(BEFORE), "span_s_before_close": SPAN, "band": BAND,
       "note": "dollars per contract (0.01 = 1 cent); [value, 2.5%, 97.5%] by resampling whole windows; no settlement result loaded",
       "counts": {"windows_listed": int(n_listed), "windows_used": int(books["ticker"].nunique()), "instants": int(len(I)), "windows_with_instants": int(I["w"].nunique()),
                  "taker_trades": int(len(TR))}}
for nm, lo, hi in [("pooled", BAND[0] - EPS, BAND[1] + 1e-6)] + BUCKETS:
    G = I[(I["a0"] >= lo - EPS) & (I["a0"] < hi)]
    X = TR[(TR["a_ref"] >= lo - EPS) & (TR["a_ref"] < hi)]
    out[nm] = {"instants": int(len(G)), "windows": int(G["w"].nunique()),
               "at_instant": {"mean_ask": round(float(G["a0"].mean()), 4), "mean_spread": round(float(G["spread"].mean()), 4),
                              "size_at_touch_median": round(float(G["sz_touch"].median()), 1), "size_at_touch_p10": round(float(np.percentile(G["sz_touch"], 10)), 1),
                              "share_touch_size_ge_15": round(float((G["sz_touch"] >= QBIG).mean()), 4)},
               "part1_quote_survival": part1(G), "part2_taker_slippage": part2_slip(X), "part2_share_of_displayed_taken": part2_share(G), "part3_ioc": part3(G)}
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps(out["counts"]))
