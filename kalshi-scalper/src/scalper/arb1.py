"""ARB1 (README, Pre-registration: ARB1): locked arithmetic across a mutually exclusive event. Rules fixed in the README before any snapshot was taken.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

If at most one leg of an event can resolve YES, buying the NO side of the K legs pays at least K-1 dollars whatever happens, so YES bids that sum to more than 1 plus fees are a
riskless profit. History goes into its OWN database (`data/arb1.sqlite`).
Usage: python -m scalper.arb1 scan  (one snapshot, 2 to 3 minutes; run it 12 times, at least 15 minutes apart)   then   python -m scalper.arb1 report  (once)
"""
from __future__ import annotations

import math
import sqlite3
import statistics as st
import sys
import time

from . import api
from .paths import DATA_DIR

ARB_DB = DATA_DIR / "arb1.sqlite"
MIN_LOCK = 0.01
MIN_CAPACITY = 10.0
SIZE_CAP = 50.0
PERSIST_S = 15 * 60
MIN_EVENTS = 3
MIN_PER_DAY = 1.0
MIN_SCANS = 8


def fee(p: float) -> float:
    return 0.07 * p * (1.0 - p)


def fee_rounded(p: float, contracts: float) -> float:
    """Per contract fee when the order's fee is rounded UP to the cent (information only)."""
    c = max(1.0, math.floor(contracts))
    return math.ceil(0.07 * c * p * (1.0 - p) * 100.0 - 1e-9) / 100.0 / c


def _f(x) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def event_row(event: dict) -> dict | None:
    """The lock of one event, or None when it is not a mutually exclusive event with at least 2 active legs that have a positive YES bid."""
    if not event.get("mutually_exclusive"):
        return None
    bids, sizes = [], []
    for m in event.get("markets", []):
        if m.get("status") != "active":
            continue
        b, z = _f(m.get("yes_bid_dollars")), _f(m.get("yes_bid_size_fp"))
        if b is None or z is None or b <= 0.0 or b >= 1.0 or z <= 0.0:
            continue
        bids.append(b)
        sizes.append(z)
    if len(bids) < 2:
        return None
    cap = min(sizes)
    total = sum(bids)
    lock = total - 1.0 - sum(fee(b) for b in bids)
    lock_r = total - 1.0 - sum(fee_rounded(b, min(cap, SIZE_CAP)) for b in bids)
    return {"event": event["event_ticker"], "series": event.get("series_ticker", ""), "legs": len(bids), "sum_bid": total, "lock": lock, "lock_rounded": lock_r, "capacity": cap}


def is_opportunity(r: dict) -> bool:
    return r["lock"] >= MIN_LOCK - 1e-12 and r["capacity"] >= MIN_CAPACITY


