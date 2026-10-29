"""GOLDSLIP: gold slippage and fill rate by order size, nightly inside `drift run` (owner, via the main session, 2026-10-29). Information only.
The owner plans a second deposit after about two weeks only if gold slippage at size stays at or under 1.0c, so this table is the input.
Usage: python -m scalper.goldslip run   (aggregates to workers/GOLDSLIP.md; raw rows stay in the scratchpad)
"""
from __future__ import annotations

import statistics as st
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from . import livewatch as LW
from .drift import close_from_ticker, live_report, load_markets, side_ask
from .paths import DATA_DIR

SERIES = "KXGOLD15M"
BUCKETS = [(1, 10), (11, 15), (16, 20), (21, 30), (31, 10_000)]
DEPOSIT_MARK = datetime(2026, 10, 29, 23, 0, tzinfo=timezone.utc).timestamp()   # the owner's first $250 deposit, "now" on Oct 29 evening
OUT = DATA_DIR.parent / "workers" / "GOLDSLIP.md"
CT = ZoneInfo("America/Chicago")
# RISK1's $528 90 day median at three gold slippage levels (workers/RISK1_RESULT.md), for a linear read at the measured value
RISK1_MEDIAN_90 = [(0.60, 330.0), (1.5, 120.0), (2.5, -58.0)]


def risk1_at(slip_c):
    pts = RISK1_MEDIAN_90
    if slip_c <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if slip_c <= x1:
            return y0 + (y1 - y0) * (slip_c - x0) / (x1 - x0)
    return pts[-1][1]


def q90(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(0.9 * len(xs)))] if xs else None


def run():
    d = live_report()
    since = datetime.fromisoformat(d["sinceUtc"].replace("Z", "+00:00"))
    M = load_markets(int(since.timestamp()) - 3600)
    rows = []
    for o in d.get("orders", []):
        if not (o.get("ticker") or "").startswith(SERIES + "-"):
            continue
        close = close_from_ticker(o["ticker"])
        if close is None:
            continue
        t = datetime.fromisoformat(o["ts"].replace("Z", "+00:00")).timestamp()
        lead = o.get("entryLead") or ("10m" if close - t > 480 else "6m")
        left = 600 if lead == "10m" else 360
        filled = (o.get("count") or 0) > 0 and o.get("status") == "filled"
        m = M.get(o["ticker"]); c = m["c"].get(close - left) if m else None
        ask = side_ask(c[0], c[1], o["side"]) if c else None
        p = LW.price_paid(o) if filled else None
        slip = round(100 * (p - ask), 2) if p is not None and ask is not None else None
        rows.append(dict(t=t, count=o.get("count") or 0, filled=filled, slip=slip, after=t >= DEPOSIT_MARK))
    lines = [f"## {datetime.now(CT):%Y-%m-%d %H:%M} CT (gold held orders; deposit marker 2026-10-29 23:00 UTC)", "",
             "| Period | Contracts per order | Attempts | No fill | Priced | Mean slippage | 90th pct |", "|---|---|---|---|---|---|---|"]
    flags = []
    for per, grp in (("before deposit", [r for r in rows if not r["after"]]), ("after deposit", [r for r in rows if r["after"]]), ("all", rows)):
        for lo, hi in BUCKETS:
            # an attempt with no fill carries count 0, so it is bucketed by the size of the neighbouring filled orders: report it per period only
            b = [r for r in grp if r["filled"] and lo <= r["count"] <= hi]
            sl = [r["slip"] for r in b if r["slip"] is not None]
            label = f"{lo} to {hi}" if hi < 10_000 else f"{lo} and up"
            lines.append(f"| {per} | {label} | {len(b)} | n/a | {len(sl)} | {('%+.2fc' % st.mean(sl)) if sl else 'n/a'} | {('%+.1fc' % q90(sl)) if sl else 'n/a'} |")
            if per == "all":
                if lo >= 16 and len(sl) >= 20 and st.mean(sl) >= 1.0:
                    flags.append(f"gold slippage {st.mean(sl):+.2f}c at {label} contracts over {len(sl)} orders (flag at 1.0c for 16+)")
                if (lo, hi) == (21, 30) and len(sl) >= 20 and st.mean(sl) >= 1.5:
                    flags.append(f"gold slippage {st.mean(sl):+.2f}c at 21 to 30 contracts over {len(sl)} orders (flag at 1.5c)")
        nf = sum(1 for r in grp if not r["filled"])
        lines.append(f"| {per} | all sizes, no-fill share | {len(grp)} | {nf} ({100 * nf / max(1, len(grp)):.0f}%) | | | |")
    big = [r["slip"] for r in rows if r["filled"] and r["count"] >= 16 and r["slip"] is not None]
    if len(big) >= 20:
        lines.append(f"\nRISK1 at the measured 16+ contract slippage ({st.mean(big):+.2f}c, {len(big)} orders): $528 90 day median about ${risk1_at(st.mean(big)):+.0f} (linear between RISK1's runs at +0.60c, +1.5c, +2.5c; a re-run is better once the number is stable)")
    else:
        lines.append(f"\nRISK1 at measured slippage: not yet (16+ contract gold orders priced: {len(big)}, need 20)")
    lines.append("\nTouch depth: the report carries no depthAtLimit or shareOfDepth; from recorder R6's gold book once it has rows (not wired yet).")
    lines.append(f"\n**Flags:** {'; '.join(flags) if flags else 'none'}\n")
    old = OUT.read_text() if OUT.exists() else "# GOLDSLIP: gold slippage and fill rate by order size (newest first; aggregates only; information)\n\n"
    head, _, rest = old.partition("\n\n")
    OUT.write_text(head + "\n\n" + "\n".join(lines) + "\n" + rest)
    print("\n".join(lines))
    return flags


if __name__ == "__main__":
    {"run": run}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
