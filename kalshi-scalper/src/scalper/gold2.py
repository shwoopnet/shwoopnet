"""GOLD2 (README, Pre-registration: GOLD2): do the pooled-failed filters work inside gold alone? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.gold2 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys

from . import feat1 as F
from .crowd1 import diff_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the gold outcomes were split by these rules ----
GROUPS = {
    "FLAT": lambda r: r["x"][6] <= 0.15 and abs(r["x"][2]) <= 0.05,
    "TIGHT": lambda r: r["x"][1] <= 0.005,
    "LONGBAND": lambda r: r["x"][4] >= 2,
}
DIFF_C, DIFF_Z_BAR, FALSIFY_C, FALSIFY_Z, MIN_N = 0.010, 2.4, 0.003, 1.0, 150
RESULT = DATA_DIR / "gold2_result.txt"


def split(rows: list[dict], f):
    a = [r for r in rows if f(r)]
    ids = {id(r) for r in a}
    return a, [r for r in rows if id(r) not in ids]


def judge(rows: list[dict], f) -> dict:
    a, b = split(rows, f)
    if len(a) < MIN_N or not b:
        return {"verdict": "NOT_ENOUGH_DATA", "n": len(a)}
    m, z, _ = diff_z(a, b)
    ms, _, _ = diff_z(a, b, "stress")
    ds = sorted({r["day"] for r in rows})
    mid = ds[len(ds) // 2]
    h1 = diff_z([r for r in a if r["day"] < mid], [r for r in b if r["day"] < mid])[0]
    h2 = diff_z([r for r in a if r["day"] >= mid], [r for r in b if r["day"] >= mid])[0]
    ok = m >= DIFF_C and z >= DIFF_Z_BAR and h1 > 0 and h2 > 0 and ms > 0
    v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    return {"verdict": v, "n": len(a), "diff": m, "z": z, "h1": h1, "h2": h2, "stress": ms,
            "mean": st.mean(r["net"] for r in a), "rest": st.mean(r["net"] for r in b)}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if m[1] == "KXGOLD15M" and all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, _, _ = F.build(full, 360)
    out = [f"GOLD2: gold entries {len(rows)} on {len({r['day'] for r in rows})} days"]
    for k, f in GROUPS.items():
        j = judge(rows, f)
        if "diff" in j:
            out.append(f"{k}: {j['verdict']} n={j['n']} group {100 * j['mean']:+.2f}c rest {100 * j['rest']:+.2f}c diff {100 * j['diff']:+.2f}c z {j['z']:+.2f} halves {100 * j['h1']:+.2f}/{100 * j['h2']:+.2f} stress {100 * j['stress']:+.2f}")
        else:
            out.append(f"{k}: {j['verdict']} n={j['n']}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
