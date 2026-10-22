"""FLAT2 (README, Pre-registration: FLAT2): FLAT1 with the looser cut rng5 <= 0.15 and |rise3| <= 0.05. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.flat2 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import sys

from . import feat1 as F
from . import flat1
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
RNG5_MAX, RISE3_MAX = 0.15, 0.05
RESULT = DATA_DIR / "flat2_result.txt"


def split(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    flat = [r for r in rows if r["x"][flat1.I_RNG5] <= RNG5_MAX and abs(r["x"][flat1.I_RISE3]) <= RISE3_MAX]
    ids = {id(r) for r in flat}
    return flat, [r for r in rows if id(r) not in ids]


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, _, _ = F.build(full, 360)
    out = ["FLAT2 primary (all series)"] + [f"{k}: {v}" for k, v in flat1.judge(*split(rows)).items()]
    out.append("info: live five series only")
    out += [f"{k}: {v}" for k, v in flat1.judge(*split([r for r in rows if r["series"] in flat1.LIVE])).items()]
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)


FRESH_FROM, F_DIFF_C, F_Z, F_MIN_N = "2026-10-14", 0.010, 2.0, 300


def flat2f(markets: list[tuple]) -> str:
    """FLAT2-F (README): FLAT2 on fresh markets closing from FRESH_FROM, never used to choose the cut."""
    import statistics as st
    rows, _, _ = F.build(markets, 360)
    rows = [r for r in rows if r["day"] >= FRESH_FROM]
    flat, moving = split(rows)
    if len(flat) < F_MIN_N or not moving:
        return f"FLAT2-F: NOT_ENOUGH_DATA (FLAT n={len(flat)}, MOVING n={len(moving)})"
    m, z, nd = flat1.diff_z(flat, moving)
    ms, _, _ = flat1.diff_z(flat, moving, "stress")
    a, b = sorted(flat, key=lambda r: r["close_ts"]), sorted(moving, key=lambda r: r["close_ts"])
    ha, hb = len(a) // 2, len(b) // 2
    h1 = st.mean(r["net"] for r in a[:ha]) - st.mean(r["net"] for r in b[:hb])
    h2 = st.mean(r["net"] for r in a[ha:]) - st.mean(r["net"] for r in b[hb:])
    ok = m >= F_DIFF_C and z >= F_Z and ms > 0 and h1 > 0 and h2 > 0
    c = lambda x: f"{x * 100:+.2f}c"
    return (f"FLAT2-F: FLAT n={len(flat)} at {c(st.mean(r['net'] for r in flat))}, MOVING n={len(moving)} at {c(st.mean(r['net'] for r in moving))} on {nd} days; "
            f"difference {c(m)} (day clustered z {z:+.2f}); halves {c(h1)} / {c(h2)}; stress {c(ms)}; VERDICT: {'NOT_YET_FALSIFIED' if ok else 'FALSIFIED'}")
