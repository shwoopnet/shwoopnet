"""ENTRY2 (README, Pre-registration: ENTRY2): three entry ideas read off the price-band by time map, scored ONCE on markets that closed after the map was drawn. Research only.
TIER (paying series: a 0.93 to 0.97 favourite at 420 s, else a 0.88 to 0.93 favourite at 360 s) against plain L1 on the same markets; LATE97A (paying series, favourite at 0.97 to 0.995
at 240 s); LATE97B (the other series, favourite at 0.97 to 0.995 at 360 s). Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.entry2 forward     (refused before 2026-11-12 and a second time; run `python -m scalper.fresh_update` first)
"""
from __future__ import annotations

import statistics as st
import sys
import time
from datetime import datetime, timezone

from . import lstrats as L
from .calibration import cluster_mean_z
from .crowd1 import diff_z
from .fwd_reads import load_fresh
from .paths import DATA_DIR

# ---- fixed in the README before any market after the start date was scored ----
PAY = ("KXXRP15M", "KXDOGE15M", "KXGOLD15M")
START = int(datetime(2026, 10, 24, tzinfo=timezone.utc).timestamp())
READ_DATE = int(datetime(2026, 11, 12, tzinfo=timezone.utc).timestamp())
TIER_C, TIER_Z, LATE_C, LATE_Z, FALSIFY_C, FALSIFY_Z = 0.005, 2.0, 0.004, 2.0, 0.001, 1.0
MIN_TIER, MIN_LATE_A, MIN_LATE_B = 300, 500, 800
EARLY_SERIES, EARLY_LEFT, EARLY_BAND, MIN_EARLY, EARLY_C, EARLY_Z = ("KXBTC15M", "KXETH15M"), 540, (0.80, 0.93), 400, 0.010, 2.0
RESULT = DATA_DIR / "entry2_result.txt"


def at(candles: list[tuple], t: int):
    return next((x for x in candles if x[0] == t), None)


def row(market: tuple, side: str, price: float) -> dict:
    t, s, c, cl, res = market
    yes = res == "yes"
    return {"day": datetime.fromtimestamp(cl, timezone.utc).strftime("%Y-%m-%d"), "close_ts": cl,
            "net": L.net(side, price, yes), "stress": L.net(side, price, yes, L.STRESS)}


def pick(market: tuple, left: int, band: tuple[float, float]):
    x = at(market[2], market[3] - left)
    return None if x is None else L.favorite(x[1], x[2], band)


def tier_entry(market: tuple):
    """The TIER entry for a paying-series market: 420 s at 0.93 to 0.97, else 360 s at 0.88 to 0.93; None if neither."""
    p = pick(market, 420, (0.93, 0.97))
    if p:
        return row(market, *p)
    p = pick(market, 360, (0.88, 0.9299))
    return row(market, *p) if p else None


def baseline_entry(market: tuple):
    p = pick(market, 360, L.L1["band"])
    return row(market, *p) if p else None


def judge_mean(rows: list[dict], min_n: int, c_bar: float = LATE_C, z_bar: float = LATE_Z) -> dict:
    if len(rows) < min_n:
        return {"verdict": "NOT_ENOUGH_DATA", "n": len(rows)}
    m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    ds = sorted({r["day"] for r in rows})
    mid = ds[len(ds) // 2]
    h = [st.mean(r["net"] for r in rows if (r["day"] < mid) == first) for first in (True, False)]
    ms = st.mean(r["stress"] for r in rows)
    ok = m >= c_bar and z >= z_bar and h[0] > 0 and h[1] > 0 and ms > 0
    v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    return {"verdict": v, "n": len(rows), "mean": m, "z": z, "h1": h[0], "h2": h[1], "stress": ms}


def forward(now: float | None = None) -> str:
    if (now if now is not None else time.time()) < READ_DATE:
        return "Refusing the registered read: before 2026-11-12."
    if RESULT.exists():
        return f"Refusing to run again: {RESULT} exists."
    mk = [m for m in load_fresh(start_ts=START) if all(x[1] is not None and x[2] is not None for x in m[2]) and m[4] in ("yes", "no")]
    pay = [m for m in mk if m[1] in PAY]
    other = [m for m in mk if m[1] not in PAY]
    out = []
    tier = [r for m in pay if (r := tier_entry(m))]
    base = [r for m in pay if (r := baseline_entry(m))]
    if len(tier) < MIN_TIER:
        out.append(f"TIER: NOT_ENOUGH_DATA (n={len(tier)}, need {MIN_TIER})")
    else:
        m, z, nd = diff_z(tier, base)
        ms, _, _ = diff_z(tier, base, "stress")
        ds = sorted({r["day"] for r in tier})
        mid = ds[len(ds) // 2]
        h1 = diff_z([r for r in tier if r["day"] < mid], [r for r in base if r["day"] < mid])[0]
        h2 = diff_z([r for r in tier if r["day"] >= mid], [r for r in base if r["day"] >= mid])[0]
        ok = m >= TIER_C and z >= TIER_Z and h1 > 0 and h2 > 0 and ms > 0
        v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
        out.append(f"TIER: {v}; n={len(tier)} vs L1 n={len(base)}; diff per day {100 * m:+.2f}c z {z:+.2f} ({nd} days); halves {100 * h1:+.2f}c / {100 * h2:+.2f}c; stress {100 * ms:+.2f}c")
    for name, ms_, left, band, min_n in (("LATE97A", pay, 240, (0.97, 0.995), MIN_LATE_A), ("LATE97B", other, 360, (0.97, 0.995), MIN_LATE_B)):
        rows = [row(m, *p) for m in ms_ if (p := pick(m, left, band))]
        j = judge_mean(rows, min_n)
        out.append(f"{name}: {j['verdict']}; n={j['n']}" + (f"; mean {100 * j['mean']:+.2f}c z {j['z']:+.2f}; halves {100 * j['h1']:+.2f}c / {100 * j['h2']:+.2f}c; stress {100 * j['stress']:+.2f}c" if "mean" in j else ""))
    early = [row(m, *p) for m in mk if m[1] in EARLY_SERIES and (p := pick(m, EARLY_LEFT, EARLY_BAND))]
    j = judge_mean(early, MIN_EARLY, EARLY_C, EARLY_Z)
    out.append(f"EARLY540: {j['verdict']}; n={j['n']}" + (f"; mean {100 * j['mean']:+.2f}c z {j['z']:+.2f}; halves {100 * j['h1']:+.2f}c / {100 * j['h2']:+.2f}c; stress {100 * j['stress']:+.2f}c" if "mean" in j else ""))
    text = "\n".join(out)
    RESULT.write_text(text + "\n")
    return text


if __name__ == "__main__":
    print(forward() if sys.argv[1:] == ["forward"] else __doc__)
