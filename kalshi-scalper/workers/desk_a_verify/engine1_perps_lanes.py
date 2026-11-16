"""ENGPERPS lanes 1 and 6 engine (Desk A, Nov 16 2026), built to ENGPERPS_LANES_1_6_SPEC_NOV16.md (v2, Auditor B's rows signed) and its amendment A1 (maker scope). Pure functions on {name: {end_ts: (bid, ask)}} candles and {name: {print_ts: rate}} funding; reuses engine1_poolperps (sigma, usable, mid, clocks, funding_adj, pf, stats) and engine1_perps (clocks, day_z) unchanged. DEVELOPMENT only: about seven trading days in one regime.
LANE 1: relative strength against the basket and pairs z-scores. LANE 6: three columns for every single-name rule: TT (taker both legs), ME (maker entry, taker exit), MM (maker entry, maker target; stop and time stop leave taker). Pairs have TT and ME (both legs rest; both must fill; the position starts at the later fill) and no MM (amendment A1)."""
import math, bisect, collections
import engine1_poolperps as Q, engine1_perps as P, engine1_driver as D
TAKER, MAKER = 0.0012, 0.0005
N_FILL = (2, 5)                              # maker entry waits N candles
BASKETS = {"semis": ("KXNVDAPERP", "KXMUPERP", "KXAMDPERP", "KXAVGOPERP", "KXAMATPERP"), "megacap": ("KXAAPLPERP", "KXMSFTPERP", "KXGOOGLPERP", "KXAMZNPERP", "KXMETAPERP"), "energy": ("KXXOMPERP", "KXCVXPERP", "KXCOPPERP")}
MAINT_DEFAULT, MAINT_GOLD = 0.045, 0.0447    # maintenance: gold measured, every other name ASSUMED
RS_L, RS_C, RS_MODES = (30, 60), (1, 2), ("follow", "revert")
PAIR_W, PAIR_Z = (120, 240), (2, 3)
FRACS = (0.10, 0.25, 0.50)
def ids_rs(): return ["rs:%d:%d:%s" % (L, c, m) for L in RS_L for c in RS_C for m in RS_MODES]
def ids_pair(): return ["pair:%d:%d" % (w, z) for w in PAIR_W for z in PAIR_Z]
ALL_IDS = tuple(ids_rs() + ids_pair())
def eligible(cand, baskets=BASKETS, min_days=5, min_names=3):
    """-> ({basket: [names kept]}, [dropped lines]); a name needs candles on min_days ET dates, a basket min_names kept names."""
    kept, dropped = {}, []
    for b, names in baskets.items():
        ok = []
        for nm in names:
            by = cand.get(nm)
            d = len({Q.et_date(t) for t in by if Q.usable(by[t])}) if by else 0
            if d >= min_days: ok.append(nm)
            else: dropped.append("%s: %s has %d trading days" % (b, nm, d))
        if len(ok) >= min_names: kept[b] = ok
        else: dropped.append("%s: only %d names, basket dropped" % (b, len(ok)))
    return kept, dropped
def tick_of(by):
    """smallest positive step between distinct bid or ask prices of the name (used when the census gives none)."""
    ps = sorted({round(x, 10) for c in by.values() for x in c}); st = [b - a for a, b in zip(ps, ps[1:]) if b - a > 1e-12]
    return min(st) if st else 0.01
def rs_events(cand, kept, sigc):
    """-> {id: [(e, name, side)]}. Window 10:31 to 15:30 ET; all basket names need a usable candle at e and e - 60 L on the same ET date at or after 09:31 ET."""
    ev = collections.defaultdict(list)
    for b, names in kept.items():
        times = sorted({t for nm in names for t in cand[nm]})
        for e in times:
            s = Q.sod(e)
            if not (10 * 3600 + 31 * 60 <= s <= 15 * 3600 + 30 * 60): continue
            if not all(Q.usable(cand[nm].get(e)) for nm in names): continue
            for L in RS_L:
                t0 = e - 60 * L
                if Q.et_date(t0) != Q.et_date(e) or Q.sod(t0) < 9 * 3600 + 31 * 60 or not all(Q.usable(cand[nm].get(t0)) for nm in names): continue
                R = {nm: math.log(Q.mid(cand[nm][e]) / Q.mid(cand[nm][t0])) for nm in names}
                for nm in names:
                    rs = R[nm] - sum(R[o] for o in names if o != nm) / (len(names) - 1)
                    u = sigc(nm, e)
                    if u is None: continue
                    for c in RS_C:
                        if abs(rs) > c * u:
                            ev["rs:%d:%d:follow" % (L, c)].append((e, nm, "long" if rs > 0 else "short")); ev["rs:%d:%d:revert" % (L, c)].append((e, nm, "short" if rs > 0 else "long"))
    return ev
