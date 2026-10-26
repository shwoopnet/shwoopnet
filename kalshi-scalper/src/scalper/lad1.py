"""LAD1 (README, Pre-registration: LAD1): option-style fair value on the hourly Bitcoin ladder (KXBTCD). Research only: nothing here places an order.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

    python -m scalper.lad1 fetch    (resumable; settled KXBTCD markets of the last 30 days; the strikes kept for each hour are chosen from the quotes at 30 minutes
                                     before the close only (mid between 0.03 and 0.97), never from the outcome)
    python -m scalper.lad1 run      (the one read; refused a second time)
"""
from __future__ import annotations

import math
import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from . import api, backfill
from . import lstrats as L
from . import search5k as S5
from .calibration import cluster_mean_z
from .paths import DATA_DIR

DB = DATA_DIR / "lad1.sqlite"
RESULT = DATA_DIR / "lad1_result.txt"
SERIES = "KXBTCD"
DAYS = 30
PROBE_S = (1860, 1740)              # the one minute at 30 minutes before the close used to pick which strikes to keep
WINDOW_S = (3300, 60)               # candles from 55 minutes to 1 minute before the close
LEFTS = (45, 30, 15)                # minutes before the close
SIGMAS = ("iv", "rv")
MARGIN = 0.03
MAX_SPREAD = 0.02
BAND = (0.10, 0.90)
MIN_N, MIN_HOURS, BAR_Z = 300, 100, 2.5
STRESS = 1.2
PAUSE = 0.4


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def fee(p: float, mult: float = 1.0) -> float:
    return mult * 0.07 * p * (1 - p)


def p_yes(spot: float, strike: float, sigma_min: float, tau_min: float) -> float | None:
    """P(60 second settlement average above the strike); variance factor tau + 1/3 for the averaging minute."""
    if not (spot > 0 and strike > 0 and sigma_min > 0 and tau_min > 0):
        return None
    return phi(math.log(spot / strike) / (sigma_min * math.sqrt(tau_min + 1.0 / 3.0)))


def decide(p: float | None, bid: float | None, ask: float | None):
    """(side, price) when the model beats the price by more than MARGIN net of the fee; one sided, wide or out-of-band books trade nothing."""
    if p is None or bid is None or ask is None or not (0 < bid < ask < 1) or ask - bid > MAX_SPREAD or not (BAND[0] <= ask <= BAND[1]):
        return None
    no_price = round(1 - bid, 4)
    ev_yes = p - ask - fee(ask)
    ev_no = (1 - p) - no_price - fee(no_price)
    best = max((ev_yes, "yes", ask), (ev_no, "no", no_price))
    return (best[1], best[2]) if best[0] > MARGIN else None


def chunks(items, n):
    for i in range(0, len(items), n):
        yield items[i:i + n]


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(backfill.SCHEMA)
    done = {r[0] for r in db.execute("SELECT DISTINCT close_ts FROM market")}
    now = int(time.time())
    listed = list(api.settled_markets(SERIES, now - DAYS * 86400, now))
    by_close = defaultdict(list)
    for m in listed:
        c = backfill.iso_ts(m.get("close_time"))
        if c is not None and m.get("result") in ("yes", "no"):
            by_close[c].append(m)
    print(f"{len(listed)} settled markets in {len(by_close)} hourly closes; {len(by_close) - len(done)} to fetch", flush=True)
    for n, close_ts in enumerate(sorted(by_close)):
        if close_ts in done:
            continue
        ms = by_close[close_ts]
        keep = []
        for ch in chunks(ms, 100):
            got = api.batch_candlesticks([m["ticker"] for m in ch], close_ts - PROBE_S[0], close_ts - PROBE_S[1])
            for m in ch:
                rows = [r for r in (backfill.parse_candle(x, m["ticker"], SERIES) for x in got.get(m["ticker"], [])) if r]
                if rows and rows[-1][3] is not None and rows[-1][7] is not None:
                    mid = (rows[-1][6] + rows[-1][10]) / 2 if rows[-1][6] is not None and rows[-1][10] is not None else None
                    if mid is not None and 0.03 <= mid <= 0.97:
                        keep.append(m)
            time.sleep(PAUSE)
        for ch in chunks(keep, 100):
            got = api.batch_candlesticks([m["ticker"] for m in ch], close_ts - WINDOW_S[0], close_ts - WINDOW_S[1])
            for m in ch:
                t = m["ticker"]
                rows = [r for r in (backfill.parse_candle(x, t, SERIES) for x in got.get(t, [])) if r]
                db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
                db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)", (t, SERIES, backfill.iso_ts(m.get("open_time")), close_ts, m.get("result"), m.get("floor_strike"), len(rows)))
            time.sleep(PAUSE)
        db.commit()
        if n % 25 == 0:
            print(f"  {n}/{len(by_close)} closes, {len(keep)} strikes kept at the last one", flush=True)
    print("done", db.execute("SELECT COUNT(*) FROM market").fetchone()[0], "markets", flush=True)


