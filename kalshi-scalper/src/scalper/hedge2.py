"""HL1 and SL1 (README, Pre-registration: HL1, SL1, an interim look at ML1, and SIZE1): hedge the L1 favourite with 0.10 of a contract of the other side, and a
scale-out ladder on 38c to 52c entries. Every entry counts. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.hedge2 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .hs1 import BAND, MIN_LEFT_S, MIN_LEFT_TRIGGER_S, load, side_quote
from .lstrats import L1, favorite
from .paths import DATA_DIR
from .scalps import STRESS, fee

# ---- fixed in the README before the first run ----
HEDGE_L1, LADDER_LOW, LADDER_HIGH = 0.10, 0.60, 0.80
MIN_N, MIN_DAYS, Z_BAR, DIFF_Z_BAR = 300, 10, 2.8, 2.0
RESULT = DATA_DIR / "hedge2_result.txt"


def hl1(candles, close_ts, res, mult=1.0):
    """L1's entry with 0.10 of a contract of the other side bought at the same candle. None if L1 has no entry."""
    if res not in ("yes", "no"):
        return None
    c = next((x for x in candles if x[0] == close_ts - L1["left_s"]), None)
    if c is None or c[1] is None or c[2] is None:
        return None
    pick = favorite(c[1], c[2], L1["band"])
    if pick is None:
        return None
    side, p = pick
    won = (side == "yes") == (res == "yes")
    plain = (1 - p - fee(p, mult)) if won else -(p + fee(p, mult))
    other = "no" if side == "yes" else "yes"
    q = side_quote(c, other)[1]
    q_wins = not won
    hedge = HEDGE_L1 * (((1.0 if q_wins else 0.0)) - q - fee(q, mult))
    return {"plain": plain, "hedged": plain + hedge, "p": p, "q": q}


def entry_of(candles, close_ts):
    for k, c in enumerate(candles):
        if close_ts - c[0] < MIN_LEFT_S:
            break
        if c[1] is None or c[2] is None or not valid_quote(c[1], c[2]):
            continue
        for side in ("yes", "no"):
            ask = side_quote(c, side)[1]
            if BAND[0] <= ask <= BAND[1]:
                return k, side, ask
    return None


def sl1(candles, close_ts, res, mult=1.0):
    """The ladder: a third sold at the first close with bid >= 0.60, a third at the first close with bid >= 0.80, the last third held. Every entry counts."""
    if res not in ("yes", "no"):
        return None
    e = entry_of(candles, close_ts)
    if e is None:
        return None
    k0, side, p0 = e
    won = (side == "yes") == (res == "yes")
    f0 = fee(p0, mult)
    hold = (1 - p0 - f0) if won else -(p0 + f0)
    hit_low = hit_high = False
    for c in candles[k0 + 1:]:
        if close_ts - c[0] < MIN_LEFT_TRIGGER_S:
            break
        if c[1] is None or c[2] is None or not valid_quote(c[1], c[2]):
            continue
        bid = side_quote(c, side)[0]
        hit_low = hit_low or bid >= LADDER_LOW
        hit_high = hit_high or bid >= LADDER_HIGH
        if hit_high:
            break
    third_low = (LADDER_LOW - p0 - f0 - fee(LADDER_LOW, mult)) if hit_low else hold
    third_high = (LADDER_HIGH - p0 - f0 - fee(LADDER_HIGH, mult)) if hit_high else hold
    return {"plain": hold, "ladder": (third_low + third_high + hold) / 3}


def judge(rows, key, base):
    n, days = len(rows), len({r["day"] for r in rows})
    if n < MIN_N or days < MIN_DAYS:
        return f"NOT_ENOUGH_DATA (n {n}, days {days})", {}
    m, _, z = cluster_mean_z([(r["day"], r[key]) for r in rows])
    mb, _, zb = cluster_mean_z([(r["day"], r[base]) for r in rows])
    d, _, zd = cluster_mean_z([(r["day"], r[key] - r[base]) for r in rows])
    h = n // 2
    h1, h2 = st.mean(r[key] for r in rows[:h]), st.mean(r[key] for r in rows[h:])
    stress = st.mean(r[key + "_s"] for r in rows)
    ok = m > 0 and z >= Z_BAR and h1 > 0 and h2 > 0 and stress > 0 and d > 0 and zd >= DIFF_Z_BAR
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": n, "days": days, "mean": m, "z": z, "plain": mb, "plain_z": zb, "diff": d, "diff_z": zd, "h1": h1, "h2": h2,
                                                       "stress": stress, "sd": st.pstdev(r[key] for r in rows), "sd_plain": st.pstdev(r[base] for r in rows)}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = load()
    h_rows, s_rows = [], []
    for tk, s, c, close_ts, res in mk:
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        a, a2 = hl1(c, close_ts, res), hl1(c, close_ts, res, STRESS)
        if a:
            h_rows.append({"day": day, "close_ts": close_ts, "plain": a["plain"], "hedged": a["hedged"], "hedged_s": a2["hedged"], "q": a["q"]})
        b, b2 = sl1(c, close_ts, res), sl1(c, close_ts, res, STRESS)
        if b:
            s_rows.append({"day": day, "close_ts": close_ts, "plain": b["plain"], "ladder": b["ladder"], "ladder_s": b2["ladder"]})
    h_rows.sort(key=lambda r: r["close_ts"]); s_rows.sort(key=lambda r: r["close_ts"])
    cc = lambda x: f"{x * 100:+.2f}c"
    lines = []
    for name, rows, key in (("HL1", h_rows, "hedged"), ("SL1", s_rows, "ladder")):
        v, s = judge(rows, key, "plain")
        if not s:
            lines.append(f"{name}: {v}")
            continue
        lines += [f"{name} on {s['n']} entries, {s['days']} days",
                  f"   {key} net {cc(s['mean'])} z {s['z']:+.2f} halves {cc(s['h1'])} / {cc(s['h2'])} fees x{STRESS} {cc(s['stress'])}",
                  f"   plain net {cc(s['plain'])} z {s['plain_z']:+.2f}; {key} minus plain {cc(s['diff'])} (day clustered z {s['diff_z']:+.2f})",
                  f"   standard deviation per entry: {key} {s['sd'] * 100:.1f}c, plain {s['sd_plain'] * 100:.1f}c; VERDICT: {v}"]
    out = "\n".join(lines)
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
