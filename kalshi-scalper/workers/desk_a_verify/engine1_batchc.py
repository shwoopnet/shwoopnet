"""ENGINE1 batch C (Desk A, Nov 16 2026), built to specs/ENGC1ETHMOM, ENGC2OIACC, ENGC3TOD, ENGC4GOLDX (frozen, hashes in ENGB_BATCHC_FREEZE or the Head's list). Pure; the extract loader supplies the data. Imports the audited driver, enumerator, core and split unchanged (engine1_driver 1281ce0a, same SEARCH and VALIDATE data as run 2) and engine1_batchb.btc_index. Gate as run 2 plus the 3 a day SEARCH gate; BH over m = the carried number plus this spec's tries.
Features (all use candles ending at or before the entry candle end e):
  ethmom3 / goldmom3: the YES mid change of the KXETH15M / KXGOLD15M market with the SAME close from e - 180 to e, both candles present in that market, classes by cls() (up, flat, down). A filter on the series of the wall only.
  oiacc: (oi at e - oi at e - 180) - (oi at e - 180 - oi at e - 360) of the series' own market, all three candles with an open interest; classes by cls().
  todct: the US Central clock hour of e in four bands (America/Chicago offset at e, DST included): 00:00 to 05:59 'ct00', 06:00 to 11:59 'ct06', 12:00 to 17:59 'ct12', 18:00 to 23:59 'ct18'; every entry has one."""
import collections
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
import engine1_driver as D, engine1_enum as N, engine1_split as S, engine1_batchb as B
CT = ZoneInfo("America/Chicago")
PRIOR_M = 6290660            # the Head's single carried number for Nov 16 prints (7,492,484 from Nov 17)
SPECS = {"ENGC1ETHMOM": ("ethmom3", "KXETH15M", 3), "ENGC2OIACC": ("oiacc", None, 3), "ENGC3TOD": ("todct", None, 4), "ENGC4GOLDX": ("goldmom3", "KXGOLD15M", 3)}
CRYPTO9 = ("KXBTC15M", "KXETH15M", "KXDOGE15M", "KXXRP15M", "KXBNB15M", "KXHYPE15M", "KXSOL15M", "KXNEAR15M", "KXZEC15M")
def wall(spec, series_all):
    f, other, k = SPECS[spec]
    if spec == "ENGC1ETHMOM": return [s for s in series_all if s != other]
    if spec == "ENGC4GOLDX": return [s for s in series_all if s in CRYPTO9]
    return list(series_all)
def xmom(idx_by_end, e):
    """YES mid change of the other market from e - 180 to e, or None if either candle is missing."""
    return B.btcmom3(idx_by_end, e)
def oiacc(by_end, e):
    cs = [by_end.get(t) for t in (e, e - 180, e - 360)]
    if any(c is None or c[5] is None for c in cs): return None
    return (cs[0][5] - cs[1][5]) - (cs[1][5] - cs[2][5])
def todct(e):
    h = datetime.fromtimestamp(e, timezone.utc).astimezone(CT).hour
    return "ct%02d" % (h // 6 * 6)
def groups_c(mkts, fname, other_idx, stats=None):
    """-> {(bucket, band, side_rule, (fname, class)): [(market, entry)]} for one phase; entries as D.groups builds them (the raw ask, whole_cent flag)."""
    g = collections.defaultdict(list)
    for m in mkts:
        by_end = {c[0]: c for c in m["candles"] if c[0] <= m["close"]}
        o = other_idx.get(m["close"]) if other_idx is not None else None
        for b in N.BUCKETS:
            e = m["close"] - b
            if e not in by_end: continue
            c = by_end[e]
            if not (0 < c[1] < c[2] < 1): continue
            if fname in ("ethmom3", "goldmom3"): v = xmom(o, e) if o is not None else None; k = None if v is None else N.cls(v)
            elif fname == "oiacc": v = oiacc(by_end, e); k = None if v is None else N.cls(v)
            else: k = todct(e)
            if k is None:
                if stats is not None: stats["missing feature"] += 1
                continue
            ya, na = N.asks(c)
            for rs in N.SIDES:
                side = N.side_for(rs, ya, na); a = ya if side == "yes" else na
                if not (5 <= a <= 94): continue
                ra = N.raw_ask(c, side); ent = {"side": side, "ask": ra, "entry_end": e, "whole_cent": abs(ra * 100 - round(ra * 100)) < 1e-6}
                g[(b, a // 5, rs, (fname, k))].append((m, ent))
    return g
def run_c(wa, spec, prior_m=PRIOR_M, m_full=None, min_spd=None):
    """wa: {series: [market]} (the archive loader's output). -> report, the same shape as engine1_batchb2.run_family."""
    min_spd = D.MIN_SPD if min_spd is None else min_spd
    fname, other, k = SPECS[spec]; per_series = len(N.BUCKETS) * len(N.BANDS) * len(N.SIDES) * len(N.EXITS) * k
    rep = {"spec": spec, "feature": fname, "rules_per_series": per_series, "no_split_constant": [], "tried_by_series": {}, "stats": collections.Counter()}
    oidx = B.btc_index(wa.get(other, [])) if other else None
    search, valid, sd, vd, total = {}, {}, {}, {}, 0
    for series in wall(spec, sorted(wa)):
        mk = wa[series]
        if D.short(series) not in S.LAST_SEARCH: rep["no_split_constant"].append(series); continue
        sm = [m for m in mk if S.phase(D.short(series), m["close"]) == "search"]; vm = [m for m in mk if S.phase(D.short(series), m["close"]) == "validate"]
        rep["tried_by_series"][series] = per_series; total += per_series
        search[series] = groups_c(sm, fname, oidx, rep["stats"]); valid[series] = groups_c(vm, fname, oidx, rep["stats"])
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
    for key in s_pass:
        series, b, band, rs, filt, x = key; items = valid[series].get((b, band, rs, filt), [])
        if len(items) < D.MIN_N: continue
        agg, p = D.score_group(items, x)
        if D.passes(agg[0.01], agg[0.02]): v_res[key] = (agg[0.01], agg[0.02]); v_p[key] = p
    rep["validate_bar_passes"] = len(v_res); keep = D.bh(v_p, rep["m_now"]); rep["validate_passes_m_now"] = len(keep)
    rep["validate_passes_m_full"] = len(D.bh(v_p, m_full)) if m_full else None
    rep["validate_bar_list"] = [{"series": q[0], "bucket": q[1], "band": q[2], "side": q[3], "filter": (list(q[4]) if q[4] else None), "exit": q[5], "pf_1c": v_res[q][0]["pf"], "pf_2c": v_res[q][1]["pf"], "n": v_res[q][0]["n"], "days": v_res[q][0]["trade_days"], "p": v_p[q], "income_1c": D.income(v_res[q][0], vd[q[0]]), "income_2c": D.income(v_res[q][1], vd[q[0]]), "bh_m_now": q in keep} for q in sorted(v_res, key=lambda q: (-D.income(v_res[q][0], vd[q[0]])["dollars_week"], str(q)))]
    rep["stats"] = dict(rep["stats"]); return rep
