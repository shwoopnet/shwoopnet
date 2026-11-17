#!/usr/bin/env python3
"""Perps live recorder (Nov 16, 2026, the Head's order, research only; needs the owner's popup before it is merged because of its runner minutes). What Kalshi's PUBLIC perps (margin) API
shows only LIVE and cannot back-serve: every 60 seconds (1) the perps list, one request for all markets (bid, ask, sizes, last price, reference price, settlement and liquidation marks,
open interest, 24 hour volume, leverage estimate and the long and short leverage estimates at each notional size; the static fields (contract size, tick, funding cap, schedule and so on) once per job in static.csv), and (2) the order books of the active markets, depth 5, one request of at most 100 tickers. Candles, funding and the trade tape DO back-serve
(candles by ticker, funding in one request, trades with time filters) and are NOT recorded here.

Added Nov 17, 2026 (Forensics' spec, the Head's order): (3) the public TRADE TAPE (/trades, no ticker), built but OFF (TAPE_ON; see the constant), once a minute when on, bounded to 20 seconds and 5 pages after the list read, into tape.csv with a coverage row per poll
(tape_cover.csv; the tape now also back-serves, so a truncated poll names the window it did not reach); (4) settle.csv, the list rows read between 16:55 and 17:05 UTC with settle_window=1 (no extra request); (5) funding_day.csv,
one request after 21:15 UTC for every market's funding prints of the day (the route's field is market_ticker). Same host, no key, same job, no new schedule.

Public GET only: no key, no signing, no auth header, no account path, no order, no Firestore. Host kalshi external-api only, redirects refused, a generic User-Agent. At most 2 requests a minute, plus the fast lane's one batched request every 5 seconds inside 14:30 to 21:00 UTC on weekdays (about 14 a minute in the window), at least
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
# FAST LANE (Nov 16, 2026, the owner's order): inside the cash session window the book top and depth 5 of a few liquid perps every 5 seconds, ONE batched orderbooks request, a step of THIS job (no new workflow, no second run).
FAST_TICKERS = ("KXNVDAPERP", "KXMUPERP", "KXTSLAPERP", "KXSPCXPERP", "KXUSTECH100PERP", "KXUS500PERP", "KXGOLDPERP", "KXBTCPERP", "KXETHPERP", "KXSPYPERP")
FAST_EVERY_S = 5.0
FAST_MIN_GAP_S = 1.0                      # our own pacing between any two requests while the fast lane is on (the list and the full book keep MIN_GAP_S)
FAST_BUDGET = 4 * 720 + 240               # 5 second polls for at most 4 hours (720 an hour) plus a margin, on top of REQUEST_BUDGET
CT_OPEN_UTC_S, CT_CLOSE_UTC_S = 14 * 3600 + 1800, 21 * 3600     # 8:30 to 15:00 US Central while Central is on standard time (UTC-6), which holds for the whole run (the stop date is before the March 2027 change)
FAST_COLS = BOOK_COLS
FAST_COVER_COLS = ["t_local_ms", "ok", "rows", "n429", "note"]
# TAPE, SETTLEMENT MARKS AND THE DAILY FUNDING READ (Nov 17, 2026, Forensics' spec RECORDER_SPEC_TAPE_SETTLE_NOV17, the Head's order; same job, no new schedule). The perps public trade tape
# (GET /margin/trades, NO ticker, newest first, limit 1000, cursor) is read every 5 minutes after the list read, bounded to 20 seconds and 5 pages; the probe of Nov 17 showed it also BACK-SERVES at
# least 60 days (a one hour window 60 days back answered with a full page), so a truncated poll writes the window it did not reach in its coverage row and a back-pull can fill it.
TAPE_ON = False                            # OFF by default (Nov 17, 2026 live test: about 25 trades a second, 5,000 rows in 200 s, so about 2 million rows and an estimated 40 to 60 MB gzipped a day, far over the spec's 2 to 8 MB; the tape also back-serves 60 days). Turn on only with a decision on the branch size.
TAPE_EVERY_S = 60.0                        # once a minute when on: at the live rate 5 minutes is about 7,500 trades, over the 5 page cap, so a 5 minute poll would truncate every time
TAPE_BUDGET_S = 20.0
TAPE_MAX_PAGES = 5
TAPE_LIMIT = 1000
TAPE_GAP_S = 1.0                           # our own pacing between two tape pages
TAPE_OVERLAP_S = 60                        # a poll starts 60 s before the newest trade the last poll saw, so nothing between two polls is lost; the overlap is removed by trade id in memory
TAPE_FIRST_BACK_S = 900                    # the first poll of a job reaches 15 minutes back (the gap before a job that started late); rows are NOT deduplicated across jobs, readers drop repeats by the whole row
TAPE_BACKOFF_S, TAPE_BACKOFF_MAX_S = 2.0, 30.0
TAPE_COLS = ["t_recv_ms", "server_date_header", "ticker", "created_time", "price", "count", "taker_side", "is_block_trade"]
TAPE_COVER_COLS = ["t_local_ms", "pages", "trades", "duplicates_dropped", "n429", "newest_created_ms", "cursor_ended", "truncated", "lost_window_lo_ms", "lost_window_hi_ms", "note"]
SETTLE_FROM_S, SETTLE_TO_S = 16 * 3600 + 55 * 60, 17 * 3600 + 5 * 60      # 16:55 to 17:05 UTC: every list row of the window is also written to settle.csv with settle_window=1
SETTLE_COLS = MARKET_COLS + ["settle_window"]
FUNDING_DAY_AFTER_S = 21 * 3600 + 15 * 60  # the first read after 21:15 UTC reads the whole day's funding prints of every market (one request, no ticker)
FUNDING_DAY_COLS = ["t_recv_ms", "server_date_header", "market_ticker", "funding_time", "funding_rate", "mark_price"]
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


def fast_window(t):
    """True on a Monday to Friday UTC date between 8:30 and 15:00 US Central (14:30 to 21:00 UTC). Holidays are not excluded: the perps list keeps trading."""
    tm = time.gmtime(t)
    return tm.tm_wday < 5 and CT_OPEN_UTC_S <= tm.tm_hour * 3600 + tm.tm_min * 60 + tm.tm_sec < CT_CLOSE_UTC_S


def fast_poll(tickers, wf, wcf, getter):
    """One batched orderbooks request for the fast tickers; returns (status, rows written). Never raises."""
    st, obj, date, t0, t1 = getter("/markets/orderbooks?tickers=" + ",".join(tickers)); rows = 0; note = ""
    if st == 200 and obj and isinstance(obj.get("orderbooks"), list):
        for e in obj["orderbooks"]:
            if isinstance(e, dict) and e.get("ticker") in tickers:
                wf.writerow(book_row(e, t0, t1, date)); rows += 1
    elif st != 429:
        note = "fast book status %s" % st
    wcf.writerow([now_ms(), 1 if rows else 0, rows, 1 if st == 429 else 0, note])
    return st, rows


def iso_ms(s):
    """'2026-11-17T01:25:52.640357Z' to epoch milliseconds, or None."""
    try:
        base, _, frac = str(s).rstrip("Z").partition(".")
        return int(calendar.timegm(time.strptime(base, "%Y-%m-%dT%H:%M:%S")) * 1000 + int((frac + "000")[:3]))
    except (ValueError, TypeError):
        return None


def tape_row(x, t1, date):
    return [t1, date, x.get("ticker", ""), x.get("created_time", ""), num(x.get("price")), num(x.get("count")), x.get("taker_side", ""), x.get("is_block_trade", "")]


def tape_poll(state, wt, wtc, getter, deadline, sleep=time.sleep, clock=time.time):
    """One bounded tape poll. state = {"min_s": epoch seconds to start from, "seen": set of trade ids kept in memory (overlap only)}. Reads newest first, follows the cursor for at most TAPE_MAX_PAGES pages and
    TAPE_BUDGET_S seconds and never past `deadline` (the next list read). Never raises. Three 429s in a row end THIS step only. A poll that did not reach the end of its window says so in the coverage row
    (truncated=1 and the window it did not read); the tape back-serves, so a back-pull can fill it."""
    t_start = clock(); cursor = None; pages = trades = dups = n429 = 0; newest = None; oldest = None; ended = False; note = ""; streak = 0; wait = TAPE_BACKOFF_S
    while pages < TAPE_MAX_PAGES:
        if clock() - t_start >= TAPE_BUDGET_S or clock() >= deadline - 1.0:
            note = "time bound"; break
        path = "/trades?limit=%d&min_ts=%d" % (TAPE_LIMIT, state["min_s"]) + (("&cursor=" + cursor) if cursor else "")
        st, obj, date, t0, t1 = getter(path); pages += 1
        if st == 429:
            n429 += 1; streak += 1
            if streak >= MAX_429_IN_ROW:
                note = "three 429s in a row: tape step ended"; break
            sleep(min(wait, max(0.0, deadline - clock() - 1.0))); wait = min(wait * 2, TAPE_BACKOFF_MAX_S); continue
        streak = 0; wait = TAPE_BACKOFF_S
        if st != 200 or not obj or not isinstance(obj.get("trades"), list):
            note = "tape status %s" % st; break
        for x in obj["trades"]:
            if not isinstance(x, dict):
                continue
            tid = x.get("trade_id"); ms = iso_ms(x.get("created_time"))
            if tid is not None and tid in state["seen"]:
                dups += 1; continue
            if tid is not None:
                state["seen"].add(tid)
            wt.writerow(tape_row(x, t1, date)); trades += 1
            if ms is not None:
                newest = ms if newest is None or ms > newest else newest
                oldest = ms if oldest is None or ms < oldest else oldest
        cursor = obj.get("cursor")
        if not cursor or not isinstance(cursor, str) or not cursor.replace("-", "").replace("_", "").replace("=", "").isalnum():
            ended = True; break
        sleep(TAPE_GAP_S)
    truncated = 0 if ended else 1
    lo = state["min_s"] * 1000 if truncated and oldest is not None else ""
    hi = oldest if truncated and oldest is not None else ""
    if newest is not None:
        state["min_s"] = max(state["min_s"], int(newest // 1000) - TAPE_OVERLAP_S)
    if len(state["seen"]) > 20000:      # the overlap is 60 seconds, so only recent ids matter; keep memory bounded
        state["seen"].clear()
    wtc.writerow([int(clock() * 1000), pages, trades, dups, n429, newest if newest is not None else "", 1 if ended else 0, truncated, lo, hi, note])
    return trades


def in_settle_window(t):
    tod = int(t) % 86400
    return SETTLE_FROM_S <= tod < SETTLE_TO_S


def funding_day_poll(day_start_s, wfd, getter):
    """One request: every market's funding prints of the UTC day starting at day_start_s (the route answers with market_ticker, funding_time, funding_rate and mark_price). Returns the rows written, -1 when the read failed."""
    st, obj, date, t0, t1 = getter("/funding_rates/historical?start_ts=%d&end_ts=%d&limit=1000" % (day_start_s, day_start_s + 86400))
    if st != 200 or not obj or not isinstance(obj.get("funding_rates"), list):
        return -1
    n = 0
    for f in obj["funding_rates"]:
        if isinstance(f, dict):
            wfd.writerow([t1, date, f.get("market_ticker", ""), f.get("funding_time", ""), num(f.get("funding_rate")), num(f.get("mark_price"))]); n += 1
    return n


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
    ff = fcf = None; wf = wcf = None; fast_budget = FAST_BUDGET; fast_429 = 0; fast_dead = False; next_fast = 0.0
    ft = ftc = wt = wtc = None
    if TAPE_ON:
        ft, ftc = open(os.path.join(a.out, "tape.csv"), "w", newline=""), open(os.path.join(a.out, "tape_cover.csv"), "w", newline="")
        wt, wtc = csv.writer(ft), csv.writer(ftc); wt.writerow(TAPE_COLS); wtc.writerow(TAPE_COVER_COLS)
    tape_state = {"min_s": int(time.time()) - TAPE_FIRST_BACK_S, "seen": set()}; next_tape = time.time() + 5.0; tape_budget = [(stop - int(time.time())) // 60 * TAPE_MAX_PAGES + 60]
    fsl = wsl = ffd = wfd = None; fd_tries = 0; fd_day = None
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
                    if in_settle_window(t1 / 1000.0):
                        if wsl is None:
                            fsl = open(os.path.join(a.out, "settle.csv"), "w", newline=""); wsl = csv.writer(fsl); wsl.writerow(SETTLE_COLS)
                        wsl.writerow(market_row(m, t0, t1, date) + [1])
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
        for f in (fm, fb, fc, fs, fsl):
            if f is not None:
                f.flush()
        if in_row >= MAX_429_IN_ROW:
            break
        if n429:
            time.sleep(wait); wait = min(wait * 2, BACKOFF_MAX_S)
        else:
            wait = BACKOFF_S
        deadline = t_poll + POLL_EVERY_S
        while time.time() < deadline - 0.05:        # the rest of the minute: tape and funding steps, fast lane polls inside the window, otherwise just wait
            now = time.time()
            if TAPE_ON and now >= next_tape and tape_budget[0] > 0 and deadline - now >= 5.0:
                def tape_get(path):
                    if tape_budget[0] <= 0:
                        return 0, None, "", now_ms(), now_ms()
                    tape_budget[0] -= 1
                    return get(path)
                tape_poll(tape_state, wt, wtc, tape_get, deadline); last_req = time.time(); next_tape = last_req + TAPE_EVERY_S
                ft.flush(); ftc.flush()
            elif fd_tries < 3 and (int(now) % 86400) >= FUNDING_DAY_AFTER_S and fd_day != int(now) // 86400 and deadline - now >= 5.0:
                if ffd is None:
                    ffd = open(os.path.join(a.out, "funding_day.csv"), "w", newline=""); wfd = csv.writer(ffd); wfd.writerow(FUNDING_DAY_COLS)
                fd_tries += 1; last_req = time.time()
                if funding_day_poll(int(now) // 86400 * 86400, wfd, get) >= 0:
                    fd_day = int(now) // 86400; fd_tries = 0
                ffd.flush()
            elif not fast_dead and fast_budget > 0 and fast_window(now) and now >= next_fast and now + FAST_MIN_GAP_S <= deadline:
                if ff is None:
                    ff = open(os.path.join(a.out, "book_fast.csv"), "w", newline=""); fcf = open(os.path.join(a.out, "coverage_fast.csv"), "w", newline="")
                    wf, wcf = csv.writer(ff), csv.writer(fcf); wf.writerow(FAST_COLS); wcf.writerow(FAST_COVER_COLS)
                d = FAST_MIN_GAP_S - (time.time() - last_req)
                if d > 0:
                    time.sleep(d)
                last_req = time.time(); fast_budget -= 1
                st, _rows = fast_poll(FAST_TICKERS, wf, wcf, get)
                fast_429 = fast_429 + 1 if st == 429 else 0
                next_fast = last_req + FAST_EVERY_S * (2 ** fast_429)         # 5 s, then 10 s and 20 s after a 429 in a row
                if fast_429 >= MAX_429_IN_ROW:        # the fast lane ends for this job; the normal minute poll carries on
                    fast_dead = True; wcf.writerow([now_ms(), 0, 0, 0, "three 429s in a row: fast lane ended for this job"])
                ff.flush(); fcf.flush()
            else:
                time.sleep(min(0.2, max(0.0, deadline - time.time())))
    for f in (fm, fb, fc, fs, ff, fcf, ft, ftc, fsl, ffd):
        if f is not None:
            f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
