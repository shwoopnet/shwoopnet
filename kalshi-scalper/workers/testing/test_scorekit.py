"""Synthetic tests for scorekit.py (made-up data only; no Kalshi, no real file opened). Run: python3 -W ignore test_scorekit.py"""
import gzip, json, os, random, tempfile
import scorekit as k

def mkrun(d, rows_bodies):
    rows = []
    for i, (rid, body) in enumerate(rows_bodies):
        f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(body)); rows.append({"id": rid, "status": 200, "file": f})
    rows.append({"id": "bad", "status": 429})
    json.dump({"job": {}, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))

with tempfile.TemporaryDirectory() as d:
    c = lambda ts, b, a: {"end_period_ts": ts, "yes_bid": {"close_dollars": str(b), "low_dollars": str(b - .01)}, "yes_ask": {"close": int(a * 100)}, "volume_fp": "5"}
    mkrun(d, [("b0", {"markets": [{"market_ticker": "T-1", "candlesticks": [c(100, .4, .42), c(160, .41, .43)]}]}), ("T-2", {"candlesticks": [c(100, .1, .2)]}),
              ("l", {"markets": [{"ticker": "KXA-26NOV-T4", "event_ticker": "KXA-26NOV", "open_time": "2026-11-01T00:00:00Z", "close_time": "2026-11-05T12:00:00Z", "result": "yes", "strike_type": "greater", "floor_strike": 4.4, "volume_fp": "900", "title": "x"}]}),
              ("ob", {"orderbook": {"yes": [[40, 5], [45, 9]], "no": [[50, 7]]}, "ts": 7})])
    cs = k.candles(d); assert [x["ts"] for x in cs["T-1"]] == [100, 160] and abs(cs["T-1"][0]["ask"] - .42) < 1e-9 and cs["T-2"][0]["ask"] == .2 and cs["T-1"][0]["bid_low"] == .39   # cents and dollars both read
    ms0 = k.markets(d); assert ms0["KXA-26NOV-T4"]["settlement_ts"] is None          # absent = None: scorers fail closed
    ms = k.markets(d); assert ms["KXA-26NOV-T4"]["close"] == 1793880000 and ms["KXA-26NOV-T4"]["floor"] == 4.4 and ms["KXA-26NOV-T4"]["series"] == "KXA"
    bk = k.books(d); assert bk["ob"][0]["yes_bids"][0] == (0.45, 9.0) and bk["ob"][0]["no_bids"] == [(0.5, 7.0)]
    assert len(list(k.iter_answers(d))) == 4              # the 429 row is skipped

# arithmetic: win at .5, loss at .5
t = [{"event": "a", "ts": 1, "price": .5, "win": True}, {"event": "b", "ts": 2, "price": .5, "win": False}]
fee5 = .07 * .25
assert abs(k.net_of(t[0]) - (.5 - fee5)) < 1e-12 and abs(k.net_of(t[1]) + (.5 + fee5)) < 1e-12 and abs(k.net_of({"net": .1, "event": "x"}, .01) - .09) < 1e-12
assert abs(k.stats(t)["pf"] - (.5 - fee5) / (.5 + fee5)) < 1e-3

random.seed(3)
def mk(n, edge, nclusters=40, price=.5):
    out = []
    for i in range(n):
        out.append({"event": "E%d" % i, "cluster": "C%d" % (i % nclusters), "ts": 1000 + i, "price": price, "win": random.random() < price + edge})
    return out
