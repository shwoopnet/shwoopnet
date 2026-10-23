"""LAG2 (README, Pre-registration: LAG2): does the Kraken spot price, read in the last two minutes, price a Bitcoin 15 minute market better than the trades that print on Kalshi,
by more than fee plus a margin? Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.lag2 run     (once, after `lag2_fetch kraken` and `kalshi` are done; a second run is refused unless the result file is deleted on purpose)
"""
from __future__ import annotations

import json
import math
import statistics as st
import sys
from datetime import datetime, timezone

from . import lstrats as L
from .calibration import cluster_mean_z
from .lag2_fetch import KRAKEN, load_tape, markets
from .paths import DATA_DIR

# ---- fixed in the README before the data was scored ----
DECISION_LEFT = (120, 90, 60)          # seconds before the close
REF_WINDOW, LATENCY, FILL_WINDOW, HALF_SPREAD, EDGE, MAX_GAP = 15, 2.0, 20.0, 0.01, 0.07, 5
VOL_LOOKBACK, VOL_STEP = 900, 10
MIN_N, MIN_DAYS, MEAN_C, Z_BAR, PF_BAR, FALSIFY_C, FALSIFY_Z = 150, 8, 0.020, 2.5, 1.3, 0.005, 1.0
RESULT = DATA_DIR / "lag2_result.txt"
RESULT_B = DATA_DIR / "lag2b_result.txt"


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def price_at(sec: dict, t: int):
    """Kraken last price at or before second t, carried forward at most MAX_GAP seconds."""
    for k in range(MAX_GAP + 1):
        e = sec.get(str(t - k))
        if e:
            return e[0]
    return None


