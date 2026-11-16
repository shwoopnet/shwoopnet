"""ENGINE1 perps block (Desk A, Nov 16 2026), built to ENGINE1_PERPS_HAND_CASE_NOV16.md. Pure functions on one ticker's candles [(end, bid, ask, last, vol, oi)]. Fee 12 bps a leg ASSUMED. Upper bound, not fill-checked, funding not booked."""
import math, time, collections, calendar
FEE = 0.0012; FEE_MAKER = 0.0005; HAIRCUTS = (0.0002, 0.0005); STRESS = (0.001, 0.002); COOLDOWN = 1800      # fees per side, ASSUMED; haircuts relative to price (0.1% and 0.2%)
MOMS = (1, 3, 5, 15); TODS = ("pre", "open", "mid", "close", "post")
FILTERS = (None,) + tuple(("mom%d" % k, c) for k in MOMS for c in ("up", "down")) + tuple(("spread", c) for c in ("low", "mid", "high")) + tuple(("tod", c) for c in TODS) + (("orb", "up"), ("orb", "down"), ("sess", "high"), ("sess", "low"))
EXITS = ("T3", "T10", "T15", "T30", "TS15", "TS30", "T60", "T240", "TC", "TO"); SIDES = ("long", "short")
RULES_PER_TICKER = len(FILTERS) * len(SIDES) * len(EXITS)
DST_START = calendar.timegm((2026, 3, 8, 7, 0, 0)); DST_END = calendar.timegm((2026, 11, 1, 6, 0, 0))     # US Eastern DAYLIGHT time (UTC-4) from DST_START to DST_END, else standard (UTC-5); 2026 only
def et_off(ts): return -4 * 3600 if DST_START <= ts < DST_END else -5 * 3600
def et_secs(ts): return (ts + et_off(ts)) % 86400
def et_day0(ts): return ts - et_secs(ts)                         # the UTC epoch of the ET midnight that starts ts's ET day
def next_et_day0(ts):
    d = et_day0(ts); return et_day0(d + 36 * 3600)           # noon of the next ET day lies safely inside it, whatever the DST step
def ok(c): return c is not None and c[1] is not None and c[2] is not None and 0 < c[1] < c[2]
def mid(c): return (c[1] + c[2]) / 2
def tod(end):
    s = et_secs(end)
    if 4 * 3600 <= s < 9 * 3600 + 1800: return "pre"
    if 9 * 3600 + 1800 <= s < 10 * 3600 + 1800: return "open"
    if 10 * 3600 + 1800 <= s < 15 * 3600: return "mid"
    if 15 * 3600 <= s < 16 * 3600: return "close"
    return "post"
def spread_cuts(vals):
    v = sorted(vals); n = len(v); return v[math.ceil(n / 3) - 1], v[math.ceil(2 * n / 3) - 1]
def feature_ok(by, e, filt, cuts):
    """True/False, or None when a needed candle is missing."""
    if filt is None: return True
    name, klass = filt; c = by[e]
    if name == "tod": return tod(e) == klass
    if name in ("orb", "sess"):
        day0 = et_day0(e); lo_t = day0 + 9 * 3600 + 31 * 60                          # candles ending 09:31 ET ...
        if name == "orb":
            if et_secs(e) < 10 * 3600 + 60: return None                             # the entry must end at 10:01 ET or later
            win = [by[t] for t in range(lo_t, day0 + 10 * 3600 + 1, 60) if t in by]  # ... to 10:00 ET
            if not win: return None
            hi, lo = max(mid(w) for w in win), min(mid(w) for w in win)
            return mid(c) > hi if klass == "up" else mid(c) < lo
        win = [by[t] for t in range(lo_t, e, 60) if t in by]                        # candles ending 09:31 ET up to e - 60
        if not win: return None
        return mid(c) > max(mid(w) for w in win) if klass == "high" else mid(c) < min(mid(w) for w in win)
    if name == "spread":
        if cuts is None: return None
        x = (c[2] - c[1]) / mid(c) * 1e4; return ("low" if x <= cuts[0] else "mid" if x <= cuts[1] else "high") == klass
    k = int(name[3:]); p = by.get(e - 60 * k)
    if not ok(p): return None
    r = math.log(mid(c) / mid(p)); return (r > 0 and klass == "up") or (r < 0 and klass == "down")
