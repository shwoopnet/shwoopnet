#!/usr/bin/env python3
"""Invented tape in the real layout (seeded, no real data): tape/YYYY-MM-DD.csv.gz, ONE file per UTC date holding all tickers, columns t_recv_ms, server_date_header, ticker, created_time, price, count, taker_side, is_block_trade, rows newest first within each page, pages with an overlap (the same rows again with a later t_recv_ms), genuine repeats (same row and same t_recv_ms), fractions of 0 to 9 digits, block trades, count 0, unknown taker_side, trades on exact minute boundaries, a ticker outside the wall. python3 tape_fixture_second.py <out dir>"""
import csv, gzip, os, random, sys
def build(out):
    rnd = random.Random(20261117); H = ["t_recv_ms", "server_date_header", "ticker", "created_time", "price", "count", "taker_side", "is_block_trade"]
    os.makedirs(os.path.join(out, "tape"), exist_ok=True)
    for day in ("2026-10-05", "2026-10-06"):
        trades = []; px = {"KXGOLDPERP": 40.0, "KXUS500PERP": 13.4, "KXUSTECH100PERP": 3.8, "KXOTHERPERP": 5.0}
        for sec in range(0, 1800):
            for tk in px:
                if rnd.random() < 0.08:
                    px[tk] = round(px[tk] * (1 + rnd.gauss(0, 0.0003)), 4); frac = rnd.choice(("", ".5", ".123", ".000000001", ".999999999", ".25"))
                    t = "%sT%02d:%02d:%02d%sZ" % (day, 12 + sec // 3600, (sec % 3600) // 60, sec % 60, frac)
                    row = [tk, t, repr(px[tk]), str(rnd.choice((0, 1, 1, 2, 5, 12))), rnd.choice(("buy", "sell", "buy", "sell", "", "x")), rnd.choice(("false",) * 12 + ("true", "TRUE", "False"))]
                    trades.append(row)
                    if rnd.random() < 0.05: trades.append(list(row))                       # a genuine repeat inside one page
        d0 = int(day[-2:]); trades.append(["KXGOLDPERP", "2026-10-%02dT23:59:59Z" % (d0 - 1), "40.0", "1", "buy", "false"]); trades.append(["KXGOLDPERP", "2026-10-%02dT00:00:01Z" % (d0 + 1), "40.1", "2", "sell", "false"])        # midnight overlap rows of the neighbouring dates
        rows = []; page = 0
        for i in range(0, len(trades), 40):
            chunk = trades[i:i + 40]; page += 1; recv = 1000 * page
            for r in reversed(chunk): rows.append([str(recv), "Mon, 16 Nov 2026 00:00:00 GMT"] + r)           # newest first within the page
            if i >= 40 and rnd.random() < 0.6:                                                              # the next page overlaps the previous page's last rows
                page += 1; recv = 1000 * page
                for r in reversed(trades[i - 5:i + 35]): rows.append([str(recv), "Mon, 16 Nov 2026 00:00:00 GMT"] + r)
        with gzip.open(os.path.join(out, "tape", day + ".csv.gz"), "wt", newline="") as f:
            w = csv.writer(f); w.writerow(H); w.writerows(rows)
if __name__ == "__main__": build(sys.argv[1])
