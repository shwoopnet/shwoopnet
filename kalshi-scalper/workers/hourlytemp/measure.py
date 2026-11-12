#!/usr/bin/env python3
"""Hourly city temperature: the COST AND TIMING measurement, zero tries. Committed Nov 12,
2026, before any list or candle was pulled. Note: workers/HOURLYTEMP_MEASUREMENT_NOTE.md.

Kalshi's own data only (Head of R&D, Nov 12): spread, round trip, the size at the touch and
how the strikes' prices sit 55, 30 and 10 minutes before the hour. No result field is read,
no outside reading is used, no rule is scored.

"Near the money" is defined from the quotes alone: at each look the strike whose YES mid is
nearest 50c is rank 0; strikes are ranked by distance from it in strike order.

Rule fixed now (Head of R&D): the family is CLOSED as too costly if the median round trip of
the two-sided strikes within two ranks of the money is above 5c at every look in every city.

Usage: python3 measure.py <markets.json> <folder of the HOURLYTEMP_LISTS run> <folder of the candle run> [...]
"""
import glob, gzip, json, os, sys

LOOKS = (55, 30, 10)        # minutes before the hour (the market opens 60 minutes before it)
NEAR = 2                    # ranks either side of the money that count as near the money
COST_BAR = 0.05
FEE = 0.07


def price(side):
    if not isinstance(side, dict):
        return None
    for k in ("close_dollars", "close"):
        v = side.get(k)
        if v in (None, ""):
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        return v / 100.0 if v > 1.0 else v
    return None


def walk(node, found, hint=None):
    if isinstance(node, dict):
        tk = node.get("market_ticker") or node.get("ticker") or hint
        c = node.get("candlesticks")
        if isinstance(c, list) and c and isinstance(c[0], dict) and "end_period_ts" in c[0]:
            if tk:
                found.setdefault(tk, []).extend(c)
        for v in node.values():
            walk(v, found, tk)
    elif isinstance(node, list):
        for v in node:
            walk(v, found, hint)


def med(v):
    v = sorted(v)
    return v[len(v) // 2] if v else None


def fmt(x, cents=True):
    return "n/a" if x is None else (f"{100 * x:.1f}c" if cents else f"{x:.0%}")


def main():
    markets = json.load(open(sys.argv[1]))
    lists_run, cand = sys.argv[2], {}
    for run in sys.argv[3:]:
        for f in sorted(glob.glob(os.path.join(run, "[0-9]*.json.gz"))):
            try:
                walk(json.load(gzip.open(f, "rt")), cand)
            except (ValueError, OSError):
                continue
    events = {}
    for m in markets:
        events.setdefault((m["series"], m["event"]), []).append(m)
    print("candle freshness measured on Bitcoin 15 minute only, not on this family; one-minute resolution, no seconds-level claim")
    print(f"markets in the fixed list {len(markets)} | events (a city and an hour) {len(events)} | markets with any candle {sum(1 for m in markets if m['ticker'] in cand)}")
    costly = True
    for series in sorted({s for s, _ in events}):
        for look in LOOKS:
            quoted = two = 0
            spreads, trips, near_trips, decided, traded_min, all_min = [], [], [], 0, 0, 0
            side_ask = {1: [], 2: [], 3: []}
            for (s, ev), ms in events.items():
                if s != series:
                    continue
                rows = []
                for m in sorted(ms, key=lambda m: m["strike"]):
                    q = {int(c["end_period_ts"]) // 60: c for c in cand.get(m["ticker"], [])}
                    c = q.get((m["close_ts"] - look * 60) // 60)
                    for c2 in q.values():
                        all_min += 1
                        try:
                            traded_min += 1 if float(c2.get("volume_fp", c2.get("volume", 0)) or 0) > 0 else 0
                        except (TypeError, ValueError):
                            pass
                    if c is None:
                        continue
                    quoted += 1
                    b, a = price(c.get("yes_bid")), price(c.get("yes_ask"))
                    if b is None or a is None or not (0 < b < a < 1):
                        continue
                    two += 1
                    mid = (a + b) / 2
                    spreads.append(a - b)
                    trips.append((a - b) + 2 * FEE * mid * (1 - mid))
                    decided += 1 if (mid >= 0.95 or mid <= 0.05) else 0
                    rows.append((m["strike"], b, a, mid))
                if not rows:
                    continue
                k0 = min(range(len(rows)), key=lambda i: abs(rows[i][3] - 0.5))
                for i, (strike, b, a, mid) in enumerate(rows):
                    r = abs(i - k0)
                    if r <= NEAR:
                        near_trips.append((a - b) + 2 * FEE * mid * (1 - mid))
                    if r >= 1:
                        side_ask[min(r, 3)].append(a if i < k0 else 1 - b)   # the nearer-certain side: YES below the money, NO above it
            nt = med(near_trips)
            if nt is not None and nt <= COST_BAR:
                costly = False
            print(f"{series} {look:2d} min before the hour: strikes with a candle {quoted} | two-sided {two} ({fmt(two / quoted if quoted else None, False)}) | median spread {fmt(med(spreads))}"
                  f" | median round trip {fmt(med(trips))} | near the money (n {len(near_trips)}) {fmt(nt)} | priced 95c or 5c and beyond {fmt(decided / two if two else None, False)}"
                  f" | ask of the nearer-certain side at rank 1, 2, 3+: {fmt(med(side_ask[1]))}, {fmt(med(side_ask[2]))}, {fmt(med(side_ask[3]))}")
        if all_min:
            print(f"{series}: market-minutes with a candle {all_min // len(LOOKS)} | with a trade {fmt(traded_min / all_min, False)}")
    sizes = {}
    try:
        man = json.load(open(os.path.join(lists_run, "manifest.json")))
        for row in man.get("rows", []):
            if row.get("status") == 200 and str(row.get("id", "")).startswith("open_"):
                body = json.load(gzip.open(os.path.join(lists_run, row["file"]), "rt"))
                for m in body.get("markets", []) if isinstance(body, dict) else []:
                    for k in ("yes_ask_size_fp", "yes_bid_size_fp"):
                        try:
                            v = float(m.get(k))
                        except (TypeError, ValueError):
                            continue
                        if v > 0:
                            sizes.setdefault(m["ticker"].split("-")[0], []).append(v)
    except (OSError, ValueError):
        pass
    for s in sorted(sizes):
        print(f"{s}: size at the touch on open markets (a list copy up to about 11 s old, a level only): median {med(sizes[s]):.0f} contracts over {len(sizes[s])} quoted sides")
    if not any(m["ticker"] in cand for m in markets):
        print("VERDICT: no candles read")
        return
    print("VERDICT: " + ("CLOSED as too costly (median round trip near the money above 5c at every look in every city)" if costly
                        else "NOT closed on cost: at least one city and look has a median round trip near the money of 5c or less. Nothing beyond this measurement is approved."))


if __name__ == "__main__":
    main()