def spread_series(ca, cb):
    return {t: math.log(Q.mid(ca[t])) - math.log(Q.mid(cb[t])) for t in ca if t in cb and Q.usable(ca[t]) and Q.usable(cb[t])}
def pair_events(cand, kept):
    """-> {id: [(e, a, b, long_name, short_name, u_s)]}. z at e = (s_e - mean) / pop sd of s over the W minutes BEFORE e (candle ends e - 60 W .. e - 60, at least 0.8 W usable points, sd > 0); |z| >= z_in; short the rich leg (z > 0: a), long the cheap leg. u_s = pop sd of the 1-minute spread changes over the 60 minutes ending e (at least 45) x sqrt(30). Window 10:31 to 15:30 ET, same ET date as the 09:31 open for the window's first point is NOT required (the baseline may reach back to the previous day: s is a ratio and continuous)."""
    ev = collections.defaultdict(list)
    for b, names in kept.items():
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, c = names[i], names[j]; s = spread_series(cand[a], cand[c])
                for e in sorted(s):
                    sec = Q.sod(e)
                    if not (10 * 3600 + 31 * 60 <= sec <= 15 * 3600 + 30 * 60): continue
                    ch = [s[t] - s[t - 60] for t in range(e - 3540, e + 1, 60) if t in s and (t - 60) in s]
                    if len(ch) < 45: continue
                    mu = sum(ch) / len(ch); us = math.sqrt(sum((x - mu) ** 2 for x in ch) / len(ch)) * math.sqrt(30)
                    if us <= 0: continue
                    for W in PAIR_W:
                        base = [s[t] for t in range(e - 60 * W, e, 60) if t in s]
                        if len(base) < 0.8 * W: continue
                        m = sum(base) / len(base); sd = math.sqrt(sum((x - m) ** 2 for x in base) / len(base))
                        if sd <= 0: continue
                        z = (s[e] - m) / sd
                        for zin in PAIR_Z:
                            if abs(z) >= zin: ev["pair:%d:%d" % (W, zin)].append((e, a, c, (c if z > 0 else a), (a if z > 0 else c), us))
    return ev
def maker_fill(by, e, side, n_candles, tick):
    """-> (fill end, limit) or None. A long rests at the entry candle's bid and fills at the first later candle (end e + 60 .. e + 60 n) whose ASK close is at or below limit minus 1 tick; a short rests at the ask and fills when a later BID close is at or above limit plus 1 tick. Fill price = the limit, no improvement."""
    c = by.get(e)
    if not Q.usable(c): return None
    long_ = side == "long"; lim = c[0] if long_ else c[1]
    for t in range(e + 60, e + 60 * n_candles + 1, 60):
        x = by.get(t)
        if not Q.usable(x): continue
        if (long_ and x[1] <= lim - tick + 1e-12) or ((not long_) and x[0] >= lim + tick - 1e-12): return t, lim
    return None
def run_leg(by, t0, fill, side, kt, ks, T, h, u, last_end, maker_target=False, tick=0.01):
    """exit from a position that started at candle end t0 at price `fill` (no haircut applied here): -> (gross return, exit end, why, exit_is_maker). Target kt u and stop ks u from `fill` on candle closes (long: bid, short: ask), stop checked before target; a maker target rests at the target price and fills only when the close trades through by 1 tick (long: bid >= tgt + tick; short: ask <= tgt - tick), price = the target; stop and time leave taker at the bid (long) or ask (short) with haircut h; time stop at t0 + 60 T (must be usable)."""
    long_ = side == "long"
    if last_end is not None and t0 + 60 * T > last_end: return None, None, "no mark", False
    tgt = fill * (1 + kt * u) if long_ else fill * (1 - kt * u); stp = fill * (1 - ks * u) if long_ else fill * (1 + ks * u)
    leave = lambda x: x[0] * (1 - h) if long_ else x[1] * (1 + h)
    for t in range(t0 + 60, t0 + 60 * T + 1, 60):
        x = by.get(t)
        if not Q.usable(x): continue
        px = x[0] if long_ else x[1]
        if (px <= stp if long_ else px >= stp): ex = leave(x); return (ex / fill - 1 if long_ else (fill - ex) / fill), t, "stop", False
        if maker_target:
            if (px >= tgt + tick - 1e-12) if long_ else (px <= tgt - tick + 1e-12): return (tgt / fill - 1 if long_ else (fill - tgt) / fill), t, "target", True
        else:
            if (px >= tgt) if long_ else (px <= tgt): ex = leave(x); return (ex / fill - 1 if long_ else (fill - ex) / fill), t, "target", False
    x = by.get(t0 + 60 * T)
    if not Q.usable(x): return None, None, "no mark", False
    ex = leave(x); return (ex / fill - 1 if long_ else (fill - ex) / fill), t0 + 60 * T, "time", False
