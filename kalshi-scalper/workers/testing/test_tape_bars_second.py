import csv, gzip, os, shutil, tempfile, unittest
import tape_bars_second as T

def row(t, p, c, side, blk, recv="100", tk="KXT", f="2026-11-17.csv.gz"): return {"file": f, "t_recv_ms": recv, "ticker": tk, "created_time": t, "price": p, "count": c, "taker_side": side, "is_block_trade": blk}
# file order is NEWEST FIRST within a page (reverse time), as the stored tape
ROWS = [row("2026-11-17T12:04:00Z", "10.40", "0", "sell", "false"), row("2026-11-17T12:03:05Z", "9.00", "7", "buy", "TRUE"), row("2026-11-17T12:01:45Z", "10.50", "2", "xxx", "false"), row("2026-11-17T12:01:30Z", "9.90", "4", "buy", "true"),
        row("2026-11-17T12:01:00Z", "10.30", "1", "sell", "false"), row("2026-11-17T12:01:00.000Z", "10.10", "5", "buy", "false"), row("2026-11-17T12:00:59.999999999Z", "10.20", "3", "sell", "false"), row("2026-11-17T12:00:10Z", "10.00", "2", "buy", "false"),
        row("2026-11-17T12:00:10Z", "10.00", "2", "buy", "false", recv="200"), row("2026-11-17T12:00:59.999999999Z", "10.20", "3", "sell", "false", recv="100")]       # last two: a page overlap (later recv: dropped) and a genuine repeat (same recv: kept)

