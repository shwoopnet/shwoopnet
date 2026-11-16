"""ENGINE1 driver (Desk A, Nov 15 2026): SEARCH, VALIDATE, Benjamini-Hochberg. Pure; the extract loader supplies the data. Binaries only: the perps block is a separate driver.
markets: {series: [ {series, ticker, close, result, candles[(end,bid,ask,last,vol,oi)]} ]}. Phases come from engine1_split constants (a series with no constant is counted and skipped).
Gate: SEARCH n >= MIN_N scored entries at 10 contracts, PF at 1c >= 1.3 and PF at 2c >= 1.0 (h 0.01 and 0.02); VALIDATE the same bar on survivors plus BH at 5% over m = ALL cells tried."""
import math, time, collections
import engine1_core as K, engine1_enum as N, engine1_split as S
MIN_N = 100; PF1 = 1.3; PF2 = 1.0; ALPHA = 0.05; CONTRACTS = 10
MIN_SPD = 3.0; INCOME_CONTRACTS = 5          # (the owner, Nov 16) a SEARCH gate of 3 or more signals a day; the income figure is at 5 contracts a signal, 7 days a week. m (the count tried) is NOT changed by the gate.
DISCLOSURE = "upper bound, not fill-checked; sales booked at max(bid - h, 0.01), purchases at min(ask + h, 0.99); fee ceil(round(x, 9)) per order per leg; target and stop only on candles ending at or before close - 60; one-sided p from day-clustered z of the 1c cash at 10 contracts; the same ticker appears in several buckets and rules, so the tests are dependent and BH is only approximate"
def search_days(closes):
    """SEARCH window days: first to last close, inclusive of both days."""
    return (max(closes) - min(closes)) / 86400.0 + 1 if closes else 0.0
def validate_days(closes, last_search_date):
    """VALIDATE window days: from the start of the day after the last SEARCH date to the last close."""
    import calendar
    return (max(closes) - (calendar.timegm(time.strptime(last_search_date, "%Y-%m-%d")) + 86400)) / 86400.0 if closes else 0.0
def income(agg, days):
    """-> signals a day, cash edge per contract in cents, dollars a week at INCOME_CONTRACTS (linear from the 10 contract cash)."""
    n = agg["n"]
    if n == 0 or not days: return {"signals_per_day": 0.0, "edge_cents_per_contract": 0.0, "dollars_week": 0.0}
    per = agg["net"] / (n * CONTRACTS)
    return {"signals_per_day": n / days, "edge_cents_per_contract": per * 100, "dollars_week": (n / days) * per * INCOME_CONTRACTS * 7}
def short(series):
    """The ONE mapping from an extract's series string to engine1_split's key: KXWTI15M -> WTI, KXBTC15M -> BTC; an already short name passes."""
    x = series[2:] if series.startswith("KX") else series
    return x[:-3] if x.endswith("15M") else x
def day_of(ts): return time.strftime("%Y-%m-%d", time.gmtime(ts))
def pval(z): return 0.5 * math.erfc(z / math.sqrt(2)) if z is not None else 1.0
def groups(mkts, cuts, stats=None):
    """-> {(bucket, band, side_rule, filter): [(market, entry dict)]} for ONE phase's markets, using the enumerator's own feature code."""
    g = collections.defaultdict(list)
    for m in mkts:
        by_end = {c[0]: c for c in m["candles"] if c[0] <= m["close"]}
        for b in N.BUCKETS:
            e = m["close"] - b
            if e not in by_end: continue
            c = by_end[e]
            if not (0 < c[1] < c[2] < 1): continue
            ya, na = N.asks(c)
            for rs in N.SIDES:
                side = N.side_for(rs, ya, na); a = ya if side == "yes" else na
                if not (5 <= a <= 94): continue
                ra = N.raw_ask(c, side); ent = {"side": side, "ask": ra, "entry_end": e, "whole_cent": abs(ra * 100 - round(ra * 100)) < 1e-6}
                if stats is not None and rs in ("yes", "no"): stats["entries"] += 1; stats["non_whole"] += 0 if ent["whole_cent"] else 1   # each side counted once
                band = a // 5; g[(b, band, rs, None)].append((m, ent))
                f, miss = N.features(by_end, e, side)
                for name in N.FEATURES:
                    if name not in miss: g[(b, band, rs, (name, N.cls(f[name])))].append((m, ent))
                if cuts.get(b) is not None: g[(b, band, rs, ("spread", N.spread_class(f["spread"], cuts[b])))].append((m, ent))
    return g
def to_core(m, ent):
    return {"id": m["ticker"], "close_ts": m["close"], "day": day_of(m["close"]), "series": m["series"], "side": ent["side"], "ask": ent["ask"], "n": CONTRACTS, "entry_end": ent["entry_end"], "result": m["result"],
            "path": [(c[0], c[1], c[2]) for c in m["candles"] if c[0] > ent["entry_end"]]}
def score_group(items, exit_):
    """-> {h: aggregate} for h 0.01 and 0.02 at CONTRACTS, plus the p-value of the 1c cash."""
    es = [to_core(m, ent) for m, ent in items]; out = {}
    for h in (0.01, 0.02): out[h] = K.aggregate(es, exit_, h, CONTRACTS)
    return out, pval(out[0.01]["day_z"])