small = k.score(mk(60, .2), {"name": "s"})
assert small["label"] == "no evidence at n = 60" and small["haircut_line"]["label_on_this_line"] == "no evidence at n = 40"
big_good = k.score(mk(4000, .25, 200), {"name": "g", "price_source": "R6 book", "freshness": "within 2 s"})
assert big_good["label"].startswith("PASS"), big_good["label"]
assert len(big_good["windows"]) == 3 and sum(w["n"] for w in big_good["windows"]) == 4000
bad = k.score(mk(300, -.15), {}); assert bad["label"].startswith("FALSIFIED"), bad["label"]
mid = k.score(mk(300, .02), {"registered_bar": {"pf": 1.0, "z": 0.0}}); assert mid["label"].startswith(("cleared its registered bar", "NO SURVIVOR", "FALSIFIED")), mid["label"]
assert set(small["haircut_table_no_book"]) >= {"+1c limit, 2 s arrival", "+1c limit, 6 s arrival"} and small["haircut_table_no_book"]["+1c limit, 2 s arrival"]["n_after_drop"] == 51.0
assert "NOT STATED" in bad["price_source"] and "NOT PROVIDED" in bad["book_replay_line"]
assert "11 seconds" in k.score(mk(10, 0), {"price_source": "market list quote"})["warning"]
# slow screen: 2 windows, 30 events, PF 1.3, both halves positive
sl = k.score(mk(40, .3, 40), {"slow": True}); assert len(sl["windows"]) == 2 and sl["label"] in ("on the paper list (unproven)", "off the list (failed the screen)")
assert k.score(mk(20, .3), {"slow": True})["label"] == "no evidence at n = 20"
# clustering: one cluster of identical trades has no z; clusters are not trades
z1 = k.cluster_z([dict(x, cluster="ONE") for x in mk(50, .1)]); assert z1["z"] is None and z1["clusters"] == 1
zc = k.cluster_z(mk(400, .1, 8)); assert zc["clusters"] == 8

# guard
with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "REG.md"); open(f, "w").write("x\nREAD-ONCE MARKER: not yet read; first read on or after 2026-12-22; after the read: READ ON <date>, commit <hash>\n")   # template text must NOT count as read
    g = k.Cutoff(5000, f, not_before=2000)
    tr = [{"event": "a", "ts": 1000}]
    for args, why in (((tr, 1999), "before the registered read date"),):
        try: g.check(*args); raise SystemExit("guard failed: " + why)
        except RuntimeError as e: assert "before" in str(e)
    assert g.check(tr, 2000)
    try: g.check([{"event": "late", "ts": 5000}], 2000); raise SystemExit("late trade passed")
    except RuntimeError as e: assert "held-out" in str(e)
    assert k.Cutoff(5000, f, held_out=True).check([{"event": "h", "ts": 5001}], 1)
    try: k.Cutoff(5000, f, held_out=True).check(tr, 1); raise SystemExit("dev trade in held-out passed")
    except RuntimeError as e: assert "development trade" in str(e)
    line = g.mark_read("2026-12-22", "abc1234"); assert line.endswith("READ ON 2026-12-22, commit abc1234")
    open(f, "w").write(line + "\n")
    try: g.check(tr, 2000); raise SystemExit("second read passed")
    except RuntimeError as e: assert "already read" in str(e)
    open(f, "w").write("nothing\n")
    try: g.check(tr, 2000); raise SystemExit("missing marker passed")
    except RuntimeError as e: assert "no marker line" in str(e)

