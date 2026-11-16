#!/usr/bin/env python3
"""ENGINE1 perps scorer, BUILD 2 (Testing Desk, Nov 16, 2026). Independent of Desk A's code: written from ENGINE1_PERPS_AMENDMENT_NOV16.md and the hand case only.
Research only: pure functions on candles, no I/O. Hand case: ENGINE1_PERPS_SECOND_HAND_CASE.md (committed first). Test: test_engine1_perps_second.py (invented rows only).
A series is {end_ts: (bid, ask)}; time is UTC epoch seconds (the US cash session is 14:30 to 21:00 UTC under EST).
"""
import math

TAKER, MAKER = 0.0024, 0.0010
PRIMARY, STRESS = (0.0002, 0.0005), (0.001, 0.002)
MOM_K = (1, 3, 5, 15)
FILTERS = (["none"] + ["mom%d_%s" % (k, d) for k in MOM_K for d in ("up", "down")] + ["spread_low", "spread_mid", "spread_high"]
           + ["tod_pre", "tod_open", "tod_mid", "tod_close", "tod_post"] + ["orb_up", "orb_down", "sess_high", "sess_low"])
EXITS = ["T3", "T10", "T15", "T30", "TS15", "TS30", "T60", "T240", "TC", "TO"]
HOLD = {"T3": 1800, "T10": 1800, "T15": 1800, "T30": 1800, "TS15": 1800, "TS30": 1800, "T60": 3600, "T240": 14400}          # the cooldown after a taken entry; TC and TO: until the previous exit
OPEN, CASH_CLOSE = 14 * 3600 + 30 * 60, 21 * 3600


def two_sided(q): return q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1]
def mid(q): return (q[0] + q[1]) / 2
def sod(ts): return ts % 86400
def day(ts): return ts // 86400


def spread_cuts(series, lo, hi):
    """c1, c2 = the ceil(n/3)-th and ceil(2n/3)-th sorted spread_bps of the two-sided candles ending in [lo, hi) (the SEARCH entries of one ticker)"""
    v = sorted((q[1] - q[0]) / mid(q) * 1e4 for t, q in series.items() if lo <= t < hi and two_sided(q)); n = len(v)
    if n == 0: return None
    return v[math.ceil(n / 3) - 1], v[math.ceil(2 * n / 3) - 1]


def tod_class(ts):
    s = sod(ts)
    if 9 * 3600 <= s < OPEN: return "pre"
    if OPEN <= s < 15 * 3600 + 1800: return "open"
    if 15 * 3600 + 1800 <= s < 20 * 3600: return "mid"
    if 20 * 3600 <= s < CASH_CLOSE: return "close"
    return "post"


def feature(filt, series, e, cuts):
    """True (fires), False (does not), None (a needed input is missing: no entry, counted)"""
    q = series[e]
    if filt == "none": return True
    if filt.startswith("mom"):
        k, d = filt[3:].split("_"); c = series.get(e - 60 * int(k))
        if not two_sided(c): return None
        m = math.log(mid(q) / mid(c)); return m > 0 if d == "up" else m < 0
    if filt.startswith("spread_"):
        if cuts is None: return None
        sp = (q[1] - q[0]) / mid(q) * 1e4; cls = "low" if sp <= cuts[0] else ("mid" if sp <= cuts[1] else "high"); return cls == filt[7:]
    if filt.startswith("tod_"): return tod_class(e) == filt[4:]
    base = day(e) * 86400
    if filt.startswith("orb_"):
        if sod(e) < 15 * 3600 + 60: return False
        w = [mid(c) for t, c in series.items() if base + OPEN + 60 <= t <= base + 15 * 3600 and two_sided(c)]
        if not w: return None
        return mid(q) > max(w) if filt == "orb_up" else mid(q) < min(w)
    if filt.startswith("sess_"):
        w = [mid(c) for t, c in series.items() if base + OPEN + 60 <= t <= e - 60 and two_sided(c)]
        if not w: return None
        return mid(q) > max(w) if filt == "sess_high" else mid(q) < min(w)
    raise ValueError(filt)


def next_open_ts(e):
    d = day(e) + 1
    while (d + 3) % 7 >= 5: d += 1          # epoch day 0 is a Thursday; Monday = 0: Saturday 5, Sunday 6
    return d * 86400 + OPEN + 60


def horizon(e, ex):
    """the time by which a rule's exit is certain to have happened, whatever the path (Auditor B R1): the rule's own exit time; e + 1800 for TS15 and TS30 (the worst case)"""
    if ex == "TC": return day(e) * 86400 + CASH_CLOSE
    if ex == "TO": return next_open_ts(e)
    if ex in ("TS15", "TS30"): return e + 1800
    return e + 60 * int(ex[1:])


