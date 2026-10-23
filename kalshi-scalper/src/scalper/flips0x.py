"""FLIPS0-X (README, Pre-registration: FLIPS0-X): the IDEAS100 rule FLIPS_0 at the 6 minute entry (a smooth, direction-flip-free climb into the favourite), scored ONCE on the sixteen non-Bitcoin
non-Ethereum 15 minute series, which the rule was never selected on. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.flips0x run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys

from . import ideas100 as D
from . import ideas20 as I
from . import lstrats as L
from .calibration import cluster_mean_z
from .paths import DATA_DIR

# ---- fixed in the README before the other series were scored ----
SERIES = ("KXXRP15M", "KXDOGE15M", "KXGOLD15M", "KXBNB15M", "KXHYPE15M", "KXNEAR15M", "KXZEC15M", "KXSILVER15M", "KXPLATINUM15M", "KXPALLADIUM15M", "KXCOPPER15M",
          "KXWTI15M", "KXNATGAS15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M")
BIG = ("KXXRP15M", "KXDOGE15M", "KXGOLD15M", "KXBNB15M", "KXHYPE15M")        # series with enough entries for a per-series sign
MEAN_C, Z_BAR, PF_BAR, MIN_N, MIN_BIG_POS, FALSIFY_C, FALSIFY_Z = 0.010, 2.5, 1.3, 300, 3, 0.003, 1.0
RESULT = DATA_DIR / "flips0x_result.txt"


def series_rows(s: str, mk: dict) -> list[dict]:
    """FLIPS_0 entries of one series at the 6 minute entry, net and stress minus the series' own mean of all entries of that entry; `raw` is the unadjusted net."""
    left, band = D.ENTRIES["L1360"]
    rule = dict(D.all_rules())["FLIPS_0"]
    ctx = D.Ctx({s: {m["close"]: m for m in mk.values()}, "x": {}}, s)
    base = I.entries(mk, left, lambda m, c, e, ps: L.favorite(c["bid"], c["ask"], band))
    if not base:
        return []
    bn, bs = st.mean(r["net"] for r in base), st.mean(r["stress"] for r in base)
    return [{**r, "raw": r["net"], "net": r["net"] - bn, "stress": r["stress"] - bs, "series": s}
            for r in I.entries(mk, left, lambda m, c, e, ps: rule(ctx, m, c, e, band, left))]


def judge(rows: list[dict]) -> dict:
    if len(rows) < MIN_N:
        return {"verdict": "NOT_ENOUGH_DATA", "n": len(rows)}
    m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    ds = sorted({r["day"] for r in rows})
    mid = ds[len(ds) // 2]
    h = [st.mean(r["net"] for r in rows if (r["day"] < mid) == first) for first in (True, False)]
    ms = st.mean(r["stress"] for r in rows)
    w = sum(r["raw"] for r in rows if r["raw"] > 0)
    l = -sum(r["raw"] for r in rows if r["raw"] < 0)
    pf = w / l if l else float("inf")
    pos = sum(1 for s in BIG if (v := [r["net"] for r in rows if r["series"] == s]) and st.mean(v) > 0)
    ok = m >= MEAN_C and z >= Z_BAR and h[0] > 0 and h[1] > 0 and ms > 0 and pf >= PF_BAR and pos >= MIN_BIG_POS
    v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    return {"verdict": v, "n": len(rows), "mean": m, "z": z, "h1": h[0], "h2": h[1], "stress": ms, "pf": pf, "pos": pos, "raw": st.mean(r["raw"] for r in rows)}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    rows = []
    per = []
    for s in SERIES:
        mk = I.load_btc(s)
        r = series_rows(s, mk) if mk else []
        rows += r
        per.append(f"{s[2:-3]} ({len(r)}, {100 * st.mean(x['net'] for x in r):+.2f})" if r else f"{s[2:-3]} (0)")
    j = judge(rows)
    out = [f"FLIPS0-X: {j['verdict']}; n={j['n']}"]
    if "mean" in j:
        out.append(f"adjusted mean {100 * j['mean']:+.2f}c z {j['z']:+.2f}; raw mean {100 * j['raw']:+.2f}c; halves {100 * j['h1']:+.2f}c / {100 * j['h2']:+.2f}c; stress {100 * j['stress']:+.2f}c; raw PF {j['pf']:.2f}; big series above own baseline {j['pos']} of {len(BIG)}")
    out.append("by series (entries, adjusted c): " + ", ".join(per))
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
