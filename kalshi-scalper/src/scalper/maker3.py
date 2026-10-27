"""MAKER3 (README, Pre-registration: MAKER3): hybrid L1 entry: rest a bid, cross after W seconds if not filled. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.maker3 run   (once; a second run is refused)
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone

from .calibration import cluster_mean_z
from .paths import DATA_DIR

RESULT = DATA_DIR / "maker3_result.txt"
SOURCES = ["book", "l1b", "fresh", "alts2", "alts3", "alts4", "e3b"]
LEFT_S, LO, HI = 360, 0.88, 0.97
BAR_C, BAR_Z = 0.003, 2.0


def fee(p: float) -> float:
    return 0.07 * p * (1 - p)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    seen, rows = set(), []
    for name in SOURCES:
        try:
            db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
            ms = db.execute("select ticker, series, close_ts, result from market where series like '%15M'").fetchall()
        except sqlite3.OperationalError:
            continue
        for tk, series, close_ts, res in ms:
            if tk in seen or res not in ("yes", "no"):
                continue
            seen.add(tk)
            cs = {r[0]: r for r in db.execute("select end_ts, bid_c, ask_c, ask_l, bid_h from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            t = close_ts - LEFT_S
            c = cs.get(t)
            if c is None:
                continue
            yes_ask, no_ask = c[2], round(1 - c[1], 4)
            if LO <= yes_ask <= HI and yes_ask >= no_ask:
                side, ask, bid = "yes", yes_ask, c[1]
            elif LO <= no_ask <= HI:
                side, ask, bid = "no", no_ask, round(1 - c[2], 4)
            else:
                continue
            won = 1.0 if res == side else 0.0
            day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
            base = won - ask - fee(ask)
            out = {}
            for W in (60, 120):
                filled = False
                for k in range(t + 60, t + W + 1, 60):
                    x = cs.get(k)
                    if x is None:
                        continue
                    low_ask = x[3] if side == "yes" else (None if x[4] is None else round(1 - x[4], 4))
                    if low_ask is not None and low_ask <= bid + 1e-9:
                        filled = True; break
                if filled:
                    out[W] = won - bid - fee(bid)
                else:
                    x = cs.get(t + W)
                    if x is None:
                        out[W] = 0.0; continue
                    a2 = x[2] if side == "yes" else round(1 - x[1], 4)
                    out[W] = (won - a2 - fee(a2)) if LO <= a2 <= HI else 0.0
            rows.append((day, base, out[60], out[120]))
    days = sorted({r[0] for r in rows}); cut = days[len(days) // 2]
    lines = [f"MAKER3: {len(rows)} L1 opportunities, {len(days)} days; TAKE net per opportunity {100 * sum(r[1] for r in rows) / len(rows):+.3f}c"]
    passed = False
    for j, W in ((2, 60), (3, 120)):
        d = cluster_mean_z([(r[0], r[j] - r[1]) for r in rows])
        h1 = [r[j] - r[1] for r in rows if r[0] < cut]; h2 = [r[j] - r[1] for r in rows if r[0] >= cut]
        ok = d[0] >= BAR_C and d[2] >= BAR_Z and sum(h1) > 0 and sum(h2) > 0
        passed = passed or ok
        lines.append(f"W={W}s: hybrid net per opportunity {100 * sum(r[j] for r in rows) / len(rows):+.3f}c, difference vs TAKE {100 * d[0]:+.3f}c (z {d[2]:+.2f}), halves {100 * sum(h1) / len(h1):+.3f}/{100 * sum(h2) / len(h2):+.3f}c {'PASS' if ok else ''}")
    lines.insert(0, f"MAKER3 {'NOT_YET_FALSIFIED' if passed else 'FALSIFIED'}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
