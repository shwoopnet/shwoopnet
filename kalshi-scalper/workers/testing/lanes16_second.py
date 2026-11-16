#!/usr/bin/env python3
"""PERPS lanes 1 and 6, BUILD 2 (Testing Desk, Nov 16, 2026), blind from Desk A's spec ENGPERPS_LANES_1_6_SPEC_NOV16.md at 84abb6f06 (sha256 75bcc677...) with amendments A1 and A2 and my readings R1 to R24 (PERPSLANES16_SECOND_READINGS.md). Reuses pool1_second.py (POOL1 conventions). data {name: {end: (bid, ask)}}, funding {name: {ts: rate}}."""
import math
import pool1_second as P
import engine1_perps_second as p

BASKETS = {"semis": ("KXNVDAPERP", "KXMUPERP", "KXAMDPERP", "KXAVGOPERP", "KXAMATPERP"),
           "megatech": ("KXAAPLPERP", "KXMSFTPERP", "KXGOOGLPERP", "KXAMZNPERP", "KXMETAPERP"),
           "energy": ("KXXOMPERP", "KXCVXPERP", "KXCOPPERP")}
TAKER, MAKER, HS, EXITS = P.TAKER, P.MAKER, P.HS, P.EXITS
M_NEW = 144
SQ = math.sqrt(30)
EPS = 1e-9          # float tolerance on the through-by-one-tick comparisons (equality counts)
usable = P.usable


def tick_of(s):
    v = sorted(set(x for c in s.values() if usable(c) for x in c[:2])); d = [b - a for a, b in zip(v, v[1:]) if b - a > 0]
    return round(min(d), 9) if d else None


def kept_baskets(data, funding, baskets=None):
    names = set(P.pool_names(data, funding)); out, dropped = {}, []
    for b, ns in (baskets or BASKETS).items():
        k = tuple(n for n in ns if n in names)
        if len(k) >= 3: out[b] = k
        else: dropped.append(b)
    return out, dropped


def rs_events(data, basket, Lmin, c, mode, sig, days):
    """-> [(e, name, side, u)] sorted (e, name)"""
    out = []; ends = sorted(set(e for n in basket for e in data[n]))
    for e in ends:
        L = p.et_local_day(e)
        if L not in days or not (P.et_end(L, 10, 31) <= e <= P.et_end(L, 15, 30)): continue
        lb = e - 60 * Lmin
        if not (p.et_local_day(lb) == L and lb >= P.et_end(L, 9, 31)): continue
        if not all(usable(data[n].get(e)) and usable(data[n].get(lb)) for n in basket): continue
        R = {n: math.log(p.mid(data[n][e]) / p.mid(data[n][lb])) for n in basket}
        for n in basket:
            if (n, e) not in sig: sig[(n, e)] = P.sigma(data[n], e)
            sg = sig[(n, e)]
            if sg is None: continue
            rs = R[n] - sum(R[j] for j in basket if j != n) / (len(basket) - 1)
            if not abs(rs) > c * sg * SQ: continue
            up = rs > 0
            out.append((e, n, "long" if (up if mode == "follow" else not up) else "short", sg * SQ))
    return out


def spread_u(a, b, e):
    r = []
    for t in range(e - 3540, e + 1, 60):
        x0, x1, y0, y1 = a.get(t - 60), a.get(t), b.get(t - 60), b.get(t)
        if usable(x0) and usable(x1) and usable(y0) and usable(y1): r.append(math.log(p.mid(x1) / p.mid(y1)) - math.log(p.mid(x0) / p.mid(y0)))
    if len(r) < 45: return None
    m = sum(r) / len(r); return math.sqrt(sum((x - m) ** 2 for x in r) / len(r)) * SQ


def pair_events(data, basket, W, zin, days):
    """-> [(e, a, c, long_name, short_name, u_s)] sorted (e, a, c)"""
    out = []; ends = sorted(set(e for n in basket for e in data[n]))
    prs = [(a, c) for a in sorted(basket) for c in sorted(basket) if a < c]
    for e in ends:
        L = p.et_local_day(e)
        if L not in days or not (P.et_end(L, 10, 31) <= e <= P.et_end(L, 15, 30)): continue
        for a, c in prs:
            A, C = data[a], data[c]
            if not (usable(A.get(e)) and usable(C.get(e))): continue
            base = [math.log(p.mid(A[t]) / p.mid(C[t])) for t in range(e - 60 * W, e, 60) if usable(A.get(t)) and usable(C.get(t))]
            if len(base) < 0.8 * W: continue
            m = sum(base) / len(base); sd = math.sqrt(sum((x - m) ** 2 for x in base) / len(base))
            if not sd > 0: continue
            z = (math.log(p.mid(A[e]) / p.mid(C[e])) - m) / sd
            if not abs(z) >= zin: continue
            us = spread_u(A, C, e)
            if us is None: continue
            out.append((e, a, c, c, a, us) if z > 0 else (e, a, c, a, c, us))     # z > 0: a rich: short a, long c
    return out


