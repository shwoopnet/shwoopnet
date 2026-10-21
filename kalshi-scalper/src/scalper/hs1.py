"""HS1 (README, Pre-registration: HS1): buy a side at 38c to 52c with at least 5 minutes left; when its bid first reaches 65c, buy half a contract of the other
side; hold both to settlement. Compared with the same entries unhedged. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.hs1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import sqlite3
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timezone

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalps import STRESS, fee

# ---- fixed in the README before the first run ----
BAND, MIN_LEFT_S, TRIGGER_BID, MIN_LEFT_TRIGGER_S, HEDGE = (0.38, 0.52), 300, 0.65, 60, 0.5
MIN_N, MIN_DAYS, Z_BAR, DIFF_Z_BAR = 300, 10, 2.7, 2.0
SOURCES = ["alts2", "alts3", "alts4", "book", "l1b", "e3b"]
RESULT = DATA_DIR / "hs1_result.txt"


def load() -> list[tuple]:
    by: dict = {}
    for name in SOURCES:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        mine: dict = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
        for s, tk, end, bc, ac, bh, al, close_ts, res in db.execute(
                "SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, c.bid_h, c.ask_l, m.close_ts, m.result FROM candle c JOIN market m ON m.ticker = c.ticker ORDER BY c.ticker, c.end_ts"):
            if not s.endswith("15M") or tk in by:
                continue
            m = mine[tk]
            m["c"].append((end, bc, ac)); m["close"] = close_ts; m["res"] = res; m["s"] = s
        by.update(mine)
    return [(tk, m["s"], m["c"], m["close"], m["res"]) for tk, m in by.items()]


def side_quote(c: tuple, side: str):
    """(bid, ask) of the side from a YES candle (end, bid_c, ask_c); NO is the mirror."""
    _, bid, ask = c
    return (bid, ask) if side == "yes" else (1 - ask, 1 - bid)


def simulate(candles: list[tuple], close_ts: int, res: str, mult: float = 1.0):
    """None, or dict with the unhedged and hedged net per contract for one market."""
    if res not in ("yes", "no"):
        return None
    entry = None
    for k, c in enumerate(candles):
        if close_ts - c[0] < MIN_LEFT_S:
            break
        if c[1] is None or c[2] is None or not valid_quote(c[1], c[2]):
            continue
        for side in ("yes", "no"):
            ask = side_quote(c, side)[1]
            if BAND[0] <= ask <= BAND[1]:
                entry = (k, side, ask)
                break
        if entry:
            break
    if not entry:
        return None
    k0, side, p0 = entry
    for c in candles[k0 + 1:]:
        if close_ts - c[0] < MIN_LEFT_TRIGGER_S:
            break
        if c[1] is None or c[2] is None or not valid_quote(c[1], c[2]):
            continue
        bid = side_quote(c, side)[0]
        if bid >= TRIGGER_BID:
            q = 1 - bid                                   # the other side's ask: buy it from the sellers of the other side
            held_wins = (side == "yes") == (res == "yes")
            f0, fq = fee(p0, mult), fee(q, mult)
            unh = (1 - p0 - f0) if held_wins else -(p0 + f0)
            hedge = HEDGE * ((-(q + fq)) if held_wins else (1 - q - fq))
            return {"unh": unh, "hed": unh + hedge, "p0": p0, "q": q}
    return None


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = load()
    rows, entries = [], 0
    for tk, s, c, close_ts, res in mk:
        r = simulate(c, close_ts, res)
        r2 = simulate(c, close_ts, res, STRESS)
        if r is None:
            continue
        r["series"], r["close_ts"] = s, close_ts
        r["day"] = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        r["hed_stress"] = r2["hed"]
        rows.append(r)
    rows.sort(key=lambda r: r["close_ts"])
    n = len(rows)
    days = len({r["day"] for r in rows})
    if n < MIN_N or days < MIN_DAYS:
        out = f"HS1: NOT_ENOUGH_DATA (triggered {n} on {days} days)"
    else:
        mh, _, zh = cluster_mean_z([(r["day"], r["hed"]) for r in rows])
        mu, _, zu = cluster_mean_z([(r["day"], r["unh"]) for r in rows])
        md, _, zd = cluster_mean_z([(r["day"], r["hed"] - r["unh"]) for r in rows])
        h = n // 2
        h1, h2 = st.mean(r["hed"] for r in rows[:h]), st.mean(r["hed"] for r in rows[h:])
        stress = st.mean(r["hed_stress"] for r in rows)
        ok = mh > 0 and zh >= Z_BAR and h1 > 0 and h2 > 0 and stress > 0 and md > 0 and zd >= DIFF_Z_BAR
        v = "NOT_YET_FALSIFIED" if ok else "FALSIFIED"
        c = lambda x: f"{x * 100:+.2f}c"
        out = "\n".join([
            f"HS1 on {len(mk)} markets; triggered {n} ({100 * n / len(mk):.1f}% of markets) on {days} days",
            f"   hedged net {c(mh)} z {zh:+.2f} halves {c(h1)} / {c(h2)} fees x{STRESS} {c(stress)}",
            f"   unhedged net {c(mu)} z {zu:+.2f}; hedged minus unhedged {c(md)} (day clustered z {zd:+.2f})",
            f"   standard deviation of net per entry: hedged {st.pstdev(r['hed'] for r in rows) * 100:.1f}c, unhedged {st.pstdev(r['unh'] for r in rows) * 100:.1f}c",
            f"   held side won {100 * sum(1 for r in rows if r['unh'] > 0) / n:.1f}% of triggered entries; mean entry price {100 * st.mean(r['p0'] for r in rows):.1f}c; mean hedge price {100 * st.mean(r['q'] for r in rows):.1f}c",
            f"   VERDICT: {v}"])
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
