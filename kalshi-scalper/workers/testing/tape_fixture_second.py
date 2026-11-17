#!/usr/bin/env python3
"""Invented tape (seeded, no real data): tape/<UTC date>/<ticker>.csv.gz for 3 tickers over 2 UTC dates, with fractions of 0 to 9 digits, block trades, a duplicated page, a duplicate that differs, count 0, unknown taker_side, trades on exact minute boundaries. python3 tape_fixture_second.py <out dir>"""
import csv, gzip, os, random, sys
def build(out):
    rnd = random.Random(20261117); H = ["ticker", "trade_id", "created_time", "price", "count", "taker_side", "is_block_trade"]
    for day in ("2026-11-17", "2026-11-18"):
        os.makedirs(os.path.join(out, "tape", day), exist_ok=True)
        for tk, base in (("KXGOLDPERP", 40.0), ("KXUS500PERP", 13.4), ("KXUSTECH100PERP", 3.8)):
            rows = []; px = base; n = 0
            for sec in range(0, 3600, rnd.choice((3, 5, 7))):
                for k in range(rnd.choice((0, 1, 1, 2, 4))):
                    n += 1; px = round(px * (1 + rnd.gauss(0, 0.0003)), 4); frac = rnd.choice(("", ".5", ".123", ".000000001", ".999999999", ".25"))
                    t = "%sT%02d:%02d:%02d%sZ" % (day, 12 + sec // 3600, (sec % 3600) // 60, sec % 60, frac)
                    rows.append([tk, "%s-%s-%d" % (tk[2:6], day[-2:], n), t, repr(px), str(rnd.choice((0, 1, 1, 2, 5, 12))), rnd.choice(("buy", "sell", "buy", "sell", "", "x")), rnd.choice(("false",) * 12 + ("true", "TRUE", "False"))])
            rows += [list(r) for r in rows[:5]]; d = list(rows[7]); d[3] = repr(float(d[3]) + 0.01); rows.append(d)
            with gzip.open(os.path.join(out, "tape", day, tk + ".csv.gz"), "wt", newline="") as f:
                w = csv.writer(f); w.writerow(H); w.writerows(rows)
if __name__ == "__main__": build(sys.argv[1])
