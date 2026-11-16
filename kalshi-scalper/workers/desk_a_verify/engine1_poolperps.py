"""ENGPERPS_POOL1 engine (Desk A, Nov 16 2026), built to ENGPERPS_POOL1_SPEC_NOV16.md (v3 or later). Pure functions on {ticker: {end_ts: (bid, ask)}} candles and {ticker: {print_ts: rate}} funding; imports engine1_perps (5171d7f5 and later) only for the ET clocks, usable test, mid and the print-gap booking. DEVELOPMENT only: about 6 trading days.
Rule = (signal, exit); trades pooled over names, one position per name at a time (cooldown = the previous exit end exactly)."""
import math, bisect, collections, time
import engine1_perps as P, engine1_driver as D
TAKER, MAKER = 0.0012, 0.0005; H_PRIMARY, H_SECOND = 0.0002, 0.0005
KS = (1, 2); TS_MIN = (15, 30, 60)
GAP_BP = (30, 60, 100); LOOKBACKS = (30, 60); CS = (1, 2)
def usable(c): return c is not None and 0 < c[0] < c[1]
def mid(c): return (c[0] + c[1]) / 2
def et_date(t): return time.strftime("%Y-%m-%d", time.gmtime(t + P.et_off(t)))
def day_start(t): return P.et_day0(t)
def sod(t): return P.et_secs(t)
def sigma(by, e):
    """population sd of the 60 one-minute log returns over candles ending e - 3540 .. e (consecutive usable minutes); None if fewer than 45."""
    rs = []
    for t in range(e - 3540, e + 1, 60):
        a, b = by.get(t - 60), by.get(t)
        if usable(a) and usable(b): rs.append(math.log(mid(b) / mid(a)))
    if len(rs) < 45: return None
    m = sum(rs) / len(rs); return math.sqrt(sum((x - m) ** 2 for x in rs) / len(rs))
def simulate(by, e, side, kt, ks, T, h, u, last_end=None):
    """-> (gross return, exit end, why). Long fills at ask x (1 + h) and leaves at bid x (1 - h); short fills at bid x (1 - h) and leaves at ask x (1 + h); target kt x u and stop ks x u from the fill on candle closes (long bid, short ask), stop before target, first hit else the candle ending exactly e + 60 T (must be usable)."""
    c = by.get(e)
    if not usable(c): return None, None, "entry candle unusable"
    if last_end is not None and e + 60 * T > last_end: return None, None, "no mark"
    long_ = side == "long"; fill = c[1] * (1 + h) if long_ else c[0] * (1 - h)
    tgt = fill * (1 + kt * u) if long_ else fill * (1 - kt * u); stp = fill * (1 - ks * u) if long_ else fill * (1 + ks * u)
    leave = lambda x: x[0] * (1 - h) if long_ else x[1] * (1 + h)
    for t in range(e + 60, e + 60 * T + 1, 60):
        x = by.get(t)
        if not usable(x): continue
        px = x[0] if long_ else x[1]
        hit_s = px <= stp if long_ else px >= stp; hit_t = px >= tgt if long_ else px <= tgt
        if hit_s or hit_t:
            ex = leave(x); return (ex / fill - 1 if long_ else (fill - ex) / fill), t, "stop" if hit_s else "target"
    x = by.get(e + 60 * T)
    if not usable(x): return None, None, "no mark"
    ex = leave(x); return (ex / fill - 1 if long_ else (fill - ex) / fill), e + 60 * T, "time"
def fixed_exit(by, e, x_end, side, h):
    """carry: entry at e, exit at the candle ending x_end, both usable."""
    a, b = by.get(e), by.get(x_end)
    if not usable(a) or not usable(b): return None, None, "no mark"
    long_ = side == "long"; fill = a[1] * (1 + h) if long_ else a[0] * (1 - h); ex = b[0] * (1 - h) if long_ else b[1] * (1 + h)
    return (ex / fill - 1 if long_ else (fill - ex) / fill), x_end, "time"
def funding_adj(fund, e, tx, side):
    """-> (adjustment to the gross return, flag): prints strictly between e and tx; long pays a positive rate, short receives it; a gap overlapping the hold = 'funding not booked'."""
    if fund is None: return 0.0, "funding not booked"
    ps, gaps = P._prints(fund); adj = 0.0
    for t in ps[bisect.bisect_right(ps, e):bisect.bisect_left(ps, tx)]: adj -= fund[t] if side == "long" else -fund[t]
    return adj, ("funding not booked" if any(e < b and tx > a for a, b in gaps) else None)
