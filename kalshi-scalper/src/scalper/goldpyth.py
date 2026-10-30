"""GOLDPYTH-H (V2 worker, 2026-10-30): access check for Pyth gold history, the settlement source of KXGOLD15M.

The registered study needed Pyth Metal.Index.1OZGOLD/USD at each minute mark of the last 10 minutes of every gold window
(Aug 6 to Oct 27). This module only checks whether that history can be read without a key. It never sends a key, reads no
environment variable and places nothing. Run: cd kalshi-scalper && PYTHONPATH=src python -m scalper.goldpyth

Result on 2026-10-30: every Pyth price endpoint answered HTTP 401 "unauthorized" (Benchmarks history, Hermes latest and
historical, Hermes beta), for gold and for Bitcoin alike; the TradingView history shim answered 404; the public Pyth Lazer
history service exposes only symbol metadata. Only feed metadata is keyless. So the study is NOT_RUNNABLE.
Kalshi's own market objects carry the Pyth value at each quarter hour (`floor_strike` = previous window's
`expiration_value`), which is not minute resolution inside the window.
"""
from __future__ import annotations

import time
import urllib.error
import urllib.request

GOLD_1OZ_ID = "7fd2c87083dd8fd5af2486a43f40b8e444acd77fda4e96263a53421cd079c387"  # Metal.Index.1OZGOLD/USD, Kalshi's source
XAU_ID = "765d2ba906dbc32ca17cc11f5310a89e9ee1f6420508c63861f2f8ba4ee34bb2"  # Metal.XAU/USD
BTC_ID = "e62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43"  # Crypto.BTC/USD, control
TS = 1793300000  # 2026-10-26, a past instant inside the study period's neighbourhood

PROBES = [
    ("benchmarks history, 1oz gold", f"https://benchmarks.pyth.network/v1/updates/price/{TS}?ids={GOLD_1OZ_ID}&parsed=true"),
    ("benchmarks history, XAU", f"https://benchmarks.pyth.network/v1/updates/price/{TS}?ids={XAU_ID}&parsed=true"),
    ("benchmarks history, BTC (control)", f"https://benchmarks.pyth.network/v1/updates/price/{TS}?ids={BTC_ID}&parsed=true"),
    ("benchmarks tradingview shim", "https://benchmarks.pyth.network/v1/shims/tradingview/history"
                                    f"?symbol=Metal.Index.1OZGOLD%2FUSD&resolution=1&from={TS}&to={TS + 600}"),
    ("hermes historical, 1oz gold", f"https://hermes.pyth.network/v2/updates/price/{TS}?ids[]={GOLD_1OZ_ID}&parsed=true"),
    ("hermes latest, 1oz gold", f"https://hermes.pyth.network/v2/updates/price/latest?ids[]={GOLD_1OZ_ID}&parsed=true"),
    ("hermes latest, BTC (control)", f"https://hermes.pyth.network/v2/updates/price/latest?ids[]={BTC_ID}&parsed=true"),
    ("hermes feed metadata", "https://hermes.pyth.network/v2/price_feeds?query=1OZGOLD"),
    ("lazer history symbols", "https://history.pyth-lazer.dourolabs.app/history/v1/symbols?query=1OZGOLD"),
]


def status(url: str) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": "shwoopnet-research/1"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def main() -> None:
    for name, url in PROBES:
        print(f"{status(url):>4}  {name}")
        time.sleep(1.0)


if __name__ == "__main__":
    main()
