"""SMOOTH20 (README, Pre-registration: SMOOTH20): twenty variables of the "smooth climb into the favourite" family, scored at two entries. DISCOVERY is the sixteen non-Bitcoin non-Ethereum
15 minute series; CONFIRMATION is Bitcoin and Ethereum (a different data set, none of its days used to choose anything). Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.smooth20 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import math
import statistics as st
import sys

from . import flips0x as FX
from . import ideas100 as D
from . import ideas20 as I
from . import lstrats as L
from .calibration import cluster_mean_z
from .paths import DATA_DIR

# ---- fixed in the README before any variant was scored ----
DISC_SERIES = FX.SERIES
CONF_SERIES = ("KXBTC15M", "KXETH15M")
ENTRIES = D.ENTRIES
MIN_DISC, MIN_CONF, DISC_C, DISC_Z, CONF_C, CONF_Z, PF_BAR, FALSIFY_C, FALSIFY_Z = 300, 100, 0.010, 3.0, 0.010, 1.65, 1.3, 0.005, 1.0
RESULT = DATA_DIR / "smooth20_result.txt"


def mids(m, c, e, side):
    return [D.side_mid(x, side) for x in e] + [D.side_mid(c, side)]


def steps(v):
    return [b - a for a, b in zip(v, v[1:])]


def r2(v):
    n = len(v)
    xs = list(range(n))
    mx, my = st.mean(xs), st.mean(v)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in v)
    if syy == 0 or n < 3:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, v))
    return sxy * sxy / (sxx * syy) if (sxy > 0) else None          # None for a path that is not rising


def rules():
    out = []

    def add(name, test):
        def rule(m, c, e, band):
            f = L.favorite(c["bid"], c["ask"], band)
            if not f or len(e) < 4:
                return None
            v = mids(m, c, e, f[0])
            return f if test(v) else None
        out.append((name, rule))

    for tol in (0.005, 0.01, 0.02, 0.03):                                           # largest single-minute pullback at most tol and the path rose overall
        add(f"MAXPULL_LE_{int(tol * 1000):03d}", lambda v, tol=tol: min(steps(v)) >= -tol and v[-1] - v[0] >= 0.10)
    add("NO_DOWN_MINUTE", lambda v: min(steps(v)) >= -0.004 and v[-1] - v[0] >= 0.10)
    for k in (2, 3, 4, 5):                                                          # the last k minute changes all up
        add(f"LAST{k}_UP", lambda v, k=k: len(steps(v)) >= k and all(x > 0.004 for x in steps(v)[-k:]))
    for thr in (0.90, 0.95, 0.98):                                                  # straight-line fit
        add(f"R2_GE_{int(thr * 100)}", lambda v, thr=thr: (r := r2(v)) is not None and r >= thr)
    for thr in (1.1, 1.3, 1.5):                                                     # path length over net displacement
        add(f"EFF_LE_{int(thr * 10)}", lambda v, thr=thr: v[-1] - v[0] >= 0.10 and sum(abs(x) for x in steps(v)) / (v[-1] - v[0]) <= thr)
    for thr in (0.10, 0.20):                                                        # worst pullback as a share of the climb
        add(f"PULLSHARE_LE_{int(thr * 100)}", lambda v, thr=thr: v[-1] - v[0] >= 0.10 and (-min(steps(v)) if min(steps(v)) < 0 else 0.0) / (v[-1] - v[0]) <= thr)
    add("UPMINUTES_ALL_BUT_ONE", lambda v: sum(1 for x in steps(v) if x < -0.004) <= 1 and v[-1] - v[0] >= 0.10)
    add("STEADY_STEP", lambda v: (lambda s: len(s) >= 4 and st.mean(s) > 0.02 and st.pstdev(s) <= 0.5 * st.mean(s))(steps(v)))
    add("ACCELERATING", lambda v: (lambda s: len(s) >= 4 and s[-1] >= s[0] and min(s) > -0.004)(steps(v)))
    return out


def entries_for(mk: dict, series: str, rule, left: int, band) -> list[dict]:
    base = I.entries(mk, left, lambda m, c, e, ps: L.favorite(c["bid"], c["ask"], band))
    if not base:
        return []
    bn, bs = st.mean(r["net"] for r in base), st.mean(r["stress"] for r in base)
    return [{**r, "raw": r["net"], "net": r["net"] - bn, "stress": r["stress"] - bs, "series": series}
            for r in I.entries(mk, left, lambda m, c, e, ps: rule(m, c, e, band))]


def pf_raw(rows):
    w = sum(r["raw"] for r in rows if r["raw"] > 0)
    l = -sum(r["raw"] for r in rows if r["raw"] < 0)
    return w / l if l else float("inf")


def stat(rows):
    if len(rows) < 2:
        return 0.0, 0.0
    m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    return m, z


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    data = {s: I.load_btc(s) for s in DISC_SERIES + CONF_SERIES}
    out = [f"SMOOTH20: discovery {len(DISC_SERIES)} series, confirmation Bitcoin and Ethereum"]
    for ename, (left, band) in ENTRIES.items():
        for name, rule in rules():
            d = [r for s in DISC_SERIES if data[s] for r in entries_for(data[s], s, rule, left, band)]
            c = [r for s in CONF_SERIES for r in entries_for(data[s], s, rule, left, band)]
            dm, dz = stat(d)
            cm, cz = stat(c)
            if len(d) < MIN_DISC or len(c) < MIN_CONF:
                v = "NOT_ENOUGH_DATA"
            elif dm >= DISC_C and dz >= DISC_Z and cm >= CONF_C and cz >= CONF_Z and pf_raw(d) >= PF_BAR and pf_raw(c) >= PF_BAR and sum(r["stress"] for r in d) > 0 and sum(r["stress"] for r in c) > 0:
                v = "NOT_YET_FALSIFIED"
            else:
                am, az = stat(d + c)
                v = "FALSIFIED" if (am < FALSIFY_C or az < FALSIFY_Z) else "NOT_ENOUGH_DATA"
            out.append(f"{ename:5s} {name:22s} {v:18s} disc n={len(d):5d} {100 * dm:+6.2f}c z {dz:+5.2f} PF {pf_raw(d) if d else 0:.2f} | conf n={len(c):5d} {100 * cm:+6.2f}c z {cz:+5.2f} PF {pf_raw(c) if c else 0:.2f}")
    RESULT.write_text("\n".join(out) + "\n")
    print(out[0], "\n", sum(1 for x in out if "NOT_YET_FALSIFIED" in x), "NOT_YET_FALSIFIED;", sum(1 for x in out if " FALSIFIED " in x), "FALSIFIED;", sum(1 for x in out if "NOT_ENOUGH_DATA" in x), "NOT_ENOUGH_DATA")


if __name__ == "__main__":
    main(sys.argv)
