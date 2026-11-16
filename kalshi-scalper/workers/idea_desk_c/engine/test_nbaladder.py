#!/usr/bin/env python3
"""NBALADDER hand case (synthetic, no network). The numbers are worked by hand in the comments."""
import gzip, json, os, sys, tempfile, time, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import nbaladder as N

iso = lambda ts: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


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


def cd(ts, yb, ya, v):
    return {"end_period_ts": ts, "yes_bid": {"close_dollars": str(yb)}, "yes_ask": {"close_dollars": str(ya)}, "volume_fp": str(v)}


def fixture(occ_offset=0):
    root = tempfile.mkdtemp()
    O = KL.iso("2026-10-25T03:00:00") + occ_offset
    D = O - 3600
    ms = []
    for k, res in ((10, "yes"), (15, "no"), (20, "yes"), (25, "yes")):
        ms.append({"ticker": "KXNBAPTS-26OCT24AAABBB-AAAPLAYER1-%d" % k, "event_ticker": "KXNBAPTS-26OCT24AAABBB", "occurrence_datetime": iso(O),
                   "close_time": iso(O + 600), "open_time": iso(O - 20 * 3600), "result": res})
    put(root, "KXNBAPTS_LISTS_A", [({"id": "dev_KXNBAPTS", "page": 1}, {"markets": ms, "cursor": ""})])
    T = lambda k: "KXNBAPTS-26OCT24AAABBB-AAAPLAYER1-%d" % k
    mk = [{"market_ticker": T(10), "candlesticks": [cd(D, .78, .80, 0)]},
          {"market_ticker": T(15), "candlesticks": [cd(D, .58, .60, 0)]},
          {"market_ticker": T(20), "candlesticks": [cd(D - 1800, .43, .47, 0), cd(D - 900, .45, .47, 4), cd(D - 300, .47, .50, 10), cd(D, .48, .52, 0), cd(O - 600, .60, .62, 0)]},
          {"market_ticker": T(25), "candlesticks": [cd(D, .28, .32, 0)]}]
    put(root, "NBALADDER_CANDLES_P1", [({"path": "/markets/candlesticks"}, {"markets": mk})])
    return root, O, D, T


class Hand(unittest.TestCase):
    def test_cells_count(self):
        self.assertEqual(N.N_RULES, 624)
        self.assertEqual(len(N.FILTERS), 13)

    def test_features(self):
        root, O, D, T = fixture()
        dec, counts, g = N.decisions(root)
        by = {(d["t"], d["D_off"]): d for d in dec}
        r20 = by[(T(20), 3600)]
        f = r20["f"]
        # rung 20: yes mid .50 is the line; move +.05 (mid .45 half an hour earlier); spread .04; volume 10 then 4: rising; age 19h
        self.assertTrue(f["dist_at"] and not f["dist_below"] and not f["dist_above"])
        self.assertTrue(f["move_up"] and not f["move_flat"] and not f["move_down"])
        self.assertTrue(f["spread6"] and not f["spread3"])
        self.assertTrue(f["vol_rise"] and not f["vol_notrise"])
        self.assertTrue(f["age_ge6"] and not f["age_lt6"])
        self.assertTrue(by[(T(15), 3600)]["f"]["dist_below"])
        self.assertTrue(by[(T(25), 3600)]["f"]["dist_above"])
        self.assertIsNone(by[(T(15), 3600)]["f"]["move_up"])          # no earlier quote: unknown, never a guess
        self.assertEqual(counts["games"], 1)
        self.assertIsNotNone(r20["mark"])

    def test_net_hand(self):
        root, O, D, T = fixture()
        dec, _, _ = N.decisions(root)
        d = {(x["t"], x["D_off"]): x for x in dec}[(T(20), 3600)]
        # H: YES ask .52 + 1c = .53, 10 contracts = 5.30; fee ceil(round(.07*10*.53*.47*100, 9)) = ceil(17.437) = 18 -> .18; won: 10 - 5.48 = +4.52
        x, why = N.net(d, "yes", 0.52, 10, 0.01, "H", d["mark"], "yes")
        self.assertEqual((round(x, 6), why), (4.52, "settle"))
        # M10: sell at the mark bid .60 - 1c = .59 (the rung closes 1200 s after the mark); 5.90 - 5.48 - fee(.59): ceil(round(.07*10*.59*.41*100, 9)) = ceil(16.933) = 17 -> .17 = +0.25
        x, why = N.net(d, "yes", 0.52, 10, 0.01, "M10", d["mark"], "yes")
        self.assertEqual((round(x, 6), why), (0.25, "time"))
        self.assertEqual(N.net(d, "yes", 0.52, 10, 0.01, "M10", None, "yes"), (None, "no mark"))

    def test_clock_drop(self):
        root, O, D, T = fixture(occ_offset=900)                        # occurrence on :15, not a schedule time
        dec, counts, g = N.decisions(root)
        self.assertEqual(counts["clock_dropped_games"], 1)
        self.assertEqual(dec, [])

    def test_run_counts(self):
        root, O, D, T = fixture()
        o = N.run(root)
        self.assertEqual(o["m_total"], 624)
        self.assertEqual(o["cells_clearing_every_gate"], 0)             # 4 rungs: no cell reaches 48 trades
        self.assertEqual(o["counts"]["games"], 1)


if __name__ == "__main__":
    unittest.main()
