#!/usr/bin/env python3
"""Records Kalshi's 15 minute crypto quotes next to the spot prices of three exchanges, in the last seconds of each window (research only, 2026-10-22).

Why it exists: the research session's RECORD1 asks whether Kalshi's quotes lag the spot index in the last two minutes of a window, which one minute candles cannot show.
Spec: kalshi-scalper/studies/RECORDER_SPEC_2026-10-22.md on the research branch. This is a PILOT: its job is to find out how many windows a free GitHub runner can actually catch
(Kalshi's public read limit, late scheduled jobs) before anyone commits to 14 days.

It reads PUBLIC data only: Kalshi's market list (no key, no login) and the public trade feeds of Coinbase, Kraken and Bitstamp. It places no order and holds no secret.
It writes files and nothing else. One request returns all five markets at once (`/markets?tickers=a,b,c`), so the Kalshi read rate is about 2 a second, well under the limit.

Usage: python3 scripts/record_quotes.py OUT_DIR [--minutes N] [--quote-lead S] [--spot-lead S]
  OUT_DIR gets quotes.csv, spot.csv, results.csv, coverage.csv and clock.csv. The run stops at the first quiet moment after N minutes, or at the top of the next hour.
"""
import argparse
import asyncio
import calendar
import csv
import json
import os
import socket
import struct
import sys
import time
import urllib.error
import urllib.request

BASE = "https://external-api.kalshi.com/trade-api/v2"
SERIES = {"KXBTC15M": "BTC", "KXETH15M": "ETH", "KXSOL15M": "SOL", "KXXRP15M": "XRP", "KXDOGE15M": "DOGE"}
WINDOW_S = 900            # markets close on the quarter hour and the epoch starts on one
DISCOVER_LEAD_S = 190     # look the open tickers up this long before the close
QUOTE_LEAD_S = 150
SPOT_LEAD_S = 600
POLL_EVERY_S = 0.5
UA = {"User-Agent": "shwoopnet-research-recorder"}

QUOTE_COLS = ["t_send_ms", "t_recv_ms", "ticker", "yes_bid", "yes_ask", "bid_size", "ask_size", "strike", "status"]
SPOT_COLS = ["t_recv_ms", "exchange", "asset", "price", "size", "exchange_time"]
RESULT_COLS = ["ticker", "result", "close_time", "seen_ms"]
COVER_COLS = ["window_close_utc", "ticker", "polls", "ok_polls", "n429", "rows", "first_recv_ms", "last_recv_ms"]
CLOCK_COLS = ["t_local_ms", "offset_ms"]


def seconds_to_close(now):
    """Seconds until the next quarter hour (900 right on a boundary: the new window has just opened)."""
    return WINDOW_S - (now % WINDOW_S)


def next_close(now):
    return now - (now % WINDOW_S) + WINDOW_S


def num(x):
    return x if x not in (None, "") else ""


def quote_rows(markets, t_send_ms, t_recv_ms):
    out = []
    for m in markets or []:
        out.append([t_send_ms, t_recv_ms, m.get("ticker", ""), num(m.get("yes_bid_dollars")), num(m.get("yes_ask_dollars")), num(m.get("yes_bid_size_fp")),
                    num(m.get("yes_ask_size_fp")), num(m.get("floor_strike", m.get("cap_strike"))), m.get("status", "")])
    return out


# Each parser takes one decoded websocket message and returns a list of (asset, price, size, exchange_time), or [] for anything that is not a trade.
def parse_coinbase(msg):
    if not isinstance(msg, dict) or msg.get("type") != "ticker" or not msg.get("price"):
        return []
    asset = str(msg.get("product_id", "")).split("-")[0]
    return [(asset, msg["price"], msg.get("last_size", ""), msg.get("time", ""))] if asset in SERIES_ASSETS else []


KRAKEN_NAMES = {"XBT": "BTC", "XDG": "DOGE", "BTC": "BTC", "ETH": "ETH", "SOL": "SOL", "XRP": "XRP", "DOGE": "DOGE"}


def parse_kraken(msg):
    if not isinstance(msg, list) or len(msg) < 4 or msg[-2] != "trade" or not isinstance(msg[1], list):
        return []
    asset = KRAKEN_NAMES.get(str(msg[-1]).split("/")[0])
    if asset not in SERIES_ASSETS:
        return []
    return [(asset, t[0], t[1], t[2]) for t in msg[1] if isinstance(t, list) and len(t) >= 3]


def parse_bitstamp(msg):
    if not isinstance(msg, dict) or msg.get("event") != "trade" or not isinstance(msg.get("data"), dict):
        return []
    ch = str(msg.get("channel", ""))
    asset = ch.replace("live_trades_", "")[:-3].upper()
    d = msg["data"]
    return [(asset, d.get("price_str", d.get("price", "")), d.get("amount_str", d.get("amount", "")), d.get("microtimestamp", ""))] if asset in SERIES_ASSETS and d.get("price", d.get("price_str")) is not None else []


