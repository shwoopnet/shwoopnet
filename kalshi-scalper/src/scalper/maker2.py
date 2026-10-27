"""MAKER2 (README, Pre-registration: MAKER2): enter the L1 favourite with a resting bid instead of crossing the spread. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.maker2 run   (once; a second run is refused)
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone

from .calibration import cluster_mean_z
from .paths import DATA_DIR

RESULT = DATA_DIR / "maker2_result.txt"
SOURCES = ["book", "l1b", "fresh", "alts2", "alts3", "alts4", "e3b"]
LEFT_S, LO, HI, WAIT_S = 360, 0.88, 0.97, 180
BAR_C, BAR_Z = 0.005, 2.0


def fee(p: float) -> float:
    return 0.07 * p * (1 - p)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    seen, take, rest, opp = set(), [], [], []
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
            n_take = won - ask - fee(ask)
            take.append((day, n_take)); opp.append(day)
            # REST fill: within the next WAIT_S, the side's ask low reaches our bid (yes) / 1 - bid high reaches our bid (no)
            filled = False
            for k in range(t + 60, t + WAIT_S + 1, 60):
                x = cs.get(k)
                if x is None:
                    continue
                low_ask = x[3] if side == "yes" else (None if x[4] is None else round(1 - x[4], 4))
                if low_ask is not None and low_ask <= bid + 1e-9:
                    filled = True; break
            if filled:
                rest.append((day, won - bid - fee(bid), n_take))
    if not rest:
        RESULT.write_text("MAKER2 NOT_ENOUGH_DATA: no fills\n"); print("no fills"); return
    days = sorted({d for d, _ in take}); cut = days[len(days) // 2]
    m_t, _, z_t = cluster_mean_z(take)
    m_r, _, _ = cluster_mean_z([(d, a) for d, a, _ in rest])
    diff = cluster_mean_z([(d, a - b) for d, a, b in rest])
    per_opp_rest = sum(a for _, a, _ in rest) / len(take)
    h1 = [a - b for d, a, b in rest if d < cut]; h2 = [a - b for d, a, b in rest if d >= cut]
    ok = diff[0] >= BAR_C and diff[2] >= BAR_Z and per_opp_rest > m_t and sum(h1) > 0 and sum(h2) > 0
    verdict = "NOT_YET_FALSIFIED" if ok else "FALSIFIED"
    lines = [f"MAKER2 {verdict}: {len(take)} L1 opportunities over {len(days)} days; TAKE net per contract {100 * m_t:+.2f}c; REST filled {len(rest)} ({100 * len(rest) / len(take):.1f}%), "
             f"REST net per filled {100 * m_r:+.2f}c; on the same filled entries TAKE would earn {100 * sum(b for _, _, b in rest) / len(rest):+.2f}c, difference {100 * diff[0]:+.2f}c (z {diff[2]:+.2f}); "
             f"REST per opportunity {100 * per_opp_rest:+.3f}c vs TAKE {100 * m_t:+.3f}c; halves of the difference {100 * sum(h1) / max(len(h1), 1):+.2f}/{100 * sum(h2) / max(len(h2), 1):+.2f}c"]
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
