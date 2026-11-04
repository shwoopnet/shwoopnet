"""PRICEMATCH1 (README "PRICEMATCH1"; workers/PRICEMATCH1_REGISTRATION.md): after exact price matching (ask in 1c bins 3..30), is there ANY liquidity
feature (spread, candle volume, event overround) whose within-bin net differs from zero-difference? Descriptive. Cheap side only (owner rule): no entry
above 0.30 is built, counted, scored or printed. Reuses the LIQ1 feature pool (LIQ1_OUT/features.jsonl) and OVERROUND1's event overround; no Kalshi fetch.

Usage: python3 -I -m scalper.pricematch1 census   counts per cell only, no outcome
       python3 -I -m scalper.pricematch1 score    ONE run -> workers/PRICEMATCH1_RESULT.json (refuses a second run)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

from scalper import calib1 as C

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKERS = ROOT / "workers"
LIQ = Path(os.environ.get("LIQ1_OUT", "/tmp/liq1"))
SEED, BOOT = 20261104, 2000
MAX_PER_EVENT = 2
MIN_N = 150            # a decisive cell under this is NOT_ENOUGH_DATA
MIN_BIN = 5            # a bin contributes to a within-bin difference only with >= 5 entries on each side
CUTS = {"spread_lo": 2.0, "spread_hi": 5.0, "vol_lo": 0.0, "vol_hi": 30.93, "ov_lo": 0.07, "ov_hi": 0.12}
BINS = list(range(3, 31))   # ask in cents
# feature -> (favoured level, opposite level); the claim is net(favoured) - net(opposite) > 0 within ask bins
FEATURES = {"spread": ("TIGHT", "WIDE"), "volume": ("HIGHV", "LOWV"), "overround": ("LOWOR", "HIGHOR")}


def bin_of(ask: float) -> int:
    b = int(round(ask * 100))
    assert 3 <= b <= 30, "entry outside the cheap-side band"
    return b


def levels(r) -> dict:
    """Level of each feature for one entry (None when the feature is not available or in the middle)."""
    s = r["spread_c"]
    sp = "TIGHT" if s <= CUTS["spread_lo"] + 1e-9 else "WIDE" if s >= CUTS["spread_hi"] - 1e-9 else "MIDSP"
    v = r["vol"]
    vo = "HIGHV" if v > CUTS["vol_hi"] + 1e-9 else "LOWV" if v <= CUTS["vol_lo"] + 1e-9 else "MIDV"
    o = r.get("ov")
    orr = None if o is None else "LOWOR" if o < CUTS["ov_lo"] - 1e-9 else "HIGHOR" if o >= CUTS["ov_hi"] - 1e-9 else "MIDOR"
    return {"spread": sp, "volume": vo, "overround": orr}


def cap_per_event(rows, k=MAX_PER_EVENT):
    by = {}
    for r in rows:
        by.setdefault(r["event"], []).append(r)
    out = []
    for e, rs in by.items():
        out += sorted(rs, key=lambda r: hashlib.md5(f"{r['market']}|{r['look']}".encode()).hexdigest())[:k]
    return out


def load_pool(with_results: bool):
    feats = [json.loads(x) for x in open(LIQ / "features.jsonl")]
    assert all(f["ask"] <= C.ASK_HI + 1e-9 for f in feats)
    ov = event_look_overround()
    for f in feats:
        f["ov"] = ov.get((f["event"], f["look"]))
    rows = cap_per_event(feats)
    if with_results:
        res = json.load(open(LIQ / "res.json"))
        for f in rows:
            won = f["side"] == res[f["market"]]
            f["won"] = 1 if won else 0
            f["net"] = C.net_per_contract(won, f["ask"])
    for f in rows:
        f["bin"] = bin_of(f["ask"])
        f["lv"] = levels(f)
    return rows


def event_look_overround():
    """OVERROUND1's event overround per (event, look) from the weather sweep cache (structure and quotes only, no outcome)."""
    from scalper import overround1 as O
    O.SWEEP = Path(os.environ.get("OVR1_SWEEP", str(O.SWEEP)))
    return {(r["event"], r["look"]): r["ov"] for r in O.build(False)}


