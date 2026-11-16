#!/usr/bin/env python3
"""Perps live recorder (Nov 16, 2026, the Head's order, research only; needs the owner's popup before it is merged because of its runner minutes). What Kalshi's PUBLIC perps (margin) API
shows only LIVE and cannot back-serve: every 60 seconds (1) the perps list, one request for all markets (bid, ask, sizes, last price, reference price, settlement and liquidation marks,
open interest, 24 hour volume, leverage estimate and the long and short leverage estimates at each notional size; the static fields (contract size, tick, funding cap, schedule and so on) once per job in static.csv), and (2) the order books of the active markets, depth 5, one request of at most 100 tickers. Candles, funding and the trade tape DO back-serve
(candles by ticker, funding in one request, trades with time filters) and are NOT recorded here.

Public GET only: no key, no signing, no auth header, no account path, no order, no Firestore. Host kalshi external-api only, redirects refused, a generic User-Agent. At most 2 requests a minute, at least
5 seconds between any two requests; a 429 waits 5 seconds doubling up to 60; three 429s in a row end the run. A hard budget of requests per run (REQUEST_BUDGET).
Rows are written as returned (best first, prices and sizes as numbers); a missing level is empty, never zero. It stops by itself: no poll at or after END_UTC (2027-02-26 23:59 UTC), and a run started after it exits at once.
usage: python3 record_perps_live.py <out dir> [--cycle-hours 4]"""
import argparse
import calendar
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://external-api.kalshi.com/trade-api/v2/margin"
UA = {"User-Agent": "shwoopnet-research-recorder"}
END_UTC = "2027-02-26T23:59:00Z"
POLL_EVERY_S = 60
MIN_GAP_S = 5.0
BACKOFF_S, BACKOFF_MAX_S, MAX_429_IN_ROW = 5.0, 60.0, 3
BOOK_BATCH_MAX = 100
LEV_SIZES = ("1000", "10000", "100000", "1000000")      # the notional keys the list gives its size-aware leverage estimates under (long and short)
DEPTH = 5
REQUEST_BUDGET = 2 * (4 * 60 + 90)          # two requests a minute for a 4 hour job plus a margin
MARKET_COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "asset_class", "status", "bid", "ask", "bid_size", "ask_size", "price", "reference_price", "settlement_mark_price",
               "liquidation_mark_price", "open_interest", "volume_24h", "leverage_estimate"] + ["long_lev_%s" % k for k in LEV_SIZES] + ["short_lev_%s" % k for k in LEV_SIZES]
STATIC_COLS = ["t_recv_ms", "ticker", "asset_class", "market_version", "contract_size", "underlying_multiplier", "tick_size", "minimum_quantity", "fractional_trading_enabled", "funding_cap", "funding_deadband",
               "funding_limit_unit", "funding_invalid_premium_handling", "halt_sources", "schedule", "leverage_estimates_json"]
BOOK_COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker"] + ["bid_px_%d" % i for i in range(1, DEPTH + 1)] + ["bid_sz_%d" % i for i in range(1, DEPTH + 1)] \
    + ["ask_px_%d" % i for i in range(1, DEPTH + 1)] + ["ask_sz_%d" % i for i in range(1, DEPTH + 1)]
COVER_COLS = ["t_local_ms", "list_ok", "list_rows", "book_ok", "book_rows", "n429", "note"]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def now_ms():
    return int(time.time() * 1000)


def get(path):
    """One public GET. Returns (status, parsed object or None, server date header, t_send_ms, t_recv_ms)."""
    url = BASE + path
    assert url.startswith("https://external-api.kalshi.com/"), url
    t0 = now_ms()
    try:
        with OPENER.open(urllib.request.Request(url, headers=UA), timeout=30) as r:
            body = r.read(); t1 = now_ms(); st = r.status; date = r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, e.headers.get("Date", "") if e.headers else "", t0, now_ms()
    except Exception:
        return 0, None, "", t0, now_ms()
    try:
        obj = json.loads(body)
    except ValueError:
        return st, None, date, t0, t1
    return st, (obj if isinstance(obj, dict) else None), date, t0, t1


def num(x):
    try:
        return float(x) if x not in ("", None) else ""
    except (TypeError, ValueError):
        return ""


def levels(lv, best_is_high):
    # The API lists the whole book with the BEST level LAST (bids ascending, asks descending), so the first five entries are the far levels.
    # Sort by price and keep the five nearest the touch: highest bids first, lowest asks first.
    out = []
    for p in (lv if isinstance(lv, list) else []):
        if isinstance(p, (list, tuple)) and len(p) >= 2 and num(p[0]) != "":
            out.append((num(p[0]), num(p[1])))
    out.sort(key=lambda x: x[0], reverse=best_is_high); out = out[:DEPTH]
    return out + [("", "")] * (DEPTH - len(out))


def px(x):
    return num(x.get("price")) if isinstance(x, dict) else num(x)


def lev(m, side, k):
    d = m.get(side + "_leverage_estimates")
    return num(d.get(k)) if isinstance(d, dict) else ""


