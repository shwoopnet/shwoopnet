"""Describes the recorded books around the L1 window. Information only: no rule, no verdict, nothing here decides anything.

For snapshots 330 to 400 seconds before close, where a side's ask is 0.88 to 0.97 (L1's band): how often the ask moves up, down or not at all by the next
snapshot (about 10 seconds later), how wide the spread is, and how much sits at the touch. This is the size of the "price moved between the
look and the order" effect behind the live no-fills; it does not say what to do about it.

Usage: python -m scalper.obstats
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict

from .bookmaker import OB, WINDOW


def stats(rows: list[tuple]) -> dict:
    """rows: (ts, ticker, close_epoch, side_ask, side_bid, touch_size) already restricted to L1's band and window, any order."""
    by: dict = defaultdict(list)
    for r in rows:
        by[r[1]].append(r)
    up = down = same = gaps = 0
    spreads, sizes = [], []
    for snaps in by.values():
        snaps.sort()
        for a, b in zip(snaps, snaps[1:]):
            dt = b[0] - a[0]
            if dt > 20:
                gaps += 1
                continue
            d = round(b[3] - a[3], 4)
            up += d > 0
            down += d < 0
            same += d == 0
        for r in snaps:
            if r[4] is not None:
                spreads.append(round(r[3] - r[4], 4))
            if r[5] is not None:
                sizes.append(r[5])
    n = up + down + same
    return {"pairs": n, "up": up / n if n else None, "down": down / n if n else None, "same": same / n if n else None, "gaps": gaps,
            "median_spread": sorted(spreads)[len(spreads) // 2] if spreads else None,
            "median_touch_size": sorted(sizes)[len(sizes) // 2] if sizes else None}


def main() -> None:
    db = sqlite3.connect(OB)
    rows = []
    for ts, ticker, close, ya, yb, na, nb, yl, nl in db.execute("SELECT ts, ticker, close_ts, yes_ask, yes_bid, no_ask, no_bid, yes_levels, no_levels FROM ob"):
        from datetime import datetime
        c = datetime.fromisoformat(close.replace("Z", "+00:00")).timestamp()
        if not (c - WINDOW[1] <= ts <= c - WINDOW[0]):
            continue
        import json
        # the touch of the side we would BUY is the other side's best bid level: a YES ask of x is a NO bid of 1 - x
        for ask, bid, levels in ((ya, yb, nl), (na, nb, yl)):
            if ask is not None and 0.88 <= ask <= 0.97:
                lv = json.loads(levels) if levels else []
                rows.append((ts, ticker + ("Y" if ask is ya else "N"), c, ask, bid, lv[-1][1] if lv else None))
    s = stats(rows)
    print(f"{len(rows)} snapshots in the L1 window and band; {s['pairs']} consecutive pairs ({s['gaps']} skipped for a gap over 20 s)")
    if s["pairs"]:
        print(f"next snapshot's ask: up {s['up'] * 100:.1f}%, same {s['same'] * 100:.1f}%, down {s['down'] * 100:.1f}%; median spread {s['median_spread']}; median size at the touch {s['median_touch_size']}")
    print("Information only.")


if __name__ == "__main__":
    main()
