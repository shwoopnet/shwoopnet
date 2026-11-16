import math, unittest
import lanes16_second as m, pool1_second as P, engine1_perps_second as p
L = 1793664000 // 86400; E0 = P.et_end(L, 9, 30); E1 = P.et_end(L, 10, 31)

def q(mid_, sp=0.02): return (round(mid_ - sp / 2, 6), round(mid_ + sp / 2, 6))

def base(shift=0.0):
    """one name: 09:00 to 12:00 ET minute candles, mid 100 with a tiny alternating pattern (sigma defined); shift applied from 10:00 on"""
    s = {}
    for t in range(P.et_end(L, 8, 0), P.et_end(L, 12, 0) + 1, 60):
        k = (t - E0) // 60; px = 100 * (1 + (0.0001 if k % 2 else -0.0001)); s[t] = q(px * (1 + (shift if t >= P.et_end(L, 10, 0) else 0)))
    return s

FP = {E0 + 28800 * k: 0.0 for k in range(0, 4)}


def sigma_u(s, e): return P.sigma(s, e) * math.sqrt(30)

class T(unittest.TestCase):
    def test_rs(self):
        data = {"X": base(0.02), "Y": base(), "Z": base()}; sig = {}; days = {L}; e = E1
        ev = m.rs_events(data, ("X", "Y", "Z"), 60, 1, "follow", sig, days)
        R_x = math.log(p.mid(data["X"][e]) / p.mid(data["X"][e - 3600])); self.assertAlmostEqual(R_x, math.log(1.02), 6)
        x = [v for v in ev if v[0] == e and v[1] == "X"]; self.assertEqual(len(x), 1); self.assertEqual(x[0][2], "long")
        self.assertAlmostEqual(x[0][3], sigma_u(data["X"], e), 12)
        self.assertEqual([v[2] for v in ev if v[0] == e and v[1] == "Y"], ["short"])   # Y's own sigma is tiny: RS_Y = -0.01 beats u_Y, follow = short
        rv = m.rs_events(data, ("X", "Y", "Z"), 60, 1, "revert", sig, days); self.assertEqual([v[2] for v in rv if v[0] == e and v[1] == "X"], ["short"])
        self.assertEqual([v for v in m.rs_events(data, ("X", "Y", "Z"), 60, 2, "follow", sig, days) if v[0] == e and v[1] == "X"], [])   # c = 2: RS_X 0.02 < 2 u_X (0.0286)
    def test_rs_needs_all_names(self):
        data = {"X": base(0.02), "Y": base(), "Z": base()}; del data["Z"][E1]
        self.assertEqual([v for v in m.rs_events(data, ("X", "Y", "Z"), 60, 1, "follow", {}, {L}) if v[0] == E1], [])
    def test_tt_hand(self):
        s = base(); e = E1 + 60 * 10; u = sigma_u(s, e)
        s[e] = (100.0, 100.02); s[e + 60] = (100.0 * (1 + 0.5 * u), 100.1)       # bid beyond the target kt = 1 / ks = 1 only if > u: set one u above
        s[e + 60] = (100.02 * (1.0002) * (1 + 1.0 * u) / 0.9998 + 0.001, 200.0)
        ev = [(e, "N", "long", u)]; tr, cnt, _ = m.single_trades({"N": s, "M": s}, {"N": FP}, ev, (1, 1, 15), 0.0002, "TT", 0, {})
        self.assertEqual(len(tr), 1); fill = 100.02 * 1.0002; xp = s[e + 60][0] * 0.9998; self.assertEqual(tr[0]["exit_ts"], e + 60)
        self.assertAlmostEqual(tr[0]["gross"], xp / fill - 1, 12); self.assertAlmostEqual(tr[0]["net"], xp / fill - 1 - 0.0024, 12)
    def test_me_mm(self):
        s = base(); e = E1 + 600; u = sigma_u(s, e); tk = 0.01
        s[e] = (100.00, 100.02); s[e + 60] = (99.97, 99.99)                      # ask 99.99 <= 100.00 - 0.01: fills the long limit 100.00 at e + 60
        fill = 100.00; tgt = fill * (1 + u)
        s[e + 120] = (tgt + tk, tgt + tk + 0.02)                                  # bid >= target + tick
        f = {"N": FP}; ev = [(e, "N", "long", u)]
        tr, cnt, _ = m.single_trades({"N": s}, f, ev, (1, 1, 15), 0.0002, "MM", 2, {"N": tk})
        self.assertEqual(len(tr), 1); self.assertEqual(tr[0]["start"], e + 60); self.assertEqual(tr[0]["exit_ts"], e + 120)
        self.assertAlmostEqual(tr[0]["net"], tgt / fill - 1 - 2 * 0.0005, 12)
        tr, cnt, _ = m.single_trades({"N": s}, f, ev, (1, 1, 15), 0.0002, "ME", 2, {"N": tk})   # taker target at bid x (1 - h), fee 5 + 12
        self.assertAlmostEqual(tr[0]["net"], s[e + 120][0] * 0.9998 / fill - 1 - 0.0005 - 0.0012, 12)
        s2 = dict(s); s2[e + 60] = (99.97, 100.00)                                # ask equals the limit: not through by a tick
        tr, cnt, unf = m.single_trades({"N": s2}, f, ev, (1, 1, 15), 0.0002, "MM", 1, {"N": tk}); self.assertEqual((len(tr), cnt["unfilled"]), (0, 1))
    def test_mm_no_taker_target(self):
        s = base(); e = E1 + 600; u = sigma_u(s, e); tk = 0.01; s[e] = (100.00, 100.02); s[e + 60] = (99.97, 99.99); tgt = 100.0 * (1 + u)
        s[e + 120] = (tgt + 0.005, tgt + 0.025)                                   # bid at the target but under target + tick
        f = {"N": FP}
        tr, _, _ = m.single_trades({"N": s}, f, [(e, "N", "long", u)], (1, 1, 15), 0.0002, "MM", 2, {"N": tk}); self.assertNotEqual(tr[0]["exit_ts"], e + 120)
    def test_pair_hand(self):
        a, c = base(), base(); e = E1 + 600; us = 0.004
        a[e] = (100.0, 100.02); c[e] = (50.0, 50.01)                               # long c at ask 50.01 x 1.0002, short a at bid 100 x 0.9998
        lfill = 50.01 * 1.0002; sfill = 100.0 * 0.9998
        c[e + 60] = (50.4, 50.42); a[e + 60] = (99.5, 99.52)
        R = (50.4 * 0.9998 / lfill - 1) + (sfill - 99.52 * 1.0002) / sfill; self.assertGreater(R, us)
        f = {"a": FP, "c": FP}
        tr, cnt, _ = m.pair_trades({"a": a, "c": c}, f, [(e, "a", "c", "c", "a", us)], (1, 1, 15), 0.0002, "TT", 0, {})
        self.assertEqual(len(tr), 1); self.assertAlmostEqual(tr[0]["R"], R, 12); self.assertAlmostEqual(tr[0]["net"], (R - 0.0048) / 2, 12)
        self.assertEqual(tr[0]["exit_ts"], e + 60)
    def test_pair_blocked_and_unfilled(self):
        a, c = base(), base(); e = E1 + 600; f = {"a": FP, "c": FP}
        tr, cnt, unf = m.pair_trades({"a": a, "c": c}, f, [(e, "a", "c", "c", "a", 0.004)], (1, 1, 15), 0.0002, "ME", 2, {"a": 0.01, "c": 0.01})
        self.assertEqual((len(tr), cnt["unfilled"]), (0, 1))                       # flat quotes never trade through by a tick
    def test_margin(self):
        tr = [{"name": "A", "side": "long", "net": 0.001, "legs": (("A", 1.0),)}, {"name": "A/B", "side": "pair", "net": 0.0005, "net_leg": 0.001, "legs": (("A", 1.0), ("B", 1.0))}]
        r = m.margin(tr, {"A": 10.0, "B": 20.0})["50%"]                           # L_A = 5, L_B = 10
        self.assertAlmostEqual(r["mean_pct_of_margin"], (100 * 0.001 * 5 + 100 * 0.001 / (1 / 5 + 1 / 10)) / 2, 12)
        self.assertAlmostEqual(r["worst_liq"], min(1 / 5 - 0.045, 1 / 5 - 0.045, 1 / 10 - 0.045), 12)
        with self.assertRaises(SystemExit): m.margin(tr, {"A": 10.0})
        r = m.margin([{"name": "KXGOLDPERP", "side": "long", "net": 0.0, "legs": (("KXGOLDPERP", 1.0),)}], {"KXGOLDPERP": 45.0})["50%"]
        self.assertEqual(r["no_buffer"], ["KXGOLDPERP"]); self.assertAlmostEqual(r["worst_liq"], 1 / 22.5 - 0.0447, 12)    # 4.444 percent less 4.47 percent: no buffer
    def test_tick(self):
        self.assertAlmostEqual(m.tick_of({1: (100.00, 100.03), 2: (100.01, 100.05)}), 0.01, 12)


