#!/usr/bin/env python3
"""Combo book recorder (Nov 12, 2026, the owner approved). Research data only: nothing here trades.

Kalshi's combo (multivariate) markets live on exchange_index 1 and number in the tens of thousands, so they are sampled, not recorded in full. Each run does ONE poll:
list the open combos (mve_filter=only, at most MAX_LIST_PAGES pages), keep every combo with a posted bid or ask at ANY price on the yes or the no side, or any traded volume (widened Nov 12, 2026 so the cheap side and the house side are both testable),
rank them tightest yes spread first (then volume, then ticker), write the quotes of the first MAX_QUOTE_ROWS, then read the order book (best DEPTH YES and NO bids with sizes) of the first MAX_BOOKS
and the public trades of the MAX_TRADES most traded.
Once a day (the 00 UTC hour) it also reads settled combos with volume, so a paper test of buying either side of a combo has the outcomes next to the depth.

PUBLIC Kalshi market data only: no key, no signing, no auth header, no account path, no order, no Firestore. One request stream, at least GAP_S seconds between calls (at most 10 a
minute); a 429 waits 5 seconds doubling up to 60, and after MAX_CONSEC_429 refusals in a row the run stops early and says so. A hard request budget per run. A body that is not an
object is no answer, never an error. Redirects are refused. It stops by itself: a run started at or after END_UTC exits at once.

Rows are written as the exchange returns them (dollar fields as strings), nothing computed. A missing field is empty."""
import argparse
import calendar
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://external-api.kalshi.com/trade-api/v2"
END_UTC = "2027-01-31T23:59:00Z"   # nothing is recorded from here on
GAP_S = 6.0                        # at least this long between calls: at most 10 a minute
BACKOFF_S = 5.0
BACKOFF_MAX_S = 60.0
MAX_CONSEC_429 = 3                 # this many refusals in a row end the run early
BUDGET = 90                        # hard request budget per run
PAGE_LIMIT = 1000
MAX_LIST_PAGES = 5                 # at most 5,000 open combos listed per run
MAX_QUOTE_ROWS = 400
MAX_BOOKS = 40
MAX_TRADES = 15
MAX_LEG_ROWS = 100                 # leg_tickers is filled for the first 100 quote rows only (the tightest spreads, which also get the books); later rows leave it empty so a day stays under 1 MB gzipped
LEGS_MAX_CHARS = 600               # cap on the leg_tickers string of one quote row; the true leg count stays in `legs`
LEGS_MARKER = "|..."               # ends a truncated leg_tickers string
DEPTH = 5
SETTLED_PAGES = 3
SETTLED_LOOKBACK_S = 36 * 3600
UA = {"User-Agent": "shwoopnet-research-recorder"}

QUOTE_COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "event_ticker", "exchange_index", "open_time", "close_time", "yes_bid", "yes_ask", "no_bid", "no_ask",
              "yes_bid_size", "yes_ask_size", "last_price", "volume", "open_interest", "legs", "leg_tickers"]
BOOK_COLS = ["t_recv_ms", "server_date_header", "ticker", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] \
    + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
TRADE_COLS = ["t_recv_ms", "ticker", "created_time", "yes_price_dollars", "count_fp", "taker_outcome_side", "trade_id"]
RESULT_COLS = ["t_recv_ms", "ticker", "event_ticker", "close_time", "result", "last_price", "volume"]
COVER_COLS = ["t_recv_ms", "listed", "pages", "list_complete", "selected", "quote_rows", "books", "trades_read", "requests", "n429", "stopped_early"]


def epoch_of(iso_s):
    return calendar.timegm(time.strptime(iso_s, "%Y-%m-%dT%H:%M:%SZ"))


END_EPOCH = epoch_of(END_UTC)


def past_end(now):
    return now >= END_EPOCH


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is never followed: the one allowed host is checked on the URL we build. A 3xx answer is a failed read (its status is returned)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def http_get(url):
    """(status, decoded json or None, Date header or ''). Never raises: a failed read is a status. Redirects are refused."""
    try:
        with _OPENER.open(urllib.request.Request(url, headers=UA), timeout=15) as r:
            return r.status, json.load(r), r.headers.get("Date", "")
    except urllib.error.HTTPError as e:
        return e.code, None, ""
    except Exception:
        return 0, None, ""


class Stream:
    """One request stream: one call at a time, GAP_S between calls, after a 429 a wait that doubles up to BACKOFF_MAX_S, a hard budget, and an early stop after MAX_CONSEC_429
    refusals in a row. `fetch` is the transport (url -> (status, body, date)); tests pass a fake one. Returns (status, body, date, t_recv_ms); status -1 means the budget is spent,
    -2 means it stopped after repeated refusals (and stays stopped)."""

    def __init__(self, budget=BUDGET, fetch=None, clock=time.time, sleep=time.sleep):
        self.budget, self.fetch, self.clock, self.sleep = budget, fetch or http_get, clock, sleep
        self.next_ok, self.backoff, self.n429, self.consec, self.calls, self.stopped = 0.0, BACKOFF_S, 0, 0, 0, False

    def get(self, url):
        if self.stopped:
            return -2, None, "", 0
        if self.calls >= self.budget:
            return -1, None, "", 0
        wait = self.next_ok - self.clock()
        if wait > 0:
            self.sleep(wait)
        self.calls += 1
        st, body, date = self.fetch(url)
        t_recv = int(self.clock() * 1000)
        if st == 429:
            self.n429 += 1
            self.consec += 1
            self.next_ok = self.clock() + self.backoff
            self.backoff = min(BACKOFF_MAX_S, self.backoff * 2)
            if self.consec >= MAX_CONSEC_429:
                self.stopped = True
        else:
            self.consec = 0
            self.next_ok = self.clock() + GAP_S
            if st == 200:
                self.backoff = BACKOFF_S
        return st, body, date, t_recv


