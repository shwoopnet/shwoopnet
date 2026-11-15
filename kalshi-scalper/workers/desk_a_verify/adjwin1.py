"""ADJWIN1 core (Desk A, Nov 15 2026), built to ADJWIN1_HAND_CASE_NOV15.md. Pure functions on normalized windows; sends nothing, opens no file.
A window is {"series","close","result":"yes"|"no","candles":[(end_ts,bid,ask),...]} (YES bid/ask closes). The LOADER for the landed NC15 candle files is NOT written here: it needs the files' real shape (Testing Desk), must drop rows at or after CUT_CLOSE by close_time first, and drop candles after close. Label: upper bound, not fill-checked."""
import math, collections
CUT_CLOSE = 1791043200            # 2026-10-03T16:00Z: windows closing at or after are dropped on load
DRIFT_MIN = 0.30; BAND = (0.40, 0.60); LEAD = 60; LEN = 900
def fee_up_order(p, n=10): return math.ceil(0.07 * n * p * (1 - p) * 100 - 1e-9) / 100
def mid(c): return (c[1] + c[2]) / 2
def two_sided(c): return 0 < c[1] < c[2] < 1
def signal(prev, w):
    """Returns (status, drift, entry_candle). status 'ok' or a skip reason string."""
    t = prev["close"]
    if t >= CUT_CLOSE or w["close"] >= CUT_CLOSE: return "after the cut", None, None
    if w["close"] != t + LEN: return "not adjacent", None, None
    pc = sorted(c for c in prev["candles"] if c[0] <= t)                     # candles after close dropped (C8)
    first = [c for c in pc if c[0] > t - LEN]
    last = [c for c in pc if c[0] <= t - LEAD and c[0] >= t - 2 * LEAD]
    if not first or not last: return "P incomplete", None, None
    f, l = first[0], last[-1]
    if not (two_sided(f) and two_sided(l)): return "one-sided", None, None
    d = mid(l) - mid(f)
    if abs(d) < DRIFT_MIN: return "no signal", d, None
    wc = sorted(c for c in w["candles"] if c[0] > t and c[0] <= w["close"])
    if not wc: return "W incomplete", d, None
    e = wc[0]
    if not two_sided(e): return "one-sided", d, e
    return "ok", d, e
def trade(prev, w, arm, h):
    """arm 'M' with drift, 'R' against. Net per contract at haircut h, or (None, reason)."""
    st, d, e = signal(prev, w)
    if st != "ok": return None, st
    yes = (d > 0) == (arm == "M")                                            # True: buy YES
    ask = e[2] if yes else 1 - e[1]
    if not (BAND[0] <= ask <= BAND[1]): return None, "out of band"
    p = ask + h
    won = (w["result"] == "yes") == yes
    return ((1 - p) if won else -p) - fee_up_order(p) / 10, "ok"
def pf(xs):
    wn = sum(x for x in xs if x > 0); ls = -sum(x for x in xs if x < 0)
    return float("inf") if ls == 0 and wn > 0 else (wn / ls if ls else float("nan"))
def run(windows_by_series):
    """windows_by_series: {series: [window,...]} sorted by close. Returns per series and arm stats at h 0, 0.01, 0.02 plus skip counts. No pooled figure."""
    out = {}
    for s, ws in windows_by_series.items():
        ws = sorted(ws, key=lambda w: w["close"]); skips = collections.Counter(); arms = {}
        for arm in ("R", "M"):
            res = {}
            for h in (0.0, 0.01, 0.02):
                rows = []
                for a, b in zip(ws, ws[1:]):
                    x, why = trade(a, b, arm, h)
                    if x is None:
                        if h == 0.0 and arm == "R": skips[why] += 1
                    else: rows.append((b["close"], x))
                xs = [x for _, x in rows]; half = len(xs) // 2
                res["h%d" % round(h * 100)] = {"n": len(xs), "pf": pf(xs), "half1": pf(xs[:half]), "half2": pf(xs[half:]), "evidence": "ok" if len(xs) >= 100 else "no evidence at n = %d" % len(xs)}
            arms[arm] = res
        out[s] = {"arms": arms, "skips": dict(skips)}
    return out
