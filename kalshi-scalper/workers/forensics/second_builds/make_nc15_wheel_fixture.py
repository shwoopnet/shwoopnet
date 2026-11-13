#!/usr/bin/env python3
"""A MADE-UP fixture for the NC15 depth-cell wheel replay, in the NC15 recorder's folder and column shape (scripts/record_nc_book.py on main):
<out>/<date>/<HHMM>/{book,coverage,clock}.csv.gz plus the marker file MADE_UP_DATA. Nothing here is real: books, clocks and results are invented so two independent
scorers can be run on the same rows. usage: python3 -I make_nc15_wheel_fixture.py <out dir> [seed]      read it with --now 2026-12-23T00:00:00Z
Runs are 4 hours long from 2026-11-12T20:00Z to 2026-12-22T20:00Z, so some windows decide before the sheet's commit time (2026-11-13T00:23:49Z) and must not count.
Each series has its own rate and its own made-up edge, so the places end differently: a block that clears and confirms, one that clears and fails its confirmation, blocks
that fail on the profit factor, a dense place whose 60 signals fall on fewer than 7 days, a sparse place whose 60 signals span more than 21 days, a place still in progress.
Planted on purpose: runs with different clock offsets, a run with no Date header (no clock), a ticker recorded in two run folders, windows with no poll in the 10 s before
the decision, a next poll later than 6 s (and one exactly 6.000 s, one 6.001 s), a missing side, an empty book, |imb5| exactly 0.50 and just under, asks exactly 0.10 and
0.90 and just outside, exactly 10 contracts at or under the limit and 9.99, fractional sizes, a second poll one cent worse (the worse of the two is paid), a second poll
two cents worse or drained (a miss), results that are empty and recent (open), empty and older than 7 days (void), "void" and "scalar", the four withdrawn series, weekends."""
import sys, os, csv, gzip, random
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime

BOOK_COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "series", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] \
    + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
COVER_COLS = ["close_time", "series", "ticker", "polls", "ok_polls", "n429", "batch_fallback", "max_gap_ms", "first_recv_ms", "last_recv_ms", "book_rows",
              "tape_pages", "tape_trades", "dupes_dropped", "tape_sum_count", "volume_fp", "result", "note"]
# series: (chance a window is in the cell, made-up edge of the bought side, trades on weekends)
PROFILE = {"KXCOPPER15M": (0.10, 0.22, False), "KXWTI15M": (0.10, 0.00, False), "KXNATGAS15M": (0.75, 0.10, False), "KXHYPE15M": (0.028, 0.05, True), "KXBNB15M": (0.085, 0.45, True),
           "KXSILVER15M": (0.10, -0.10, False), "KXUSDCAD15M": (0.11, 0.27, False),      # USD/CAD's made-up edge turns negative on Dec 1 (in the code below): a block can clear and its confirmation fail
           "KXEURUSD15M": (0.05, 0.0, False), "KXGBPUSD15M": (0.05, 0.0, False), "KXUSDJPY15M": (0.05, 0.0, False), "KXAUDUSD15M": (0.05, 0.0, False)}
NOW = datetime(2026, 12, 23, tzinfo=timezone.utc)