SERIES_ASSETS = set(SERIES.values())


def sntp_offset_ms(host="time.cloudflare.com", timeout=3.0):
    """How far this machine's clock is from a network time server, in ms (positive: the server is ahead). Blank on any failure."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        t0 = time.time()
        s.sendto(b"\x1b" + 47 * b"\0", (host, 123))
        data, _ = s.recvfrom(48)
        t3 = time.time()
        secs, frac = struct.unpack("!II", data[40:48])
        server = secs - 2208988800 + frac / 2 ** 32
        return round((server - (t0 + t3) / 2) * 1000)
    except Exception:
        return ""


def http_get(url):
    """(status, decoded json or None). Never raises: a failed read is a status, so one bad second cannot end the run."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=10) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


class Out:
    def __init__(self, d):
        os.makedirs(d, exist_ok=True)
        self.files, self.writers = [], {}
        for name, cols in (("quotes", QUOTE_COLS), ("spot", SPOT_COLS), ("results", RESULT_COLS), ("coverage", COVER_COLS), ("clock", CLOCK_COLS)):
            f = open(os.path.join(d, name + ".csv"), "a", newline="")
            w = csv.writer(f)
            if f.tell() == 0:
                w.writerow(cols)
            self.files.append(f)
            self.writers[name] = w

    def write(self, name, rows):
        self.writers[name].writerows(rows)

    def flush(self):
        for f in self.files:
            f.flush()

    def close(self):
        self.flush()
        for f in self.files:
            f.close()


class Recorder:
    def __init__(self, out, quote_lead, spot_lead):
        self.out, self.quote_lead, self.spot_lead = out, quote_lead, spot_lead
        self.pending = {}          # ticker -> close_time, waiting for its result
        self.spot_rows = 0

    def spot(self, exchange, parsed):
        now = time.time()
        if seconds_to_close(now) > self.spot_lead:
            return
        ms = int(now * 1000)
        for asset, price, size, ts in parsed:
            self.out.write("spot", [[ms, exchange, asset, price, size, ts]])
            self.spot_rows += 1

    async def discover(self, close):
        """The open market of each series that closes at `close`. A series whose read is refused is simply missing from this window."""
        loop = asyncio.get_running_loop()
        found = {}
        for series in SERIES:
            for attempt in range(3):
                st, d = await loop.run_in_executor(None, http_get, "%s/markets?series_ticker=%s&status=open&limit=5" % (BASE, series))
                if st == 200 and d:
                    for m in d.get("markets") or []:
                        if m.get("close_time", "").startswith(time.strftime("%Y-%m-%dT%H:%M", time.gmtime(close))):
                            found[m["ticker"]] = m.get("close_time", "")
                    break
                await asyncio.sleep(1.5 * (attempt + 1))
            await asyncio.sleep(0.3)
        return found

    async def poll_window(self, close, tickers):
        loop = asyncio.get_running_loop()
        cover = {t: [0, 0, 0, 0, "", ""] for t in tickers}     # polls, ok, n429, rows, first, last
        url = "%s/markets?tickers=%s" % (BASE, ",".join(tickers))
        backoff = 0.0
        while time.time() < close:
            t_send = int(time.time() * 1000)
            st, d = await loop.run_in_executor(None, http_get, url)
            t_recv = int(time.time() * 1000)
            for t in tickers:
                cover[t][0] += 1
            if st == 200 and d:
                backoff = 0.0
                rows = quote_rows(d.get("markets"), t_send, t_recv)
                self.out.write("quotes", rows)
                for r in rows:
                    c = cover.get(r[2])
                    if c is not None:
                        c[1] += 1; c[3] += 1; c[4] = c[4] or t_recv; c[5] = t_recv
            elif st == 429:
                for t in tickers:
                    cover[t][2] += 1
                backoff = min(4.0, max(1.0, backoff * 2))      # the limit is the thing under test: ask less, never harder
            await asyncio.sleep(POLL_EVERY_S + backoff)
        for t, c in cover.items():
            self.out.write("coverage", [[time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(close)), t] + c])
        self.out.flush()

    async def window_loop(self, stop_at):
        while True:
            now = time.time()
            close = next_close(now)
            if now >= stop_at and seconds_to_close(now) > self.spot_lead:
                return
            wait = (close - now) - max(DISCOVER_LEAD_S, self.quote_lead + 20)
            if wait > 0:
                await asyncio.sleep(min(wait, 30))
                continue
            found = await self.discover(close)
            self.pending.update(found)
            wait = (close - time.time()) - self.quote_lead
            if wait > 0:
                await asyncio.sleep(wait)
            if found and time.time() < close:
                await self.poll_window(close, sorted(found))
            else:
                self.out.write("coverage", [[time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(close)), "(none found)", 0, 0, 0, 0, "", ""]])
            await asyncio.sleep(1.0)

    async def result_loop(self, stop_at):
        loop = asyncio.get_running_loop()
        tries = {}
        while True:
            await asyncio.sleep(20)
            due = [t for t, c in self.pending.items() if c and calendar_ts(c) + 75 < time.time()]
            if due:
                st, d = await loop.run_in_executor(None, http_get, "%s/markets?tickers=%s" % (BASE, ",".join(due[:20])))
                got = {m["ticker"]: m for m in (d or {}).get("markets", [])} if st == 200 else {}
                for t in due[:20]:
                    tries[t] = tries.get(t, 0) + 1
                    m = got.get(t)
                    if m and m.get("result") in ("yes", "no"):
                        self.out.write("results", [[t, m["result"], m.get("close_time", ""), int(time.time() * 1000)]])
                        self.pending.pop(t, None)
                    elif tries[t] > 30:
                        self.pending.pop(t, None)
                self.out.flush()
            if time.time() >= stop_at + 120 and not self.pending or time.time() >= stop_at + 300:
                return

    async def clock_loop(self, stop_at):
        loop = asyncio.get_running_loop()
        while time.time() < stop_at:
            off = await loop.run_in_executor(None, sntp_offset_ms)
            self.out.write("clock", [[int(time.time() * 1000), off]])
            await asyncio.sleep(1800)


