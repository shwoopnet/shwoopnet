"""ENGINE1 perps block (Desk A, Nov 16 2026), built to ENGINE1_PERPS_HAND_CASE_NOV16.md. Pure functions on one ticker's candles [(end, bid, ask, last, vol, oi)]. Fee 12 bps a leg ASSUMED. Upper bound, not fill-checked, funding not booked."""
import math, time, collections
FEE = 0.0012; FEE_MAKER = 0.0005; HAIRCUTS = (0.001, 0.002); COOLDOWN = 1800      # fees per side, ASSUMED; haircuts relative to price (0.1% and 0.2%)
MOMS = (1, 3, 5, 15); TODS = ("pre", "open", "mid", "close", "post")
FILTERS = (None,) + tuple(("mom%d" % k, c) for k in MOMS for c in ("up", "down")) + tuple(("spread", c) for c in ("low", "mid", "high")) + tuple(("tod", c) for c in TODS) + (("orb", "up"), ("orb", "down"), ("sess", "high"), ("sess", "low"))
EXITS = ("T3", "T10", "T15", "T30", "TS15", "TS30"); SIDES = ("long", "short")
RULES_PER_TICKER = len(FILTERS) * len(SIDES) * len(EXITS)
def ok(c): return c is not None and c[1] is not None and c[2] is not None and 0 < c[1] < c[2]
def mid(c): return (c[1] + c[2]) / 2
def tod(end):
    s = end % 86400
    if 9 * 3600 <= s < 14 * 3600 + 1800: return "pre"
    if 14 * 3600 + 1800 <= s < 15 * 3600 + 1800: return "open"
    if 15 * 3600 + 1800 <= s < 20 * 3600: return "mid"
    if 20 * 3600 <= s < 21 * 3600: return "close"
    return "post"
def spread_cuts(vals):
    v = sorted(vals); n = len(v); return v[math.ceil(n / 3) - 1], v[math.ceil(2 * n / 3) - 1]
def feature_ok(by, e, filt, cuts):
    """True/False, or None when a needed candle is missing."""
    if filt is None: return True
    name, klass = filt; c = by[e]
    if name == "tod": return tod(e) == klass
    if name in ("orb", "sess"):
        day0 = e - e % 86400; lo_t = day0 + 14 * 3600 + 1800 + 60                  # candles ending 14:31 UTC ...
        if name == "orb":
            if e % 86400 < 15 * 3600 + 60: return None                             # the entry must end at 15:01 UTC or later
            win = [by[t] for t in range(lo_t, day0 + 15 * 3600 + 1, 60) if t in by]  # ... to 15:00 UTC
            if not win: return None
            hi, lo = max(mid(w) for w in win), min(mid(w) for w in win)
            return mid(c) > hi if klass == "up" else mid(c) < lo
        win = [by[t] for t in range(lo_t, e, 60) if t in by]                        # candles ending 14:31 UTC up to e - 60
        if not win: return None
        return mid(c) > max(mid(w) for w in win) if klass == "high" else mid(c) < min(mid(w) for w in win)
    if name == "spread":
        if cuts is None: return None
        x = (c[2] - c[1]) / mid(c) * 1e4; return ("low" if x <= cuts[0] else "mid" if x <= cuts[1] else "high") == klass
    k = int(name[3:]); p = by.get(e - 60 * k)
    if not ok(p): return None
    r = math.log(mid(c) / mid(p)); return (r > 0 and klass == "up") or (r < 0 and klass == "down")
def trade_full(by, e, side, exit_, h):
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
        mins = 30
    else: mins = int(exit_[1:])
    if ex is None:
        x = by.get(e + 60 * mins)
        if not ok(x): return None, "no mark", 0
        ex, why, hold = leave(x), "time", 60 * mins
    gross = (ex / fill - 1) if long_ else (fill - ex) / fill
    return gross, why, hold
def trade(by, e, side, exit_, h):
    """-> (net return at the taker fee, reason) or (None, reason); kept for the hand case."""
    g, why, hold = trade_full(by, e, side, exit_, h)
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
def run_rule(candles, filt, side, exit_, h, cuts, lo=None, hi=None, boundary=None):
    """All entries of one rule with the 1800 s cooldown; lo and hi bound the entry end (inclusive lo, exclusive hi). -> rows [(e, net)], counters."""
    by = {c[0]: c for c in candles if ok(c)}; rows, cnt, last = [], collections.Counter(), None
    for e in sorted(by):
        if (lo is not None and e < lo) or (hi is not None and e >= hi): continue
        if last is not None and e < last + COOLDOWN: continue
        if boundary is not None and e + COOLDOWN >= boundary: cnt["exit crosses the boundary"] += 1; continue          # (Auditor B) SEARCH never touches VALIDATE prices
        f = feature_ok(by, e, filt, cuts)
        if f is None: cnt["missing feature candle"] += 1; continue
        if not f: continue
        g, why, hold = trade_full(by, e, side, exit_, h)
        if g is None: cnt[why] += 1; continue
        rows.append((e, g, hold)); cnt[why] += 1; last = e
    return rows, cnt
def days(rows): return len({time.strftime('%Y-%m-%d', time.gmtime(r[0])) for r in rows})
def stats(rows, fee=FEE):
    """rows [(e, gross, hold)] -> stats at a per side fee; also the average hold (minutes) and the average gross move."""
    nets = [(r[0], r[1] - 2 * fee) for r in rows]; xs = [x for _, x in nets]; half = len(xs) // 2
    return {"n": len(xs), "pf": pf(xs), "half1": pf(xs[:half]), "half2": pf(xs[half:]), "net": sum(xs), "day_z": day_z(nets), "avg_hold_min": (sum(r[2] for r in rows) / len(rows) / 60) if rows else None, "avg_gross_bp": (sum(r[1] for r in rows) / len(rows) * 1e4) if rows else None, "evidence": "ok" if len(xs) >= 100 else "no evidence at n = %d" % len(xs)}
