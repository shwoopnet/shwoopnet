#!/usr/bin/env python3
"""NBALADDER / NBAREB search, BUILD 2 (Testing Desk, Nov 16, 2026), written blind from Desk C's cards and their answers N1 to N13 (NBALADDER_SECOND_HAND_CASE.md and addendum 1). Pure functions on in-memory data; the loader is separate.
rungs: list of dicts {ticker, event, player, strike, open_time, close_time, occ, result}; candles: {ticker: {end_ts: (bid, ask, vol)}} (bid and ask None when absent)."""
import math, itertools
import engine1_core_second as core

TOL = 1e-9
DS = (120, 60, 30)
BANDS = ((0.30, 0.40), (0.40, 0.50), (0.50, 0.60), (0.60, 0.70))
SIDES = ("yes", "no")
EXITS = ("H", "M10")
FILTERS = (["none"] + ["move_down", "move_flat", "move_up", "dist_below", "dist_at", "dist_above", "spread3", "spread6", "vol_rising", "vol_not", "age_young", "age_old"])
N_CELLS = len(DS) * len(BANDS) * len(SIDES) * len(EXITS) * len(FILTERS)
assert N_CELLS == 624


def usable(c): return c is not None and c[0] is not None and c[1] is not None and c[0] > TOL and c[1] - c[0] > TOL and c[1] < 1 - TOL
def mid(c): return (c[0] + c[1]) / 2


def games(rungs):
    """-> ({event: O}, counts): a game keeps only when all its rungs share one occurrence value on :00 or :30 with second 0"""
    by = {}
    for r in rungs: by.setdefault(r["event"], set()).add(r["occ"])
    ok, bad = {}, 0
    for ev, s in by.items():
        if len(s) == 1 and next(iter(s)) % 1800 == 0: ok[ev] = next(iter(s))
        else: bad += 1
    return ok, {"games_dropped_clock": bad}


def latest_usable(series, lo, hi):
    best = None
    for t, c in series.items():
        if lo <= t <= hi and usable(c[:2]) and (best is None or t > best[0]): best = (t, c)
    return best


def vol(series, lo, hi):
    return sum((c[2] or 0.0) for t, c in series.items() if lo < t <= hi)


def decisions(rungs, candles, O_by_event, D_min):
    """-> list of dicts, one per rung that is open at D with a usable decision candle, with the features; counts of skips"""
    cnt = {"closed_by_D": 0, "no_quote": 0, "not_open": 0}; out = []
    for r in rungs:
        if r["event"] not in O_by_event: continue
        O = O_by_event[r["event"]]; D = O - 60 * D_min; s = candles.get(r["ticker"], {})
        if r["close_time"] <= D: cnt["closed_by_D"] += 1; continue
        if r["open_time"] > D: cnt["not_open"] += 1; continue
        q = latest_usable(s, D - 180, D)
        if q is None: cnt["no_quote"] += 1; continue
        anc = latest_usable(s, D - 1800 - 180, D - 1800)
        out.append({"r": r, "O": O, "D": D, "t": q[0], "bid": q[1][0], "ask": q[1][1], "mid": mid(q[1]), "mv": None if anc is None else mid(q[1]) - mid(anc[1]), "spread": q[1][1] - q[1][0],
                    "v1": vol(s, D - 600, D), "v0": vol(s, D - 1200, D - 600), "age": D - r["open_time"]})
    # the line rung per (event, player): the rung whose mid is closest to 0.50, ties (within 1e-9) to the higher strike
    groups = {}
    for d in out: groups.setdefault((d["r"]["event"], d["r"]["player"]), []).append(d)
    for g in groups.values():
        m0 = min(abs(d["mid"] - 0.5) for d in g); L = max(d["r"]["strike"] for d in g if abs(d["mid"] - 0.5) <= m0 + TOL)
        for d in g: s_ = d["r"]["strike"]; d["dist"] = "below" if s_ < L else ("at" if s_ == L else "above")
    return out, cnt


def side_ask(d, side): return d["ask"] if side == "yes" else 1 - d["bid"]


def in_band(ask, band):
    lo, hi = band
    return ask >= lo - TOL and (ask <= hi + TOL if hi == 0.70 else ask < hi - TOL)


def passes(d, f):
    mv = d.get("mv")
    if f == "none": return True
    if f == "move_down": return mv is not None and mv <= -0.05 + TOL
    if f == "move_up": return mv is not None and mv >= 0.05 - TOL
    if f == "move_flat": return mv is not None and abs(mv) < 0.05 - TOL
    if f.startswith("dist_"): return d["dist"] == f[5:]
    if f == "spread3": return d["spread"] <= 0.03 + TOL
    if f == "spread6": return d["spread"] <= 0.06 + TOL
    if f == "vol_rising": return d["v1"] > d["v0"]
    if f == "vol_not": return not d["v1"] > d["v0"]
    if f == "age_young": return d["age"] < 21600
    if f == "age_old": return d["age"] >= 21600
    raise ValueError(f)


