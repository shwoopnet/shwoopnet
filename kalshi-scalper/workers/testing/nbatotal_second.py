#!/usr/bin/env python3
"""NBATOTAL search, BUILD 2 (Testing Desk, Nov 16, 2026), written blind from Desk C's card and spec (NBATOTAL_SECOND_HAND_CASE.md, readings T1 to T10). Built on my NBALADDER second build's helpers. Pure functions."""
import math
import engine1_core_second as core
import nbaladder_second as b

TOL = b.TOL
CELLS = ((9, "H"), (9, "M35"), (5, "H"), (5, "M35"), (4, "H"))          # (hours before the scheduled end, exit)
BANDS, SIDES, FILTERS = b.BANDS, b.SIDES, b.FILTERS
N_CELLS = len(CELLS) * len(BANDS) * len(SIDES) * len(FILTERS)
assert N_CELLS == 520
MARK = 12600          # 3.5 h


def decisions(rungs, candles, O_by, hours):
    """-> (kept, guarded, counts). guarded = open rungs with a usable quote whose last two two-sided candles differ by 0.15 or more (features computed, no entry)"""
    cnt = {"closed_by_D": 0, "no_quote": 0, "not_open": 0}; rows = []
    for r in rungs:
        if r["event"] not in O_by: continue
        O = O_by[r["event"]]; D = O - 3600 * hours; s = candles.get(r["ticker"], {})
        if r["close_time"] <= D: cnt["closed_by_D"] += 1; continue
        if r["open_time"] > D: cnt["not_open"] += 1; continue
        q = b.latest_usable(s, D - 180, D)
        if q is None: cnt["no_quote"] += 1; continue
        prev = [(t, c) for t, c in s.items() if t <= D and t < q[0] and b.usable(c[:2])]
        guard = bool(prev) and abs(b.mid(q[1]) - b.mid(max(prev)[1])) >= 0.15 - TOL
        anc = b.latest_usable(s, D - 3600 - 180, D - 3600)
        rows.append({"r": r, "O": O, "D": D, "t": q[0], "bid": q[1][0], "ask": q[1][1], "mid": b.mid(q[1]), "mv": None if anc is None else b.mid(q[1]) - b.mid(anc[1]), "spread": q[1][1] - q[1][0],
                     "v1": b.vol(s, D - 1800, D), "v0": b.vol(s, D - 3600, D - 1800), "age": D - r["open_time"], "guard": guard})
    byg = {}
    for d in rows: byg.setdefault(d["r"]["event"], []).append(d)
    for g in byg.values():
        m0 = min(abs(d["mid"] - 0.5) for d in g); L = max(d["r"]["strike"] for d in g if abs(d["mid"] - 0.5) <= m0 + TOL)
        for d in g: s_ = d["r"]["strike"]; d["dist"] = "below" if s_ < L else ("at" if s_ == L else "above")
    return [d for d in rows if not d["guard"]], [d for d in rows if d["guard"]], cnt


def passes(d, f):
    mv = d.get("mv")
    if f == "move_down": return mv is not None and mv <= -0.03 + TOL
    if f == "move_up": return mv is not None and mv >= 0.03 - TOL
    if f == "move_flat": return mv is not None and abs(mv) < 0.03 - TOL
    if f == "age_young": return d["age"] < 86400
    if f == "age_old": return d["age"] >= 86400
    return b.passes(d, f)


def m35_dropped(rungs, candles, O_by):
    """games dropped from M35 scoring: any rung with two consecutive two-sided candles ending in (O - 4 h, O - 3.5 h] whose mids differ by 0.15 or more"""
    out = set()
    for r in rungs:
        ev = r["event"]
        if ev not in O_by or ev in out: continue
        O = O_by[ev]; s = candles.get(r["ticker"], {})
        two = sorted((t, c) for t, c in s.items() if O - 14400 < t <= O - MARK and b.usable(c[:2]))
        for (t0, c0), (t1, c1) in zip(two, two[1:]):
            if abs(b.mid(c1[:2]) - b.mid(c0[:2])) >= 0.15 - TOL: out.add(ev); break
    return out


def cash(d, side, ex, candles, mode="primary", n=10):
    """as NBALADDER.cash with the M35 mark candle ending exactly at O - 3.5 h; -> (cash, marked)"""
    r = d["r"]; O = d["O"]; mark = O - MARK
    h_in = 0.02 if mode == "two" else (0.01 if mode == "weekly" else (0.02 if r["close_time"] - d["D"] <= 120 else 0.01))
    h_out = 0.02 if mode == "two" or r["close_time"] - mark <= 120 else 0.01
    ask = b.side_ask(d, side); paid = min(core.r6(ask + h_in), core.CAP); fee_in = core.fee_up_order(paid, n)
    def settle():
        if r["result"] not in ("yes", "no"): return round(-fee_in, 9)
        return round((n * 1.0 if r["result"] == side else 0.0) - n * paid - fee_in, 9)
    if ex == "H": return settle(), False
    c = candles.get(r["ticker"], {}).get(mark)
    if r["close_time"] > mark and c is not None and b.usable(c[:2]):
        bid = c[0] if side == "yes" else 1 - c[1]; px = max(core.r6(bid - h_out), core.FLOOR)
        return round(n * px - n * paid - fee_in - core.fee_up_order(px, n), 9), True
    return settle(), False


def m_total(carried=6290660): return N_CELLS + carried


def search(rungs, candles, carried=6290660, validate_h_only=False):
    """-> (cells {(hours, exit, band_lo, side, filter): stats}, counts, survivors)"""
    O_by, cnt = b.games(rungs); drop = m35_dropped(rungs, candles, O_by); cnt["m35_dropped_games"] = len(drop); cells = {}
    for hours in (9, 5, 4):
        kept, guarded, c2 = decisions(rungs, candles, O_by, hours)
        for k, v in c2.items(): cnt["%s_%dh" % (k, hours)] = v
        cnt["inplay_guard_%d" % hours] = len(guarded)          # once per skipped rung, per decision time (Desk C)
        for (h, ex) in CELLS:
            if h != hours or (validate_h_only and ex != "H"): continue
            for band in BANDS:
                for side in SIDES:
                    for f in FILTERS:
                        tr = []
                        for d in kept:
                            if ex == "M35" and d["r"]["event"] in drop: continue
                            if not b.in_band(b.side_ask(d, side), band) or not passes(d, f): continue
                            c1, mk = cash(d, side, ex, candles, "primary"); c2_, _ = cash(d, side, ex, candles, "two"); cw, _ = cash(d, side, ex, candles, "weekly", 5)
                            tr.append({"game": d["r"]["event"], "day": d["D"] // 86400, "close_time": d["r"]["close_time"], "ticker": d["r"]["ticker"], "cash1": c1, "cash2": c2_, "cashw": cw, "marked": mk})
                        st = b.cell_stats(tr); cells[(hours, ex, band[0], side, f)] = st
    elig = b.eligible(cells); surv = {k for k in b.bh(elig, m_total(carried)) if b.gate_ok(cells[k])}
    return cells, cnt, surv
