"""HOURBRIDGE1 core (Desk A, Nov 16 2026), built to HOURBRIDGE1_REGISTRATION_NOV16.md (hand case first). Pure functions; no I/O. Upper bound, not fill-checked.
event = {"H": epoch of the hourly close, "ladder": {strike: [(t_recv_ms, yes_bid, yes_ask), ...]}, "q15": {"strike": K15, "rows": [(t_recv_ms, yes_bid, yes_ask), ...]}, "result": "yes"|"no"|"void"}"""
import sys, os, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_core as K
LEAD = 100; FRESH_MS = 6000; GAP = 0.04; SPREAD = 0.04; CONTRACTS = 10; HAIRCUTS = (0.01, 0.02)
def last_fresh(rows, d_ms):
    c = [r for r in rows if r[0] <= d_ms]
    if not c: return None
    r = max(c, key=lambda x: x[0])
    return r if d_ms - r[0] <= FRESH_MS else None
def two_sided(r): return r is not None and 0 < r[1] < r[2] < 1
def decide(ev):
    """-> (reason, detail). reason 'ok' with detail {side, ask, g} or a skip reason."""
    d_ms = (ev["H"] - LEAD) * 1000
    q = last_fresh(ev["q15"]["rows"], d_ms)
    if q is None: return "stale 15m quote", None
    if not two_sided(q): return "one-sided", None
    if q[2] - q[1] > SPREAD + 1e-9: return "15m spread wide", None
    pts = {}
    for k, rows in ev["ladder"].items():
        r = last_fresh(rows, d_ms)
        if r is None: continue
        if not two_sided(r): continue
        pts[float(k)] = r
    if not pts: return "stale ladder", None
    k15 = float(ev["q15"]["strike"])
    lo = [k for k in pts if k <= k15]; hi = [k for k in pts if k >= k15]
    if not lo or not hi: return "K15 outside the ladder", None
    a, b = max(lo), min(hi)
    for kk in {a, b}:
        if pts[kk][2] - pts[kk][1] > SPREAD + 1e-9: return "ladder spread wide", None
    ma, mb = (pts[a][1] + pts[a][2]) / 2, (pts[b][1] + pts[b][2]) / 2
    p_l = ma if a == b else ma + (mb - ma) * (k15 - a) / (b - a)
    g = p_l - (q[1] + q[2]) / 2
    if abs(g) < GAP - 1e-9: return "no signal", None
    return "ok", ({"side": "yes", "ask": q[2], "g": g} if g > 0 else {"side": "no", "ask": 1 - q[1], "g": g})
def cash(ev, det, h):
    """Net dollars at CONTRACTS contracts for the entry at ask + h (cap 0.99), held to settlement; a void keeps the fee."""
    paid = min(det["ask"] + h, 0.99); fee = K.fee_up_order(paid, CONTRACTS)
    if ev["result"] == "void": return round(-fee, 9)
    if ev["result"] == det["side"]: return round(CONTRACTS * (1 - paid) - fee, 9)
    return round(-CONTRACTS * paid - fee, 9)
def run(events):
    skips = collections.Counter(); rows = {h: [] for h in HAIRCUTS}
    for ev in sorted(events, key=lambda e: e["H"]):
        why, det = decide(ev)
        if why != "ok": skips[why] += 1; continue
        for h in HAIRCUTS: rows[h].append((ev["H"], cash(ev, det, h)))
    out = {"skips": dict(skips)}
    for h in HAIRCUTS:
        xs = [x for _, x in rows[h]]; half = len(xs) // 2
        out["h%d" % round(h * 100)] = {"n": len(xs), "pf": K.pf(xs), "half1": K.pf(xs[:half]), "half2": K.pf(xs[half:]), "net": sum(xs), "day_z": K.day_z([(time.strftime("%Y-%m-%d", time.gmtime(t)), x) for t, x in rows[h]]), "evidence": "ok" if len(xs) >= 100 else "no evidence at n = %d" % len(xs)}
    return out
