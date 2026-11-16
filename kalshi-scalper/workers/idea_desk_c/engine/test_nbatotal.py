#!/usr/bin/env python3
"""NBATOTAL hand case (synthetic, no network). Numbers worked by hand in the comments."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import nbatotal as N
import test_nbaladder as T

put, cd, iso = T.put, T.cd, T.iso


def fixture():
    root = tempfile.mkdtemp()
    O = KL.iso("2026-10-25T03:00:00")
    D4, D9 = O - 14400, O - 32400
    ms = []
    for k, res in ((205, "yes"), (210, "yes"), (215, "no"), (220, "no")):
        ms.append({"ticker": "KXNBATOTAL-26OCT24AAABBB-%d" % k, "event_ticker": "KXNBATOTAL-26OCT24AAABBB", "occurrence_datetime": iso(O),
                   "close_time": iso(O + 600), "open_time": iso(O - 40 * 3600), "result": res})
    put(root, "KXNBATOTAL_LISTS_A", [({"id": "dev_KXNBATOTAL", "page": 1}, {"markets": ms, "cursor": ""})])
    Tk = lambda k: "KXNBATOTAL-26OCT24AAABBB-%d" % k
    mk = [
        # 205: yes .78/.82; 210: the line (mid .50) with move +.04 over 60 min and a spread of .04; 215: yes mid .30; 220: jumps .20 between its last two candles (in-play guard)
        {"market_ticker": Tk(205), "candlesticks": [cd(D4, .78, .82, 0)]},
        {"market_ticker": Tk(210), "candlesticks": [cd(D4 - 3600, .44, .48, 0), cd(D4 - 1500, .47, .51, 4), cd(D4 - 300, .48, .52, 10), cd(D4, .48, .52, 0),
                                                    cd(D9 - 0, .60, .62, 0), cd(O - 12600, .60, .64, 0)]},
        {"market_ticker": Tk(215), "candlesticks": [cd(D4, .28, .32, 0)]},
        {"market_ticker": Tk(220), "candlesticks": [cd(D4 - 120, .20, .24, 0), cd(D4, .43, .47, 0)]},
    ]
    put(root, "NBATOTAL_CANDLES_P1", [({"path": "/markets/candlesticks"}, {"markets": mk})])
    return root, O, D4, D9, Tk


class Hand(unittest.TestCase):
    def test_grid(self):
        self.assertEqual(N.N_RULES, 520)                    # (3 H + 2 M35) x 4 x 2 x 13
        self.assertEqual(N.DS, (32400, 18000, 14400))

    def test_features_and_guard(self):
        root, O, D4, D9, Tk = fixture()
        dec, c, g = N.decisions(root)
        by = {(d["t"], d["D_off"]): d for d in dec}
        r = by[(Tk(210), 14400)]["f"]
        # 210: yes mid .50 is the game's line; move: mid(D) .50 against mid(D - 60 min) .46 = +.04 >= .03: up; spread .04: only the 6c option;
        # volume 10 (last 30 min) against 4 (the 30 before)... 4 is at D-1500 (inside the last 30), 10 at D-300: both in (D-1800, D]: 14 against 0: rising
        self.assertTrue(r["dist_at"] and r["move_up"] and r["spread6"] and not r["spread3"] and r["vol_rise"] and r["age_ge24"])
        self.assertTrue(by[(Tk(205), 14400)]["f"]["dist_below"] and by[(Tk(215), 14400)]["f"]["dist_above"])   # strikes 205 below the line 210, 215 above
        self.assertNotIn((Tk(220), 14400), by)             # the in-play guard skipped it (mid moved .20 in its last two candles)
        self.assertEqual(c["inplay_guard_4"], 1)

    def test_m35_only_for_early_decisions(self):
        root, O, D4, D9, Tk = fixture()
        o = N.run(root)
        self.assertEqual(o["m_total"], 520)

    def test_net_mark(self):
        root, O, D4, D9, Tk = fixture()
        d = {"t": Tk(210), "close": O + 600, "O": O, "D": D4}
        mark = (.60, .64)
        # M35 YES at ask .52 + 1c = .53, 10 contracts: cost 5.30 + fee .18 = 5.48; sale bid .60 - .01 (the rung closes 15000 s after the mark) = .59:
        # 5.90 - 5.48 - fee(.59) .17 = +0.25
        x, why = N.net(d, "yes", 0.52, 10, 0.01, "M35", mark, "yes")
        self.assertEqual((round(x, 6), why), (0.25, "time"))
        self.assertEqual(N.net(d, "yes", 0.52, 10, 0.01, "M35", None, "yes"), (None, "no mark"))


class RunPrint(unittest.TestCase):
    def test_header_first(self):
        import io, contextlib, json
        import nbatotal_run as R
        root, O, D4, D9, Tk = fixture()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            R.main(root, 6290660, 1250)
        lines = buf.getvalue().split("\n")
        h = json.loads(lines[0])
        self.assertEqual((h["m_carried"], h["m_new"], h["m_total"]), (6290660, 1770, 6292430))     # 520 + 1,250 other rules
        self.assertIn("counts", json.loads(lines[1]))


if __name__ == "__main__":
    unittest.main()
