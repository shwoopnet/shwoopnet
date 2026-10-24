"""COMM1 (README, Pre-registration: COMM1): twenty rules for the six commodity 15 minute series (silver, WTI, copper, natural gas, platinum, palladium), pooled, from three families that worked
elsewhere or are specific to futures-settled markets: session block of the UTC day, price band by time, and the smooth climb. Discovery on the first two thirds of the days, confirmation on the last third,
each rule scored against its own series' baseline for the same entry. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.comm1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone

from . import ideas20 as I
from . import lstrats as L
from . import smooth20 as S
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before any outcome was scored ----
SERIES = ("KXSILVER15M", "KXWTI15M", "KXCOPPER15M", "KXNATGAS15M", "KXPLATINUM15M", "KXPALLADIUM15M")
ENTRIES = {"E360": 360, "E600": 600}
MIN_DISC, MIN_CONF, DISC_Z = 200, 100, 2.5
RESULT = DATA_DIR / "comm1_result.txt"


def as_market(m: tuple) -> dict:
    t, s, c, cl, res = m
    return {"close": cl, "res": res, "strike": None, "c": [{"end": e, "bid": b, "ask": a, "bid_h": b, "bid_l": b, "ask_h": a, "ask_l": a, "vol": 0.0, "oi": 0.0, "last": a} for e, b, a, *_ in sorted(c)]}


def hour(m): return datetime.fromtimestamp(m["close"], timezone.utc).hour


def rules():
    R = []
    def fav(c, band): return L.favorite(c["bid"], c["ask"], band)
    def block(lo, hi):
        return lambda m, c, e, band: (f if (f := fav(c, band)) and lo <= hour(m) < hi else None)
    for lo, hi in ((0, 6), (6, 12), (12, 18), (18, 24)):
        R.append((f"SESSION_{lo:02d}_{hi:02d}", block(lo, hi)))
    R.append(("WEEKEND", lambda m, c, e, band: (f if (f := fav(c, band)) and datetime.fromtimestamp(m["close"], timezone.utc).weekday() >= 5 else None)))
    R.append(("WEEKDAY", lambda m, c, e, band: (f if (f := fav(c, band)) and datetime.fromtimestamp(m["close"], timezone.utc).weekday() < 5 else None)))
    for lo, hi in ((0.80, 0.88), (0.88, 0.93), (0.93, 0.97), (0.97, 0.995)):                  # price bands (the entry band itself is replaced by this band)
        R.append((f"BAND_{int(lo * 100)}_{int(hi * 1000)}", None))
    rl = dict(S.rules())
    for name in ("MAXPULL_LE_010", "EFF_LE_11", "NO_DOWN_MINUTE"):
        r = rl[name]
        R.append((name, lambda m, c, e, band, r=r: r(m, c, e, band)))
    return R


def band_rules():
    out = []
    for lo, hi in ((0.80, 0.88), (0.88, 0.93), (0.93, 0.97), (0.97, 0.995)):
        out.append((f"BAND_{int(lo * 100)}_{int(hi * 1000)}", (lo, hi)))
    return out


def rows_for(data, rule, left, band, cut):
    out = []
    for s, mk in data.items():
        base = I.entries(mk, left, lambda m, c, e, ps: L.favorite(c["bid"], c["ask"], L.L1["band"]))
        b = {}
        for part in (True, False):
            sel = [r for r in base if (r["day"] < cut) == part]
            b[part] = (st.mean(r["net"] for r in sel), st.mean(r["stress"] for r in sel)) if sel else (0.0, 0.0)
        for r in I.entries(mk, left, lambda m, c, e, ps: rule(m, c, e, band)):
            adj = b[r["day"] < cut]
            out.append({**r, "raw": r["net"], "net": r["net"] - adj[0], "stress": r["stress"] - adj[1], "series": s})
    return out


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = {}
    for m in load() + load_fresh():
        if m[1] in SERIES and m[4] in ("yes", "no") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = m
    data = {s: {tk: as_market(m) for tk, m in mk.items() if m[1] == s} for s in SERIES}
    all_days = sorted({datetime.fromtimestamp(m["close"], timezone.utc).strftime("%Y-%m-%d") for d in data.values() for m in d.values()})
    cut = all_days[int(len(all_days) * 2 / 3)]
    out = [f"COMM1: {sum(len(d) for d in data.values())} markets in {len(SERIES)} series, discovery before {cut}"]
    plain = [r for r in rules() if r[1] is not None]
    for ename, left in ENTRIES.items():
        todo = [(n, fn, L.L1["band"]) for n, fn in plain] + [(n, (lambda m, c, e, band: L.favorite(c["bid"], c["ask"], band)), b) for n, b in band_rules()]
        for name, fn, band in todo:
            rows = rows_for(data, fn, left, band, cut)
            j = I.judge(rows, cut, [{**r, "net": r["raw"]} for r in rows], MIN_DISC, MIN_CONF, DISC_Z)
            out.append(f"{ename:5s} {name:18s} {j['verdict']:18s} disc n={j['nd']:5d} {100 * j['dm']:+6.2f}c z {j['dz']:+5.2f} | conf n={j['nc']:5d} {100 * j['cm']:+6.2f}c z {j['cz']:+5.2f} | all {100 * j['am']:+6.2f}c z {j['az']:+5.2f} PF {j['pf']:.2f}")
    RESULT.write_text("\n".join(out) + "\n")
    print(out[0], "\n", sum(1 for x in out if "NOT_YET_FALSIFIED" in x), "NOT_YET_FALSIFIED;", sum(1 for x in out if " FALSIFIED " in x), "FALSIFIED;", sum(1 for x in out if "NOT_ENOUGH_DATA" in x), "NOT_ENOUGH_DATA")


if __name__ == "__main__":
    main(sys.argv)
