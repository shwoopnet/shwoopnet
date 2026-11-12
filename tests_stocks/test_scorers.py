"""Synthetic tests only. No market data. Run: python3 -I -m unittest discover -s tests_stocks -t ."""
import os, tempfile, unittest
import numpy as np, pandas as pd
from stocks_desk import common as C, scorers as S

def make_daily(n_sym=80, start="2018-05-01", end="2020-12-31", seed=1, on_mu=None, intra_mu=None, sd=30.0):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, end); rows = []
    for k in range(n_sym):
        px = 50.0
        mu_on = (on_mu(k) if on_mu else 0.0); mu_in = (intra_mu(k) if intra_mu else 0.0)
        for d in dates:
            o = px * (1 + (mu_on + rng.normal(0, sd)) / 1e4)
            c = o * (1 + (mu_in + rng.normal(0, sd)) / 1e4)
            rows.append((d, f"X{k:03d}", o, c, 1e6)); px = c
    return pd.DataFrame(rows, columns=["date", "symbol", "open", "close", "volume"])

class Basics(unittest.TestCase):
    def test_pf_and_events(self):
        self.assertAlmostEqual(C.profit_factor([2, 1, -1.5]), 2.0)
        self.assertAlmostEqual(C.events_needed(), 1141, delta=2)
        self.assertAlmostEqual(C.events_needed(C.Z_RESEARCH, 0.84), 1519, delta=3)
    def test_windows_and_cutoff(self):
        self.assertEqual(C.window_of("2024-06-28"), "W2"); self.assertEqual(C.window_of("2024-07-01"), "W3")
        self.assertEqual(C.HELDOUT_START, pd.Timestamp("2024-07-01"))
    def test_labels(self):
        ok = {w: {"n": 600, "pf": 1.6, "mean_bp": 5, "z": 6} for w in ("W1", "W2", "W3")}
        ok["DEV"] = {"n": 1200, "pf": 1.6, "mean_bp": 5, "z": 6}
        self.assertTrue(C.label(ok, True).startswith("cleared its registered bar"))
        self.assertNotIn("cleared", C.label(ok, False))          # screens never clear
        small = {w: {"n": 50, "pf": 1.6, "mean_bp": 5, "z": 3} for w in ("W1", "W2", "W3")}
        small["DEV"] = {"n": 100, "pf": 1.6, "mean_bp": 5, "z": 3}
        self.assertTrue(C.label(small, True).startswith("no evidence at n = 150"))
        bad = dict(small); bad["DEV"] = {"n": 150, "pf": 0.8, "mean_bp": -1, "z": -2}
        self.assertTrue(C.label(bad, True).startswith("FALSIFIED"))
    def test_split_drop(self):
        d = make_daily(2, end="2018-08-01"); d.loc[(d.symbol == "X000") & (d.date >= "2018-06-01"), ["open", "close"]] *= 0.1
        n = len(C.drop_splits(d)); self.assertLess(n, len(d))
    def test_heldout_marker_once(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "m.txt"); C.read_heldout_once("S1", p)
            with self.assertRaises(RuntimeError): C.read_heldout_once("S1", p)
            C.read_heldout_once("S2", p)

class S1(unittest.TestCase):
    def test_flat_prices_pnl_is_exactly_cost(self):
        d = make_daily(4, sd=0.0)
        pnl, _ = S.s1_overnight_etf(d)
        self.assertTrue(np.allclose(pnl.values, -(2 * 0.5 + 0.206)))
    def test_planted_overnight_drift(self):
        d = make_daily(4, on_mu=lambda k: 10.0, intra_mu=lambda k: -10.0, sd=1.0)
        pnl, meta = S.s1_overnight_etf(d)
        self.assertAlmostEqual(pnl.mean(), 10 - 1.206, delta=0.5)
        self.assertLess(meta["control_intraday_gross_bp"], -8)

class S2(unittest.TestCase):
    def test_planted_clientele_beats_null_and_costs_bite(self):
        pl = make_daily(100, end="2019-06-30", on_mu=lambda k: 25.0 if k < 30 else 0.0, intra_mu=lambda k: -25.0 if k < 30 else 0.0, seed=2)
        nu = make_daily(100, end="2019-06-30", seed=3)
        a, _ = S.s2_clientele(pl, long_only=True); b, _ = S.s2_clientele(nu, long_only=True)
        self.assertGreater(a.mean(), b.mean() + 5)
        self.assertLess(b.mean(), 0)                       # null loses the round trip cost
    def test_no_lookahead_truncation_invariance(self):
        d = make_daily(60, end="2019-03-29", seed=4)
        full, _ = S.s2_clientele(d); cut_date = pd.Timestamp("2018-12-31")
        part, _ = S.s2_clientele(d[d.date <= cut_date])
        common = part.index[part.index < cut_date - pd.Timedelta(days=5)]
        self.assertGreater(len(common), 40)
        self.assertTrue(np.allclose(full.loc[common].values, part.loc[common].values))

