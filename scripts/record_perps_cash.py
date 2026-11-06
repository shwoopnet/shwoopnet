#!/usr/bin/env python3
"""Saves Yahoo's 1 minute prices for the stocks, ETFs, indexes and commodities behind Kalshi's perpetual markets (research only, 2026-11-06).

Why (V2's request, Nov 6, 2026, after Kalshi listed single stock perps): the open, close and overnight gap tests compare a perp with the thing it tracks, and Yahoo keeps only about 7 days of 1 minute
bars, so unless they are copied now the stock side of every test is lost. The first run asks for the 7 day backfill; later runs ask for 2 days (overlap is deliberate, dedupe on timestamp downstream).
One plain GET of a public page per symbol: no key, no login, no order. It writes files and nothing else.

Symbols come from the public perps list: equities and ETFs by their title (BRK.B becomes BRK-B), indexes by a fixed map (US500 ^GSPC, US Tech 100 ^NDX, US 2000 ^RUT), commodities by a fixed map
(futures), plus the three index futures (ES=F, NQ=F, RTY=F) because the cash indexes are shut overnight. Pre and post market bars are included. It stops by itself after STOP_DATE.

Usage: python3 scripts/record_perps_cash.py OUT_DIR      (writes OUT_DIR/<UTC date>.csv.gz; a second start the same day does nothing)
"""
import csv
import datetime as dt
import gzip
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import quote

PERPS_URL = "https://external-api.kalshi.com/trade-api/v2/margin/markets?limit=200"
HOSTS = ("query2.finance.yahoo.com", "query1.finance.yahoo.com")
STOP_DATE = dt.date(2027, 2, 26)
PAUSE_S = 0.4
COLUMNS = ["ts_unix", "symbol", "open", "high", "low", "close", "volume"]
FIXED = {"US500": "^GSPC", "US Tech 100": "^NDX", "US 2000": "^RUT", "Gold": "GC=F", "Silver": "SI=F", "Copper": "HG=F", "Platinum": "PL=F",
         "Palladium": "PA=F", "Aluminum": "ALI=F", "WTI Crude Oil": "CL=F"}
EXTRA = ("ES=F", "NQ=F", "RTY=F")


def symbols_from(markets):
    """The Yahoo symbols for a perps list. Crypto is skipped (it trades around the clock on its own feeds); an unknown title is passed through as is, so a wrong one is a counted failed read, not a value."""
    out = []
    for m in markets:
        if m.get("asset_class") == "Crypto":
            continue
        t = str(m.get("title") or "").strip()
        s = FIXED.get(t) or t.replace(".", "-")
        if s and s not in out:
            out.append(s)
    for s in EXTRA:
        if s not in out:
            out.append(s)
    return out


def chart_url(symbol, rng, host):
    return "https://%s/v8/finance/chart/%s?interval=1m&range=%s&includePrePost=true" % (host, quote(symbol), rng)


def parse_bars(body):
    """[[ts, symbol, o, h, l, c, v], ...] for every bar with a close. A body that is not a chart returns [] (a counted failure), never a made-up value."""
    try:
        res = json.loads(body)["chart"]["result"][0]
        ts = res["timestamp"]
        q = res["indicators"]["quote"][0]
        sym = res["meta"]["symbol"]
    except (ValueError, KeyError, IndexError, TypeError):
        return []
    out = []
    for i, t in enumerate(ts):
        try:
            c = q["close"][i]
            if c is None:
                continue
            g = lambda k: ("" if q.get(k) is None or q[k][i] is None else q[k][i])
            out.append([int(t), sym, g("open"), g("high"), g("low"), c, g("volume")])
        except (IndexError, KeyError, TypeError):
            continue
    return out


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (shwoopnet-research-recorder)"})
    return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")


def read_symbol(symbol, rng, get=http_get, sleep=time.sleep):
    """Two hosts, one retry after a 429 (the same service answers 429 on one host when the other is fine, seen Nov 4, 2026)."""
    last = ""
    for host in HOSTS:
        for attempt in range(2):
            try:
                return parse_bars(get(chart_url(symbol, rng, host)))
            except urllib.error.HTTPError as e:
                last = "HTTP %s" % e.code
                if e.code == 429 and attempt == 0:
                    sleep(3)
                    continue
                break
            except Exception as e:
                last = str(e)[:60]
                break
    print("read failed for %s: %s" % (symbol, last))
    return []


def main(out_dir, today=None, get_perps=None, get=http_get, sleep=time.sleep):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    if today > STOP_DATE:
        print("past the stop date; nothing recorded")
        return 0
    path = os.path.join(out_dir, today.isoformat() + ".csv.gz")
    if os.path.exists(path):
        print("today's file is already recorded; nothing to do")
        return 0
    get_perps = get_perps or (lambda: json.loads(get(PERPS_URL)).get("markets") or [])
    markets = get_perps()
    if not markets:
        print("no perps list; nothing written")
        return 1
    first = not (os.path.isdir(out_dir) and any(f.endswith(".csv.gz") for f in os.listdir(out_dir)))
    rng = "7d" if first else "2d"
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(COLUMNS)
    syms = symbols_from(markets)
    ok = rows = 0
    for s in syms:
        bars = read_symbol(s, rng, get, sleep)
        if bars:
            ok += 1
            rows += len(bars)
            w.writerows(bars)
        sleep(PAUSE_S)
    if ok < len(syms) // 2:
        print("only %d of %d symbols read; nothing written (a later start will retry)" % (ok, len(syms)))
        return 1
    os.makedirs(out_dir, exist_ok=True)
    with gzip.open(path, "wt", newline="") as f:
        f.write(buf.getvalue())
    print("wrote %d bars for %d of %d symbols (range %s) to %s" % (rows, ok, len(syms), rng, path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "cash1m"))
