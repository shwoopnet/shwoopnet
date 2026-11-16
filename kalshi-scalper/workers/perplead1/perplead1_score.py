"""PERPLEAD1 pure scorer (Desk B, Nov 16 2026; DRAFT, unrun, unsigned): ladder-implied median against a perp's bid and ask. No file read, no network. Expected figures: EXPECTED_perplead1_nov16.md.
Every figure from here is 'upper bound, zero latency' (the entry is the same minute's ask or bid close; see robust shift in score_rule)."""
import math
LMAX = 1 / 0.045; SHARES = (0.10, 0.25, 0.50); MAINT = 0.045
def implied_median(strike_mids):
    pts = sorted(strike_mids)
    for (k1, m1), (k2, m2) in zip(pts, pts[1:]):
        if m1 >= 0.5 > m2: return k1 + (m1 - 0.5) / (m1 - m2) * (k2 - k1)
    return None
def gap_bps(median, perp_mid, scale=1.0): return 1e4 * (median / (perp_mid * scale) - 1)
def trade(d, e_bid, e_ask, x_bid, x_ask, fee_bps):
    """d = +1 long (buy at the entry ask, sell at the exit bid), -1 short (sell at the entry bid, buy at the exit ask)."""
    if d > 0: return 1e4 * (x_bid - e_ask) / e_ask - fee_bps
    return 1e4 * (e_bid - x_ask) / e_bid - fee_bps
def score_rule(events, theta, exit_key, direction, fee_bps, cnt, shift=0):
    """events: [{day, strikes: {look: [(strike, mid)]}, perp: {look: (bid, ask)}, scale}]; look in ('m120', 'm60', 'm0'); entry look m120 (shift 1: m60); exit_key 'm60' or 'm0' (shift 1 moves it one look later; past the close: not scored).
    -> [(day, net_bps)] and cnt counted."""
    looks = ("m120", "m60", "m0"); out = []
    for ev in events:
        el = looks[looks.index("m120") + shift]; xi = looks.index(exit_key) + shift
        if xi >= len(looks): cnt["exit after the close (not scored)"] += 1; continue
        xl = looks[xi]
        med = implied_median(ev["strikes"].get(el, []))
        if med is None: cnt["no signal"] += 1; continue
        p = ev["perp"].get(el)
        if not p: cnt["entry perp candle missing"] += 1; continue
        g = gap_bps(med, (p[0] + p[1]) / 2, ev.get("scale", 1.0))
        if abs(g) < theta: cnt["under theta"] += 1; continue
        x = ev["perp"].get(xl)
        if not x: cnt["exit candle missing"] += 1; continue
        d = (1 if g > 0 else -1) * (1 if direction == "convergence" else -1)
        out.append((ev["day"], trade(d, p[0], p[1], x[0], x[1], fee_bps)))
    return out
def summary(trades):
    nets = [n for _, n in trades]; w = sum(n for n in nets if n > 0); l = -sum(n for n in nets if n < 0)
    return {"n": len(nets), "days": len({d for d, _ in trades}), "mean": sum(nets) / len(nets) if nets else float("nan"),
            "pf": (w / l if l else (float("inf") if w else 0.0)) if nets else float("nan")}
def margin_print(mean_bps):
    return [{"share_of_lmax": s, "leverage": LMAX * s, "margin_fraction": 1 / (LMAX * s), "return_on_margin_pct": mean_bps / (1e4 / (LMAX * s)) * 100, "liquidation_distance_pct": (1 / (LMAX * s) - MAINT) * 100} for s in SHARES]
def split_dates(days):
    ds = sorted(set(days)); k = len(ds) // 2
    return set(ds[:k]), set(ds[k:])
