"""How much has the recorder saved, and did it miss anything?

Usage: python -m scalper.status

A laptop that sleeps stops recording without any error, so silence looks the
same as "nothing happened". This reports gaps explicitly: a 40 minute hole in
the data is a fact about the data, and anything computed across it (a move over
60 seconds, an average spread) must not span it.
"""
from __future__ import annotations

import sqlite3
import time
from collections import defaultdict

from .recorder import DB

GAP_SECONDS = 30.0  # the recorder polls every 2s, so 30s of silence is a real hole


def find_gaps(timestamps: list[float], threshold: float = GAP_SECONDS) -> list[tuple[float, float]]:
    """(start, end) of every stretch longer than `threshold` with no snapshot."""
    ts = sorted(timestamps)
    return [(a, b) for a, b in zip(ts, ts[1:]) if b - a > threshold]


def _fmt(t: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def main() -> None:
    if not DB.exists():
        print(f"No data yet at {DB}. Is the recorder running?")
        return
    db = sqlite3.connect(DB)
    by = defaultdict(list)
    for series, ts in db.execute("SELECT series, ts FROM snap"):
        by[series].append(ts)
    if not by:
        print("Database exists but holds no snapshots yet.")
        return
    now = time.time()
    for series, ts in sorted(by.items()):
        gaps = find_gaps(ts)
        lost = sum(b - a for a, b in gaps)
        span = max(ts) - min(ts)
        print(f"{series}")
        print(f"  snapshots : {len(ts):,}")
        print(f"  first     : {_fmt(min(ts))}")
        print(f"  latest    : {_fmt(max(ts))}  ({now - max(ts):.0f}s ago)")
        print(f"  gaps >30s : {len(gaps)}  ({lost / 60:.1f} min missing of {span / 60:.1f} min)")
        for a, b in gaps[-3:]:
            print(f"    missing {_fmt(a)} to {_fmt(b)}  ({(b - a) / 60:.1f} min)")
    results = db.execute("SELECT COUNT(*) FROM result").fetchone()[0]
    print(f"\nsettled results saved: {results}")
    latest = max(max(v) for v in by.values())
    if now - latest > 60:
        print("\nWARNING: nothing recorded in the last minute. The recorder is not running, or the computer slept.")


if __name__ == "__main__":
    main()