class MOCSignalLag(unittest.TestCase):
    """Amendment 2: signals for a trade at the official close t may not use close t."""
    def test_s2_signal_ignores_todays_close(self):
        d = make_daily(60, end="2018-12-31", seed=8); t = pd.Timestamp("2018-11-15")
        a = S.s2_signal(d); d2 = d.copy(); d2.loc[d2.date == t, ["open", "close"]] *= 1.07
        b = S.s2_signal(d2); self.assertTrue(np.allclose(a.loc[t].values, b.loc[t].values, equal_nan=True))
    def test_s3_signal_ignores_todays_close_and_volume(self):
        d = make_daily(60, end="2018-12-31", seed=9); t = pd.Timestamp("2018-11-15")
        a, av = S.s3_signal(d); d2 = d.copy(); d2.loc[d2.date == t, "close"] *= 1.07; d2.loc[d2.date == t, "volume"] *= 9
        b, bv = S.s3_signal(d2)
        self.assertTrue(np.allclose(a.loc[t].values, b.loc[t].values, equal_nan=True))
        self.assertTrue(np.allclose(av.loc[t].values, bv.loc[t].values, equal_nan=True))

class S3(unittest.TestCase):
    def test_runs_and_pays_round_trip(self):
        d = make_daily(120, end="2019-12-31", seed=5)
        pnl, _ = S.s3_reversal(d)
        self.assertGreater(len(pnl), 40)
        self.assertLess(pnl.mean(), 0)                     # no planted reversal, 30bp round trip must bite

class S4(unittest.TestCase):
    def test_todays_volume_cannot_change_selection(self):
        d = make_daily(60, end="2019-03-29", seed=6, sd=120.0)
        a, _ = S.s4_gap_fade(d)
        days = [x for x in a.index if x > pd.Timestamp("2018-09-01")][:15]
        self.assertGreater(len(days), 5)                   # real event days, not NaN == NaN
        for t in days:
            d3 = d.copy(); d3.loc[d3.date == t, "volume"] *= 100
            b, _ = S.s4_gap_fade(d3)
            self.assertAlmostEqual(a[t], b[t], places=9)

class S5(unittest.TestCase):
    def _frame(self, drift):
        d = make_daily(25, end="2018-12-31", seed=7, sd=5.0)
        s = d[d.symbol == "X000"].reset_index(drop=True); i = 100
        base = s.loc[i - 1, "close"]
        for j in range(i, len(s)):
            s.loc[j, "open"] = base * 1.08 if j == i else s.loc[j - 1, "close"]
            s.loc[j, "close"] = (base * 1.08) * (1 + drift) ** (j - i)
        s.loc[i, "volume"] = 5e6
        d = pd.concat([d[d.symbol != "X000"], s]); return d.sort_values(["symbol", "date"])
    def test_gap_day_move_not_captured_and_drift_is(self):
        flat, _ = S.s5_post_gap(self._frame(0.0)); drift, _ = S.s5_post_gap(self._frame(0.005))
        self.assertLess(flat.iloc[0], 0)                    # flat after the gap: costs only
        self.assertGreater(drift.iloc[0], 800)              # 20 days at 0.5%, minus costs

def make_minute(days, prev_close=100.0, sig_ret=0.015, first_ret=0.003, final=None):
    rows = []; dd = []; pc = prev_close
    for d in pd.bdate_range("2019-01-02", periods=days):
        p1530 = pc * (1 + sig_ret)
        for hm, o, c in [("09:30", pc, pc * (1 + first_ret)), ("09:59", pc, pc * (1 + first_ret)),
                         ("15:29", p1530, p1530), ("15:30", p1530, p1530)]:
            rows.append((pd.Timestamp(f"{d.date()} {hm}"), "SPY", o, c))
        fin = p1530 * (1 + (final if final is not None else 0.003))
        dd.append((d, "SPY", pc, fin, 1e7)); pc = fin
    return (pd.DataFrame(rows, columns=["ts", "symbol", "open", "close"]),
            pd.DataFrame(dd, columns=["date", "symbol", "open", "close", "volume"]))

class S6S7(unittest.TestCase):
    def test_s6_threshold_and_entry_price(self):
        m, d = make_minute(10, sig_ret=0.015, final=0.003)
        pnl, meta = S.s6_lev_etf(m, d)
        self.assertGreater(len(pnl), 5)
        self.assertAlmostEqual(pnl.iloc[0], 30 - 1.206, delta=0.5)
        m2, d2 = make_minute(10, sig_ret=0.004)
        pnl2, meta2 = S.s6_lev_etf(m2, d2); self.assertEqual(meta2["qualifying_days"], 0)
    def test_s6_signal_ignores_bars_after_1530(self):
        m, d = make_minute(10, sig_ret=0.015)
        a, _ = S.s6_lev_etf(m, d); m = m.copy(); m.loc[m.ts.dt.strftime("%H:%M") == "15:30", "close"] *= 1.05
        b, _ = S.s6_lev_etf(m, d); self.assertTrue(np.allclose(a.values, b.values))
    def test_s7_follows_sign_of_first_30(self):
        m, d = make_minute(10, first_ret=0.003, final=0.002)
        p, _ = S.s7_first30_last30(m, d); self.assertAlmostEqual(p.iloc[0], 20 - 1.206, delta=0.5)
        m, d = make_minute(10, first_ret=-0.003, final=0.002)
        p, _ = S.s7_first30_last30(m, d); self.assertAlmostEqual(p.iloc[0], -20 - 1.206, delta=0.5)

if __name__ == "__main__":
    unittest.main()
