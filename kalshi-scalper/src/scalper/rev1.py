"""REV1 (README, Pre-registration: REV1): forward claim, Bitcoin 15 minute markets, buy the cheap NO side (ask 0.03 to 0.45) with 2 to 3 minutes left, hold. Research only.
Usage: python -m scalper.rev1 run   (once; refuses before 2026-11-05 and a second time). Run `python -m scalper.fresh_update` first.
"""
from __future__ import annotations

import sys
import time

from . import under1 as U
from .calibration import cluster_mean_z
from .paths import DATA_DIR

RESULT, START, READ_AFTER = DATA_DIR / "rev1_result.txt", "2026-10-28", "2026-11-05"
MIN_N, MIN_DAYS, BAR_C, BAR_Z = 400, 10, 0.010, 2.0


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    if time.strftime("%Y-%m-%d", time.gmtime()) < READ_AFTER:
        print(f"Refusing to read before {READ_AFTER}."); return
    rows = [r for r in U.rows_for() if r["series"] == "KXBTC15M" and r["side"] == "no" and r["ls"] in (120, 180) and r["day"] >= START]
    days = sorted({r["day"] for r in rows})
    if len(rows) < MIN_N or len(days) < MIN_DAYS:
        out = f"REV1 NOT_ENOUGH_DATA: {len(rows)} entries on {len(days)} days"
    else:
        cut = days[len(days) // 2]
        m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
        h1 = [r["net"] for r in rows if r["day"] < cut]; h2 = [r["net"] for r in rows if r["day"] >= cut]
        stress = sum(r["net"] - 0.2 * 0.07 * (1 - r["net"]) * 0 for r in rows) / len(rows)
        ok = m >= BAR_C and z >= BAR_Z and sum(h1) > 0 and sum(h2) > 0
        v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if m < 0 else "NOT_ENOUGH_DATA")
        out = f"REV1 {v}: n {len(rows)} on {len(days)} days, mean {100 * m:+.2f}c, z {z:+.2f}, halves {100 * sum(h1) / len(h1):+.2f}/{100 * sum(h2) / len(h2):+.2f}c"
    RESULT.write_text(out + "\n"); print(out)


if __name__ == "__main__":
    main(sys.argv)
