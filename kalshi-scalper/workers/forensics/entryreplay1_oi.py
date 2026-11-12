"""ENTRYREPLAY1-OI: OICORE's model trigger windows against the same-week baseline, on the R6 books and tape.

Registration: ENTRYREPLAY1_OI_REGISTRATION.md (committed before anything was computed).
Part A reads no outcome (closes to Nov 11). Part B joins outcomes for closes BEFORE 2026-11-05 only.
Public recorded data and a public-data trigger list only. No network, no account data.

usage: python3 -I entryreplay1_oi.py <r6_root> <trigger_csv> <out_json>
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import r6load as R

ROOT, TRIG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SERIES = "KXBTC15M"
FROM, BEFORE = pd.Timestamp("2026-10-29T22:15:00Z"), pd.Timestamp("2026-11-12T00:00:00Z")
OUTCOME_BEFORE = pd.Timestamp("2026-11-05T00:00:00Z")
LOOK_S, LOOK_TOL_S, BAND, QTY, CANCEL_S = 178, 10, (0.08, 0.50), 10, 60
DELAYS = (2, 6, 10)
EPS = 1e-9
rng = np.random.default_rng(20261112)

trig = set(pd.read_csv(TRIG, comment="#")["ticker"])
parts = []
for d in R.run_dirs(ROOT):
    f = os.path.join(d, "coverage.csv.gz")
    if os.path.exists(f):
        c = pd.read_csv(f, dtype={"ticker": str, "result": str}, usecols=["close_time", "series", "ticker", "max_gap_ms", "result"])
        c = c[c["ticker"].notna() & (c["series"] == SERIES)].copy()
        c["close_ts"] = pd.to_datetime(c["close_time"], utc=True)
        c.loc[c["close_ts"] >= OUTCOME_BEFORE, "result"] = ""          # blanked on the close time before anything is computed
        parts.append(c)
c = pd.concat(parts, ignore_index=True)
c["result"] = c["result"].fillna("").str.lower()
cov = c.groupby("ticker").agg(close_ts=("close_ts", "first"), max_gap_ms=("max_gap_ms", "max"),
                              result=("result", lambda s: next((x for x in s if x in ("yes", "no")), "")))
cov = cov[(cov["close_ts"] >= FROM) & (cov["close_ts"] < BEFORE) & (cov["max_gap_ms"] <= 15000)]
cov["close_ms"] = ((cov["close_ts"] - R.EPOCH) / pd.Timedelta(milliseconds=1)).astype("int64")
close_ms = cov["close_ms"].to_dict()
books = R.load_books(ROOT, cov.index, min_left_s=0, max_left_s=200, close_ms=close_ms)
tape = R.load_trades(ROOT, cov.index, close_ms, CANCEL_S, LOOK_S + 2)
tape_by = {tk: g for tk, g in tape.groupby("ticker", sort=False)}

rows = []
for tk, g in books.groupby("ticker", sort=False):
    T = close_ms[tk]
    t = g["t_recv_ms"].to_numpy()
    yb = g[R.PX[:5]].to_numpy(float); nb = g[R.PX[5:]].to_numpy(float)
    ybs = np.nan_to_num(g[R.SZ[:5]].to_numpy(float)); nbs = np.nan_to_num(g[R.SZ[5:]].to_numpy(float))
    usable = (yb[:, 0] == yb[:, 0]) & (nb[:, 0] == nb[:, 0]) & (yb[:, 0] < 1 - nb[:, 0] - EPS) & (t < T)
    cand = np.flatnonzero(usable & (t >= T - LOOK_S * 1000) & (t <= T - (LOOK_S - LOOK_TOL_S) * 1000))
    if len(cand) == 0:
        continue
    i0 = cand[0]
    ay, an = 1 - nb[i0, 0], 1 - yb[i0, 0]
    if abs(ay - an) < EPS:
        continue
    yes = ay < an
    a0 = float(min(ay, an))
    if not (BAND[0] - EPS <= a0 <= BAND[1] + EPS):
        continue
    apx, asz = (1 - nb, nbs) if yes else (1 - yb, ybs)          # our side's ask ladder
    bpx, bsz = (yb, ybs) if yes else (nb, nbs)                  # our side's bid ladder
    row = {"ticker": tk, "close_ms": T, "trigger": tk in trig, "a0": a0, "spread": float(a0 - bpx[i0, 0]),
           "dev": bool(cov.at[tk, "close_ts"] < OUTCOME_BEFORE), "result": cov.at[tk, "result"], "yes": bool(yes)}

    def first_at(ms):
        k = np.flatnonzero(usable & (t >= t[i0] + ms))
        return int(k[0]) if len(k) and t[k[0]] <= t[i0] + ms + 4000 else None
    for d in DELAYS:
        j = first_at(d * 1000)
        for nm, slip in (("L0", 0.0), ("L1", 0.01)):
            if j is None:
                continue
            ok = apx[j] <= a0 + slip + EPS
            got = cost = 0.0
            for p, s in zip(apx[j][ok], asz[j][ok]):
                q = min(QTY - got, s)
                if q <= 0:
                    break
                got += q; cost += q * p
            row["fill_%s_%d" % (nm, d)] = float(got >= QTY - 1e-6)
            if got > 0:
                row["px_%s_%d" % (nm, d)] = cost / got
    j30 = first_at(30000)
    if j30 is not None:
        row["mid30"] = float((bpx[j30, 0] + apx[j30, 0]) / 2 - (bpx[i0, 0] + a0) / 2)
    j = first_at(1000)
    if j is not None and t[j] < T - CANCEL_S * 1000:
        P = float(bpx[j, 0]); Q0 = float(bsz[j, 0])
        tr = tape_by.get(tk); vol_at = 0.0; through = False
        if tr is not None:
            x = tr[(tr["ms"] > t[j]) & (tr["ms"] < T - CANCEL_S * 1000)]
            yp = x["yes_price_dollars"].to_numpy(float); cnt = x["count_fp"].to_numpy(float); sd = x["taker_outcome_side"].to_numpy()
            if yes:
                hit = sd == "no"; at = hit & (np.abs(yp - P) < 1e-6); thru = hit & (yp < P - 1e-6)
            else:
                hit = sd == "yes"; at = hit & (np.abs(yp - (1 - P)) < 1e-6); thru = hit & (yp > (1 - P) + 1e-6)
            vol_at = float(cnt[at].sum()); through = bool(thru.any())
        row.update({"m_px": P, "m_fill": float(QTY if through else min(QTY, max(0.0, vol_at - Q0))) / QTY, "m_through": through})
    rows.append(row)
W = pd.DataFrame(rows)


def cl(v, w):
    v = np.asarray(v, float); w = np.asarray(w); ok = v == v
    v, w = v[ok], w[ok]
    if len(v) == 0:
        return None
    pick = rng.integers(0, len(v), (2000, len(v)))
    bs = v[pick].mean(1)
    return [round(float(v.mean()), 5), round(float(np.percentile(bs, 2.5)), 5), round(float(np.percentile(bs, 97.5)), 5)]


def pf_ci(p):
    p = np.asarray(p, float)
    if len(p) == 0:
        return None
    pick = rng.integers(0, len(p), (2000, len(p)))
    bs = [R.pf(p[i]) for i in pick]
    bs = [x for x in bs if x == x and abs(x) != float("inf")]
    return [round(R.pf(p), 3), round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)] if bs else [round(R.pf(p), 3), None, None]


def part_a(G):
    o = {"windows": int(len(G)), "mean_ask": round(float(G["a0"].mean()), 4), "mean_spread": round(float(G["spread"].mean()), 4)}
    for d in DELAYS:
        for nm, lab in (("L0", "ask_seen"), ("L1", "plus_1c")):
            f = G["fill_%s_%d" % (nm, d)]
            x = {"filled_in_full": cl(f, G["ticker"])}
            px = G.get("px_%s_%d" % (nm, d))
            if px is not None:
                m = f == 1
                x["paid_minus_a0"] = cl((px[m] - G["a0"][m]), G["ticker"][m])
            o["ioc_%s_%ds" % (lab, d)] = x
    M = G[G["m_px"].notna()]
    o["resting"] = {"orders": int(len(M)), "share_with_any_fill": cl((M["m_fill"] > 0).astype(float), M["ticker"]),
                    "share_filled_in_full": cl((M["m_fill"] >= 1 - 1e-9).astype(float), M["ticker"]),
                    "traded_through_share": cl(M["m_through"].astype(float), M["ticker"]),
                    "price_and_fee_saved_on_filled": cl((M["a0"] + R.fee(M["a0"]) - M["m_px"])[M["m_fill"] > 0], M["ticker"][M["m_fill"] > 0])}
    o["mid_move_30s"] = cl(G["mid30"], G["ticker"])
    return o


def part_b(G):
    G = G[G["dev"] & G["result"].isin(["yes", "no"])].copy()
    if len(G) == 0:
        return {"windows": 0}
    G["win"] = (G["result"] == np.where(G["yes"], "yes", "no")).astype(float)
    G["t0"] = G["win"] - G["a0"] - R.fee(G["a0"])
    o = {"windows": int(len(G)), "mean_ask": round(float(G["a0"].mean()), 4), "win_rate": round(float(G["win"].mean()), 4),
         "taker_T0_pf": pf_ci(G["t0"]), "taker_T0_mean": cl(G["t0"], G["ticker"])}
    M = G[G["m_px"].notna()]
    mk = (M["m_fill"] * (M["win"] - M["m_px"])).to_numpy()
    o["resting_pf"] = pf_ci(mk); o["resting_orders_filled"] = int((M["m_fill"] > 0).sum())
    o["paired_resting_minus_T0"] = cl(mk - M["t0"].to_numpy(), M["ticker"])
    return o, G


out = {"test": "ENTRYREPLAY1-OI", "note": "dollars per contract (0.01 = 1 cent); [value, 2.5%, 97.5%] by resampling windows",
       "counts": {"windows_in_band": int(len(W)), "trigger": int(W["trigger"].sum()), "other": int((~W["trigger"]).sum()),
                  "dev_windows_in_band": int(W["dev"].sum())}}
out["part_a_no_outcome"] = {"trigger": part_a(W[W["trigger"]]), "other": part_a(W[~W["trigger"]])}
bt, Gt = part_b(W[W["trigger"]]); bo, Go = part_b(W[~W["trigger"]])
a, b = Gt["t0"].to_numpy(), Go["t0"].to_numpy()
bs = [a[rng.integers(0, len(a), len(a))].mean() - b[rng.integers(0, len(b), len(b))].mean() for _ in range(4000)]
out["part_b_outcome_closes_before_nov5"] = {"trigger": bt, "other": bo,
                                            "trigger_minus_other_T0_mean": [round(float(a.mean() - b.mean()), 5), round(float(np.percentile(bs, 2.5)), 5), round(float(np.percentile(bs, 97.5)), 5)]}
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
