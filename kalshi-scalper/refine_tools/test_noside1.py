"""Tests on SYNTHETIC answers and a synthetic candle file (no real pulled data, no network).
Run: python3 -I test_noside1.py"""
import contextlib, gzip, hashlib, io, json, os, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import noside1_convert as C
import noside1_score as S

CLOSE = 1_700_000_000


def out_of(fn, *a):
    b = io.StringIO()
    with contextlib.redirect_stdout(b):
        fn(*a)
    return b.getvalue()


def candle(ts, bid, ask):
    d = lambda v: {"close_dollars": "%.4f" % v}
    return {"end_period_ts": ts, "yes_ask": d(ask), "yes_bid": d(bid), "price": d(bid), "volume_fp": "5.00"}


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.runs = os.path.join(self.d, "runs")
        self.out = os.path.join(self.d, "out")
        os.makedirs(self.runs)
        # master job: 2 historical requests and 1 live batch of 2 markets
        self.reqs = [
            {"id": "hist_E1-A", "path": "/historical/markets/E1-A/candlesticks", "params": {}},
            {"id": "hist_E2-A", "path": "/historical/markets/E2-A/candlesticks", "params": {}},
            {"id": "live_E3_0", "path": "/markets/candlesticks", "params": {"market_tickers": "E3-A,E3-B"}},
        ]
        self.job = os.path.join(self.d, "job.json")
        json.dump({"job_id": "NOSIDE1_CANDLES", "requests": self.reqs}, open(self.job, "w"))
        self.mk = os.path.join(self.d, "mk.jsonl")
        with open(self.mk, "w") as f:
            for t, e in [("E1-A", "E1"), ("E2-A", "E2"), ("E3-A", "E3"), ("E3-B", "E3")]:
                f.write(json.dumps({"ticker": t, "event_ticker": e, "series": "KXAPRPOTUS",
                                    "close_time": "2023-11-14T22:13:20Z", "result": "no"}) + "\n")
        self.ex = os.path.join(self.d, "held.jsonl")
        open(self.ex, "w").write(json.dumps({"t": "H-A", "e": "H", "s": "KXAPRPOTUS", "ct": 5, "res": "yes", "c": []}) + "\n")

    def tearDown(self):
        shutil.rmtree(self.d)

    def run_folder(self, name, job_id, items, status, bad_sha=False):
        """items: list of (request id, http status, body)"""
        p = os.path.join(self.runs, name)
        os.makedirs(p)
        rows = []
        for i, (rid, st, body) in enumerate(items, 1):
            fn = "%04d.json.gz" % i
            raw = json.dumps(body).encode()
            open(os.path.join(p, fn), "wb").write(gzip.compress(raw))
            sha = hashlib.sha256(raw).hexdigest()
            rows.append({"id": rid, "status": st, "file": fn, "sha256": ("0" * 64 if bad_sha else sha)})
        json.dump({"job": {"job_id": job_id}, "rows": rows}, open(os.path.join(p, "manifest.json"), "w"))
        open(os.path.join(p, "STATUS"), "w").write(status)

    def conv(self):
        return out_of(C.convert, self.runs, self.out, self.job, [self.mk], self.ex)

    def hist(self, tk):
        return {"candlesticks": [candle(CLOSE - 90000, 0.2, 0.22)]}

    def live(self):
        return {"markets": [{"market_ticker": "E3-A", "candlesticks": [candle(CLOSE - 90000, 0.2, 0.22)]},
                            {"market_ticker": "E3-B", "candlesticks": []}]}

    def test_incomplete_no_marker(self):
        self.run_folder("r1", "NOSIDE1_CANDLES", [("hist_E1-A", 200, self.hist("E1-A"))], "complete")
        out = self.conv()
        self.assertEqual(out.strip(), "pull incomplete: 1 of 3 answered")
        self.assertEqual(os.listdir(self.out) if os.path.isdir(self.out) else [], [])

    def test_not_complete_status_no_marker(self):
        self.run_folder("r1", "NOSIDE1_CANDLES", [("hist_E1-A", 200, self.hist(0)), ("hist_E2-A", 404, {}),
                                                  ("live_E3_0", 200, self.live())], "running")
        self.assertTrue(self.conv().startswith("pull incomplete: 3 of 3"))
        self.assertFalse(os.path.exists(os.path.join(self.out, C.MARKER)))

    def test_three_parts_merge_writes_marker(self):
        self.run_folder("r1", "NOSIDE1_CANDLES", [("hist_E1-A", 200, self.hist(0))], "complete")
        self.run_folder("r2", "NOSIDE1_CANDLES_P2", [("hist_E2-A", 404, {})], "complete")
        self.run_folder("r3", "NOSIDE1_CANDLES_P3", [("live_E3_0", 200, self.live())], "complete")
        self.run_folder("other", "SOMETHING_ELSE", [("hist_E1-A", 200, {"bogus": 1})], "complete")
        self.assertIn("marker", self.conv())
        self.assertEqual(open(os.path.join(self.out, C.MARKER)).read(), "3")
        rows = {j["t"]: j for j in map(json.loads, open(os.path.join(self.out, "cand_no.jsonl")))}
        self.assertEqual(sorted(rows), ["E1-A", "E2-A", "E3-A", "E3-B", "H-A"])  # held 302 part merged in
        self.assertEqual(rows["E1-A"]["c"][0], [CLOSE - 90000, "0.2200", "0.2000", "0.2000", "5.00"])
        self.assertEqual(rows["E2-A"]["c"], [])  # 404 = no candles
        self.assertEqual(rows["E3-A"]["ct"], 1700000000)
        self.assertEqual(rows["E1-A"]["res"], "no")

    def test_bad_sha_refuses(self):
        self.run_folder("r1", "NOSIDE1_CANDLES", [("hist_E1-A", 200, self.hist(0)), ("hist_E2-A", 404, {}),
                                                  ("live_E3_0", 200, self.live())], "complete", bad_sha=True)
        with self.assertRaises(C.Refuse):
            self.conv()
        self.assertFalse(os.path.exists(os.path.join(self.out, C.MARKER)))

    def test_read_done_refuses(self):
        os.makedirs(self.out)
        open(os.path.join(self.out, C.READ_DONE), "w").write("x")
        with self.assertRaises(C.Refuse):
            self.conv()