def sigma_per_s(sec: dict, t: int):
    """Standard deviation of log returns on a VOL_STEP second grid over the previous VOL_LOOKBACK seconds, per sqrt(second)."""
    pts = [price_at(sec, t - i * VOL_STEP) for i in range(VOL_LOOKBACK // VOL_STEP + 1)]
    if any(p is None for p in pts):
        return None
    r = [math.log(a / b) for a, b in zip(pts, pts[1:])]
    s = st.pstdev(r) if len(r) > 5 else None
    return None if not s else s / math.sqrt(VOL_STEP)


VOL_MIN_POINTS = 45          # LAG2B: at least this many of the 91 grid points must have a price


def sigma_b(sec: dict, t: int):
    """LAG2B volatility: the grid points that have a price (carried forward at most MAX_GAP s) are kept, and the variance per second is the sum of squared log returns over the sum of the
    time gaps between consecutive kept points (so a return across a gap is scaled by the gap). Needs at least VOL_MIN_POINTS points."""
    pts = [(t - i * VOL_STEP, price_at(sec, t - i * VOL_STEP)) for i in range(VOL_LOOKBACK // VOL_STEP + 1)]
    pts = [(ts, p) for ts, p in pts if p is not None]
    if len(pts) < VOL_MIN_POINTS:
        return None
    sq = sum(math.log(a[1] / b[1]) ** 2 for a, b in zip(pts, pts[1:]))
    dt = sum(a[0] - b[0] for a, b in zip(pts, pts[1:]))
    return math.sqrt(sq / dt) if sq > 0 and dt > 0 else None


def p_yes(S: float, K: float, sigma: float, left: float) -> float:
    """P(settlement average > strike): the settlement is the mean of the last 60 seconds, so the variance is sigma^2 * (left - 40)."""
    return phi(math.log(S / K) / (sigma * math.sqrt(max(left - 40.0, 1.0))))


def reference(trades: list, t: float):
    r = [x for x in trades if t - REF_WINDOW < x[0] <= t]
    return None if not r else max(r, key=lambda x: x[0])[1]


def fill(trades: list, t: float, side: str):
    """Price of the first trade after t + LATENCY, within FILL_WINDOW, whose taker bought our side: what someone actually paid for it."""
    for sec, yes_price, taker, _ in sorted(trades):
        if t + LATENCY < sec <= t + LATENCY + FILL_WINDOW and taker == side:
            return yes_price if side == "yes" else round(1 - yes_price, 4)
    return None


def trade_for(market: tuple, trades: list, sec: dict, vol=None):
    """The first qualifying decision for a market: (day, close, net, stress) or None."""
    tk, close, strike, res = market
    for left in DECISION_LEFT:
        t = close - left
        S, sg, ref = price_at(sec, t), (vol or sigma_per_s)(sec, t), reference(trades, t)
        if S is None or sg is None or ref is None:
            continue
        p = p_yes(S, strike, sg, left)
        side = "yes" if p - (ref + HALF_SPREAD) >= EDGE else ("no" if (1 - p) - ((1 - ref) + HALF_SPREAD) >= EDGE else None)
        if side is None:
            continue
        price = fill(trades, t, side)
        if price is None:
            continue
        yes = res == "yes"
        return {"day": datetime.fromtimestamp(close, timezone.utc).strftime("%Y-%m-%d"), "close_ts": close, "net": L.net(side, price, yes), "stress": L.net(side, price, yes, L.STRESS)}
    return None


def judge(rows: list[dict]) -> dict:
    days = {r["day"] for r in rows}
    if len(rows) < MIN_N or len(days) < MIN_DAYS:
        return {"verdict": "NOT_ENOUGH_DATA", "n": len(rows), "days": len(days)}
    m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    ds = sorted(days)
    mid = ds[len(ds) // 2]
    h = [st.mean(r["net"] for r in rows if (r["day"] < mid) == first) for first in (True, False)]
    w = sum(r["net"] for r in rows if r["net"] > 0)
    l = -sum(r["net"] for r in rows if r["net"] < 0)
    pf = w / l if l else float("inf")
    stress = st.mean(r["stress"] for r in rows)
    ok = m >= MEAN_C and z >= Z_BAR and h[0] > 0 and h[1] > 0 and stress > 0 and pf >= PF_BAR
    v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    return {"verdict": v, "n": len(rows), "days": len(days), "mean": m, "z": z, "h1": h[0], "h2": h[1], "stress": stress, "pf": pf}


def run_b() -> None:
    if RESULT_B.exists():
        print(f"Refusing to run again: {RESULT_B} exists.")
        return
    sec = json.load(open(KRAKEN))["sec"]
    tape = load_tape()
    ms = [m for m in markets() if m[0] in tape]
    rows = [t for m in ms if (t := trade_for(m, tape[m[0]], sec, sigma_b))]
    j = judge(rows)
    out = [f"LAG2B: verdict {j['verdict']}; markets with a tape {len(ms)}, trades {len(rows)} on {j.get('days', 0)} days"]
    if "mean" in j:
        out.append(f"mean {100 * j['mean']:+.2f}c z {j['z']:+.2f} halves {100 * j['h1']:+.2f}c / {100 * j['h2']:+.2f}c stress {100 * j['stress']:+.2f}c PF {j['pf']:.2f}")
    RESULT_B.write_text("\n".join(out) + "\n")
    print("\n".join(out))


def main(argv: list[str]) -> None:
    if len(argv) >= 2 and argv[1] == "runb":
        run_b()
        return
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    sec = json.load(open(KRAKEN))["sec"]
    tape = load_tape()
    ms = [m for m in markets() if m[0] in tape]
    rows = [t for m in ms if (t := trade_for(m, tape[m[0]], sec))]
    j = judge(rows)
    out = [f"LAG2: verdict {j['verdict']}; markets with a tape {len(ms)}, trades {len(rows)} on {j.get('days', 0)} days"]
    if "mean" in j:
        out.append(f"mean {100 * j['mean']:+.2f}c z {j['z']:+.2f} halves {100 * j['h1']:+.2f}c / {100 * j['h2']:+.2f}c stress {100 * j['stress']:+.2f}c PF {j['pf']:.2f}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
