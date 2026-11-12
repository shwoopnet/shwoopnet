"""EXITREPLAY1: the 25c early sell replayed on the recorded R6 books.

Registration: FORENSICS_REGISTRATION_NOV12.md (pushed before any recorded row was opened).
Public recorded market data only. The bot's own orders are not read or reconstructed.

usage: python3 -I exitreplay1.py <data_root> <block: D|H|POOLED> <out_json>
POOLED only re-reads blocks already read (it is the two periods side by side, no new data).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import r6load as R

ROOT, BLOCK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SERIES = ["KXGOLD15M", "KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M"]
LOOK_S, LOOK_TOL_S = 360, 10
BAND = (0.88, 0.97)
TRIG, SLIP = 0.25, 0.15
PHASES_MS = (0, 2000, 4000, 6000, 8000)
EPS = 1e-9

cov = R.load_coverage(ROOT, SERIES)
if BLOCK in ("D", "H"):
    cov = cov[cov["block"] == BLOCK]
counts = {"windows_listed": int(len(cov))}
cov_ok = cov[(cov["result"].isin(["yes", "no"])) & (cov["max_gap_ms"] <= 15000)]
counts["dropped_no_result"] = int((~cov["result"].isin(["yes", "no"])).sum())
counts["dropped_gap"] = int((cov["result"].isin(["yes", "no"]) & (cov["max_gap_ms"] > 15000)).sum())
close_ms = cov_ok["close_ms"].to_dict()
books = R.load_books(ROOT, cov_ok.index, min_left_s=0, max_left_s=900, close_ms=close_ms)


def sell_walk(px, sz, limit, qty):
    """Sell qty into bid levels (best first) at or above limit. Returns (contracts sold, proceeds, fee)."""
    sold = proceeds = fee = 0.0
    for p, s in zip(px, sz):
        if not (p == p) or not (s == s) or p < limit - EPS or p <= 0:
            continue
        q = min(qty - sold, s)
        if q <= 0:
            break
        sold += q; proceeds += q * p; fee += q * R.fee(p)
    return sold, proceeds, fee


def replay(t, bid_px, bid_sz, ask, usable, i_look, T, hold_val, qty, detect_times, need_ask=None):
    """Sale loop: at each detection time, read the last usable poll at or before it; if the bid is in (0, TRIG]
    (and, for V1, the ask at or below need_ask), sell what is left on the first usable poll at least 1 s later.
    Returns dict with detected bid (first detection), value per contract of the whole position, sold share, avg sale price."""
    left = float(qty); proceeds = fee = 0.0
    first_bid = None; first_det_t = None
    uidx = np.flatnonzero(usable)
    ut = t[uidx]
    for g in detect_times:
        if left <= EPS or g >= T:
            break
        k = np.searchsorted(ut, g, side="right") - 1
        if k < 0:
            continue
        i = uidx[k]
        if i <= i_look or g - t[i] > 10000:
            continue
        b = bid_px[i, 0]
        if not (b > 0 and b <= TRIG + EPS):
            continue
        if need_ask is not None and not (ask[i] <= need_ask + EPS):
            continue
        if first_bid is None:
            first_bid, first_det_t = float(b), int(t[i])
        k2 = np.searchsorted(ut, t[i] + 1000, side="left")
        if k2 >= len(uidx) or ut[k2] >= T:
            continue
        j = uidx[k2]
        s, pr, fe = sell_walk(bid_px[j], bid_sz[j], max(0.01, b - SLIP), left)
        left -= s; proceeds += pr; fee += fe
    sold = qty - left
    value = (proceeds - fee + left * hold_val) / qty
    return {"det_bid": first_bid, "det_t": first_det_t, "sold_share": sold / qty, "avg_sale": (proceeds / sold) if sold > 0 else None,
            "value": value, "fee_pc": (fee / sold) if sold > 0 else None}


rows, events = [], []
no_look = 0
for tk, g in books.groupby("ticker", sort=False):
    T = close_ms[tk]; res = cov_ok.at[tk, "result"]; series = cov_ok.at[tk, "series"]; block = cov_ok.at[tk, "block"]
    t = g["t_recv_ms"].to_numpy()
    yb = g[R.PX[:5]].to_numpy(float); nb = g[R.PX[5:]].to_numpy(float)
    ybs = g[R.SZ[:5]].to_numpy(float); nbs = g[R.SZ[5:]].to_numpy(float)
    usable = (yb[:, 0] == yb[:, 0]) & (nb[:, 0] == nb[:, 0]) & (yb[:, 0] < 1 - nb[:, 0] - EPS) & (t < T)
    cand = np.flatnonzero(usable & (t <= T - LOOK_S * 1000) & (t >= T - (LOOK_S + LOOK_TOL_S) * 1000))
    if len(cand) == 0:
        no_look += 1
        continue
    i0 = cand[-1]
    ask_yes, ask_no = 1 - nb[i0, 0], 1 - yb[i0, 0]
    if BAND[0] - EPS <= ask_yes <= BAND[1] + EPS:
        side = "yes"
    elif BAND[0] - EPS <= ask_no <= BAND[1] + EPS:
        side = "no"
    else:
        rows.append({"ticker": tk, "series": series, "block": block, "close_ms": T, "entry": False})
        continue
    bid_px, bid_sz = (yb, ybs) if side == "yes" else (nb, nbs)
    other = nb if side == "yes" else yb
    ask = 1 - other[:, 0]
    entry_ask = float(ask[i0])
    hold_val = 1.0 if res == side else 0.0
    cost = entry_ask + R.fee(entry_ask)
    after = np.flatnonzero(usable & (np.arange(len(t)) > i0))
    trig_i = next((i for i in after if 0 < bid_px[i, 0] <= TRIG + EPS), None)
    row = {"ticker": tk, "series": series, "block": block, "close_ms": T, "entry": True, "side": side, "entry_ask": entry_ask,
           "cost": cost, "hold_val": hold_val, "trigger": trig_i is not None}
    grid0 = int(t[0])
    live15, live1, v1 = [], [], []
    for ph in PHASES_MS:
        first = grid0 + ph
        k0 = max(0, int(np.ceil((t[i0] - first) / 10000.0)))
        times = [first + 10000 * k for k in range(k0, k0 + 95)]
        live15.append(replay(t, bid_px, bid_sz, ask, usable, i0, T, hold_val, 15, times))
        live1.append(replay(t, bid_px, bid_sz, ask, usable, i0, T, hold_val, 1, times))
        v1.append(replay(t, bid_px, bid_sz, ask, usable, i0, T, hold_val, 15, times, need_ask=0.35))
    row["val_live15"] = float(np.mean([r["value"] for r in live15]))
    row["val_live1"] = float(np.mean([r["value"] for r in live1]))
    row["val_v1"] = float(np.mean([r["value"] for r in v1]))
    if trig_i is not None:
        tt = int(t[trig_i])
        inst_times = [int(x) for x in t[after] if x >= tt]
        inst15 = replay(t, bid_px, bid_sz, ask, usable, i0, T, hold_val, 15, inst_times)
        inst1 = replay(t, bid_px, bid_sz, ask, usable, i0, T, hold_val, 1, inst_times)
        row["val_inst15"] = inst15["value"]

        def later(ms):
            k = [i for i in after if t[i] >= tt + ms]
            return k[0] if k else None
        i10, i30, i2 = later(10000), later(30000), later(2000)
        det = [r for r in live15 if r["det_bid"] is not None]
        sold = [r for r in live15 if r["avg_sale"] is not None]
        ev = {"ticker": tk, "series": series, "block": block, "close_ms": T, "side": side, "entry_ask": entry_ask, "hold_val": hold_val,
              "left_s": (T - tt) / 1000.0, "trig_bid": float(bid_px[trig_i, 0]), "trig_ask": float(ask[trig_i]),
              "pulled": bool(ask[trig_i] >= 0.40 - EPS),
              "back10": (bool(bid_px[i10, 0] > TRIG + EPS) if i10 is not None else None),
              "back30": (bool(bid_px[i30, 0] > TRIG + EPS) if i30 is not None else None),
              "live_det_bid": float(np.mean([r["det_bid"] for r in det])) if det else None,
              "live_detected_share": len(det) / len(live15),
              "live15_sale": float(np.mean([r["avg_sale"] for r in sold])) if sold else None,
              "live15_sold_share": float(np.mean([r["sold_share"] for r in live15])),
              "live15_value": row["val_live15"], "live1_value": row["val_live1"],
              "live1_sale": float(np.mean([r["avg_sale"] for r in live1 if r["avg_sale"] is not None])) if any(r["avg_sale"] is not None for r in live1) else None,
              "inst15_sale": inst15["avg_sale"], "inst15_value": inst15["value"], "inst15_sold_share": inst15["sold_share"], "inst1_sale": inst1["avg_sale"],
              "v1_value": row["val_v1"], "v1_detected_share": float(np.mean([r["det_bid"] is not None for r in v1])),
              "depth15c": float(np.nansum(np.where(bid_px[trig_i] >= bid_px[trig_i, 0] - SLIP - EPS, bid_sz[trig_i], 0.0)))}
        if i2 is not None and ask[i2] <= 0.35 + EPS and ask[i2] > 0:
            a = float(ask[i2]); ev["buyer_ask"] = a; ev["buyer_pnl"] = hold_val - a - R.fee(a)
        events.append(ev)
    else:
        row["val_inst15"] = hold_val
    rows.append(row)

E = pd.DataFrame(events); W = pd.DataFrame(rows)
counts["dropped_no_look_poll"] = no_look


def cents(x):
    return None if x is None or x != x else round(100 * float(x), 3)


def mean_ci(v, cl):
    v = np.asarray(v, float)
    if len(v) == 0:
        return None
    lo, hi = R.boot(v, cl, np.mean)
    return [cents(v.mean()), cents(lo) if lo is not None else None, cents(hi) if hi is not None else None]


def summarize(Wg, Eg):
    o = {"windows_with_look": int(len(Wg)), "entries": int(Wg["entry"].sum())}
    Wen = Wg[Wg["entry"]]
    if len(Wen) == 0:
        return o
    o["mean_entry_ask"] = round(float(Wen["entry_ask"].mean()), 4)
    o["favourite_win_rate"] = round(float(Wen["hold_val"].mean()), 4)
    o["trigger_events"] = int(len(Eg)); o["trigger_share_of_entries"] = round(len(Eg) / len(Wen), 4)
    tw = {}
    for name, col in (("live_exit_15", "val_live15"), ("hold", "hold_val"), ("v1_confirm", "val_v1"), ("instant_exit_15", "val_inst15")):
        pnl = (Wen[col] - Wen["cost"]).to_numpy()
        tw[name] = {"pf": round(R.pf(pnl), 3), "pf_ci": R.boot(pnl, Wen["close_ms"].to_numpy(), R.pf), "mean_c": cents(pnl.mean()), "n": int(len(pnl))}
    o["twin_cash_pf_per_contract"] = tw
    if len(Eg) == 0:
        return o
    cl = Eg["close_ms"].to_numpy()
    o["events"] = {
        "n": int(len(Eg)), "median_left_s": round(float(Eg["left_s"].median()), 1),
        "left_s_quartiles": [round(float(x), 1) for x in np.percentile(Eg["left_s"], [25, 50, 75])],
        "trigger_poll_bid_c": cents(Eg["trig_bid"].mean()), "trigger_poll_ask_c": cents(Eg["trig_ask"].mean()),
        "live_detected_bid_c": cents(Eg["live_det_bid"].mean()),
        "live_sale_15_c": cents(Eg["live15_sale"].mean()), "live_sale_1_c": cents(Eg["live1_sale"].mean()),
        "live_sold_share_15": round(float(Eg["live15_sold_share"].mean()), 4),
        "gap_trigger_to_detected_c": cents((TRIG - Eg["live_det_bid"]).mean()),
        "gap_detected_to_sale_15_c": cents((Eg["live_det_bid"] - Eg["live15_sale"]).mean()),
        "gap_detected_to_sale_1_c": cents((Eg["live_det_bid"] - Eg["live1_sale"]).mean()),
        "instant_sale_15_c": cents(Eg["inst15_sale"].mean()), "instant_sale_1_c": cents(Eg["inst1_sale"].mean()),
        "instant_gap_trigger_to_sale_15_c": cents((TRIG - Eg["inst15_sale"]).mean()),
        "depth_within_15c_at_trigger_median": round(float(Eg["depth15c"].median()), 1),
        "share_depth_under_15": round(float((Eg["depth15c"] < 15).mean()), 4),
        "hold_win_rate_after_trigger": round(float(Eg["hold_val"].mean()), 4),
        "hold_minus_live_sell_15_c": mean_ci(Eg["hold_val"] - Eg["live15_value"], cl),
        "hold_minus_instant_sell_15_c": mean_ci(Eg["hold_val"] - Eg["inst15_value"], cl),
        "instant_minus_live_sell_15_c": mean_ci(Eg["inst15_value"] - Eg["live15_value"], cl),
        "pulled_bid_share": round(float(Eg["pulled"].mean()), 4),
        "back_above_25c_after_10s": round(float(Eg["back10"].dropna().astype(float).mean()), 4) if Eg["back10"].notna().any() else None,
        "back_above_25c_after_30s": round(float(Eg["back30"].dropna().astype(float).mean()), 4) if Eg["back30"].notna().any() else None,
        "v1_minus_live_c": mean_ci(Eg["v1_value"] - Eg["live15_value"], cl),
        "v1_detected_share": round(float(Eg["v1_detected_share"].mean()), 4),
    }
    if "buyer_pnl" in Eg and Eg["buyer_pnl"].notna().any():
        B = Eg[Eg["buyer_pnl"].notna()]
        o["counterparty_buyer"] = {"n": int(len(B)), "mean_ask_c": cents(B["buyer_ask"].mean()), "win_rate": round(float(B["hold_val"].mean()), 4),
                                   "pf": round(R.pf(B["buyer_pnl"]), 3), "pf_ci": R.boot(B["buyer_pnl"].to_numpy(), B["close_ms"].to_numpy(), R.pf),
                                   "mean_c": mean_ci(B["buyer_pnl"], B["close_ms"].to_numpy())}
    return o


out = {"test": "EXITREPLAY1", "block": BLOCK, "counts": counts, "note": "cents per contract unless said; intervals 95% by resampling close times"}
groups = {"KXGOLD15M": ["KXGOLD15M"], "crypto_pooled": ["KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M"], "all_five": SERIES,
          "KXBTC15M": ["KXBTC15M"], "KXETH15M": ["KXETH15M"], "KXXRP15M": ["KXXRP15M"], "KXDOGE15M": ["KXDOGE15M"]}
for name, ss in groups.items():
    Wg = W[W["series"].isin(ss)]
    Eg = E[E["series"].isin(ss)] if len(E) else E
    out[name] = summarize(Wg, Eg)
    if BLOCK == "POOLED":
        out[name]["by_block"] = {b: summarize(Wg[Wg["block"] == b], Eg[Eg["block"] == b] if len(Eg) else Eg) for b in ("D", "H")}
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps({k: out[k] for k in ("counts", "KXGOLD15M", "crypto_pooled")}, indent=1, default=float))
