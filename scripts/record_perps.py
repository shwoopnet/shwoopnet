#!/usr/bin/env python3
"""Appends one hourly sample of Kalshi's public perpetual markets to a CSV (research only, 2026-10-21).

Why it exists: the research session's FUND1 test (crypto cash-and-carry) passed on Hyperliquid's history, but that venue is not available to US persons and Kalshi's perps API has no historical
endpoints, so the only way to get Kalshi perp history is to record it from now. This reads PUBLIC market data with a plain GET: no key, no login, no order. It writes a file and nothing else.

The public market object carries no funding-rate field, so the inputs of the funding premium are kept instead: the traded price, the reference (index) price, the settlement and liquidation marks, the
top of the book, open interest, 24 hour volume, and the venue's funding cap and deadband. The premium (price over reference minus 1) can be rebuilt from them later.

Usage: python3 scripts/record_perps.py OUT_DIR      (appends to OUT_DIR/perps-YYYY-MM-DD.csv, creating it with a header)
"""
import csv
import json
import os
import sys
import time
import urllib.request

URL = "https://external-api.kalshi.com/trade-api/v2/margin/markets?limit=200"
COLUMNS = ["ts_utc", "ticker", "asset_class", "status", "bid", "ask", "bid_size", "ask_size", "price", "reference_price", "settlement_mark", "liquidation_mark",
           "open_interest", "volume_24h", "notional_oi_usd", "funding_cap", "funding_deadband"]


def num(x):
    return x if x not in (None, "") else ""


def mark(m, key):
    v = m.get(key)
    return v.get("price", "") if isinstance(v, dict) else num(v)


def rows(markets, ts):
    out = []
    for m in markets:
        out.append([ts, m.get("ticker", ""), m.get("asset_class", ""), m.get("status", ""), num(m.get("bid")), num(m.get("ask")), num(m.get("bid_size_fp")), num(m.get("ask_size_fp")),
                    num(m.get("price")), mark(m, "reference_price"), mark(m, "settlement_mark_price"), mark(m, "liquidation_mark_price"), num(m.get("open_interest")),
                    num(m.get("volume_24h")), num(m.get("open_interest_notional_value_dollars")), num(m.get("funding_cap")), num(m.get("funding_deadband"))])
    return out


def main(out_dir):
    req = urllib.request.Request(URL, headers={"User-Agent": "shwoopnet-research-recorder"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    markets = data.get("markets") or []
    if not markets:
        print("no markets returned; nothing written")
        return 1
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "perps-" + ts[:10] + ".csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(COLUMNS)
        w.writerows(rows(markets, ts))
    print("wrote %d markets to %s" % (len(markets), path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "perp-data"))
