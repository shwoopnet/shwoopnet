import hashlib, lzma, os, shutil, sqlite3, tempfile, unittest, calendar, time
import vspike_cuts_second_load as LD, vspike_cuts_second as V
def ts(s): return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); p = os.path.join(self.d, "x.sqlite"); db = sqlite3.connect(p)
        db.execute("create table market(ticker, close_ts, result, series, other)"); db.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
        C = ts("2026-09-01T12:00:00Z"); V3 = ts("2026-09-04T12:00:00Z")
        db.executemany("insert into market values (?,?,?,?,?)", [("A", C, "yes", "KXBNB15M", 0), ("B", C, None, "KXBNB15M", 0), ("C", V3, "yes", "KXBNB15M", 0), ("D", C, "yes", "KXFOO15M", 0), ("E", C + 0.5, "yes", "KXBNB15M", 0), ("F", 1791043200, "yes", "KXCOPPER15M", 0)])
        db.executemany("insert into candle values (?,?,?,?,?,?,?)", [("A", C - 60, 0.4, 0.5, 0.5, 10, 1), ("A", C + 60, 0.4, 0.5, 0.5, 10, 1), ("C", C - 60, 0.4, 0.5, 0.5, 10, 1), ("D", C - 60, 0.4, 0.5, 0.5, 10, 1)]); db.commit(); db.close()
        raw = lzma.compress(open(p, "rb").read()); open(os.path.join(self.d, LD.XZ), "wb").write(raw); self.sha = hashlib.sha256(raw).hexdigest()
        self.allow = os.path.join(self.d, "a.md"); open(self.allow, "w").write("x " + LD.ALLOW_MARK + " vspike_cuts_second_load.py " + LD.self_sha() + " " + self.sha + "\n"); self.C = C
    def tearDown(self): shutil.rmtree(self.d)
    def test_load(self):
        mk, cd, c = LD.load(self.d, self.allow, self.sha)
        self.assertEqual(mk, [("A", self.C, "KXBNB15M")]); self.assertEqual(list(cd["A"]), [self.C - 60])
        self.assertEqual(c["candle after the close (dropped)"], 1); self.assertEqual(c["market in the VALIDATE half (not read further)"], 1); self.assertEqual(c["market outside the series wall (not read further)"], 1)
        self.assertEqual(c["SEARCH market without a yes or no result (dropped)"], 1); self.assertEqual(c["candle row of a market not read (not parsed)"], 2)
        self.assertEqual(c["market with a non-integer close_ts or at or after the cut (dropped)"], 2)
    def test_refuse(self):
        open(self.allow, "w").write("x " + LD.ALLOW_MARK + " vspike_cuts_second_load.py 00 " + self.sha + "\n")
        with self.assertRaises(SystemExit): LD.load(self.d, self.allow, self.sha)
        open(self.allow, "w").write("x " + LD.ALLOW_MARK + " vspike_cuts_second_load.py " + LD.self_sha() + " 00\n")
        with self.assertRaises(SystemExit): LD.load(self.d, self.allow, self.sha)
