"""Synthetic test for spread_cell1_times_convert.py. Run: python3 -I test_spread_cell1_times_convert.py"""
import gzip, hashlib, json, os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spread_cell1_times_convert as C

EVENTS = [["KXMLBSPREAD", "KXMLBSPREAD-26SEP111840AAABBB", 1000],
          ["KXNBASPREAD", "KXNBASPREAD-26NOV11CCCDDD", 2000],
          ["KXNBASPREAD", "KXNBASPREAD-26NOV11EEEFFF", 3000]]
T = ["KXMLBSPREAD-26SEP111840AAABBB-AAA2", "KXNBASPREAD-26NOV11CCCDDD-CCC5", "KXNBASPREAD-26NOV11EEEFFF-EEE7"]
JOB = {"job_id": "SPREADLISTS", "requests": [
    {"id": "t00", "path": "/markets", "params": {"tickers": ",".join(T[:2]), "limit": 100}},
    {"id": "t01", "path": "/markets", "params": {"tickers": T[2], "limit": 100}}]}
ANS = {"t00": {"markets": [
    {"ticker": T[0], "close_time": "c0", "expected_expiration_time": "x0", "occurrence_datetime": "o0", "yes_ask": 1},
    {"ticker": T[1], "close_time": "c1", "expected_expiration_time": None, "occurrence_datetime": "o1"}]},
    "t01": {"markets": [{"ticker": T[2], "close_time": "c2"}]}}


def mkrun(root, name, ids, status="complete", bad=False):
    d = os.path.join(root, name); os.makedirs(d)
    rows = []
    for i, rid in enumerate(ids, 1):
        body = json.dumps(ANS[rid]).encode()
        fn = "%04d.json.gz" % i
        open(os.path.join(d, fn), "wb").write(gzip.compress(body))
        rows.append({"index": i, "id": rid, "status": 200, "file": fn,
                     "sha256": "0" * 64 if bad else hashlib.sha256(body).hexdigest()})
    json.dump({"job": {"job_id": "SPREADLISTS"}, "status": status, "rows": rows}, open(os.path.join(d, "manifest.json"), "w"))
    open(os.path.join(d, "STATUS"), "w").write(status)


class Tst(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.runs = os.path.join(self.tmp, "runs"); os.makedirs(self.runs)
        self.out = os.path.join(self.tmp, "out")
        self.jp = os.path.join(self.tmp, "job.json"); json.dump(JOB, open(self.jp, "w"))
        self.ep = os.path.join(self.tmp, "ev.json"); json.dump({"events": EVENTS}, open(self.ep, "w"))

    def go(self):
        return C.convert(self.runs, self.out, self.jp, self.ep)

    def test_incomplete(self):
        mkrun(self.runs, "r1", ["t00"], "incomplete")
        self.assertFalse(self.go())
        self.assertFalse(os.path.exists(os.path.join(self.out, "SPREADLISTS_COMPLETE")))

    def test_complete_across_runs(self):
        mkrun(self.runs, "r1", ["t00"], "incomplete")
        mkrun(self.runs, "r2", ["t01"], "complete")
        self.assertTrue(self.go())
        m = json.load(open(os.path.join(self.out, "SPREAD_CELL1_EXPECTED.json")))
        self.assertEqual(m[EVENTS[0][1]], {"close_time": "c0", "expected_expiration_time": "x0", "occurrence_datetime": "o0"})
        self.assertEqual(m[EVENTS[1][1]]["expected_expiration_time"], None)
        self.assertEqual(m[EVENTS[1][1]]["occurrence_datetime"], "o1")
        self.assertEqual(m[EVENTS[2][1]], {"close_time": "c2", "expected_expiration_time": None, "occurrence_datetime": None})
        self.assertNotIn("yes_ask", json.dumps(m))
        self.assertEqual(open(os.path.join(self.out, "SPREADLISTS_COMPLETE")).read(), "2")

    def test_sha_mismatch_refuses(self):
        mkrun(self.runs, "r1", ["t00", "t01"], "complete", bad=True)
        with self.assertRaises(C.Refuse):
            self.go()

    def test_read_done_refuses(self):
        mkrun(self.runs, "r1", ["t00", "t01"])
        os.makedirs(self.out); open(os.path.join(self.out, "SPREADCELL1_READ_DONE"), "w").write("x")
        with self.assertRaises(C.Refuse):
            self.go()


if __name__ == "__main__":
    unittest.main()
