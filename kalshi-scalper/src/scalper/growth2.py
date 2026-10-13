"""GROWTH2: the same account simulation as `growth.py`, on the 68 days of public candles, with and without XRP and Dogecoin appended to the END of the series list.
Information, not a hypothesis test: nothing here is a try and nothing in it changes the bot. Day-block bootstrap of the days, each entry filled with probability FILL, the live sizing,
window cap and day stop of `growth.py` (the profit add-on pool and the weekly review are left out, as there).

The scenario "XRP and Dogecoin at half their measured edge" shifts their entries' nets so their mean equals half of what was measured; "at +0.5c" sets it to +0.5c.
Usage: python -m scalper.growth2
"""
from __future__ import annotations

import random
import statistics as st

from . import altseries as A
from . import growth as G
from . import lstrats as L
from .paths import DATA_DIR
from . import e3b, l1b
from .scalps import load as load_book

LIVE = ("KXBTC15M", "KXGOLD15M", "KXETH15M")
APPENDED = ("KXXRP15M", "KXDOGE15M")


def load_entries() -> list[dict]:
    """All L1 entries on the five series over the 68 days, from the four databases."""
    out = []
    A.ALT_DB = DATA_DIR / "l1b.sqlite"
    m, _ = A.load_alts()
    out += [e for e in L.hold_rule(m, **L.L1) if e["series"] in LIVE and e["close_ts"] < l1b.FLOOR_TS]
    book, _ = load_book()
    out += [e for e in L.hold_rule(book, **L.L1) if e["series"] in LIVE]
    A.ALT_DB = DATA_DIR / "alts2.sqlite"
    m, _ = A.load_alts()
    out += [e for e in L.hold_rule(m, **L.L1) if e["series"] in APPENDED]
    A.ALT_DB = DATA_DIR / "e3b.sqlite"
    m, _ = A.load_alts()
    out += [e for e in L.hold_rule(m, **L.L1) if e["series"] in APPENDED and e["close_ts"] < e3b.FLOOR_TS]
    return out


def shift_series(entries: list[dict], series: tuple, target_mean: float | None) -> list[dict]:
    """Copy of `entries` in which the nets of `series` are shifted by a constant so their mean is `target_mean` (None leaves them as measured)."""
    if target_mean is None:
        return [dict(e) for e in entries]
    mine = [e["net"] for e in entries if e["series"] in series]
    delta = target_mean - (sum(mine) / len(mine)) if mine else 0.0
    return [dict(e, net=e["net"] + delta) if e["series"] in series else dict(e) for e in entries]


def main() -> None:
    G.SERIES_ORDER = {"KXBTC15M": 0, "KXGOLD15M": 1, "KXETH15M": 2, "KXXRP15M": 3, "KXDOGE15M": 4}
    ents = load_entries()
    xd = [e["net"] for e in ents if e["series"] in APPENDED]
    print(f"{len(ents)} entries on {len({e['day'] for e in ents})} days; XRP and Dogecoin measured mean {st.mean(xd) * 100:+.2f}c on {len(xd)} entries. Start ${G.START:.0f} plus ${G.DEPOSIT:.0f} every 30 days, {G.PATHS} paths of {G.HORIZON_DAYS} days.\n")
    cases = (("live three only", LIVE, None), ("three + XRP, Dogecoin at the end, as measured", LIVE + APPENDED, None),
             ("three + XRP, Dogecoin at +0.5c", LIVE + APPENDED, 0.005), ("three + XRP, Dogecoin at 0.0c", LIVE + APPENDED, 0.0))
    for name, series, target in cases:
        use = [e for e in shift_series(ents, APPENDED, target) if e["series"] in series]
        pool = G.by_day(use)
        rng = random.Random(53)
        paths = [G.simulate_path(pool, 0.0, rng) for _ in range(G.PATHS)]
        s = G.summarize(paths)
        print(name)
        for cp in (90, 180, 360):
            v = s[cp]
            print(f"   day {cp:>3}: paid in ${v['paid']:>6.0f}  5th ${v['p5']:>7.0f}  median ${v['p50']:>7.0f}  95th ${v['p95']:>7.0f}   below paid-in {v['below']:.0%}")
    print("\nNo scenario here is a forecast. The XRP and Dogecoin edge is found on 41 days and held on 29; E3F reads new days on or after 2026-11-16.")


if __name__ == "__main__":
    main()
