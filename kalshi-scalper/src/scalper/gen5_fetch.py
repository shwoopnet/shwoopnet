"""GEN5 outside data (workers/GEN5_REGISTRATION.md): Yahoo 1 minute GC=F, DX-Y.NYB, ^TNX (last 30 days) and Coinbase BTC-USD 1 minute
candles back to 2026-08-06. Public, keyless. Every bar keyed by its START unix second, value = close.
    python -m scalper.gen5_fetch
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone

from .paths import DATA_DIR

OUT = DATA_DIR / "gen5"
UA = {"User-Agent": "Mozilla/5.0"}


def get(url):
    for i in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001
            print("retry", i, url[:90], e, flush=True); time.sleep(3 + 5 * i)
    raise RuntimeError(url)


def yahoo(sym):
    now = int(time.time()); start = now - 29 * 86400 - 3600
    bars = {}
    t = start
    while t < now:
        e = min(t + 7 * 86400, now)
        d = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1m&period1={t}&period2={e}&includePrePost=true")
        r = d["chart"]["result"][0]
        for ts, c in zip(r.get("timestamp") or [], r["indicators"]["quote"][0]["close"]):
            if c is not None:
                bars[int(ts)] = float(c)
        t = e; time.sleep(1.0)
    OUT.mkdir(exist_ok=True)
    (OUT / f"{sym.replace('^', '').replace('=', '')}.json").write_text(json.dumps({"symbol": sym, "fetched": now, "key": "bar start unix s", "bars": bars}))
    print(sym, len(bars), datetime.fromtimestamp(min(bars), timezone.utc), datetime.fromtimestamp(max(bars), timezone.utc), flush=True)


def coinbase():
    start = int(datetime(2026, 8, 5, 22, tzinfo=timezone.utc).timestamp())
    now = int(time.time()) // 60 * 60
    bars = {}
    t = start
    while t < now:
        e = min(t + 299 * 60, now)
        a = datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"); b = datetime.fromtimestamp(e, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for row in get(f"https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=60&start={a}&end={b}"):
            bars[int(row[0])] = float(row[4])
        t = e + 60; time.sleep(0.35)
    (OUT / "CB_BTCUSD.json").write_text(json.dumps({"symbol": "coinbase BTC-USD", "fetched": now, "key": "bar start unix s", "bars": bars}))
    print("coinbase", len(bars), datetime.fromtimestamp(min(bars), timezone.utc), datetime.fromtimestamp(max(bars), timezone.utc), flush=True)


if __name__ == "__main__":
    for s in ("GC=F", "DX-Y.NYB", "^TNX"):
        yahoo(s)
    coinbase()
