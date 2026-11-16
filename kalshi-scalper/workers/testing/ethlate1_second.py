#!/usr/bin/env python3
"""ETHLATE1 scorer and enumeration, BUILD 2 (Testing Desk, Nov 16, 2026), written blind from Desk B's spec and card and their answers E1 to E10 (ETHLATE1_SECOND_HAND_CASE.md and addendum 1). Pure functions.
markets: {ticker: {"close_ts": int, "result": "yes"|"no"|other}}; candles: {ticker: {end_ts: (bid, ask)}} (the YES quotes)."""
import math
import engine1_core_second as core

TOL = 1e-9
BUCKET = 120
BANDS = tuple(range(1, 13))
FILTERS = ("none", "low", "mid", "high")
EXITS = ("H", "M60")
H2, H1 = 0.02, 0.01          # 2c is the primary haircut, 1c secondary
N_RULES = len(BANDS) * len(FILTERS) * len(EXITS)
assert N_RULES == 96
M_TOTAL = 6290756


def cents(x): return math.ceil(round(100 * x, 6))
def two_sided(c): return c is not None and c[0] is not None and c[1] is not None and 0 < c[0] < c[1] < 1


def entries(markets, candles):
    """one dict per market with a two-sided look candle ending exactly at close - 120 whose cheap side is in 5c to 94c"""
    out = []
    for tk, mk in sorted(markets.items()):
        c = candles.get(tk, {}).get(mk["close_ts"] - BUCKET)
        if not two_sided(c): continue
        yes_c, no_c = cents(c[1]), cents(1 - c[0])
        side = "yes" if yes_c <= no_c else "no"; a = yes_c if side == "yes" else no_c
        if not 5 <= a <= 94: continue
        out.append({"ticker": tk, "close_ts": mk["close_ts"], "day": mk["close_ts"] // 86400, "result": mk["result"], "side": side, "a": a, "band": a // 5, "raw_ask": c[1] if side == "yes" else 1 - c[0], "spread_c": cents(c[1] - c[0])})
    return out


def split(es):
    """-> (search entries, validate entries, last SEARCH day) by the floor(D/2)-th distinct close date, D over the entries (markets with a two-sided look)"""
    days = sorted(set(e["day"] for e in es)); D = len(days)
    if D < 2: return es, [], (days[-1] if days else None)
    last = days[D // 2 - 1]
    return [e for e in es if e["day"] <= last], [e for e in es if e["day"] > last], last


def spread_cuts(search):
    sp = sorted(e["spread_c"] for e in search); n = len(sp)
    if n == 0: return None
    return sp[math.ceil(n / 3) - 1], sp[math.ceil(2 * n / 3) - 1]


def klass(e, cuts):
    s = e["spread_c"]; c1, c2 = cuts
    return "low" if s <= c1 else ("mid" if s <= c2 else "high")


def cash(e, ex, h, candles, n=10):
    """-> cash for one entry, or None (M60 with no mark = no entry for this cell-exit)"""
    paid = min(core.r6(e["raw_ask"] + h), core.CAP); fee_in = core.fee_up_order(paid, n)
    if ex == "H":
        if e["result"] not in ("yes", "no"): return round(-fee_in, 9)
        return round((n * 1.0 if e["result"] == e["side"] else 0.0) - n * paid - fee_in, 9)
    c = candles.get(e["ticker"], {}).get(e["close_ts"] - 60)
    if not two_sided(c): return None
    bid = c[0] if e["side"] == "yes" else 1 - c[1]; px = max(core.r6(bid - h), core.FLOOR)
    return round(n * px - n * paid - fee_in - core.fee_up_order(px, n), 9)


def pf(v):
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    if neg == 0: return math.inf if pos > 0 else math.nan
    return pos / neg


def z_day(rows):
    by = {}
    for d, x in rows: by[d] = by.get(d, 0.0) + x
    v = list(by.values()); k = len(v)
    if k < 2: return None
    m = sum(v) / k; sd = math.sqrt(sum((x - m) ** 2 for x in v) / (k - 1))
    return None if sd == 0 else m / (sd / math.sqrt(k))


def p_upper(z): return None if z is None else 0.5 * math.erfc(z / math.sqrt(2))


def stats(es, ex, candles, span):
    ts = []
    for e in sorted(es, key=lambda e: (e["close_ts"], e["ticker"])):
        c2, c1 = cash(e, ex, H2, candles), cash(e, ex, H1, candles)
        if c2 is None: continue
        ts.append((e["day"], c2, c1))
    k = len(ts); h = k // 2; v2 = [t[1] for t in ts]
    ev = len(set(e["close_ts"] for e in es if cash(e, ex, H2, candles) is not None))
    return {"n": k, "events": ev, "days": len(set(t[0] for t in ts)), "per_day": (k / span) if span else 0.0, "pf2": pf(v2), "h1": pf(v2[:h]), "h2": pf(v2[h:]), "pf1": pf([t[2] for t in ts]), "z": z_day([(t[0], t[1]) for t in ts]), "marked": k}


def ge(x, lim): return (not math.isnan(x)) and x >= lim
def passes(s, search=True): return s["n"] >= 100 and s["events"] >= 40 and ge(s["pf2"], 1.3) and ge(s["h1"], 1.0) and ge(s["h2"], 1.0) and s["days"] >= 10 and (s["per_day"] >= 3 if search else True)          # 3 signals a day is gated in SEARCH only (spec 20cfbf65); 40 distinct hourly closes (events) per cell


def bh(pvals, m, q=0.05):
    items = sorted(((p, k) for k, p in pvals.items() if p is not None), key=lambda x: (x[0], x[1])); kmax = 0
    for i, (p, k) in enumerate(items, 1):
        if p <= i * q / m: kmax = i
    return {k for p, k in items[:kmax]}


def run(markets, candles, m=M_TOTAL):
    """-> dict: m, entries, split info, cuts, per rule SEARCH and VALIDATE stats, SEARCH and VALIDATE passes, BH survivors"""
    es = entries(markets, candles); se, va, last = split(es)
    sdays = sorted(set(e["day"] for e in se)); vdays = sorted(set(e["day"] for e in va))
    sspan = (sdays[-1] - sdays[0] + 1) if sdays else 0; vspan = (vdays[-1] - vdays[0] + 1) if vdays else 0
    cuts = spread_cuts(se); out = {"m": m, "entries": len(es), "search_n": len(se), "validate_n": len(va), "last_search_day": last, "cuts": cuts, "rules": {}, "search_passes": [], "validate_passes": [], "survivors": []}
    pv = {}
    for band in BANDS:
        for f in FILTERS:
            for ex in EXITS:
                sel = lambda part: [e for e in part if e["band"] == band and (f == "none" or (cuts is not None and klass(e, cuts) == f))]
                ss, vs = stats(sel(se), ex, candles, sspan), stats(sel(va), ex, candles, vspan)
                key = (band, f, ex); out["rules"][key] = (ss, vs)
                if passes(ss):
                    out["search_passes"].append(key)
                    if passes(vs, search=False): out["validate_passes"].append(key); pv[key] = p_upper(vs["z"])
    out["survivors"] = sorted(bh(pv, m))
    return out