def list_url(status, cursor="", min_close_ts=None):
    u = "%s/markets?mve_filter=only&status=%s&limit=%d" % (BASE, status, PAGE_LIMIT)
    if min_close_ts is not None:
        u += "&min_close_ts=%d" % min_close_ts
    return u + ("&cursor=" + cursor if cursor else "")


def list_combos(stream, status, pages, min_close_ts=None):
    """Combos of one status, following the cursor for at most `pages` pages. Returns (markets, date, t_recv, pages_read, complete). A non-object body, a non-list `markets` or a
    failed read is no answer: what was read so far is kept and complete is False. A 429 is waited out by the stream and the same page asked again once."""
    out, cursor, date, tr, n, retried = [], "", "", 0, 0, False
    while n < pages:
        st, body, d, r = stream.get(list_url(status, cursor, min_close_ts))
        if st == 429 and not retried:
            retried = True
            continue
        if st != 200 or not isinstance(body, dict) or not isinstance(body.get("markets"), list):
            return out, date, tr, n, False
        retried = False
        n += 1
        out += [m for m in body["markets"] if isinstance(m, dict)]
        date, tr = d, r
        cursor = body.get("cursor")
        if not isinstance(cursor, str) or not cursor:
            return out, date, tr, n, True
    return out, date, tr, n, False


def posted(m):
    """The posted prices of a combo as (yes bid, yes ask, no bid, no ask) in dollars, None for an empty side. A bid of 0 and an ask of exactly 1.0000 are the empty side, not prices."""
    out = []
    for k, empty in (("yes_bid_dollars", 0.0), ("yes_ask_dollars", 1.0), ("no_bid_dollars", 0.0), ("no_ask_dollars", 1.0)):
        v = num(m.get(k))
        out.append(None if v is None or v == empty else v)
    return out


def is_selected(m):
    """Any posted bid or ask at ANY price on the yes or the no side, or any traded volume (widened Nov 12, 2026: the cheap side and the house side must both be testable)."""
    if not isinstance(m, dict) or not m.get("ticker"):
        return False
    return any(p is not None for p in posted(m)) or (num(m.get("volume_fp")) or 0) > 0


def rank_key(m):
    """Tightest yes spread first (a combo with both a yes bid and a yes ask), then the most volume, then the ticker. A one-sided or unquoted combo has no spread and ranks after every two-sided one."""
    yb, ya = posted(m)[0], posted(m)[1]
    spread = (ya - yb) if (yb is not None and ya is not None) else float("inf")
    return (spread, -(num(m.get("volume_fp")) or 0), m.get("ticker", ""))


def pick(markets):
    """(the selected markets, tightest spread first). Deterministic: ties break on volume, then the ticker. The books and the quote cap take from the front of this order."""
    return sorted([m for m in markets if is_selected(m)], key=rank_key)


def leg_tickers(legs):
    """The legs of a combo as `ticker:side` joined by `|`, read from the market object already in hand (no request). A leg that is a plain string is its own ticker; a leg with no readable ticker is skipped.
    Longer than LEGS_MAX_CHARS: cut at the last whole leg that fits and end with LEGS_MARKER (the total stays within the cap; `legs` keeps the true count). Not a list: empty."""
    if not isinstance(legs, list):
        return ""
    parts = []
    for lg in legs:
        t, side = (lg, "") if isinstance(lg, str) else ((lg.get("market_ticker") or lg.get("ticker") or "", lg.get("side") or "") if isinstance(lg, dict) else ("", ""))
        if isinstance(t, str) and t:
            parts.append(t + (":" + side if isinstance(side, str) and side else ""))
    full = "|".join(parts)
    if len(full) <= LEGS_MAX_CHARS:
        return full
    out = ""
    for x in parts:
        nxt = (out + "|" if out else "") + x
        if len(nxt) + len(LEGS_MARKER) > LEGS_MAX_CHARS:
            break
        out = nxt
    return out + LEGS_MARKER


def quote_row(t_recv, date, m, with_legs=True):
    if not isinstance(m, dict) or not m.get("ticker"):
        return None
    g = lambda k: m.get(k, "") if m.get(k) is not None else ""
    legs = m.get("mve_selected_legs")
    return [t_recv, t_recv, date, m["ticker"], g("event_ticker"), g("exchange_index"), g("open_time"), g("close_time"), g("yes_bid_dollars"), g("yes_ask_dollars"), g("no_bid_dollars"),
            g("no_ask_dollars"), g("yes_bid_size_fp"), g("yes_ask_size_fp"), g("last_price_dollars"), g("volume_fp"), g("open_interest_fp"), len(legs) if isinstance(legs, list) else "", leg_tickers(legs) if with_legs else ""]