def find_exit(series, e, side, fill, ex, h):
    """-> (exit_ts, exit_price) or None (no mark)"""
    long_ = side == "long"
    def px(q): return q[0] * (1 - h) if long_ else q[1] * (1 + h)
    def at(ts):
        q = series.get(ts); return (ts, px(q)) if two_sided(q) else None
    if ex[0] == "T" and ex[1] != "S" and ex not in ("TC", "TO"): return at(e + 60 * int(ex[1:]))
    if ex in ("TS15", "TS30"):
        k = int(ex[2:]) / 1e4
        for t in sorted(series):
            if not (e < t <= e + 1800): continue
            q = series[t]
            if not two_sided(q): continue
            if long_ and (q[0] >= fill * (1 + k) or q[0] <= fill * (1 - k)): return t, px(q)
            if not long_ and (q[1] <= fill * (1 - k) or q[1] >= fill * (1 + k)): return t, px(q)
        return at(e + 1800)
    if ex == "TC":
        ts = day(e) * 86400 + CASH_CLOSE
        return None if e >= ts else at(ts)
    if ex == "TO": return at(next_open_ts(e))
    raise ValueError(ex)


def rule_trades(series, cuts, filt, side, ex, h, entry_range=(-math.inf, math.inf), boundary=None, funding=None):
    """all trades of one rule at relative haircut h. -> (trades, counts). funding: {utc day: rate of that day's 21:00 print} or None (no extract).
    A trade carries gross, funding (None when not booked) and the nets at both fees; funding-not-booked trades are labelled and kept apart."""
    out, cnt = [], {"missing_feature": 0, "no_mark": 0, "clipped": 0, "funding_not_booked": 0}
    last_e = last_exit = None
    for e in sorted(series):
        if not (entry_range[0] <= e < entry_range[1]) or not two_sided(series[e]): continue
        f = feature(filt, series, e, cuts)
        if f is None: cnt["missing_feature"] += 1; continue
        if not f: continue
        if last_e is not None and ((ex in ("TC", "TO") and e < last_exit) or (ex not in ("TC", "TO") and e < last_e + HOLD[ex])): continue
        if boundary is not None and e < boundary and horizon(e, ex) >= boundary: cnt["clipped"] += 1; continue          # R1: the clip horizon never depends on the outcome path
        q = series[e]; long_ = side == "long"
        fill = q[1] * (1 + h) if long_ else q[0] * (1 - h)
        r = find_exit(series, e, side, fill, ex, h)
        if r is None: cnt["no_mark"] += 1; continue
        xt, xp = r
        last_e, last_exit = e, xt
        gross = xp / fill - 1 if long_ else (fill - xp) / fill
        fund, booked = 0.0, True
        for d in range(day(e), day(xt) + 1):          # the 21:00 prints strictly between the entry end and the exit end
            p = d * 86400 + CASH_CLOSE
            if e < p < xt:
                rate = None if funding is None else funding.get(d)
                if rate is None: booked = False
                else: fund += rate if long_ else -rate          # paid by longs when positive, received by shorts
        t = {"e": e, "exit_ts": xt, "side": side, "fill": fill, "exit": xp, "gross": gross, "funding": fund if booked else None, "day": day(e)}
        if booked: t["net_taker"], t["net_maker"] = gross - TAKER - fund, gross - MAKER - fund
        else: cnt["funding_not_booked"] += 1
        out.append(t)
    return out, cnt


def booked(trades): return [t for t in trades if t["funding"] is not None]


def pf(v):
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    if neg == 0: return math.inf if pos > 0 else math.nan
    return pos / neg


def day_z(trades, key):
    by = {}
    for t in trades: by[t["day"]] = by.get(t["day"], 0.0) + t[key]
    v = list(by.values())
    if len(v) < 2: return None
    m = sum(v) / len(v); sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    return None if sd == 0 else m / (sd / math.sqrt(len(v)))


def stats(trades, key="net_taker"):
    b = sorted(booked(trades), key=lambda t: t["e"]); v = [t[key] for t in b]; k = len(v); h2 = k // 2
    return {"n": k, "trade_days": len(set(t["day"] for t in b)), "net": sum(v), "pf": pf(v), "h1": pf(v[:h2]), "h2": pf(v[h2:]), "z": day_z(b, key)}


def p_upper(z): return None if z is None else 0.5 * math.erfc(z / math.sqrt(2))


def gate(trades_lo, trades_hi, fee="net_taker", min_n=100, min_days=10):
    """the bar: n >= 100 booked trades, >= 10 trade days, PF >= 1.3 at the lower primary haircut and >= 1.0 at the higher"""
    a, b = stats(trades_lo, fee), stats(trades_hi, fee)
    return a["n"] >= min_n and a["trade_days"] >= min_days and a["pf"] >= 1.3 and b["pf"] >= 1.0


def bh(pvals, m, q=0.05):
    """Benjamini-Hochberg over m tests; pvals {id: p} for the tests that were scored with a p; the others count as p = 1. -> the set of ids rejected"""
    order = sorted((p, i) for i, p in pvals.items() if p is not None); k = 0
    for rank, (p, i) in enumerate(order, 1):
        if p <= rank / m * q: k = rank
    return {i for p, i in order[:k]}
