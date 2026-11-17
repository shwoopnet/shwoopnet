#!/usr/bin/env python3
"""MECH1 fast-clock feasibility, cost part (Idea Desk C, Nov 17, 2026). COUNTS AND MEDIANS ONLY, from bid and ask columns: never a result, a trade price, a last price, a volume or a price change.
Per source family it prints the median half spread-free round-trip cost inputs: for the 15 minute binary books the median spread (cents a contract) and the median fee per contract at the ask, for
the perps candles the median spread in basis points of the mid (round trip taker = 2 x 12 bp + spread), for the in-game books the median spread in cents and fee.
Reads, by index from csv.reader, only these columns. nc15 book.csv.gz: series, close_time, t_recv_ms, yes_bid_px_1..5, no_bid_px_1..5 (only KXHYPE15M, KXBNB15M, KXNATGAS15M; other series are counted, never parsed).
kalshi1m: ticker, end_period_ts, bid_close, ask_close. ingame obs.csv.gz: kind, yes_bid, yes_ask. Usage: python3 -I fastclock_cost.py <nc15 root> <perp-data root> <ingame root>"""
import csv, glob, gzip, json, math, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calendar, time
import engine1_core as K

WALL = ("KXHYPE15M", "KXBNB15M", "KXNATGAS15M")
DEV_END = 1794787199                                                         # development cut, as the other cards
H16_START = 1797897600
TAKER_BP = 12.0


def fee_pc(p):                                                               # fee per contract at 10 contracts (the repo's fee function)
    return K.fee_up_order(p, 10) / 10.0


def iso(s):
    return calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))


def med(xs):
    return None if not xs else statistics.median(xs)


def nc15(root):
    spreads, fees, n, outside = [], [], 0, {}
    for f in sorted(glob.glob(os.path.join(root, "*", "*", "book.csv.gz"))):
        with gzip.open(f, "rt", newline="") as fh:
            rd = csv.reader(fh); hdr = next(rd)
            c = {k: hdr.index(k) for k in ["t_recv_ms", "series", "close_time"] + ["yes_bid_px_%d" % i for i in range(1, 6)] + ["no_bid_px_%d" % i for i in range(1, 6)]}
            for r in rd:
                s = r[c["series"]]
                if s not in WALL:
                    outside[s] = outside.get(s, 0) + 1
                    continue
                ct = iso(r[c["close_time"]])
                if ct > DEV_END:
                    continue
                left = ct - int(r[c["t_recv_ms"]]) / 1000.0
                if not (120 <= left <= 900):
                    continue
                yb = [float(r[c["yes_bid_px_%d" % i]]) for i in range(1, 6) if r[c["yes_bid_px_%d" % i]] != ""]
                nb = [float(r[c["no_bid_px_%d" % i]]) for i in range(1, 6) if r[c["no_bid_px_%d" % i]] != ""]
                if not yb or not nb:
                    continue
                y, nn = max(yb), max(nb)
                ya, na = 1 - nn, 1 - y                                         # YES ask and NO ask
                if y <= ya:
                    spreads.append(round(ya - y, 6)); fees.append(fee_pc(round(ya, 6)))
                    n += 1
    return {"rows_used": n, "median_spread_cents": None if not spreads else 100 * med(spreads), "median_fee_cents_per_contract_at_ask": None if not fees else 100 * med(fees),
            "round_trip_cents_median_if_sold": None if not spreads else 100 * (med(spreads) + 2 * med(fees)), "round_trip_cents_median_if_held": None if not spreads else 100 * (med(spreads) / 2 + med(fees)),
            "rows_outside_wall_counted_not_parsed": dict(sorted(outside.items()))}


def perps(root):
    by = {}
    for sub in ("kalshi1m",):
        for f in sorted(glob.glob(os.path.join(root, sub, "*.csv.gz"))):
            with gzip.open(f, "rt", newline="") as fh:
                rd = csv.reader(fh); hdr = next(rd)
                it, ie, ib, ia = (hdr.index(k) for k in ("ticker", "end_period_ts", "bid_close", "ask_close"))
                for r in rd:
                    try:
                        ts, b, a = int(r[ie]), float(r[ib]), float(r[ia])
                    except ValueError:
                        continue
                    if ts > DEV_END or ts >= H16_START or not (0 < b <= a < 1e9):
                        continue
                    by.setdefault(r[it], []).append(1e4 * (a - b) / ((a + b) / 2))
    return {n: {"candles": len(v), "median_spread_bp": med(v), "round_trip_taker_bp": 2 * TAKER_BP + med(v)} for n, v in sorted(by.items())}


H04_FROM = "2026-11-12"                                                      # H04 holds in-game rows of KXNBATOTAL, KXNFLTOTAL, KXNHLGAME, KXNHLTOTAL and the spread series from 1794528000 (2026-11-12 00:00Z)


def ingame(root):
    """walks the <date> level of the path only (no ticker or time column is read): a folder dated on or after 2026-11-12 is skipped and counted; an unparseable date REFUSES"""
    sp, fe, skipped = [], [], 0
    for f in sorted(glob.glob(os.path.join(root, "*", "*", "obs.csv.gz"))):
        day = os.path.basename(os.path.dirname(os.path.dirname(f)))
        try:
            time.strptime(day, "%Y-%m-%d")
        except ValueError:
            raise SystemExit("REFUSED: cannot parse the date of folder %r" % day)
        if day >= H04_FROM:
            skipped += 1
            continue
        with gzip.open(f, "rt", newline="") as fh:
            rd = csv.reader(fh); hdr = next(rd)
            ik, ib, ia = hdr.index("kind"), hdr.index("yes_bid"), hdr.index("yes_ask")
            for r in rd:
                if not r[ib] or not r[ia]:
                    continue
                b, a = float(r[ib]), float(r[ia])
                if 0 < b <= a < 1:
                    sp.append(a - b); fe.append(fee_pc(a))
    return {"folders_skipped_h04": skipped, "rows_used": len(sp), "median_spread_cents": None if not sp else 100 * med(sp), "median_fee_cents_per_contract_at_ask": None if not fe else 100 * med(fe),
            "round_trip_cents_median_if_sold": None if not sp else 100 * (med(sp) + 2 * med(fe))}


if __name__ == "__main__":
    print(json.dumps({"nc15_three_series": nc15(sys.argv[1]), "perps_by_name": perps(sys.argv[2]), "ingame": ingame(sys.argv[3])}, sort_keys=True))
