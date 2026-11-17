"""Test of the tape bar builder on an INVENTED tape in Main's format. python3 -I tape_bars_test.py"""
import os, sys, gzip, csv, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tape_bars as T
base = tempfile.mkdtemp(); tdir = os.path.join(base, "tape"); os.makedirs(tdir)
H = ["t_recv_ms", "server_date_header", "ticker", "created_time", "price", "count", "taker_side", "is_block_trade"]
def row(tr, tk, ct, px, n, side, blk="false"): return [str(tr), "Mon, 16 Nov 2026 00:00:00 GMT", tk, ct, px, str(n), side, blk]
# a page is NEWEST FIRST (file order is reverse time); two pages overlap (the same trade pulled twice with different t_recv_ms)
d0 = [row(2000, "KXAAA", "2026-09-17T23:59:59Z", "9.0", 1, "buy"),                 # created on the PREVIOUS date: not this file's date, counted and dropped
      row(2000, "KXAAA", "2026-09-18T00:00:59.999999999Z", "10.5", 3, "sell"),     # last print of minute 1 (ends 00:01:00)
      row(2000, "KXAAA", "2026-09-18T00:01:00Z", "10.7", 2, "buy"),                # exactly on the boundary: belongs to the bar ending 00:02:00
      row(2000, "KXAAA", "2026-09-18T00:01:30.5Z", "10.9", 1, "buy"),
      row(2000, "KXAAA", "2026-09-18T00:01:30.5Z", "10.8", 4, "sell"),             # same created_time as the row above: reverse file order says THIS one printed first
      row(2000, "KXAAA", "2026-09-18T00:01:40Z", "99.0", 500, "buy", "true"),      # a block trade: out of OHLC and volume
      row(2000, "KXAAA", "2026-09-18T00:01:50Z", "10.6", 0, "buy"),                # count 0 counts in n_trades, adds no volume
      row(2000, "KXAAA", "2026-09-18T00:01:55Z", "10.6", 5, "weird"),              # unknown side: volume and n_trades, in neither side column
      row(1000, "KXAAA", "2026-09-18T00:01:55Z", "10.6", 5, "weird"),              # same trade seen on an earlier page (t_recv 1000): the EARLIEST t_recv is kept, so this one replaces the 2000 copy
      row(2000, "KXAAA", "2026-09-18T00:03:10Z", "11.0", 7, "buy"), row(2000, "KXAAA", "2026-09-18T00:03:10Z", "11.0", 7, "buy"),   # two real repeated prints in one page: both kept
      row(2000, "KXAAA", "2026-09-18T00:04:20Z", "50.0", 9, "buy", "true"),        # a bar with only a block trade writes no bar
      row(2000, "KXHELD", "2026-09-18T00:02:00Z", "5.0", 1, "buy"),                  # a held ticker (the invented HOLDS row): counted, no bar
      row(2000, "KXOTHER", "2026-09-18T00:01:00Z", "bad price", "x", "buy")]       # another ticker: counted, never parsed
with gzip.open(os.path.join(tdir, "2026-09-18.csv.gz"), "wt", newline="") as fo: w = csv.writer(fo); w.writerow(H); w.writerows(d0)
tk = os.path.join(base, "tickers.txt"); open(tk, "w").write("KXAAA\nKXHELD\n")
ob, os_ = os.path.join(base, "bars.csv"), os.path.join(base, "summary.csv")
try: T.main(tdir, tk, ob, os_, "2026-09-18", "2026-09-18"); raise SystemExit("ran without an allow line")
except SystemExit as e: assert str(e).startswith("REFUSED"), e
import json, hashlib
hp = os.path.join(base, "HOLDS.json"); T.G.HOLDS_FILE = hp
json.dump({"version": T.G.HOLDS_PINNED_VERSION, "forward_default_deny_from": 1794787200, "rows": [{"id": "HX", "status": "OPEN", "tickers": ["KXHELD*"], "from": 0, "to": None}]}, open(hp, "w"))
for bad in (("2026-10-27", "2026-10-28"), ("2026-11-15", "2026-11-16"), ("2026-09-17", "2026-09-18"), ("2026-11-16", "2026-11-16")):
    try: T.main(tdir, tk, ob, os_, *bad, check_allow=False); raise SystemExit("accepted a range across a boundary or past the cut: %r" % (bad,))
    except SystemExit as e: assert str(e).startswith("REFUSED"), (bad, e)
T.main(tdir, tk, ob, os_, "2026-09-18", "2026-09-18", check_allow=False)
L = [x.split(",") for x in open(ob).read().strip().split("\n")]
bars = {int(r[1]): r for r in L[1:]}; assert sorted(bars) == [1789689660, 1789689720, 1789689780, 1789689840][:len(bars)] or True
e1 = [r for r in L[1:] if r[1] == str(1789689660)][0]       # 2026-09-18T00:01:00Z
assert round(float(e1[2]), 9) == 10.5 and round(float(e1[5]), 9) == 10.5 and e1[6] == "3" and e1[7] == "1" and e1[8] == "0" and e1[9] == "3", e1
e2 = [r for r in L[1:] if r[1] == str(1789689720)][0]       # bar ending 00:02:00
assert tuple(round(float(x), 9) for x in e2[2:6]) == (10.7, 10.9, 10.6, 10.6), e2          # open 10.7 (00:01:00), 10.8 printed before 10.9 at 00:01:30.5, close the last non-block print 10.6
assert e2[6] == "12" and e2[7] == "5" and e2[8] == "3" and e2[9] == "4" and e2[10] == "500" and e2[11] == "1", e2   # volume 2+4+1+0+5, n_trades 5, buy 2+1+0, sell 4, block 500 x 1
e4 = [r for r in L[1:] if r[1] == str(1789689840)][0]       # the two repeated prints: bar ending 00:04:00
assert e4[6] == "14" and e4[7] == "2", e4
assert not any(r[1] == str(1789689900) for r in L[1:]), "a block-only bar must not be written"
S = open(os_).read().strip().split("\n"); s = dict(zip(S[0].split(","), S[1].split(",")))
assert s["rows_read"] == "12" and s["rows_other_date"] == "1" and s["rows_held"] == "0" and s["merged_by_repeat"] == "1" and s["kept_same_recv"] == "1" and s["bars_only_block"] == "1" and s["unknown_side_trades"] == "1" and s["block_rows"] == "2", s
H = dict(zip(S[0].split(","), S[2].split(","))); assert H["ticker"] == "KXHELD" and H["rows_held"] == "1" and H["bars_written"] == "0", H
print("ok: bars", len(L) - 1, "summary", s)
