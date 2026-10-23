"""HOUR2 (README, Pre-registration: HOUR2): do non-gold metals and energy favourites do better in the 04 to 07Z close block? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.hour2 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timezone

from . import feat1 as F
from .crowd1 import diff_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the non-gold hour numbers were computed ----
SERIES = ("KXSILVER15M", "KXPLATINUM15M", "KXPALLADIUM15M", "KXCOPPER15M", "KXWTI15M", "KXNATGAS15M")
BLOCK = (4, 8)                                   # close hour 04 to 07Z
DIFF_C, DIFF_Z_BAR, FALSIFY_C, FALSIFY_Z, MIN_N, MIN_SERIES, PLACEBO_REPS, SEED = 0.010, 2.0, 0.003, 1.0, 500, 4, 100, 83
RESULT = DATA_DIR / "hour2_result.txt"


def hour(r: dict) -> int:
    return datetime.fromtimestamp(r["close_ts"], timezone.utc).hour


def split(rows: list[dict], block=BLOCK):
    night = [r for r in rows if block[0] <= hour(r) < block[1]]
    ids = {id(r) for r in night}
    return night, [r for r in rows if id(r) not in ids]


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if m[1] in SERIES and all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, _, _ = F.build(full, 360)
    night, rest = split(rows)
    n, days = len(night), len({r["day"] for r in night})
    m, z, nd = diff_z(night, rest)
    ms, _, _ = diff_z(night, rest, "stress")
    ds = sorted({r["day"] for r in rows})
    mid = ds[len(ds) // 2]
    h1 = diff_z([r for r in night if r["day"] < mid], [r for r in rest if r["day"] < mid])[0]
    h2 = diff_z([r for r in night if r["day"] >= mid], [r for r in rest if r["day"] >= mid])[0]
    pos = {}
    for s in SERIES:
        a = [r for r in night if r["series"] == s]
        b = [r for r in rest if r["series"] == s]
        pos[s] = (len(a), 100 * (st.mean(r["net"] for r in a) - st.mean(r["net"] for r in b))) if a and b else (0, 0.0)
    rng = random.Random(SEED)
    pz = []
    for _ in range(PLACEBO_REPS):
        lo = rng.randrange(0, 21)
        pz.append(diff_z(*split(rows, (lo, lo + 4)))[1])
    p95 = sorted(pz)[int(0.95 * len(pz)) - 1]
    npos = sum(1 for k, v in pos.values() if k and v > 0)
    ok = n >= MIN_N and m >= DIFF_C and z >= DIFF_Z_BAR and h1 > 0 and h2 > 0 and ms > 0 and npos >= MIN_SERIES and z > p95
    verdict = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    out = [f"HOUR2: verdict {verdict}", f"entries {len(rows)}; NIGHT n={n} on {days} days, REST n={len(rest)}",
           f"NIGHT mean {100 * st.mean(r['net'] for r in night):+.2f}c, REST mean {100 * st.mean(r['net'] for r in rest):+.2f}c, diff {100 * m:+.2f}c, z {z:+.2f}",
           f"halves {100 * h1:+.2f}c / {100 * h2:+.2f}c, stress {100 * ms:+.2f}c, placebo 95th percentile z {p95:+.2f}, series positive {npos} of {len(SERIES)}",
           "by series (night n, night minus rest c): " + ", ".join(f"{s[2:-3]} ({k}, {v:+.2f})" for s, (k, v) in pos.items())]
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