def base2(phase, jump=0.0, at=None):
    s = {}
    for t in range(P.et_end(L, 8, 0), P.et_end(L, 12, 0) + 1, 60):
        k = (t - E0) // 60; px = 100 * (1 + (0.0001 if (k + phase) % 2 else -0.0001)); s[t] = q(px * (1 + (jump if at is not None and t == at else 0)))
    return s


class T2(unittest.TestCase):
    def test_pair_direction_and_baseline(self):
        e = E1; a = base2(0, 0.01, e); c = base2(1)
        ev = m.pair_events({"a": a, "c": c}, ("a", "c"), 120, 2, {L})
        x = [v for v in ev if v[0] == e]; self.assertEqual(len(x), 1); self.assertEqual(x[0][1:5], ("a", "c", "c", "a"))     # a rich: long c, short a
        a2 = base2(0, -0.01, e); ev = m.pair_events({"a": a2, "c": c}, ("a", "c"), 120, 2, {L}); self.assertEqual([v[3:5] for v in ev if v[0] == e], [("a", "c")])
        for k, ok in ((30, False), (15, True)):                                           # 30 of 120 baseline candles missing (0.75 W) blocks; 15 missing (0.875 W) passes
            a3 = dict(a); c3 = dict(c)
            for i in range(61, 61 + k): a3.pop(e - 60 * i); c3.pop(e - 60 * i)
            self.assertEqual(len([v for v in m.pair_events({"a": a3, "c": c3}, ("a", "c"), 120, 2, {L}) if v[0] == e]), 1 if ok else 0)
    def test_pair_me_start_fees_and_stop(self):
        a, c = base(), base(); e = E1 + 600; FP2 = {"a": FP, "c": FP}; us = 0.004; tk = {"a": 0.01, "c": 0.01}
        a[e] = (100.00, 100.02); c[e] = (50.00, 50.02)                  # long c rests at its bid 50.00, short a rests at its ask 100.02
        c[e + 60] = (49.97, 49.99)                                       # long leg fills at e + 60 (ask 49.99 <= 50.00 - 0.01)
        a[e + 120] = (100.03, 100.05)                                    # short leg fills at e + 120 (bid 100.03 >= 100.02 + 0.01)
        c[e + 180] = (50.4, 50.42); a[e + 180] = (99.5, 99.52)
        lfill, sfill = 50.00, 100.02; R = (50.4 * 0.9998 / lfill - 1) + (sfill - 99.52 * 1.0002) / sfill; self.assertGreater(R, us)
        tr, cnt, _ = m.pair_trades({"a": a, "c": c}, FP2, [(e, "a", "c", "c", "a", us)], (1, 1, 15), 0.0002, "ME", 5, tk)
        self.assertEqual(len(tr), 1); self.assertEqual(tr[0]["start"], e + 120); self.assertEqual(tr[0]["exit_ts"], e + 180)
        self.assertAlmostEqual(tr[0]["net"], (R - 2 * 0.0005 - 2 * 0.0012) / 2, 12)
        a, c = base(), base(); a[e] = (100.0, 100.02); c[e] = (50.0, 50.01); c[e + 60] = (49.0, 49.02)    # long leg falls 2 percent: stop at ks = 1, not at ks = 2 x 0.004 u
        tr, _, _ = m.pair_trades({"a": a, "c": c}, FP2, [(e, "a", "c", "c", "a", us)], (1, 1, 15), 0.0002, "TT", 0, {}); self.assertEqual(tr[0]["exit_ts"], e + 60)
        us2 = 0.012; tr, _, _ = m.pair_trades({"a": a, "c": c}, FP2, [(e, "a", "c", "c", "a", us2)], (1, 1, 15), 0.0002, "TT", 0, {}); self.assertEqual(tr[0]["exit_ts"], e + 60)      # R about -0.02: below -us2 = -0.012
        tr, _, _ = m.pair_trades({"a": a, "c": c}, FP2, [(e, "a", "c", "c", "a", 0.015)], (1, 2, 15), 0.0002, "TT", 0, {}); self.assertNotEqual(tr[0]["exit_ts"], e + 60)      # ks = 2: stop at -0.03, not hit
    def test_pair_blocked_by_second_name(self):
        a, b, c = base(), base(), base(); e = E1 + 600; f = {"a": FP, "b": FP, "c": FP}
        ev = [(e, "a", "c", "c", "a", 0.5), (e + 60, "b", "c", "c", "b", 0.5)]
        tr, cnt, _ = m.pair_trades({"a": a, "b": b, "c": c}, f, ev, (2, 2, 15), 0.0002, "TT", 0, {}); self.assertEqual((len(tr), cnt["blocked"]), (1, 1))
