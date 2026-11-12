"""Tests on a synthetic answer set (no real pulled data). Run: python3 -I test_spread_cell1_convert.py"""
import gzip, hashlib, json, os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spread_cell1_convert as C

# format reference only: one real line of the scorer's candles file, if present on this machine
REAL = "/tmp/claude-0/-home-user-shwoopnet/76de750d-5e48-584f-a0fa-77e7d05b9163/scratchpad/w_cat_sports/candles_sp.jsonl"

EVENTS = [["KXMLBSPREAD", "KXMLBSPREAD-26SEP111840AAABBB", 1000],
          ["KXNBASPREAD", "KXNBASPREAD-26NOV11CCCDDD", 2000],
          ["KXNBASPREAD", "KXNBASPREAD-26NOV11EEEFFF", 3000]]
TICK = {0: ["KXMLBSPREAD-26SEP111840AAABBB-AAA2", "KXMLBSPREAD-26SEP111840AAABBB-BBB3"],
        1: ["KXNBASPREAD-26NOV11CCCDDD-CCC5"],
        2: ["KXNBASPREAD-26NOV11EEEFFF-EEE7"]}


def job():
    return {"job_id": "SPREADCELL1", "requests": [
        {"id": "b00%d" % i, "path": "/markets/candlesticks",
         "params": {"market_tickers": ",".join(t), "start_ts": 1, "end_ts": 2, "period_interval": 60}}
        for i, t in TICK.items()]}


def answer(tickers):
    return {"markets": [{"market_ticker": t, "candlesticks": [
        {"end_period_ts": 100, "yes_ask": {"close_dollars": "0.2500"}, "yes_bid": {"close_dollars": "0.2400"},
         "price": {"close_dollars": None}, "volume_fp": "0.00"}]} for t in tickers]}


def mkrun(root, name, rows, status="complete"):
    d = os.path.join(root, name); os.makedirs(d)
    out = []
    for i, (rid, st, tickers, badsha) in enumerate(rows, 1):
        fn = "%04d.json.gz" % i
        body = json.dumps(answer(tickers) if st == 200 else {"error": "none"}).encode()
        with open(os.path.join(d, fn), "wb") as f:
            f.write(gzip.compress(body))
        sha = hashlib.sha256(body).hexdigest()
        out.append({"index": i, "id": rid, "status": st, "bytes": len(body), "file": fn,
                    "sha256": "0" * 64 if badsha else sha})
    json.dump({"job": {"job_id": "SPREADCELL1"}, "status": status, "rows": out}, open(os.path.join(d, "manifest.json"), "w"))
    open(os.path.join(d, "STATUS"), "w").write(status)


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.runs = os.path.join(self.tmp, "runs"); os.makedirs(self.runs)
        self.out = os.path.join(self.tmp, "out")
        self.jp = os.path.join(self.tmp, "job.json"); json.dump(job(), open(self.jp, "w"))
        self.ep = os.path.join(self.tmp, "ev.json"); json.dump({"events": EVENTS}, open(self.ep, "w"))

    def run_c(self):
        return C.convert(self.runs, self.out, self.jp, self.ep)

    def test_a_incomplete_no_marker(self):
        mkrun(self.runs, "r1", [("b000", 200, TICK[0], 0), ("b001", 200, TICK[1], 0)], "incomplete")
        self.assertFalse(self.run_c())
        self.assertFalse(os.path.exists(os.path.join(self.out, C.MARKER)))

    def test_a2_all_answered_but_status_incomplete(self):
        mkrun(self.runs, "r1", [("b000", 200, TICK[0], 0), ("b001", 404, [], 0), ("b002", 200, TICK[2], 0)], "incomplete")
        self.assertFalse(self.run_c())
        self.assertFalse(os.path.exists(os.path.join(self.out, C.MARKER)))

    def test_b_two_runs_merge_and_marker(self):
        mkrun(self.runs, "2026-11-13T0100Z_1", [("b000", 200, TICK[0], 0), ("b001", 404, [], 0)], "incomplete")
        mkrun(self.runs, "2026-11-13T0200Z_2", [("b002", 200, TICK[2], 0)], "complete")
        self.assertTrue(self.run_c())
        self.assertEqual(open(os.path.join(self.out, C.MARKER)).read(), "3")
        recs = [json.loads(l) for l in open(os.path.join(self.out, "candles_sp.jsonl"))]
        self.assertEqual([r["_e"] for r in recs], [e[1] for e in EVENTS])
        self.assertEqual(recs[1]["h"]["KXNBASPREAD-26NOV11CCCDDD-CCC5"], [])  # 404 = no candles
        self.assertEqual(recs[0]["h"][TICK[0][0]], [[100, "0.2500", "0.2400", None, "0.00"]])

    def test_c_bad_sha_refuses(self):
        mkrun(self.runs, "r1", [("b000", 200, TICK[0], 1), ("b001", 200, TICK[1], 0), ("b002", 200, TICK[2], 0)])
        with self.assertRaises(C.Refuse):
            self.run_c()
        self.assertFalse(os.path.exists(os.path.join(self.out, C.MARKER)))

    def test_read_done_refuses(self):
        os.makedirs(self.out); open(os.path.join(self.out, C.READ_DONE), "w").write("x")
        mkrun(self.runs, "r1", [("b000", 200, TICK[0], 0), ("b001", 200, TICK[1], 0), ("b002", 200, TICK[2], 0)])
        with self.assertRaises(C.Refuse):
            self.run_c()
        self.assertFalse(os.path.exists(os.path.join(self.out, C.MARKER)))

    def test_d_format_matches_real_line(self):
        mkrun(self.runs, "r1", [("b000", 200, TICK[0], 0), ("b001", 200, TICK[1], 0), ("b002", 200, TICK[2], 0)])
        self.assertTrue(self.run_c())
        mine = json.loads(open(os.path.join(self.out, "candles_sp.jsonl")).readline())
        self.assertEqual(list(mine), ["_e", "s", "c", "h"])
        self.assertIsInstance(mine["c"], int)
        if os.path.exists(REAL):
            real = json.loads(open(REAL).readline())
            self.assertEqual(list(mine), list(real))
            for k in real:
                self.assertIs(type(mine[k]), type(real[k]))
            rc = next(v for v in real["h"].values() if v)[0]
            mc = mine["h"][TICK[0][0]][0]
            self.assertEqual(len(mc), len(rc))
            self.assertEqual([type(x) for x in (mc[0], mc[1], mc[2], mc[4])],
                             [type(x) for x in (rc[0], rc[1], rc[2], rc[4])])


if __name__ == "__main__":
    unittest.main(verbosity=2)
