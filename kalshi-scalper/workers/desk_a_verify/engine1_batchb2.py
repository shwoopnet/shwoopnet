"""ENGINE1 batch B, ENGB1TIMESTOP, ENGB2VSPIKE and ENGB3SPRW (Desk A, Nov 16 2026), built to specs/ENGB1TIMESTOP.spec.json, ENGB2VSPIKE and ENGB3SPRW. Pure. Imports the audited driver, enumerator, core and split unchanged and adds:
- exits TA3 and TA5 (score_ta): sell at max(side bid - h, 0.01) on the candle ending EXACTLY 3 or 5 minutes after the entry end; no trade ('too late') if that candle ends after close - 60, none ('no mark') if absent or not two sided; cash as the core: round(exit x n - paid x n - fee_in - fee_out, 9), paid = min(raw ask + h, 0.99), fee ceil(round(0.07 n p (1-p) x 100, 9)) / 100 at paid and at the exit price. The rest of the grid is run 2's.
- feature vspike = volume(e) / mean(volume of the 5 candles ending e - 60 ... e - 300): all six candles must exist with a non-null volume and the mean must be positive, else missing; classes low, mid, high from SEARCH terciles of the ratio per series and bucket (N.spread_cuts on the SEARCH ratios; low <= c1, mid <= c2).
- feature swid = cents(ask - bid) of the entry candle minus the same at the candle ending e - 180 (both must exist and be two sided, else missing); classes up (> 0), flat (0), down (< 0) by the enumerator's cls.
Gate and BH as run 2 plus the 3 a day gate (engine1_driver 1281ce0a); the BH m is printed first."""
import math, collections
import engine1_driver as D, engine1_enum as N, engine1_core as K, engine1_split as S
PRIOR_M = 2347488
def score_ta(e, k, h, n):
    """-> (net dollars for n contracts, reason) or (None, 'no mark' | 'too late'). Same conventions as engine1_core.score."""
    paid = min(e["ask"] + h, 0.99); close = e["close_ts"]; mark = e["entry_end"] + 60 * k
    if mark > close - K.TRIG_CUT: return None, "too late"
    c = [c for c in e["path"] if c[0] == mark]
    if not c or not K.sellable(c[0]): return None, "no mark"
    ex = max(K.side_bid(e["side"], c[0]) - h, 0.01); cost = paid * n + K.fee_up_order(paid, n)
    return round(ex * n - cost - K.fee_up_order(ex, n), 9), "time"
def aggregate_x(entries, scorer, h, n):
    rows, why = [], collections.Counter()
    for e in sorted(entries, key=lambda e: (e["close_ts"], e["id"])):
        x, r = scorer(e, h, n)
        if x is None: why[r] += 1
        else: rows.append((e["day"], x, e["side"] == e["result"])); why[r] += 1
    xs = [x for _, x, _ in rows]; half = len(xs) // 2
    return {"n": len(xs), "wins": sum(1 for x in xs if x > 0), "net": sum(xs), "pf": K.pf(xs), "half1": K.pf(xs[:half]), "half2": K.pf(xs[half:]), "day_z": K.day_z([(d, x) for d, x, _ in rows]), "trade_days": len({d for d, _, _ in rows}), "reasons": dict(why)}
def vspike(by_end, e):
    vs = [by_end[t][4] if t in by_end else None for t in (e, e - 60, e - 120, e - 180, e - 240, e - 300)]
    if any(v is None for v in vs): return None
    m = sum(vs[1:]) / 5.0
    return vs[0] / m if m > 0 else None
def swid(by_end, e):
    a, b = by_end.get(e), by_end.get(e - 180)
    if a is None or b is None or not (0 < a[1] < a[2] < 1) or not (0 < b[1] < b[2] < 1): return None
    return N.cents(a[2] - a[1]) - N.cents(b[2] - b[1])
FEATURES = {"vspike": vspike, "swid": swid}
def feature_cuts(sm, name):
    """SEARCH tercile cuts of a continuous feature per bucket (vspike only; swid uses the sign classes)."""
    cuts = {}
    for b in N.BUCKETS:
        vals = []
        for m in sm:
            by_end = {c[0]: c for c in m["candles"] if c[0] <= m["close"]}; e = m["close"] - b
            if e in by_end and 0 < by_end[e][1] < by_end[e][2] < 1:
                v = FEATURES[name](by_end, e)
                if v is not None: vals.append(v)
        cuts[b] = N.spread_cuts(vals) if vals else None
    return cuts
def klass(name, v, cuts_b):
    if name == "swid": return N.cls(v)
    if cuts_b is None: return None
    return "low" if v <= cuts_b[0] else ("mid" if v <= cuts_b[1] else "high")
