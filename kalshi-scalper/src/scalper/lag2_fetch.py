"""LAG2 data fetch (README, Pre-registration: LAG2). Read-only public data, no key. Resumable: re-run after a restart.
  python -m scalper.lag2_fetch kraken     per-second last price of Kraken XBT/USD trades for the days covered by the Bitcoin markets
  python -m scalper.lag2_fetch kalshi     Kalshi's public trades for each Bitcoin market from 150 s to 20 s before the close
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime

from . import api
from .paths import DATA_DIR

DAYS = 12
KRAKEN = DATA_DIR / "lag2_kraken.json"      # {"sec": {epoch second: [last price, quantity]}, "last": cursor}
KALSHI = DATA_DIR / "lag2_kalshi.json"      # {ticker: [[epoch seconds float, yes price, taker outcome side, count], ...]}
FROM_S, TO_S = 150, 38      # a 60 s decision fills no later than 60 - 2 - 20 = 38 s before the close, so later trades are never read


def markets() -> list[tuple]:
    db = sqlite3.connect(DATA_DIR / "fresh.sqlite")
    return db.execute("SELECT ticker, close_ts, strike, result FROM market WHERE series = 'KXBTC15M' AND result IN ('yes','no') ORDER BY close_ts DESC").fetchall()


def fetch_kraken() -> None:
    ms = markets()
    lo, hi = min(m[1] for m in ms) - 1800, max(m[1] for m in ms) + 60
    d = json.load(open(KRAKEN)) if KRAKEN.exists() else {"sec": {}, "last": None}
    cur = d["last"] or str(int(lo * 1e9))
    n = 0
    while True:
        try:
            with urllib.request.urlopen(f"https://api.kraken.com/0/public/Trades?pair=XBTUSD&since={cur}&count=1000", timeout=30) as r:
                j = json.load(r)
        except Exception as e:
            print("retry", e, flush=True)
            time.sleep(5)
            continue
        if j.get("error"):
            print("error", j["error"], flush=True)
            time.sleep(10)
            continue
        res = j["result"]
        tr = res[[k for k in res if k != "last"][0]]
        for p, q, ts, *_ in tr:
            sec = str(int(float(ts)))
            e = d["sec"].get(sec)
            d["sec"][sec] = [float(p), float(q) + (e[1] if e else 0.0)]
        cur = res["last"]
        d["last"] = cur
        n += 1
        if n % 25 == 0:
            json.dump(d, open(KRAKEN, "w"))
            print("kraken", datetime.utcfromtimestamp(float(tr[-1][2])).strftime("%m-%d %H:%M"), len(d["sec"]), flush=True)
        if not tr or float(tr[-1][2]) >= hi:
            break
        time.sleep(1.0)
    json.dump(d, open(KRAKEN, "w"))
    print("done kraken", len(d["sec"]), flush=True)


def fetch_kalshi() -> None:
    ms = markets()
    done = json.load(open(KALSHI)) if KALSHI.exists() else {}
    for i, (tk, close, strike, res) in enumerate(ms):
        if tk in done:
            continue
        out, cur = [], None
        while True:
            p = {"ticker": tk, "limit": 1000, "min_ts": close - FROM_S, "max_ts": close - TO_S}
            if cur:
                p["cursor"] = cur
            try:
                d = api._get("/markets/trades", p)
            except Exception:
                time.sleep(5)
                continue
            for t in d.get("trades", []):
                sec = datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp()
                out.append([sec, float(t["yes_price_dollars"]), t["taker_outcome_side"], float(t["count_fp"])])
            cur = d.get("cursor")
            if not cur or not d.get("trades"):
                break
        done[tk] = out
        if len(done) % 20 == 0:
            json.dump(done, open(KALSHI, "w"))
            print("kalshi", len(done), "of", len(ms), flush=True)
        time.sleep(0.1)
    json.dump(done, open(KALSHI, "w"))
    print("done kalshi", len(done), flush=True)


if __name__ == "__main__":
    {"kraken": fetch_kraken, "kalshi": fetch_kalshi}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
