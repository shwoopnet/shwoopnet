"""ADJWIN1 core (Desk A, Nov 15 2026), built to ADJWIN1_HAND_CASE_NOV15.md. Pure functions on normalized windows; sends nothing, opens no file.
A window is {"series","close","result":"yes"|"no","candles":[(end_ts,bid,ask),...]} (YES bid/ask closes). The LOADER for the landed NC15 candle files is NOT written here: it needs the files' real shape (Testing Desk), must drop rows at or after CUT_CLOSE by close_time first, and drop candles after close. Label: upper bound, not fill-checked."""
import math, collections, time
CUT_CLOSE = 1791043200            # 2026-10-03T16:00Z: windows closing at or after are dropped on load
VAL_START = 1788220800            # 2026-09-01T00:00Z: development closes before, validation from
DRIFT_MIN = 0.30; BAND = (0.40, 0.60); LEAD = 60; LEN = 900
def fee_up_order(p, n=10): return math.ceil(round(0.07 * n * p * (1 - p) * 100, 9)) / 100
def mid(c): return (c[1] + c[2]) / 2
def two_sided(c): return 0 < c[1] < c[2] < 1
def signal(prev, w):
    """Returns (status, drift, entry_candle). status 'ok' or a skip reason string."""
    t = prev["close"]
    if t >= CUT_CLOSE or w["close"] >= CUT_CLOSE: return "after the cut", None, None
    if w["close"] != t + LEN: return "not adjacent", None, None
    pc = sorted(c for c in prev["candles"] if c[0] <= t)                     # candles after close dropped (C8)
    first = [c for c in pc if c[0] == t - LEN + LEAD]                        # exactly the first minute (ends t-840)
    last = [c for c in pc if c[0] == t - LEAD]                               # exactly the t-60 candle, no substitute
    if not first or not last: return "P incomplete", None, None
    f, l = first[0], last[-1]
    if not (two_sided(f) and two_sided(l)): return "one-sided", None, None
    d = mid(l) - mid(f)
    if abs(d) < DRIFT_MIN: return "no signal", d, None
    wc = [c for c in w["candles"] if c[0] == t + LEAD]                       # exactly W's first minute (ends t+60)
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
    if not (BAND[0] - 1e-9 <= ask <= BAND[1] + 1e-9): return None, "out of band"
    p = ask + h
    won = (w["result"] == "yes") == yes
    return ((1 - p) if won else -p) - fee_up_order(p) / 10, "ok"
def pf(xs):
    wn = sum(x for x in xs if x > 0); ls = -sum(x for x in xs if x < 0)
    return float("inf") if ls == 0 and wn > 0 else (wn / ls if ls else float("nan"))
def day_z(rows):                                                           # rows [(close_ts, net)] -> day-clustered z, None under 2 days or sd 0
    by = collections.defaultdict(float)
    for t, x in rows: by[time.strftime("%Y-%m-%d", time.gmtime(t))] += x
    d = list(by.values()); n = len(d)
    if n < 2: return None
    m = sum(d) / n; sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    return None if sd == 0 else m / (sd / math.sqrt(n))
def stats(rows):
    xs = [x for _, x in rows]; half = len(xs) // 2
    return {"n": len(xs), "pf": pf(xs), "half1": pf(xs[:half]), "half2": pf(xs[half:]), "day_z": day_z(rows), "trade_days": len({time.strftime("%Y-%m-%d", time.gmtime(t)) for t, _ in rows}), "evidence": "ok" if len(xs) >= 100 else "no evidence at n = %d" % len(xs)}
def run(windows_by_series):
    """{series: [window,...]} -> per series: arms R and M, each at h 0/1c/2c, development (close < VAL_START) and validation reported SEPARATELY, plus skip counts. No pooled figure."""
    out = {}
    for s, ws in windows_by_series.items():
        ws = sorted(ws, key=lambda w: w["close"]); skips = collections.Counter(); arms = {}
        for arm in ("R", "M"):
            res = {}
            for h in (0.0, 0.01, 0.02):
                dev, val = [], []
                for a, b in zip(ws, ws[1:]):
                    x, why = trade(a, b, arm, h)
                    if x is None:
                        if h == 0.0 and arm == "R": skips[why] += 1
                    else: (dev if b["close"] < VAL_START else val).append((b["close"], x))
                res["h%d" % round(h * 100)] = {"dev": stats(dev), "val": stats(val)}
            arms[arm] = res
        out[s] = {"arms": arms, "skips": dict(skips)}
    return out
