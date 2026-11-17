import os, sqlite3, lzma, hashlib, tempfile, unittest, datetime
import oicore_all_second_load as L
def mk(d):
    db = os.path.join(d, "a.sqlite"); c = sqlite3.connect(db)
    c.execute("create table market(ticker, close_ts, result, series)"); c.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    for r in (("KXBTC15M-A", 1000, "yes", "KXBTC15M"), ("KXBTC15M-B", L.CUT_TS, "yes", "KXBTC15M"), ("KXBTC15M-C", 1000, "", "KXBTC15M"), ("KXFOO15M-D", 1000, "yes", "KXFOO15M")): c.execute("insert into market values (?,?,?,?)", r)
    for r in (("KXBTC15M-A", 820, .3, .4, 0, 0, 5), ("KXBTC15M-A", 1100, .3, .4, 0, 0, 5)): c.execute("insert into candle values (?,?,?,?,?,?,?)", r)
    c.commit(); c.close(); raw = lzma.compress(open(db, "rb").read()); xz = os.path.join(d, "a.xz"); open(xz, "wb").write(raw); return xz, hashlib.sha256(raw).hexdigest()
class T(unittest.TestCase):
    def test_wall_and_cuts(self):
        d = tempfile.mkdtemp(); xz, h = mk(d); allow = os.path.join(d, "al.md")
        me, scr = L.sha_of(L.__file__), L.sha_of(os.path.join(L.HERE, "oicore_all_second.py"))
        open(allow, "w").write("%s oicore_all_second_load.py %s %s %s\n" % (L.ALLOW_MARK, me, scr, h))
        m, c, sp, cnt = L.load(xz, allow, h)
        self.assertEqual(m, [("KXBTC15M-A", 1000, "yes", "BTC")]); self.assertEqual(dict(cnt), {"cut_close": 1, "no_result": 1, "outside_wall": 1, "candle_after_close": 1}); self.assertEqual(list(c), [("KXBTC15M-A", 820)])
        for bad in ("", "%s oicore_all_second_load.py %s %s %s\n" % (L.ALLOW_MARK, "00", scr, h), "%s oicore_all_second_load.py %s %s %s\n" % (L.ALLOW_MARK, me, "00", h), "%s oicore_all_second_load.py %s %s %s\n" % (L.ALLOW_MARK, me, scr, "00")):
            open(allow, "w").write(bad)
            with self.assertRaises(SystemExit): L.load(xz, allow, h)
    def test_wrong_archive(self):
        d = tempfile.mkdtemp(); xz, h = mk(d); allow = os.path.join(d, "al.md"); me, scr = L.sha_of(L.__file__), L.sha_of(os.path.join(L.HERE, "oicore_all_second.py"))
        open(allow, "w").write("%s oicore_all_second_load.py %s %s %s\n" % (L.ALLOW_MARK, me, scr, "ab" * 32))
        with self.assertRaises(SystemExit): L.load(xz, allow, "ab" * 32)
if __name__ == "__main__": unittest.main()
