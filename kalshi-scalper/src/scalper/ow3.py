"""OW3, OW4, OW7: three hold-to-settlement contrasts. Rules fixed in the README ("Pre-registration: OW3, OW4, OW7") before this file ran on any market.

Each compares an arm A (what would be traded) against an arm B on net cents a contract after the entry fee, with a day-clustered standard error. Verdict words: FALSIFIED,
NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade, and nothing here changes L1.

Usage: python -m scalper.ow3
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict
from datetime import datetime, timezone

from . import lstrats as L
from .scalps import load as load_markets

L1_BAND = (0.88, 0.97)
OW3_BAND = (0.82, 0.97)
OW3_LEFTS = (600, 480, 360)
L1_LEFT = 360
Z_BAR = 2.5
MIN_N = 300
MIN_DAYS = 5


def contrast(a: list[dict], b: list[dict], key: str = "net") -> tuple[float, float, float]:
    """(difference of means A minus B, day-clustered standard error, z). Each entry carries its influence on the difference, summed by day, so twenty entries from one day count about once."""
    if len(a) < 2 or len(b) < 2:
        return 0.0, float("inf"), 0.0
    ma, mb = sum(r[key] for r in a) / len(a), sum(r[key] for r in b) / len(b)
    by: dict[str, float] = defaultdict(float)
    for r in a:
        by[r["day"]] += (r[key] - ma) / len(a)
    for r in b:
        by[r["day"]] -= (r[key] - mb) / len(b)
    se = math.sqrt(sum(v * v for v in by.values()))
    d = ma - mb
    return d, se, (d / se if se > 0 else 0.0)


def verdict(a: list[dict], b: list[dict], midpoint: float):
    days_a = len({r["day"] for r in a})
    if len(a) < MIN_N or len(b) < MIN_N or days_a < MIN_DAYS:
        return "NOT_ENOUGH_DATA", {"n_a": len(a), "n_b": len(b), "days": days_a}
    d, se, z = contrast(a, b)
    halves = []
    for first in (True, False):
        ha = [r for r in a if (r["close_ts"] < midpoint) == first]
        hb = [r for r in b if (r["close_ts"] < midpoint) == first]
        halves.append(contrast(ha, hb)[0] if len(ha) > 1 and len(hb) > 1 else 0.0)
    stress = sum(r["stress"] for r in a) / len(a)
    ok = z >= Z_BAR and halves[0] > 0 and halves[1] > 0 and stress > 0
    mean_a = sum(r["net"] for r in a) / len(a)
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n_a": len(a), "n_b": len(b), "days": days_a, "mean_a": mean_a, "mean_b": sum(r["net"] for r in b) / len(b),
                                                        "diff": d, "se": se, "z": z, "h1": halves[0], "h2": halves[1], "stress": stress}


def residualise(rows: list[dict]) -> None:
    """OW3: net minus the mean net of the entries at the same time and the same 2c price bucket, so the side cannot win just by sitting at a different price."""
    cell: dict = defaultdict(list)
    for r in rows:
        r["cell"] = (r["left"], int(r["price"] * 50 + 1e-9))
        cell[r["cell"]].append(r["net"])
    mean = {k: sum(v) / len(v) for k, v in cell.items()}
    for r in rows:
        r["res"] = r["net"] - mean[r["cell"]]


def ow3_arms(markets: list[tuple]):
    rows = []
    for left in OW3_LEFTS:
        for e in L.hold_rule(markets, left, OW3_BAND):
            rows.append(dict(e, left=left))
    residualise(rows)
    a = [dict(r, net=r["res"], stress=r["stress"]) for r in rows if r["side"] == "no"]
    b = [dict(r, net=r["res"]) for r in rows if r["side"] == "yes"]
    return a, b


def is_us_hours(close_ts: int) -> bool:
    d = datetime.fromtimestamp(close_ts, timezone.utc)
    if d.weekday() >= 5:
        return False
    return (13, 30) <= (d.hour, d.minute) < (20, 0)


def ow4_arms(markets: list[tuple]):
    rows = [r for r in L.hold_rule(markets, L1_LEFT, L1_BAND) if datetime.fromtimestamp(r["close_ts"], timezone.utc).weekday() < 5]
    return [r for r in rows if is_us_hours(r["close_ts"])], [r for r in rows if not is_us_hours(r["close_ts"])]


def oi_feature(by: dict, close_ts: int):
    """(open interest at the candle ending 360 s left minus open interest at the one ending 600 s left) / max(1, summed volume of the candles ending 540, 480, 420, 360 s left).
    `by` maps end_ts to (oi, volume). None if any needed candle, oi or volume is missing: such a market is counted and left out, never filled in."""
    try:
        oi_now, oi_then = by[close_ts - 360][0], by[close_ts - 600][0]
        vols = [by[close_ts - k][1] for k in (540, 480, 420, 360)]
    except KeyError:
        return None
    if oi_now is None or oi_then is None or any(v is None for v in vols):
        return None
    return (oi_now - oi_then) / max(1.0, float(sum(vols)))


def load_oi() -> dict:
    import sqlite3
    from .paths import DB
    out: dict = defaultdict(dict)
    for t, end, oi, vol in sqlite3.connect(DB).execute("SELECT ticker, end_ts, oi, volume FROM candle"):
        out[t][end] = (oi, vol)
    return out


OW7_FIXED_CUT = 0.2395      # the lowest-tercile boundary of the 31 day sample the first read used (largest bottom value 0.23924, smallest kept value 0.23968); the forward read does not refit it


def ow7_arms(markets: list[tuple], raw: dict, fixed_cut: float | None = None):
    """Arm B is the lowest tercile. The first read took the tercile of its own sample; the forward read passes fixed_cut so the boundary comes from the old data, never the new."""
    rows = []
    for e in L.hold_rule(markets, L1_LEFT, L1_BAND):
        f = raw.get(e["ticker"])
        if f is not None:
            rows.append(dict(e, feature=f))
    if len(rows) < 3:
        return [], [], len(rows)
    cut = fixed_cut if fixed_cut is not None else sorted(r["feature"] for r in rows)[len(rows) // 3]
    return [r for r in rows if r["feature"] > cut], [r for r in rows if r["feature"] <= cut], len(rows)


def forward(after: str) -> None:
    """The one forward read of OW7: markets closing on or after `after` (a UTC date), the old fixed boundary, the same bar. OW3 and OW4 are not rerun."""
    markets, _ = load_markets()
    cutoff = int(datetime.strptime(after, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
    markets = [m for m in markets if m[3] >= cutoff]
    if not markets:
        print("No markets on or after " + after + ". Run: python -m scalper.backfill 30")
        return
    mid = (min(m[3] for m in markets) + max(m[3] for m in markets)) / 2
    oi = load_oi()
    raw = {t: f for t, _, cs, c, _r in markets if (f := oi_feature(oi.get(t, {}), c)) is not None}
    a, b, n = ow7_arms(markets, raw, OW7_FIXED_CUT)
    v, s = verdict(a, b, mid)
    print(f"OW7 forward, markets closing on or after {after}: {len(markets)} markets, {n} usable entries, boundary {OW7_FIXED_CUT} fixed.")
    print(f"  arm A (kept) n={len(a)}  arm B (lowest tercile) n={len(b)}  {v}")
    if "z" in s:
        print(f"  A {s['mean_a']*100:+.2f}c  B {s['mean_b']*100:+.2f}c  diff {s['diff']*100:+.2f}c  z {s['z']:+.2f}  halves {s['h1']*100:+.2f}c / {s['h2']*100:+.2f}c  A x1.2 {s['stress']*100:+.2f}c")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--forward":
        forward(sys.argv[2])
        return
    markets, mid = load_markets()
    print(f"{len(markets)} markets. Three hold-to-settlement contrasts, net cents a contract (A minus B).\n")
    head = f"{'':5} {'n A':>6} {'n B':>6} {'days':>5} {'mean A':>8} {'mean B':>8} {'diff':>7} {'se':>6} {'z':>6} {'1st half':>9} {'2nd half':>9} {'A x1.2':>8}  verdict"
    print(head)
    def show(name, a, b):
        v, s = verdict(a, b, mid)
        if "z" in s:
            print(f"{name:5} {s['n_a']:>6} {s['n_b']:>6} {s['days']:>5} {s['mean_a']*100:>8.2f} {s['mean_b']*100:>8.2f} {s['diff']*100:>7.2f} {s['se']*100:>6.2f} {s['z']:>6.2f} {s['h1']*100:>9.2f} {s['h2']*100:>9.2f} {s['stress']*100:>8.2f}  {v}")
        else:
            print(f"{name:5} {s['n_a']:>6} {s['n_b']:>6} {s['days']:>5}  (too few entries or days)  {v}")
    show("OW3", *ow3_arms(markets))
    show("OW4", *ow4_arms(markets))
    oi = load_oi()
    raw = {}
    unusable = 0
    for t, _, cs, close_ts, _r in markets:
        f = oi_feature(oi.get(t, {}), close_ts)
        if f is None:
            unusable += 1
        else:
            raw[t] = f
    vals = sorted(raw.values())
    if vals:
        print(f"\nOW7 units: {len(vals)} markets with a feature, {unusable} unusable; feature min {vals[0]:.3f}, median {vals[len(vals)//2]:.3f}, max {vals[-1]:.3f}")
    a7, b7, n7 = ow7_arms(markets, raw)
    show("OW7", a7, b7)


if __name__ == "__main__":
    main()
