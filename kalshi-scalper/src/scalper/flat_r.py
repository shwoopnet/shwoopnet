"""FLAT-R (README, Pre-registration: FLAT-R): FLAT2's rule at 360 s left on 15 minute series no earlier study used (data/rep.sqlite). Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.flat_r run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import sqlite3
import statistics as st
import sys
from collections import defaultdict

from . import feat1 as F
from . import flat1, flat2
from .paths import DATA_DIR

# ---- fixed in the README before the download and the run ----
SERIES = ("KXADA15M", "KXAUDUSD15M", "KXBCH15M", "KXBRENT15M", "KXDJIA15M", "KXINX15M", "KXNDQ15M", "KXSOL15M", "KXTON15M", "KXUSDCAD15M", "KXUSDMXN15M",
          "KX2YRRATE15M", "KX5YRRATE15M", "KX10YRRATE15M", "KX30YRRATE15M")
MIN_N, MONTH_MIN = 300, 100
DB, RESULT = DATA_DIR / "rep.sqlite", DATA_DIR / "flat_r_result.txt"


def load_rep(path=DB, series=SERIES) -> list[tuple]:
    """(ticker, series, [(end, bid, ask, bid, ask)], close_ts, result) for the replication series; markets with a missing quote are dropped, as in every study."""
    db = sqlite3.connect(path)
    by: dict = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
    for s, tk, end, bc, ac, close_ts, res in db.execute(
            "SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, m.close_ts, m.result FROM candle c JOIN market m ON m.ticker = c.ticker ORDER BY c.ticker, c.end_ts"):
        if s not in series:
            continue
        m = by[tk]
        m["c"].append((end, bc, ac, bc, ac)); m["close"] = close_ts; m["res"] = res; m["s"] = s
    return [(tk, m["s"], m["c"], m["close"], m["res"]) for tk, m in by.items() if all(x[1] is not None and x[2] is not None for x in m["c"])]


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    markets = load_rep()
    rows, _, _ = F.build(markets, 360)
    flat, moving = flat2.split(rows)
    out = [f"FLAT-R: {len(markets)} markets, {len(rows)} entries"] + [f"{k}: {v}" for k, v in flat1.judge(flat, moving, min_n=MIN_N, month_min=MONTH_MIN).items()]
    out.append("info: by series  (flat n, flat c, rest c, diff c, z)")
    by = defaultdict(list)
    for r in rows:
        by[r["series"]].append(r)
    for s, rs in sorted(by.items()):
        fl, mv = flat2.split(rs)
        if len(fl) >= 20 and len(mv) >= 20:
            m, z, _ = flat1.diff_z(fl, mv)
            out.append(f"{s}: {len(fl)}, {100 * st.mean(r['net'] for r in fl):+.2f}, {100 * st.mean(r['net'] for r in mv):+.2f}, {100 * m:+.2f}, {z:+.2f}")
        else:
            out.append(f"{s}: flat {len(fl)}, rest {len(mv)} (too few)")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
