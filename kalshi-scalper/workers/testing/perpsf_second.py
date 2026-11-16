#!/usr/bin/env python3
"""PERPS-FAM-F scorer (F1 gap by hold, F3 overnight drift), Testing Desk, Nov 16, 2026. Pure functions on in-memory candles; raw data never read here (a loader is separate and only after the read date).
Hand case: PERPSF_SCORER_HAND_CASE.md (committed first). Reuses engine1_perps_second primitives (two_sided, mid, funding_for, stats, pf, p_upper, bh) and the OPENGAP1 trigger rule."""
import math
import engine1_perps_second as p

H = 3600
REL = (0.0002, 0.0005); STRESS = (0.001, 0.002)
F1_EXITS = ("T15", "T30", "T60", "T240", "TC", "TO")


def weekday(L): return (L + 3) % 7          # epoch day 0 is a Thursday; Monday = 0
def next_weekday_open(ts):
    """14:31 UTC (09:31 EST) of the next Monday to Friday UTC day strictly after ts's UTC day"""
    L = ts // 86400 + 1
    while weekday(L) >= 5: L += 1
    return L * 86400 + 14 * H + 31 * 60


def trade(series, e, xt, long_, h, funding):
    q, x = series.get(e), series.get(xt)
    if not (p.two_sided(q) and p.two_sided(x)): return None
    fill = q[1] * (1 + h) if long_ else q[0] * (1 - h)
    xp = x[0] * (1 - h) if long_ else x[1] * (1 + h)
    gross = xp / fill - 1 if long_ else (fill - xp) / fill
    fund = p.funding_for(funding, e, xt, long_); t = {"e": e, "exit_ts": xt, "gross": gross, "funding": fund, "day": e // 86400}
    if fund is not None: t["net_taker"], t["net_maker"] = gross - p.TAKER - fund, gross - p.MAKER - fund
    return t


def f3(series, days, side, h, funding=None):
    """days: UTC day numbers (Monday to Friday only count). -> (trades, counts)"""
    out, cnt = [], {"no_mark": 0, "funding_not_booked": 0}
    for L in sorted(days):
        if weekday(L) >= 5: continue
        e = L * 86400 + 21 * H; xt = next_weekday_open(e)
        t = trade(series, e, xt, side == "long", h, funding)
        if t is None: cnt["no_mark"] += 1; continue
        if t["funding"] is None: cnt["funding_not_booked"] += 1
        out.append(t)
    return out, cnt


def trigger(ev):
    """the OPENGAP1 entry: -> (sign, entry_ts) or None; untriggered, missing underlying or a one-sided candle give None"""
    if ev["u_open"] is None or ev["u_prev"] is None or ev["u_prev"] <= 0: return None
    o, c = ev["open_ts"], ev["c"]
    pp, p25, e = c.get(ev["prev16_ts"]), c.get(o - 300), c.get(o + 60)
    if not (p.two_sided(pp) and p.two_sided(p25) and p.two_sided(e)): return None
    g = (ev["u_open"] / ev["u_prev"] - 1) - (p.mid(p25) / p.mid(pp) - 1)
    half = ((e[1] - e[0]) / 2) / p.mid(e)
    if round(g, 9) == 0 or not round(abs(g), 9) > round(2 * half, 9): return None
    return (1 if g > 0 else -1), o + 60


def exit_ts(e, ex):
    if ex == "TC": return e // 86400 * 86400 + 21 * H
    if ex == "TO": return next_weekday_open(e)
    return e + 60 * int(ex[1:])


def f1(evs, ex, h, funding=None):
    """evs of ONE name; -> (trades, counts). counts: triggered, no_mark, blocked, funding_not_booked"""
    out, cnt = [], {"triggered": 0, "no_mark": 0, "blocked": 0, "funding_not_booked": 0}; free = -math.inf
    for ev in sorted(evs, key=lambda v: v["open_ts"]):
        tr = trigger(ev)
        if tr is None: continue
        cnt["triggered"] += 1; sgn, e = tr
        if e < free: cnt["blocked"] += 1; continue
        xt = exit_ts(e, ex); t = trade(ev["c"], e, xt, sgn > 0, h, funding)
        if t is None: cnt["no_mark"] += 1; continue
        free = xt
        if t["funding"] is None: cnt["funding_not_booked"] += 1
        out.append(t)
    return out, cnt


def counts_only(per_name_counts):
    """integers only: pooled sum of every counter"""
    tot = {}
    for c in per_name_counts.values():
        for k, v in c.items(): tot[k] = tot.get(k, 0) + v
    return tot
