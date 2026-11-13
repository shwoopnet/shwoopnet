#!/usr/bin/env python3
"""A MADE-UP fixture for DEPTH1 in the R6 recorder's folder and column shape (scripts/record_15m_book.py on main): <out>/<date>/<HHMM>/{book,trades,coverage,clock}.csv.gz
plus the marker file MADE_UP_DATA. Nothing here is real: books, trades, results and clocks are invented so two independent builds can be run on the same rows.
usage: python3 -I make_depth1_fixture.py <out dir> [seed] [edge]
  edge (default 0.0): the chance, beyond a coin flip, that a Bitcoin window's result follows the sign of the touch imbalance at the look. 0.0 = no edge anywhere.
Planted on purpose: runs with different clock offsets, a run with no Date header, windows dated Oct 29 (US Central) and Nov 14, a ticker recorded in two runs, coverage rows
that fail each usable test, windows with no yes or no result (about 0.4%), missing polls around the look and the lookbacks, one-sided and empty books, a missing second
level, equal sizes 60 s ago, asks outside 0.10 to 0.90, under one contract at the ask, tape sweeps on both sides, and a fill quote that differs from the look's."""
import sys, os, csv, gzip, random
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime

BOOK_COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "series", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] \
    + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
TRADE_COLS = ["ticker", "created_time", "yes_price_dollars", "count_fp", "taker_outcome_side"]
COVER_COLS = ["close_time", "series", "ticker", "polls", "ok_polls", "n429", "batch_fallback", "max_gap_ms", "first_recv_ms", "last_recv_ms", "book_rows",
              "tape_pages", "tape_trades", "dupes_dropped", "tape_sum_count", "volume_fp", "result", "note"]
CLOCK_COLS = ["t_local_ms", "offset_ms"]


