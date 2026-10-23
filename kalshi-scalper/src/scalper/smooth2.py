"""SMOOTH2 (README, Pre-registration: SMOOTH2): twenty further path variables for the 6 minute entry: the bid and ask paths separately, how long ago the favourite crossed 0.7 or 0.8, the opening level,
the volume and open-interest paths, and conditions stacked on the strict smooth climb. Same design as SMOOTH20: DISCOVERY on the sixteen non-Bitcoin non-Ethereum series, CONFIRMATION on Bitcoin and
Ethereum, each entry scored against its own series' L1 baseline. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.smooth2 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import sys

from . import ideas20 as I
from . import lstrats as L
from . import smooth20 as S
from .paths import DATA_DIR

LEFT, BAND = S.ENTRIES["L1360"]
RESULT = DATA_DIR / "smooth2_result.txt"
NOT_DOWN = lambda v: min(S.steps(v)) >= -0.004 and v[-1] - v[0] >= 0.10          # the strict smooth climb (FLIPS_0 / NO_DOWN_MINUTE)


def paths(c, e, side):
    cs = list(e) + [c]
    mid = [S.D.side_mid(x, side) for x in cs]
    ask = [x["ask"] if side == "yes" else round(1 - x["bid"], 4) for x in cs]
    bid = [x["bid"] if side == "yes" else round(1 - x["ask"], 4) for x in cs]
    return cs, mid, bid, ask


def age(mid, level):
    """Candles between the first time the mid is at or above `level` and the decision candle (0 = it first got there now); None if never."""
    for i, v in enumerate(mid):
        if v >= level:
            return len(mid) - 1 - i
    return None


def rules():
    out = []

    def add(name, test):
        def rule(m, c, e, band):
            f = L.favorite(c["bid"], c["ask"], band)
            if not f or len(e) < 4:
                return None
            cs, mid, bid, ask = paths(c, e, f[0])
            return f if test(cs, mid, bid, ask) else None
        out.append((name, rule))

    mono = lambda v: min(S.steps(v)) >= -0.004 and v[-1] - v[0] >= 0.10
    add("BIDMONO", lambda cs, mid, bid, ask: mono(bid))
    add("ASKMONO", lambda cs, mid, bid, ask: mono(ask))
    add("SPREADSTABLE", lambda cs, mid, bid, ask: max(a - b for a, b in zip(ask, bid)) <= 0.02)
    add("BIDLEADS", lambda cs, mid, bid, ask: len(mid) >= 4 and (bid[-1] - bid[-4]) > (ask[-1] - ask[-4]) + 0.005)
    add("AGE80_GE3", lambda cs, mid, bid, ask: (a := age(mid, 0.80)) is not None and a >= 3)
    add("AGE80_LE1", lambda cs, mid, bid, ask: (a := age(mid, 0.80)) is not None and a <= 1)
    add("AGE70_GE4", lambda cs, mid, bid, ask: (a := age(mid, 0.70)) is not None and a >= 4)
    add("AGE70_LE2", lambda cs, mid, bid, ask: (a := age(mid, 0.70)) is not None and a <= 2)
    add("CLEANSTART_SMOOTH", lambda cs, mid, bid, ask: 0.45 <= mid[0] <= 0.55 and NOT_DOWN(mid))
    add("OFFSTART_SMOOTH", lambda cs, mid, bid, ask: not (0.45 <= mid[0] <= 0.55) and NOT_DOWN(mid))
    vols = lambda cs: [x["vol"] for x in cs[-4:]]
    add("VOL_RISING", lambda cs, mid, bid, ask: all(b >= a for a, b in zip(vols(cs), vols(cs)[1:])) and vols(cs)[-1] > vols(cs)[0])
    add("VOL_FALLING", lambda cs, mid, bid, ask: all(b <= a for a, b in zip(vols(cs), vols(cs)[1:])) and vols(cs)[-1] < vols(cs)[0])
    ois = lambda cs: [x["oi"] for x in cs]
    add("OI_MONO_UP", lambda cs, mid, bid, ask: all(b >= a for a, b in zip(ois(cs), ois(cs)[1:])) and ois(cs)[-1] > ois(cs)[0])
    add("OI_STALL", lambda cs, mid, bid, ask: len(cs) >= 4 and cs[-4]["oi"] > 0 and cs[-1]["oi"] / cs[-4]["oi"] <= 1.005)
    add("SMOOTH_AND_OI", lambda cs, mid, bid, ask: NOT_DOWN(mid) and all(b >= a for a, b in zip(ois(cs), ois(cs)[1:])))
    add("SMOOTH_AND_VOLRISE", lambda cs, mid, bid, ask: NOT_DOWN(mid) and vols(cs)[-1] >= vols(cs)[0])
    add("SMOOTH_AND_TIGHT", lambda cs, mid, bid, ask: NOT_DOWN(mid) and ask[-1] - bid[-1] <= 0.0101)
    add("SMOOTH_AND_FAST", lambda cs, mid, bid, ask: NOT_DOWN(mid) and (a := age(mid, 0.80)) is not None and a <= 1)
    add("LAST_STEP_BIG", lambda cs, mid, bid, ask: mid[-1] - mid[-2] >= 0.05)
    add("LAST_STEP_SMALL", lambda cs, mid, bid, ask: 0 <= mid[-1] - mid[-2] <= 0.01)
    return out


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    data = {s: I.load_btc(s) for s in S.DISC_SERIES + S.CONF_SERIES}
    out = [f"SMOOTH2: discovery {len(S.DISC_SERIES)} series, confirmation Bitcoin and Ethereum, entry L1360"]
    for name, rule in rules():
        d = [r for s in S.DISC_SERIES if data[s] for r in S.entries_for(data[s], s, rule, LEFT, BAND)]
        c = [r for s in S.CONF_SERIES for r in S.entries_for(data[s], s, rule, LEFT, BAND)]
        dm, dz = S.stat(d)
        cm, cz = S.stat(c)
        if len(d) < S.MIN_DISC or len(c) < S.MIN_CONF:
            v = "NOT_ENOUGH_DATA"
        elif dm >= S.DISC_C and dz >= S.DISC_Z and cm >= S.CONF_C and cz >= S.CONF_Z and S.pf_raw(d) >= S.PF_BAR and S.pf_raw(c) >= S.PF_BAR and sum(r["stress"] for r in d) > 0 and sum(r["stress"] for r in c) > 0:
            v = "NOT_YET_FALSIFIED"
        else:
            am, az = S.stat(d + c)
            v = "FALSIFIED" if (am < S.FALSIFY_C or az < S.FALSIFY_Z) else "NOT_ENOUGH_DATA"
        out.append(f"{name:20s} {v:18s} disc n={len(d):5d} {100 * dm:+6.2f}c z {dz:+5.2f} PF {S.pf_raw(d) if d else 0:.2f} | conf n={len(c):5d} {100 * cm:+6.2f}c z {cz:+5.2f} PF {S.pf_raw(c) if c else 0:.2f}")
    RESULT.write_text("\n".join(out) + "\n")
    print(out[0], "\n", sum(1 for x in out if "NOT_YET_FALSIFIED" in x), "NOT_YET_FALSIFIED;", sum(1 for x in out if " FALSIFIED " in x), "FALSIFIED;", sum(1 for x in out if "NOT_ENOUGH_DATA" in x), "NOT_ENOUGH_DATA")


if __name__ == "__main__":
    main(sys.argv)
