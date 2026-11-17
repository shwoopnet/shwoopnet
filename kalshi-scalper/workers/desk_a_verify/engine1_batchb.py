"""ENGINE1 batch B, ENGB4XBTC (Desk A, Nov 16 2026), built to specs/ENGB4XBTC.spec.json. Pure; the extract loader supplies the data. Imports the audited driver, enumerator, core and split unchanged (engine1_driver 1281ce0a) and adds ONE filter:
btcmom3 = the YES mid change of the KXBTC15M market with the SAME close time, from the candle ending e - 180 to the candle ending e (mid = (bid + ask)/2; both candles must exist in that BTC market, no other requirement, as the enumerator's own mom features), classes up / flat / down by the enumerator's cls(). It is a filter on the 18 series that are NOT Bitcoin. Every other dimension is run 2's grid: 13 buckets x 18 bands x 4 side rules x 6 exits x 3 classes = 16,848 rules a series.
Gate as run 2 plus the 3 a day SEARCH gate; BH over m = prior + this spec's tries."""
import math, collections
import engine1_driver as D, engine1_enum as N, engine1_split as S
FEATURE = "btcmom3"; BTC = "KXBTC15M"; PRIOR_M = 2347488; RULES_PER_SERIES_X = len(N.BUCKETS) * len(N.BANDS) * len(N.SIDES) * len(N.EXITS) * len(N.CLASSES)
def btc_index(btc_markets):
    """{close_ts: {end_ts: candle}} of the Bitcoin 15 minute markets, candles ending at or before the close."""
    return {m["close"]: {c[0]: c for c in m["candles"] if c[0] <= m["close"]} for m in btc_markets}
def btcmom3(btc_by_end, e):
    """-> change of the BTC YES mid from e - 180 to e, or None if either candle is missing."""
    a, b = btc_by_end.get(e - 180), btc_by_end.get(e)
    if a is None or b is None: return None
    return (b[1] + b[2]) / 2 - (a[1] + a[2]) / 2
def groups_x(mkts, btc_idx, stats=None):
    """-> {(bucket, band, side_rule, (FEATURE, class)): [(market, entry)]} for ONE phase's markets of a non-Bitcoin series, entries exactly as D.groups builds them."""
    g = collections.defaultdict(list)
    for m in mkts:
        by_end = {c[0]: c for c in m["candles"] if c[0] <= m["close"]}; bt = btc_idx.get(m["close"])
        for b in N.BUCKETS:
            e = m["close"] - b
            if e not in by_end: continue
            c = by_end[e]
            if not (0 < c[1] < c[2] < 1): continue
            x = btcmom3(bt, e) if bt is not None else None
            if x is None:
                if stats is not None: stats["no btc candle"] += 1
                continue
            ya, na = N.asks(c)
            for rs in N.SIDES:
                side = N.side_for(rs, ya, na); a = ya if side == "yes" else na
                if not (5 <= a <= 94): continue
                ra = N.raw_ask(c, side); ent = {"side": side, "ask": ra, "entry_end": e, "whole_cent": abs(ra * 100 - round(ra * 100)) < 1e-6}
                g[(b, a // 5, rs, (FEATURE, N.cls(x)))].append((m, ent))
    return g
def run_x(wa, prior_m=PRIOR_M, min_spd=None, m_full=None):
    """wa: {series: [market]} (the archive loader's output). -> report. BH is done at m = prior + the tries of this spec, and again at m_full if given (the whole batch B, a stricter bar)."""
    min_spd = D.MIN_SPD if min_spd is None else min_spd
    rep = {"spec": "ENGB4XBTC", "feature": FEATURE, "rules_per_series": RULES_PER_SERIES_X, "no_split_constant": [], "tried_by_series": {}, "stats": collections.Counter()}
    btc = wa.get(BTC)
    if not btc: rep["error"] = "no Bitcoin markets"; return rep
    btc_idx = btc_index(btc); search, valid, sd, vd = {}, {}, {}, {}; total = 0
    for series, mk in wa.items():
        if series == BTC: continue
        if D.short(series) not in S.LAST_SEARCH: rep["no_split_constant"].append(series); continue
        sm = [m for m in mk if S.phase(D.short(series), m["close"]) == "search"]; vm = [m for m in mk if S.phase(D.short(series), m["close"]) == "validate"]
        rep["tried_by_series"][series] = RULES_PER_SERIES_X; total += RULES_PER_SERIES_X
        search[series] = groups_x(sm, btc_idx, rep["stats"]); valid[series] = groups_x(vm, btc_idx, rep["stats"])
        sd[series] = D.search_days([m["close"] for m in sm]); vd[series] = D.validate_days([m["close"] for m in vm], S.LAST_SEARCH[D.short(series)])
    rep["tries_this_spec"] = total; rep["m_now"] = prior_m + total; rep["m_full_batch"] = m_full
    s_pass = {}
    for series, g in search.items():
        for rule, items in g.items():
            if len(items) < D.MIN_N: continue
            for x in N.EXITS:
                agg, p = D.score_group(items, x)
                if D.passes(agg[0.01], agg[0.02]) and sd[series] and agg[0.01]["n"] / sd[series] >= min_spd: s_pass[(series,) + rule + (x,)] = 1
    rep["search_passes"] = len(s_pass); v_res, v_p = {}, {}
    for k in s_pass:
        series, b, band, rs, filt, x = k; items = valid[series].get((b, band, rs, filt), [])
        if len(items) < D.MIN_N: continue
        agg, p = D.score_group(items, x)
        if D.passes(agg[0.01], agg[0.02]): v_res[k] = (agg[0.01], agg[0.02]); v_p[k] = p
    rep["validate_bar_passes"] = len(v_res); keep = D.bh(v_p, rep["m_now"]); rep["validate_passes_m_now"] = len(keep)
    rep["validate_passes_m_full"] = len(D.bh(v_p, m_full)) if m_full else None
    rep["validate_bar_list"] = [{"series": k[0], "bucket": k[1], "band": k[2], "side": k[3], "filter": list(k[4]), "exit": k[5], "pf_1c": v_res[k][0]["pf"], "pf_2c": v_res[k][1]["pf"], "n": v_res[k][0]["n"], "days": v_res[k][0]["trade_days"], "p": v_p[k], "income_1c": D.income(v_res[k][0], vd[k[0]]), "income_2c": D.income(v_res[k][1], vd[k[0]]), "bh_m_now": k in keep} for k in sorted(v_res, key=lambda k: (-D.income(v_res[k][0], vd[k[0]])["dollars_week"], str(k)))]
    rep["stats"] = dict(rep["stats"]); return rep
