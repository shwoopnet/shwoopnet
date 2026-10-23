"""FLIPS0-X (README, Pre-registration: FLIPS0-X): the IDEAS100 rule FLIPS_0 at the 6 minute entry (a smooth, direction-flip-free climb into the favourite), scored ONCE on the sixteen non-Bitcoin
non-Ethereum 15 minute series, which the rule was never selected on. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.flips0x run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
import time
from datetime import datetime, timezone

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
FWD_RESULT = DATA_DIR / "flips0f_result.txt"
FWD_SERIES = ("KXBTC15M", "KXETH15M") + SERIES
FWD_START = int(datetime(2026, 10, 24, tzinfo=timezone.utc).timestamp())
FWD_READ_DATE = int(datetime(2026, 11, 12, tzinfo=timezone.utc).timestamp())
FWD_MIN_N, FWD_C, FWD_Z, FWD_PF = 150, 0.010, 2.0, 1.3


def flip_count(mids: list[float]) -> int:
    """Direction flips of a favourite-side mid path: minute changes of 0.004 or less are ignored, then the sign changes between consecutive remaining changes are counted. Same rule as the FLIPS_0 bucket."""
    ch = [b - a for a, b in zip(mids, mids[1:])]
    mv = [x for x in ch if abs(x) > 0.004]
    return sum(1 for a, b in zip(mv, mv[1:]) if (a > 0) != (b > 0))


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


def forward(now: float | None = None) -> str:
    """FLIPS0-F: FLIPS_0 at the 6 minute entry on Bitcoin, Ethereum and the sixteen other series, markets closing from 2026-10-24 only, each scored against its own series' L1 baseline of that period. Read once, on or after 2026-11-12."""
    if (now if now is not None else time.time()) < FWD_READ_DATE:
        return "Refusing the registered read: before 2026-11-12."
    if FWD_RESULT.exists():
        return f"Refusing to run again: {FWD_RESULT} exists."
    I.SOURCES = ("fresh",)
    rows = []
    for s in FWD_SERIES:
        mk = {tk: m for tk, m in I.load_btc(s).items() if m["close"] >= FWD_START}
        if mk:
            rows += series_rows(s, mk)
    if len(rows) < FWD_MIN_N:
        out = f"FLIPS0-F: NOT_ENOUGH_DATA (n={len(rows)}, need {FWD_MIN_N})"
    else:
        m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
        ds = sorted({r["day"] for r in rows})
        mid = ds[len(ds) // 2]
        h = [st.mean(r["net"] for r in rows if (r["day"] < mid) == first) for first in (True, False)]
        w = sum(r["raw"] for r in rows if r["raw"] > 0)
        l = -sum(r["raw"] for r in rows if r["raw"] < 0)
        pf = w / l if l else float("inf")
        ok = m >= FWD_C and z >= FWD_Z and h[0] > 0 and h[1] > 0 and pf >= FWD_PF
        v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < 0.003 or z < 1.0) else "NOT_ENOUGH_DATA")
        btc_eth = [r for r in rows if r["series"] in ("KXBTC15M", "KXETH15M")]
        out = (f"FLIPS0-F: {v}; n={len(rows)} adjusted mean {100 * m:+.2f}c z {z:+.2f} raw PF {pf:.2f} halves {100 * h[0]:+.2f}c / {100 * h[1]:+.2f}c; "
               f"Bitcoin and Ethereum alone n={len(btc_eth)} adjusted {100 * st.mean(r['net'] for r in btc_eth):+.2f}c" if btc_eth else f"FLIPS0-F: {v}; n={len(rows)} adjusted mean {100 * m:+.2f}c z {z:+.2f}")
    # the two better-defined smoothness variants found by SMOOTH20 (registered before the read): same data, adjusted the same way, bars as the FLIPS0-F claim with n >= 300
    from . import smooth20 as S
    left, band = D.ENTRIES["L1360"]
    lines = [out]
    for name in ("MAXPULL_LE_010", "EFF_LE_11"):
        rule = dict(S.rules())[name]
        vr = []
        for s_ in FWD_SERIES:
            mk = {tk: m for tk, m in I.load_btc(s_).items() if m["close"] >= FWD_START}
            if mk:
                vr += S.entries_for(mk, s_, rule, left, band)
        if len(vr) < 300:
            lines.append(f"{name}-F: NOT_ENOUGH_DATA (n={len(vr)}, need 300)")
            continue
        m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in vr])
        ds = sorted({r["day"] for r in vr})
        mid = ds[len(ds) // 2]
        h = [st.mean(r["net"] for r in vr if (r["day"] < mid) == first) for first in (True, False)]
        w = sum(r["raw"] for r in vr if r["raw"] > 0)
        l = -sum(r["raw"] for r in vr if r["raw"] < 0)
        pf = w / l if l else float("inf")
        ok = m >= FWD_C and z >= FWD_Z and h[0] > 0 and h[1] > 0 and pf >= FWD_PF
        v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < 0.003 or z < 1.0) else "NOT_ENOUGH_DATA")
        lines.append(f"{name}-F: {v}; n={len(vr)} adjusted mean {100 * m:+.2f}c z {z:+.2f} raw PF {pf:.2f} halves {100 * h[0]:+.2f}c / {100 * h[1]:+.2f}c")
    out = "\n".join(lines)
    FWD_RESULT.write_text(out + "\n")
    return out


def main(argv: list[str]) -> None:
    if len(argv) >= 2 and argv[1] == "forward":
        print(forward())
        return
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