def load_events():
    db = sqlite3.connect(DB)
    ev = defaultdict(dict)
    meta = {}
    for tk, close, res, strike in db.execute("SELECT ticker, close_ts, result, strike FROM market"):
        meta[tk] = (close, res, strike)
    for tk, end, bc, ac in db.execute("SELECT ticker, end_ts, bid_c, ask_c FROM candle"):
        if tk in meta:
            ev[meta[tk][0]].setdefault(tk, {})[end] = (bc, ac)
    return ev, meta


def run() -> None:
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists.")
        return
    ev, meta = load_events()
    con = sqlite3.connect(S5.DB)
    perp = S5.Perp(con, "BTC")
    entries = {(left, sg): [] for left in LEFTS for sg in SIGMAS}
    for close in sorted(ev):
        for left in LEFTS:
            t = close - left * 60
            j = perp.idx(t - 60)
            if j < 61 or j >= perp.n or np.isnan(perp.c[j - 60:j + 1]).any():
                continue
            S = float(perp.c[j])
            rv = float(np.std(np.diff(np.log(perp.c[j - 60:j + 1])), ddof=1))
            dv = perp.d[j]
            if np.isnan(dv) or rv <= 0:
                continue
            sig = {"iv": float(dv) / 100.0 / math.sqrt(525_600.0), "rv": rv}
            for tk, cs in ev[close].items():
                q = cs.get(t)
                if q is None:
                    continue
                _, res, K = meta[tk]
                if K is None:
                    continue
                for sg in SIGMAS:
                    p = p_yes(S, float(K), sig[sg], left)
                    pick = decide(p, q[0], q[1])
                    if pick is None:
                        continue
                    side, price = pick
                    yes = res == "yes"
                    entries[(left, sg)].append({"close": close, "day": datetime.fromtimestamp(close, timezone.utc).strftime("%Y-%m-%d"), "net": L.net(side, price, yes),
                                                "stress": L.net(side, price, yes, STRESS), "won": (yes if side == "yes" else not yes), "price": price})
    out = [f"LAD1: {len(ev)} hourly closes, {len(meta)} strikes"]
    for (left, sg), rows in entries.items():
        if len(rows) < 5:
            out.append(f"left {left}m sigma {sg}: {len(rows)} entries")
            continue
        rows.sort(key=lambda r: r["close"])
        hours = len({r["close"] for r in rows})
        m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
        h = len(rows) // 2
        h1, h2 = st.mean(r["net"] for r in rows[:h]), st.mean(r["net"] for r in rows[h:])
        s = st.mean(r["stress"] for r in rows)
        ok = len(rows) >= MIN_N and hours >= MIN_HOURS and z >= BAR_Z and h1 > 0 and h2 > 0 and s > 0
        verdict = "NOT_YET_FALSIFIED" if ok else ("NOT_ENOUGH_DATA" if len(rows) < MIN_N or hours < MIN_HOURS else "FALSIFIED")
        out.append(f"left {left:2d}m sigma {sg}: {verdict:18s} n={len(rows):5d} hours={hours:4d} net {100*m:+6.2f}c z {z:+5.2f} halves {100*h1:+5.2f}/{100*h2:+5.2f} stress {100*s:+6.2f}c win {100*sum(r['won'] for r in rows)/len(rows):4.1f}% vs price {st.mean(r['price'] for r in rows):.3f}")
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