def taker_fill(c, side, h): return c[1] * (1 + h) if side == "long" else c[0] * (1 - h)
def single_trade(by, fund, e, side, ex, h, u, last_end, mode, n_candles=2, tick=0.01):
    """one single-name trade in column mode 'TT', 'ME' or 'MM'. -> row dict or ('skip', why). net = gross + funding - fees (entry maker 5 bp in ME and MM; exit 5 bp only for a maker target)."""
    kt, ks, T = ex
    if mode == "TT":
        c = by.get(e)
        if not Q.usable(c): return ("skip", "entry candle unusable")
        t0, fill, fin = e, taker_fill(c, side, h), TAKER
    else:
        mf = maker_fill(by, e, side, n_candles, tick)
        if mf is None: return ("skip", "maker entry not filled")
        t0, fill = mf; fin = MAKER
    g, tx, why, mk = run_leg(by, t0, fill, side, kt, ks, T, h, u, last_end, maker_target=(mode == "MM"), tick=tick)
    if g is None: return ("skip", why)
    if t0 >= Q.END_EPOCH or tx >= Q.END_EPOCH: return ("skip", "at or after 2026-11-17T00:00Z (dropped)")
    adj, flag = Q.funding_adj(fund, t0, tx, side)                 # fund = THIS name's {print ts: rate}
    return {"e": e, "t0": t0, "tx": tx, "gross": g, "adj": adj, "flag": flag, "fee": fin + (MAKER if mk else TAKER), "net": g + adj - fin - (MAKER if mk else TAKER), "why": why}
def pair_trade(cand, fund, e, lg, sh, kt, ks, T, h, us, last_end, mode, n_candles=2, ticks=None):
    """one pair trade, TT or ME. Position return R_t = (long leg return) + (short leg return) at leave marks, in units of ONE leg's notional; target R >= kt us, stop R <= -ks us, time stop T minutes after the start (both legs usable). net per pair = (R + funding of both legs - 4 fees) / 2, i.e. on the sum of both legs' notional. ME: both legs rest; both must fill within n_candles; the position starts at the later fill."""
    bl, bs = cand[lg], cand[sh]
    if mode == "TT":
        if not (Q.usable(bl.get(e)) and Q.usable(bs.get(e))): return ("skip", "entry candle unusable")
        t0, fl, fs, fin = e, taker_fill(bl[e], "long", h), taker_fill(bs[e], "short", h), TAKER
    else:
        m1 = maker_fill(bl, e, "long", n_candles, ticks[lg]); m2 = maker_fill(bs, e, "short", n_candles, ticks[sh])
        if m1 is None or m2 is None: return ("skip", "maker entry not filled (both legs must fill)")
        t0, fl, fs, fin = max(m1[0], m2[0]), m1[1], m2[1], MAKER
    if last_end is not None and t0 + 60 * T > last_end: return ("skip", "no mark")
    leave_l = lambda x: x[0] * (1 - h); leave_s = lambda x: x[1] * (1 + h)
    tx = None
    for t in range(t0 + 60, t0 + 60 * T + 1, 60):
        xl, xs = bl.get(t), bs.get(t)
        if not (Q.usable(xl) and Q.usable(xs)): continue
        R = (leave_l(xl) / fl - 1) + (fs - leave_s(xs)) / fs
        if R <= -ks * us: tx, why = t, "stop"; break
        if R >= kt * us: tx, why = t, "target"; break
    if tx is None:
        xl, xs = bl.get(t0 + 60 * T), bs.get(t0 + 60 * T)
        if not (Q.usable(xl) and Q.usable(xs)): return ("skip", "no mark")
        tx, why = t0 + 60 * T, "time"
    xl, xs = bl[tx], bs[tx]; R = (leave_l(xl) / fl - 1) + (fs - leave_s(xs)) / fs
    if t0 >= Q.END_EPOCH or tx >= Q.END_EPOCH: return ("skip", "at or after 2026-11-17T00:00Z (dropped)")
    al, f1 = Q.funding_adj(fund.get(lg), t0, tx, "long"); as_, f2 = Q.funding_adj(fund.get(sh), t0, tx, "short")
    fee = 2 * (fin + TAKER)                                              # two legs, each one entry and one taker exit
    return {"e": e, "t0": t0, "tx": tx, "gross": R, "adj": al + as_, "flag": f1 or f2, "fee": fee, "net": (R + al + as_ - fee) / 2.0, "net_units": R + al + as_ - fee, "why": why, "legs": (lg, sh)}
