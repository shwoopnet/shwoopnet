import csv, gzip, os, shutil, tempfile, unittest, hashlib
import perpscalp2_second_load as LD

def w(path, rows, head):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", newline="") as f:
        x = csv.writer(f); x.writerow(head); x.writerows(rows)

class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.allow = os.path.join(self.d, "allow.md")
        open(self.allow, "w").write("x " + LD.ALLOW_MARK + " perpscalp2_second_load.py " + LD.self_sha() + "\n")
        H = ["ticker", "end_period_ts", "bid_close", "ask_close", "volume"]; r = os.path.join(self.d, "root")
        w(r + "/kalshi1m/2026-11-10.csv.gz", [["KXNVDAPERP", 1000, 101, 100, 5], ["KXNVDAPERP", 2000, 100, 100, 5], ["KXOTHERPERP", 1, 1, 2, 3], ["KXNVDAPERP", 1794787200, 1, 2, 3]], H)
        w(r + "/kalshi1m/2026-11-11.csv.gz", [["KXNVDAPERP", 1000, 99, 100, 7]], H)   # the crossed first copy must not block this good one
        w(r + "/kalshi1m/all-history.csv.gz", [["KXNVDAPERP", 3000, 99, 100, 7]], H)
        F = ["ticker", "funding_time", "funding_rate"]
        w(r + "/funding/2026-11-10.csv.gz", [["KXNVDAPERP", "2026-11-10T16:00:00.123Z", 0.0001]], F); w(r + "/funding/all-history.csv.gz", [["KXNVDAPERP", "2026-11-09T16:00:00Z", 0.5]], F)
        self.r = r
    def tearDown(self): shutil.rmtree(self.d)
    def test_load(self):
        data, fund, c = LD.load(self.r, self.allow)
        self.assertEqual(data["KXNVDAPERP"], {1000: (99.0, 100.0, 7.0), 2000: (100.0, 100.0, 5.0)}); self.assertNotIn(3000, data["KXNVDAPERP"])
        self.assertEqual(len(fund["KXNVDAPERP"]), 1); self.assertEqual(c["skipped file name kalshi1m/all-history.csv.gz"], 1); self.assertEqual(c["skipped file name funding/all-history.csv.gz"], 1)
        self.assertEqual(c["files_read kalshi1m"], 2)
        man = sorted([(os.path.relpath(os.path.join(self.r, s, n), self.r), hashlib.sha256(open(os.path.join(self.r, s, n), "rb").read()).hexdigest()) for s, n in (("kalshi1m", "2026-11-10.csv.gz"), ("kalshi1m", "2026-11-11.csv.gz"), ("funding", "2026-11-10.csv.gz"))])
        self.assertIn("manifest_sha256 " + hashlib.sha256(repr(man).encode()).hexdigest(), c)
    def test_refuse(self):
        open(self.allow, "w").write("x " + LD.ALLOW_MARK + " perpscalp2_second_load.py 00\n")
        with self.assertRaises(SystemExit): LD.load(self.r, self.allow)
