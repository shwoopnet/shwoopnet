#!/usr/bin/env python3
"""SOCDRIFT search, BUILD 2 (Testing Desk, Nov 16, 2026), written blind from Desk C's card, amendments and spec (SOCDRIFT_SECOND_HAND_CASE.md, S1 to S14 and addendum 1). Pure functions on in-memory data.
rungs: list of dicts {ticker, event, outcome, open_time, close_time, occ, result} (one per outcome market; the game = event ticker); candles: {ticker: {end_ts: (bid, ask, vol)}} (hourly)."""
import calendar, math, re
import engine1_core_second as core
import nbaladder_second as b

TOL = b.TOL
H = 3600
D_OFFS = (24, 12, 6)
EXITS = ("H", "M2")
BANDS = ((0.10, 0.25), (0.25, 0.40), (0.40, 0.55), (0.55, 0.70), (0.70, 0.85))
SIDES = ("yes", "no")
FILTERS = ("none", "move_down", "move_flat", "move_up", "spread2", "spread4", "vol_rise", "vol_notrise", "tie", "team")
N_CELLS = len(D_OFFS) * len(EXITS) * len(BANDS) * len(SIDES) * len(FILTERS)
assert N_CELLS == 600
DAYS_WINDOW = (1793328799 - 1789689600) / 86400
MONTHS = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}


def floor_hour(t): return t // H * H


def ticker_midnight(event):
    m = re.search(r"-(\d\d)([A-Z]{3})(\d\d)", event)
    if not m or m.group(2) not in MONTHS: return None
    return calendar.timegm((2000 + int(m.group(1)), MONTHS[m.group(2)], int(m.group(3)), 0, 0, 0))


def games(rungs):
    """-> ({event: O}, counts): one occurrence value, on a quarter hour, within 2 days of the ticker's date midnight"""
    by = {}
    for r in rungs: by.setdefault(r["event"], set()).add(r["occ"])
    ok, bad = {}, 0
    for ev, s in by.items():
        mid = ticker_midnight(ev)
        if len(s) == 1 and next(iter(s)) % 900 == 0 and mid is not None and abs(next(iter(s)) - mid) <= 2 * 86400: ok[ev] = next(iter(s))
        else: bad += 1
    return ok, {"clock_dropped_games": bad}


def in_band(ask, band):
    lo, hi = band
    return ask >= lo - TOL and (ask <= hi + TOL if hi == 0.85 else ask < hi - TOL)


def decisions(rungs, candles, O_by, off):
    cnt = {"closed_by_D": 0, "no_quote": 0, "not_open": 0}; out = []
    for r in rungs:
        if r["event"] not in O_by: continue
        K = O_by[r["event"]] - 3 * H; D = floor_hour(K - off * H); s = candles.get(r["ticker"], {})
        if r["close_time"] <= D: cnt["closed_by_D"] += 1; continue
        if r["open_time"] > D: cnt["not_open"] += 1; continue
        q = b.latest_usable(s, D - H + 1, D)
        if q is None: cnt["no_quote"] += 1; continue
        anc = b.latest_usable(s, D - 7 * H + 1, D - 6 * H)
        out.append({"r": r, "O": O_by[r["event"]], "K": K, "D": D, "Mh": floor_hour(K - 2 * H), "t": q[0], "bid": q[1][0], "ask": q[1][1], "mid": b.mid(q[1]), "mv": None if anc is None else b.mid(q[1]) - b.mid(anc[1]), "spread": q[1][1] - q[1][0],
                    "v1": b.vol(s, D - 3 * H, D), "v0": b.vol(s, D - 6 * H, D - 3 * H), "tie": r["outcome"] == "TIE"})
    return out, cnt


def passes(d, f):
    mv = d.get("mv")
    if f == "none": return True
    if f == "move_down": return mv is not None and mv <= -0.02 + TOL
    if f == "move_up": return mv is not None and mv >= 0.02 - TOL
    if f == "move_flat": return mv is not None and abs(mv) < 0.02 - TOL
    if f == "spread2": return d["spread"] <= 0.02 + TOL
    if f == "spread4": return d["spread"] <= 0.04 + TOL
    if f == "vol_rise": return d["v1"] > d["v0"]
    if f == "vol_notrise": return not d["v1"] > d["v0"]
    if f == "tie": return d["tie"]
    if f == "team": return not d["tie"]
    raise ValueError(f)


def live_guard(rungs, candles, O_by):
    """games whose Kh and Kh - 1 h candles (both two-sided) on any outcome differ in mid by 0.15 or more: M2 off for every decision of the game"""
    out = set()
    for r in rungs:
        ev = r["event"]
        if ev not in O_by or ev in out: continue
        Kh = floor_hour(O_by[ev] - 3 * H); s = candles.get(r["ticker"], {}); c0, c1 = s.get(Kh - H), s.get(Kh)
        if b.usable(c0[:2] if c0 else None) and b.usable(c1[:2] if c1 else None) and abs(b.mid(c1[:2]) - b.mid(c0[:2])) >= 0.15 - TOL: out.add(ev)
    return out


