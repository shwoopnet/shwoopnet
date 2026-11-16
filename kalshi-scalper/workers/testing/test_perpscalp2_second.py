import math, unittest
import perpscalp2_second as m
import lane4_plugin as L4
import engine1_perps_second as p

L = 1794873600 // 86400 + 0; L = (1793664000 // 86400); o = L4.et_end(L, 9, 30)
def fx():
    s = {}
    # 70 minutes of history from 08:20 to 09:30 alternating +-0.05% so sigma1 defined; mids around 100
    for i in range(-70, 0):
        t = o + 60 * i; px = 100 * (1 + (0.0005 if i % 2 else -0.0005)); s[t] = (px - .01, px + .01, 10)
    for i in range(0, 30):
        t = o + 60 * i; px = 100.0 + (0 if i <= 5 else (0.02 + 0.02 * (i - 6)) if i < 10 else 0.5)
        s[t] = (px - .01, px + .01, 10)
    return s

class T(unittest.TestCase):
    def test_counts(self): self.assertEqual(m.N_CELLS, 168)
    def test_orb_signal(self):
        s = fx(); sg = m.signals(s, "orb", 5)
        self.assertEqual(sg[0][1], 1); self.assertGreater(sg[0][0], o + 5 * 60)
    def test_tt_trade(self):
        s = fx(); sg = m.signals(s, "orb", 5); t, d = sg[0]
        cell = (("E3", "orb", 5), "W0", 1, 600)
        tr, cnt = m.run_cell({"X": s}, {}, {"X": 0.02}, cell, "TT")
        self.assertEqual(len(tr), 1)
        U = m.sigma1(s, t) * math.sqrt(10); ref = m.mid(s[t]); tgt = ref * (1 + U)
        c = s[t + 60]; ep = c[1] * 1.0002; self.assertEqual(tr[0]["e"], t + 60)
        # exit: first candle with bid >= tgt, else time
        x = None
        for u in range(t + 120, t + 60 + 600 + 1, 60):
            if u in s and s[u][0] >= tgt: x = u; break
        if x is None: x = t + 60 + 600
        xp = s[x][0] * 0.9998; net = xp / ep - 1 - 0.0024
        self.assertAlmostEqual(tr[0]["net"], net, 12)
    def test_ts_haircut(self):
        s = fx(); cell = (("E3", "orb", 5), "W0", 1, 600)
        a, _ = m.run_cell({"X": s}, {}, {"X": 0.02}, cell, "TT"); b, _ = m.run_cell({"X": s}, {}, {"X": 0.02}, cell, "TS")
        self.assertLess(b[0]["net"], a[0]["net"])
    def test_funding_sign(self):
        s = fx(); cell = (("E3", "orb", 5), "W0", 1, 600); a, _ = m.run_cell({"X": s}, {}, {"X": 0.02}, cell, "TT")
        f = {a[0]["e"] + 60: 0.0001}; b, _ = m.run_cell({"X": s}, {"X": f}, {"X": 0.02}, cell, "TT")
        self.assertAlmostEqual(b[0]["net"], a[0]["net"] - 0.0001, 12); self.assertTrue(b[0]["span"])
    def test_window_drop(self):
        s = fx(); cell = (("E3", "orb", 5), "W3", 1, 600); tr, cnt = m.run_cell({"X": s}, {}, {"X": 0.02}, cell, "TT")
        self.assertEqual(tr, []); self.assertEqual(cnt["window"], 1)
    def test_maker_fill(self):
        s = fx(); t, d = m.signals(s, "orb", 5)[0]; lim = s[t][0]
        s2 = dict(s); c = s[t + 60]; s2[t + 60] = (lim - 0.05, lim - 0.03, 10)  # ask <= limit - tick
        en = m.entry_of(s2, t, 1, "MT2", 0.0002, 0.02); self.assertEqual(en, (t + 60, lim, 0.0005))
        s3 = dict(s); s3[t + 60] = (lim - 0.05, lim - 0.01, 10); s3[t + 120] = (lim - 0.05, lim - 0.01, 10)
        self.assertIsNone(m.entry_of(s3, t, 1, "MT2", 0.0002, 0.02))

