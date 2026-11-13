#!/usr/bin/env python3
"""A MADE-UP fixture for DEPTH1's exact-tie cases (Amendment 4), in the R6 recorder's folder and column shape, with the marker file MADE_UP_DATA. Nothing here is real.
usage: python3 -I make_depth1_tie_fixture.py <out dir> [seed]
What is planted, and what a correct build must print:
 1. BITCOIN f7 (tape sweeps) is built so its profit factor is EXACTLY 1.5 in whole cents, pooled and in each of the three blocks: in each block 420 windows carry one sweep and a
    fixed book whose bought side asks exactly 0.50 (fee 2c: a win is +0.48, a loss is -0.52); 260 win and 160 lose (260 x 48 = 12480, 160 x 52 = 8320, 2 x 12480 = 3 x 8320).
    Half the sweeps are taker-yes (buy YES) and half taker-no (buy NO), so the sign carries the result and the shuffled-book control can be passed. In floating point the same
    sums read 1.4999999999999998, so a build that compares floats says "bar not met" and a build that compares whole cents says "BAR MET". No other feature fires in those windows
    (the book is symmetric), and no other Bitcoin window has any trade on the tape.
 2. GOLD f6: five windows where the 5 level size sums 60 s before the look are 0.10 + 0.20 on the YES side and 0.30 on the NO side: equal, but not equal in floats. With the tie
    rule f6 is zero there (no trade); a build with an exact comparison trades all five.
 Everything else is plain: every poll present, every run has a clock, every coverage row is usable, every result is yes or no. The other Bitcoin windows have the same
 symmetric book and no tape, so Bitcoin's nine book features never trade and the shuffled-book control is passed with room to spare (the tie is the only delicate thing)."""
import sys, os, csv, gzip, random
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from zoneinfo import ZoneInfo

BOOK_COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "series", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["yes_bid_sz_%d" % i for i in range(1, 6)] \
    + ["no_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_sz_%d" % i for i in range(1, 6)]
TRADE_COLS = ["ticker", "created_time", "yes_price_dollars", "count_fp", "taker_outcome_side"]
COVER_COLS = ["close_time", "series", "ticker", "polls", "ok_polls", "n429", "batch_fallback", "max_gap_ms", "first_recv_ms", "last_recv_ms", "book_rows",
              "tape_pages", "tape_trades", "dupes_dropped", "tape_sum_count", "volume_fp", "result", "note"]
CT = ZoneInfo("America/Chicago")
BLOCKS = (("2026-10-30", "2026-11-03"), ("2026-11-04", "2026-11-08"), ("2026-11-09", "2026-11-13"))
RECORDER_END = datetime(2026, 11, 13, 23, 59, tzinfo=timezone.utc)
PER_BLOCK = 420                                   # 21 x 20: 260 wins and 160 losses


def levels(touch, sizes):
    return [("%.4f" % round(touch - 0.01 * j, 2), "%.2f" % sizes[j]) if j < len(sizes) else ("", "") for j in range(5)]


