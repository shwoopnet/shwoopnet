"""LIVE3 (README, information only): do the live orders that FILLED differ from the ones that did NOT, once both are settled from public results?
Fills come from studies/live_orders_condensed_2026-10-22.csv, no-fills from studies/live_nofills_2026-10-22.csv. Both are scored the same way:
held to settlement at the order's limit price with the 7% fee, so the exit rule and the real fill price do not enter. No verdict is given.
Usage: python -m scalper.live_fill
"""
from __future__ import annotations

import csv
import sqlite3
import statistics as st
import sys
from datetime import datetime, timedelta, timezone

from .calibration import cluster_mean_z
from .paths import DATA_DIR

LETTER = {"B": "KXBTC15M", "G": "KXGOLD15M", "E": "KXETH15M", "X": "KXXRP15M", "D": "KXDOGE15M", "N": "KXNATGAS15M"}
STUDIES = DATA_DIR.parent / "studies"
SOURCES = ["alts2", "alts3", "alts4", "book", "l1b", "e3b", "fresh"]
MONTHS = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}


def close_utc_from_ticker(tk: str) -> datetime:
    """KXBTC15M-26OCT071415-15: close 2026-10-07 14:15 US Eastern daylight (UTC-4 through Nov 1)."""
    t = tk.split("-")[1]
    local = datetime(2000 + int(t[:2]), MONTHS[t[2:5]], int(t[5:7]), int(t[7:9]), int(t[9:11]), tzinfo=timezone.utc)
    return local + timedelta(hours=4)


def results() -> dict[tuple[str, int], str]:
    out = {}
    for name in SOURCES:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        for s, close_ts, res in db.execute("SELECT series, close_ts, result FROM market"):
            if res in ("yes", "no"):
                out[(s, close_ts)] = res
    return out


def net(side: str, price: float, res: str) -> float:
    fee = 0.07 * price * (1 - price)
    return (1 - price - fee) if side == res else -(price + fee)


def main() -> None:
    res = results()
    fills, nof, unsettled = [], [], 0
    for r in csv.DictReader(open(STUDIES / "live_orders_condensed_2026-10-22.csv")):
        t = datetime.strptime(r["ts"], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
        close = t.replace(minute=0) + timedelta(minutes=(t.minute // 15 + 1) * 15)
        k = (LETTER[r["s"]], int(close.timestamp()))
        if k not in res:
            unsettled += 1
            continue
        fills.append({"day": r["ts"][:10], "series": r["s"], "net": net(r["side"][0] == "y" and "yes" or "no", float(r["price"]), res[k])})
    for r in csv.DictReader(open(STUDIES / "live_nofills_2026-10-22.csv")):
        k = (r["ticker"].split("-")[0], int(close_utc_from_ticker(r["ticker"]).timestamp()))
        if k not in res:
            unsettled += 1
            continue
        nof.append({"day": close_utc_from_ticker(r["ticker"]).strftime("%Y-%m-%d"), "series": r["ticker"][2:3] if False else r["ticker"][2:5], "net": net(r["side"], float(r["price"]), res[k])})
    print(f"fills settled {len(fills)}, no-fills settled {len(nof)}, not settled from public data {unsettled}")
    for name, rows in (("FILLED", fills), ("NO FILL", nof)):
        loss = sum(1 for r in rows if r["net"] < 0)
        print(f"{name}: n={len(rows)}, loss {100*loss/len(rows):.1f}%, mean {100*st.mean(r['net'] for r in rows):+.2f}c a contract (held to settlement at the limit)")
    d = {}
    for tag, rows in (("f", fills), ("n", nof)):
        for r in rows:
            d.setdefault(r["day"], {"f": [], "n": []})[tag].append(r["net"])
    xs = [(k, st.mean(v["f"]) - st.mean(v["n"])) for k, v in d.items() if v["f"] and v["n"]]
    if len(xs) > 1:
        m, _, z = cluster_mean_z(xs)
        print(f"FILLED minus NO FILL per day: {100*m:+.2f}c, day-clustered z {z:+.2f}, {len(xs)} days")


if __name__ == "__main__":
    main()
