"""ingame_drift_spread.py: scorer plugin for IGDRIFTSPREAD1 (History Miner, Nov 16, 2026). Card IGDRIFTSPREAD1_CARD_NOV16.md. Pure functions, no I/O.
It reuses the CLEAN decision of ingame_drift_grid.py (6a4e63c8) by treating a NBA or NHL spread event as a totals event, and the signed scorer ingame_events.py (4698bae0). Upper bound, not fill-checked."""
import collections, hashlib, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
GRID_SHA256 = "6a4e63c897a1ff93bd36777330398fbd5f7392274230c938d586b1b005914b4d"           # Auditor B's CLEAN of ingame_drift_grid.py
if hashlib.sha256(open(os.path.join(HERE, "..", "igdriftgrid", "ingame_drift_grid.py"), "rb").read()).hexdigest() != GRID_SHA256:
    raise SystemExit("REFUSED: ingame_drift_grid.py is not the cleared file (sha256 %s)" % GRID_SHA256)
sys.path.insert(0, os.path.join(HERE, "..", "igdriftgrid"))
import ingame_drift_grid as G                      # imports and pins ingame_events.py itself
E = G.E
CELLS = [(d, th, di) for d in G.OFFSETS for th in G.THRESHOLDS for di in G.DIRECTIONS]
RATE_GATE = G.RATE_GATE; GATE_DAYS = G.GATE_DAYS


def rid(cell):
    return G.rid(cell).replace("IGDG_", "IGDS_")


def as_total(ev):
    return dict(ev, kind="total") if ev["kind"] == "spread" and ev["league"] in ("NBA", "NHL") else None


def decide(ev, cell):
    t = as_total(ev)
    return ("not in wall", None) if t is None else G.decide(t, cell)


def in_scope(ev):
    return as_total(ev) is not None


def compute_gate(events):
    days = sorted({G.tip_day(ev) for ev in events if in_scope(ev) and G.tip_day(ev)})
    if len(days) < GATE_DAYS:
        return None
    first = set(days[:GATE_DAYS]); out = {}
    for cell in CELLS:
        n = sum(1 for ev in events if in_scope(ev) and G.tip_day(ev) in first and decide(ev, cell)[0] == "ok")
        out[rid(cell)] = {"rate": n / GATE_DAYS, "dropped": n / GATE_DAYS < RATE_GATE, "days": sorted(first)}
    return out


def run(events, stored_gate=None):
    out = {}
    span = max(len({G.tip_day(ev) for ev in events if in_scope(ev) and G.tip_day(ev)}), 1)
    gate = stored_gate or compute_gate(events)
    for cell in CELLS:
        skips = collections.Counter(); rows = {h: [] for h in E.HAIRCUTS}
        for ev in events:
            why, det = decide(ev, cell)
            if why != "ok":
                skips[why] += 1; continue
            for h in E.HAIRCUTS:
                rows[h].append((det["t"], E.cash(ev, det, h)))
        r = {"cell": {"offset_min": cell[0], "threshold": cell[1], "direction": cell[2]}, "skips": dict(skips), "days_with_games": span, "unit": "games (one trade per game and kind)"}
        n = len(rows[0.02]); r["n"] = n; r["games_per_day_all_days"] = n / span
        g = gate.get(rid(cell)) if gate else None
        r["rate_gate"] = "pending (fewer than %d tip days)" % GATE_DAYS if g is None else ("ok (first-7-day rate %.2f games a day)" % g["rate"] if not g["dropped"] else "DROPPED: first-7-day rate %.2f games a day under %.1f (a rate failure, not a bar failure)" % (g["rate"], RATE_GATE))
        for h in E.HAIRCUTS:
            rs = sorted(rows[h]); xs = [x for _, x in rs]; half = len(xs) // 2
            r["h%d" % round(h * 100)] = {"pf": E.pf(xs) if xs else None, "half1": E.pf(xs[:half]) if half else None, "half2": E.pf(xs[half:]) if xs else None, "net": sum(xs),
                "day_z": E.day_z([(time.strftime("%Y-%m-%d", time.gmtime(t)), x) for t, x in rs]), "evidence": "ok" if len(xs) >= 100 else "no evidence at n = %d" % len(xs)}
        mean2 = (sum(x for _, x in rows[0.02]) / n / E.CONTRACTS) if n else None
        r["mean_net_per_contract_2c"] = mean2
        r["dollars_a_week_at_5_contracts"] = (r["games_per_day_all_days"] * 7 * mean2 * 5) if mean2 is not None else None
        r["kill_fast"] = r["h2"]["pf"] is not None and r["h2"]["pf"] < 1.0
        out[rid(cell)] = r
    ranked = sorted((k for k, v in out.items() if v["rate_gate"].startswith("ok") and v["dollars_a_week_at_5_contracts"] is not None), key=lambda k: -out[k]["dollars_a_week_at_5_contracts"])
    res = {"m_cells_this_spec": len(CELLS), "m_with_igdriftgrid1": len(CELLS) + len(G.CELLS), "m_with_iglatedrift1": len(CELLS) + len(G.CELLS) + 1, "cells": out, "ranked_by_dollars_a_week": ranked}
    if stored_gate is None and gate is not None:
        res["gate_to_store"] = gate
    return res
