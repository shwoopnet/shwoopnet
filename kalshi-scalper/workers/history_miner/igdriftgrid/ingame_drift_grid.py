"""ingame_drift_grid.py: scorer plugin for IGDRIFTGRID1 (History Miner, Nov 16, 2026). Card IGDRIFTGRID1_CARD_NOV16.md. Pure functions, no I/O.
Imports the signed ingame_events.py (4698bae0, unchanged) for fee, pf, day_z, two, tip_of, quote_at and cash; it adds only the grid. Upper bound, not fill-checked."""
import collections, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "igspecs"))
import ingame_events as E

EPS = 1e-9
OFFSETS = (45, 75, 120)
THRESHOLDS = (0.05, 0.08)
DIRECTIONS = ("follow", "fade")
LOOKBACK = 30
CELLS = [(d, th, di) for d in OFFSETS for th in THRESHOLDS for di in DIRECTIONS if not (d == 120 and th == 0.08 and di == "follow")]
RATE_GATE = 3.0


def rid(cell):
    return "IGDG_%d_%02d_%s" % (cell[0], round(cell[1] * 100), cell[2].upper())


def decide(ev, cell):
    """-> (reason, det). One trade per game and kind; NBA and NHL totals and the NHL moneyline only."""
    d_min, theta, direction = cell
    if ev["kind"] == "spread" or ev["league"] == "NFL":
        return "not in wall", None
    if ev["kind"] == "ml" and ev["league"] != "NHL":
        return "not in wall", None
    tip = E.tip_of(ev)
    if tip is None:
        return "schedule test failed", None
    tks = sorted(ev["rows"])[:1] if ev["kind"] == "ml" else sorted(ev["rows"])
    for tk in tks:
        now = tip + d_min * 60
        q1, q0 = E.quote_at(ev["rows"][tk], now), E.quote_at(ev["rows"][tk], now - LOOKBACK * 60)
        if not q1 or not q0:
            continue
        d = (q1[0] + q1[1]) / 2 - (q0[0] + q0[1]) / 2
        if abs(d) < theta - EPS:
            return "no signal", None
        up = d > 0
        yes = up if direction == "follow" else not up
        side, ask = ("yes", q1[1]) if yes else ("no", round(1 - q1[0], 6))
        if 0.20 - EPS <= ask <= 0.80 + EPS:
            return "ok", {"ticker": tk, "side": side, "ask": ask, "t": now}
        return "ask out of range", None
    return "no quote at a mark", None


def run(events):
    out = {}
    tip_days = set()
    for ev in events:
        tp = E.tip_of(ev)
        if tp is not None and ev["league"] in ("NBA", "NHL") and ev["kind"] in ("total", "ml"):
            tip_days.add(time.strftime("%Y-%m-%d", time.gmtime(tp)))
    span = max(len(tip_days), 1)
    for cell in CELLS:
        skips = collections.Counter(); rows = {h: [] for h in E.HAIRCUTS}
        for ev in events:
            why, det = decide(ev, cell)
            if why != "ok":
                skips[why] += 1; continue
            for h in E.HAIRCUTS:
                rows[h].append((det["t"], E.cash(ev, det, h)))
        r = {"cell": {"offset_min": cell[0], "threshold": cell[1], "direction": cell[2]}, "skips": dict(skips), "days_with_games": span}
        n = len(rows[0.02]); rate = n / span
        r["n"] = n; r["rate_per_day"] = rate
        r["rate_gate"] = "ok" if rate >= RATE_GATE else "DROPPED: rate %.2f a day under %.1f (a rate failure, not a bar failure)" % (rate, RATE_GATE)
        for h in E.HAIRCUTS:
            rs = sorted(rows[h]); xs = [x for _, x in rs]; half = len(xs) // 2
            r["h%d" % round(h * 100)] = {"pf": E.pf(xs) if xs else None, "half1": E.pf(xs[:half]) if half else None, "half2": E.pf(xs[half:]) if xs else None,
                "net": sum(xs), "day_z": E.day_z([(time.strftime("%Y-%m-%d", time.gmtime(t)), x) for t, x in rs]),
                "evidence": "ok" if len(xs) >= 100 else "no evidence at n = %d" % len(xs)}
        mean2 = (sum(x for _, x in rows[0.02]) / n / E.CONTRACTS) if n else None
        r["mean_net_per_contract_2c"] = mean2
        r["dollars_a_week_at_5_contracts"] = (rate * 7 * mean2 * 5) if mean2 is not None else None
        r["kill_fast"] = r["h2"]["pf"] is not None and r["h2"]["pf"] < 1.0
        out[rid(cell)] = r
    ranked = sorted((k for k, v in out.items() if v["rate_gate"] == "ok" and v["dollars_a_week_at_5_contracts"] is not None), key=lambda k: -out[k]["dollars_a_week_at_5_contracts"])
    return {"cells": out, "ranked_by_dollars_a_week": ranked, "tries": len(CELLS)}
