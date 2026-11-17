"""OICORE's rule on every other market (Desk A, Nov 17 2026), to OICORE_XMARKET_REGISTRATION_NOV17.md and its dated amendment 1 (the Head's O1 to O11). Pure functions on markets {series: [ {series, ticker, close, result, candles[(end,bid,ask,last,vol,oi)]} ]}; no I/O.
run(markets, phase_of, cut=None): phase_of(series_key, close_ts) -> label; the threshold C per series is computed from the markets labelled "search" unless cut is given (held-out reads pass the SEARCH cuts)."""
import math, time, collections
import engine1_core as K
H1, H2, N10 = 0.01, 0.02, 10; LO, HI = 0.08, 0.50
def day_of(ts): return time.strftime("%Y-%m-%d", time.gmtime(ts))
def rise(m):
    by = {c[0]: c for c in m["candles"]}; a, b = by.get(m["close"] - 180), by.get(m["close"] - 360)
    if a is None or b is None or a[5] is None or b[5] is None: return None
    return a[5] - b[5]
def p90(xs):
    s = sorted(xs); return s[math.ceil(0.9 * len(s)) - 1] if s else None
def entry(m, h=0.0):
    """-> dict for engine1_core.score or None (reason via the second value)."""
    for c in m["candles"]:
        if c[0] != m["close"] - 180: continue                       # the Head's ruling (O1 to O11): side and price on the candle ending exactly close - 180
        if not (0 < c[1] < c[2] < 1): continue
        ya, na = c[2], 1 - c[1]; side = "yes" if ya <= na else "no"; ask = ya if side == "yes" else na
        if LO - 1e-12 <= ask <= HI + 1e-12:
            return {"id": m["ticker"], "day": day_of(m["close"]), "ask": ask, "side": side, "close_ts": m["close"], "entry_end": c[0], "path": [], "result": m["result"]}, None
    return None, "no entry"
def score_market(m, cut):
    r = rise(m)
    if r is None: return None, "no rise"
    if r < cut: return None, "below cut"
    e, why = entry(m)
    return e, why
MIN_RISES = 20
def run(markets, phase_of, cut=None, min_rises=MIN_RISES):
    out = {}
    for s, ms in markets.items():
        key = s[2:-3] if s.startswith("KX") and s.endswith("15M") else s
        rs = [rise(m) for m in ms if phase_of(key, m["close"]) == "search" and m.get("result") in ("yes", "no")]; rs = [x for x in rs if x is not None]
        C = (cut or {}).get(s) if cut else (p90(rs) if len(rs) >= min_rises else None)
        res = {"cut": C, "phases": {}}
        if C is None or C <= 0: res["note"] = "no usable threshold"; out[s] = res; continue
        by = collections.defaultdict(list); skipped = collections.Counter(); closes_ph = collections.defaultdict(list)
        for m in ms:
            if m.get("result") not in ("yes", "no"): skipped["unsettled or void result"] += 1; continue      # Auditor B (b): never scored as a loss
            closes_ph[phase_of(key, m["close"])].append(m["close"])
            e, why = score_market(m, C)
            if e is None: skipped[why] += 1; continue
            by[phase_of(key, m["close"])].append(e)
        res["skipped"] = dict(skipped)
        for ph, es in by.items():
            row = {}
            for h, tag in ((H1, "1c"), (H2, "2c")):
                a = K.aggregate(es, "H", h, N10); row[tag] = {"n": a["n"], "wins": a["wins"], "pf": a["pf"], "cents_per_contract": (a["net"] / (a["n"] * N10) * 100) if a["n"] else 0.0}
            closes = [e["close_ts"] for e in es]; days = (max(closes) - min(closes)) / 86400.0 + 1 if closes else 0.0
            row["signals_per_day_fired_span"] = len(es) / days if days else 0.0          # days from the first to the last FIRED close (overstates when few or clustered)
            cl = closes_ph.get(ph, []); pdays = (max(cl) - min(cl)) / 86400.0 + 1 if cl else 0.0
            row["signals_per_day"] = len(es) / pdays if pdays else 0.0                      # Auditor B (a): the calendar days of the PHASE (first to last close of all the market's windows in it)
            row["phase_days"] = pdays; row["windows_in_phase"] = len(cl)
            row["day_net_1c"] = day_nets(es, H1); res["phases"][ph] = row
        out[s] = res
    return out
def day_nets(es, h):
    d = collections.defaultdict(float)
    for e in es:
        x, _ = K.score(e, "H", h, N10)
        if x is not None: d[e["day"]] += x
    return dict(d)
def corr(a, b):
    ks = sorted(set(a) & set(b))
    if len(ks) < 10: return None
    x = [a[k] for k in ks]; y = [b[k] for k in ks]; mx, my = sum(x) / len(x), sum(y) / len(y)
    sx = math.sqrt(sum((i - mx) ** 2 for i in x)); sy = math.sqrt(sum((i - my) ** 2 for i in y))
    return None if sx == 0 or sy == 0 else sum((i - mx) * (j - my) for i, j in zip(x, y)) / (sx * sy)
