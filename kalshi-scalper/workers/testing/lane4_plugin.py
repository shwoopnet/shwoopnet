#!/usr/bin/env python3
"""PERPSLANE4 plugin, FIRST BUILD (Testing Desk, Nov 16, 2026): gaps and sessions on the perps archive. Pure functions. Written from LANE4_HAND_CASE.md and PERPSLANE4_DEFINITIONS.md. Reuses engine1_perps_second's clock and funding booking (16b met on 10,080 lines).
data[name] = {end_ts: (bid, ask)}; funding[name] = {ts: rate}; under[name] = {ET day number: (u_open, u_prev)}."""
import math
import engine1_perps_second as p

H = 3600
CUT = 1794873600          # 2026-11-17T00:00:00Z: nothing at or after it is used
HS = (0.0002, 0.0005); STRESS = (0.001, 0.002)
FEES = {"net_taker": 0.0024, "net_maker": 0.0010}          # round trip (12 and 5 bps a side)
M_NEW = 101


HOLIDAYS = frozenset(__import__("calendar").timegm((y, mo, d, 12, 0, 0)) // 86400 for (y, mo, d) in ((2026, 11, 26), (2026, 12, 25)))          # full US cash closures: not an ET weekday for the rules (the day number is the UTC day of that midday; ET local day = the same number at midday)
EARLY = frozenset(__import__("calendar").timegm((y, mo, d, 12, 0, 0)) // 86400 for (y, mo, d) in ((2026, 11, 27), (2026, 12, 24)))          # early 13:00 ET closes: no B2 or B3 on those days


def weekday(L): return (L + 3) % 7          # epoch day 0 is a Thursday; Monday = 0
def is_session(L): return weekday(L) < 5 and L not in HOLIDAYS
def next_weekday(L):
    L += 1
    while not is_session(L): L += 1
    return L
def et_end(L, hh, mm): return p.day_start_of_local(L) + hh * H + mm * 60
def usable(q): return p.two_sided(q)
def mid(q): return p.mid(q)


def rules():
    r = []
    for cls in ("weekend", "weeknight"):
        for side in ("long", "short"): r.append(("A", cls, side))
    for cls in ("mon", "tuefri"):
        for thr in (40, 100):
            for mode in ("follow", "fade"):
                for ex in ("T30", "T60", "TC"): r.append(("A2", cls, thr, mode, ex))
    for n in (5, 15, 30):
        for thr in (20, 40):
            for mode in ("follow", "fade"):
                for ex in ("T30", "T60", "TC"): r.append(("B1", n, thr, mode, ex))
    for thr in (20, 40):
        for mode in ("follow", "fade"):
            for ex in ("T1601", "TO"): r.append(("B2", thr, mode, ex))
    for side in ("long", "short"): r.append(("B3", side))
    for x in (60, 30, 15):
        for y in (15, 30, 60):
            for side in ("long", "short", "receive"): r.append(("C", x, y, side))
    return r
assert len(rules()) == M_NEW


def ge9(x, lim): return round(x, 9) >= round(lim, 9)


def exit_ts(kind, L, e):
    if kind == "T30": return e + 1800
    if kind == "T60": return e + 3600
    if kind == "TC": return et_end(L, 16, 0)
    if kind == "T1601": return et_end(L, 16, 1)
    if kind == "TO": return et_end(next_weekday(L), 9, 31)
    raise ValueError(kind)


def schedule_T(funding):
    """the funding window's T (Auditor B): the previous print's timestamp plus 24 h, per name, never the day's own print; one T per print of the extract (the one after the last print included)"""
    return [t + 86400 for t in sorted(funding or {})]


def schedule_misses(funding):
    """information: the number of days on which the actual next print differed from the schedule T"""
    ps = sorted(funding or {}); return sum(1 for a, b in zip(ps, ps[1:]) if b != a + 86400)


def candidates(rule, name, s, funding, under):
    """-> list of (e, x, long_, day) signal-true candidates of one rule for one name, in entry order (before cooldown and marks)"""
    out = []; k = rule[0]
    days = sorted(set(p.et_local_day(t) for t in s))
    if k == "A":
        for L in days:
            if not is_session(L): continue
            if (weekday(L) == 4) != (rule[1] == "weekend"): continue
            out.append((et_end(L, 16, 0), et_end(next_weekday(L), 9, 31), rule[2] == "long", L))
    elif k == "A2":
        _, cls, thr, mode, ex = rule
        for L in days:
            if not is_session(L) or (weekday(L) == 0) != (cls == "mon"): continue
            E, P25 = s.get(et_end(L, 9, 31)), s.get(et_end(L, 9, 25)); u = (under.get(name) or {}).get(L)
            if u is None or u[0] is None or u[1] is None or u[1] <= 0 or not (usable(E) and usable(P25)): continue
            Lp = L - 1
            while Lp >= days[0] and et_end(Lp, 16, 0) not in s: Lp -= 1
            if Lp < days[0]: continue
            PP = s[et_end(Lp, 16, 0)]
            if not usable(PP): continue
            g = (u[0] / u[1] - 1) - (mid(P25) / mid(PP) - 1); half = ((E[1] - E[0]) / 2) / mid(E)
            if not (round(abs(g), 9) > round(2 * half, 9) and ge9(abs(g) * 1e4, thr)): continue
            up = g > 0; long_ = up if mode == "follow" else not up
            e = et_end(L, 9, 31); out.append((e, exit_ts(ex, L, e), long_, L))
    elif k == "B1":
        _, n, thr, mode, ex = rule
        for L in days:
            if not is_session(L): continue
            O, En = s.get(et_end(L, 9, 31)), s.get(et_end(L, 9, 31) + 60 * n)
            if not (usable(O) and usable(En)): continue
            m = mid(En) / mid(O) - 1
            if not ge9(abs(m) * 1e4, thr): continue
            up = m > 0; long_ = up if mode == "follow" else not up
            e = et_end(L, 9, 31) + 60 * n; out.append((e, exit_ts(ex, L, e), long_, L))
    elif k == "B2":
        _, thr, mode, ex = rule
        for L in days:
            if not is_session(L) or L in EARLY: continue
            A, B = s.get(et_end(L, 15, 0)), s.get(et_end(L, 15, 30))
            if not (usable(A) and usable(B)): continue
            m = mid(B) / mid(A) - 1
            if not ge9(abs(m) * 1e4, thr): continue
            up = m > 0; long_ = up if mode == "follow" else not up
            out.append((et_end(L, 15, 30), exit_ts(ex, L, 0), long_, L))
    elif k == "B3":
        for L in days:
            if not is_session(L) or L in EARLY: continue
            out.append((et_end(L, 15, 30), et_end(L, 16, 1), rule[1] == "long", L))
    elif k == "C":
        _, x, y, side = rule
        for T in schedule_T(funding):
            e, xt = T - 60 * x, T + 60 * y
            prior = [t for t in funding if t < e]
            if side == "receive":
                if not prior: continue
                r = funding[max(prior)]
                if r == 0: continue
                long_ = r < 0
            else: long_ = side == "long"
            out.append((e, xt, long_, p.et_local_day(e)))
    return sorted(out, key=lambda c: (c[0], c[1]))


def score(rule, data, funding, under, h):
    """-> (trades, counts) pooled over names for one rule at haircut h; a trade: name, e, exit_ts, gross, funding, day, nets"""
    out, cnt = [], {"blocked": 0, "no_mark": 0, "funding_not_booked": 0, "boundary": 0}
    for name in sorted(data):
        s = data[name]; f = (funding or {}).get(name); free = -math.inf
        for (e, x, long_, L) in candidates(rule, name, s, f, under):
            if e < free: cnt["blocked"] += 1; continue
            q, w = s.get(e), s.get(x)
            if not (usable(q) and usable(w)): cnt["no_mark"] += 1; continue
            free = x
            if e >= CUT or x >= CUT: cnt["boundary"] += 1; continue
            fill = q[1] * (1 + h) if long_ else q[0] * (1 - h); xp = w[0] * (1 - h) if long_ else w[1] * (1 + h)
            gross = xp / fill - 1 if long_ else (fill - xp) / fill
            fd = p.funding_for(f, e, x, long_); t = {"name": name, "e": e, "exit_ts": x, "side": "long" if long_ else "short", "gross": gross, "funding": fd, "day": L}
            if fd is None: cnt["funding_not_booked"] += 1
            else:
                for k, fee in FEES.items(): t[k] = gross - fee - fd
            out.append(t)
    return out, cnt


def trading_days(data):
    ds = set()
    for s in data.values():
        for t in s:
            L = p.et_local_day(t)
            if t == et_end(L, 9, 31) and t < CUT and usable(s[t]): ds.add(L)
    return len(ds)


def pf(v): return p.pf(v)


def half_ok(tr, key, lim):
    v = [t[key] for t in sorted(tr, key=lambda t: (t["e"], t["name"]))]; k = len(v) // 2
    a, b = pf(v[:k]), pf(v[k:])
    return (not math.isnan(a)) and a >= lim and (not math.isnan(b)) and b >= lim


def gate(lo, hi, key, ndays):
    """lo, hi: booked trades at the primary haircuts 0.0002 and 0.0005 of one rule (each its own set); the bar of the spec"""
    if not lo or not hi or ndays == 0: return False
    a = [t[key] for t in lo]; b = [t[key] for t in hi]; days = set(t["day"] for t in lo)
    f1, f2 = pf(a), pf(b)
    return (len(a) >= 100 and len(days) >= 10 and len(a) / ndays >= 3 and (not math.isnan(f1)) and f1 >= 1.3 and half_ok(lo, key, 1.0) and (not math.isnan(f2)) and f2 >= 1.0 and half_ok(hi, key, 1.0))


def run(data, funding, under, m_carried=0):
    """-> {rule: {fee key: {n, days, per_day, pf_lo, pf_hi, h1, h2, z, p, gate}, counts}}, survivors per fee after BH"""
    nd = trading_days(data); out = {}; pv = {k: {} for k in FEES}
    for rule in rules():
        lo, cnt = score(rule, data, funding, under, HS[0]); hi, _ = score(rule, data, funding, under, HS[1]); blo, bhi = p.booked(lo), p.booked(hi)
        res = {"counts": cnt}
        for key in FEES:
            st = p.stats(blo, key); sb = p.stats(bhi, key)
            ok = gate(blo, bhi, key, nd); pz = p.p_upper(st["z"])
            res[key] = {"n": st["n"], "days": st["trade_days"], "per_day": (st["n"] / nd) if nd else 0.0, "pf_lo": st["pf"], "pf_hi": sb["pf"], "h1": st["h1"], "h2": st["h2"], "z": st["z"], "p": pz, "gate": ok}
            if pz is not None: pv[key][rule] = pz
        out[rule] = res
    mt = m_carried + M_NEW; surv = {key: sorted(r for r in p.bh(pv[key], mt) if out[r][key]["gate"]) for key in FEES}
    return out, surv, nd
