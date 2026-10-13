"""PM2 (README, Pre-registration: PM2): skip an L1 entry when Polymarket disagrees, on the older days PM1 never saw. Rules fixed in the README before any Polymarket price for these days was downloaded.
Research only: nothing here places an order and the Polymarket API is only read. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Kalshi windows come from `data/l1b.sqlite` (the L1B download), Polymarket prices go into `data/pm2.sqlite`.
Usage: python -m scalper.pm2 fetch   (after L1B's download is complete)   then, ONCE:   python -m scalper.pm2 run
"""
from __future__ import annotations

import random
import statistics as st
import sys
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone

from . import lstrats as L
from . import pm1
from .calibration import cluster_mean_z
from .paths import DATA_DIR

SRC_DB = DATA_DIR / "l1b.sqlite"
PM2_DB = DATA_DIR / "pm2.sqlite"
FLOOR_TS = int(datetime(2026, 9, 2, 19, 30, tzinfo=timezone.utc).timestamp())      # the earliest close in book.sqlite: nothing on or after it counts
DISAGREE = 0.05
MIN_SKIPPED = 100
Z_BAR = 2.1
NULL_REPS = 200


def windows() -> list[dict]:
    return [w for w in pm1.windows(SRC_DB) if w["close_ts"] < FLOOR_TS]


def fetch() -> None:
    pm1.fetch_windows(PM2_DB, windows())


def entries(obs: list[dict]) -> list[dict]:
    """L1 entries among the PM1-style observations, each flagged `skip` when Polymarket's price for the side bought is at least DISAGREE below Kalshi's mid of that side."""
    out = []
    for o in obs:
        pick = L.favorite(o["bid"], o["ask"], L.L1["band"])
        if pick is None:
            continue
        side, price = pick
        k_side = o["p_k"] if side == "yes" else 1.0 - o["p_k"]
        pm_side = o["p_pm"] if side == "yes" else 1.0 - o["p_pm"]
        out.append({"series": o["series"], "close_ts": o["close_ts"], "day": o["day"], "net": L.net(side, price, o["y"] == 1.0), "skip": pm_side <= k_side - DISAGREE + 1e-12})
    return out


def improvement(es: list[dict], flags: list[bool]) -> float:
    """Kept mean minus the all-entries mean: positive when skipping the flagged entries would have helped."""
    kept = [e["net"] for e, f in zip(es, flags) if not f]
    return (sum(kept) / len(kept) - sum(e["net"] for e in es) / len(es)) if kept else float("-inf")


def null_improvements(es: list[dict], reps: int = NULL_REPS, seed: int = 41) -> list[float]:
    """The same NUMBER of entries per series flagged at random: what skipping that many entries does by chance."""
    rng = random.Random(seed)
    by = defaultdict(list)
    for i, e in enumerate(es):
        by[e["series"]].append(i)
    k = {s: sum(1 for i in idx if es[i]["skip"]) for s, idx in by.items()}
    return [improvement(es, random_flags(by, k, len(es), rng)) for _ in range(reps)]


def random_flags(by: dict, k: dict, n: int, rng: random.Random) -> list[bool]:
    flags = [False] * n
    for s, idx in by.items():
        for i in rng.sample(idx, k[s]):
            flags[i] = True
    return flags


def verdict(es: list[dict], null: list[float]) -> tuple[str, dict]:
    skipped = [e for e in es if e["skip"]]
    kept = [e for e in es if not e["skip"]]
    if len(skipped) < MIN_SKIPPED:
        return "NOT_ENOUGH_DATA", {"skipped": len(skipped), "kept": len(kept)}
    mean_s, _, z = cluster_mean_z([(e["day"], e["net"]) for e in skipped])
    days = sorted({e["day"] for e in es})
    mid = days[len(days) // 2]
    h1 = [e["net"] for e in skipped if e["day"] < mid]
    h2 = [e["net"] for e in skipped if e["day"] >= mid]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    base = sum(e["net"] for e in es) / len(es)
    kept_mean = sum(e["net"] for e in kept) / len(kept) if kept else float("-inf")
    imp = improvement(es, [e["skip"] for e in es])
    p95 = sorted(null)[int(0.95 * (len(null) - 1))] if null else float("inf")
    ok = mean_s < 0 and z <= -Z_BAR and h1 and h2 and m1 < 0 and m2 < 0 and kept_mean > base and imp > p95
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"skipped": len(skipped), "kept": len(kept), "mean": mean_s, "z": z, "h1": m1 if h1 else None, "h2": m2 if h2 else None,
                                                          "kept_mean": kept_mean, "base": base, "imp": imp, "p95": p95}


def run() -> None:
    wins = windows()
    pm = sqlite3.connect(PM2_DB)
    pts: dict = {}
    for s, t, p in pm.execute("SELECT slug, t, p FROM pt"):
        pts.setdefault(s, []).append((t, p))
    es = entries(pm1.observations(wins, pts))
    print(f"{len(wins)} Kalshi windows with a quote (older days), {len(es)} L1 entries with a recent Polymarket point on {len({e['day'] for e in es})} days. Signal counts first.\n")
    v, s = verdict(es, null_improvements(es) if es else [])
    c = lambda x: f"{x * 100:+.2f}c" if x is not None else "n/a"
    print(f"PM2: skipped {s['skipped']} of {len(es)} entries ({s['skipped'] / max(len(es), 1):.1%})")
    if "mean" in s:
        print(f"    skipped entries' mean net {c(s['mean'])} (day clustered z {s['z']:+.2f}); halves {c(s['h1'])} / {c(s['h2'])}")
        print(f"    kept entries' mean net {c(s['kept_mean'])} against all entries {c(s['base'])}; improvement {c(s['imp'])} per entry, permutation 95th percentile {c(s['p95'])}")
    print(f"    -> {v}")
    for series in pm1.ASSETS:
        mine = [e for e in es if e["series"] == series]
        for name, flag in (("skipped", True), ("kept", False)):
            g = [e for e in mine if e["skip"] == flag]
            if g:
                print(f"    {series} {name}: n={len(g)} loss rate {sum(1 for e in g if e['net'] < 0) / len(g):.1%} mean net {c(st.mean(e['net'] for e in g))} (information only)")


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