def cash(d, side, ex, candles, mode="primary", n=10):
    """-> (cash, marked) for one trade; mode 'primary' (1c, 2c when close - D <= 120 on entry; sale leg 2c when close - (O - 600) <= 120), 'two' (0.02 on every leg), 'weekly' (entry 0.01, sale leg as primary)"""
    r = d["r"]; O = d["O"]
    h_in = 0.02 if mode == "two" else (0.01 if mode == "weekly" else (0.02 if r["close_time"] - d["D"] <= 120 else 0.01))
    h_out = 0.02 if mode == "two" or r["close_time"] - (O - 600) <= 120 else 0.01
    ask = side_ask(d, side); paid = min(core.r6(ask + h_in), core.CAP); fee_in = core.fee_up_order(paid, n)
    def settle():
        if r["result"] not in ("yes", "no"): return round(-fee_in, 9)
        return round((n * 1.0 if r["result"] == side else 0.0) - n * paid - fee_in, 9)
    if ex == "H": return settle(), False
    c = candles.get(r["ticker"], {}).get(O - 600)
    if r["close_time"] > O - 600 and c is not None and usable(c[:2]):
        bid = c[0] if side == "yes" else 1 - c[1]
        px = max(core.r6(bid - h_out), core.FLOOR)
        return round(n * px - n * paid - fee_in - core.fee_up_order(px, n), 9), True
    return settle(), False


def pf(v):
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    if neg == 0: return math.inf if pos > 0 else math.nan
    return pos / neg


def zstat(sums):
    k = len(sums)
    if k < 2: return None
    m = sum(sums) / k; sd = math.sqrt(sum((x - m) ** 2 for x in sums) / (k - 1))
    return None if sd == 0 else m / (sd / math.sqrt(k))


def p_upper(z): return None if z is None else 0.5 * math.erfc(z / math.sqrt(2))


def cell_stats(trades):
    """trades: list of dicts {game, day, close_time, ticker, cash1 (primary), cash2, cashw, marked}"""
    ts = sorted(trades, key=lambda t: (t["close_time"], t["ticker"])); v1 = [t["cash1"] for t in ts]; k = len(ts); h = k // 2
    games = {}
    for t in ts: games[t["game"]] = games.get(t["game"], 0.0) + t["cash1"]
    z = zstat(list(games.values()))
    mk = [t for t in ts if t["marked"]]
    return {"n": k, "games": len(games), "days": len(set(t["day"] for t in ts)), "pf1": pf(v1), "h1": pf(v1[:h]), "h2": pf(v1[h:]), "pf2": pf([t["cash2"] for t in ts]), "z": z, "p": p_upper(z),
            "net1": sum(v1), "weekly5": sum(t["cashw"] for t in ts) / (16 / 7), "marked_n": len(mk), "marked_pf": pf([t["cash1"] for t in mk])}


def ge(x, lim): return (not math.isnan(x)) and x >= lim


def gate_ok(s): return s["n"] >= 100 and s["games"] >= 40 and s["days"] >= 10 and ge(s["pf1"], 1.3) and ge(s["h1"], 1.0) and ge(s["h2"], 1.0) and ge(s["pf2"], 1.0)


def bh(cells, m_total, q=0.05):
    """cells {key: p or None} of the eligible cells (n >= 48); the survivors, with k x q / m_total at rank k"""
    items = sorted(((p, k) for k, p in cells.items() if p is not None), key=lambda x: (x[0], x[1])); kmax = 0
    for i, (p, k) in enumerate(items, 1):
        if p <= i * q / m_total: kmax = i
    return {k for p, k in items[:kmax]}


def eligible(cells): return {k: s["p"] for k, s in cells.items() if s["n"] >= 48}


def search(rungs, candles, carried=0):
    """-> {cell: stats}, counts, survivors (the cells that clear the gates and BH)"""
    O_by, cnt = games(rungs); cells = {}
    for D_min in DS:
        dec, c2 = decisions(rungs, candles, O_by, D_min)
        for k, v in c2.items(): cnt["%s_%d" % (k, D_min)] = v
        for band in BANDS:
            for side in SIDES:
                for ex in EXITS:
                    for f in FILTERS:
                        tr = []
                        for d in dec:
                            if not in_band(side_ask(d, side), band) or not passes(d, f): continue
                            c1, mk = cash(d, side, ex, candles, "primary"); c2_, _ = cash(d, side, ex, candles, "two"); cw, _ = cash(d, side, ex, candles, "weekly", 5)
                            tr.append({"game": d["r"]["event"], "day": d["D"] // 86400, "close_time": d["r"]["close_time"], "ticker": d["r"]["ticker"], "cash1": c1, "cash2": c2_, "cashw": cw, "marked": mk})
                        cells[(D_min, band[0], side, ex, f)] = cell_stats(tr)
    elig = eligible(cells)
    surv = {k for k in bh(elig, N_CELLS + carried) if gate_ok(cells[k])}
    return cells, cnt, surv
