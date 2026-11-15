#!/usr/bin/env python3
"""Hand case for ol_score.py build 1 (synthetic, no network). Expected values worked by hand in HAND_CASE.md."""
import gzip, json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ol_score as S


def put(root, job, rows_bodies):
    d = os.path.join(root, "pull", job, "2026-11-20T0000Z_1")
    os.makedirs(d)
    rows = []
    for i, (row, body) in enumerate(rows_bodies, 1):
        row = dict(row, index=i)
        rows.append(row)
        with gzip.open(os.path.join(d, "%04d.json.gz" % i), "wt") as f:
            json.dump(body, f)
    with open(os.path.join(d, "manifest.json"), "w") as f:
        json.dump({"status": "complete", "rows": rows}, f)


def cnd(ts, yb, ya):
    return {"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % yb}, "yes_ask": {"close_dollars": "%.4f" % ya}}


def t(s):
    return S.iso(s)


class NBA(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        occ = "2026-10-25T03:00:00Z"
        A = {"ticker": "KXNBAPTS-26OCT24AAABBB-AAAP1-20", "event_ticker": "KXNBAPTS-26OCT24AAABBB", "occurrence_datetime": occ,
             "close_time": "2026-10-25T02:30:00Z", "result": "no"}
        OUT = {"ticker": "KXNBAPTS-26NOV07AAABBB-AAAP1-20", "event_ticker": "KXNBAPTS-26NOV07AAABBB", "occurrence_datetime": "2026-11-08T03:00:00Z",
               "close_time": "2026-11-08T02:30:00Z", "result": "TRAP"}
        put(self.root, "KXNBAPTS_LISTS_A", [({"path": "/markets"}, {"markets": [A, OUT], "cursor": ""})])
        G = t(occ) - 3 * 3600 - 1800
        D = G - 3600
        cs = [cnd(D - 180 * 60, .30, .32), cnd(D - 3600, .40, .42), cnd(D, .45, .47), cnd(G, .52, .54), cnd(G + 3600, .20, .22), cnd(G + 5400, .05, .08)]
        cs += [cnd(G + 7200, .03, .04)]
        put(self.root, "KXNBAPTS_CANDLES_B1", [({"path": "/markets/candlesticks"}, {"markets": [{"market_ticker": A["ticker"], "candlesticks": cs}]})])

    def test_fade(self):
        o = S.score("NBA_O", self.root, ("KXNBAPTS_CANDLES_B1",))
        self.assertEqual(o["counts"]["outside_window"], 1)
        self.assertEqual(o["proxy_check"]["closed_before_G"], 0)
        self.assertEqual(o["hold"]["n"], 1)
        self.assertAlmostEqual(o["hold"]["raw"]["mean_c"], 43.0)
        self.assertAlmostEqual(o["T"]["raw"]["mean_c"], 34.0)
        self.assertEqual(o["T"]["exits"], {"T": 1})
        self.assertAlmostEqual(o["M"]["raw"]["mean_c"], -13.0)
        self.assertAlmostEqual(o["S"]["raw"]["mean_c"], 43.0)
        self.assertAlmostEqual(o["hold"]["1c"]["mean_c"], 42.0)    # a .56, fee .02 -> 1 - .58

    def test_follow_no_move(self):
        o = S.score("NBA_L", self.root, ("KXNBAPTS_CANDLES_B1",))
        self.assertEqual(o["hold"]["n"], 0)                       # 1 h move .46 - .41 = .05 < .06
        self.assertEqual(o["drops"]["no_move"], 1)

    def test_result_not_read_outside_window(self):
        kept, c, _ = S.select("NBA_O", S.list_markets(self.root, S.CARDS["NBA_O"]))
        self.assertTrue(all(m["result"] != "TRAP" for m in kept.values()))

    def test_proxy_stop(self):
        r = tempfile.mkdtemp()
        B = {"ticker": "KXNBAPTS-26OCT24CCCDDD-X-10", "event_ticker": "KXNBAPTS-26OCT24CCCDDD", "occurrence_datetime": "2026-10-25T03:00:00Z",
             "close_time": "2026-10-24T22:00:00Z", "result": "yes"}
        put(r, "KXNBAPTS_LISTS_A", [({"path": "/markets"}, {"markets": [B]})])
        o = S.score("NBA_O", r, ())
        self.assertIn("stopped", o)
        self.assertNotIn("hold", o)


class MENT(unittest.TestCase):
    def test_cap_and_follow(self):
        root = tempfile.mkdtemp()
        occ = "2026-06-10T18:00:00Z"
        O = t(occ)
        D, anc = O - 3600, O - 3600 - 300 * 60
        ms, cands = [], {}
        moves = [(.20, .45), (.30, .45), (.36, .45), (.25, .45)]     # mids at anchor, at D: m = .25, .15, .09, .20
        for i, (a, b) in enumerate(moves):
            tk = "KXTRUMPMENTION-26JUN10-W%d" % i
            ms.append({"ticker": tk, "event_ticker": "KXTRUMPMENTION-26JUN10", "occurrence_datetime": occ, "close_time": "2026-06-10T19:00:00Z",
                       "yes_sub_title": "Word%d" % i, "result": "yes"})
            cands[tk] = [cnd(anc, a - .01, a + .01), cnd(D, b - .01, b + .01), cnd(O - 300, .60, .62)]
        ms.append({"ticker": "KXTRUMPMENTION-26JUN10-NQ", "event_ticker": "KXTRUMPMENTION-26JUN10", "occurrence_datetime": occ,
                   "close_time": "2026-06-10T19:00:00Z", "yes_sub_title": "Event does not qualify", "result": "no"})
        ms.append({"ticker": "KXTRUMPMENTION-26AUG10-W0", "event_ticker": "KXTRUMPMENTION-26AUG10", "occurrence_datetime": "2026-08-10T18:00:00Z",
                   "close_time": "2026-08-10T19:00:00Z", "yes_sub_title": "X", "result": "TRAP"})
        put(root, "MENTDRIFT_LISTS_A", [({"path": "/historical/markets"}, {"markets": ms})])
        put(root, "MENTDRIFT_CANDLES_P1", [({"path": "/historical/markets/%s/candlesticks" % k}, {"ticker": k, "candlesticks": v}) for k, v in sorted(cands.items())])
        o = S.score("MENT", root, ("MENTDRIFT_CANDLES_P1",))
        self.assertEqual(o["counts"]["outside_window"], 1)
        self.assertEqual(o["counts"]["not_qualify_word"], 1)
        self.assertEqual(o["hold"]["n"], 3)                       # W2 moved .09: signal; cap 3 keeps W0 (.25), W3 (.20), W1 (.15)
        self.assertEqual(o["drops"]["event_cap"], 1)
        # each buys YES at ask .46: fee ceil(.07*.46*.54*100)=2 -> .02; won: 1 - .48 = .52
        self.assertAlmostEqual(o["hold"]["raw"]["mean_c"], 52.0)
        # M sells at O-5min, yes bid .60: fee ceil(.07*.6*.4*100)=2 -> .02: .60 - .02 - .48 = .10
        self.assertAlmostEqual(o["M"]["raw"]["mean_c"], 10.0)


class Sample(unittest.TestCase):
    def test_md5_sample(self):
        mk = {("KXTRUMPMENTION-26JUN10-W%04d" % i): {"ticker": "KXTRUMPMENTION-26JUN10-W%04d" % i, "event_ticker": "KXTRUMPMENTION-26JUN10",
              "occurrence_datetime": "2026-06-10T18:00:00Z", "close_time": "2026-06-10T19:00:00Z", "yes_sub_title": "w"} for i in range(1500)}
        kept, c, _ = S.select("MENT", mk)
        self.assertEqual(len(kept), 1400)
        self.assertEqual(c["not_sampled"], 100)
        import hashlib
        want = sorted(mk, key=lambda t: (hashlib.md5(("MENTDRIFT-2026-11-15" + t).encode()).hexdigest(), t))[:1400]
        self.assertEqual(sorted(kept), sorted(want))


if __name__ == "__main__":
    unittest.main()