def m2_guard(rungs, candles, O_by, off):
    """games dropped from M2 for this D: consecutive two-sided candles ending in (D, Mh] on any outcome differ by 0.15 or more"""
    out = set()
    for r in rungs:
        ev = r["event"]
        if ev not in O_by or ev in out: continue
        K = O_by[ev] - 3 * H; D = floor_hour(K - off * H); Mh = floor_hour(K - 2 * H); s = candles.get(r["ticker"], {})
        two = sorted((t, c) for t, c in s.items() if D < t <= Mh and b.usable(c[:2]))
        for (t0, c0), (t1, c1) in zip(two, two[1:]):
            if abs(b.mid(c1[:2]) - b.mid(c0[:2])) >= 0.15 - TOL: out.add(ev); break
    return out


def cash(d, side, ex, candles, mode="primary", n=10):
    r = d["r"]; Mh = d["Mh"]
    near_in = r["close_time"] - d["D"] <= 120; near_out = r["close_time"] - Mh <= 120
    if mode == "two": h_in = h_out = 0.02
    elif mode == "weekly": h_in = 0.01; h_out = 0.02 if near_out else 0.01
    else: h_in = 0.02 if near_in else 0.01; h_out = 0.02 if (near_in or near_out) else 0.01
    ask = b.side_ask(d, side); paid = min(core.r6(ask + h_in), core.CAP); fee_in = core.fee_up_order(paid, n)
    def settle():
        if r["result"] not in ("yes", "no"): return round(-fee_in, 9)
        return round((n * 1.0 if r["result"] == side else 0.0) - n * paid - fee_in, 9)
    if ex == "H": return settle(), False
    c = candles.get(r["ticker"], {}).get(Mh)
    if r["close_time"] > Mh and Mh > d["D"] and c is not None and b.usable(c[:2]):
        bid = c[0] if side == "yes" else 1 - c[1]; px = max(core.r6(bid - h_out), core.FLOOR)
        return round(n * px - n * paid - fee_in - core.fee_up_order(px, n), 9), True
    return settle(), False


def cell_stats(trades, days_window=DAYS_WINDOW):
    ts = sorted(trades, key=lambda t: (t["close_time"], t["ticker"])); v1 = [t["cash1"] for t in ts]; k = len(ts); h = k // 2
    games_ = {}
    for t in ts: games_[t["game"]] = games_.get(t["game"], 0.0) + t["cash1"]
    z = b.zstat(list(games_.values())); mk = [t for t in ts if t["marked"]]
    return {"n": k, "games": len(games_), "days": len(set(t["day"] for t in ts)), "pf1": b.pf(v1), "h1": b.pf(v1[:h]), "h2": b.pf(v1[h:]), "pf2": b.pf([t["cash2"] for t in ts]), "z": z, "p": b.p_upper(z),
            "net1": sum(v1), "weekly5": sum(t["cashw"] for t in ts) / (days_window / 7), "marked_n": len(mk), "marked_pf": b.pf([t["cash1"] for t in mk])}


def m_total(carried=6290660, m_new=N_CELLS): return carried + m_new


def search(rungs, candles, carried=6290660, m_new=N_CELLS, days_window=DAYS_WINDOW):
    O_by, cnt = games(rungs); live = live_guard(rungs, candles, O_by); cnt["live_guard_dropped_m2"] = len(live); m2_any = set(); cells = {}
    for off in D_OFFS:
        dec, c2 = decisions(rungs, candles, O_by, off)
        for k, v in c2.items(): cnt["%s_%dh" % (k, off)] = v
        g2 = m2_guard(rungs, candles, O_by, off); m2_any |= g2
        for ex in EXITS:
            for band in BANDS:
                for side in SIDES:
                    for f in FILTERS:
                        tr = []
                        for d in dec:
                            ev = d["r"]["event"]
                            if ex == "M2" and (ev in live or ev in g2): continue
                            if not in_band(b.side_ask(d, side), band) or not passes(d, f): continue
                            c1, mk = cash(d, side, ex, candles, "primary"); c2_, _ = cash(d, side, ex, candles, "two"); cw, _ = cash(d, side, ex, candles, "weekly", 5)
                            tr.append({"game": ev, "day": d["D"] // 86400, "close_time": d["r"]["close_time"], "ticker": d["r"]["ticker"], "cash1": c1, "cash2": c2_, "cashw": cw, "marked": mk})
                        cells[(off, ex, band[0], side, f)] = cell_stats(tr, days_window)
    cnt["m2_dropped_games"] = len(m2_any)
    elig = b.eligible(cells); surv = {k for k in b.bh(elig, m_total(carried, m_new)) if b.gate_ok(cells[k])}
    return cells, cnt, surv
