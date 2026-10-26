"""SC1 (README, Pre-registration: SC1): in-play scalping after a price jump on tennis match-winner markets. Research only: nothing here places an order.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

    python -m scalper.sc1 fetch    (resumable; settled markets of the last 45 days, 1 minute candles for the last 6 hours before each close)
    python -m scalper.sc1 run      (the one read; refused a second time)
"""
from __future__ import annotations

import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from . import api, backfill
from .calibration import cluster_mean_z
from .paths import DATA_DIR

DB = DATA_DIR / "sc1.sqlite"
RESULT = DATA_DIR / "sc1_result.txt"
SERIES = ("KXATPCHALLENGERMATCH", "KXATPMATCH", "KXWTAMATCH", "KXWTACHALLENGERMATCH", "KXITFMATCH", "KXITFWMATCH")
DAYS = 45
WINDOW_S = 6 * 3600
JUMP, MAX_SPREAD, MID_LO, MID_HI, MIN_VOL, QUIET_S = 0.05, 0.03, 0.15, 0.85, 100.0, 600
KS = (2, 5)
MIN_EVENTS, MIN_DAYS, BAR_C, BAR_Z, STRESS = 1000, 30, 0.010, 3.0, 1.2
PAUSE = 0.3


def fee(p: float, mult: float = 1.0) -> float:
    return mult * 0.07 * p * (1 - p)


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(backfill.SCHEMA)
    have = {r[0] for r in db.execute("SELECT ticker FROM market")}
    now = int(time.time())
    for series in SERIES:
        listed = [m for m in api.settled_markets(series, now - DAYS * 86400, now) if m.get("result") in ("yes", "no")]
        todo = [m for m in listed if m["ticker"] not in have]
        print(f"{series}: {len(listed)} settled, {len(todo)} to fetch", flush=True)
        by_close = defaultdict(list)
        for m in todo:
            c = backfill.iso_ts(m.get("close_time"))
            if c:
                by_close[c // 3600].append((m, c))
        batch = []
        def flush(batch):
            lo = min(c for _, c in batch) - WINDOW_S
            hi = max(c for _, c in batch)
            got = api.batch_candlesticks([m["ticker"] for m, _ in batch], lo, hi)
            for m, c in batch:
                t = m["ticker"]
                rows = [r for r in (backfill.parse_candle(x, t, series) for x in got.get(t, [])) if r and c - WINDOW_S <= r[2] <= c]
                db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
                db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)", (t, series, backfill.iso_ts(m.get("open_time")), c, m.get("result"), m.get("floor_strike"), len(rows)))
            db.commit()
            time.sleep(PAUSE)
        for hour in sorted(by_close):
            for item in by_close[hour]:
                batch.append(item)
                if len(batch) >= 40:
                    flush(batch)
                    batch = []
        if batch:
            flush(batch)
        print(f"  {series} done", flush=True)


def events_for(candles: list[tuple]):
    """candles: (end, bid, ask, volume) sorted. Yields (t_index) of event minutes per the pre-registered definition, skipping any within QUIET_S of the previous event."""
    last_ev = None
    for i in range(1, len(candles)):
        e0, b0, a0, _ = candles[i - 1]
        e1, b1, a1, v1 = candles[i]
        if e1 - e0 != 60 or None in (b0, a0, b1, a1) or not (0 < b0 < a0 < 1 and 0 < b1 < a1 < 1):
            continue
        m0, m1 = (b0 + a0) / 2, (b1 + a1) / 2
        if abs(m1 - m0) >= JUMP - 1e-12 and a0 - b0 <= MAX_SPREAD and a1 - b1 <= MAX_SPREAD and MID_LO <= m0 <= MID_HI and (v1 or 0) >= MIN_VOL:
            if last_ev is None or e1 - last_ev >= QUIET_S:
                last_ev = e1
                yield i


def trade(candles: list[tuple], i: int, mode: str, k: int, yes_jumped: bool, mult: float = 1.0):
    """Buy at the closing quote of minute i+1, sell at the closing bid k minutes after that. None if a needed minute is missing."""
    by = {c[0]: c for c in candles}
    t0 = candles[i][0] + 60
    q0, q1 = by.get(t0), by.get(t0 + 60 * k)
    if q0 is None or q1 is None or None in (q0[1], q0[2], q1[1], q1[2]):
        return None
    want_yes = yes_jumped if mode == "MOM" else (not yes_jumped)
    if want_yes:
        buy, sell = q0[2], q1[1]
    else:
        buy, sell = round(1 - q0[1], 4), round(1 - q1[2], 4)
    if not (0 < buy < 1) or not (0 <= sell < 1):
        return None
    return sell - buy - fee(buy, mult) - fee(sell, mult)


def run() -> None:
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists.")
        return
    db = sqlite3.connect(DB)
    close = {t: c for t, c in db.execute("SELECT ticker, close_ts FROM market")}
    by = defaultdict(list)
    for tk, end, bc, ac, vol in db.execute("SELECT ticker, end_ts, bid_c, ask_c, volume FROM candle ORDER BY ticker, end_ts"):
        by[tk].append((end, bc, ac, vol))
    res = {(m, k): [] for m in ("MOM", "FADE") for k in KS}
    skipped = defaultdict(int)
    n_events = 0
    for tk, cs in by.items():
        day = datetime.fromtimestamp(close[tk], timezone.utc).strftime("%Y-%m-%d")
        for i in events_for(cs):
            n_events += 1
            yes_jumped = (cs[i][1] + cs[i][2]) / 2 > (cs[i - 1][1] + cs[i - 1][2]) / 2
            for (m, k), lst in res.items():
                a = trade(cs, i, m, k, yes_jumped)
                if a is None:
                    skipped[(m, k)] += 1
                    continue
                lst.append({"day": day, "t": cs[i][0], "net": a, "stress": trade(cs, i, m, k, yes_jumped, STRESS)})
    out = [f"SC1: {len(by)} markets with candles, {n_events} events"]
    for (m, k), rows in res.items():
        if len(rows) < 5:
            out.append(f"{m}{k}: {len(rows)} trades")
            continue
        rows.sort(key=lambda r: r["t"])
        days = len({r["day"] for r in rows})
        mean, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
        h = len(rows) // 2
        h1, h2 = st.mean(r["net"] for r in rows[:h]), st.mean(r["net"] for r in rows[h:])
        s = st.mean(r["stress"] for r in rows)
        ok = len(rows) >= MIN_EVENTS and days >= MIN_DAYS and mean >= BAR_C and z >= BAR_Z and h1 > 0 and h2 > 0 and s > 0
        verdict = "NOT_YET_FALSIFIED" if ok else ("NOT_ENOUGH_DATA" if (len(rows) < MIN_EVENTS or days < MIN_DAYS) else "FALSIFIED")
        out.append(f"{m}{k}: {verdict:18s} n={len(rows):5d} days={days:3d} net {100*mean:+6.2f}c z {z:+5.2f} halves {100*h1:+5.2f}/{100*h2:+5.2f} stress {100*s:+6.2f}c skipped {skipped[(m, k)]}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
    elif cmd == "run":
        run()
    else:
        print(__doc__)
