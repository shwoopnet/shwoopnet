"""Information (README, "Information: the 25c exit on 40 days"): what the live exit line does to L1 entries in the history. Not a hypothesis and not a try; nothing here places an order.

For every L1 entry (the candle ending 360 s before the close, favourite ask 0.88 to 0.97) look at the candles AFTER the entry candle: if the held side's closing bid is at or below the line
(0.25) at some minute close, a sell is assumed at that minute's bid minus SLIP (an optimistic 0c and a pessimistic 5c are both printed), otherwise the position is held to settlement.
Candle closes are a coarse proxy for the live watch, which looks about every 10 seconds, so the number of triggers here is a lower bound.

Usage: python -m scalper.exit25
"""
from __future__ import annotations

import statistics as st

from . import lstrats as L
from .analyze import valid_quote
from .scalps import fee, load as load_markets

LINE = 0.25
SLIPS = (0.0, 0.05)


def side_bid(side: str, bid: float, ask: float) -> float:
    return bid if side == "yes" else round(1.0 - ask, 4)


def exit_outcome(entry: dict, candles: list[tuple], close_ts: int, slip: float):
    """(net if the line is used, net if held, triggered) for one entry. Candles are (end, bid, ask, bid_h, ask_l) in time order; only those strictly after the entry candle count."""
    t0 = close_ts - L.L1["left_s"]
    side, price = entry["side"], entry["price"]
    held = entry["net"]
    for c in candles:
        if c[0] <= t0:
            continue
        if c[1] is None or c[2] is None or not valid_quote(c[1], c[2]):
            continue
        b = side_bid(side, c[1], c[2])
        if b <= LINE:
            got = max(0.0, b - slip)
            return got - fee(got) - price - fee(price), held, True
    return held, held, False


def main() -> None:
    markets, _ = load_markets()
    ents = {e["ticker"]: e for e in L.hold_rule(markets, **L.L1)}
    by = {m[0]: m for m in markets}
    rows = {s: [] for s in SLIPS}
    triggered = []
    for t, e in ents.items():
        m = by[t]
        for s in SLIPS:
            used, held, trig = exit_outcome(e, sorted(m[2]), m[3], s)
            rows[s].append((used, held, trig, e))
    n = len(ents)
    trig = [r for r in rows[SLIPS[0]] if r[2]]
    print(f"{n} L1 entries; the {LINE:.0%} line is crossed at a minute close in {len(trig)} of them ({len(trig) / n:.1%}).")
    if trig:
        won = sum(1 for r in trig if r[1] > 0)
        print(f"Of those {len(trig)}, held to settlement: {won} won ({won / len(trig):.1%}), mean net if held {st.mean(r[1] for r in trig) * 100:+.1f}c per contract.")
    for s in SLIPS:
        used = [r[0] for r in rows[s]]
        held = [r[1] for r in rows[s]]
        print(f"slip {s * 100:.0f}c: mean net per entry with the line {st.mean(used) * 100:+.3f}c against hold-only {st.mean(held) * 100:+.3f}c; "
              f"sum difference over {n} entries {(sum(used) - sum(held)) * 100:+.1f}c per contract")
        tr = [r for r in rows[s] if r[2]]
        if tr:
            print(f"    on the {len(tr)} triggered entries: with the line {st.mean(r[0] for r in tr) * 100:+.1f}c, held {st.mean(r[1] for r in tr) * 100:+.1f}c per contract")


if __name__ == "__main__":
    main()