import engine1_split as S
ALPHA = 0.05; MIN_N = 100; PF1 = 1.3; PF2 = 1.0; MIN_DAYS = 10     # trade days needed in SEARCH and in VALIDATE (Auditor B): fewer prints 'insufficient days' and the rule cannot pass
def pval(z): return 0.5 * math.erfc(z / math.sqrt(2)) if z is not None else 1.0
def short(t): return t[2:] if t.startswith("KX") else t
def passes(a, b): return a["n"] >= MIN_N and a["pf"] >= PF1 and b["pf"] >= PF2
def run_all(perps):
    """perps: {ticker: candles}. SEARCH then VALIDATE by engine1_split dates of the entry candle, spread cuts from SEARCH entries only, every rule scored under the TAKER fee (the gate) and the MAKER fee (flagged, resting fills assumed), BH over m = every rule tried. Perps block only."""
    rep = {"label": "perps block: upper bound, not fill-checked; taker fee 12 bps a side and maker fee 5 bps a side, both ASSUMED (not confirmed); relative haircuts 0.1% and 0.2%; funding not booked; a maker-only pass assumes resting fills, fill rate unknown; information for the forward shadow only", "tried": 0, "cells_n100_search": 0, "search_bar_taker": 0, "search_bar_maker": 0, "maker_only": 0, "insufficient_days": 0, "validate_bar_passes": 0, "validate_passes": 0, "survivors": [], "maker_only_list": [], "no_split_constant": [], "by_ticker": {}}
    m = 0; cand = []; mk_only = []
    for tk, cs in perps.items():
        key = short(tk)
        if key not in S.LAST_SEARCH: rep["no_split_constant"].append(tk); continue
        good = [c for c in cs if ok(c)]
        sp = [(c[2] - c[1]) / mid(c) * 1e4 for c in good if S.phase(key, c[0]) == "search"]
        cuts = spread_cuts(sp) if sp else None
        first_val = min([c[0] for c in good if S.phase(key, c[0]) == "validate"] or [10 ** 12])
        bt = {"cells_n100": 0, "bar_taker": 0, "bar_maker": 0, "search_days_max": 0}
        for f in FILTERS:
            for side in SIDES:
                for x in EXITS:
                    m += 1
                    r1, _ = run_rule(good, f, side, x, HAIRCUTS[0], cuts, hi=first_val, boundary=first_val); r2, _ = run_rule(good, f, side, x, HAIRCUTS[1], cuts, hi=first_val, boundary=first_val)
                    a_t, b_t = stats(r1, FEE), stats(r2, FEE); a_m, b_m = stats(r1, FEE_MAKER), stats(r2, FEE_MAKER)
                    bt["search_days_max"] = max(bt["search_days_max"], days(r1))
                    if a_t["n"] >= MIN_N: bt["cells_n100"] += 1
                    pt, pm = passes(a_t, b_t), passes(a_m, b_m)
                    bt["bar_taker"] += pt; bt["bar_maker"] += pm
                    if (pt or pm) and days(r1) < MIN_DAYS: rep["insufficient_days"] += 1; continue
                    if pt: cand.append((tk, f, side, x, cuts, first_val, a_t, b_t))
                    elif pm: mk_only.append((tk, f, side, x))
        rep["by_ticker"][tk] = bt
        rep["cells_n100_search"] += bt["cells_n100"]; rep["search_bar_taker"] += bt["bar_taker"]; rep["search_bar_maker"] += bt["bar_maker"]
    rep["tried"] = m; rep["maker_only"] = len(mk_only); rep["maker_only_list"] = [{"ticker": t, "filter": f, "side": sd, "exit": x, "flag": "assumes resting fills; fill rate unknown"} for t, f, sd, x in mk_only]
    vp = {}
    for tk, f, side, x, cuts, fv, a_t, b_t in cand:
        good = [c for c in perps[tk] if ok(c)]
        v1, _ = run_rule(good, f, side, x, HAIRCUTS[0], cuts, lo=fv); v2, _ = run_rule(good, f, side, x, HAIRCUTS[1], cuts, lo=fv)
        sa, sb = stats(v1, FEE), stats(v2, FEE)
        if passes(sa, sb):
            if days(v1) < MIN_DAYS: rep["insufficient_days"] += 1; continue
            vp[(tk, f, side, x)] = (pval(sa["day_z"]), sa, sb, stats(v1, FEE_MAKER))
    rep["search_passes"] = len(cand); rep["validate_bar_passes"] = len(vp)
    items = sorted(vp.items(), key=lambda kv: kv[1][0]); k = 0
    for i, (_, v) in enumerate(items, 1):
        if v[0] <= ALPHA * i / m: k = i
    rep["validate_passes"] = k
    rep["survivors"] = [{"ticker": key[0], "filter": key[1], "side": key[2], "exit": key[3], "pf_taker_h1": v[1]["pf"], "pf_taker_h2": v[2]["pf"], "pf_maker_h1": v[3]["pf"], "n": v[1]["n"], "avg_hold_min": v[1]["avg_hold_min"], "avg_gross_bp": v[1]["avg_gross_bp"], "p": v[0], "leverage_table": "to be built for a survivor (needs Kalshi's margin rules)"} for key, v in items[:k]]
    return rep