def exit_time(e, exit_):
    """The candle end at which a time exit sells (TS exits: 1800 s horizon), or None when there is none."""
    if exit_ in ("TS15", "TS30"): return e + COOLDOWN
    if exit_ == "TC":
        t = et_day0(e) + 16 * 3600                                    # the candle ending 16:00 ET the same ET day
        return t if t > e else None
    if exit_ == "TO":
        d = next_et_day0(e)
        while time.gmtime(d + et_off(d) + 12 * 3600).tm_wday >= 5: d = next_et_day0(d)       # the next ET weekday
        return d + 9 * 3600 + 31 * 60                                  # its 09:31 ET candle
    return e + 60 * int(exit_[1:])
def funding_times(e, tx):
    """Daily funding prints at 16:00 ET (21:00 UTC under EST, 20:00 UTC under EDT) strictly between the entry candle end and the exit candle end (an exit AT the print pays nothing)."""
    out, d = [], et_day0(e)
    while d + 16 * 3600 < tx:
        t = d + 16 * 3600
        if t > e: out.append(t)
        d = next_et_day0(d)
    return out
def hold_of(e, exit_):
    t = exit_time(e, exit_); return COOLDOWN if t is None else max(COOLDOWN, t - e)
def trade_full(by, e, side, exit_, h, funding=None):
    """-> (gross return, reason, hold seconds) or (None, 'no mark', 0). Candles in `by` are keyed by end_ts. The fee is applied by the caller."""
    c = by[e]; long_ = side == "long"
    fill = c[2] * (1 + h) if long_ else c[1] * (1 - h)
    def leave(x): return x[1] * (1 - h) if long_ else x[2] * (1 + h)
    ex, why, hold = None, None, 0
    if exit_ in ("TS15", "TS30"):
        k = (15 if exit_ == "TS15" else 30) / 1e4
        for t in range(e + 60, e + COOLDOWN + 1, 60):
            x = by.get(t)
            if not ok(x): continue
            if long_: hit_t, hit_s = x[1] >= fill * (1 + k), x[1] <= fill * (1 - k)
            else: hit_t, hit_s = x[2] <= fill * (1 - k), x[2] >= fill * (1 + k)
            if hit_t or hit_s: ex, why, hold = leave(x), "target" if hit_t else "stop", t - e; break
        tx = e + COOLDOWN
    else: tx = exit_time(e, exit_)
    if ex is None:
        x = by.get(tx) if tx is not None else None
        if not ok(x): return None, "no mark", 0, None
        ex, why, hold = leave(x), "time", tx - e
    gross = (ex / fill - 1) if long_ else (fill - ex) / fill
    flag = None
    for t in funding_times(e, e + hold):                 # a positive rate: longs pay shorts; the rate is a fraction of notional
        if funding is not None and t in funding: gross -= funding[t] if long_ else -funding[t]
        else: flag = "funding not booked"
    return gross, why, hold, flag
def trade(by, e, side, exit_, h):
    """-> (net return at the taker fee, reason) or (None, reason); kept for the hand case."""
    g, why, hold, flag = trade_full(by, e, side, exit_, h)
    return (None, why) if g is None else (g - 2 * FEE, why)
def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 and w > 0 else (w / l if l else float("nan"))
def day_z(rows):
    by = collections.defaultdict(float)
    for t, x in rows: by[time.strftime("%Y-%m-%d", time.gmtime(t))] += x
    v = list(by.values()); n = len(v)
    if n < 2: return None
    m = sum(v) / n; sd = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1))
    return None if sd == 0 else m / (sd / math.sqrt(n))