def market_row(m, t0, t1, date):
    return [t0, t1, date, m.get("ticker", ""), m.get("asset_class", ""), m.get("status", ""), num(m.get("bid")), num(m.get("ask")), num(m.get("bid_size_fp")), num(m.get("ask_size_fp")), num(m.get("price")),
            px(m.get("reference_price")), px(m.get("settlement_mark_price")), px(m.get("liquidation_mark_price")), num(m.get("open_interest")), num(m.get("volume_24h")), num(m.get("leverage_estimate"))] \
        + [lev(m, "long", k) for k in LEV_SIZES] + [lev(m, "short", k) for k in LEV_SIZES]


def static_row(m, t1):
    hs = m.get("halt_sources")
    return [t1, m.get("ticker", ""), m.get("asset_class", ""), m.get("market_version", ""), m.get("contract_size", ""), m.get("underlying_multiplier", ""), m.get("tick_size", ""), m.get("minimum_quantity", ""),
            m.get("fractional_trading_enabled", ""), m.get("funding_cap", ""), m.get("funding_deadband", ""), m.get("funding_limit_unit", ""), m.get("funding_invalid_premium_handling", ""),
            "|".join(str(x) for x in hs) if isinstance(hs, list) else "", json.dumps(m.get("schedule"), sort_keys=True), json.dumps(m.get("leverage_estimates"), sort_keys=True)]


def book_row(e, t0, t1, date):
    ob = e.get("orderbook") if isinstance(e.get("orderbook"), dict) else {}
    b, a = levels(ob.get("bids"), True), levels(ob.get("asks"), False)
    return [t0, t1, date, e.get("ticker", "")] + [x[0] for x in b] + [x[1] for x in b] + [x[0] for x in a] + [x[1] for x in a]


def end_epoch():
    return calendar.timegm(time.strptime(END_UTC, "%Y-%m-%dT%H:%M:%SZ"))


def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--cycle-hours", type=float, default=4.0); a = ap.parse_args(argv)
    if time.time() >= end_epoch():
        print("past the end date: nothing to record"); return 0
    os.makedirs(a.out, exist_ok=True)
    step = int(a.cycle_hours * 3600); stop = (int(time.time()) // step + 1) * step
    fm, fb, fc, fs = (open(os.path.join(a.out, n), "w", newline="") for n in ("markets.csv", "book.csv", "coverage.csv", "static.csv"))
    wm, wb, wc, ws = csv.writer(fm), csv.writer(fb), csv.writer(fc), csv.writer(fs)
    wm.writerow(MARKET_COLS); wb.writerow(BOOK_COLS); wc.writerow(COVER_COLS); ws.writerow(STATIC_COLS); static_done = False
    budget = REQUEST_BUDGET; last_req = 0.0; in_row = 0; wait = BACKOFF_S

    def paced():
        nonlocal last_req
        d = MIN_GAP_S - (time.time() - last_req)
        if d > 0:
            time.sleep(d)
        last_req = time.time()

    while time.time() < min(stop, end_epoch()) and budget > 0:
        t_poll = time.time(); n429 = 0; note = ""; lrows = brows = 0; lok = bok = 0; active = []
        paced(); budget -= 1
        st, obj, date, t0, t1 = get("/markets")
        if st == 429:
            n429 += 1; in_row += 1
        elif st == 200 and obj and isinstance(obj.get("markets"), list):
            in_row = 0; lok = 1
            for m in obj["markets"]:
                if isinstance(m, dict) and m.get("ticker"):
                    wm.writerow(market_row(m, t0, t1, date)); lrows += 1
                    if not static_done:
                        ws.writerow(static_row(m, t1))
                    if m.get("status") == "active":
                        active.append(m["ticker"])
            static_done = True
        else:
            note = "list status %s" % st
        if in_row >= MAX_429_IN_ROW:
            note += " three 429s in a row: run ended"; wc.writerow([now_ms(), lok, lrows, bok, brows, n429, note.strip()]); break
        for i in range(0, len(active), BOOK_BATCH_MAX):
            if budget <= 0:
                break
            paced(); budget -= 1
            st, obj, date, t0, t1 = get("/markets/orderbooks?tickers=" + ",".join(active[i:i + BOOK_BATCH_MAX]))
            if st == 429:
                n429 += 1; in_row += 1
            elif st == 200 and obj and isinstance(obj.get("orderbooks"), list):
                in_row = 0; bok = 1
                for e in obj["orderbooks"]:
                    if isinstance(e, dict):
                        wb.writerow(book_row(e, t0, t1, date)); brows += 1
            else:
                note += " book status %s" % st
        wc.writerow([now_ms(), lok, lrows, bok, brows, n429, note.strip()])
        for f in (fm, fb, fc, fs):
            f.flush()
        if in_row >= MAX_429_IN_ROW:
            break
        if n429:
            time.sleep(wait); wait = min(wait * 2, BACKOFF_MAX_S)
        else:
            wait = BACKOFF_S
        time.sleep(max(0.0, POLL_EVERY_S - (time.time() - t_poll)))
    for f in (fm, fb, fc, fs):
        f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