def maint_of(name): return MAINT_GOLD if name.startswith("KXGOLD") else MAINT_DEFAULT
def margin_view(rows, levmax, names_of):
    """price terms and % of margin at 10%, 25%, 50% of each name's page max leverage; liquidation distance = 1 / leverage minus maintenance (assumed), 'no buffer' when it is not positive. rows: [(net in units of ONE leg's notional, [legs])] (a single name is one leg); % of margin = net / sum of the legs' margins (1 / (f L) each)."""
    out = {}
    for f in FRACS:
        tot, n = 0.0, 0; dist = []
        for net, legs in rows:
            margin = sum(1.0 / (f * levmax(l)) for l in legs); tot += net / margin; n += 1
            dist.append(min(1.0 / (f * levmax(l)) - maint_of(l) for l in legs))
        out["%d%%" % round(f * 100)] = {"mean_pct_of_margin_per_trade": (tot / n * 100 if n else None), "mean_liq_distance_pct": (sum(dist) / n * 100 if n else None), "worst_liq_distance_pct": (min(dist) * 100 if n else None), "no_buffer_names": sorted({l for _, legs in rows for l in legs if 1.0 / (f * levmax(l)) - maint_of(l) <= 0}), "label": "maintenance assumed (gold 4.47% measured, 4.5% elsewhere); page maxima from the census"}
    return out
def interest_credit(rows):
    """labelled CREDIT, never in the gate: % of margin per trade = APY x hold / 365 days, at 3.5% and 7%. rows: hold seconds."""
    if not rows: return None
    mean = sum(rows) / len(rows)
    return {"mean_hold_min": mean / 60, "credit_pct_of_margin_per_trade_at_3.5pct_apy": 3.5 * mean / (365 * 86400), "credit_pct_of_margin_per_trade_at_7pct_apy": 7.0 * mean / (365 * 86400), "label": "credit, outside the gate; the owner's terms are a placeholder"}

EXITS = Q.EXITS
COLUMNS_SINGLE = (("TT", 2), ("ME", 2), ("ME", 5), ("MM", 2), ("MM", 5)); COLUMNS_PAIR = (("TT", 2), ("ME", 2), ("ME", 5))
def col_name(mode, n): return mode if mode == "TT" else "%s%d" % (mode, n)
def gate(s1, s2, min_per_day=3.0):
    return bool(s1["per_day"] >= min_per_day and s1["pf"] >= 1.3 and s1["half1"] >= 1.3 and s1["half2"] >= 1.3 and s2["pf"] >= 1.0 and s2["half1"] >= 1.0 and s2["half2"] >= 1.0 and s2["net_total"] > 0 and (s1["top_day_share"] is None or s1["top_day_share"] <= 0.30))
def run_column(cand, fund, evs, ex, mode, ncand, h, sigc, ticks, pair, lasts):
    """-> (rows [(e, label, net, net, hold s, gross, flag, units, legs)], skip counter, signals, filled signals, missed-taker nets). One rule, one column, one haircut; one position per name at a time (cooldown = the previous exit end exactly)."""
    rows, free, cnt, sig, filled, missed = [], {}, collections.Counter(), 0, 0, []
    for ev in sorted(evs, key=lambda x: (x[0], x[1], x[2])):
        e = ev[0]
        if pair:
            _, a, b, lg, sh, us = ev; names = (a, b)
            if any(e < free.get(n, 0) for n in names): cnt["cooldown"] += 1; continue
            sig += 1; r = pair_trade(cand, fund, e, lg, sh, ex[0], ex[1], ex[2], h, us, min(lasts[a], lasts[b]), mode, ncand, ticks)
            legs = (lg, sh); label = lg + "|" + sh
        else:
            nm, side = ev[1], ev[2]; names = (nm,)
            if e < free.get(nm, 0): cnt["cooldown"] += 1; continue
            u = sigc(nm, e)
            if u is None: cnt["no vol"] += 1; continue
            sig += 1; r = single_trade(cand[nm], fund.get(nm), e, side, ex, h, u, lasts[nm], mode, ncand, ticks[nm]); legs = (nm,); label = nm
        if isinstance(r, tuple):
            cnt[r[1]] += 1
            if r[1].startswith("maker entry not filled"):
                t = pair_trade(cand, fund, e, lg, sh, ex[0], ex[1], ex[2], h, us, min(lasts[a], lasts[b]), "TT") if pair else single_trade(cand[nm], fund.get(nm), e, side, ex, h, u, lasts[nm], "TT", 2, ticks[nm])
                if not isinstance(t, tuple): missed.append(t["net"])
            continue
        filled += 1
        for n in names: free[n] = r["tx"]
        units = r.get("net_units", r["net"])
        rows.append((r["e"], label, r["net"], r["net"], r["tx"] - r["t0"], r["gross"], r["flag"], units, legs))
    return rows, cnt, sig, filled, missed