def trading_days(cand):
    """distinct ET dates with a candle ending 09:31 ET for at least one name."""
    ds = set()
    for by in cand.values():
        for t in by:
            if sod(t) == 9 * 3600 + 31 * 60: ds.add(et_date(t))
    return sorted(ds)
def prev_close(by, e):
    """mid of the candle ending 16:00 ET of the latest earlier ET date that has one, scanning back at most 6 days."""
    d0 = day_start(e)
    for k in range(1, 7):
        t = P.et_day0(d0 - 86400 * k + 43200) + 16 * 3600
        if t in by: return mid(by[t]) if usable(by[t]) else None            # the latest earlier date whose 16:00 ET key is PRESENT; if it is unusable the gap is skipped (the Testing Desk's R4)
    return None
def last_print(fund, before, maxage):
    if not fund: return None
    ps = sorted(fund); i = bisect.bisect_left(ps, before) - 1
    if i < 0 or before - ps[i] > maxage: return None
    return ps[i], fund[ps[i]], (fund[ps[i]] - fund[ps[i - 1]] if i >= 1 and ps[i] - ps[i - 1] <= 60 * 3600 else None)
def tercile_sets(vals):
    """vals {name: v}; N >= 3: top = first ceil(N/3) by v descending (ties by name), bottom = last ceil(N/3)."""
    if len(vals) < 3: return set(), set()
    order = sorted(vals, key=lambda n: (-vals[n], n)); k = math.ceil(len(order) / 3)
    return set(order[:k]), set(order[-k:])
def events(cand, fund):
    """-> {signal id: [(entry end, name, side)]}, all candidate entries (the cooldown is applied per rule). Signal ids: 'gap:<bp>:<follow|fade>', 'fl:<fade|follow>', 'fc:<fade|follow>', 'tr:<L>:<c>:<trend|rev>', 'carry:<A|B>' (carry carries its own exit end)."""
    ev = collections.defaultdict(list); days = trading_days(cand)
    open_end = {}; day_open_clock = {}                                  # (date, name) -> the 09:31 ET candle end; date -> that clock instant
    for nm, by in cand.items():
        for t in by:
            if sod(t) == 9 * 3600 + 31 * 60:
                day_open_clock[et_date(t)] = t
                if usable(by[t]): open_end[(et_date(t), nm)] = t
    for d in days:
        opens = sorted(n for (dd, n) in open_end if dd == d)
        for nm in opens:                                                   # opening gap
            e = open_end[(d, nm)]; pc = prev_close(cand[nm], e)
            if pc is None: continue
            g = mid(cand[nm][e]) / pc - 1
            for bp in GAP_BP:
                if round(abs(g) * 1e4, 9) >= bp:
                    up = g > 0
                    ev["gap:%d:follow" % bp].append((e, nm, "long" if up else "short")); ev["gap:%d:fade" % bp].append((e, nm, "short" if up else "long"))
        lv, ch = {}, {}                                                    # funding level and change: ALL names, each name's own latest print before the 09:31 ET clock of that date (a name with an unusable 09:31 candle is ranked but skipped at entry; the Testing Desk's R2)
        clock = day_open_clock[d]
        for nm in sorted(cand):
            lp = last_print(fund.get(nm), clock, 36 * 3600)
            if lp: lv[nm] = lp[1]
            if lp and lp[2] is not None: ch[nm] = lp[2]
        for tag, vals in (("fl", lv), ("fc", ch)):
            top, bot = tercile_sets(vals)
            for nm in top | bot:
                if (d, nm) not in open_end: continue
                e = open_end[(d, nm)]; rich = nm in top
                ev[tag + ":fade"].append((e, nm, "short" if rich else "long")); ev[tag + ":follow"].append((e, nm, "long" if rich else "short"))
    for nm, by in cand.items():                                            # trend and reversion
        for e in sorted(by):
            s = sod(e)
            if not (10 * 3600 + 31 * 60 <= s <= 15 * 3600 + 30 * 60) or not usable(by[e]): continue
            u = None
            for L in LOOKBACKS:
                b0 = by.get(e - 60 * L)
                if not usable(b0) or et_date(e - 60 * L) != et_date(e) or sod(e - 60 * L) < 9 * 3600 + 31 * 60: continue
                if u is None:
                    sg = sigma(by, e)
                    if sg is None: break
                    u = sg * math.sqrt(30)
                R = math.log(mid(by[e]) / mid(b0))
                for c in CS:
                    if abs(R) > c * u:
                        ev["tr:%d:%d:trend" % (L, c)].append((e, nm, "long" if R > 0 else "short")); ev["tr:%d:%d:rev" % (L, c)].append((e, nm, "short" if R > 0 else "long"))
    carry = collections.defaultdict(list)                                  # carry: entry at T - 30 min, the side that receives, by |last rate| rank of that day
    for nm, f in fund.items():
        for T in sorted(f):
            e = T - 1800; lp = last_print(f, e, 36 * 3600)
            if not lp or lp[1] == 0 or e not in cand.get(nm, {}): continue
            carry[et_date(e)].append((abs(lp[1]), nm, e, T, "short" if lp[1] > 0 else "long"))
    for d, lst in carry.items():
        if len({x[1] for x in lst}) < 3: continue                          # skipped if fewer than 3 distinct names
        lst.sort(key=lambda x: (-x[0], x[1], x[3])); n = len(lst)             # |rate| descending, then ticker, then print time
        for rank, (mag, nm, e, T, side) in enumerate(lst):
            if rank < math.ceil(n / 3): ev["carry:A"].append((e, nm, side, T + 1800))
            if rank < math.ceil(n / 2): ev["carry:B"].append((e, nm, side, T + 1800))
    return ev