def run_rule(candles, filt, side, exit_, h, cuts, lo=None, hi=None, boundary=None, funding=None):
    """All entries of one rule with the 1800 s cooldown; lo and hi bound the entry end (inclusive lo, exclusive hi). -> rows [(e, net)], counters."""
    by = {c[0]: c for c in candles if ok(c)}; rows, cnt, last = [], collections.Counter(), None
    for e in sorted(by):
        if (lo is not None and e < lo) or (hi is not None and e >= hi): continue
        if last is not None and e < last: continue                                  # last = the previous entry's exit time (hold)
        if boundary is not None and e + hold_of(e, exit_) >= boundary: cnt["exit crosses the boundary"] += 1; continue          # (Auditor B) SEARCH never touches VALIDATE prices
        f = feature_ok(by, e, filt, cuts)
        if f is None: cnt["missing feature candle"] += 1; continue
        if not f: continue
        g, why, hold, flag = trade_full(by, e, side, exit_, h, funding)
        if g is None: cnt[why] += 1; continue
        rows.append((e, g, hold, flag)); cnt[why] += 1; last = e + hold_of(e, exit_)
        if flag: cnt[flag] += 1
    return rows, cnt
def days(rows): return len({time.strftime('%Y-%m-%d', time.gmtime(r[0])) for r in rows})
def stats(rows, fee=FEE):
    """rows [(e, gross, hold)] -> stats at a per side fee; also the average hold (minutes) and the average gross move."""
    unbooked = sum(1 for r in rows if len(r) > 3 and r[3]); rows = [r for r in rows if not (len(r) > 3 and r[3])]
    nets = [(r[0], r[1] - 2 * fee) for r in rows]; xs = [x for _, x in nets]; half = len(xs) // 2
    return {"n": len(xs), "pf": pf(xs), "half1": pf(xs[:half]), "half2": pf(xs[half:]), "net": sum(xs), "day_z": day_z(nets), "avg_hold_min": (sum(r[2] for r in rows) / len(rows) / 60) if rows else None, "avg_gross_bp": (sum(r[1] for r in rows) / len(rows) * 1e4) if rows else None, "funding_unbooked": unbooked, "evidence": "ok" if len(xs) >= 100 else "no evidence at n = %d" % len(xs)}