def passes(agg1, agg2): return agg1["n"] >= MIN_N and agg1["pf"] >= PF1 and agg2["pf"] >= PF2
def bh(pvals, m, alpha=ALPHA):
    """Benjamini-Hochberg over m tests of which len(pvals) were scored (the rest p = 1). Returns the set of keys that pass."""
    items = sorted(pvals.items(), key=lambda kv: kv[1]); k = 0
    for i, (_, p) in enumerate(items, 1):
        if p <= alpha * i / m: k = i
    return {key for key, _ in items[:k]}
def run(markets_by_source):
    """markets_by_source: {source: {series: [market]}}. Returns a report dict (counts first)."""
    rep = {"no_split_constant": [], "disclosure": DISCLOSURE, "tried_by_series": {}, "search_entries_total": 0, "search_non_whole_cent_entries": 0, "validate_entries_total": 0, "validate_non_whole_cent_entries": 0}
    search, valid, sdays, vdays = {}, {}, {}, {}
    st = {"entries": 0, "non_whole": 0}; stv = {"entries": 0, "non_whole": 0}; total = 0; seen = set(); rep["duplicate_tickers_dropped"] = 0
    for src, bys in markets_by_source.items():
        for series, mk in bys.items():
            if short(series) not in S.LAST_SEARCH: rep["no_split_constant"].append((src, series)); continue
            kept_mk = []
            for m in mk:
                if m["ticker"] in seen: rep["duplicate_tickers_dropped"] += 1
                else: kept_mk.append(m)
            mk = kept_mk
            seen.update(m["ticker"] for m in mk)
            sm = [m for m in mk if S.phase(short(series), m["close"]) == "search"]; vm = [m for m in mk if S.phase(short(series), m["close"]) == "validate"]
            cuts = {}
            for b in N.BUCKETS:
                sp = [N.cents(c[2] - c[1]) for m in sm for c in m["candles"] if c[0] == m["close"] - b and 0 < c[1] < c[2] < 1]
                cuts[b] = N.spread_cuts(sp) if sp else None
            rep["tried_by_series"][(src, series)] = N.RULES_PER_SERIES; total += N.RULES_PER_SERIES
            search[(src, series)] = (groups(sm, cuts, st), cuts); valid[(src, series)] = groups(vm, cuts, stv)
            sdays[(src, series)] = search_days([m["close"] for m in sm]); vdays[(src, series)] = validate_days([m["close"] for m in vm], S.LAST_SEARCH[short(series)])
    rep["search_entries_total"] = st["entries"]; rep["search_non_whole_cent_entries"] = st["non_whole"]; rep["validate_entries_total"] = stv["entries"]; rep["validate_non_whole_cent_entries"] = stv["non_whole"]
    rep["combos_tried_m"] = total                                              # printed before any result
    s_pass, s_p = {}, {}
    for key, (g, cuts) in search.items():
        for rule, items in g.items():
            if len(items) < MIN_N: continue
            for x in N.EXITS:
                agg, p = score_group(items, x)
                if agg[0.01]["n"] >= MIN_N: s_p[key + rule + (x,)] = p
                if passes(agg[0.01], agg[0.02]) and sdays[key] and agg[0.01]["n"] / sdays[key] >= MIN_SPD: s_pass[key + rule + (x,)] = (agg[0.01], agg[0.02])      # the 3 a day gate: dropped without a write-up, m unchanged
    rep["search_passes"] = len(s_pass)
    v_res, v_p = {}, {}
    for k, _ in s_pass.items():
        src, series, b, band, rs, filt, x = k
        g, cuts = search[(src, series)]
        vg = valid[(src, series)]
        items = vg.get((b, band, rs, filt), [])
        if len(items) < MIN_N: continue
        agg, p = score_group(items, x)
        if passes(agg[0.01], agg[0.02]): v_res[k] = (agg[0.01], agg[0.02]); v_p[k] = p
    keep = bh(v_p, total)
    rep["validate_bar_passes"] = len(v_res); rep["validate_passes"] = len(keep)
    rep["validate_bar_list"] = [{"source": k[0], "series": k[1], "bucket": k[2], "band": k[3], "side": k[4], "filter": k[5], "exit": k[6], "pf_1c": v_res[k][0]["pf"], "pf_2c": v_res[k][1]["pf"], "n": v_res[k][0]["n"], "days": v_res[k][0]["trade_days"], "p": v_p[k], "family": family(k), "income_1c": income(v_res[k][0], vdays[(k[0], k[1])]), "income_2c": income(v_res[k][1], vdays[(k[0], k[1])])} for k in sorted(v_res, key=lambda k: (-income(v_res[k][0], vdays[(k[0], k[1])])["dollars_week"], str(k)))]    # ranked by dollars a week at 1c   # information only: every rule that met the bar on the VALIDATE dates, before BH (added for run 2, listing only)
    rep["survivors"] = [{"source": k[0], "series": k[1], "bucket": k[2], "band": k[3], "side": k[4], "filter": k[5], "exit": k[6], "pf_1c": v_res[k][0]["pf"], "pf_2c": v_res[k][1]["pf"], "n": v_res[k][0]["n"], "days": v_res[k][0]["trade_days"], "family": family(k)} for k in sorted(keep, key=str)]
    return rep
def family(k):
    src, series, b, band, rs, filt, x = k
    if filt and filt[0].startswith("oi"): return "OI (check against OICORE)"
    if rs in ("favourite", "cheap") and band >= 17 and b <= 600: return "favourite-late (closed family)"
    return "none identified (lead-lag cannot be seen from this data; check by hand)"