# ---- fixture-shaped tests, one per verified format (keys copied from landed files; values made up) ----
import csv
with tempfile.TemporaryDirectory() as d:
    # perp candle PULL answer (PERPBTC1M shape): {'candlesticks': [{'ask': {...}, 'bid': {...}, 'end_period_ts': int, 'price': {...None}, ...}], 'ticker': 'KXAAAPERP'}; absolute levels, never divided by 100
    pc = {"ticker": "KXAAPLPERP", "candlesticks": [{"ask": {"close": "6.8332", "high": "6.8354", "low": "6.8271", "open": "6.8271"}, "bid": {"close": "6.8295", "high": "6.8304", "low": "6.8234", "open": "6.8234"},
          "end_period_ts": 1794182400, "open_interest": "355838.00", "open_interest_notional_value_dollars": "1", "price": {"close": None, "high": None, "low": None, "mean": None, "open": None, "previous": None}, "volume": "750.00", "volume_notional_value_dollars": "5"}]}
    mkrun(d, [("KXAAPLPERP_2026-11-09", pc)]); r = k.candles(d)["KXAAPLPERP"][0]
    assert r["bid"] == 6.8295 and r["ask"] == 6.8332 and r["ts"] == 1794182400 and r["price"] is None and r["bid_low"] == 6.8234     # NOT 0.068
    # binary candle PULL answer (SPREADCELL1 / R6SLICE shape): yes_bid and yes_ask objects with *_dollars strings, volume_fp, open_interest_fp, int end_period_ts
    bc = {"markets": [{"candlesticks": [{"end_period_ts": 100, "open_interest_fp": "10.00", "price": {"close_dollars": "0.4000"}, "volume_fp": "5.00",
          "yes_ask": {"close_dollars": "0.4200", "high_dollars": "0.43", "low_dollars": "0.41", "open_dollars": "0.42"}, "yes_bid": {"close_dollars": "0.4000", "high_dollars": "0.41", "low_dollars": "0.39", "open_dollars": "0.40"}}], "market_ticker": "T-1"}]}
    mkrun(d, [("b000_0", bc)]); r = k.candles(d)["T-1"][0]; assert r["bid"] == .4 and r["ask"] == .42 and r["volume"] == 5.0 and r["oi"] == 10.0 and r["ask_low"] == .41
    # settled list PULL answer: market objects with these key names (BTC15M had floor_strike and no cap_strike: cap stays None, unverified for 'less' and 'between')
    ml = {"cursor": "", "markets": [{"ticker": "KXBTC15M-26OCT291815-15", "event_ticker": "KXBTC15M-26OCT291815", "open_time": "2026-10-29T18:00:00Z", "close_time": "2026-10-29T18:15:00Z", "result": "yes",
          "strike_type": "greater", "floor_strike": 100.5, "volume_fp": "12.00", "title": "t", "yes_ask_dollars": "0.40", "yes_bid_dollars": "0.38"}]}
    mkrun(d, [("live_KXBTC15M", ml)]); m = k.markets(d)["KXBTC15M-26OCT291815-15"]; assert m["floor"] == 100.5 and m["cap"] is None and m["type"] == "greater" and m["close"] - m["open"] == 900 and m["volume"] == 12.0
    # perp-data csv (kalshi1m/<date>.csv.gz): header copied from the landed file
    hdr = "ticker,end_period_ts,bid_open,bid_high,bid_low,bid_close,ask_open,ask_high,ask_low,ask_close,price_open,price_high,price_low,price_close,price_mean,price_previous,open_interest,volume"
    pcsv = os.path.join(d, "p.csv.gz"); gzip.open(pcsv, "wt").write(hdr + "\nKXAAPLPERP,1794182400,6.8234,6.8304,6.8234,6.8295,6.8271,6.8354,6.8271,6.8332,,,,,,,355838.00,750.00\n")
    r = k.perp_csv(pcsv)["KXAAPLPERP"][0]; assert r["bid"] == 6.8295 and r["ask"] == 6.8332 and r["price"] is None and r["volume"] == 750.0
    # R6 recorder book file: header copied from the landed file; empty level cells are skipped
    h6 = "t_send_ms,t_recv_ms,server_date_header,ticker,series,close_time," + ",".join("yes_bid_px_%d" % i for i in range(1, 6)) + "," + ",".join("yes_bid_sz_%d" % i for i in range(1, 6)) + "," + ",".join("no_bid_px_%d" % i for i in range(1, 6)) + "," + ",".join("no_bid_sz_%d" % i for i in range(1, 6))
    def row(t_ms, yes, no):
        pad = lambda lv, j: [str(x[j]) if i < len(lv) else "" for i, x in enumerate(lv + [(0, 0)] * (5 - len(lv)))]
        return ",".join([str(t_ms - 40), str(t_ms), '"Thu, 29 Oct 2026 22:04:00 GMT"', "KXBTC15M-X", "KXBTC15M", "2026-10-29T22:15:00Z"] + pad(yes, 0) + pad(yes, 1) + pad(no, 0) + pad(no, 1))
    r6 = os.path.join(d, "book.csv.gz")
    gzip.open(r6, "wt").write(h6 + "\n" + row(10000, [(.29, 3928.4), (.28, 3093.7)], [(.70, 0.5), (.69, 5000)]) + "\n" + row(11000, [(.30, 10)], [(.69, 4000)]) + "\n")
    B = k.r6_book(r6)["KXBTC15M-X"]; assert len(B) == 2 and B[0]["t"] == 10.0 and B[0]["yes_bids"] == [(.29, 3928.4), (.28, 3093.7)] and B[0]["no_bids"][0] == (.7, .5)
    # fill_ioc, the company convention: 1 contract, walk up to 5 levels at or below the limit, first poll within 4 s after t0 + delay, no poll = no trade, short size = no trade
        # YES buy meets NO bids: asks are 1 - .70 = .30 (size .5) and 1 - .69 = .31 (size 5000): 0.5 at .30 + 0.5 at .31 = .305
    assert abs(k.fill_ioc(B, "yes", 0.31, 9.0, 1.0) - 0.305) < 1e-9
    assert k.fill_ioc(B, "yes", 0.30, 9.0, 1.0) is None     # not enough size at or below .30 (only 0.5)
    assert k.fill_ioc(B, "yes", 0.50, 20.0, 1.0) is None                                # no poll within 4 s after t0 + delay
    assert k.fill_ioc(B, "yes", 0.50, 9.0, 1.0) is not None and k.fill_ioc(B, "no", 0.80, 9.0, 1.0) is not None
    assert k.fill_ioc(B, "yes", 0.50, 4.0, 1.0) is None                                 # first poll at or after 5.0 s is t=10.0: 5 s late, over the 4 s allowance
    # recorder-style batch order book (UNVERIFIED shape, from the recorder's parser)
    ob = {"orderbooks": [{"ticker": "T-1", "orderbook_fp": {"yes_dollars": [["0.40", "5"], ["0.45", "9"]], "no_dollars": [["0.50", "7"]]}}]}
    mkrun(d, [("o1", ob)]); bk = k.books(d)["T-1"][0]; assert bk["yes_bids"][0] == (0.45, 9.0) and bk["no_bids"] == [(0.5, 7.0)]