import engine1_split as S
ALPHA = 0.05; MIN_N = 100; PF1 = 1.3; PF2 = 1.0; MIN_DAYS = 10     # trade days needed in SEARCH and in VALIDATE (Auditor B): fewer prints 'insufficient days' and the rule cannot pass
def pval(z): return 0.5 * math.erfc(z / math.sqrt(2)) if z is not None else 1.0
def short(t): return t[2:] if t.startswith("KX") else t
def passes(a, b): return a["n"] >= MIN_N and a["pf"] >= PF1 and b["pf"] >= PF2
def run_all(perps, funding=None, m_prior=0, last_search=None):
    """perps: {ticker: candles}. SEARCH then VALIDATE by engine1_split dates of the entry candle, spread cuts from SEARCH entries only, every rule scored under the TAKER fee (the gate) and the MAKER fee (flagged, resting fills assumed), BH over m = every rule tried. Perps block only. funding: {ticker: {print ts: rate}} or None (then every trade crossing a 4 pm ET print is labelled "funding not booked" and left out of the gate); m_prior: tries already spent (read 1's 504) that stay in the BH denominator."""
    ls = last_search or S.LAST_SEARCH                       # {short ticker: last SEARCH date}; pass 3 supplies its own (2026-09-30)
    phase = lambda key, ts: "search" if time.strftime("%Y-%m-%d", time.gmtime(ts)) <= ls[key] else "validate"
    rep = {"m_prior": m_prior, "funding_unbooked_trades": 0, "label": "perps block: upper bound, not fill-checked; taker fee 12 bps a side and maker fee 5 bps a side, both ASSUMED (not confirmed); relative haircuts 0.02% and 0.05% a side (stress line 0.1% and 0.2%); funding not booked; a maker-only pass assumes resting fills, fill rate unknown; information for the forward shadow only", "tried": 0, "cells_n100_search": 0, "search_bar_stress_taker": 0, "search_bar_taker": 0, "search_bar_maker": 0, "maker_only": 0, "insufficient_days": 0, "validate_bar_passes": 0, "validate_passes": 0, "survivors": [], "maker_only_list": [], "no_split_constant": [], "by_ticker": {}}
    m = 0; cand = []; mk_only = []
    for tk, cs in perps.items():
        key = short(tk)
        if key not in ls: rep["no_split_constant"].append(tk); continue
        good = [c for c in cs if ok(c)]
        sp = [(c[2] - c[1]) / mid(c) * 1e4 for c in good if phase(key, c[0]) == "search"]
        cuts = spread_cuts(sp) if sp else None
        first_val = min([c[0] for c in good if phase(key, c[0]) == "validate"] or [10 ** 12])
        fund = (funding or {}).get(tk)
        bt = {"cells_n100": 0, "bar_taker": 0, "bar_maker": 0, "bar_stress_taker": 0, "search_days_max": 0}
        for f in FILTERS:
            for side in SIDES:
                for x in EXITS:
                    m += 1
                    r1, _ = run_rule(good, f, side, x, HAIRCUTS[0], cuts, hi=first_val, boundary=first_val, funding=fund); r2, _ = run_rule(good, f, side, x, HAIRCUTS[1], cuts, hi=first_val, boundary=first_val, funding=fund)
                    rep["funding_unbooked_trades"] += stats(r1, FEE)["funding_unbooked"]
                    a_t, b_t = stats(r1, FEE), stats(r2, FEE); a_m, b_m = stats(r1, FEE_MAKER), stats(r2, FEE_MAKER)
                    bt["search_days_max"] = max(bt["search_days_max"], days(r1))
                    if a_t["n"] >= MIN_N: bt["cells_n100"] += 1
                    pt, pm = passes(a_t, b_t), passes(a_m, b_m)
                    bt["bar_taker"] += pt; bt["bar_maker"] += pm
                    s1, _ = run_rule(good, f, side, x, STRESS[0], cuts, hi=first_val, boundary=first_val, funding=fund); s2, _ = run_rule(good, f, side, x, STRESS[1], cuts, hi=first_val, boundary=first_val, funding=fund)
                    bt["bar_stress_taker"] += passes(stats(s1, FEE), stats(s2, FEE))                # the old 0.1% and 0.2% lines, a stress line only
                    if (pt or pm) and days(r1) < MIN_DAYS: rep["insufficient_days"] += 1; continue
                    if pt: cand.append((tk, f, side, x, cuts, first_val, a_t, b_t))
                    elif pm: mk_only.append((tk, f, side, x))
        rep["by_ticker"][tk] = bt
        rep["cells_n100_search"] += bt["cells_n100"]; rep["search_bar_taker"] += bt["bar_taker"]; rep["search_bar_stress_taker"] += bt["bar_stress_taker"]; rep["search_bar_maker"] += bt["bar_maker"]
    rep["tried"] = m; rep["m_total"] = m + m_prior; rep["maker_only"] = len(mk_only); rep["maker_only_list"] = [{"ticker": t, "filter": f, "side": sd, "exit": x, "flag": "assumes resting fills; fill rate unknown"} for t, f, sd, x in mk_only]
    vp = {}
    for tk, f, side, x, cuts, fv, a_t, b_t in cand:
        good = [c for c in perps[tk] if ok(c)]
        v1, _ = run_rule(good, f, side, x, HAIRCUTS[0], cuts, lo=fv, funding=(funding or {}).get(tk)); v2, _ = run_rule(good, f, side, x, HAIRCUTS[1], cuts, lo=fv, funding=(funding or {}).get(tk))
        sa, sb = stats(v1, FEE), stats(v2, FEE)
        if passes(sa, sb):
            if days(v1) < MIN_DAYS: rep["insufficient_days"] += 1; continue
            vp[(tk, f, side, x)] = (pval(sa["day_z"]), sa, sb, stats(v1, FEE_MAKER))
    rep["search_passes"] = len(cand); rep["validate_bar_passes"] = len(vp)
    items = sorted(vp.items(), key=lambda kv: kv[1][0]); k = 0
    for i, (_, v) in enumerate(items, 1):
        if v[0] <= ALPHA * i / (m + m_prior): k = i
    rep["validate_passes"] = k
    rep["survivors"] = [{"ticker": key[0], "filter": key[1], "side": key[2], "exit": key[3], "pf_taker_h1": v[1]["pf"], "pf_taker_h2": v[2]["pf"], "pf_maker_h1": v[3]["pf"], "n": v[1]["n"], "avg_hold_min": v[1]["avg_hold_min"], "avg_gross_bp": v[1]["avg_gross_bp"], "p": v[0], "leverage_table": "to be built for a survivor (needs Kalshi's margin rules)"} for key, v in items[:k]]
    return rep
