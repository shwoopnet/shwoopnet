"""ENGINE1 enumerator (Desk A, Nov 15 2026), built to ENGINE1_ENUMERATOR_HAND_CASE_NOV15.md. Pure functions on one market's candles; no I/O.
Candle = (end_ts, yes_bid, yes_ask, last, volume, oi). Features use candles ending AT or BEFORE the entry candle only."""
import math
BUCKETS = tuple(range(120, 841, 60)); BANDS = tuple(range(1, 19)); SIDES = ("yes", "no", "cheap", "favourite"); EXITS = ("H", "T", "S", "B", "M180", "M60")
FEATURES = ("oi3", "oi6", "vol3", "mom1", "mom3", "mom5"); CLASSES = ("up", "flat", "down"); SPREAD = ("low", "mid", "high")
FILTERS = (None,) + tuple((f, c) for f in FEATURES for c in CLASSES) + tuple(("spread", c) for c in SPREAD)
RULES_PER_SERIES = len(BUCKETS) * len(BANDS) * len(SIDES) * len(EXITS) * len(FILTERS)
def cls(x): return "up" if x > 1e-12 else ("down" if x < -1e-12 else "flat")
def cents(x): return int(round(100 * x))
def asks(c):
    """-> (yes ask cents, no ask cents) at a candle."""
    return cents(c[2]), cents(1 - c[1])
def side_for(rule_side, ya, na):
    if rule_side in ("yes", "no"): return rule_side
    if rule_side == "cheap": return "yes" if ya <= na else "no"
    return "yes" if ya >= na else "no"
def features(by_end, e, side):
    """by_end: {end_ts: candle}. Returns (feature dict, set of missing feature names). Only candles ending <= e are read."""
    f, miss = {}, set(); c = by_end[e]
    mid = lambda t: (by_end[t][1] + by_end[t][2]) / 2 if t in by_end else None
    sm = (lambda m: m if side == "yes" else 1 - m)
    for name, lag in (("oi3", 180), ("oi6", 360)):
        t = e - lag
        if t in by_end: f[name] = c[5] - by_end[t][5]
        else: miss.add(name)
    ts1, ts2 = (e - 120, e - 60, e), (e - 300, e - 240, e - 180)
    if all(t in by_end for t in ts1 + ts2): f["vol3"] = sum(by_end[t][4] for t in ts1) - sum(by_end[t][4] for t in ts2)
    else: miss.add("vol3")
    for name, lag in (("mom1", 60), ("mom3", 180), ("mom5", 300)):
        m0, m1 = mid(e - lag), mid(e)
        if m0 is None: miss.add(name)
        else: f[name] = sm(m1) - sm(m0)
    f["spread"] = cents(c[2] - c[1])
    return f, miss
def spread_cuts(spreads):
    """From SEARCH spreads (cents): c1 = ceil(n/3)-th, c2 = ceil(2n/3)-th sorted value."""
    v = sorted(spreads); n = len(v)
    return v[math.ceil(n / 3) - 1], v[math.ceil(2 * n / 3) - 1]
def spread_class(x, cuts): return "low" if x <= cuts[0] else ("mid" if x <= cuts[1] else "high")
def entries(candles, close_ts, bucket, band, rule_side, filt, cuts=None):
    """-> (entry or None, reason). entry = {side, ask (dollars), entry_end}."""
    by_end = {c[0]: c for c in candles if c[0] <= close_ts}
    e = close_ts - bucket
    if e not in by_end: return None, "no entry candle"
    c = by_end[e]
    if not (0 < c[1] < c[2] < 1): return None, "one-sided"
    ya, na = asks(c); side = side_for(rule_side, ya, na); a = ya if side == "yes" else na
    if not (5 <= a <= 94) or a // 5 != band: return None, "out of band"
    if filt is None: return {"side": side, "ask": a / 100, "entry_end": e}, "ok"
    f, miss = features(by_end, e, side)
    name, klass = filt
    if name == "spread":
        if cuts is None: return None, "no cuts"
        ok = spread_class(f["spread"], cuts) == klass
    else:
        if name in miss: return None, "missing feature candle"
        ok = cls(f[name]) == klass
    return ({"side": side, "ask": a / 100, "entry_end": e}, "ok") if ok else (None, "filter")
