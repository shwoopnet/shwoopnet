"""GAS1-F (README, Pre-registration: GAS1-F): the scout's generic L1 on the AAA gas price series, scored on markets closing from 2026-10-23. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.gas1 look     an INFORMATION look at the days so far (decides nothing; may be repeated)
       python -m scalper.gas1 read     the registered read; refused before 2026-11-22 and refused a second time
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time
from datetime import datetime, timezone

from . import api
from .backfill import iso_ts, parse_candle
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scout import BAND, CENSUS, FRAC, decision_candle, entry_of, net_of

# ---- fixed in the README before any day in the window had closed ----
PREFIX, FROM = "KXAAAGASD", "2026-10-23"
READ_AFTER = "2026-11-22"
MEAN_C, Z_BAR, FALSIFY_C, FALSIFY_Z, MAX_LOSS, MIN_N, MIN_DATES, STRESS = 0.020, 3.0, 0.005, 1.0, 0.05, 300, 30, 1.2
RESULT = DATA_DIR / "gas1_result.txt"


def series_list() -> list[str]:
    return sorted(t for t in json.loads(CENSUS.read_text())["series"] if t.startswith(PREFIX))


def stress_net(side: str, price: float, result: str) -> float:
    f = 0.07 * price * (1 - price) * STRESS
    return (1.0 if side == result else 0.0) - price - f


def entries(series: str, lo: int, hi: int) -> list[dict]:
    """Entries of one series for markets closing in [lo, hi]: the scout's rule, one decision per market."""
    ms = [m for m in api.settled_markets(series, lo, hi) if m.get("result") in ("yes", "no")]
    todo = sorted(ms, key=lambda m: m["close_time"])
    rows, step, i = [], 20, 0
    while i < len(todo):
        chunk = todo[i:i + step]
        o, c = min(iso_ts(m["open_time"]) for m in chunk), max(iso_ts(m["close_time"]) for m in chunk)
        try:
            got = api._get("/markets/candlesticks", {"market_tickers": ",".join(m["ticker"] for m in chunk), "start_ts": o, "end_ts": c, "period_interval": 60})
            cmap = {x.get("market_ticker"): x.get("candlesticks", []) for x in got.get("markets", [])}
        except Exception:
            if step > 1:
                step = max(1, step // 2)
                continue
            cmap = {}
        for m in chunk:
            cs = [parse_candle(x, m["ticker"], series) for x in cmap.get(m["ticker"], [])]
            cs = [(r[2], r[6], r[10]) for r in cs if r]
            dc = decision_candle(cs, iso_ts(m["open_time"]), iso_ts(m["close_time"]))
            en = entry_of(dc) if dc else None
            if en:
                rows.append({"date": m["close_time"][:10], "series": series, "net": net_of(en[0], en[1], m["result"]), "stress": stress_net(en[0], en[1], m["result"]),
                             "loss": 1 if en[0] != m["result"] else 0, "price": en[1]})
        i += len(chunk)
        time.sleep(0.3)
    return rows


def judge(rows: list[dict], dates_ok: bool = True) -> dict:
    n, dates = len(rows), sorted({r["date"] for r in rows})
    if n < 2:
        return {"verdict": "NOT_ENOUGH_DATA", "n": n, "dates": len(dates)}
    m, _, z = cluster_mean_z([(r["date"], r["net"]) for r in rows])
    mid = dates[len(dates) // 2]
    h1 = [r["net"] for r in rows if r["date"] < mid]
    h2 = [r["net"] for r in rows if r["date"] >= mid]
    ms = st.mean(r["stress"] for r in rows)
    loss = sum(r["loss"] for r in rows) / n
    if n < MIN_N or len(dates) < MIN_DATES:
        verdict = "NOT_ENOUGH_DATA"
    elif m >= MEAN_C and z >= Z_BAR and loss < MAX_LOSS and h1 and h2 and st.mean(h1) > 0 and st.mean(h2) > 0 and ms > 0:
        verdict = "NOT_YET_FALSIFIED"
    elif m < FALSIFY_C or z < FALSIFY_Z:
        verdict = "FALSIFIED"
    else:
        verdict = "NOT_ENOUGH_DATA"
    return {"verdict": verdict, "n": n, "dates": len(dates), "mean_c": 100 * m, "z": z, "loss_pct": 100 * loss, "stress_c": 100 * ms,
            "halves_c": (100 * st.mean(h1) if h1 else None, 100 * st.mean(h2) if h2 else None), "mean_price_c": 100 * st.mean(r["price"] for r in rows)}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] not in ("look", "read"):
        print(__doc__)
        return
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if argv[1] == "read":
        if today < READ_AFTER:
            print(f"Refusing the registered read: it is {today} and the read opens on {READ_AFTER}.")
            return
        if RESULT.exists():
            print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
            return
    lo = int(datetime.strptime(FROM, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
    hi = int(time.time())
    rows = []
    for s in series_list():
        rows += entries(s, lo, hi)
    out = [("REGISTERED READ" if argv[1] == "read" else "INFORMATION LOOK, NOT THE REGISTERED READ (decides nothing)") + f": {len(series_list())} series, markets closing {FROM} to {today}",
           json.dumps(judge(rows), default=str)]
    if argv[1] == "read":
        RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
