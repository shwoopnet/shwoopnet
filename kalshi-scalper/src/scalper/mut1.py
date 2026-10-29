"""MUT1 (README, Pre-registration: MUT1): one-step mutations of GEN1's five near-misses, frozen now, judged once on GEN1's holdout.
    python -m scalper.mut1 freeze     (scores parents and mutations on discovery and validation, writes the frozen list)
    python -m scalper.mut1 holdout    (once, on or after 2026-11-08, after gen1's holdout rows are built)
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone

import numpy as np

from . import gen1 as G
from .paths import DATA_DIR

PARENTS = DATA_DIR.parent / "studies" / "gen1_top_info_2026-10-29.txt"
FROZEN = DATA_DIR.parent / "studies" / "mut1_frozen_2026-10-29.json"
RESULT = DATA_DIR / "mut1_result.txt"
ASSETS = {"all": None, "BTC": 0, "ETH": 1, "GOLD": 2}
PAT = re.compile(r"^\[(\w+) (yes|no|both) (\d+)\.\.(\d+)s left \| (.*?) \| TP (\w+) stop (\w+) time (\d+)s book (\w+)\] \| disc PF ([\d.]+) n=(\d+)")


def parse(Q):
    out = []
    for line in PARENTS.read_text().splitlines():
        m = PAT.match(line.strip())
        if not m:
            continue
        a, side, hi, lo, conds, tp, st, te, bk, dpf, dn = m.groups()
        cs = []
        for c in conds.split(" & "):
            f, op, th = re.match(r"(\w+?)(<=|>)(.+)", c).groups()
            qv = min(range(10, 91, 10), key=lambda q: abs(Q[f][q] - float(th)))
            cs.append([f, "le" if op == "<=" else "gt", qv])
        pick = lambda seq, txt: None if txt == "none" else next(x for x in seq if x is not None and round(x * 100) == int(txt))
        c = G.COMBOS.index((pick(G.TP, tp), pick(G.ST, st), int(te), bk))
        out.append(({"L_hi": int(hi), "L_lo": int(lo), "side": side, "asset": ASSETS[a], "qconds": cs, "c": c}, float(dpf), int(dn)))
    return out


def materialise(s, Q):
    t = {k: v for k, v in s.items() if k != "qconds"}
    t["conds"] = [(f, op, float(Q[f][qv])) for f, op, qv in s["qconds"]]
    return t


def mutations(p):
    out = []
    for i, (f, op, qv) in enumerate(p["qconds"]):
        for d in (-20, -10, 10, 20):
            if 10 <= qv + d <= 90:
                m = copy.deepcopy(p); m["qconds"][i][2] = qv + d; out.append(("thr", m))
    for end, d in (("L_hi", 60), ("L_hi", -60), ("L_lo", 60), ("L_lo", -60)):
        m = copy.deepcopy(p); m[end] += d
        if 180 <= m["L_lo"] and m["L_hi"] <= 840 and m["L_hi"] - m["L_lo"] >= 60:
            out.append(("window", m))
    tp, st, te, bk = G.COMBOS[p["c"]]
    for seq, pos in ((G.TP, 0), (G.ST, 1), (G.TE, 2)):
        cur = (tp, st, te)[pos]
        j = seq.index(cur)
        for k in (j - 1, j + 1):
            if 0 <= k < len(seq):
                v = [tp, st, te, bk]; v[pos] = seq[k]
                m = copy.deepcopy(p); m["c"] = G.COMBOS.index(tuple(v)); out.append(("exit", m))
    for sd in ("yes", "no", "both"):
        if sd != p["side"]:
            m = copy.deepcopy(p); m["side"] = sd; out.append(("side", m))
    return out


def freeze():
    if FROZEN.exists():
        print("Refusing to run again"); return
    D = G.load()
    disc, val = D["day"] < G.DISC_DAYS, D["day"] >= G.DISC_DAYS
    X = D["X"]
    Q = {f: np.percentile(X[disc][:, G.FEATS.index(f)], list(range(0, 101))) for f in G.GRAMMAR_FEATS}
    lines, frozen, tried = [], [], 0
    for k, (p, dpf, dn) in enumerate(parse(Q)):
        ps = materialise(p, Q)
        sc = G.score(D, G.trades(D, ps, disc), ps["c"])
        ok = abs(sc["pf"] - dpf) <= 0.03
        lines.append(f"parent {k + 1}: {G.desc(ps)} | listed disc PF {dpf:.2f} n={dn}, snapped {sc['pf']:.2f} n={sc['n']} {'kept' if ok else 'DROPPED (snap mismatch)'}")
        if not ok:
            continue
        for kind, m in [("parent", p)] + mutations(p):
            tried += 1
            ms = materialise(m, Q)
            d = G.score(D, G.trades(D, ms, disc), ms["c"]); v = G.score(D, G.trades(D, ms, val), ms["c"])
            sel = d["pf"] >= 1.3 and d["n"] >= 100 and d["days"] >= 20 and v["pf"] >= 1.3 and v["n"] >= 50 and v["days"] >= 10 and d["zv"] <= 0.2 and v["zv"] <= 0.2
            if sel:
                frozen.append({"parent": k + 1, "kind": kind, "strategy": ms, "disc": d, "valid": v})
            lines.append(f"  {'FROZEN' if sel else '      '} {kind:6s} disc PF {d['pf']:.2f} n={d['n']} days {d['days']} | valid PF {v['pf']:.2f} n={v['n']} days {v['days']}")
    body = json.dumps({"frozen_at": datetime.now(timezone.utc).isoformat(), "tried": tried, "survivors": frozen}, indent=1, default=float)
    FROZEN.write_text(body)
    h = hashlib.sha256(body.encode()).hexdigest()
    lines.insert(0, f"MUT1 freeze: {tried} tried (parents included), {len(frozen)} frozen; sha256 {h}" + ("; nothing frozen: FALSIFIED (registered kill)" if not frozen else "; holdout read once on or after 2026-11-08"))
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


def holdout():
    out = DATA_DIR / "mut1_holdout_result.txt"
    if out.exists():
        print("Refusing to run again"); return
    if datetime.now(timezone.utc) < datetime(2026, 11, 8, tzinfo=timezone.utc):
        print("Refused: the holdout is read on or after 2026-11-08"); return
    fz = json.loads(FROZEN.read_text())["survivors"]
    if not G.HOLD_NPZ.exists():
        G.build(holdout=True)
    D = G.load(G.HOLD_NPZ)
    alls = np.ones(len(D["X"]), bool)
    lines, byparent = [], {}
    for r in fz:
        s = r["strategy"]; s["conds"] = [tuple(c) for c in s["conds"]]
        idx = G.trades(D, s, alls); sc = G.score(D, idx, s["c"])
        byparent.setdefault(r["parent"], []).append(sc["pf"])
        r["hold"] = sc
    ok = []
    for r in fz:
        sc, nb = r["hold"], byparent[r["parent"]]
        plateau = sum(1 for x in nb if x >= 1.0) >= len(nb) / 2
        p = sc["pf"] >= 1.5 and sc["n"] >= 60 and sc["days"] >= 10 and sc["pfs"] >= 1.2 and plateau
        ok.append(p)
        lines.append(f"  {'PASS' if p else 'fail'} parent {r['parent']} {r['kind']} {G.desc(r['strategy'])} | holdout PF {sc['pf']:.2f} n={sc['n']} days {sc['days']} stress {sc['pfs']:.2f} plateau {plateau}")
    lines.insert(0, "MUT1 holdout VERDICT: " + ("NOT_YET_FALSIFIED (then: independent re-implementation and forward paper read)" if any(ok) else "FALSIFIED"))
    out.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"freeze": freeze, "holdout": holdout}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