class T2(unittest.TestCase):
    def test_orb_strict(self):
        s = fx(); hi = max(m.mid(s[o + 60 * i]) for i in range(1, 6))
        for i in range(6, 9): s[o + 60 * i] = (hi - .01, hi + .01, 10)   # equals the high: not a breakout
        sg = m.signals(s, "orb", 5); self.assertGreater(sg[0][0], o + 60 * 8)
    def test_kt_scales_target(self):
        s = fx(); t, d = m.signals(s, "orb", 5)[0]; U = m.sigma1(s, t) * math.sqrt(10); ref = m.mid(s[t])
        s[t + 120] = (ref * (1 + 1.4 * U), ref * (1 + 1.4 * U) + .02, 10)   # clears 1.0 U, not 2.0 U
        e = t + 60; a = m.exit_of(s, t, 1, e, 0, 1, 600, .0002, "TT", .02, U); b = m.exit_of(s, t, 1, e, 0, 2, 600, .0002, "TT", .02, U)
        self.assertEqual((a[0], a[3]), (t + 120, "target")); self.assertEqual(b[3], "time")
    def test_cooldown_900(self):
        s = fx(); cell = (("E3", "orb", 5), "W0", 1, 600)
        t, d = m.signals(s, "orb", 5)[0]
        sig = [(t, 1), (t + 12 * 60, 1)]; orig = m.signals; m.signals = lambda *a: sig
        try:
            tr, cnt = m.run_cell({"X": s}, {}, {"X": .02}, cell, "TT")
        finally: m.signals = orig
        self.assertEqual((len(tr), cnt["cooldown"]), (1, 1))
    def test_cap_10min(self):
        s = fx(); L2 = m.day_of(o); end = m.session_end(L2)
        self.assertTrue(m.in_window("W3", end - 10 * 60)); self.assertFalse(m.in_window("W3", end - 10 * 60 + 60))

class T3(unittest.TestCase):
    def test_margin_hand(self):
        tr = [{"name": "KXNVDAPERP", "net": 0.0, "U": 0.0015811}, {"name": "KXNVDAPERP", "net": -0.003, "U": 0.02}]
        r = m.margin(tr)["50%"]                          # L = 0.5 x 4.5 = 2.25; liq = 1/2.25 - 0.045 = 0.399444
        self.assertAlmostEqual(r["mean_pct_of_margin"], 100 * (-0.003 * 2.25) / 2, 12); self.assertEqual(r["stop_beyond_liquidation"], 0)
        r = m.margin(tr, {"KXNVDAPERP": 40.0})["50%"]    # L = 20, liq = 0.005: U 0.02 beyond, U 0.0015811 not
        self.assertEqual(r["stop_beyond_liquidation"], 1)
        r = m.margin([{"name": "KXNVDAPERP", "net": 0.0, "U": 1 / 20 - 0.045}], {"KXNVDAPERP": 40.0})["50%"]; self.assertEqual(r["stop_beyond_liquidation"], 1)   # at equality counts
    def test_adverse_hand(self):
        s = fx(); cell = (("E3", "orb", 5), "W0", 1, 600); t, d = m.signals(s, "orb", 5)[0]
        tn = m.taker_net(s, "X", {}, 0.02, cell, t, d); self.assertIsNotNone(tn)
        a = m.adverse({"X": s}, {}, {"X": 0.02}, cell, 2); self.assertEqual(a["filled_n"] + a["unfilled_n"], 1)
        v = a["filled_mean_bps"] if a["filled_n"] else a["unfilled_mean_bps"]; self.assertAlmostEqual(v, tn * 1e4, 9)
    def test_no_taker_target_in_mm(self):
        s = fx(); t, d = m.signals(s, "orb", 5)[0]; U = m.sigma1(s, t) * math.sqrt(10); ref = m.mid(s[t]); tgt = ref * (1 + U)
        for u in range(t + 120, t + 60 * 40, 60): s[u] = (ref, ref + .02, 10)
        s[t + 120] = (tgt + 0.005, tgt + 0.025, 10)          # bid above the target, below target + tick
        self.assertEqual(m.exit_of(s, t, 1, t + 60, 0, 1, 600, .0002, "TT", .02, U)[3], "target")
        self.assertEqual(m.exit_of(s, t, 1, t + 60, 0, 1, 600, .0002, "MM2", .02, U)[3], "time")

class T4(unittest.TestCase):
    def test_equal_bid_ask_usable(self):
        self.assertTrue(m.usable((100.0, 100.0, 1))); self.assertFalse(m.usable((100.01, 100.0, 1))); self.assertFalse(m.usable((0, 1, 1)))
