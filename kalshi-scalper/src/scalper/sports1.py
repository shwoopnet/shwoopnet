"""F6 and F7 (README, Pre-registration: F6 and F7): pre-game favourites in tennis and the under in game totals. Research only: nothing here places an order.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

    python -m scalper.sports1 fetch    (resumable; game-total ladders, settled in the last 45 days, candles 8 to 5 hours before each close, into data/sports1.sqlite)
    python -m scalper.sports1 run      (the one read of F6 (from data/sc1.sqlite) and F7; refused a second time)
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

DB = DATA_DIR / "sports1.sqlite"
SC1_DB = DATA_DIR / "sc1.sqlite"
RESULT = DATA_DIR / "sports1_result.txt"
TOTALS = ("KXNBATOTAL", "KXNFLTOTAL", "KXNHLTOTAL", "KXNBA1HTOTAL", "KXNFL1HTOTAL")
DAYS = 45
PRE_FROM, PRE_TO = 8 * 3600, 5 * 3600           # the pre-game quote is the last candle in [close - 8h, close - 5h]
MAX_SPREAD = 0.03
F6_BAND, F7_BAND = (0.75, 0.95), (0.40, 0.60)
F6_MIN, F7_MIN, MIN_DAYS, BAR_C, BAR_Z, STRESS = 500, 1000, 25, 0.010, 2.5, 1.2
PAUSE = 0.3


def fee(p: float, mult: float = 1.0) -> float:
    return mult * 0.07 * p * (1 - p)


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(backfill.SCHEMA)
    have = {r[0] for r in db.execute("SELECT ticker FROM market")}
    now = int(time.time())
    for series in TOTALS:
        listed = [m for m in api.settled_markets(series, now - DAYS * 86400, now) if m.get("result") in ("yes", "no") and m["ticker"] not in have]
        print(f"{series}: {len(listed)} to fetch", flush=True)
        by_hour = defaultdict(list)
        for m in listed:
            c = backfill.iso_ts(m.get("close_time"))
            if c:
                by_hour[c // 3600].append((m, c))
        for hour in sorted(by_hour):
            items = by_hour[hour]
            for i in range(0, len(items), 50):
                batch = items[i:i + 50]
                lo, hi = min(c for _, c in batch) - PRE_FROM, max(c for _, c in batch) - PRE_TO
                got = api.batch_candlesticks([m["ticker"] for m, _ in batch], lo, hi)
                for m, c in batch:
                    t = m["ticker"]
                    rows = [r for r in (backfill.parse_candle(x, t, series) for x in got.get(t, [])) if r and c - PRE_FROM <= r[2] <= c - PRE_TO]
                    db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
                    db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)", (t, series, backfill.iso_ts(m.get("open_time")), c, m.get("result"), m.get("floor_strike"), len(rows)))
                db.commit()
                time.sleep(PAUSE)
        print(f"  {series} done", flush=True)


def pre_quote(candles: list[tuple], close: int):
    """Last (bid, ask) closing quote with both sides in [close - 8h, close - 5h], else None."""
    ok = [c for c in candles if close - PRE_FROM <= c[0] <= close - PRE_TO and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1]
    return (ok[-1][1], ok[-1][2]) if ok else None


def judge(name: str, rows: list[dict], min_n: int) -> str:
    if len(rows) < 5:
        return f"{name}: {len(rows)} trades"
    rows = sorted(rows, key=lambda r: r["t"])
    days = len({r["day"] for r in rows})
    m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    h = len(rows) // 2
    h1, h2 = st.mean(r["net"] for r in rows[:h]), st.mean(r["net"] for r in rows[h:])
    s = st.mean(r["stress"] for r in rows)
    ok = len(rows) >= min_n and days >= MIN_DAYS and m >= BAR_C and z >= BAR_Z and h1 > 0 and h2 > 0 and s > 0
    verdict = "NOT_YET_FALSIFIED" if ok else ("NOT_ENOUGH_DATA" if (len(rows) < min_n or days < MIN_DAYS) else "FALSIFIED")
    win = sum(r["won"] for r in rows) / len(rows)
    return f"{name}: {verdict:18s} n={len(rows):5d} days={days:3d} net {100*m:+6.2f}c z {z:+5.2f} halves {100*h1:+5.2f}/{100*h2:+5.2f} stress {100*s:+6.2f}c win {100*win:4.1f}% vs price {st.mean(r['price'] for r in rows):.3f}"


def f6() -> list[str]:
    db = sqlite3.connect(SC1_DB)
    meta = {t: (s, c, r) for t, s, c, r in db.execute("SELECT ticker, series, close_ts, result FROM market")}
    by = defaultdict(list)
    for tk, end, bc, ac in db.execute("SELECT ticker, end_ts, bid_c, ask_c FROM candle ORDER BY ticker, end_ts"):
        by[tk].append((end, bc, ac))
    ev = defaultdict(list)
    dropped = 0
    for tk, (s, close, res) in meta.items():
        q = pre_quote(by.get(tk, []), close)
        if q is None:
            dropped += 1
            continue
        ev[tk.rsplit("-", 1)[0]].append((tk, q, close, res))
    rows = {"fav": [], "mid": [], "dog": []}
    for e, ms in ev.items():
        if len(ms) != 2:
            continue
        tk, (b, a), close, res = max(ms, key=lambda x: (x[1][0] + x[1][1]) / 2)
        for name, band in (("fav", F6_BAND), ("mid", (0.55, 0.75))):
            if a - b <= MAX_SPREAD and band[0] <= a < band[1]:
                yes = res == "yes"
                rows[name].append({"day": datetime.fromtimestamp(close, timezone.utc).strftime("%Y-%m-%d"), "t": close, "net": (1.0 if yes else 0.0) - a - fee(a),
                                   "stress": (1.0 if yes else 0.0) - a - fee(a, STRESS), "won": yes, "price": a})
        tk2, (b2, a2), close2, res2 = min(ms, key=lambda x: (x[1][0] + x[1][1]) / 2)
        if a2 - b2 <= MAX_SPREAD and a2 < 0.35:
            yes = res2 == "yes"
            rows["dog"].append({"day": datetime.fromtimestamp(close2, timezone.utc).strftime("%Y-%m-%d"), "t": close2, "net": (1.0 if yes else 0.0) - a2 - fee(a2),
                                "stress": (1.0 if yes else 0.0) - a2 - fee(a2, STRESS), "won": yes, "price": a2})
    return [f"F6 tennis ({len(meta)} markets, {dropped} without a pre-match quote)", judge("F6 favourite 0.75-0.95", rows["fav"], F6_MIN),
            "  information: " + judge("favourite 0.55-0.75", rows["mid"], F6_MIN), "  information: " + judge("underdog under 0.35", rows["dog"], F6_MIN)]


def f7() -> list[str]:
    db = sqlite3.connect(DB)
    meta = {t: (s, c, r) for t, s, c, r in db.execute("SELECT ticker, series, close_ts, result FROM market")}
    by = defaultdict(list)
    for tk, end, bc, ac in db.execute("SELECT ticker, end_ts, bid_c, ask_c FROM candle ORDER BY ticker, end_ts"):
        by[tk].append((end, bc, ac))
    no_rows, yes_rows = [], []
    per = defaultdict(list)
    dropped = 0
    for tk, (s, close, res) in meta.items():
        q = pre_quote(by.get(tk, []), close)
        if q is None:
            dropped += 1
            continue
        b, a = q
        if a - b > MAX_SPREAD or not (F7_BAND[0] <= (b + a) / 2 < F7_BAND[1]):
            continue
        yes = res == "yes"
        day = datetime.fromtimestamp(close, timezone.utc).strftime("%Y-%m-%d")
        pn = round(1 - b, 4)
        rn = {"day": day, "t": close, "net": (0.0 if yes else 1.0) - pn - fee(pn), "stress": (0.0 if yes else 1.0) - pn - fee(pn, STRESS), "won": not yes, "price": pn}
        ry = {"day": day, "t": close, "net": (1.0 if yes else 0.0) - a - fee(a), "stress": (1.0 if yes else 0.0) - a - fee(a, STRESS), "won": yes, "price": a}
        no_rows.append(rn)
        yes_rows.append(ry)
        per[s].append(rn)
    out = [f"F7 totals ({len(meta)} markets, {dropped} without a pre-game quote)", judge("F7 buy NO (the under), YES mid 0.40-0.60", no_rows, F7_MIN), "  information: " + judge("buy YES (the over)", yes_rows, F7_MIN)]
    for s, rs in sorted(per.items()):
        out.append("  information: " + judge(f"under, {s}", rs, F7_MIN))
    return out


def run() -> None:
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists.")
        return
    out = f6() + f7()
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
