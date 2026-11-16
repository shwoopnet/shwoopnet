"""ENGINE1 perps block (Desk A, Nov 16 2026), built to ENGINE1_PERPS_HAND_CASE_NOV16.md. Pure functions on one ticker's candles [(end, bid, ask, last, vol, oi)]. Fee 12 bps a leg ASSUMED. Upper bound, not fill-checked, funding not booked."""
import math, time, collections
FEE = 0.0012; HAIRCUTS = (0.0001, 0.0002); COOLDOWN = 1800
MOMS = (1, 3, 5, 15); TODS = ("pre", "open", "mid", "close", "post")
FILTERS = (None,) + tuple(("mom%d" % k, c) for k in MOMS for c in ("up", "down")) + tuple(("spread", c) for c in ("low", "mid", "high")) + tuple(("tod", c) for c in TODS)
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
    if name == "spread":
        if cuts is None: return None
        x = (c[2] - c[1]) / mid(c) * 1e4; return ("low" if x <= cuts[0] else "mid" if x <= cuts[1] else "high") == klass
    k = int(name[3:]); p = by.get(e - 60 * k)
    if not ok(p): return None
    r = math.log(mid(c) / mid(p)); return (r > 0 and klass == "up") or (r < 0 and klass == "down")
def trade(by, e, side, exit_, h):
    """-> (net return, reason) or (None, 'no mark'). Candles in `by` are keyed by end_ts."""
    c = by[e]; long_ = side == "long"
    fill = c[2] * (1 + h) if long_ else c[1] * (1 - h)
    def leave(x): return x[1] * (1 - h) if long_ else x[2] * (1 + h)
    ex, why = None, None
    if exit_ in ("TS15", "TS30"):
        k = (15 if exit_ == "TS15" else 30) / 1e4
        for t in range(e + 60, e + COOLDOWN + 1, 60):
            x = by.get(t)
            if not ok(x): continue
            if long_: hit_t, hit_s = x[1] >= fill * (1 + k), x[1] <= fill * (1 - k)
            else: hit_t, hit_s = x[2] <= fill * (1 - k), x[2] >= fill * (1 + k)
            if hit_t or hit_s: ex, why = leave(x), "target" if hit_t else "stop"; break
        mins = 30
    else: mins = int(exit_[1:])
    if ex is None:
        x = by.get(e + 60 * mins)
        if not ok(x): return None, "no mark"
        ex, why = leave(x), "time"
    gross = (ex / fill - 1) if long_ else (fill - ex) / fill
    return gross - 2 * FEE, why
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
        r, why = trade(by, e, side, exit_, h)
        if r is None: cnt[why] += 1; continue
        rows.append((e, r)); cnt[why] += 1; last = e
    return rows, cnt
def days(rows): return len({time.strftime('%Y-%m-%d', time.gmtime(t)) for t, _ in rows})
def stats(rows):
    xs = [x for _, x in rows]; half = len(xs) // 2
    return {"n": len(xs), "pf": pf(xs), "half1": pf(xs[:half]), "half2": pf(xs[half:]), "net": sum(xs), "day_z": day_z(rows), "evidence": "ok" if len(xs) >= 100 else "no evidence at n = %d" % len(xs)}

import engine1_split as S
ALPHA = 0.05; MIN_N = 100; PF1 = 1.3; PF2 = 1.0; MIN_DAYS = 10     # trade days needed in SEARCH and in VALIDATE (Auditor B): fewer prints 'insufficient days' and the rule cannot pass
def pval(z): return 0.5 * math.erfc(z / math.sqrt(2)) if z is not None else 1.0
def short(t): return t[2:] if t.startswith("KX") else t
def run_all(perps):
    """perps: {ticker: candles}. SEARCH then VALIDATE by engine1_split dates (the UTC date of the entry candle end), spread cuts from SEARCH entries only, BH over m = every rule tried. Returns a report; perps block only."""
    rep = {"label": "perps block: upper bound, not fill-checked; fee 12 bps a leg ASSUMED (not confirmed); haircuts 1 and 2 bp stand in for 1c and 2c; funding not booked; information for the forward shadow only", "tried": 0, "search_passes": 0, "validate_bar_passes": 0, "validate_passes": 0, "survivors": [], "no_split_constant": [], "insufficient_days": 0}
    m = 0; cand = []
    for tk, cs in perps.items():
        key = short(tk)
        if key not in S.LAST_SEARCH: rep["no_split_constant"].append(tk); continue
        good = [c for c in cs if ok(c)]
        sp = [(c[2] - c[1]) / mid(c) * 1e4 for c in good if S.phase(key, c[0]) == "search"]
        cuts = spread_cuts(sp) if sp else None
        last_search = max([c[0] for c in good if S.phase(key, c[0]) == "search"] or [0])
        first_val = min([c[0] for c in good if S.phase(key, c[0]) == "validate"] or [10 ** 12])
        for f in FILTERS:
            for side in SIDES:
                for x in EXITS:
                    m += 1
                    r1, _ = run_rule(good, f, side, x, HAIRCUTS[0], cuts, hi=first_val, boundary=first_val); r2, _ = run_rule(good, f, side, x, HAIRCUTS[1], cuts, hi=first_val, boundary=first_val)
                    a, b = stats(r1), stats(r2)
                    if a["n"] >= MIN_N and a["pf"] >= PF1 and b["pf"] >= PF2:
                        if days(r1) < MIN_DAYS: rep["insufficient_days"] += 1; continue
                        cand.append((tk, f, side, x, cuts, first_val, a, b))
    rep["tried"] = m; rep["search_passes"] = len(cand)
    vp = {}
    for tk, f, side, x, cuts, fv, a, b in cand:
        good = [c for c in perps[tk] if ok(c)]
        v1, _ = run_rule(good, f, side, x, HAIRCUTS[0], cuts, lo=fv); v2, _ = run_rule(good, f, side, x, HAIRCUTS[1], cuts, lo=fv)
        sa, sb = stats(v1), stats(v2)
        if sa["n"] >= MIN_N and sa["pf"] >= PF1 and sb["pf"] >= PF2 and days(v1) < MIN_DAYS: rep["insufficient_days"] += 1; continue
        if sa["n"] >= MIN_N and sa["pf"] >= PF1 and sb["pf"] >= PF2: vp[(tk, f, side, x)] = (pval(sa["day_z"]), sa, sb)
    rep["validate_bar_passes"] = len(vp)
    items = sorted(vp.items(), key=lambda kv: kv[1][0]); k = 0
    for i, (_, v) in enumerate(items, 1):
        if v[0] <= ALPHA * i / m: k = i
    rep["validate_passes"] = k
    rep["survivors"] = [{"ticker": key[0], "filter": key[1], "side": key[2], "exit": key[3], "pf_1bp": v[1]["pf"], "pf_2bp": v[2]["pf"], "n": v[1]["n"], "p": v[0]} for key, v in items[:k]]
    return rep
