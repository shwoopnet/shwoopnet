"""ENGINE1 scorer core (Desk A, Nov 15 2026), built to ENGINE1_SPEC_NOV15.md and the interface text sent to the Testing Desk. Pure functions, no I/O.
Entry: {id, close_ts, day, series, side 'yes'|'no', ask (side's raw ask), n, entry_end, result 'yes'|'no'|'void', path [[end_ts, yes_bid, yes_ask], ...]}."""
import math, collections, time
def fee_up_order(p, n): return math.ceil(round(0.07 * n * p * (1 - p) * 100, 9)) / 100
TRIG_CUT = 60                                                               # target and stop marks only on candles ending at or before close - 60 (Auditor B, b); a quote at the closing instant is not tradable
def sellable(c): return 0 < c[1] < c[2] < 1
def side_bid(side, c): return c[1] if side == "yes" else 1 - c[2]
def score(e, exit_, h, n):
    """-> (net dollars for n contracts, reason) or (None, 'no mark' | 'too late')."""
    paid = min(e["ask"] + h, 0.99); close = e["close_ts"]
    path = sorted((c for c in e["path"] if e["entry_end"] < c[0] <= close), key=lambda c: c[0])
    ex = None                                                              # (price, reason)
    if exit_ in ("T", "S", "B"):
        tgt, stp = min(2 * paid, 0.99), paid / 2
        for c in path:
            if c[0] > close - TRIG_CUT or not sellable(c): continue
            b = side_bid(e["side"], c)
            hit_t = exit_ in ("T", "B") and b >= tgt - 1e-12
            hit_s = exit_ in ("S", "B") and b <= stp + 1e-12
            if hit_t or hit_s: ex = (max(b - h, 0.01), "target" if hit_t else "stop"); break
    elif exit_ in ("M180", "M60"):
        mark = close - (180 if exit_ == "M180" else 60)
        if e["entry_end"] > mark: return None, "too late"
        c = [c for c in path if c[0] == mark]
        if not c or not sellable(c[0]): return None, "no mark"
        ex = (max(side_bid(e["side"], c[0]) - h, 0.01), "time")
    cost = paid * n + fee_up_order(paid, n)
    if ex is not None: return round(ex[0] * n - cost - fee_up_order(ex[0], n), 9), ex[1]
    win = (e["result"] == e["side"])
    if e["result"] == "void": return round(-fee_up_order(paid, n), 9), "void"
    return round((n if win else 0) - cost, 9), "settle"
def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 and w > 0 else (w / l if l else float("nan"))
def day_z(rows):
    by = collections.defaultdict(float)
    for d, x in rows: by[d] += x
    v = list(by.values()); k = len(v)
    if k < 2: return None
    m = sum(v) / k; sd = math.sqrt(sum((x - m) ** 2 for x in v) / (k - 1))
    return None if sd == 0 else m / (sd / math.sqrt(k))
def aggregate(entries, exit_, h, n):
    rows, why = [], collections.Counter()
    for e in sorted(entries, key=lambda e: (e["close_ts"], e["id"])):
        x, r = score(e, exit_, h, n)
        if x is None: why[r] += 1
        else: rows.append((e["day"], x, e["side"] == e["result"])); why[r] += 1
    xs = [x for _, x, _ in rows]; half = len(xs) // 2
    return {"n": len(xs), "wins": sum(1 for x in xs if x > 0), "net": sum(xs), "pf": pf(xs), "half1": pf(xs[:half]), "half2": pf(xs[half:]), "day_z": day_z([(d, x) for d, x, _ in rows]), "trade_days": len({d for d, _, _ in rows}), "reasons": dict(why)}
