"""ENTRYREPLAY1: cheap-side entry execution on Bitcoin in OICORE's entry window, replayed on the R6 books and tape.

Registration: FORENSICS_REGISTRATION_NOV12.md (pushed before any recorded row was opened).
Baseline population only (no open interest condition: open interest is not in the held files).
Public recorded market data only. The bot's own orders are not read or reconstructed.

usage: python3 -I entryreplay1.py <data_root> <block: D|H|POOLED> <out_json>
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import r6load as R

ROOT, BLOCK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SERIES = ["KXBTC15M"]
LOOK_S, LOOK_TOL_S = 178, 10
BAND = (0.08, 0.50)
QTY = 10
CANCEL_S = 60
EPS = 1e-9

cov = R.load_coverage(ROOT, SERIES)
if BLOCK in ("D", "H"):
    cov = cov[cov["block"] == BLOCK]
counts = {"windows_listed": int(len(cov))}
ok = cov[(cov["result"].isin(["yes", "no"])) & (cov["max_gap_ms"] <= 15000)]
counts["dropped_no_result_or_gap"] = int(len(cov) - len(ok))
close_ms = ok["close_ms"].to_dict()
books = R.load_books(ROOT, ok.index, min_left_s=0, max_left_s=200, close_ms=close_ms)
tape = R.load_trades(ROOT, ok.index, close_ms, CANCEL_S, LOOK_S + 2)
tape_by = {tk: g for tk, g in tape.groupby("ticker", sort=False)}

rows = []
no_look = 0
for tk, g in books.groupby("ticker", sort=False):
    T = close_ms[tk]; res = ok.at[tk, "result"]; block = ok.at[tk, "block"]
    t = g["t_recv_ms"].to_numpy()
    yb, nb = g["yes_bid_px_1"].to_numpy(float), g["no_bid_px_1"].to_numpy(float)
    ybs, nbs = g["yes_bid_sz_1"].to_numpy(float), g["no_bid_sz_1"].to_numpy(float)
    usable = (yb == yb) & (nb == nb) & (yb < 1 - nb - EPS) & (t < T)
    cand = np.flatnonzero(usable & (t >= T - LOOK_S * 1000) & (t <= T - (LOOK_S - LOOK_TOL_S) * 1000))
    if len(cand) == 0:
        no_look += 1
        continue
    i0 = cand[0]
    ask_yes, ask_no = 1 - nb[i0], 1 - yb[i0]
    if abs(ask_yes - ask_no) < EPS:
        rows.append({"ticker": tk, "block": block, "close_ms": T, "in_band": False}); continue
    side = "yes" if ask_yes < ask_no else "no"
    a0 = float(min(ask_yes, ask_no))
    if not (BAND[0] - EPS <= a0 <= BAND[1] + EPS):
        rows.append({"ticker": tk, "block": block, "close_ms": T, "in_band": False}); continue
    own_bid, own_bsz = (yb, ybs) if side == "yes" else (nb, nbs)
    oth_bid, oth_bsz = (nb, nbs) if side == "yes" else (yb, ybs)
    ask = 1 - oth_bid            # our side's ask; the size shown at it is the other side's best bid size
    win = 1.0 if res == side else 0.0
    row = {"ticker": tk, "block": block, "close_ms": T, "in_band": True, "side": side, "ask0": a0, "win": win,
           "spread0": float(a0 - own_bid[i0]), "t0_pnl": win - a0 - R.fee(a0)}

    def first_at(ms):
        k = np.flatnonzero(usable & (t >= t[i0] + ms))
        return int(k[0]) if len(k) else None
    for name, ms in (("t1", 1000), ("t5", 5000)):
        j = first_at(ms)
        fill = j is not None and ask[j] <= a0 + 0.01 + EPS and oth_bsz[j] >= QTY
        row[name + "_fill"] = bool(fill)
        if fill:
            p = float(ask[j]); row[name + "_px"] = p; row[name + "_pnl"] = win - p - R.fee(p)
            fee10 = np.ceil(0.07 * QTY * p * (1 - p) * 100 - 1e-9) / 100 / QTY
            row[name + "_pnl_r10"] = win - p - fee10
    # maker rule M
    j = first_at(1000)
    if j is None or t[j] >= T - CANCEL_S * 1000:
        row["m_placed"] = False
        rows.append(row); continue
    P = float(own_bid[j]); Q0 = float(own_bsz[j])
    row.update({"m_placed": True, "m_px": P, "m_q0": Q0})
    tr = tape_by.get(tk)
    vol_at = 0.0; through = False
    if tr is not None:
        x = tr[(tr["ms"] > t[j]) & (tr["ms"] < T - CANCEL_S * 1000)]
        yp = x["yes_price_dollars"].to_numpy(float); c = x["count_fp"].to_numpy(float); sd = x["taker_outcome_side"].to_numpy()
        if side == "yes":
            hit = sd == "no"; at = hit & (np.abs(yp - P) < 1e-6); thru = hit & (yp < P - 1e-6)
        else:
            hit = sd == "yes"; at = hit & (np.abs(yp - (1 - P)) < 1e-6); thru = hit & (yp > (1 - P) + 1e-6)
        vol_at = float(c[at].sum()); through = bool(thru.any())
    row["m_vol_at"] = vol_at; row["m_through"] = through
    row["m_fill_pess"] = float(QTY if through else min(QTY, max(0.0, vol_at - Q0)))
    row["m_fill_opt"] = float(QTY if through else min(QTY, vol_at))
    rows.append(row)

W = pd.DataFrame(rows)
for _c in ("in_band", "t1_fill", "t5_fill", "m_placed", "m_through"):       # rows outside the band carry no value: read a missing flag as False
    W[_c] = W[_c].fillna(False).astype(bool) if _c in W else False
counts["dropped_no_look_poll"] = no_look


def cents(x):
    return None if x is None or x != x else round(100 * float(x), 3)


def taker(G, name):
    if name == "t0":
        x = G; pnl = x["t0_pnl"].to_numpy(); px = x["ask0"]
        fillrate = 1.0; un = x.iloc[0:0]
    else:
        x = G[G[name + "_fill"]]; pnl = x[name + "_pnl"].to_numpy(); px = x[name + "_px"]
        fillrate = float(G[name + "_fill"].mean()); un = G[~G[name + "_fill"]]
    o = {"n": int(len(x)), "fill_rate": round(fillrate, 4), "mean_px_c": cents(px.mean()) if len(x) else None,
         "win_rate": round(float(x["win"].mean()), 4) if len(x) else None,
         "pf": round(R.pf(pnl), 3) if len(x) else None, "pf_ci": R.boot(pnl, x["close_ms"].to_numpy(), R.pf) if len(x) else None,
         "mean_c": cents(pnl.mean()) if len(x) else None}
    if name != "t0" and len(x):
        o["pf_fee_rounded_10lot"] = round(R.pf(x[name + "_pnl_r10"]), 3)
    if len(un):
        o["unfilled"] = {"n": int(len(un)), "win_rate": round(float(un["win"].mean()), 4), "mean_ask0_c": cents(un["ask0"].mean()),
                         "t0_pf_if_filled_at_look_ask": round(R.pf(un["t0_pnl"]), 3)}
    return o


def maker(G, col, fee_share=0.0):
    M = G[G["m_placed"]]
    f = M[col].to_numpy()
    pc = (M["win"] - M["m_px"] - fee_share * R.fee(M["m_px"])).to_numpy()      # cash per filled contract
    pnl = f * pc                                                                # dollars per order
    filled = f > 0
    o = {"orders": int(len(M)), "orders_with_fill": int(filled.sum()), "fill_rate_orders": round(float(filled.mean()), 4) if len(M) else None,
         "contracts_filled_share": round(float(f.sum() / (QTY * len(M))), 4) if len(M) else None}
    if filled.sum() == 0:
        return o
    cl = M["close_ms"].to_numpy()
    o.update({"mean_px_c": cents(np.average(M["m_px"], weights=f)), "win_rate_contracts": round(float(np.average(M["win"], weights=f)), 4),
              "pf": round(R.pf(pnl), 3), "pf_ci": R.boot(pnl, cl, R.pf),
              "mean_c_per_filled_contract": cents(pnl.sum() / f.sum()), "mean_c_per_resting_order_per_contract": cents(pnl.sum() / (QTY * len(M))),
              "unfilled_orders": {"n": int((~filled).sum()), "win_rate": round(float(M["win"][~filled].mean()), 4) if (~filled).any() else None,
                                  "mean_bid_c": cents(M["m_px"][~filled].mean()) if (~filled).any() else None},
              "t1_taker_same_windows": taker(M[filled], "t1")})
    return o


def summarize(G):
    o = {"windows_with_look": int(len(G)), "in_band": int(G["in_band"].sum())}
    B = G[G["in_band"]]
    if len(B) == 0:
        return o
    o["mean_ask_at_look_c"] = cents(B["ask0"].mean()); o["mean_spread_at_look_c"] = cents(B["spread0"].mean())
    o["cheap_side_win_rate"] = round(float(B["win"].mean()), 4)
    o["median_queue_at_bid"] = round(float(B["m_q0"].median()), 1) if "m_q0" in B else None
    o["taker_T0_at_look_ask"] = taker(B, "t0"); o["taker_T1_limit_plus_1c_after_1s"] = taker(B, "t1"); o["taker_T5_limit_plus_1c_after_5s"] = taker(B, "t5")
    o["maker_pessimistic"] = maker(B, "m_fill_pess"); o["maker_optimistic"] = maker(B, "m_fill_opt")
    o["maker_pessimistic_fee_25pct_of_taker"] = {k: v for k, v in maker(B, "m_fill_pess", 0.25).items() if k in ("pf", "mean_c_per_filled_contract")}
    M = B[B["m_placed"]]
    o["maker_through_share"] = round(float(M["m_through"].mean()), 4) if len(M) else None
    # Added AFTER both blocks were read (descriptive, no try): the paired cost figure. Per window, per contract ordered:
    # the resting order's cash result minus the taker's at the look ask (T0), same windows, same outcome.
    if len(M):
        f = M["m_fill_pess"].to_numpy() / QTY
        mk = f * (M["win"] - M["m_px"]).to_numpy(); tk0 = M["t0_pnl"].to_numpy()
        d = mk - tk0; lo, hi = R.boot(d, M["close_ms"].to_numpy(), np.mean)
        o["paired_maker_pess_minus_T0_c"] = [cents(d.mean()), cents(lo), cents(hi)]
        o["paired_parts_c"] = {"price_and_fee_saved_on_filled": cents((f * (M["ask0"] + R.fee(M["ask0"]) - M["m_px"])).mean()),
                               "given_up_on_unfilled": cents(((1 - f) * (M["win"] - M["ask0"] - R.fee(M["ask0"]))).mean())}
    return o


out = {"test": "ENTRYREPLAY1", "block": BLOCK, "counts": counts, "note": "cents per contract; PF cash; intervals 95% by resampling windows"}
out["KXBTC15M"] = summarize(W)
if BLOCK == "POOLED":
    out["by_block"] = {b: summarize(W[W["block"] == b]) for b in ("D", "H")}
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
