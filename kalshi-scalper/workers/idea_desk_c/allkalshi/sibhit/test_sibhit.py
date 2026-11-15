#!/usr/bin/env python3
"""SIBHIT hand case (synthetic, no network)."""
import gzip, json, os, sys, tempfile, unittest, io, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sibhit_lib as L
import sibhit_score as SC


def put(root, job, rid, body):
    d = os.path.join(root, "pull", job, "r1")
    os.makedirs(d, exist_ok=True)
    with gzip.open(os.path.join(d, "0001.json.gz"), "wt") as f:
        json.dump(body, f)
    with open(os.path.join(d, "manifest.json"), "w") as f:
        json.dump({"status": "complete", "rows": [{"index": 1, "id": rid, "file": "0001.json.gz"}]}, f)


def iso(ts):
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


class Hand(unittest.TestCase):
    def test_game(self):
        root = tempfile.mkdtemp()
        occ = L.iso("2026-10-25T03:00:00")
        T = occ - 3600
        ms = []
        # 11 rungs open at occ-180; 2 hit well before T, 1 closes exactly at T-240 (NOT counted: strict); s = 2/11 >= median -> HIGH; 8 open after T
        for i in range(11):
            close = occ - 7000 if i < 2 else (T - 240 if i == 10 else occ + 600)
            ms.append({"ticker": "KXNBAPTS-26OCT24AAABBB-P%d-10" % i, "event_ticker": "KXNBAPTS-26OCT24AAABBB", "close_time": iso(close),
                       "occurrence_datetime": iso(occ), "result": "yes" if i in (2, 3) else "no"})
        ms.append({"ticker": "KXNBAPTS-26NOV08AAABBB-P0-10", "event_ticker": "KXNBAPTS-26NOV08AAABBB", "close_time": "2026-11-08T03:00:00Z",
                   "occurrence_datetime": "2026-11-08T03:00:00Z", "result": "TRAP"})
        put(root, "KXNBAPTS_LISTS_A", "dev_KXNBAPTS", {"markets": ms})
        g = L.games(L.list_rows(root))
        self.assertEqual(list(g), ["KXNBAPTS-26OCT24AAABBB"])
        self.assertEqual(g["KXNBAPTS-26OCT24AAABBB"]["arm"], "HIGH")
        self.assertEqual(len(g["KXNBAPTS-26OCT24AAABBB"]["open"]), 8)
        self.assertAlmostEqual(g["KXNBAPTS-26OCT24AAABBB"]["s"], 2 / 11)
        c = lambda ts, yb, ya: {"end_period_ts": ts, "yes_bid": {"close_dollars": str(yb)}, "yes_ask": {"close_dollars": str(ya)}}
        mk = [{"market_ticker": "KXNBAPTS-26OCT24AAABBB-P2-10", "candlesticks": [c(T, .48, .50)]},       # in band: YES .50, won
              {"market_ticker": "KXNBAPTS-26OCT24AAABBB-P3-10", "candlesticks": [c(T - 120, .38, .40)]}, # latest in window: YES .40, won
              {"market_ticker": "KXNBAPTS-26OCT24AAABBB-P4-10", "candlesticks": [c(T, .58, .60)]},       # YES .60, lost
              {"market_ticker": "KXNBAPTS-26OCT24AAABBB-P5-10", "candlesticks": [c(T, .80, .82)]},       # out of band
              {"market_ticker": "KXNBAPTS-26OCT24AAABBB-P6-10", "candlesticks": [c(T - 240, .48, .50)]}]  # too old: no quote
        put(root, "SIBHIT_CANDLES", "x", {"markets": mk})
        with contextlib.redirect_stdout(io.StringIO()):
            o = SC.main(root)
        self.assertEqual(o["HIGH"]["n"], 3)
        self.assertEqual(o["drops"]["out_of_band"], 1)
        self.assertEqual(o["drops"]["no_quote"], 4)    # P6 too old plus P7..P9 with no candle
        # raw: .50 fee .02 -> +.48 ; .40 fee .02 -> +.58 ; .60 fee .02 -> -.62 ; mean = .44/3
        self.assertAlmostEqual(o["HIGH"]["raw"]["mean_c"], round(100 * 0.44 / 3, 3))
        self.assertEqual(o["HIGH"]["raw"]["pf"], round(1.06 / 0.62, 4))
        self.assertIn("info_first_half_median_split", o)
        self.assertEqual(o["share_per_game"]["max"], round(2 / 11, 4))


if __name__ == "__main__":
    unittest.main()