EXITS = tuple((kt, ks, T) for kt in KS for ks in KS for T in TS_MIN)
def run_rule(cand, fund, evs, exit_, h, sig_cache):
    """-> rows [(e, name, net_taker, net_maker, hold_s, gross, flag)] at relative haircut h for ONE rule, pooled, cooldown per name = the previous exit end; carry events carry their own exit end (exit_ is None)."""
    rows, free, cnt = [], {}, collections.Counter(); lasts = {nm: max(by) for nm, by in cand.items()}
    for ev in sorted(evs, key=lambda x: (x[0], x[1])):
        e, nm, side = ev[0], ev[1], ev[2]; by = cand[nm]
        if e < free.get(nm, 0): cnt["cooldown"] += 1; continue
        if exit_ is None: g, tx, why = fixed_exit(by, e, ev[3], side, h)
        else:
            u = sig_cache(nm, e)
            if u is None: cnt["no vol"] += 1; continue
            g, tx, why = simulate(by, e, side, exit_[0], exit_[1], exit_[2], h, u, lasts[nm])
        if g is None: cnt[why] += 1; continue
        if e >= END_EPOCH or tx >= END_EPOCH: cnt["at or after 2026-11-17T00:00Z (dropped)"] += 1; continue
        adj, flag = funding_adj(fund.get(nm), e, tx, side); free[nm] = tx
        rows.append((e, nm, g + adj - 2 * TAKER, g + adj - 2 * MAKER, tx - e, g, flag))
    return rows, cnt
def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 and w > 0 else (w / l if l else float("nan"))
PRIOR_PERPS_M = 103444                 # perps passes 1 to 3 and PERPGEN (Auditor B: pass 3 tried 1,260 more, m 103,444)
END_EPOCH = 1794873600                   # 2026-11-17T00:00:00Z: a trade whose entry or exit end is at or after it is dropped (the forward days stay unread)
ALL_SIGNALS = tuple(["gap:%d:%s" % (b, m) for b in GAP_BP for m in ("follow", "fade")] + ["fl:fade", "fl:follow", "fc:fade", "fc:follow"] + ["tr:%d:%d:%s" % (L, c, m) for L in LOOKBACKS for c in CS for m in ("trend", "rev")] + ["carry:A", "carry:B"])
def stats(rows, days):
    """rows at one haircut -> figures. net = column 2 (taker) or 3 (maker)."""
    n = len(rows); xs = [r[2] for r in rows]; half = n // 2; byday = collections.defaultdict(float)
    for r in rows: byday[et_date(r[0])] += r[2]
    tot = sum(xs); top = max(byday.values()) if byday else 0.0
    return {"n": n, "per_day": (n / days if days else 0.0), "pf": pf(xs), "half1": pf(xs[:half]), "half2": pf(xs[half:]), "net_mean": (tot / n if n else 0.0), "net_total": tot,
            "top_day_share": (top / tot if tot > 0 else None), "maker_pf": pf([r[3] for r in rows]), "mean_hold_min": (sum(r[4] for r in rows) / n / 60 if n else 0.0), "mean_gross_bp": (sum(r[5] for r in rows) / n * 1e4 if n else 0.0),
            "day_z": (P.day_z([(r[0], r[2]) for r in rows]) if n else None)}
