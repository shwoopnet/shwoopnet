#!/usr/bin/env python3
"""Hand cases for deskc_kp_load.py and the MENTTWIN plugin (synthetic, no network)."""
import gzip, io, json, os, sys, tempfile, time, unittest, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import menttwin as P
import menttwin_run as R

iso = lambda ts: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
c = lambda ts, yb, ya: {"end_period_ts": ts, "yes_bid": {"close_dollars": str(yb)}, "yes_ask": {"close_dollars": str(ya)}}


def put(root, job, rows):
    d = os.path.join(root, "pull", job, "r1")
    os.makedirs(d)
    man = [{"index": 0, "id": "x", "status": 429}]                 # a 429 row stores nothing and must be skipped
    for i, (row, body) in enumerate(rows, 1):
        with gzip.open(os.path.join(d, "%04d.json.gz" % i), "wt") as f:
            json.dump(body, f)
        man.append(dict(row, index=i, file="%04d.json.gz" % i))
    with open(os.path.join(d, "manifest.json"), "w") as f:
        json.dump({"status": "complete", "rows": man}, f)


class Loader(unittest.TestCase):
    def test_wall(self):
        root = tempfile.mkdtemp()
        ms = [{"ticker": "KXTRUMPMENTION-26JUN10-A", "event_ticker": "E", "occurrence_datetime": "2026-06-10T18:00:00Z", "close_time": "2026-06-10T19:00:00Z",
               "open_time": "2026-06-09T00:00:00Z", "yes_sub_title": "a", "title": "t", "result": "yes", "yes_bid_dollars": "0.5"},
              {"ticker": "KXTRUMPMENTION-26AUG10-A", "event_ticker": "F", "occurrence_datetime": "2026-08-10T18:00:00Z", "close_time": "2026-08-10T19:00:00Z", "result": "TRAP"},
              {"ticker": "KXTRUMPMENTION-26JUN10-B", "event_ticker": "E", "occurrence_datetime": "", "close_time": "2026-06-10T19:00:00Z", "result": "TRAP"}]
        put(root, "L", [({"id": "p", "page": 1}, {"markets": ms, "cursor": ""})])
        mk = KL.markets(root, ("L",), ("KXTRUMPMENTION",), "occurrence", *P.DEV)
        self.assertEqual(list(mk), ["KXTRUMPMENTION-26JUN10-A"])
        self.assertNotIn("result", mk["KXTRUMPMENTION-26JUN10-A"])
        self.assertNotIn("yes_bid_dollars", mk["KXTRUMPMENTION-26JUN10-A"])
        self.assertFalse(KL.truncated(root, "L", "p", P.DEV[0]))

    def test_truncation_by_coverage(self):
        root = tempfile.mkdtemp()
        put(root, "L", [({"id": "p", "page": 1}, {"markets": [{"ticker": "X", "close_time": "2026-06-01T00:00:00Z"}], "cursor": "c"})])
        self.assertTrue(KL.truncated(root, "L", "p", KL.iso("2026-04-17T00:00:00")))
        self.assertFalse(KL.truncated(root, "L", "p", KL.iso("2026-07-01T00:00:00")))

    def test_quote_cut(self):
        root = tempfile.mkdtemp()
        put(root, "C", [({"path": "/historical/markets/T1/candlesticks"}, {"candlesticks": [c(100, .4, .42), c(200, .5, .52)]})])
        q = KL.quotes(root, ("C",), {"T1": 150})
        self.assertEqual(sorted(q["T1"]), [100])                     # nothing after the cut
        self.assertEqual(KL.quote_at(q["T1"], 150, 180), (0.4, 0.42))
        self.assertIsNone(KL.quote_at(q["T1"], 400, 180))


class Twin(unittest.TestCase):
    def test_hand(self):
        root = tempfile.mkdtemp()
        O = KL.iso("2026-06-10T18:00:00")
        oa, ob = O - 20 * 3600, O - 10 * 3600
        D = ob + 1800
        def m(ev, w, op, res):
            return {"ticker": "KXTRUMPMENTION%s-26JUN10%s-%s" % ("" if ev == "A" else "B", "" if ev == "A" else "B", w), "event_ticker": "EV" + ev,
                    "occurrence_datetime": iso(O), "close_time": iso(O + 3600), "open_time": iso(op), "yes_sub_title": w, "title": "", "result": res}
        ms = [m("A", "TARIFF", oa, "yes"), m("B", "TARIFF", ob, "yes"),    # gap .30: buy YES on the cheap twin (B at .41), won
              m("A", "CHINA", oa, "no"), m("B", "CHINA", ob, "no"),        # gap .05: no trade
              m("A", "SOLO", oa, "yes")]                                    # no twin
        put(root, "MENTDRIFT_LISTS_A", [({"id": "hist_KXTRUMPMENTION", "page": 1}, {"markets": ms, "cursor": ""})])
        tk = {x["yes_sub_title"] + x["event_ticker"]: x["ticker"] for x in ms}
        put(root, "MENTTWIN_CANDLES_P1", [({"path": "/historical/markets/%s/candlesticks" % tk["TARIFFEVA"]}, {"candlesticks": [c(D, .69, .71)]}),
                                          ({"path": "/historical/markets/%s/candlesticks" % tk["TARIFFEVB"]}, {"candlesticks": [c(D - 60, .39, .41)]}),
                                          ({"path": "/historical/markets/%s/candlesticks" % tk["CHINAEVA"]}, {"candlesticks": [c(D, .40, .42)]}),
                                          ({"path": "/historical/markets/%s/candlesticks" % tk["CHINAEVB"]}, {"candlesticks": [c(D, .45, .47)]})])
        es, why, npairs = P.entries(root)
        self.assertEqual(npairs, 2)
        self.assertEqual(why, {"ok": 1, "small_gap": 1})
        self.assertEqual([(e["id"], e["ask"], e["result"]) for e in es], [(tk["TARIFFEVB"], 0.41, "yes")])
        with contextlib.redirect_stdout(io.StringIO()):
            o = R.main(root)
        # 10 contracts at .42 (1c): cost 4.20 + fee ceil(0.07*10*.42*.58*100)/100 = ceil(17.052)/100 = .18 -> 4.38; won 10 -> +5.62
        self.assertAlmostEqual(o["1c"]["net"], 5.62)
        self.assertEqual(o["bar"], "no evidence at n = 1")


if __name__ == "__main__":
    unittest.main()
