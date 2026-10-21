"""V3 and V4 (README, Pre-registration: V3 and V4): the VM volatility-managed rule on TLT and GLD. Research only: nothing here places an order.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.vm34 run   (reads data/slow1_bars.json from `python -m scalper.slow1 fetch`; once, a second run is refused unless the result file is deleted on purpose)
"""
from __future__ import annotations

import json
import random
import sys

from . import vm
from .paths import DATA_DIR
from .slow1 import alpha_only

BARS_FILE = DATA_DIR / "slow1_bars.json"
RESULT_FILE = DATA_DIR / "vm34_result.txt"
CELLS = {"V3": "TLT", "V4": "GLD"}
vm.Z_BAR = 2.8                                   # the registered bar for this family of 18 (VM's own was 2.7)


def run() -> None:
    if RESULT_FILE.exists():
        sys.exit(f"{RESULT_FILE} exists: V3/V4 is a single read. Delete it on purpose (a crash fix only) to rerun.")
    bars = json.loads(BARS_FILE.read_text())
    out = []
    for name, sym in CELLS.items():
        dates = sorted(bars[sym])
        rows = vm.managed_rows(dates, [bars[sym][d] for d in dates])
        w = [r["w"] for r in rows]
        s, b = vm.managed_series(rows, w)
        s2, _ = vm.managed_series(rows, w, vm.STRESS)
        rng = random.Random(1)
        pl = []
        for _ in range(vm.PLACEBO_REPS):
            ww = w[:]
            rng.shuffle(ww)
            ps, _ = vm.managed_series(rows, ww)
            pl.append(alpha_only(ps, b))
        out.append(vm.judge(name, [r["date"] for r in rows], s, b, s2, pl, {"asset": sym, "mean_weight": sum(w) / len(w)}))
    text = json.dumps(out, indent=1, default=str)
    RESULT_FILE.write_text(text)
    print(text)


if __name__ == "__main__":
    {"run": run}[sys.argv[1]]()