def main(out, seed):
    rng = random.Random(seed); os.makedirs(out); open(os.path.join(out, "MADE_UP_DATA"), "w").write("invented rows for a build comparison (exact-tie cases); nothing here is real\n")
    run_start = datetime(2026, 10, 29, 20, 0, tzinfo=timezone.utc); end = datetime(2026, 11, 14, 8, 0, tzinfo=timezone.utc)
    used = [0, 0, 0]; f6_left = 5; nrun = 0; counts = {"btc_designated": 0, "gold_f6_tie": 0, "windows": 0}
    while run_start < end:
        d = os.path.join(out, run_start.strftime("%Y-%m-%d"), run_start.strftime("%H%M")); os.makedirs(d)
        off = (-900, -350, 0, 250, 700, 1400)[nrun % 6]; nrun += 1; B, TR, CV = [], [], []; t = run_start
        while t < run_start + timedelta(hours=4):
            t += timedelta(minutes=15); T = int(t.timestamp() * 1000); iso = t.strftime("%Y-%m-%dT%H:%M:%SZ"); date = t.astimezone(CT).strftime("%Y-%m-%d")
            blk = next((i for i, (lo, hi) in enumerate(BLOCKS) if lo <= date <= hi), None); eligible = blk is not None and t - timedelta(seconds=900) < RECORDER_END
            for series in ("KXGOLD15M", "KXBTC15M"):
                counts["windows"] += 1; tk = "%s-%s-00" % (series, t.strftime("%y%b%d%H%M").upper()); kind = "plain"; sweep = None
                if series == "KXBTC15M" and eligible and used[blk] < PER_BLOCK:
                    j = used[blk]; used[blk] += 1; counts["btc_designated"] += 1
                    win = (j * 13) % 21 < 13; side = "yes" if j % 2 == 0 else "no"; kind = "btc_" + side; sweep = side
                    result = side if win else ("no" if side == "yes" else "yes")
                elif series == "KXGOLD15M" and eligible and blk == 1 and f6_left > 0 and t.minute == 0:
                    f6_left -= 1; counts["gold_f6_tie"] += 1; kind = "gold_f6"; result = rng.choice(["yes", "no"])
                mid = rng.choice([0.5, 0.5, 0.42, 0.61, 0.3, 0.74]); ysz = [rng.choice([5, 20, 60, 150, 400]) for _ in range(5)]; nsz = [rng.choice([5, 20, 60, 150, 400]) for _ in range(5)]
                first = last = None; n = 0
                for k in range(0, 136):                                          # polls every 2 s from T-620 s to T-350 s, none missing
                    left = 620 - 2 * k; ex = T - left * 1000 + rng.randint(-300, 300); n += 1
                    if kind == "btc_yes" or (kind == "plain" and series == "KXBTC15M"): yrow, nrow = levels(0.49, [100] * 5), levels(0.50, [100] * 5)   # YES ask = 1 - 0.50 = 0.50; every book feature is zero (plain Bitcoin windows too, so only f7 trades in Bitcoin)
                    elif kind == "btc_no": yrow, nrow = levels(0.50, [100] * 5), levels(0.49, [100] * 5)                # NO ask = 1 - 0.50 = 0.50
                    elif kind == "gold_f6":
                        if left >= 520: yrow, nrow = levels(0.45, [0.10, 0.20]), levels(0.53, [0.30])                    # 60 s before the look: 0.1 + 0.2 against 0.3, a tie that floats do not see
                        else: yrow, nrow = levels(0.45, [5.00, 5.00]), levels(0.53, [2.00])                              # at the look: the NO side grew, so an untied f6 is negative and buys NO
                    else:
                        mid = min(0.9, max(0.1, mid + rng.choice([0, 0, 0, 0.01, -0.01])))
                        for q in range(5):
                            if rng.random() < 0.15: ysz[q] = rng.choice([5, 20, 60, 150, 400])
                            if rng.random() < 0.15: nsz[q] = rng.choice([5, 20, 60, 150, 400])
                        sp = rng.choice([0.01, 0.02, 0.03]); lv = rng.choice([5, 5, 4, 3, 2])
                        yrow, nrow = levels(round(mid - sp / 2, 2), ysz[:lv]), levels(round(1 - (mid + sp / 2), 2), nsz[:lv])
                    recv = ex - off; hdr = format_datetime(datetime.fromtimestamp(ex // 1000, timezone.utc), usegmt=True)
                    B.append([recv - 120, recv, hdr, tk, series, iso] + [p for p, _ in yrow] + [s for _, s in yrow] + [p for p, _ in nrow] + [s for _, s in nrow])
                    first = recv if first is None else first; last = recv
                    if series == "KXGOLD15M" and kind == "plain" and rng.random() < 0.03:                               # gold: ordinary sweeps on both sides
                        s_ = rng.choice(["yes", "no"]); sec = datetime.fromtimestamp(ex // 1000, timezone.utc)
                        for px in (mid, mid + (0.01 if s_ == "yes" else -0.01)):
                            TR.append([tk, (sec + timedelta(milliseconds=rng.randint(0, 999))).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "%.4f" % px, "5.00", s_])
                if sweep:                                                        # one sweep about 20 s before the look: same taker side, same second, two prices
                    sec = datetime.fromtimestamp((T - 500 * 1000) // 1000, timezone.utc)
                    for ms, px in ((100, 0.50), (600, 0.51 if sweep == "yes" else 0.49)):
                        TR.append([tk, (sec + timedelta(milliseconds=ms)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "%.4f" % px, "5.00", sweep])
                if kind == "plain": result = "yes" if rng.random() < mid else "no"
                CV.append([iso, series, tk, n, n, 0, 0, 2300, first, last, n, 1, 0, 0, "0", "100.00", result, ""])
        for name, cols, data in (("book", BOOK_COLS, B), ("trades", TRADE_COLS, TR), ("coverage", COVER_COLS, CV), ("clock", ["t_local_ms", "offset_ms"], [[int(run_start.timestamp() * 1000), off]])):
            with gzip.open(os.path.join(d, name + ".csv.gz"), "wt", newline="") as f:
                w = csv.writer(f); w.writerow(cols); w.writerows(data)
        run_start += timedelta(hours=4)
    assert used == [PER_BLOCK] * 3 and f6_left == 0, (used, f6_left)
    print("made-up DEPTH1 tie fixture written to %s: %d windows; Bitcoin windows with a planted sweep %d (420 a block: 260 wins, 160 losses, all at an ask of 0.50); gold windows with an f6 size tie %d; seed %d" % (
        out, counts["windows"], counts["btc_designated"], counts["gold_f6_tie"], seed))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5)