def synth_cand(path, with_heldout):
    """Events: KXAPRPOTUS arm A pass-like (40 per third), KXVHGCB arm A thin (10 in total),
    KXTRUMPAPPROVE arm B fail-like (35 per third). Third 2 events optionally added."""
    cuts = {"series": {"KXAPRPOTUS": {"events": []}, "KXVHGCB": {"events": []}, "KXTRUMPAPPROVE": {"events": []}}}
    lines = []

    def add(series, third, i, bid, win_no):
        e = "%s-%d-%d" % (series, third, i)
        cuts["series"][series]["events"].append([e, third])
        ct = CLOSE + 100000 * (third * 100 + i)
        lines.append({"t": e + "-T1", "e": e, "s": series, "ct": ct, "res": "no" if win_no else "yes",
                      "c": [[ct - 86400 - 600, "%.4f" % (bid + 0.02), "%.4f" % bid, None, "1"]]})

    for th in (0, 1):
        for i in range(40):
            add("KXAPRPOTUS", th, i, 0.20, i != 7)       # NO price 0.80, one loss in 40
        for i in range(5):
            add("KXVHGCB", th, i, 0.20, True)             # n 5 per third
        for i in range(35):
            add("KXTRUMPAPPROVE", th, i, 0.80, i < 3)     # arm B: NO price 0.20, wins 3 of 35
    if with_heldout:
        for i in range(60):
            add("KXAPRPOTUS", 2, i, 0.20, False)          # would wreck arm A if it were read
            add("KXTRUMPAPPROVE", 2, i, 0.80, True)       # would rescue arm B if it were read
        lines.append({"t": "UNLISTED-T1", "e": "UNLISTED", "s": "KXAPRPOTUS", "ct": CLOSE, "res": "yes",
                      "c": [[CLOSE - 86400 - 600, "0.22", "0.20", None, "1"]]})
    d = os.path.dirname(path)
    open(path, "w").write("\n".join(json.dumps(x) for x in lines) + "\n")
    cp = os.path.join(d, "cuts.json")
    json.dump(cuts, open(cp, "w"))
    return cp


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self._req = S.REQUESTS
        S.REQUESTS = 7  # synthetic marker content

    def tearDown(self):
        S.REQUESTS = self._req
        shutil.rmtree(self.d)

    def mk(self, name, held):
        p = os.path.join(self.d, name)
        os.makedirs(p)
        cuts = synth_cand(os.path.join(p, "cand_no.jsonl"), held)
        return p, cuts

    def test_before_marker_only_incomplete(self):
        p, cuts = self.mk("a", False)
        self.assertEqual(out_of(S.main, [p, "--cuts", cuts]).strip(), "pull incomplete")
        self.assertFalse(os.path.exists(os.path.join(p, S.READ_DONE)))
        open(os.path.join(p, S.MARKER), "w").write("6")  # wrong count still incomplete
        self.assertEqual(out_of(S.main, [p, "--cuts", cuts]).strip(), "pull incomplete")

    def test_once_then_already_read_and_labels(self):
        p, cuts = self.mk("a", False)
        open(os.path.join(p, S.MARKER), "w").write("7")
        out = out_of(S.main, [p, "--cuts", cuts])
        self.assertTrue(os.path.exists(os.path.join(p, S.READ_DONE)))
        self.assertEqual(out_of(S.main, [p, "--cuts", cuts]).strip(), "already read")
        def block(prefix):
            ls = out.splitlines()
            i = next(i for i, l in enumerate(ls) if l.startswith(prefix))
            j = next(k for k in range(i, len(ls)) if ls[k].startswith("  VERDICT"))
            return "\n".join(ls[i:j + 1])
        a_appr = block("ARM A price paid [0.75,0.90) family APPR")
        self.assertIn("VERDICT: PASS", a_appr)
        a_gcb = block("ARM A price paid [0.75,0.90) family GCB")
        self.assertIn("no evidence at n = 5 (TRAIN) / 5 (VALID)", a_gcb)
        self.assertNotIn("PF", a_gcb)
        self.assertNotIn("mean", a_gcb)
        self.assertIn("VERDICT: NO EVIDENCE", a_gcb)
        b_appr = block("ARM B price paid [0.10,0.25) family APPR")
        self.assertIn("VERDICT: FAIL", b_appr)

    def test_heldout_and_unlisted_ignored(self):
        p1, c1 = self.mk("clean", False)
        p2, c2 = self.mk("withheld", True)
        for p in (p1, p2):
            open(os.path.join(p, S.MARKER), "w").write("7")
        self.assertEqual(out_of(S.main, [p1, "--cuts", c1]), out_of(S.main, [p2, "--cuts", c2]))

    def test_load_drops_third_two(self):
        p, cuts = self.mk("h", True)
        TH = S.thirds(cuts)
        ob = S.load(os.path.join(p, "cand_no.jsonl"), TH)
        self.assertTrue(all(TH[o["e"]] < 2 for o in ob.values()))
        self.assertFalse(any(o["e"] == "UNLISTED" for o in ob.values()))


class EndToEnd(unittest.TestCase):
    def test_converter_output_is_read_by_scorer(self):
        t = ConvertTests("test_three_parts_merge_writes_marker")
        t.setUp()
        try:
            t.test_three_parts_merge_writes_marker()
            TH = {"E1": 0, "E2": 1, "E3": 0}
            ob = S.load(os.path.join(t.out, "cand_no.jsonl"), TH)
            self.assertTrue(isinstance(ob, dict))
        finally:
            t.tearDown()


if __name__ == "__main__":
    unittest.main(verbosity=2)