print("scorekit fixture-shaped tests passed")
with tempfile.TemporaryDirectory() as d2:
    mkrun(d2, [("l", {"markets": [{"ticker": "KXS-1", "event_ticker": "KXS", "close_time": "2026-11-05T12:00:00Z", "settlement_ts": "2026-11-05T12:04:10Z", "result": "yes"}, {"ticker": "KXS-2", "event_ticker": "KXS", "close_time": "2026-11-05T12:00:00Z", "settlement_ts": 1793880250, "result": "no"}]})])
    mm = k.markets(d2); assert mm["KXS-1"]["settlement_ts"] == 1793880250 and mm["KXS-2"]["settlement_ts"] == 1793880250 and mm["KXS-1"]["settlement_ts"] - mm["KXS-1"]["close"] == 250
with tempfile.TemporaryDirectory() as d3:
    hd = os.path.join(d3, "HELDOUT_X", "run1"); os.makedirs(hd); mkrun(hd, [("l", {"markets": []})])
    for fn in (lambda: list(k.iter_answers(hd)), lambda: k.manifest(hd), lambda: k.markets(hd), lambda: k.candles(hd)):
        try: fn(); raise AssertionError("a HELDOUT_ folder must be refused")
        except SystemExit as e: assert "HELDOUT_" in str(e)
    assert list(k.iter_answers(hd, allow_heldout=True)) is not None            # only with the explicit flag, on the Head's go
with tempfile.TemporaryDirectory() as d4:
    hd = os.path.join(d4, "HELDOUT_Y", "run"); os.makedirs(hd); mkrun(hd, [("l", {"markets": []})]); ln = os.path.join(d4, "innocent"); os.symlink(hd, ln)
    for fn in (lambda: list(k.iter_answers(ln)), lambda: k.manifest(ln), lambda: k.guard(ln)):
        try: fn(); raise AssertionError("a link to a HELDOUT_ folder must be refused")
        except SystemExit: pass
print("scorekit synthetic tests passed")
