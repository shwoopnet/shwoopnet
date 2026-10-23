"""IDEAS20C (README, Pre-registration: IDEAS20C): the 38 IDEAS20 and IDEAS20B rules that do not depend on Bitcoin's price level, run on XRP, Dogecoin and gold pooled.
Same split, bars and verdict words as IDEAS20 (imported); plus at least 2 of the 3 series must have a positive all-days mean. Research only. Nothing here means trade.
Usage: python -m scalper.ideas20c run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
import time
from datetime import datetime, timezone

from . import ideas20 as I
from . import ideas20b as B
from .calibration import cluster_mean_z
from .paths import DATA_DIR

SERIES = ("KXXRP15M", "KXDOGE15M", "KXGOLD15M")
SKIP = {"ROUND", "ROUND500"}          # strike multiples of 1,000 or 500 only mean something at Bitcoin's price level
MIN_SERIES_POS = 2
RESULT = DATA_DIR / "ideas20c_result.txt"


def all_rules(mk: dict) -> list[tuple[str, int, object]]:
    return [r for r in list(I.RULES) + B.rules(mk) if r[0] not in SKIP]


FAV_RULES = {"SURGE_FOLLOW", "SURGE_FADE", "MOM_FOLLOW", "MOM_FADE"}      # not L1 favourite entries: scored raw, every other rule is scored against the series' own L1 baseline


def pooled(mks: dict[str, dict], name: str, cut: str | None = None):
    """Entries of rule `name` over every series (each series' own context), tagged with the series. For L1-favourite rules `net` and `stress` are the entry's value minus the mean of ALL
    360 s L1 entries of the same series in the same period (discovery or confirmation), because these three series already earn about +1.5c with no rule; `raw` keeps the unadjusted net."""
    rows = []
    for s, mk in mks.items():
        base = I.entries(mk, 360, lambda m, c, e, ps: I.fav(c))
        b = {}
        for part in (True, False):
            sel = [r for r in base if cut is not None and (r["day"] < cut) == part]
            b[part] = (st.mean(r["net"] for r in sel), st.mean(r["stress"] for r in sel)) if sel else (0.0, 0.0)
        for n, left, fn in all_rules(mk):
            if n == name:
                for r in I.entries(mk, left, fn):
                    adj = (0.0, 0.0) if (name in FAV_RULES or cut is None) else b[r["day"] < cut]
                    rows.append({**r, "series": s, "raw": r["net"], "net": r["net"] - adj[0], "stress": r["stress"] - adj[1]})
    return rows


FWD_RESULT = DATA_DIR / "absorb_f_result.txt"
FWD_START = int(datetime(2026, 10, 24, tzinfo=timezone.utc).timestamp())
FWD_READ_DATE = int(datetime(2026, 12, 1, tzinfo=timezone.utc).timestamp())
FWD_MIN_N, FWD_C, FWD_Z, FWD_PF = 200, 0.010, 2.0, 1.3


def absorb_forward(now: float | None = None) -> str:
    """ABSORB-F: ABSORB (previous-minute volume >= 1.5x the one before while the mid moved under 3c, buy the L1 favourite) on XRP, Dogecoin and gold markets closing from
    2026-10-24 only, scored against the same series' L1 baseline of that period. Read on or after 2026-12-01, once."""
    if (now if now is not None else time.time()) < FWD_READ_DATE:
        return "Refusing the registered read: before 2026-12-01."
    if FWD_RESULT.exists():
        return f"Refusing to run again: {FWD_RESULT} exists."
    I.SOURCES = ("fresh",)
    mks = {s: {tk: m for tk, m in I.load_btc(s).items() if m["close"] >= FWD_START} for s in SERIES}
    rows = pooled(mks, "ABSORB", "9999-12-31")
    if len(rows) < FWD_MIN_N:
        out = f"ABSORB-F: NOT_ENOUGH_DATA (n={len(rows)}, need {FWD_MIN_N})"
    else:
        m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
        raw = I.pf([{**r, "net": r["raw"]} for r in rows])
        ds = sorted({r["day"] for r in rows})
        mid = ds[len(ds) // 2]
        h = [st.mean(r["net"] for r in rows if (r["day"] < mid) == first) for first in (True, False)]
        pos = sum(1 for s in SERIES if (v := [r["net"] for r in rows if r["series"] == s]) and st.mean(v) > 0)
        ok = m >= FWD_C and z >= FWD_Z and raw >= FWD_PF and h[0] > 0 and h[1] > 0 and pos >= MIN_SERIES_POS
        v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < 0.003 or z < 1.0) else "NOT_ENOUGH_DATA")
        out = f"ABSORB-F: {v}; n={len(rows)} adjusted mean {100 * m:+.2f}c z {z:+.2f} raw PF {raw:.2f} halves {100 * h[0]:+.2f}c / {100 * h[1]:+.2f}c series positive {pos} of 3"
    FWD_RESULT.write_text(out + "\n")
    return out


def main(argv: list[str]) -> None:
    if len(argv) >= 2 and argv[1] == "absorb_forward":
        print(absorb_forward())
        return
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mks = {s: I.load_btc(s) for s in SERIES}
    names = [r[0] for r in all_rules(next(iter(mks.values())))]
    cut = I.cut_day({tk: m for mk in mks.values() for tk, m in mk.items()})
    out = [f"IDEAS20C: {sum(len(m) for m in mks.values())} markets ({', '.join(f'{s[2:-3]} {len(m)}' for s, m in mks.items())}), discovery before {cut}"]
    for name in names:
        rows = pooled(mks, name, cut)
        j = I.judge(rows, cut, [{**r, "net": r["raw"]} for r in rows])
        pos = sum(1 for s in SERIES if (r := [x["net"] for x in rows if x["series"] == s]) and st.mean(r) > 0)
        if j["verdict"] == "NOT_YET_FALSIFIED" and pos < MIN_SERIES_POS:
            j["verdict"] = "NOT_ENOUGH_DATA"
        out.append(f"{name:15s} {j['verdict']:18s} disc n={j['nd']:5d} {100 * j['dm']:+6.2f}c z {j['dz']:+5.2f} | conf n={j['nc']:5d} {100 * j['cm']:+6.2f}c z {j['cz']:+5.2f} | all {100 * j['am']:+6.2f}c z {j['az']:+5.2f} PF {j['pf']:.2f} series+ {pos}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
