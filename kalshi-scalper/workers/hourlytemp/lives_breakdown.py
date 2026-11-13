#!/usr/bin/env python3
"""Hourly temperature: a TIMES-ONLY breakdown of the landed lists, approved by the Head of R&D (08:12Z Nov 13, 2026)
after the audited builder stopped on its 60 minute life rule. It decides nothing: it prints counts for a ruling.

  lives_breakdown.py <lists run>

From each settled market it takes exactly three fields: ticker, open_time, close_time. It reads no price, no
strike, no volume, no result, no rules text, and it does not read the open-market answers. It uses the audited
reader's own list reader, series, window and guard (hourlytemp.py), so the same answers are read the same way.
Nothing is written. Standard library only.
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hourlytemp as H  # noqa: E402

TAG = " [times only, no price, no result]"


def hour(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H")


def main():
    H.refuse_all()
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    rows, skipped = [], 0
    for m in H.read_lists(sys.argv[1], "settled_"):
        try:
            tk, o, c = m["ticker"], H.ts(m["open_time"]), H.ts(m["close_time"])
        except (KeyError, TypeError, ValueError, AttributeError):
            skipped += 1
            continue
        if not H.ts(H.FROM) <= c <= H.ts(H.TO):
            sys.exit("REFUSED: %s closes outside the fixed seven days" % tk)
        rows.append((tk.split("-")[0], c, c - o))
    odd = [r for r in rows if r[2] != H.LIFE_S]
    print("settled markets %d | without a ticker or a time %d | life not exactly %d s: %d%s" % (len(rows), skipped, H.LIFE_S, len(odd), TAG))

    print("1. Life lengths of the odd markets (seconds: count per series)%s" % TAG)
    for life in sorted({r[2] for r in odd}):
        per = ", ".join("%s %d" % (s, sum(1 for r in odd if r[0] == s and r[2] == life)) for s in H.SERIES if any(r[0] == s and r[2] == life for r in odd))
        print("   %5d s: %3d  (%s)" % (life, sum(1 for r in odd if r[2] == life), per))
    print("   per series: " + ", ".join("%s %d of %d" % (s, sum(1 for r in odd if r[0] == s), sum(1 for r in rows if r[0] == s)) for s in H.SERIES))
    off_hour = sum(1 for r in rows if r[1] % 3600)
    print("   markets whose close is not on the clock hour: %d" % off_hour)

    first = H.ts(H.FROM)
    expected = [first + 3600 * k for k in range((H.ts(H.TO) + 1 - first) // 3600)]
    print("2. Clock hours (close hours, UTC) per series against the %d of the seven days%s" % (len(expected), TAG))
    union = set()
    for s in H.SERIES:
        have = {r[1] for r in rows if r[0] == s}
        union |= have
        missing = [hour(t) for t in expected if t not in have]
        shown = ", ".join(missing[:40]) + (" ... and %d more" % (len(missing) - 40) if len(missing) > 40 else "")
        print("   %s: %d present, %d missing%s" % (s, len(have & set(expected)), len(missing), (": " + shown) if missing else ""))
    print("   close hours with a market of any series: %d" % len(union))

    print("3. Are the odd markets whole hours or part of an hour's ladder?%s" % TAG)
    shapes, whole, part = {}, 0, 0
    per_hour = {}
    for s, c, life in rows:
        per_hour.setdefault((s, c), []).append(life)
    for (s, c), lives in sorted(per_hour.items()):
        n_odd = sum(1 for x in lives if x != H.LIFE_S)
        if not n_odd:
            continue
        whole += n_odd == len(lives)
        part += n_odd != len(lives)
        key = (n_odd, len(lives), len({x for x in lives if x != H.LIFE_S}))
        shapes[key] = shapes.get(key, 0) + 1
    print("   series-hours with an odd market: %d | every market of the hour odd: %d | only part of the hour odd: %d" % (whole + part, whole, part))
    for (n_odd, n_all, n_lives), k in sorted(shapes.items()):
        print("   %2d odd of %2d markets in the hour, %d distinct odd life length(s): %d series-hours" % (n_odd, n_all, n_lives, k))
    sizes = {}
    for lives in per_hour.values():
        sizes[len(lives)] = sizes.get(len(lives), 0) + 1
    print("   markets per series-hour (markets: series-hours): " + ", ".join("%d: %d" % kv for kv in sorted(sizes.items())))
    print("   odd series-hours by close hour of day, UTC (hour: count): " + ", ".join(
        "%02d: %d" % (h, sum(1 for (s, c), lv in per_hour.items() if any(x != H.LIFE_S for x in lv) and datetime.fromtimestamp(c, timezone.utc).hour == h))
        for h in range(24) if any(any(x != H.LIFE_S for x in lv) and datetime.fromtimestamp(c, timezone.utc).hour == h for (s, c), lv in per_hour.items())))
    print("nothing is decided here: the Head of R&D rules; no candle job exists%s" % TAG)


if __name__ == "__main__":
    main()
