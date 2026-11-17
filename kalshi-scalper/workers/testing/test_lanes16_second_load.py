import hashlib, lzma, os, shutil, sqlite3, tempfile, unittest
import lanes16_second_load as LD

class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); c = os.path.join(self.d, "c.sqlite"); f = os.path.join(self.d, "f.sqlite")
        db = sqlite3.connect(c); db.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
        rows = [("KXNVDAPERP", LD.FIRST_TS, 100.0, 100.1, 9, 9, 9), ("KXNVDAPERP", LD.FIRST_TS - 60, 1, 2, 0, 0, 0), ("KXNVDAPERP", LD.CUTOFF, 1, 2, 0, 0, 0), ("KXTSLAPERP", LD.FIRST_TS, 5, 6, 0, 0, 0)]
        db.executemany("insert into candle values (?,?,?,?,?,?,?)", rows); db.commit(); db.close()
        db = sqlite3.connect(f); db.execute("create table funding(ticker, ts, rate)"); db.executemany("insert into funding values (?,?,?)", [("KXNVDAPERP", LD.FIRST_TS + 100, 0.0001), ("KXTSLAPERP", LD.FIRST_TS + 100, 0.5)]); db.commit(); db.close()
        for src, name in ((c, LD.CANDLE_XZ), (f, LD.FUNDING_XZ)): open(os.path.join(self.d, name), "wb").write(lzma.compress(open(src, "rb").read()))
        self.sha = {n: hashlib.sha256(open(os.path.join(self.d, n), "rb").read()).hexdigest() for n in (LD.CANDLE_XZ, LD.FUNDING_XZ)}
        self.allow = os.path.join(self.d, "allow.md")
        open(self.allow, "w").write("x " + LD.ALLOW_MARK + " lanes16_second_load.py " + LD.self_sha() + " " + " ".join(self.sha.values()) + "\n")
    def tearDown(self): shutil.rmtree(self.d)
    def test_load(self):
        data, fund, c = LD.load(self.d, self.allow, self.sha)
        self.assertEqual(data["KXNVDAPERP"], {LD.FIRST_TS: (100.0, 100.1)}); self.assertNotIn("KXTSLAPERP", data); self.assertEqual(c["candle row outside the wall (not parsed)"], 1)
        self.assertEqual(c["candle before 2026-11-05T18:39Z (dropped)"], 1); self.assertEqual(c["candle at or after 2026-11-17 (dropped)"], 1); self.assertEqual(fund["KXNVDAPERP"], {LD.FIRST_TS + 100: 0.0001})
    def test_refuse(self):
        open(self.allow, "w").write("x " + LD.ALLOW_MARK + " lanes16_second_load.py 00\n")
        with self.assertRaises(SystemExit): LD.load(self.d, self.allow, self.sha)
        with self.assertRaises(SystemExit): LD.load(self.d, os.path.join(self.d, "none.md"), self.sha)
    def test_page_max_pin(self):
        p = os.path.join(self.d, "pm.tsv"); open(p, "w").write("ticker\tclass\tpage_max\nKXNVDAPERP\tE\t4.5\n")
        with self.assertRaises(SystemExit): LD.page_max(p)
        LD.PAGE_MAX_SHA = hashlib.sha256(open(p, "rb").read()).hexdigest()
        try: self.assertEqual(LD.page_max(p), {"KXNVDAPERP": 4.5})
        finally: LD.PAGE_MAX_SHA = "5be707ecce0cab05f7c5e1103af1ec2915d2b340b27f969853fb22d85888de36"
