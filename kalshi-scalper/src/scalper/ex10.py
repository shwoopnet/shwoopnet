"""EX10 (README, Pre-registration: EX10): which exit line suits L1 entries made 10 minutes before the close. Walk-forward: choose the line on the first two thirds
of days, judge it on the last third against the live 0.25 line. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.ex10 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys

from . import lstrats as L
from .analyze import valid_quote
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR
from .scalps import fee

# ---- fixed in the README before the first run ----
LINES, LIVE_LINE, ENTRY_S, SLIP, SLIP_ALT = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35), 0.25, 600, 0.02, 0.05
Z_BAR, MIN_HOLDOUT = 2.4, 500
RESULT = DATA_DIR / "ex10_result.txt"


def side_bid(side: str, bid: float, ask: float) -> float:
    return bid if side == "yes" else round(1.0 - ask, 4)


def exit_net(entry: dict, candles: list[tuple], close_ts: int, line: float, slip: float):
    """(net, exited?) when the held side's bid first closes at or below `line` after the entry candle, sold at bid minus slip with the sale fee; else held."""
    t0 = close_ts - ENTRY_S
    for c in candles:
        if c[0] <= t0:
            continue
        if c[1] is None or c[2] is None or not valid_quote(c[1], c[2]):
            continue
        b = side_bid(entry["side"], c[1], c[2])
        if b <= line:
            got = max(0.0, b - slip)
            return got - fee(got) - entry["price"] - fee(entry["price"]), True
    return entry["net"], False


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    idx = {m[0]: m for m in full}
    entries = L.hold_rule(full, ENTRY_S, L.L1["band"])
    days = sorted({e["day"] for e in entries})
    cut = days[(2 * len(days)) // 3]
    for e in entries:
        m = idx[e["ticker"]]
        e["by"] = {}
        for slip in (SLIP, SLIP_ALT):
            for line in LINES:
                e["by"][(line, slip)] = exit_net(e, m[2], m[3], line, slip)
    train = [e for e in entries if e["day"] < cut]
    hold = [e for e in entries if e["day"] >= cut]
    lines = [f"EX10 on {len(entries)} 10 minute entries; train {len(train)} (days before {cut}), holdout {len(hold)}; held to settlement: train {100 * st.mean(e['net'] for e in train):+.2f}c, holdout {100 * st.mean(e['net'] for e in hold):+.2f}c",
             "line   train net  holdout net  holdout exits  worst single exit (holdout)   holdout net at 5c slip"]
    tr_mean = {}
    for line in LINES:
        tm = st.mean(e["by"][(line, SLIP)][0] for e in train)
        hm = st.mean(e["by"][(line, SLIP)][0] for e in hold)
        tr_mean[line] = tm
        ex = [e for e in hold if e["by"][(line, SLIP)][1]]
        worst = min((e["by"][(line, SLIP)][0] for e in ex), default=0.0)
        lines.append(f"{line:4.2f}  {100 * tm:+7.2f}c  {100 * hm:+8.2f}c   {100 * len(ex) / len(hold):5.1f}%       {100 * worst:+8.1f}c                {100 * st.mean(e['by'][(line, SLIP_ALT)][0] for e in hold):+8.2f}c")
    chosen = max(LINES, key=lambda l: tr_mean[l])
    lines.append(f"Chosen on training: {chosen:.2f}")
    if len(hold) < MIN_HOLDOUT:
        verdict = "NOT_ENOUGH_DATA"
    elif chosen == LIVE_LINE:
        verdict = "FALSIFIED"
    else:
        d, _, z = cluster_mean_z([(e["day"], e["by"][(chosen, SLIP)][0] - e["by"][(LIVE_LINE, SLIP)][0]) for e in hold])
        d5 = st.mean(e["by"][(chosen, SLIP_ALT)][0] - e["by"][(LIVE_LINE, SLIP_ALT)][0] for e in hold)
        h = len(hold) // 2
        h1 = st.mean(e["by"][(chosen, SLIP)][0] - e["by"][(LIVE_LINE, SLIP)][0] for e in hold[:h])
        h2 = st.mean(e["by"][(chosen, SLIP)][0] - e["by"][(LIVE_LINE, SLIP)][0] for e in hold[h:])
        lines.append(f"Chosen {chosen:.2f} minus live 0.25 on the holdout: {100 * d:+.2f}c (day clustered z {z:+.2f}); at 5c slip {100 * d5:+.2f}c; halves {100 * h1:+.2f}c / {100 * h2:+.2f}c")
        verdict = "NOT_YET_FALSIFIED" if (d > 0 and z >= Z_BAR and d5 >= 0 and h1 > 0 and h2 > 0) else "FALSIFIED"
    lines.append(f"VERDICT: {verdict}")
    for ser in ("KXBTC15M", "KXXRP15M", "KXNATGAS15M"):
        es = [e for e in hold if e["series"] == ser]
        if es:
            lines.append(f"   {ser} holdout n={len(es)}: " + ", ".join(f"{l:.2f}:{100 * st.mean(e['by'][(l, SLIP)][0] for e in es):+.2f}c" for l in LINES) + f"; held {100 * st.mean(e['net'] for e in es):+.2f}c")
    out = "\n".join(lines)
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
