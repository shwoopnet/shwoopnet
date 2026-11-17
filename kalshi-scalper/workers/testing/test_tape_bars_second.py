import csv, gzip, os, shutil, tempfile, unittest
import tape_bars_second as T

def row(tid, t, p, c, side, blk, tk="KXT"): return {"ticker": tk, "trade_id": tid, "created_time": t, "price": p, "count": c, "taker_side": side, "is_block_trade": blk}
ROWS = [row("a1", "2026-11-17T12:00:10Z", "10.00", "2", "buy", "false"), row("a2", "2026-11-17T12:00:59.999999999Z", "10.20", "3", "sell", "false"), row("a3", "2026-11-17T12:01:00.000Z", "10.10", "5", "buy", "false"),
        row("a4", "2026-11-17T12:01:00Z", "10.30", "1", "sell", "false"), row("a5", "2026-11-17T12:01:30Z", "9.90", "4", "buy", "true"), row("a6", "2026-11-17T12:01:45Z", "10.50", "2", "xxx", "false"),
        row("a7", "2026-11-17T12:03:05Z", "9.00", "7", "buy", "TRUE"), row("a8", "2026-11-17T12:04:00Z", "10.40", "0", "sell", "false"), row("a1", "2026-11-17T12:00:10Z", "10.00", "2", "buy", "false"), row("a2", "2026-11-17T12:00:59.999999999Z", "10.25", "3", "sell", "false")]

class TT(unittest.TestCase):
    def test_hand_case(self):
        bars, summ, ticks = T.build(ROWS, {"KXT"}); E0 = 1794916800
        self.assertEqual(sorted(e for _t, e in bars), [E0 + 60, E0 + 120, E0 + 300])
        b = bars[("KXT", E0 + 60)]; self.assertEqual((float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"]), b["volume"], b["n_trades"], b["buy_volume"], b["sell_volume"], b["block_volume"], b["block_count"]), (10.0, 10.2, 10.0, 10.2, 5, 2, 2, 3, 0, 0))
        b = bars[("KXT", E0 + 120)]; self.assertEqual((float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"]), b["volume"], b["n_trades"], b["buy_volume"], b["sell_volume"], b["block_volume"], b["block_count"]), (10.1, 10.5, 10.1, 10.5, 8, 3, 5, 1, 4, 1))
        b = bars[("KXT", E0 + 300)]; self.assertEqual((float(b["open"]), b["volume"], b["n_trades"], b["buy_volume"], b["sell_volume"]), (10.4, 0, 1, 0, 0)); self.assertNotIn(("KXT", E0 + 240), bars)
        s = summ["KXT"]; self.assertEqual((s["rows_read"], s["rows_kept"], s["duplicates_dropped"], s["duplicate_differs"], s["block_rows"], s["unknown_side_trades"], s["bars_written"], s["bars_only_block"], s["block_volume_in_those"]), (10, 8, 2, 1, 2, 1, 3, 1, 7))
        self.assertEqual(ticks["KXT"], T.Decimal("0.10"))
        self.assertEqual(T.bar_line(bars[("KXT", E0 + 60)]), "KXT,%d,10,10.199999999999999,10,10.199999999999999,5,2,2,3,0,0" % (E0 + 60))
    def test_time_parse(self):
        a = T.parse_ns("2026-11-17T12:01:00.000Z"); self.assertEqual(a, T.parse_ns("2026-11-17T12:01:00Z")); self.assertEqual(a, T.parse_ns("2026-11-17T12:01:00+00:00")); self.assertEqual(T.parse_ns("2026-11-17T12:01:00.000000001Z"), a + 1)
        for bad in ("2026-11-17T12:01:00+01:00", "2026-11-17 12:01:00Z", "2026-11-17T12:01:00.1234567891Z", "2026-11-17T12:01Z", ""):
            with self.assertRaises(ValueError): T.parse_ns(bad)
        self.assertEqual(T.end_ts_of(T.parse_ns("2026-11-17T12:00:59.999999999Z")), 1794916860); self.assertEqual(T.end_ts_of(a), 1794916920)
    def test_bad_rows_raise(self):
        for kw in ({"count": "-1"}, {"count": "1.5"}, {"price": "0"}, {"price": "abc"}, {"is_block_trade": "maybe"}, {"price": "-1"}):
            r = dict(row("z", "2026-11-17T12:00:10Z", "1.0", "1", "buy", "false")); r.update(kw)
            with self.assertRaises(ValueError): T.build([r], {"KXT"})
    def test_wall_not_parsed(self):
        bad = {"ticker": "KXOTHER", "trade_id": "x", "created_time": "garbage", "price": "garbage", "count": "garbage", "taker_side": "", "is_block_trade": "garbage"}
        bars, summ, ticks = T.build([bad] + ROWS, {"KXT"}); self.assertEqual(len(bars), 3); self.assertEqual(summ["_outside_wall"]["rows"], 1)
    def test_tie_and_order_by_exact_time(self):
        rs = [row("b", "2026-11-17T12:00:20.5Z", "5.0", "1", "buy", "false"), row("a", "2026-11-17T12:00:20Z", "6.0", "1", "buy", "false"), row("c", "2026-11-17T12:00:20.5Z", "7.0", "1", "buy", "false")]
        b = T.build(rs, {"KXT"})[0][("KXT", 1794916860)]          # exact time: a (20.0), then b and c tied at 20.5 by trade_id: b before c; as strings '20.5Z' < '20Z'
        self.assertEqual((float(b["open"]), float(b["close"])), (6.0, 7.0))
    def test_decimal_exact(self):
        b = T.build([row("p", "2026-11-17T12:00:20Z", "0.1", "1", "buy", "false"), row("q", "2026-11-17T12:00:21Z", "0.3", "1", "sell", "false")], {"KXT"})[0][("KXT", 1794916860)]
        self.assertEqual((b["low"], b["high"]), (T.Decimal("0.1"), T.Decimal("0.3")))
    def test_files_and_allow(self):
        d = tempfile.mkdtemp()
        try:
            H = list(T.COLS) + ["extra"]
            for day, rs in (("2026-11-17", ROWS[:5]), ("2026-11-18", ROWS[5:])):
                p = os.path.join(d, "tape", day); os.makedirs(p)
                with gzip.open(os.path.join(p, "KXT.csv.gz"), "wt", newline="") as f:
                    w = csv.writer(f); w.writerow(H); [w.writerow([r[c] for c in T.COLS] + ["x"]) for r in rs]
            allow = os.path.join(d, "a.md"); open(allow, "w").write("x readable ONLY by the Testing Desk's tape bar builder tape_bars_second.py " + T.sha(open(T.__file__).read()) + "\n")
            bars, summ, ticks, man = T.build_from_files(d, ["KXT"], allow); self.assertEqual(len(man), 2)
            open(allow, "w").write("x readable ONLY by the Testing Desk's tape bar builder tape_bars_second.py 00\n")
            with self.assertRaises(SystemExit): T.build_from_files(d, ["KXT"], allow)
        finally: shutil.rmtree(d)
