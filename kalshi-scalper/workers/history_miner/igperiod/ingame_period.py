"""ingame_period.py: scorer plugin for IGPERIOD1 (History Miner, Nov 16, 2026). Card IGPERIOD1_CARD_NOV16.md. Pure functions, no I/O.
Reuses the signed ingame_events.py (4698bae0) through the cleared ingame_drift_grid.py (6a4e63c8), both pinned. Upper bound, not fill-checked."""
import collections, hashlib, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
GRID_SHA256 = "6a4e63c897a1ff93bd36777330398fbd5f7392274230c938d586b1b005914b4d"
if hashlib.sha256(open(os.path.join(HERE, "..", "igdriftgrid", "ingame_drift_grid.py"), "rb").read()).hexdigest() != GRID_SHA256:
    raise SystemExit("REFUSED: ingame_drift_grid.py is not the cleared file (sha256 %s)" % GRID_SHA256)
sys.path.insert(0, os.path.join(HERE, "..", "igdriftgrid"))
import ingame_drift_grid as G
E = G.E
FLAT = 0.005; QUIET = 720; MAXGAP = 360; EARLIEST = 30 * 60; LATEST = 140 * 60; EPS = 1e-9
CELLS = [(b, th, di) for b in (1, 2) for th in (0.02, 0.04) for di in ("follow", "fade")]
RATE_GATE = G.RATE_GATE; GATE_DAYS = G.GATE_DAYS


def rid(cell):
    return "IGPD_B%d_%02d_%s" % (cell[0], round(cell[1] * 100), cell[2].upper())


def stretches(rows, tip):
    """quiet stretches of one ticker: -> [(t_start, level_mid, after_poll(t, bid, ask))], in time order, those STARTING in [tip + 30 min, tip + 140 min]."""
    polls = [(t, b, a) for t, b, a in rows if E.two(b, a)]
    out = []; i = 0
    while i < len(polls):
        base = (polls[i][1] + polls[i][2]) / 2; j = i
        while j + 1 < len(polls) and polls[j + 1][0] - polls[j][0] <= MAXGAP and abs((polls[j + 1][1] + polls[j + 1][2]) / 2 - base) <= FLAT + EPS:
            j += 1
        if j + 1 < len(polls) and polls[j][0] - polls[i][0] >= QUIET and polls[j + 1][0] - polls[j][0] <= MAXGAP and EARLIEST <= polls[i][0] - tip <= LATEST:
            out.append((polls[i][0], base, polls[j + 1])); i = j + 1
        else:
            i = i + 1 if j == i else j
    return out


def decide(ev, cell):
    b, theta, direction = cell
    if ev["league"] != "NHL" or ev["kind"] not in ("total", "ml"):
        return "not in wall", None
    tip = E.tip_of(ev)
    if tip is None:
        return "schedule test failed", None
    tks = sorted(ev["rows"])[:1] if ev["kind"] == "ml" else sorted(ev["rows"])
    cands = []
    for tk in tks:
        st = stretches(ev["rows"][tk], tip)
        if len(st) >= b:
            cands.append((st[b - 1][2][0], tk, st[b - 1]))           # (decision time, ticker, the b-th stretch): known at that poll
    if not cands:
        return "no boundary", None
    cands.sort(key=lambda c: (c[0], c[1]))                           # the rung whose boundary comes FIRST is the one a live rule acts on (Auditor B, no end-of-game ticker choice)
    _t, tk, (_t0, level, after) = cands[0]
    d = (after[1] + after[2]) / 2 - level
    if abs(d) < theta - EPS:
        return "no signal", None
    yes = (d > 0) if direction == "follow" else (d < 0)
    side, ask = ("yes", after[2]) if yes else ("no", round(1 - after[1], 6))
    if 0.20 - EPS <= ask <= 0.80 + EPS:
        return "ok", {"ticker": tk, "side": side, "ask": ask, "t": after[0]}
    return "ask out of range", None


def in_scope(ev):
    return ev["league"] == "NHL" and ev["kind"] in ("total", "ml")


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
        r = {"cell": {"boundary": cell[0], "threshold": cell[1], "direction": cell[2]}, "skips": dict(skips), "days_with_games": span, "unit": "games (one trade per game, kind and boundary)"}
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
    res = {"m_cells_this_spec": len(CELLS), "m_with_all_ingame_specs": len(CELLS) + 11 + 12 + 1 + 1, "cells": out, "ranked_by_dollars_a_week": ranked}
    if stored_gate is None and gate is not None:
        res["gate_to_store"] = gate
    return res