def groups_f(mkts, name, cuts, stats=None):
    """-> {(bucket, band, side_rule, (name, class)): [(market, entry)]} for one phase; entries as D.groups builds them."""
    g = collections.defaultdict(list)
    for m in mkts:
        by_end = {c[0]: c for c in m["candles"] if c[0] <= m["close"]}
        for b in N.BUCKETS:
            e = m["close"] - b
            if e not in by_end: continue
            c = by_end[e]
            if not (0 < c[1] < c[2] < 1): continue
            v = FEATURES[name](by_end, e)
            k = klass(name, v, cuts.get(b)) if v is not None else None
            if k is None:
                if stats is not None: stats["missing feature"] += 1
                continue
            ya, na = N.asks(c)
            for rs in N.SIDES:
                side = N.side_for(rs, ya, na); a = ya if side == "yes" else na
                if not (5 <= a <= 94): continue
                ra = N.raw_ask(c, side); ent = {"side": side, "ask": ra, "entry_end": e, "whole_cent": abs(ra * 100 - round(ra * 100)) < 1e-6}
                g[(b, a // 5, rs, (name, k))].append((m, ent))
    return g
def run_family(wa, spec, prior_m=PRIOR_M, m_full=None, min_spd=None):
    """spec: 'ENGB1TIMESTOP' (exits TA3, TA5, run 2's 22 filters), 'ENGB2VSPIKE' or 'ENGB3SPRW' (the one new filter, run 2's six exits). wa: {series: [market]}."""
    min_spd = D.MIN_SPD if min_spd is None else min_spd
    ta = spec == "ENGB1TIMESTOP"; fname = {"ENGB2VSPIKE": "vspike", "ENGB3SPRW": "swid"}.get(spec)
    exits = ("TA3", "TA5") if ta else N.EXITS; nfilt = 22 if ta else len(N.CLASSES)
    per_series = len(N.BUCKETS) * len(N.BANDS) * len(N.SIDES) * len(exits) * nfilt
    def score_group(items, x):
        es = [D.to_core(m, ent) for m, ent in items]
        if ta:
            k = 3 if x == "TA3" else 5; out = {h: aggregate_x(es, lambda e, hh, n, k=k: score_ta(e, k, hh, n), h, D.CONTRACTS) for h in (0.01, 0.02)}
        else: out = {h: K.aggregate(es, x, h, D.CONTRACTS) for h in (0.01, 0.02)}
        return out, D.pval(out[0.01]["day_z"])
    rep = {"spec": spec, "rules_per_series": per_series, "no_split_constant": [], "tried_by_series": {}, "stats": collections.Counter()}
    search, valid, sd, vd, total = {}, {}, {}, {}, 0
    for series, mk in wa.items():
        if D.short(series) not in S.LAST_SEARCH: rep["no_split_constant"].append(series); continue
        sm = [m for m in mk if S.phase(D.short(series), m["close"]) == "search"]; vm = [m for m in mk if S.phase(D.short(series), m["close"]) == "validate"]
        rep["tried_by_series"][series] = per_series; total += per_series
        if ta:
            cuts = {}
            for b in N.BUCKETS:
                sp = [N.cents(c[2] - c[1]) for m in sm for c in m["candles"] if c[0] == m["close"] - b and 0 < c[1] < c[2] < 1]
                cuts[b] = N.spread_cuts(sp) if sp else None
            search[series] = D.groups(sm, cuts); valid[series] = D.groups(vm, cuts)
        else:
            cuts = feature_cuts(sm, fname) if fname == "vspike" else {}
            search[series] = groups_f(sm, fname, cuts, rep["stats"]); valid[series] = groups_f(vm, fname, cuts, rep["stats"])
        sd[series] = D.search_days([m["close"] for m in sm]); vd[series] = D.validate_days([m["close"] for m in vm], S.LAST_SEARCH[D.short(series)])
    rep["tries_this_spec"] = total; rep["m_now"] = prior_m + total; rep["m_full_batch"] = m_full
    s_pass = {}
    for series, g in search.items():
        for rule, items in g.items():
            if len(items) < D.MIN_N: continue
            for x in exits:
                agg, p = score_group(items, x)
                if D.passes(agg[0.01], agg[0.02]) and sd[series] and agg[0.01]["n"] / sd[series] >= min_spd: s_pass[(series,) + rule + (x,)] = 1
    rep["search_passes"] = len(s_pass); v_res, v_p = {}, {}
    for k in s_pass:
        series, b, band, rs, filt, x = k; items = valid[series].get((b, band, rs, filt), [])
        if len(items) < D.MIN_N: continue
        agg, p = score_group(items, x)
        if D.passes(agg[0.01], agg[0.02]): v_res[k] = (agg[0.01], agg[0.02]); v_p[k] = p
    rep["validate_bar_passes"] = len(v_res); keep = D.bh(v_p, rep["m_now"]); rep["validate_passes_m_now"] = len(keep)
    rep["validate_passes_m_full"] = len(D.bh(v_p, m_full)) if m_full else None
    rep["validate_bar_list"] = [{"series": k[0], "bucket": k[1], "band": k[2], "side": k[3], "filter": (list(k[4]) if k[4] else None), "exit": k[5], "pf_1c": v_res[k][0]["pf"], "pf_2c": v_res[k][1]["pf"], "n": v_res[k][0]["n"], "days": v_res[k][0]["trade_days"], "p": v_p[k], "income_1c": D.income(v_res[k][0], vd[k[0]]), "income_2c": D.income(v_res[k][1], vd[k[0]]), "bh_m_now": k in keep} for k in sorted(v_res, key=lambda k: (-D.income(v_res[k][0], vd[k[0]])["dollars_week"], str(k)))]
    rep["stats"] = dict(rep["stats"]); return rep