def scan() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(ARB_DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS scan(scan_id INTEGER PRIMARY KEY, ts INTEGER, n_events INTEGER, n_exclusive INTEGER);
CREATE TABLE IF NOT EXISTS row(scan_id INTEGER, event TEXT, series TEXT, legs INTEGER, sum_bid REAL, lock REAL, lock_rounded REAL, capacity REAL, PRIMARY KEY(scan_id, event));""")
    ts = int(time.time())
    cur, n_events, n_ex, rows = None, 0, 0, []
    while True:
        params = {"status": "open", "with_nested_markets": "true", "limit": 200}
        if cur:
            params["cursor"] = cur
        d = api._get("/events", params)
        for e in d.get("events", []):
            n_events += 1
            if e.get("mutually_exclusive"):
                n_ex += 1
            r = event_row(e)
            if r:
                rows.append(r)
        cur = d.get("cursor")
        if not cur:
            break
    scan_id = (db.execute("SELECT COALESCE(MAX(scan_id), 0) FROM scan").fetchone()[0]) + 1
    db.execute("INSERT INTO scan VALUES(?,?,?,?)", (scan_id, ts, n_events, n_ex))
    db.executemany("INSERT OR REPLACE INTO row VALUES(?,?,?,?,?,?,?,?)", [(scan_id, r["event"], r["series"], r["legs"], r["sum_bid"], r["lock"], r["lock_rounded"], r["capacity"]) for r in rows])
    db.commit()
    best = max(rows, key=lambda r: r["lock"], default=None)
    print(f"scan {scan_id}: {n_events} events, {n_ex} mutually exclusive, {len(rows)} usable, {sum(1 for r in rows if is_opportunity(r))} opportunities"
          + (f", largest lock {best['lock'] * 100:+.2f}c on {best['event']} (capacity {best['capacity']:.0f})" if best else ""), flush=True)


def persistent(scans: list[dict]) -> dict:
    """`scans` is [{"ts": int, "rows": [row, ...]}]. Returns {event: value} for the events that are an opportunity in two scans at least PERSIST_S apart, valued as
    lock x min(capacity, SIZE_CAP) in the first scan where the event was an opportunity."""
    seen: dict = {}
    for sc in sorted(scans, key=lambda s: s["ts"]):
        for r in sc["rows"]:
            if is_opportunity(r):
                seen.setdefault(r["event"], []).append((sc["ts"], r))
    out = {}
    for ev, lst in seen.items():
        if lst[-1][0] - lst[0][0] >= PERSIST_S:
            r = lst[0][1]
            out[ev] = r["lock"] * min(r["capacity"], SIZE_CAP)
    return out


def verdict(scans: list[dict]) -> tuple[str, dict]:
    if len(scans) < MIN_SCANS:
        return "NOT_ENOUGH_DATA", {"scans": len(scans)}
    ts = sorted(s["ts"] for s in scans)
    span = max(ts[-1] - ts[0], 1)
    per = persistent(scans)
    total = sum(per.values())
    per_day = total * 86400.0 / span
    ok = len(per) >= MIN_EVENTS and per_day >= MIN_PER_DAY
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"scans": len(scans), "persistent": len(per), "total": total, "per_day": per_day, "span_h": span / 3600.0}


def report() -> None:
    db = sqlite3.connect(ARB_DB)
    scans = []
    for sid, ts, ne, nx in db.execute("SELECT scan_id, ts, n_events, n_exclusive FROM scan ORDER BY scan_id"):
        rows = [{"event": e, "series": s, "legs": l, "sum_bid": sb, "lock": lk, "lock_rounded": lr, "capacity": c}
                for e, s, l, sb, lk, lr, c in db.execute("SELECT event, series, legs, sum_bid, lock, lock_rounded, capacity FROM row WHERE scan_id=?", (sid,))]
        scans.append({"ts": ts, "rows": rows, "n_events": ne, "n_exclusive": nx})
    print(f"{len(scans)} scans. Signal counts first.")
    for i, sc in enumerate(scans):
        print(f"  scan {i + 1}: {sc['n_events']} events, {sc['n_exclusive']} mutually exclusive, {len(sc['rows'])} usable, {sum(1 for r in sc['rows'] if is_opportunity(r))} opportunities")
    v, s = verdict(scans)
    if "persistent" in s:
        print(f"\nARB1: {s['persistent']} persistent events over {s['span_h']:.1f} h, total value of one fill each ${s['total']:.2f}, scaled ${s['per_day']:.2f} per day -> {v}")
    else:
        print(f"\nARB1: {s['scans']} scans -> {v}")
    allrows = [r for sc in scans for r in sc["rows"]]
    if allrows:
        sums = sorted(r["sum_bid"] for r in allrows)
        q = lambda a: sums[min(len(sums) - 1, int(a * (len(sums) - 1)))]
        print(f"\nInformation: sum of YES bids over usable events: median {q(0.5):.3f}, 95th percentile {q(0.95):.3f}, share over 1.00 {sum(1 for x in sums if x > 1.0) / len(sums):.2%}")
        top = max(allrows, key=lambda r: r["lock"])
        print(f"  largest lock seen {top['lock'] * 100:+.2f}c on {top['event']} ({top['legs']} legs, capacity {top['capacity']:.0f}); with cent-rounded fees {top['lock_rounded'] * 100:+.2f}c")
        opp = [r for r in allrows if is_opportunity(r)]
        if opp:
            print(f"  opportunities in any scan: {len(opp)} rows on {len({r['event'] for r in opp})} events; with cent-rounded fees {sum(1 for r in opp if r['lock_rounded'] >= MIN_LOCK)} of them still clear 1c")
            by_series: dict = {}
            for r in opp:
                by_series.setdefault(r["series"], set()).add(r["event"])
            print("  by series: " + ", ".join(f"{k} {len(v)}" for k, v in sorted(by_series.items(), key=lambda kv: -len(kv[1]))[:10]))
        if len(scans) > 1:
            gone = tot = 0
            for a, b in zip(scans, scans[1:]):
                now = {r["event"] for r in b["rows"] if is_opportunity(r)}
                for r in a["rows"]:
                    if is_opportunity(r):
                        tot += 1
                        gone += r["event"] not in now
            print(f"  opportunities gone by the next scan: {gone} of {tot}")


if __name__ == "__main__":
    scan() if sys.argv[1:2] == ["scan"] else report()
