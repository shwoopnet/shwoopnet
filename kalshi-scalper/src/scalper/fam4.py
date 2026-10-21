"""RP1, CS1 and FA1 (README, Pre-registration: RP1, CS1, FA1 and ML1): an inverse-volatility ETF portfolio against 60/40, volatility-managed Bitcoin spot, and four
factor ETFs against SPY. Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.fam4 run   (reads data/fam4_bars.json; once, a second run is refused unless the result file is deleted on purpose)
"""
from __future__ import annotations

import json
import math
import random
import sys

from . import vm
from .paths import DATA_DIR
from .slow1 import alpha_only, month_ends

BARS_FILE = DATA_DIR / "fam4_bars.json"
RESULT_FILE = DATA_DIR / "fam4_result.txt"
RP_ASSETS, RP_VOL_DAYS, RP_COST = ["SPY", "TLT", "GLD", "DBC"], 63, 0.0005
CS_TARGET, CS_DAYS, CS_COST = 0.40, 21, 0.0035
FA_ASSETS, FA_COST = ["MTUM", "QUAL", "VLUE", "SIZE"], 0.0005
vm.Z_BAR = 2.9                                  # the registered bar for the family of 21 (VM's own was 2.7)
PLACEBO_REPS = 200


def vol(px: list[float], i: int, n: int, per_year: int) -> float:
    r = [px[k] / px[k - 1] - 1 for k in range(i - n + 1, i + 1)]
    m = sum(r) / n
    return math.sqrt(sum((v - m) ** 2 for v in r) / (n - 1)) * math.sqrt(per_year)


def common(bars: dict, syms: list[str]) -> list[str]:
    return sorted(set.intersection(*(set(bars[s]) for s in syms)))


# ---------------------------------------------------------------- RP1
def rp_rows(bars: dict) -> list[dict]:
    dates = common(bars, RP_ASSETS)
    px = {a: [bars[a][d] for d in dates] for a in RP_ASSETS}
    me = month_ends(dates)
    rows = []
    for k in range(len(me) - 1):
        i, j = me[k], me[k + 1]
        if i < RP_VOL_DAYS or j + 1 >= len(dates):
            continue
        inv = {a: 1.0 / vol(px[a], i, RP_VOL_DAYS, 252) for a in RP_ASSETS}
        tot = sum(inv.values())
        rows.append({"date": dates[i], "w": [inv[a] / tot for a in RP_ASSETS], "ret": [px[a][j + 1] / px[a][i + 1] - 1 for a in RP_ASSETS]})
    return rows


def rp_series(rows: list[dict], weights: list[list[float]], mult: float = 1.0) -> tuple[list[float], list[float]]:
    prev = [0.0] * len(RP_ASSETS)
    s, b = [], []
    for r, w in zip(rows, weights):
        turn = sum(abs(x - y) for x, y in zip(w, prev))
        s.append(sum(x * y for x, y in zip(w, r["ret"])) - turn * RP_COST * mult)
        b.append(0.6 * r["ret"][0] + 0.4 * r["ret"][1])
        prev = w
    return s, b


# ---------------------------------------------------------------- CS1
def cs_rows(dates: list[str], px: list[float]) -> list[dict]:
    me = month_ends(dates)
    rows = []
    for k in range(len(me) - 1):
        i, j = me[k], me[k + 1]
        if i < CS_DAYS or j + 1 >= len(dates):
            continue
        v = vol(px, i, CS_DAYS, 365)
        rows.append({"date": dates[i], "w": min(1.0, CS_TARGET / v) if v > 0 else 1.0, "ret": px[j + 1] / px[i + 1] - 1})
    return rows


def cs_series(rows: list[dict], weights: list[float], mult: float = 1.0) -> tuple[list[float], list[float]]:
    prev, s, b = 0.0, [], []
    for r, w in zip(rows, weights):
        s.append(w * r["ret"] - abs(w - prev) * CS_COST * mult)
        b.append(r["ret"])
        prev = w
    return s, b


# ---------------------------------------------------------------- FA1
def fa_series(bars: dict) -> tuple[list[str], list[float], list[float], list[float]]:
    dates = common(bars, FA_ASSETS + ["SPY"])
    me = month_ends(dates)
    d, s, b = [], [], []
    for k in range(len(me) - 1):
        i, j = me[k], me[k + 1]
        if j + 1 >= len(dates):
            continue
        d.append(dates[i])
        s.append(sum(bars[a][dates[j + 1]] / bars[a][dates[i + 1]] - 1 for a in FA_ASSETS) / len(FA_ASSETS))
        b.append(bars["SPY"][dates[j + 1]] / bars["SPY"][dates[i + 1]] - 1)
    one_off = 2 * FA_COST / len(s)
    return d, [x - one_off for x in s], [x - one_off * vm.STRESS for x in s], b


def run() -> None:
    if RESULT_FILE.exists():
        sys.exit(f"{RESULT_FILE} exists: this is a single read. Delete it on purpose (a crash fix only) to rerun.")
    bars = json.loads(BARS_FILE.read_text())
    out = []
    rng = random.Random(1)
    # RP1
    rows = rp_rows(bars)
    w = [r["w"] for r in rows]
    s, b = rp_series(rows, w)
    s2, _ = rp_series(rows, w, vm.STRESS)
    pl = []
    for _ in range(PLACEBO_REPS):
        ww = w[:]
        rng.shuffle(ww)
        pl.append(alpha_only(rp_series(rows, ww)[0], b))
    out.append(vm.judge("RP1", [r["date"] for r in rows], s, b, s2, pl, {"mean_weights": [round(sum(x[k] for x in w) / len(w), 3) for k in range(4)]}))
    # CS1 (BTC is the try; ETH is information, under the 120 month minimum by construction)
    for name, sym in (("CS1", "BTC-USD"), ("CS1_ETH_info", "ETH-USD")):
        dates = sorted(bars[sym])
        rows = cs_rows(dates, [bars[sym][d] for d in dates])
        w = [r["w"] for r in rows]
        s, b = cs_series(rows, w)
        s2, _ = cs_series(rows, w, vm.STRESS)
        pl = []
        for _ in range(PLACEBO_REPS):
            ww = w[:]
            rng.shuffle(ww)
            pl.append(alpha_only(cs_series(rows, ww)[0], b))
        out.append(vm.judge(name, [r["date"] for r in rows], s, b, s2, pl, {"mean_weight": sum(w) / len(w)}))
    # FA1
    d, s, s2, b = fa_series(bars)
    out.append(vm.judge("FA1", d, s, b, s2, None, {}))
    text = json.dumps(out, indent=1, default=str)
    RESULT_FILE.write_text(text)
    print(text)


if __name__ == "__main__":
    {"run": run}[sys.argv[1]]()
