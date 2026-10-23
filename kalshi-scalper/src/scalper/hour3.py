"""HOUR3 (README, Pre-registration: HOUR3): does the window closing at :00 UTC beat the other windows of the hour on the other crypto series? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.hour3 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone

from . import feat1 as F
from .crowd1 import diff_z
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the outcomes were split ----
SERIES = ("KXETH15M", "KXXRP15M", "KXDOGE15M", "KXBNB15M", "KXHYPE15M", "KXNEAR15M", "KXZEC15M")
DIFF_C, Z_BAR, FALSIFY_C, FALSIFY_Z, MIN_SERIES_POS = 0.010, 2.0, 0.003, 1.0, 5
RESULT = DATA_DIR / "hour3_result.txt"
FWD_RESULT = DATA_DIR / "hour3f_result.txt"
FWD_SERIES = SERIES + ("KXBTC15M",)
FWD_START = int(datetime(2026, 10, 24, tzinfo=timezone.utc).timestamp())
FWD_READ_DATE = int(datetime(2026, 11, 12, tzinfo=timezone.utc).timestamp())
FWD_MIN_N = 600


def on_hour(r: dict) -> bool:
    return datetime.fromtimestamp(r["close_ts"], timezone.utc).minute == 0


def split(rows: list[dict]):
    return [r for r in rows if on_hour(r)], [r for r in rows if not on_hour(r)]


def forward(now: float | None = None) -> str:
    """HOUR3-F: the same claim, scored once on markets closing from 2026-10-24 (never seen by HOUR3), Bitcoin added. Read on or after 2026-11-12."""
    import time
    if (now if now is not None else time.time()) < FWD_READ_DATE:
        return "Refusing the registered read: before 2026-11-12."
    if FWD_RESULT.exists():
        return f"Refusing to run again: {FWD_RESULT} exists."
    mk = [m for m in load_fresh(series=FWD_SERIES, start_ts=FWD_START) if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, _, _ = F.build(full, 360)
    g, rest = split(rows)
    if len(g) < FWD_MIN_N:
        out = f"HOUR3-F: NOT_ENOUGH_DATA (HOUR n={len(g)}, need {FWD_MIN_N}; REST n={len(rest)})"
    else:
        m, z, nd = diff_z(g, rest)
        ms = diff_z(g, rest, "stress")[0]
        o = sorted({r["day"] for r in rows})
        mid = o[len(o) // 2]
        h1 = diff_z([r for r in g if r["day"] < mid], [r for r in rest if r["day"] < mid])[0]
        h2 = diff_z([r for r in g if r["day"] >= mid], [r for r in rest if r["day"] >= mid])[0]
        ok = m >= DIFF_C and z >= Z_BAR and h1 > 0 and h2 > 0 and ms > 0
        v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
        out = f"HOUR3-F: {v}; HOUR n={len(g)} REST n={len(rest)} on {nd} days; diff {100 * m:+.2f}c z {z:+.2f}; halves {100 * h1:+.2f}c / {100 * h2:+.2f}c; stress diff {100 * ms:+.2f}c"
    FWD_RESULT.write_text(out + "\n")
    return out


def main(argv: list[str]) -> None:
    if len(argv) >= 2 and argv[1] == "forward":
        print(forward())
        return
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = {}
    for m in load() + load_fresh():
        if m[1] in SERIES and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = m
    full = [(t, s, [(e, b, a, b, a) for e, b, a, *_ in c], cl, r) for t, s, c, cl, r in mk.values()]
    rows, _, _ = F.build(full, 360)
    g, rest = split(rows)
    m, z, nd = diff_z(g, rest)
    ms, _, _ = diff_z(g, rest, "stress")
    ds = sorted({r["day"] for r in rows})
    mid = ds[len(ds) // 2]
    h1 = diff_z([r for r in g if r["day"] < mid], [r for r in rest if r["day"] < mid])[0]
    h2 = diff_z([r for r in g if r["day"] >= mid], [r for r in rest if r["day"] >= mid])[0]
    pos, per = 0, []
    for s in SERIES:
        a = [r["net"] for r in g if r["series"] == s]
        b = [r["net"] for r in rest if r["series"] == s]
        d = st.mean(a) - st.mean(b) if a and b else 0.0
        pos += d > 0
        per.append(f"{s[2:-3]} ({len(a)}, {100 * d:+.2f})")
    gm = st.mean(r["net"] for r in g)
    ok = m >= DIFF_C and z >= Z_BAR and h1 > 0 and h2 > 0 and ms > 0 and gm > 0 and pos >= MIN_SERIES_POS
    verdict = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    out = [f"HOUR3: verdict {verdict}", f"entries {len(rows)}; HOUR n={len(g)} on {len({r['day'] for r in g})} days, REST n={len(rest)}",
           f"HOUR mean {100 * gm:+.2f}c, REST mean {100 * st.mean(r['net'] for r in rest):+.2f}c, diff {100 * m:+.2f}c, z {z:+.2f} ({nd} days)",
           f"halves {100 * h1:+.2f}c / {100 * h2:+.2f}c, stress diff {100 * ms:+.2f}c, series positive {pos} of {len(SERIES)}",
           "by series (n, diff c): " + ", ".join(per)]
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