def main(out, seed):
    rng = random.Random(seed); os.makedirs(out); open(os.path.join(out, "MADE_UP_DATA"), "w").write("invented rows for a build comparison; nothing here is real\n")
    run_start = datetime(2026, 11, 12, 20, 0, tzinfo=timezone.utc); end = datetime(2026, 12, 22, 20, 0, tzinfo=timezone.utc); nrun = 0; nwin = 0; special = 0; carry = []
    while run_start < end:
        d = os.path.join(out, run_start.strftime("%Y-%m-%d"), run_start.strftime("%H%M")); os.makedirs(d)
        off = (-900, -350, 0, 250, 700, 1400)[nrun % 6]; no_clock = (nrun % 37 == 5); nrun += 1; B, CV = list(carry), []; carry = []
        t = run_start
        while t < run_start + timedelta(hours=4):
            t += timedelta(minutes=15); T = int(t.timestamp() * 1000); iso = t.strftime("%Y-%m-%dT%H:%M:%SZ")
            for series, (pcell, edge, weekend) in PROFILE.items():
                if not weekend and t.weekday() >= 5: continue
                nwin += 1; tk = "%s-%s-00" % (series, t.strftime("%y%b%d%H%M").upper()); kind = rng.random(); in_cell = rng.random() < pcell
                side = rng.choice(["yes", "no"]); ask = rng.choice([0.12, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.88]); sp = rng.choice([0.01, 0.02, 0.03])
                heavy = [rng.choice([80, 150, 300, 500]) for _ in range(5)]; thin = [rng.choice([0.4, 3.5, 6, 12, 20, 40]) for _ in range(rng.choice([5, 4, 3, 2]))]
                if not in_cell: thin = [round(h * rng.choice([0.7, 0.9, 1.0, 1.1, 1.3]), 2) for h in heavy]      # a balanced book: |imb5| stays far under 0.50
                plant = None
                if in_cell and kind < 0.30:
                    plant = rng.choice(["imb_050", "imb_0499", "ask_010", "ask_090", "ask_009", "ask_091", "ten_exact", "ten_short", "gap_6000", "gap_6001", "gap_late", "second_1c", "second_2c", "second_drained",
                                        "missing_side", "empty_book", "no_poll", "two_runs"]); special += 1
                if plant == "imb_050": heavy, thin = [100, 20, 15, 10, 5], [20, 12, 8, 6, 4]
                if plant == "imb_0499": heavy, thin = [100, 20, 15, 10, 4.9], [20, 12, 8, 6, 4.1]
                if plant in ("ask_010", "ask_090", "ask_009", "ask_091"): ask = {"ask_010": 0.10, "ask_090": 0.90, "ask_009": 0.09, "ask_091": 0.91}[plant]
                if plant == "ten_exact": thin = [6, 4, 50]
                if plant == "ten_short": thin = [6, 3.99, 50]
                # the bought side's ask is `ask`: the met side's best bid is 1 - ask; the heavy side's best bid sits `sp` under the bought side's ask
                met_px = [round(1 - ask - 0.01 * j, 2) for j in range(5)]; own_px = [round(ask - sp - 0.01 * j, 2) for j in range(5)]
                def book(thin_now, shift=0.0):
                    met = [("%.4f" % round(met_px[j] - shift, 2), "%.2f" % thin_now[j]) if j < len(thin_now) and met_px[j] - shift > 0.005 else ("", "") for j in range(5)]
                    own = [("%.4f" % own_px[j], "%.2f" % heavy[j]) if own_px[j] > 0.005 else ("", "") for j in range(5)]
                    return (own, met) if side == "yes" else (met, own)           # (yes levels, no levels): a YES buy meets the NO bids
                first = last = None; n = 0; lookk = None
                grid = [640 - 5 * k for k in range(17)]                           # polls about every 5 s from T-640 s to T-560 s; the signal poll is the one just before T-600 s
                jit = {left: rng.randint(-300, 300) for left in grid}
                rows = []
                for left in grid:
                    ex = T - left * 1000 - 1500 + jit[left]                       # exchange time, 1.2 to 1.8 s before the grid point: the poll before T-600 s lands 1.2 to 1.8 s before the decision
                    if plant == "no_poll" and 598 <= left <= 615: continue
                    after = left < 600                                            # polls after the decision
                    if plant in ("gap_6000", "gap_6001", "gap_late") and left == 595: continue
                    thin_now = list(thin); shift = 0.0
                    if after:
                        if plant == "second_1c": shift = 0.01
                        elif plant == "second_2c": shift = 0.02
                        elif plant == "second_drained": thin_now = [0.4, 0.4]
                        elif plant is None and rng.random() < 0.25: shift = rng.choice([0.01, 0.01, 0.02]) if rng.random() < 0.6 else 0.0; thin_now = thin_now if shift else [x * rng.choice([0.2, 1, 1]) for x in thin_now]
                    y, nn = book(thin_now, shift)
                    if plant == "missing_side" and left == 600: y, nn = (([("", "")] * 5, nn) if side == "yes" else (y, [("", "")] * 5))      # the heavy side vanishes at the signal poll
                    if plant == "empty_book" and left == 600: y = nn = [("", "")] * 5
                    rows.append([left, ex, y, nn])
                if plant in ("gap_6000", "gap_6001", "gap_late"):                 # the poll after the signal poll is placed exactly 6.000 s, 6.001 s or 9 s after it on the recorder's clock
                    sig = next(r for r in rows if r[0] == 600); nxt = next(r for r in rows if r[0] == 590)
                    nxt[1] = sig[1] + {"gap_6000": 6000, "gap_6001": 6001, "gap_late": 9000}[plant]
                for left, ex, y, nn in rows:
                    recv = ex - off; hdr = "" if no_clock else format_datetime(datetime.fromtimestamp(ex // 1000, timezone.utc), usegmt=True)
                    line = [recv - 120, recv, hdr, tk, series, iso] + [p for p, _ in y] + [s for _, s in y] + [p for p, _ in nn] + [s for _, s in nn]
                    if plant == "two_runs" and left <= 590: carry.append(line)   # the later polls of this window are in the NEXT run folder (its clock differs)
                    else: B.append(line)
                    first = recv if first is None else first; last = recv; n += 1
                age_days = (NOW - t).total_seconds() / 86400.0; r = rng.random()
                p_win = min(0.97, max(0.03, ask + (-0.25 if (series == "KXUSDCAD15M" and t >= datetime(2026, 12, 1, tzinfo=timezone.utc)) else edge))); res = side if rng.random() < p_win else ("no" if side == "yes" else "yes")
                if age_days < 1.0: res = ""                                      # closed in the last day before the read: still open
                elif r < 0.004: res = ""                                         # never given a result: a void once 7 days old, open before that
                elif r < 0.007: res = rng.choice(["void", "scalar"])
                CV.append([iso, series, tk, n, n, 0, 0, 5300, first, last, n, 1, 0, 0, "0", "100.00", res, ""])
        B.sort(key=lambda x: x[1])
        for name, cols, data in (("book", BOOK_COLS, B), ("coverage", COVER_COLS, CV), ("clock", ["t_local_ms", "offset_ms"], [[int(run_start.timestamp() * 1000), off]])):
            with gzip.open(os.path.join(d, name + ".csv.gz"), "wt", newline="") as f:
                w = csv.writer(f); w.writerow(cols); w.writerows(data)
        run_start += timedelta(hours=4)
    print("made-up NC15 wheel fixture written to %s: %d run folders, %d windows over 11 series, %d planted cases, seed %d; read it with --now 2026-12-23T00:00:00Z" % (out, nrun, nwin, special, seed))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5)
