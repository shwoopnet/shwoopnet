"""EL1 (README, Pre-registration: EL1): L1 entered at 10 minutes left instead of 6, on TREE2's pool of 15 minute series. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.el1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from collections import defaultdict

from . import lstrats as L
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR
from .scalps import STRESS

# ---- fixed in the README before the first run ----
LEFT_S, BASE_LEFT_S = 600, 360
MIN_N, MIN_DAYS, Z_BAR, DIFF_Z_BAR, MIN_SERIES_POSITIVE = 1000, 10, 2.8, 2.0, 10
RESULT = DATA_DIR / "el1_result.txt"


def entries_for(markets: list[tuple], left_s: int) -> dict[str, dict]:
    full = [(tk, s, [(e, b, a, b, a) for (e, b, a) in c], close, res) for tk, s, c, close, res in markets]
    return {e["ticker"]: e for e in L.hold_rule(full, left_s, L.L1["band"])}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    early, base = entries_for(mk, LEFT_S), entries_for(mk, BASE_LEFT_S)
    rows = sorted(early.values(), key=lambda e: e["close_ts"])
    n, days = len(rows), len({e["day"] for e in rows})
    both = [(early[t], base[t]) for t in early if t in base]
    m, _, z = cluster_mean_z([(e["day"], e["net"]) for e in rows])
    h = n // 2
    h1, h2 = st.mean(e["net"] for e in rows[:h]), st.mean(e["net"] for e in rows[h:])
    stress = st.mean(e["stress"] for e in rows)
    md, _, zd = cluster_mean_z([(a["day"], a["net"] - b["net"]) for a, b in both])
    by = defaultdict(list)
    for e in rows:
        by[e["series"]].append(e["net"])
    pos = sum(1 for v in by.values() if st.mean(v) > 0)
    ok = n >= MIN_N and days >= MIN_DAYS and m > 0 and z >= Z_BAR and h1 > 0 and h2 > 0 and stress > 0 and pos >= MIN_SERIES_POSITIVE and md > 0 and zd >= DIFF_Z_BAR
    v = "NOT_ENOUGH_DATA" if (n < MIN_N or days < MIN_DAYS) else ("NOT_YET_FALSIFIED" if ok else "FALSIFIED")
    c = lambda x: f"{x * 100:+.2f}c"
    lines = [f"EL1 on {len(mk)} markets; 10 minute entries {n} on {days} days; 6 minute entries {len(base)}",
             f"   10 minute net {c(m)} z {z:+.2f} halves {c(h1)} / {c(h2)} fees x{STRESS} {c(stress)}; series positive {pos} of {len(by)}",
             f"   6 minute net over the same markets {c(st.mean(b['net'] for b in base.values()))}; on the {len(both)} markets entered at BOTH times: 10 minute minus 6 minute {c(md)} (day clustered z {zd:+.2f})",
             f"   VERDICT: {v}", "Per series (information): n, 10 minute net, loss rate"]
    for sr in sorted(by):
        v_ = by[sr]
        lines.append(f"   {sr}: n {len(v_)} at {c(st.mean(v_))}; 6 minute n {sum(1 for b in base.values() if b['series'] == sr)} at {c(st.mean([b['net'] for b in base.values() if b['series'] == sr] or [0]))}")
    out = "\n".join(lines)
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