def calendar_ts(iso):
    return calendar.timegm(time.strptime(iso, "%Y-%m-%dT%H:%M:%SZ"))


async def ws_loop(name, url, subscribe, parse, rec, stop_at):
    """One exchange's public trade feed, kept alive until the run ends. A drop reconnects after a pause; nothing here can raise out of the task."""
    import websockets
    pause = 1.0
    while time.time() < stop_at + 60:
        try:
            async with websockets.connect(url, open_timeout=15, ping_interval=20) as ws:
                for m in subscribe:
                    await ws.send(json.dumps(m))
                pause = 1.0
                async for raw in ws:
                    if time.time() > stop_at + 60:
                        break
                    try:
                        parsed = parse(json.loads(raw))
                    except Exception:
                        continue
                    if parsed:
                        rec.spot(name, parsed)
        except Exception as e:
            print("%s feed dropped: %s" % (name, str(e)[:100]), flush=True)
        await asyncio.sleep(pause)
        pause = min(30.0, pause * 2)


FEEDS = [
    ("coinbase", "wss://ws-feed.exchange.coinbase.com",
     [{"type": "subscribe", "product_ids": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD"], "channels": ["ticker"]}], parse_coinbase),
    ("kraken", "wss://ws.kraken.com",
     [{"event": "subscribe", "pair": ["XBT/USD", "ETH/USD", "SOL/USD", "XRP/USD", "XDG/USD"], "subscription": {"name": "trade"}}], parse_kraken),
    ("bitstamp", "wss://ws.bitstamp.net",
     [{"event": "bts:subscribe", "data": {"channel": "live_trades_" + p}} for p in ("btcusd", "ethusd", "solusd", "xrpusd", "dogeusd")], parse_bitstamp),
]


def stop_time(minutes, now):
    """Stop at `minutes` from now, but never later than the top of the next hour, where the next scheduled run takes over."""
    return min(now + minutes * 60, now - (now % 3600) + 3600 + 60)


async def run(out_dir, minutes, quote_lead, spot_lead):
    out = Out(out_dir)
    rec = Recorder(out, quote_lead, spot_lead)
    stop_at = stop_time(minutes, time.time())
    tasks = [asyncio.create_task(ws_loop(n, u, s, p, rec, stop_at)) for n, u, s, p in FEEDS]
    tasks += [asyncio.create_task(rec.window_loop(stop_at)), asyncio.create_task(rec.result_loop(stop_at)), asyncio.create_task(rec.clock_loop(stop_at))]
    ticker = asyncio.create_task(flusher(out, stop_at))
    await asyncio.gather(tasks[3], tasks[4], tasks[5])
    for t in tasks[:3] + [ticker]:
        t.cancel()
    out.close()
    print("done: %d spot rows" % rec.spot_rows)


async def flusher(out, stop_at):
    while True:
        await asyncio.sleep(5)
        out.flush()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--minutes", type=float, default=58)
    ap.add_argument("--quote-lead", type=float, default=QUOTE_LEAD_S)
    ap.add_argument("--spot-lead", type=float, default=SPOT_LEAD_S)
    a = ap.parse_args(argv)
    asyncio.run(run(a.out_dir, a.minutes, a.quote_lead, a.spot_lead))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
