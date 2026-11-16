#!/usr/bin/env python3
"""SOCDRIFT hand case (synthetic, no network). Numbers worked by hand in the comments. One EPL game: O 2026-10-25 19:30Z, so K = 16:30Z (estimate), Kh = 16:00,
D(6 h) = 10:00, D(12 h) = 04:00, D(24 h) = 16:00 the day before; mark hour Mh = 14:00 (K - 2 h = 14:30)."""
import contextlib, io, json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import socdrift as N
import test_nbaladder as T

put, cd, iso = T.put, T.cd, T.iso
H = 3600


def fixture(occ="2026-10-25T19:30:00", jump_live=False, jump_m2=False, close_off=-3000):
    root = tempfile.mkdtemp()
    O = KL.iso(occ)
    K = O - 10800                                                           # 16:30
    day = KL.iso("2026-10-25T00:00:00")
    ms = []
    for sfx, res in (("MUN", "yes"), ("AVL", "no"), ("TIE", "no")):
        ms.append({"ticker": "KXEPLGAME-26OCT25MUNAVL-" + sfx, "event_ticker": "KXEPLGAME-26OCT25MUNAVL", "occurrence_datetime": iso(O),
                   "close_time": iso(O + close_off), "open_time": iso(day - 14 * 86400), "result": res})
    put(root, "SOCDERIV_LISTS", [({"id": "live_KXEPLGAME", "page": 1}, {"markets": ms, "cursor": ""})])
    Tk = lambda s: "KXEPLGAME-26OCT25MUNAVL-" + s
    h = lambda hh, mm=0: day + hh * H + mm * 60
    mun = [cd(h(4), .30, .34, 0), cd(h(5), .31, .35, 1), cd(h(7), .32, .36, 2), cd(h(9), .33, .37, 5), cd(h(10), .34, .38, 0),
           cd(h(11), .34, .38, 0), cd(h(12), .55, .59, 0) if jump_m2 else cd(h(12), .35, .39, 0), cd(h(14), .50, .54, 0)]
    if jump_live:
        mun += [cd(h(15), .40, .44, 0), cd(h(16), .60, .64, 0)]
    mk = [{"market_ticker": Tk("MUN"), "candlesticks": mun},
          {"market_ticker": Tk("AVL"), "candlesticks": [cd(h(10), .25, .30, 0)]},
          {"market_ticker": Tk("TIE"), "candlesticks": [cd(h(10), .28, .32, 0)]}]
    put(root, "SOCDRIFT_CANDLES_P1", [({"path": "/markets/candlesticks"}, {"markets": mk})])
    return root, O, Tk, h