def px_exit(c, long_, h): return c[0] * (1 - h) if long_ else c[1] * (1 + h)


def single_trades(data, funding, events, ex, h, col, N, ticks):
    """col TT, ME, MM -> (trades, counts, unfilled_tt_nets). events [(e, name, side, u)] in order."""
    kt, ks, T = ex; out = []; cnt = {"no_entry": 0, "blocked": 0, "no_mark": 0, "funding_not_booked": 0, "window_dropped": 0, "unfilled": 0}; unf = []
    last = {}; lastts = {n: max(data[n]) for n in data}
    for (e, n, side, u) in sorted(events, key=lambda x: (x[0], x[1])):
        s = data[n]; long_ = side == "long"
        if n in last and e < last[n]: cnt["blocked"] += 1; continue
        if not usable(s.get(e)): cnt["no_entry"] += 1; continue
        if col == "TT":
            r = P.run_exit(s, e, side, kt, ks, T, h, lastts[n], u)
            if r is None: cnt["no_mark"] += 1; continue
            xt, fill, xp = r; f0 = e; ef = xf = TAKER
        else:
            tick = ticks[n]; lim = s[e][0] if long_ else s[e][1]; f0 = None
            for t in range(e + 60, e + 60 * N + 1, 60):
                c = s.get(t)
                if usable(c) and ((long_ and c[1] <= lim - tick + EPS) or (not long_ and c[0] >= lim + tick - EPS)): f0 = t; break
            if f0 is None:
                cnt["unfilled"] += 1; r = P.run_exit(s, e, side, kt, ks, T, h, lastts[n], u)
                if r is not None:
                    xt, fill, xp = r; fd = P.fund_book(funding.get(n), e, xt, long_)
                    if fd is not None: unf.append(((xp / fill - 1 if long_ else (fill - xp) / fill) - 2 * TAKER - fd))
                continue
            fill = lim; end = f0 + 60 * T
            if end > lastts[n]: cnt["no_mark"] += 1; continue
            tgt = fill * (1 + kt * u) if long_ else fill * (1 - kt * u); stp = fill * (1 - ks * u) if long_ else fill * (1 + ks * u); xt = None
            for t in range(f0 + 60, end + 1, 60):
                c = s.get(t)
                if not usable(c): continue
                if (long_ and c[0] <= stp) or (not long_ and c[1] >= stp): xt, xp, xf = t, px_exit(c, long_, h), TAKER; break
                if col == "ME" and ((long_ and c[0] >= tgt) or (not long_ and c[1] <= tgt)): xt, xp, xf = t, px_exit(c, long_, h), TAKER; break
                if col == "MM" and ((long_ and c[0] >= tgt + tick - EPS) or (not long_ and c[1] <= tgt - tick + EPS)): xt, xp, xf = t, tgt, MAKER; break
            if xt is None:
                c = s.get(end)
                if not usable(c): cnt["no_mark"] += 1; continue
                xt, xp, xf = end, px_exit(c, long_, h), TAKER
            ef = MAKER
        if e >= P.CUTOFF or xt >= P.CUTOFF: cnt["window_dropped"] += 1; continue
        last[n] = xt; gross = xp / fill - 1 if long_ else (fill - xp) / fill; fd = P.fund_book(funding.get(n), f0, xt, long_)
        t = {"name": n, "e": e, "start": f0, "exit_ts": xt, "side": side, "gross": gross, "funding": fd, "day": p.et_local_day(e), "u": u, "legs": ((n, 1.0),)}
        if fd is None: cnt["funding_not_booked"] += 1
        else: t["net"] = gross - ef - xf - fd
        out.append(t)
    return out, cnt, unf