def evaluate(cand, fund, m_prior=PRIOR_PERPS_M, min_per_day=3.0):
    days = trading_days(cand); nd = len(days); ev = events(cand, fund); memo = {}
    def sig_cache(nm, e):
        k = (nm, e)
        if k not in memo:
            sg = sigma(cand[nm], e); memo[k] = None if sg is None else sg * math.sqrt(30)
        return memo[k]
    rules = []
    for sid in ALL_SIGNALS:                                            # every defined rule counts in m and is printed, whether or not it ever fires
        for x in ([None] if sid.startswith("carry") else EXITS):
            rules.append((sid, x))
    m_new = len(rules); out = []; names = sorted(cand)
    for sid, x in rules:
        r1, c1 = run_rule(cand, fund, ev.get(sid, []), x, H_PRIMARY, sig_cache); r2, c2 = run_rule(cand, fund, ev.get(sid, []), x, H_SECOND, sig_cache)
        unb = collections.Counter(r[1] for r in r1 if r[6]); ok1 = [r for r in r1 if not r[6]]; ok2 = [r for r in r2 if not r[6]]
        s1, s2 = stats(ok1, nd), stats(ok2, nd)
        gate = (s1["per_day"] >= min_per_day and s1["pf"] >= 1.3 and s1["half1"] >= 1.3 and s1["half2"] >= 1.3 and s2["pf"] >= 1.0 and s2["half1"] >= 1.0 and s2["half2"] >= 1.0
                and s2["net_total"] > 0 and (s1["top_day_share"] is None or s1["top_day_share"] <= 0.30))
        pn = collections.Counter(r[1] for r in ok1)
        out.append({"signal": sid, "exit": (None if x is None else {"kt": x[0], "ks": x[1], "T": x[2]}), "n": s1["n"], "trades_per_day": s1["per_day"], "pf_primary": s1["pf"], "pf_second": s2["pf"], "halves_primary": [s1["half1"], s1["half2"]], "halves_second": [s2["half1"], s2["half2"]],
                    "net_pct_per_trade": s1["net_mean"] * 100, "mean_hold_min": s1["mean_hold_min"], "mean_gross_bp": s1["mean_gross_bp"], "maker_pf_flag": s1["maker_pf"], "top_day_share": s1["top_day_share"], "per_name_trades": dict(sorted(pn.items())),
                    "funding_unbooked_by_name": dict(unb), "skips": dict(c1), "p": D.pval(s1["day_z"]), "gate": bool(gate),
                    "weekly_pct_of_account": {"%dx" % L: s1["net_mean"] * s1["per_day"] * 5 * L * 100 for L in (1, 2, 5)}, "liquidation_distance_pct_approx": {"%dx" % L: 100.0 / L for L in (1, 2, 5)}})
    keep = D.bh({i: o["p"] for i, o in enumerate(out) if o["gate"]}, m_new + m_prior)
    for i, o in enumerate(out): o["bh_survivor"] = i in keep
    out.sort(key=lambda o: (-o["weekly_pct_of_account"]["1x"], o["signal"], str(o["exit"])))
    return {"header": "BH m = %d (%d new rules + %d carried perps tries) before any result" % (m_new + m_prior, m_new, m_prior), "m_new": m_new, "m_total": m_new + m_prior, "trading_days": days, "names": names, "n_names": len(names),
            "label": "DEVELOPMENT, about %d trading days: no evidence at n < 100; funding cadence unverified (one print a day in the extract)" % nd, "gate_passes": sum(1 for o in out if o["gate"]), "bh_survivors": len(keep), "rules": out}