def main(out, seed, edge):
    rng = random.Random(seed); os.makedirs(out); open(os.path.join(out, "MADE_UP_DATA"), "w").write("invented rows for a build comparison; nothing here is real\n")
    start = datetime(2026, 10, 29, 20, 0, tzinfo=timezone.utc); end = datetime(2026, 11, 14, 8, 0, tzinfo=timezone.utc)
    run_start = start; n_windows = 0; carry = []
    while run_start < end:
        d = os.path.join(out, run_start.strftime("%Y-%m-%d"), run_start.strftime("%H%M")); os.makedirs(d)
        off = rng.choice([-900, -350, 0, 250, 700, 1400]); no_clock = rng.random() < 0.02
        B, TR, CV = [], [], carry; carry = []                                   # a ticker recorded in two runs: the earlier run's window also has a coverage row here, with no book rows
        t = run_start
        while t < run_start + timedelta(hours=4):
            t += timedelta(minutes=30)                                           # every other quarter hour: 48 windows a day a market
            T = int(t.timestamp() * 1000); iso = t.strftime("%Y-%m-%dT%H:%M:%SZ")
            for series in ("KXGOLD15M", "KXBTC15M"):
                n_windows += 1; tk = "%s-%s-00" % (series, t.strftime("%y%b%d%H%M").upper()); kind = rng.random()
                mid = rng.choice([0.5, 0.5, 0.42, 0.61, 0.3, 0.74, 0.93, 0.06]) if kind > 0.02 else 0.5
                ysz = [rng.choice([5, 20, 60, 150, 400]) for _ in range(5)]; nsz = [rng.choice([5, 20, 60, 150, 400]) for _ in range(5)]
                if 0.02 <= kind < 0.04: nsz = ysz[:]                             # equal sizes 60 s ago and now
                gap_at = rng.choice([None, None, None, 480, 510, 540]) if kind > 0.1 else None    # a hole in the polls around the look or a lookback
                first = None; last = None; npolls = 0; nrows = 0; look = (0.0, 0.0)
                for k in range(0, 136):                                          # polls every 2 s from T-620 s to T-350 s (past L1's look at T-360 s, for the overlap mark)
                    left = 620 - 2 * k; ex = T - left * 1000 + rng.randint(-300, 300)
                    npolls += 1
                    if gap_at is not None and gap_at - 2 <= left <= gap_at + 12: continue
                    if rng.random() < 0.01: continue
                    drift = rng.choice([0, 0, 0, 0.01, -0.01]); mid = min(0.97, max(0.03, mid + drift))
                    for j in range(5):
                        if rng.random() < 0.15: ysz[j] = rng.choice([0.4, 5, 20, 60, 150, 400])
                        if rng.random() < 0.15: nsz[j] = rng.choice([0.4, 5, 20, 60, 150, 400])
                    sp = rng.choice([0.01, 0.01, 0.02, 0.03]); yb = round(mid - sp / 2, 2); nb = round(1 - (mid + sp / 2), 2)
                    lv = rng.choice([5, 5, 5, 3, 2, 1]); hole = rng.choice([0.01, 0.01, 0.02, 0.05])
                    ypx = [round(yb - (0 if j == 0 else hole + 0.01 * (j - 1)), 2) for j in range(5)]; npx = [round(nb - (0 if j == 0 else 0.01 * j), 2) for j in range(5)]
                    yrow = [("%.4f" % ypx[j], "%.2f" % ysz[j]) if (j < lv and ypx[j] > 0) else ("", "") for j in range(5)]
                    nrow = [("%.4f" % npx[j], "%.2f" % nsz[j]) if (j < lv and npx[j] > 0) else ("", "") for j in range(5)]
                    r = rng.random()
                    if r < 0.01: yrow = [("", "")] * 5                         # one-sided
                    elif r < 0.015: yrow = nrow = [("", "")] * 5                # empty book
                    recv = ex - off; hdr = "" if no_clock else format_datetime(datetime.fromtimestamp(ex // 1000, timezone.utc), usegmt=True)
                    B.append([recv - 120, recv, hdr, tk, series, iso] + [p for p, _ in yrow] + [s for _, s in yrow] + [p for p, _ in nrow] + [s for _, s in nrow])
                    first = recv if first is None else first; last = recv; nrows += 1
                    if abs(left - 480) <= 1: look = (float(yrow[0][1] or 0), float(nrow[0][1] or 0))
                    if rng.random() < 0.03:                                      # a sweep: one taker side, one second, two prices
                        side = rng.choice(["yes", "no"]); sec = datetime.fromtimestamp(ex // 1000, timezone.utc)
                        for px in (mid, mid + (0.01 if side == "yes" else -0.01)):
                            TR.append([tk, (sec + timedelta(milliseconds=rng.randint(0, 999))).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "%.4f" % px, "%.2f" % rng.choice([1, 5, 30]), side])
                    elif rng.random() < 0.05:
                        TR.append([tk, datetime.fromtimestamp(ex / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "%.4f" % mid, "3.00", rng.choice(["yes", "no"])])
                p_yes = mid
                if series == "KXBTC15M" and edge and look[0] != look[1]: p_yes = min(0.98, max(0.02, mid + (edge if look[0] > look[1] else -edge)))
                result = "yes" if rng.random() < p_yes else "no"
                if rng.random() < 0.004: result = rng.choice(["", "void"])
                ok = npolls if kind > 0.06 else int(npolls * 0.7); note = "" if kind > 0.08 or kind < 0.07 else rng.choice(["tape incomplete (HTTP 500)", "tape page cap", "joined late"])
                maxgap = rng.choice([2100, 2300, 4100]) if kind > 0.09 or kind < 0.085 else 26000
                pages = 1 if kind > 0.095 or kind < 0.09 else 0
                CV.append([iso, series, tk, npolls, ok, 0, 0, maxgap, first, last, nrows, pages, 0, 0, "0", "100.00", result, note])
                if rng.random() < 0.03: carry.append([iso, series, tk, npolls, int(npolls * rng.choice([0.6, 0.9])), 0, 0, maxgap, first, last, 0, pages, 0, 0, "0", "100.00", result, "joined late"])
        for name, cols, data in (("book", BOOK_COLS, B), ("trades", TRADE_COLS, TR), ("coverage", COVER_COLS, CV), ("clock", CLOCK_COLS, [[int(run_start.timestamp() * 1000), off]])):
            with gzip.open(os.path.join(d, name + ".csv.gz"), "wt", newline="") as f:
                w = csv.writer(f); w.writerow(cols); w.writerows(data)
        run_start += timedelta(hours=4)
    print("made-up DEPTH1 fixture written to %s: %d windows over both markets, seed %d, edge %s" % (out, n_windows, seed, edge))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5, float(sys.argv[3]) if len(sys.argv) > 3 else 0.0)