def pair_trades(data, funding, events, ex, h, col, N, ticks):
    kt, ks, T = ex; out = []; cnt = {"no_entry": 0, "blocked": 0, "no_mark": 0, "funding_not_booked": 0, "window_dropped": 0, "unfilled": 0}; unf = []
    last = {}; lastts = {n: max(data[n]) for n in data}
    for (e, a, c, ln, sn, us) in sorted(events, key=lambda x: (x[0], x[1], x[2])):
        if (a in last and e < last[a]) or (c in last and e < last[c]): cnt["blocked"] += 1; continue
        L, S = data[ln], data[sn]
        if not (usable(L.get(e)) and usable(S.get(e))): cnt["no_entry"] += 1; continue
        def fills(f_l, f_s, f0, tick_rule_t):
            return f_l, f_s
        def play(lfill, sfill, f0, maker_entry):
            end = f0 + 60 * T
            if end > min(lastts[ln], lastts[sn]): return None
            for t in range(f0 + 60, end + 1, 60):
                cl, cs = L.get(t), S.get(t)
                if not (usable(cl) and usable(cs)): continue
                R = (cl[0] * (1 - h) / lfill - 1) + (sfill - cs[1] * (1 + h)) / sfill
                if R <= -ks * us or R >= kt * us: return t, R
            cl, cs = L.get(end), S.get(end)
            if not (usable(cl) and usable(cs)): return None
            return end, (cl[0] * (1 - h) / lfill - 1) + (sfill - cs[1] * (1 + h)) / sfill
        if col == "TT":
            f0 = e; lfill = L[e][1] * (1 + h); sfill = S[e][0] * (1 - h); fees = 4 * TAKER
        else:
            ll, sl = L[e][0], S[e][1]; tl, ts_ = ticks[ln], ticks[sn]; fl = fs = None
            for t in range(e + 60, e + 60 * N + 1, 60):
                if fl is None and usable(L.get(t)) and L[t][1] <= ll - tl + EPS: fl = t
                if fs is None and usable(S.get(t)) and S[t][0] >= sl + ts_ - EPS: fs = t
            if fl is None or fs is None:
                cnt["unfilled"] += 1; lf, sf = L[e][1] * (1 + h), S[e][0] * (1 - h); r = play(lf, sf, e, False)
                if r is not None:
                    fdl, fds = P.fund_book(funding.get(ln), e, r[0], True), P.fund_book(funding.get(sn), e, r[0], False)
                    if fdl is not None and fds is not None: unf.append((r[1] - 4 * TAKER - fdl - fds) / 2)
                continue
            f0 = max(fl, fs); lfill, sfill = ll, sl; fees = 2 * MAKER + 2 * TAKER
        r = play(lfill, sfill, f0, col != "TT")
        if r is None: cnt["no_mark"] += 1; continue
        xt, R = r
        if e >= P.CUTOFF or xt >= P.CUTOFF: cnt["window_dropped"] += 1; continue
        last[a] = last[c] = xt
        fdl, fds = P.fund_book(funding.get(ln), f0, xt, True), P.fund_book(funding.get(sn), f0, xt, False)
        t = {"name": a + "/" + c, "e": e, "start": f0, "exit_ts": xt, "side": "pair", "gross": R, "funding": None if fdl is None or fds is None else fdl + fds, "day": p.et_local_day(e), "u": us, "legs": ((ln, 1.0), (sn, 1.0)), "R": R, "fees": fees}
        if t["funding"] is None: cnt["funding_not_booked"] += 1
        else: t["net_leg"] = R - fees - t["funding"]; t["net"] = t["net_leg"] / 2
        out.append(t)
    return out, cnt, unf


def day_p(trades):
    z = p.day_z(trades, "net"); return p.p_upper(z)


def margin(trades, lmax, fracs=(0.10, 0.25, 0.50)):
    """per fraction: mean pct of margin, worst and mean liquidation distance, names with no buffer. Single: 100 x net x f L. Pair: 100 x net_leg / (1/(f L1) + 1/(f L2)). A3: a trade that touches a name with no page max is left out of every margin figure and counted (not_shown, names), no default."""
    out = {}; shown = [t for t in trades if all(n in lmax for (n, _w) in t["legs"])]; hidden = [t for t in trades if t not in shown]
    hn = sorted(set(n for t in hidden for (n, _w) in t["legs"] if n not in lmax))
    for x in fracs:
        pct = []; liq = []; nobuf = set()
        for t in shown:
            ls = [x * lmax[n] for (n, _w) in t["legs"]]; maint = [0.0447 if "GOLD" in n else 0.045 for (n, _w) in t["legs"]]
            if t["side"] == "pair": pct.append(100 * t["net_leg"] / sum(1 / L for L in ls))
            else: pct.append(100 * t["net"] * ls[0])
            d = [1 / L - m_ for L, m_ in zip(ls, maint)]; liq.append(min(d))
            for (n, _w), dd in zip(t["legs"], d):
                if dd <= 0: nobuf.add(n)
        k = len(shown)
        out["%d%%" % round(x * 100)] = {"mean_pct_of_margin": sum(pct) / k if k else None, "worst_liq": min(liq) if liq else None, "mean_liq": sum(liq) / k if k else None, "no_buffer": sorted(nobuf), "trades_without_page_max_not_shown": len(hidden), "names_without_page_max": hn}
    return out


def interest(trades):
    hold = [t["exit_ts"] - t["start"] for t in trades if t.get("net") is not None]
    mh = sum(hold) / len(hold) if hold else None
    return {"3.5": None if mh is None else 100 * 0.035 * mh / (365 * 86400), "7": None if mh is None else 100 * 0.07 * mh / (365 * 86400)}
