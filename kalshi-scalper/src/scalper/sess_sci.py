"""SESS1 and SCI1 (README, Pre-registration: SESS1 and SCI1): L1 when the commodity futures session is closed, and a scale-in at 12, 10 and 8 minutes.
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.sess_sci run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timezone

from . import lstrats as L
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR
from .scalps import STRESS, fee

# ---- fixed in the README before the first run ----
COMMODITY = {"KXWTI15M", "KXNATGAS15M", "KXCOPPER15M", "KXSILVER15M", "KXPLATINUM15M", "KXPALLADIUM15M", "KXGOLD15M"}
SCALE_TIMES, THIRD = (720, 600, 480), 1.0 / 3
SESS_Z, SESS_MIN_CLOSED, SCI_Z, SCI_DIFF_Z, SCI_MIN_N, MIN_DAYS = 2.4, 300, 2.8, 2.0, 1000, 10
RESULT = DATA_DIR / "sess_sci_result.txt"


def closed(ts: int) -> bool:
    d = datetime.fromtimestamp(ts, timezone.utc)
    wd, h = d.weekday(), d.hour + d.minute / 60
    if wd == 5 or (wd == 4 and h >= 21) or (wd == 6 and h < 22):
        return True
    return 21 <= h < 22


def day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def scale_in(candles: list[tuple], close_ts: int, res: str, mult: float = 1.0):
    """Per contract net of buying a third at each of SCALE_TIMES while the favourite on the first qualifying side stays in band, held to settlement. None if no buy."""
    if res not in ("yes", "no"):
        return None
    side, buys = None, []
    for left in SCALE_TIMES:
        c = next((x for x in candles if x[0] == close_ts - left), None)
        if c is None or c[1] is None or c[2] is None:
            continue
        pick = L.favorite(c[1], c[2], L.L1["band"])
        if pick is None:
            continue
        if side is None:
            side = pick[0]
        if pick[0] == side:
            buys.append(pick[1])
    if not buys:
        return None
    won = (side == "yes") == (res == "yes")
    total = sum((1.0 if won else 0.0) - p - fee(p, mult) for p in buys) * THIRD
    return total / (len(buys) * THIRD), len(buys)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    lines = []
    # ---- SESS1
    es = L.hold_rule([m for m in full if m[1] in COMMODITY], L.L1["left_s"], L.L1["band"])
    cl = [e for e in es if closed(e["close_ts"] - L.L1["left_s"])]
    op = [e for e in es if not closed(e["close_ts"] - L.L1["left_s"])]
    cdays = len({e["day"] for e in cl})
    cm, _, cz = cluster_mean_z([(e["day"], e["net"]) for e in cl])
    om, _, _ = cluster_mean_z([(e["day"], e["net"]) for e in op])
    byday = defaultdict(lambda: [[], []])
    for e in cl:
        byday[e["day"]][0].append(e["net"])
    for e in op:
        byday[e["day"]][1].append(e["net"])
    dd = [(d, st.mean(v[0]) - st.mean(v[1])) for d, v in byday.items() if v[0] and v[1]]
    dm, _, dz = cluster_mean_z(dd) if len(dd) > 1 else (0.0, 0.0, 0.0)
    if len(cl) < SESS_MIN_CLOSED or cdays < MIN_DAYS:
        v1 = "NOT_ENOUGH_DATA"
    else:
        v1 = "NOT_YET_FALSIFIED" if (abs(dz) >= SESS_Z and cm > 0 and cz >= 2.0) else "FALSIFIED"
    c = lambda x: f"{x * 100:+.2f}c"
    lines += [f"SESS1: closed {len(cl)} entries on {cdays} days, net {c(cm)} (z {cz:+.2f}); open {len(op)} entries, net {c(om)}; closed minus open per day {c(dm)} (day clustered z {dz:+.2f}, {len(dd)} days both); VERDICT: {v1}"]
    per = defaultdict(lambda: [[], []])
    for e in es:
        per[e["series"]][0 if closed(e["close_ts"] - L.L1["left_s"]) else 1].append(e["net"])
    for s in sorted(per):
        a, b = per[s]
        lines.append(f"   {s}: closed n {len(a)} at {c(st.mean(a)) if a else 'n/a'}; open n {len(b)} at {c(st.mean(b))}")
    # ---- SCI1
    rows, base = [], L.hold_rule(full, L.L1["left_s"], L.L1["band"])
    for tk, s, cs, close_ts, res in full:
        r, r2 = scale_in(cs, close_ts, res), scale_in(cs, close_ts, res, STRESS)
        if r:
            rows.append({"day": day(close_ts), "close_ts": close_ts, "net": r[0], "stress": r2[0], "n": r[1], "series": s})
    rows.sort(key=lambda r: r["close_ts"])
    n = len(rows)
    m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    h = n // 2
    h1, h2 = st.mean(r["net"] for r in rows[:h]), st.mean(r["net"] for r in rows[h:])
    stress = st.mean(r["stress"] for r in rows)
    bd = defaultdict(lambda: [[], []])
    for r in rows:
        bd[r["day"]][0].append(r["net"])
    for e in base:
        bd[e["day"]][1].append(e["net"])
    dd2 = [(d, st.mean(v[0]) - st.mean(v[1])) for d, v in bd.items() if v[0] and v[1]]
    m2, _, z2 = cluster_mean_z(dd2)
    mb, _, zb = cluster_mean_z([(e["day"], e["net"]) for e in base])
    ok = n >= SCI_MIN_N and len({r["day"] for r in rows}) >= MIN_DAYS and m > 0 and z >= SCI_Z and h1 > 0 and h2 > 0 and stress > 0 and m2 > 0 and z2 >= SCI_DIFF_Z
    v2 = "NOT_YET_FALSIFIED" if ok else "FALSIFIED"
    legs = [sum(1 for r in rows if r["n"] == k) for k in (1, 2, 3)]
    lines += [f"SCI1: {n} markets with a buy; thirds bought 1/2/3: {legs[0]}/{legs[1]}/{legs[2]}; net {c(m)} (z {z:+.2f}) halves {c(h1)} / {c(h2)} fees x{STRESS} {c(stress)}",
              f"   plain L1 (6 minutes) {len(base)} entries net {c(mb)} (z {zb:+.2f}); SCI1 minus plain L1 per day {c(m2)} (day clustered z {z2:+.2f}); VERDICT: {v2}"]
    out = "\n".join(lines)
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