def halves(rows):
    t = {}
    for r in rows:
        t[r["event"]] = min(t.get(r["event"], r["t"]), r["t"])
    order = sorted(t, key=lambda e: (t[e], e))
    first = set(order[: len(order) // 2])
    return [r for r in rows if r["event"] in first], [r for r in rows if r["event"] not in first]


def mh_diff(S1, N1, S0, N0, bins_ok):
    """Mantel-Haenszel style pooled difference of means (fav minus opp) over bins with both sides present: weights n1*n0/(n1+n0).
    Inputs are per-bin arrays (last axis = bins); returns the pooled difference."""
    ok = bins_ok
    n1, n0 = N1[..., ok], N0[..., ok]
    d = S1[..., ok] / np.maximum(n1, 1) - S0[..., ok] / np.maximum(n0, 1)
    w = n1 * n0 / np.maximum(n1 + n0, 1)
    return (w * d).sum(axis=-1) / np.maximum(w.sum(axis=-1), 1e-12)


def event_bin_matrices(rows, fav, opp, feature):
    ev = sorted({r["event"] for r in rows})
    ix = {e: i for i, e in enumerate(ev)}
    S1, N1, S0, N0 = (np.zeros((len(ev), len(BINS))) for _ in range(4))
    for r in rows:
        lv = r["lv"][feature]
        j = r["bin"] - 3
        if lv == fav:
            S1[ix[r["event"]], j] += r["net"]; N1[ix[r["event"]], j] += 1
        elif lv == opp:
            S0[ix[r["event"]], j] += r["net"]; N0[ix[r["event"]], j] += 1
    return S1, N1, S0, N0


def pooled_difference(rows, feature, rng, B=BOOT):
    fav, opp = FEATURES[feature]
    S1, N1, S0, N0 = event_bin_matrices(rows, fav, opp, feature)
    n1, n0 = N1.sum(), N0.sum()
    ok = (N1.sum(0) >= MIN_BIN) & (N0.sum(0) >= MIN_BIN)
    if n1 < MIN_N or n0 < MIN_N or not ok.any():
        return {"verdict": "NOT_ENOUGH_DATA", "n_fav": int(n1), "n_opp": int(n0), "bins_used": int(ok.sum())}
    est = float(mh_diff(S1.sum(0), N1.sum(0), S0.sum(0), N0.sum(0), ok))
    k = S1.shape[0]
    out = np.empty(B)
    step = max(1, 2_000_000 // k)
    for i in range(0, B, step):
        c = np.stack([np.bincount(rng.integers(0, k, size=k), minlength=k) for _ in range(min(step, B - i))])
        out[i:i + c.shape[0]] = mh_diff(c @ S1, c @ N1, c @ S0, c @ N0, ok)
    out.sort()
    return {"diff": est, "lo": float(out[int(0.025 * B)]), "hi": float(out[int(0.975 * B) - 1]), "n_fav": int(n1), "n_opp": int(n0),
            "bins_used": int(ok.sum()), "events": k}


def cell_stats(rows, binmean, rng, B=BOOT):
    n = len(rows)
    if n == 0:
        return {"n": 0}
    g = {}
    for r in rows:
        x = g.setdefault(r["event"], np.zeros(3))
        x += (r["net"], r["net"] - binmean[r["bin"]], 1)
    M = np.array(list(g.values()))
    k = len(M)
    nets, exc = np.empty(B), np.empty(B)
    for i in range(B):
        s = M[rng.integers(0, k, size=k)].sum(axis=0)
        nets[i], exc[i] = s[0] / s[2], s[1] / s[2]
    nets.sort(); exc.sort()
    w = sum(r["won"] for r in rows) / n
    pf_w = sum(r["net"] for r in rows if r["net"] > 0)
    pf_l = -sum(r["net"] for r in rows if r["net"] < 0)
    return {"n": n, "events": k, "win": w, "price": sum(r["ask"] for r in rows) / n, "net": sum(r["net"] for r in rows) / n,
            "lo": float(nets[int(0.025 * B)]), "hi": float(nets[int(0.975 * B) - 1]),
            "lo_bonf": float(nets[int(0.025 / 9 * B)]),     # 9 registered cells, one-sided-ish Bonferroni lower bound (0.28 percentile)
            "excess": sum(r["net"] - binmean[r["bin"]] for r in rows) / n, "exc_lo": float(exc[int(0.025 * B)]), "exc_hi": float(exc[int(0.975 * B) - 1]),
            "pf": pf_w / pf_l if pf_l > 0 else float("inf")}


def census():
    rows = load_pool(False)
    print(f"{len(rows)} cheap entries after max {MAX_PER_EVENT} per event, {len({r['event'] for r in rows})} events (COUNTS ONLY; no outcome joined)")
    print("cuts:", CUTS)
    for f, (a, b) in FEATURES.items():
        names = sorted({r["lv"][f] for r in rows if r["lv"][f]})
        print(f"  {f}: " + ", ".join(f"{n} {sum(1 for r in rows if r['lv'][f] == n)}" for n in names) + f"; none {sum(1 for r in rows if r['lv'][f] is None)}")
        S1, N1, S0, N0 = event_bin_matrices([dict(r, net=0.0) for r in rows], a, b, f)
        ok = (N1.sum(0) >= MIN_BIN) & (N0.sum(0) >= MIN_BIN)
        print(f"    bins with >= {MIN_BIN} on both sides: {int(ok.sum())} of {len(BINS)}; entries in those bins {a} {int(N1.sum(0)[ok].sum())}, {b} {int(N0.sum(0)[ok].sum())}")


def score(force=False):
    path = WORKERS / "PRICEMATCH1_RESULT.json"
    if path.exists() and not force:
        raise SystemExit("already run: workers/PRICEMATCH1_RESULT.json exists (run once)")
    rows = load_pool(True)
    rng = np.random.default_rng(SEED)
    d1, d2 = halves(rows)
    sums, cnts = np.zeros(31), np.zeros(31)
    for r in rows:
        sums[r["bin"]] += r["net"]; cnts[r["bin"]] += 1
    binmean = {b: (sums[b] / cnts[b] if cnts[b] else 0.0) for b in range(31)}
    out = {"entries": len(rows), "events": len({r["event"] for r in rows}), "cuts": CUTS, "claims": {}, "cells": {}}
    for f in FEATURES:
        res = {"all": pooled_difference(rows, f, rng), "D1": pooled_difference(d1, f, rng), "D2": pooled_difference(d2, f, rng)}
        h = [res["D1"], res["D2"]]
        holds = all("diff" in x and x["diff"] > 0 and x["lo"] > 0 for x in h)
        res["verdict"] = "NOT_ENOUGH_DATA" if any("diff" not in x for x in h) else ("SUPPORTED" if holds else "FALSIFIED")
        out["claims"][f] = res
    cells = {"CONTROL": lambda r: True}
    for f, (a, b) in FEATURES.items():
        for lv in sorted({r["lv"][f] for r in rows if r["lv"][f]}):
            cells[lv] = (lambda f, lv: lambda r: r["lv"][f] == lv)(f, lv)
    for name, fn in cells.items():
        sel = [r for r in rows if fn(r)]
        a, b = halves(sel)
        c = {"all": cell_stats(sel, binmean, rng), "D1": cell_stats(a, binmean, rng), "D2": cell_stats(b, binmean, rng)}
        c["verdict"] = ("NOT_ENOUGH_DATA" if c["all"]["n"] < MIN_N else
                        "LEAD_CANDIDATE" if all(c[h]["n"] and c[h]["lo"] > 0 for h in ("D1", "D2")) else
                        "ABOVE_ZERO_BOTH_HALVES" if all(c[h]["n"] and c[h]["net"] > 0 for h in ("D1", "D2")) else "NEGATIVE_OR_NOT_BOTH")
        out["cells"][name] = c
    reg = [n for n in out["cells"] if n != "CONTROL" and out["cells"][n]["all"]["n"] >= MIN_N]
    best = max(reg, key=lambda n: out["cells"][n]["all"]["net"]) if reg else None
    out["best_cell"] = best
    out["pooled_overall_verdict"] = ("FALSIFIED" if not any(out["cells"][n]["verdict"] in ("LEAD_CANDIDATE", "ABOVE_ZERO_BOTH_HALVES") for n in reg) else "SEE_CELLS")
    path.write_text(json.dumps(out, indent=1))
    return out


def fmt(s):
    if not s.get("n"):
        return "n=0"
    return (f"n={s['n']} ev={s['events']} win={100*s['win']:.2f}% px={100*s['price']:.2f}c net={100*s['net']:+.2f}c [{100*s['lo']:+.2f},{100*s['hi']:+.2f}] "
            f"vs bin mean {100*s['excess']:+.2f}c [{100*s['exc_lo']:+.2f},{100*s['exc_hi']:+.2f}] PF={s['pf']:.2f}")


def report(out):
    print(f"{out['entries']} entries, {out['events']} events")
    for f, r in out["claims"].items():
        print(f"{f}: {r['verdict']}")
        for k in ("all", "D1", "D2"):
            x = r[k]
            print(f"   {k}: " + (f"diff {100*x['diff']:+.2f}c [{100*x['lo']:+.2f},{100*x['hi']:+.2f}] n {x['n_fav']}/{x['n_opp']} bins {x['bins_used']}" if "diff" in x else str(x)))
    for n, c in out["cells"].items():
        print(f"{n:8s} {c['verdict']}\n   all: {fmt(c['all'])}\n   D1: {fmt(c['D1'])}\n   D2: {fmt(c['D2'])}")
    print("best cell:", out["best_cell"], "overall:", out["pooled_overall_verdict"])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "census":
        census()
    elif cmd == "score":
        report(score())
    else:
        print(__doc__)
