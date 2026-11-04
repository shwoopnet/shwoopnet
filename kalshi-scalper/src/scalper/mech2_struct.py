"""MECH2S (workers/MECH2S_REGISTRATION.md): scores the seven remaining MECH1S mechanisms once, reusing mech1_struct's pool, cap, split, fee and judge.
Cheap side only (ask <= 0.30 asserted). No fetch. Usage: python3 -I -m scalper.mech2_struct score  (refuses a second run)."""
from __future__ import annotations

import json
import sys

import numpy as np

from scalper import mech1_struct as M

TOP = ["PATH_FALL", "VS_OPEN", "WEEKEND", "SHOULDER", "SPREADM", "FEE_WASTE", "VOLRANK"]
NOT_SCORED = ["OFFHOURS", "YDAY"]


def eligible(rows):
    """Capped treated rows per part (D1, D2, TEST) for every mechanism, features only."""
    d1, d2, te = M.split_events(rows)
    out = {}
    for name in M.MECH:
        t = M.cap_per_event(M.treated(rows, name, 0))
        out[name] = tuple(sum(1 for r in t if r["event"] in s) for s in (d1, d2, te))
    return out


def qualifies(counts, k=150):
    return min(counts) >= k


def score(force=False):
    path = M.WORKERS / "MECH2S_RESULT.json"
    if path.exists() and not force:
        raise SystemExit("already run: workers/MECH2S_RESULT.json exists (run once)")
    rows = M.load_rows()
    assert len(rows) == 16201
    el = eligible(rows)
    assert all(qualifies(el[n]) for n in TOP) and not any(qualifies(el[n]) for n in NOT_SCORED)
    results = json.loads((M.OUT / "res.json").read_text())
    d1, d2, te = M.split_events(rows)
    rng = np.random.default_rng(M.SEED)
    out = {}
    for name in TOP:
        res = {}
        for arm, lab in ((0, "treated"), (1, "placebo")):
            t = M.attach(M.cap_per_event(M.treated(rows, name, arm)), results)
            assert all(r["ask"] <= M.CAP + 1e-9 for r in t)
            parts = {"D1": [r for r in t if r["event"] in d1], "D2": [r for r in t if r["event"] in d2], "TEST": [r for r in t if r["event"] in te]}
            st = {k: M.cell(v, rng) for k, v in parts.items()}
            st["ALL"] = M.cell(t, rng)
            res[lab] = st
        tr = res["treated"]
        res["verdict"] = M.judge(name, tr, tr["D1"], tr["D2"], tr["TEST"], tr["ALL"])
        out[name] = res
    path.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "score":
        o = score()
        for n, r in o.items():
            a = r["treated"]["ALL"]
            print(n, r["verdict"], a["n"], round(a["net"] * 100, 2), round(a["lo"] * 100, 2), round(a["hi"] * 100, 2))
    else:
        print(__doc__)