def evaluate_lanes(cand, fund, levmax, m_carried, min_per_day=3.0, baskets=BASKETS, min_days=5):
    """-> report. cand: {name: {end: (bid, ask)}} for ALL names; fund: {name: {ts: rate}}; levmax(name) -> page max leverage; m_carried = the Head's single carried m (6,290,660 today) before the 144 new rules."""
    kept, dropped = eligible(cand, baskets, min_days); names = sorted({n for v in kept.values() for n in v}); sub = {n: cand[n] for n in names}
    days = Q.trading_days(sub); nd = len(days); memo = {}
    def sigc(nm, e):
        k = (nm, e)
        if k not in memo:
            sg = Q.sigma(cand[nm], e); memo[k] = None if sg is None else sg * math.sqrt(30)
        return memo[k]
    ticks = {n: tick_of(cand[n]) for n in names}; lasts = {n: max(sub[n]) for n in names}
    evs = rs_events(sub, kept, sigc); pev = pair_events(sub, kept); out = []
    for sid in ALL_IDS:
        pair = sid.startswith("pair"); e_list = pev.get(sid, []) if pair else evs.get(sid, [])
        for ex in EXITS:
            cols = {}
            for mode, nn in (COLUMNS_PAIR if pair else COLUMNS_SINGLE):
                res = {}
                for h in (Q.H_PRIMARY, Q.H_SECOND): res[h] = run_column(sub, fund, e_list, ex, mode, nn, h, sigc, ticks, pair, lasts)
                r1 = [r for r in res[Q.H_PRIMARY][0] if not r[6]]; r2 = [r for r in res[Q.H_SECOND][0] if not r[6]]
                s1, s2 = Q.stats(r1, nd), Q.stats(r2, nd); g = gate(s1, s2, min_per_day)
                _, cnt, sg, fl, missed = res[Q.H_PRIMARY]
                cols[col_name(mode, nn)] = {"n": s1["n"], "trades_per_day": s1["per_day"], "pf_primary": s1["pf"], "pf_second": s2["pf"], "halves_primary": [s1["half1"], s1["half2"]], "halves_second": [s2["half1"], s2["half2"]], "top_day_share": s1["top_day_share"], "gate": g, "p": D.pval(s1["day_z"]),
                    "price_terms": {"net_bp_per_trade": s1["net_mean"] * 1e4, "mean_gross_bp": s1["mean_gross_bp"]}, "signals": sg, "filled": fl, "fill_rate": (fl / sg if sg else None), "unfilled_taker_mean_net_bp": (sum(missed) / len(missed) * 1e4 if missed else None), "skips": dict(cnt),
                    "margin_view": margin_view([(r[7], r[8]) for r in r1], levmax, None), "interest_credit": interest_credit([r[4] for r in r1]), "funding_unbooked": sum(1 for r in res[Q.H_PRIMARY][0] if r[6])}
            tt = cols["TT"]["gate"]
            for k, c in cols.items(): c["maker_only_flag"] = bool(k != "TT" and c["gate"] and not tt)
            out.append({"signal": sid, "exit": {"kt": ex[0], "ks": ex[1], "T": ex[2]}, "columns": cols})
    m_new = len(ALL_IDS) * len(EXITS)
    keep = D.bh({i: o["columns"]["TT"]["p"] for i, o in enumerate(out) if o["columns"]["TT"]["gate"]}, m_carried + m_new)
    for i, o in enumerate(out): o["bh_survivor_taker"] = i in keep
    return {"header": "BH m = %d (carried %d + %d new rules: 96 relative strength + 48 pairs) before any result" % (m_carried + m_new, m_carried, m_new), "m_new": m_new, "kept_baskets": kept, "dropped": dropped, "trading_days": days, "ticks": ticks, "label": "development; first week, one regime (about %d trading days); the same seven days as POOL1 and the ENGINE1 perps passes; no evidence at n < 100" % nd, "rules": out,
            "maker_note": "fill model: through-by-1-tick on candle closes, a lower bound on fills; a maker-only pass is flagged and not counted; interest is a credit outside the gate; amendment A1: pairs have TT and ME only (both legs must fill)"}