def parse_levels(levels):
    """The exchange lists levels worst price first, the best last. Up to DEPTH (price, size) pairs, best first, as strings exactly as returned."""
    out = []
    for lv in reversed(levels or []):
        if isinstance(lv, (list, tuple)) and len(lv) >= 2 and num(lv[0]) is not None and num(lv[1]) is not None:
            out.append((lv[0], lv[1]))
    return out[:DEPTH]


def book_row(t_recv, date, m, resp):
    """One CSV row, or None when the response has no book. Missing levels are empty, never zero."""
    if not isinstance(resp, dict):
        return None
    ob = resp.get("orderbook_fp") or resp.get("orderbook") or {}
    if not isinstance(ob, dict):
        return None
    yes, no = parse_levels(ob.get("yes_dollars")), parse_levels(ob.get("no_dollars"))
    if not yes and not no:
        return None
    pad = lambda lv, k: [lv[i][k] if i < len(lv) else "" for i in range(DEPTH)]
    return [t_recv, date, m.get("ticker"), m.get("close_time", "")] + pad(yes, 0) + pad(yes, 1) + pad(no, 0) + pad(no, 1)


def trade_rows(t_recv, trades):
    rows = []
    for t in (trades or []):
        if isinstance(t, dict) and t.get("trade_id") is not None:
            rows.append([t_recv, t.get("ticker"), t.get("created_time"), t.get("yes_price_dollars"), t.get("count_fp"), t.get("taker_outcome_side"), t.get("trade_id")])
    return rows


def result_row(t_recv, m):
    if not isinstance(m, dict) or not m.get("ticker") or m.get("result") in (None, "") or (num(m.get("volume_fp")) or 0) <= 0:
        return None
    g = lambda k: m.get(k, "") if m.get(k) is not None else ""
    return [t_recv, m["ticker"], g("event_ticker"), g("close_time"), m["result"], g("last_price_dollars"), g("volume_fp")]


def write_csv(path, cols, rows):
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(cols)
        w.writerows(rows)


def poll(stream, now, out_dir):
    """One poll. Returns the coverage row."""
    markets, date, tr, pages, complete = list_combos(stream, "open", MAX_LIST_PAGES)
    chosen = pick(markets)
    qrows = [r for r in (quote_row(tr, date, m, i < MAX_LEG_ROWS) for i, m in enumerate(chosen[:MAX_QUOTE_ROWS])) if r]
    write_csv(os.path.join(out_dir, "quotes.csv"), QUOTE_COLS, qrows)
    brows, trows, nbooks, ntrades = [], [], 0, 0
    for m in chosen[:MAX_BOOKS]:
        st, body, d, r = stream.get("%s/markets/%s/orderbook?depth=%d" % (BASE, m["ticker"], DEPTH))
        if st in (-1, -2):
            break
        nbooks += 1
        row = book_row(r, d, m, body) if st == 200 else None
        if row:
            brows.append(row)
    write_csv(os.path.join(out_dir, "books.csv"), BOOK_COLS, brows)
    # trades go to the MOST traded combos (volume, then ticker), not to the tightest spreads: a trade read is the scarce one
    traded = sorted([m for m in chosen if (num(m.get("volume_fp")) or 0) > 0], key=lambda m: (-(num(m.get("volume_fp")) or 0), m["ticker"]))[:MAX_TRADES]
    for m in traded:
        st, body, d, r = stream.get("%s/markets/trades?ticker=%s&limit=100" % (BASE, m["ticker"]))
        if st in (-1, -2):
            break
        ntrades += 1
        if st == 200 and isinstance(body, dict) and isinstance(body.get("trades"), list):
            trows += trade_rows(r, body["trades"])
    write_csv(os.path.join(out_dir, "trades.csv"), TRADE_COLS, trows)
    if time.gmtime(now).tm_hour == 0 and not stream.stopped:
        sm, _d, str_, _p, _c = list_combos(stream, "settled", SETTLED_PAGES, int(now) - SETTLED_LOOKBACK_S)
        write_csv(os.path.join(out_dir, "results.csv"), RESULT_COLS, [r for r in (result_row(str_, m) for m in sm) if r])
    return [tr, len(markets), pages, int(complete), len(chosen), len(qrows), nbooks, ntrades, stream.calls, stream.n429, int(stream.stopped)]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    a = ap.parse_args(argv)
    if past_end(time.time()):
        print("past the end date %s: nothing to record" % END_UTC)
        return 0
    os.makedirs(a.out_dir, exist_ok=True)
    stream = Stream()
    cov = poll(stream, time.time(), a.out_dir)
    write_csv(os.path.join(a.out_dir, "coverage.csv"), COVER_COLS, [cov])
    print("done: %d requests, %d refused (429)%s" % (stream.calls, stream.n429, ", stopped early after repeated refusals" if stream.stopped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