class TT(unittest.TestCase):
    def test_hand_case(self):
        bars, summ, ticks = T.build(ROWS, {"KXT"}); E0 = 1794916800
        self.assertEqual(sorted(e for _t, e in bars), [E0 + 60, E0 + 120, E0 + 300])
        b = bars[("KXT", E0 + 60)]; self.assertEqual((float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"]), b["volume"], b["n_trades"], b["buy_volume"], b["sell_volume"], b["block_volume"], b["block_count"]), (10.0, 10.2, 10.0, 10.2, 8, 3, 2, 6, 0, 0))   # a2 repeated (same recv): two prints of 3
        b = bars[("KXT", E0 + 120)]      # ties at 12:01:00: file order 10.30 then 10.10, reverse file order: 10.10 (later in file) first, then 10.30, then 10.50 at 12:01:45
        self.assertEqual((float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"]), b["volume"], b["n_trades"], b["buy_volume"], b["sell_volume"], b["block_volume"], b["block_count"]), (10.1, 10.5, 10.1, 10.5, 8, 3, 5, 1, 4, 1))
        b = bars[("KXT", E0 + 300)]; self.assertEqual((float(b["open"]), b["volume"], b["n_trades"]), (10.4, 0, 1)); self.assertNotIn(("KXT", E0 + 240), bars)
        s = summ[("2026-11-17.csv.gz", "KXT")]; self.assertEqual((s["rows_read"], s["rows_kept"], s["merged_by_repeat"], s["kept_same_recv"], s["block_rows"], s["unknown_side_trades"], s["bars_written"], s["bars_only_block"], s["block_volume_in_those"]), (10, 9, 1, 1, 2, 1, 3, 1, 7))
        self.assertEqual(ticks[("2026-11-17.csv.gz", "KXT")], T.Decimal("0.10"))
    def test_tie_close_by_reverse_file_order(self):
        rs = [row("2026-11-17T12:00:20Z", "5.0", "1", "buy", "false"), row("2026-11-17T12:00:20Z", "6.0", "1", "buy", "false"), row("2026-11-17T12:00:20Z", "7.0", "1", "sell", "false")]   # file order 5, 6, 7: printed order 7, 6, 5
        b = T.build(rs, {"KXT"})[0][("KXT", 1794916860)]; self.assertEqual((float(b["open"]), float(b["close"])), (7.0, 5.0))
        rs = [row("2026-11-17T12:00:20.5Z", "5.0", "1", "buy", "false"), row("2026-11-17T12:00:20Z", "6.0", "1", "buy", "false")]                    # exact time wins over file order
        b = T.build(rs, {"KXT"})[0][("KXT", 1794916860)]; self.assertEqual((float(b["open"]), float(b["close"])), (6.0, 5.0))
    def test_overlap_keeps_earliest_recv(self):
        a = row("2026-11-17T12:00:20Z", "5.0", "1", "buy", "false", recv="300"); b = row("2026-11-17T12:00:20Z", "5.0", "1", "buy", "false", recv="100"); c = row("2026-11-17T12:00:20Z", "5.0", "1", "buy", "false", recv="100")
        bars, summ, _ = T.build([a, b, c], {"KXT"}); bb = bars[("KXT", 1794916860)]; s = summ[("2026-11-17.csv.gz", "KXT")]
        self.assertEqual((bb["n_trades"], bb["volume"], s["merged_by_repeat"], s["kept_same_recv"]), (2, 2, 1, 1))
        d = row("2026-11-17T12:00:20Z", "5.0", "1", "sell", "false", recv="500"); self.assertEqual(T.build([b, d], {"KXT"})[0][("KXT", 1794916860)]["n_trades"], 2)       # a different side is a different trade
    def test_time_parse(self):
        a = T.parse_ns("2026-11-17T12:01:00.000Z"); self.assertEqual(a, T.parse_ns("2026-11-17T12:01:00Z")); self.assertEqual(a, T.parse_ns("2026-11-17T12:01:00+00:00")); self.assertEqual(T.parse_ns("2026-11-17T12:01:00.000000001Z"), a + 1)
        for bad in ("2026-11-17T12:01:00+01:00", "2026-11-17 12:01:00Z", "2026-11-17T12:01:00.1234567891Z", "2026-11-17T12:01Z", ""):
            with self.assertRaises(ValueError): T.parse_ns(bad)
        self.assertEqual(T.end_ts_of(T.parse_ns("2026-11-17T12:00:59.999999999Z")), 1794916860); self.assertEqual(T.end_ts_of(a), 1794916920)
    def test_bad_rows_raise(self):
        for kw in ({"count": "-1"}, {"count": "1.5"}, {"price": "0"}, {"price": "abc"}, {"is_block_trade": "maybe"}, {"price": "-1"}):
            r = row("2026-11-17T12:00:10Z", "1.0", "1", "buy", "false"); r.update(kw)
            with self.assertRaises(ValueError): T.build([r], {"KXT"})
    def test_wall_not_parsed(self):
        bad = {"file": "2026-11-17.csv.gz", "ticker": "KXOTHER"}; bars, summ, ticks = T.build([bad] + ROWS, {"KXT"}); self.assertEqual(len(bars), 3); self.assertEqual(summ[("2026-11-17.csv.gz", "_outside_wall")]["rows"], 1)
    def test_two_tickers_one_file(self):
        rs = [row("2026-11-17T12:00:20Z", "5.0", "1", "buy", "false", tk="KXA"), row("2026-11-17T12:00:20Z", "9.0", "1", "buy", "false", tk="KXB")]
        bars, summ, _ = T.build(rs, {"KXA", "KXB"}); self.assertEqual((float(bars[("KXA", 1794916860)]["close"]), float(bars[("KXB", 1794916860)]["close"])), (5.0, 9.0)); self.assertEqual(len(T.summary_lines(summ, {})), 3)         # header and two lines
    def test_other_date_and_held_rows(self):
        rs = [row("2026-11-17T23:59:59Z", "5.0", "1", "buy", "false"), row("2026-11-18T00:00:00Z", "6.0", "1", "buy", "false"), row("2026-11-17T12:00:00Z", "7.0", "1", "sell", "false")]
        bars, summ, _ = T.build(rs, {"KXT"}); s = summ[("2026-11-17.csv.gz", "KXT")]; self.assertEqual((s["rows_read"], s["rows_other_date"], s["rows_kept"]), (3, 1, 2)); self.assertEqual(len(bars), 2)
        held = lambda tk, t: t >= 1794916860 + 1000       # everything from 12:17:20 on
        rs2 = [row("2026-11-17T12:00:00Z", "7.0", "1", "sell", "false"), row("2026-11-17T12:20:00Z", "8.0", "1", "sell", "false"), row("2026-11-17T12:17:19Z", "9.0", "1", "sell", "false")]
        bars, summ, _ = T.build(rs2, {"KXT"}, held); s = summ[("2026-11-17.csv.gz", "KXT")]; self.assertEqual((s["rows_held"], s["rows_kept"], len(bars)), (1, 2, 2))      # t < from is not held, the boundary is inclusive from 12:17:20
        self.assertEqual(T.summary_lines(summ, {})[1].split(",")[-2:], ["0", "1"])
    def test_holds_loader(self):
        import json as J
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "h.json"); J.dump({"forward_default_deny_from": 1794787200, "rows": [{"id": "H1", "tickers": ["KXGOLDPERP*"], "from": 1000, "to": 2000, "status": "OPEN"}, {"id": "H2", "tickers": ["*"], "from": 0, "to": None, "status": "FROZEN", "scope": "archive_binary"},
                {"id": "H3", "tickers": ["KXAAA"], "from": 5000, "to": None, "status": "APPROVED"}, {"id": "H4", "tickers": ["KXFRZ"], "from": 3000, "to": 4000, "status": "FROZEN"}, {"id": "H5", "tickers": ["KXSC"], "from": 0, "to": None, "status": "OPEN", "scope": "other_scope"}, {"id": "H6", "tickers": ["KXCL"], "from": 0, "to": None, "status": "OPEN", "kind": "clearance"}]}, open(p, "w"))
            sh = T.hashlib.sha256(open(p, "rb").read()).hexdigest(); h = T.load_holds(p, sh)
            self.assertTrue(h("KXGOLDPERP", 1000)); self.assertFalse(h("KXGOLDPERP", 2000)); self.assertFalse(h("KXGOLDPERP", 999)); self.assertFalse(h("KXOTHER", 1500)); self.assertFalse(h("KXAAA", 6000))      # APPROVED and archive_binary rows do not hold
            self.assertFalse(h("KXSC", 10)); self.assertFalse(h("KXCL", 10)); self.assertTrue(h("KXFRZ", 3500)); self.assertTrue(h("KXOTHER", 1794787200)); self.assertFalse(h("KXOTHER", 1794787199))
            with self.assertRaises(SystemExit): T.load_holds(p, "00")
        finally: shutil.rmtree(d)
    def test_range_rules(self):
        for a, b in (("2026-09-18", "2026-10-27"), ("2026-10-28", "2026-11-15"), ("2026-09-20", "2026-09-20")): T.check_range(a, b)
        for a, b in (("2026-10-27", "2026-10-28"), ("2026-11-15", "2026-11-16"), ("2026-11-16", "2026-11-16"), ("2026-09-17", "2026-09-18"), ("2026-10-02", "2026-10-01"), ("x", "2026-10-01")):
            with self.assertRaises(SystemExit): T.check_range(a, b)
    def test_files_and_allow(self):
        d = tempfile.mkdtemp()
        try:
            H = ["t_recv_ms", "server_date_header", "ticker", "created_time", "price", "count", "taker_side", "is_block_trade"]; os.makedirs(os.path.join(d, "tape"))
            for day in ("2026-10-05", "2026-10-06", "2026-10-30"):
                with gzip.open(os.path.join(d, "tape", day + ".csv.gz"), "wt", newline="") as f:
                    w = csv.writer(f); w.writerow(H); w.writerow(["100", "hdr", "KXT", day + "T12:00:10Z", "5.0", "1", "buy", "false"]); w.writerow(["100", "hdr", "KXT", day + "T12:00:20Z", "5.5", "1", "sell", "false"]); w.writerow(["1", "h", "KXOTHER", "bad", "bad", "bad", "bad", "bad"])
            open(os.path.join(d, "tape", "all-history.csv.gz"), "wb").write(b"junk")
            allow = os.path.join(d, "a.md"); open(allow, "w").write("x readable ONLY by the Testing Desk's tape bar builder tape_bars_second.py " + T.sha(open(T.__file__).read()) + "\n")
            bars, summ, ticks, man = T.build_from_files(d, ["KXT"], allow, "2026-10-05", "2026-10-06"); self.assertEqual(len(man), 2); self.assertEqual(len(bars), 2)            # the 10-30 file is neither listed nor opened
            with self.assertRaises(SystemExit): T.build_from_files(d, ["KXT"], allow, "2026-10-05", "2026-10-30")
            open(allow, "w").write("x readable ONLY by the Testing Desk's tape bar builder tape_bars_second.py 00\n")
            with self.assertRaises(SystemExit): T.build_from_files(d, ["KXT"], allow, "2026-10-05", "2026-10-06")
        finally: shutil.rmtree(d)
