"""LAG2 data fetch (README, Pre-registration: LAG2). Read-only public data, no key. Resumable: re-run after a restart.
  python -m scalper.lag2_fetch kraken     per-second last price of Kraken XBT/USD trades for the days covered by the Bitcoin markets
  python -m scalper.lag2_fetch kalshi [N k]   Kalshi's public trades for each Bitcoin market from 150 s to 20 s before the close
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


def shard_path(k: int):
    return DATA_DIR / f"lag2_kalshi_{k}.json"


def load_tape() -> dict:
    """Every shard written by `kalshi N k` plus the original single file."""
    out = json.load(open(KALSHI)) if KALSHI.exists() else {}
    for f in sorted(DATA_DIR.glob("lag2_kalshi_*.json")):
        out.update(json.load(open(f)))
    return out


def fetch_kalshi(n_shards: int = 1, shard: int = 0) -> None:
    """Shard k of n takes the markets whose position in the list is k modulo n, and writes its own file, so shards never touch each other's data."""
    ms = [m for i, m in enumerate(markets()) if i % n_shards == shard]
    path = shard_path(shard) if n_shards > 1 else KALSHI
    have = load_tape()
    done = json.load(open(path)) if path.exists() else {}
    for i, (tk, close, strike, res) in enumerate(ms):
        if tk in done or tk in have:
            continue
        out, cur = [], None
        while True:
            p = {"ticker": tk, "limit": 1000, "min_ts": close - FROM_S, "max_ts": close - TO_S}
            if cur:
                p["cursor"] = cur
            try:
                d = api._get("/markets/trades", p)
            except Exception as e:
                print("retry", str(e)[:80], flush=True)
                time.sleep(5)
                continue
            for t in d.get("trades", []):
                sec = datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp()
                out.append([sec, float(t["yes_price_dollars"]), t["taker_outcome_side"], float(t["count_fp"])])
            cur = d.get("cursor")
            if not cur or not d.get("trades"):
                break
        done[tk] = out
        if len(done) % 5 == 0:
            json.dump(done, open(path, "w"))
            print("kalshi", shard, len(done), "of", len(ms), flush=True)
        time.sleep(0.1)
    json.dump(done, open(path, "w"))
    print("done kalshi", shard, len(done), flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["kalshi"]:
        fetch_kalshi(*(int(x) for x in a[1:3]))
    elif a[:1] == ["kraken"]:
        fetch_kraken()
    else:
        print(__doc__)
