"""VOL1 (README, Pre-registration: VOL1): skip Bitcoin and Ethereum L1 entries made in a busy minute. Rules fixed in the README before any day it covers existed.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Reads the SAME forward data as FWD1 (`data/fwd1.sqlite`, fetched by `python -m scalper.fwd1 fetch`), in the same single read, on or after 2026-11-16: python -m scalper.vol1 run
"""
from __future__ import annotations

import statistics as st
import sys
import time

from . import altseries as A
from . import fwd1
from . import lstrats as L
from . import pm2
from .paths import DATA_DIR

A.ALT_DB = DATA_DIR / "fwd1.sqlite"
SERIES = ("KXBTC15M", "KXETH15M")
THRESHOLDS = {"KXBTC15M": 132_766.0, "KXETH15M": 5_751.0}     # the 2/3 quantile of entry-minute volume over the 68 days, fixed in the README and not refitted
MIN_SKIPPED = 150
MIN_DAYS = 10


def is_skipped(series: str, volume: float | None) -> bool:
    """Strictly above the series' threshold; a missing volume is never a reason to skip."""
    return volume is not None and volume > THRESHOLDS[series]


def entries(raw: list[dict], vol: dict) -> list[dict]:
    """Forward Bitcoin and Ethereum L1 entries, each flagged `skip` by its entry candle's volume."""
    out = []
    for e in fwd1.forward(raw):
        if e["series"] not in SERIES:
            continue
        v = vol.get((e["ticker"], e["close_ts"] - L.L1["left_s"]))
        out.append({"series": e["series"], "close_ts": e["close_ts"], "day": e["day"], "net": e["net"], "skip": is_skipped(e["series"], v)})
    return out


def verdict(es: list[dict], null: list[float], min_skipped: int = MIN_SKIPPED) -> tuple[str, dict]:
    skipped = [e for e in es if e["skip"]]
    kept = [e for e in es if not e["skip"]]
    days = sorted({e["day"] for e in es})
    if len(skipped) < min_skipped or len(days) < MIN_DAYS or not kept:
        return "NOT_ENOUGH_DATA", {"skipped": len(skipped), "kept": len(kept), "days": len(days)}
    mid = days[len(days) // 2]
    mean = lambda g: sum(e["net"] for e in g) / len(g) if g else None
    halves = [([e for e in skipped if (e["day"] < mid) == first], [e for e in kept if (e["day"] < mid) == first]) for first in (True, False)]
    gaps = [(mean(s), mean(k)) for s, k in halves]
    imp = pm2.improvement(es, [e["skip"] for e in es])
    p95 = sorted(null)[int(0.95 * (len(null) - 1))] if null else float("inf")
    ms, mk = mean(skipped), mean(kept)
    ok = (ms < 0 and ms < mk and all(a is not None and b is not None and a < b for a, b in gaps) and imp > p95)
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"skipped": len(skipped), "kept": len(kept), "days": len(days), "skipped_mean": ms, "kept_mean": mk, "imp": imp, "p95": p95,
                                                          "gaps": gaps}


def run(now_ts: int | None = None) -> None:
    now = int(time.time()) if now_ts is None else now_ts
    if now < fwd1.EARLIEST_READ_TS:
        print("Too early: the registered single read is on or after 2026-11-16. Not run; nothing recorded.")
        return
    markets, vol = A.load_alts()
    es = entries(L.hold_rule(markets, **L.L1), vol)
    print(f"{len(markets)} markets in fwd1.sqlite; {len(es)} forward Bitcoin and Ethereum entries on {len({e['day'] for e in es})} days. Signal counts first.\n")
    v, s = verdict(es, pm2.null_improvements(es) if es else [])
    c = lambda x: f"{x * 100:+.2f}c" if x is not None else "n/a"
    if "skipped_mean" in s:
        print(f"VOL1: skipped {s['skipped']} of {len(es)} entries; skipped mean net {c(s['skipped_mean'])}, kept mean net {c(s['kept_mean'])}; improvement {c(s['imp'])} per entry, permutation 95th percentile {c(s['p95'])}")
        print(f"    halves (skipped / kept): {c(s['gaps'][0][0])} / {c(s['gaps'][0][1])} and {c(s['gaps'][1][0])} / {c(s['gaps'][1][1])}")
    else:
        print(f"VOL1: skipped {s['skipped']}, kept {s['kept']} on {s['days']} days")
    print(f"    -> {v}")
    for series in SERIES:
        for name, flag in (("skipped", True), ("kept", False)):
            g = [e for e in es if e["series"] == series and e["skip"] == flag]
            if g:
                print(f"    {series} {name}: n={len(g)} mean net {c(st.mean(e['net'] for e in g))} (information only)")


if __name__ == "__main__":
    run()
