"""GEN1S (README, Pre-registration: GEN1S): GEN1 restricted to the second slot's registry shape. Research only; nothing here places an order.
    python -m scalper.gen1s build    (path rows, discovery and validation days only)
    python -m scalper.gen1s search   (generate to 5,000 distinct, gates, freeze, write forward_candidates.json)
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations

import numpy as np

from .calibration import cluster_mean_z
from .gen1 import load_markets, boot_pf5, pf, _norm_ppf, SERIES, ASSET, DISC_DAYS, N_PRIOR
from .paths import DATA_DIR

NPZ = DATA_DIR / "gen1s_rows.npz"
RESULT = DATA_DIR / "gen1s_result.txt"
FROZEN = DATA_DIR / "gen1s_survivors.json"
OUT = DATA_DIR.parent / "forward_candidates.json"
LEFTS = list(range(840, 119, -60))
PW = 14
STOP_OFF = (0.05, 0.10, 0.20, 0.30)
TGT_OFF = (0.03, 0.05, 0.10, 0.20)
MUST = (60, 120, 180)
SUBSETS = [c for r in (1, 2, 3) for c in combinations(range(3), r)]
TARGET_DISTINCT, MIN_DISC = 5000, 30


def fee(p, c, m=1.0):
    return np.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def build():
    M = load_markets(False)
    rows, paths, lefts, pv0, l1 = [], [], [], [], []
    for wid, tk in enumerate(sorted(M)):
        series, strike, close_ts, cs = M[tk]
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        keys = sorted(k for k in cs if k <= close_ts - 60)
        q1 = cs.get(close_ts - 360)
        l1side = -1
        if q1:
            if 0.88 <= q1[1] <= 0.97: l1side = 1
            elif 0.88 <= 1 - q1[0] <= 0.97: l1side = 0
        for L in LEFTS:
            t = close_ts - L; q = cs.get(t)
            if q is None:
                continue
            later = [k for k in keys if k > t][:PW]
            if not later:
                continue
            for yes in (1, 0):
                bid, ask = (q[0], q[1]) if yes else (1 - q[1], 1 - q[0])
                if not 0.03 <= ask <= 0.85:
                    continue
                pb = np.full(PW, np.nan); pl = np.full(PW, np.nan); pz = np.zeros(PW, bool)
                for j, k in enumerate(later):
                    b = cs[k][0] if yes else 1 - cs[k][1]
                    pb[j] = b; pl[j] = close_ts - k; pz[j] = cs[k][2] <= 0
                rows.append((wid, day, ASSET[series], yes, L, ask, bid, q[2] <= 0, l1side))
                paths.append(pb); lefts.append(pl); pv0.append(pz)
    days = sorted({r[1] for r in rows}); didx = {d: i for i, d in enumerate(days)}
    A = np.array([[r[2], r[3], r[4], r[5], r[6], r[7], r[8]] for r in rows], dtype=np.float32)
    wid = np.array([r[0] for r in rows]); day = np.array([didx[r[1]] for r in rows])
    order = np.lexsort((-A[:, 1], -A[:, 2], wid))
    np.savez(NPZ, A=A[order], P=np.array(paths, dtype=np.float32)[order], PL=np.array(lefts, dtype=np.float32)[order],
             PZ=np.array(pv0)[order], wid=wid[order], day=day[order], days=np.array(days))
    print("rows", len(rows), "days", len(days), "windows", len(M), flush=True)


def load():
    z = np.load(NPZ)
    return {k: z[k] for k in z.files}


def draw(rng):
    side = rng.choice(["yes", "no", "favourite"])
    lo_p = 50 if side == "favourite" else 5
    width = rng.choice(range(5, 41, 5))
    pmin = rng.choice([p for p in range(lo_p, 86, 5) if p + width <= 85])
    wsec = rng.choice(range(60, 601, 60))
    lmax = rng.choice([L for L in range(180, 841, 60) if L - wsec >= 120])
    lmin = lmax - wsec
    must = rng.choice([m for m in MUST if m < lmin])
    so = rng.randrange(len(STOP_OFF)); to = rng.randrange(len(TGT_OFF))
    return {"series": rng.choice(SUBSETS), "side": side, "pmin": pmin / 100, "pmax": (pmin + width) / 100, "lmax": lmax, "lmin": lmin,
            "so": so, "to": to, "must": must}


def stop_tgt(s):
    return max(0.01, round(s["pmin"] - STOP_OFF[s["so"]], 2)), min(0.99, round(s["pmax"] + TGT_OFF[s["to"]], 2))


def trades(D, s, split):
    A = D["A"]
    m = split & np.isin(A[:, 0], s["series"]) & (A[:, 2] <= s["lmax"]) & (A[:, 2] >= s["lmin"]) & (A[:, 3] >= s["pmin"] - 1e-9) & (A[:, 3] <= s["pmax"] + 1e-9)
    if s["side"] == "yes":
        m &= A[:, 1] == 1
    elif s["side"] == "no":
        m &= A[:, 1] == 0
    else:
        m &= A[:, 3] >= 0.5
    idx = np.flatnonzero(m)
    if len(idx) == 0:
        return idx
    w = D["wid"][idx]
    return idx[np.r_[True, w[1:] != w[:-1]]]


def outcome(D, s, idx):
    stop, tgt = stop_tgt(s)
    P = D["P"][idx]; PL = D["PL"][idx]; PZ = D["PZ"][idx]
    valid = ~np.isnan(P)
    hit = valid & ((P >= tgt - 1e-9) | (P <= stop + 1e-9) | (PL <= s["must"]))
    last = valid.sum(axis=1) - 1
    first = np.where(hit.any(axis=1), hit.argmax(axis=1), last)
    r = np.arange(len(idx))
    xb = P[r, first].astype(np.float64); e = D["A"][idx, 3].astype(np.float64)
    zv = PZ[r, first] | (D["A"][idx, 5] > 0)
    return {"n10": xb - e - fee(e, 10) - fee(xb, 10), "n1": xb - e - fee(e, 1) - fee(xb, 1), "ns": xb - e - fee(e, 10, 1.2) - fee(xb, 10, 1.2), "zv": zv}


def score(D, s, idx):
    o = outcome(D, s, idx)
    days = D["day"][idx]
    _, _, z = cluster_mean_z(list(zip(days.tolist(), o["n10"].tolist()))) if len(idx) > 1 else (0, 0, 0.0)
    return {"n": int(len(idx)), "days": int(len(set(days.tolist()))), "pf": pf(o["n10"]), "pf1": pf(o["n1"]), "pfs": pf(o["ns"]),
            "zv": float(o["zv"].mean()) if len(idx) else 1.0, "mean_c": float(100 * o["n10"].mean()) if len(idx) else 0.0,
            "loss": float((o["n10"] < 0).mean()) if len(idx) else 0.0, "z": float(z)}, o


def near(a, b):
    return abs(a["so"] - b["so"]) <= 1 and abs(a["to"] - b["to"]) <= 1 and abs(MUST.index(a["must"]) - MUST.index(b["must"])) <= 1


def gen1_generated():
    p = DATA_DIR / "gen1_result.txt"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith("GEN1: generated"):
                return int(line.split("generated ")[1].split(",")[0])
    return 400_000  # GEN1 not finished: its maximum, so the bar is not lower than it should be


def search():
    D = load()
    disc = D["day"] < DISC_DAYS; val = ~disc
    rng = random.Random(20261029 + 1)
    distinct, generated = [], 0
    while len(distinct) < TARGET_DISTINCT and generated < 300_000:
        s = draw(rng); generated += 1
        idx = trades(D, s, disc)
        if len(idx) < MIN_DISC:
            continue
        ws = set(D["wid"][idx].tolist())
        if any(near(s, s2) and len(ws & ws2) / len(ws | ws2) > 0.5 for s2, ws2, _ in distinct):
            continue
        sc, _ = score(D, s, idx)
        distinct.append((s, ws, sc))
        if len(distinct) % 500 == 0:
            print("distinct", len(distinct), "generated", generated, flush=True)
    N_total = N_PRIOR + gen1_generated() + generated
    zbar = _norm_ppf(1 - 0.05 / N_total)
    res = []
    for s, ws, dsc in distinct:
        stage, fail = "discovery", None
        if not (dsc["pf"] >= 1.5): fail = "DISCOVERY_PF"
        elif not (dsc["n"] >= 150 and dsc["days"] >= 25): fail = "DISCOVERY_N"
        elif not (dsc["zv"] <= 0.2): fail = "FILL_OPTIMISM"
        vsc = None; b5 = None
        if fail is None:
            idx = trades(D, s, val); vsc, o = score(D, s, idx)
            if not (vsc["n"] >= 60 and vsc["days"] >= 15): fail = "VALIDATION_N"
            elif not (vsc["pf"] >= 1.5): fail = "VALIDATION_PF"
            elif not (vsc["pfs"] >= 1.2): fail = "VALIDATION_STRESS"
            elif not (vsc["zv"] <= 0.2): fail = "FILL_OPTIMISM"
            else:
                b5 = boot_pf5(o["n10"], D["day"][idx])
                if not (b5 > 1.0): fail = "VALIDATION_BOOTSTRAP"
                elif not (vsc["z"] >= zbar): fail = "DEFLATION"
            stage = "validation"
        res.append({"s": s, "disc": dsc, "valid": vsc, "boot5": b5, "fail": fail, "stage": stage})
    d_pass = [r for r in res if r["stage"] == "validation"]
    full = [r for r in res if r["fail"] is None]
    order = {"DEFLATION": 6, "VALIDATION_BOOTSTRAP": 5, "VALIDATION_STRESS": 4, "VALIDATION_PF": 3, "VALIDATION_N": 2, None: 7}
    ranked = sorted(d_pass, key=lambda r: (order.get(r["fail"], 0), (r["valid"] or {}).get("pf", 0)), reverse=True)
    if len(ranked) < 5:
        ranked += sorted([r for r in res if r["stage"] == "discovery"], key=lambda r: r["disc"]["pf"], reverse=True)[:5 - len(ranked)]
    lines = [f"GEN1S: generated {generated}, distinct {len(distinct)}; N tried for deflation {N_total}, Bonferroni z bar {zbar:.2f}",
             f"passed discovery {len(d_pass)}; failed in validation by gate: " + ", ".join(f"{k} {sum(1 for r in d_pass if r['fail'] == k)}" for k in ("VALIDATION_N", "VALIDATION_PF", "VALIDATION_STRESS", "FILL_OPTIMISM", "VALIDATION_BOOTSTRAP", "DEFLATION")) + f"; passed every validation gate incl. deflation {len(full)}"]
    cands = []
    for i, r in enumerate(ranked[:10]):
        s = r["s"]; stop, tgt = stop_tgt(s)
        idx_v = trades(D, s, val); l1 = D["A"][idx_v, 6]; side = D["A"][idx_v, 1]
        same = int(((l1 >= 0) & (l1 == side)).sum()); opp = int(((l1 >= 0) & (l1 != side)).sum())
        label = "PASSED_ALL_GATES_TO_VALIDATION (FINAL HOLDOUT not yet read; registered for 2026-11-08)" if r["fail"] is None else "FAILED_GATE_" + r["fail"]
        cid = f"G1S{i + 1:02d}"
        cand = {"id": cid, "readme": "kalshi-scalper/README.md#pre-registration-gen1s-the-same-generator-restricted-to-the-second-slots-registry-shape",
                "series": [SERIES[a] for a in s["series"]],
                "entry": {"sideRule": s["side"], "priceMin": s["pmin"], "priceMax": s["pmax"], "leftMaxSec": s["lmax"], "leftMinSec": s["lmin"]},
                "exit": {"stopBid": stop, "targetBid": tgt, "mustExitLeftSec": s["must"]},
                "contractsPerOrder": 10, "scaleIn": {"maxSteps": 1, "minGapSec": 30, "sameSideOnly": True, "requirePriorFilled": True},
                "killRules": {"maxConsecutiveLosses": 4, "minNet": {"afterFills": 30, "net": -2.0}}, "forwardReadDate": "2026-11-19",
                "research": {"rank": i + 1, "label": label, "stageReached": r["stage"], "window": {"discovery": "2026-08-05 to day 55", "validation": "days 56 to 83, to 2026-10-27 23:45 UTC"},
                             "discovery": r["disc"], "validation": r["valid"], "bootstrap5thPctPF": r["boot5"], "deflation": {"nTried": N_total, "zBar": round(zbar, 2), "z": (r["valid"] or {}).get("z")},
                             "positiveAtFeesX1_2": bool(r["valid"] and r["valid"]["pfs"] > 1.0),
                             "counterparty": "takers who cross the spread mid-window in this price band (impatient or late traders); unproven unless it passes the holdout",
                             "l1OverlapValidation": {"windows": int(len(idx_v)), "l1SameSide": same, "l1OppositeSide": opp, "note": "opposite side would be refused by the slot's direction rule"}}}
        cands.append(cand)
        v = r["valid"] or {}
        lines.append(f"  #{i + 1} {cid} {label}: {json.dumps(cand['series'])} {s['side']} {s['pmin']:.2f}-{s['pmax']:.2f} at {s['lmax']}..{s['lmin']}s, stop {stop} target {tgt} exit {s['must']}s | disc PF {r['disc']['pf']:.2f} n={r['disc']['n']} | valid PF {v.get('pf', 0):.2f} (1 contract {v.get('pf1', 0):.2f}, stress {v.get('pfs', 0):.2f}) n={v.get('n', 0)} days {v.get('days', 0)} loss {100 * v.get('loss', 0):.0f}% z {v.get('z', 0):+.2f} boot5 {r['boot5'] if r['boot5'] is not None else 'n/a'} | L1 same {same} opposite {opp}")
    verdict = "NO_WINNER (nothing passes every validation gate; FALSIFIED before the holdout)" if not full else f"{len(full)} pass every validation gate and are frozen for the holdout"
    lines.insert(0, f"GEN1S VERDICT so far: {verdict}")
    FROZEN.write_text(json.dumps({"frozen_at": datetime.now(timezone.utc).isoformat(), "survivors": [r["s"] for r in full]}, default=list, indent=1))
    OUT.write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "source": "GEN1S (README)", "verdict": verdict,
                               "note": "Ranked best first. Labels are the registered gates; nothing here has passed a FINAL HOLDOUT. No promote verb; the owner decides.",
                               "candidates": cands}, indent=1, default=list))
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"build": build, "search": search}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
