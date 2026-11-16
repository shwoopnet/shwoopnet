#!/usr/bin/env python3
"""LATEWORD hand case (synthetic, no network)."""
import gzip, json, os, sys, tempfile, unittest, io, contextlib, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lateword_lib as L
import lateword_score as SC


def put(root, job, rows):
    d = os.path.join(root, "pull", job, "r1")
    os.makedirs(d)
    man = []
    for i, (row, body) in enumerate(rows, 1):
        with gzip.open(os.path.join(d, "%04d.json.gz" % i), "wt") as f:
            json.dump(body, f)
        man.append(dict(row, index=i, file="%04d.json.gz" % i))
    with open(os.path.join(d, "manifest.json"), "w") as f:
        json.dump({"status": "complete", "rows": man}, f)


iso = lambda ts: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
c = lambda ts, yb, ya: {"end_period_ts": ts, "yes_bid": {"close_dollars": str(yb)}, "yes_ask": {"close_dollars": str(ya)}}


class Hand(unittest.TestCase):
    def test_case(self):
        root = tempfile.mkdtemp()
        O = L.iso("2026-06-10T18:00:00")
        first = O - 20 * 3600
        def m(word, op, res, occ=O, close=O + 3600, sub=None):
            return {"ticker": "KXTRUMPMENTION-26JUN10-" + word, "event_ticker": "KXTRUMPMENTION-26JUN10", "open_time": iso(op), "occurrence_datetime": iso(occ),
                    "close_time": iso(close), "yes_sub_title": sub or word, "result": res}
        ms = [m("EARLY", first, "yes"),                       # not late
              m("LATEA", first + 7 * 3600, "yes"),            # late, YES .50 -> won
              m("LATEB", first + 8 * 3600, "no"),             # late, YES .40 -> lost
              m("LATEC", first + 9 * 3600, "yes"),            # late, YES .85 -> out of band
              m("LATED", O + 3000, "yes"),                    # late, but closes before open + 30 min: not traded
              m("LATEE", first + 6 * 3600, "yes", occ=None),  # no own occurrence: dropped
              m("NQ", first + 7 * 3600, "no", sub="Event does not qualify"),
              {"ticker": "KXTRUMPMENTION-26AUG10-X", "event_ticker": "KXTRUMPMENTION-26AUG10", "open_time": "2026-08-10T00:00:00Z",
               "occurrence_datetime": "2026-08-10T18:00:00Z", "close_time": "2026-08-10T19:00:00Z", "yes_sub_title": "X", "result": "TRAP"}]
        ms[5]["occurrence_datetime"] = ""
        put(root, "MENTDRIFT_LISTS_A", [({"id": "hist_KXTRUMPMENTION", "page": 1}, {"markets": ms, "cursor": ""})])
        w = L.late_words(L.list_rows(root))
        self.assertEqual(sorted(w), ["KXTRUMPMENTION-26JUN10-LATEA", "KXTRUMPMENTION-26JUN10-LATEB", "KXTRUMPMENTION-26JUN10-LATEC"])
        DA, DB, DC = (w["KXTRUMPMENTION-26JUN10-LATE" + k]["D"] for k in "ABC")
        self.assertEqual(DA, first + 7 * 3600 + 1800)
        put(root, "LATEWORD_CANDLES", [({"path": "/historical/markets/KXTRUMPMENTION-26JUN10-LATEA/candlesticks"}, {"candlesticks": [c(DA, .48, .50)]}),
                                       ({"path": "/historical/markets/KXTRUMPMENTION-26JUN10-LATEB/candlesticks"}, {"candlesticks": [c(DB - 60, .38, .40)]}),
                                       ({"path": "/historical/markets/KXTRUMPMENTION-26JUN10-LATEC/candlesticks"}, {"candlesticks": [c(DC, .83, .85)]})])
        with contextlib.redirect_stdout(io.StringIO()):
            o = SC.main(root)
        self.assertEqual(o["n"], 2)
        self.assertEqual(o["drops"]["out_of_band"], 1)
        # .50 fee .02 -> +.48 ; .40 fee .02 lost -> -.42 ; PF raw 48/42
        self.assertEqual(o["raw"]["pf"], round(.48 / .42, 4))
        self.assertAlmostEqual(o["raw"]["mean_c"], 3.0)
        self.assertEqual(o["bar"], "no evidence at n = 2")
        self.assertIn("no held-out read", o["result_note"])

    def test_fee_form(self):
        self.assertEqual(L.fee(0.5), 0.02)
        self.assertEqual(L.fee(0.40), 0.02)

    def test_truncated(self):
        root = tempfile.mkdtemp()
        put(root, "MENTDRIFT_LISTS_A", [({"id": "hist_KXTRUMPMENTION", "page": 10}, {"markets": [], "cursor": "abc"})])
        with contextlib.redirect_stdout(io.StringIO()):
            o = SC.main(root)
        self.assertIn("stopped", o)


if __name__ == "__main__":
    unittest.main()
