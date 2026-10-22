"""SIDE1, HOUR1 and XLEAD1 (README, Pre-registration: SIDE1, HOUR1 and XLEAD1): three two-sided group comparisons on L1 entries at 360 seconds.
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.cuts3 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timezone

from . import lstrats as L
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
Z_BAR, MIN_GROUP, MIN_DAYS = 2.4, 500, 10
FOLLOWERS = {"KXETH15M", "KXXRP15M", "KXDOGE15M", "KXHYPE15M", "KXNEAR15M", "KXBNB15M", "KXZEC15M"}
RESULT = DATA_DIR / "cuts3_result.txt"


def compare(a: list[dict], b: list[dict], label: str):
    """(text, verdict) for group a minus group b: own means, day-clustered difference, both halves same sign."""
    if len(a) < MIN_GROUP or len(b) < MIN_GROUP or len({e["day"] for e in a + b}) < MIN_DAYS:
        return f"{label}: NOT_ENOUGH_DATA (a {len(a)}, b {len(b)})", "NOT_ENOUGH_DATA"
    d = defaultdict(lambda: [[], []])
    for e in a:
        d[e["day"]][0].append(e["net"])
    for e in b:
        d[e["day"]][1].append(e["net"])
    rows = [(k, st.mean(v[0]) - st.mean(v[1])) for k, v in d.items() if v[0] and v[1]]
    dm, _, dz = cluster_mean_z(rows)
    cut = sorted({e["close_ts"] for e in a + b})[len({e["close_ts"] for e in a + b}) // 2]
    halves = []
    for sel in (lambda e: e["close_ts"] < cut, lambda e: e["close_ts"] >= cut):
        xa, xb = [e["net"] for e in a if sel(e)], [e["net"] for e in b if sel(e)]
        halves.append(st.mean(xa) - st.mean(xb) if xa and xb else 0.0)
    same = halves[0] * halves[1] > 0 and halves[0] * dm > 0
    v = "NOT_YET_FALSIFIED" if (abs(dz) >= Z_BAR and same) else "FALSIFIED"
    c = lambda x: f"{x * 100:+.2f}c"
    return (f"{label}: a n={len(a)} at {c(st.mean(e['net'] for e in a))}, b n={len(b)} at {c(st.mean(e['net'] for e in b))}; a minus b per day {c(dm)} "
            f"(day clustered z {dz:+.2f}); halves {c(halves[0])} / {c(halves[1])}; VERDICT: {v}"), v


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    es = L.hold_rule(full, L.L1["left_s"], L.L1["band"])
    lines = []
    lines.append(compare([e for e in es if e["side"] == "yes"], [e for e in es if e["side"] == "no"], "SIDE1 (a = YES favourite, b = NO favourite)")[0])
    es10 = L.hold_rule(full, 600, L.L1["band"])
    lines.append("   information, 600 seconds: " + compare([e for e in es10 if e["side"] == "yes"], [e for e in es10 if e["side"] == "no"], "SIDE1@600")[0])
    minute = lambda e: datetime.fromtimestamp(e["close_ts"], timezone.utc).minute
    lines.append(compare([e for e in es if minute(e) == 0], [e for e in es if minute(e) != 0], "HOUR1 (a = closes on the hour, b = :15 :30 :45)")[0])
    btc = {e["close_ts"]: e for e in es if e["series"] == "KXBTC15M"}
    a, b = [], []
    for e in es:
        if e["series"] not in FOLLOWERS:
            continue
        prev = btc.get(e["close_ts"] - 900)
        if prev is None:
            continue
        (a if prev["gross"] < 0 else b).append(e)
    lines.append(compare(a, b, "XLEAD1 (a = after a Bitcoin L1 loss in the previous window, b = after a Bitcoin L1 win)")[0])
    out = "\n".join(lines)
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
