"""FIX1 and the JUMP1 history look (README, Pre-registration: JUMP1, FIX1, VRP2 and the two data requests). Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
FIX1 is a registered test; the JUMP1 history split is information only (JUMP1 itself is a forward read).
Usage: python -m scalper.cuts4 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone

from . import lstrats as L
from .calibration import cluster_mean_z
from .cuts3 import compare
from .gold1 import load as load_gold
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
FIX_MINUTES, FIX_HALF_WINDOW_MIN, MIN_GROUP_FIX, JUMP_CUT = (9 * 60 + 30, 14 * 60), 30, 100, 0.05
RESULT = DATA_DIR / "cuts4_result.txt"


def near_fix(ts: int) -> bool:
    d = datetime.fromtimestamp(ts, timezone.utc)
    if d.weekday() >= 5:
        return False
    m = d.hour * 60 + d.minute
    return any(abs(m - f) <= FIX_HALF_WINDOW_MIN for f in FIX_MINUTES)


def weekday(ts: int) -> bool:
    return datetime.fromtimestamp(ts, timezone.utc).weekday() < 5


def d3_of(candles: list[tuple], t: int, side: str):
    idx = {c[0]: c for c in candles}
    now, then = idx.get(t), idx.get(t - 180)
    if now is None or then is None:
        return None
    mid = lambda c: (c[1] + c[2]) / 2 if side == "yes" else 1 - (c[1] + c[2]) / 2
    return mid(now) - mid(then)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    lines = []
    # ---- FIX1: gold, book + l1b
    gold = []
    for name in ("l1b", "book"):
        gold += [m for m in load_gold(DATA_DIR / f"{name}.sqlite") if m[1] == "KXGOLD15M"]
    es = L.hold_rule(gold, L.L1["left_s"], L.L1["band"])
    wk = [e for e in es if weekday(e["close_ts"] - L.L1["left_s"])]
    a = [e for e in wk if near_fix(e["close_ts"] - L.L1["left_s"])]
    b = [e for e in wk if not near_fix(e["close_ts"] - L.L1["left_s"])]
    if len(a) < MIN_GROUP_FIX or len(b) < MIN_GROUP_FIX:
        lines.append(f"FIX1: NOT_ENOUGH_DATA (near the fixes {len(a)}, other {len(b)})")
    else:
        import scalper.cuts3 as C3
        C3.MIN_GROUP, C3.MIN_DAYS = MIN_GROUP_FIX, 5                        # FIX1's registered group minimum is 100
        lines.append(compare(a, b, "FIX1 (a = within 30 minutes of the 09:30 or 14:00 UTC fixes, b = other weekday gold entries)")[0])
    # ---- JUMP1 history look (information only)
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b_, a_, b_, a_) for e, b_, a_ in c], cl, r) for t, s, c, cl, r in mk]
    idx = {m[0]: m for m in full}
    rows = L.hold_rule(full, L.L1["left_s"], L.L1["band"])
    jumped, stable = [], []
    for e in rows:
        d3 = d3_of([(c[0], c[1], c[2]) for c in idx[e["ticker"]][2]], e["close_ts"] - L.L1["left_s"], e["side"])
        if d3 is None:
            continue
        (jumped if d3 >= JUMP_CUT else stable).append(e)
    sm, _, sz = cluster_mean_z([(e["day"], e["net"]) for e in stable])
    jm, _, jz = cluster_mean_z([(e["day"], e["net"]) for e in jumped])
    import scalper.cuts3 as C3
    C3.MIN_GROUP, C3.MIN_DAYS = 500, 10
    txt = compare(stable, jumped, "JUMP1 history (information; a = stable, b = jumped)")[0]
    lines.append(f"{txt}; jumped share {100 * len(jumped) / (len(jumped) + len(stable)):.1f}% (stable z {sz:+.2f}, jumped z {jz:+.2f})")
    out = "\n".join(lines)
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