class Hand(unittest.TestCase):
    def test_grid(self):
        self.assertEqual(N.N_RULES, 600)                              # 3 D x 2 exits x 5 bands x 2 sides x 10 filters
        self.assertEqual(len(N.SERIES), 15)
        self.assertNotIn("KXCOPADELREYGAME", N.SERIES)
        self.assertEqual(N.DS, (86400, 43200, 21600))

    def test_features_at_6h(self):
        root, O, Tk, h = fixture()
        dec, c, g = N.decisions(root)
        by = {(d["t"], d["D_off"]): d for d in dec}
        m = by[(Tk("MUN"), 21600)]
        self.assertEqual(m["D"], h(10))
        # MUN at 10:00: yes .34/.38 (mid .36), anchor 04:00 mid .32: move +.04 = move_up; spread .04: spread4 only
        # volume (07:00, 10:00] = 5 + 0 against (04:00, 07:00] = 1 + 2: 5 > 3 rising; a team rung
        f = m["f"]
        self.assertTrue(f["move_up"] and not f["move_flat"] and not f["move_down"])
        self.assertTrue(f["spread4"] and not f["spread2"])
        self.assertTrue(f["vol_rise"] and not f["vol_notrise"])
        self.assertTrue(f["team"] and not f["tie"])
        self.assertTrue(by[(Tk("TIE"), 21600)]["f"]["tie"])
        self.assertIsNone(by[(Tk("AVL"), 21600)]["f"]["move_up"])      # no anchor candle: unknown, never a guess
        self.assertEqual(m["Mh"], h(14))
        self.assertEqual(m["mark"], (.50, .54))
        self.assertEqual(c["games"], 1)
        self.assertEqual(c["live_guard_dropped_m2"], 0)

    def test_hour_boundaries(self):
        root, O, Tk, h = fixture()
        dec, c, g = N.decisions(root)
        ds = {d["D_off"]: d["D"] for d in dec if d["t"] == Tk("MUN")}
        self.assertEqual(ds[21600], h(10))                              # K - 6 h = 10:30 -> 10:00
        # at 12 h and 24 h MUN has a candle only if one ends at 04:00 (yes) or 16:00 the day before (none): 24 h has no quote
        self.assertEqual(ds[43200], h(4))
        self.assertNotIn(86400, ds)

    def test_net_hand(self):
        root, O, Tk, h = fixture()
        dec, _, _ = N.decisions(root)
        d = [x for x in dec if x["t"] == Tk("MUN") and x["D_off"] == 21600][0]
        # yes ask .38, entry haircut 1c: paid .39, 10 contracts: cost 3.90 + fee 0.17 (0.07 x 10 x .39 x .61 = .16653 -> 17 cents)
        self.assertAlmostEqual(N.net(d, "yes", .38, 10, .01, "H", d["mark"], "yes")[0], 10 - 3.90 - 0.17, 9)          # 5.93 won
        self.assertAlmostEqual(N.net(d, "yes", .38, 10, .01, "H", d["mark"], "no")[0], -3.90 - 0.17, 9)                # -4.07 lost
        self.assertAlmostEqual(N.net(d, "yes", .38, 10, .01, "H", d["mark"], "void")[0], -0.17, 9)                     # a void refunds the price, keeps the fee
        # M2 sells at the bid .50 less 1c = .49: 4.90 - 4.07 - fee(.49) 0.18 (0.07 x 10 x .49 x .51 = .17493 -> 18 cents) = 0.65
        self.assertAlmostEqual(N.net(d, "yes", .38, 10, .01, "M2", d["mark"], "no")[0], 4.90 - 4.07 - 0.18, 9)
        self.assertEqual(N.net(d, "yes", .38, 10, .01, "M2", None, "no"), (None, "no mark"))

    def test_clock_drop_and_info(self):
        root, *_ = fixture("2026-10-25T19:40:00")                       # not on a quarter hour
        dec, c, g = N.decisions(root)
        self.assertEqual((c["clock_dropped_games"], c["games"], len(dec)), (1, 0, 0))
        root, O, Tk, h = fixture(close_off=-20 * 3600)                  # closed 20 h before the occurrence = before K: information only
        dec, c, g = N.decisions(root)
        self.assertEqual(c["closed_before_K_info"], 1)

    def test_live_guard_touches_m2_only(self):
        root, O, Tk, h = fixture(jump_live=True)                        # MUN .42 at 15:00 to .62 at 16:00: the game was already live
        dec, c, g = N.decisions(root)
        self.assertEqual(c["live_guard_dropped_m2"], 1)
        self.assertTrue(dec and all(d["m2_ok"] is False for d in dec))  # M2 off for every decision of the game, H decisions kept
        self.assertTrue(any(d["D_off"] == 21600 for d in dec))

    def test_m2_guard_drops_m2_only(self):
        root, O, Tk, h = fixture(jump_m2=True)                          # .36 at 11:00 to .57 at 12:00, inside (D, mark]
        dec, c, g = N.decisions(root)
        self.assertTrue(dec and all(d["m2_ok"] is False for d in dec if d["D_off"] == 21600))
        out = N.run(root, 0)
        cells = []
        orig = N.metrics
        N.metrics = lambda rows: (cells.append(orig(rows)) or cells[-1])
        try:
            N.run(root, 0)
        finally:
            N.metrics = orig
        self.assertTrue(cells and all(m["cell"][3] == "H" for m in cells))   # no M2 cell exists for the game, H keeps it

    def test_header_first(self):
        import socdrift_run as R
        root, *_ = fixture()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            R.main(root, 6290660, 0)
        lines = buf.getvalue().split("\n")
        h = json.loads(lines[0])
        self.assertEqual((h["m_carried"], h["m_new"], h["m_total"]), (6290660, 600, 6291260))
        self.assertIn("counts", json.loads(lines[1]))


if __name__ == "__main__":
    unittest.main()
