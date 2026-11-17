import json, math, unittest
import mech1_second as m

REG = [
    {"id": "P1", "kind": "pattern", "status": "declined", "source": "7e", "market": "*", "signal": "price_change", "clock": "any_minute", "entry": "*", "exit": "*", "side": "*"},
    {"id": "PT", "kind": "pattern", "status": "declined", "source": "ban", "market": "*", "signal": "volume", "clock": "any_minute", "entry": "*", "exit": "*", "side": "*", "tickers": ["KXAAA"], "exceptions": ["ok_idea"]},
    {"id": "R1", "status": "live", "source": "x", "market": "crypto_perp", "signal": "funding_rate", "clock": "print", "entry": "taker", "exit": "next_print", "side": "follow"},
    {"id": "R2", "status": "live", "source": "x", "market": "stock_perp", "signal": "tape_flow", "clock": "any_minute", "entry": "taker", "exit": "fixed_time", "side": "follow"},
    {"id": "U1", "status": "live", "source": "x", "market": "politics", "signal": "spread", "clock": "time_of_day", "entry": "taker", "exit": "stop", "side": "follow", "verified": False, "confidence": "from_title"},
    {"id": "U2", "status": "live", "source": "x", "market": "sports", "signal": "open_interest", "clock": "time_of_day", "entry": "taker", "exit": "stop", "side": "follow", "verified": False},
    {"id": "V2", "status": "live", "source": "x", "market": "sports", "signal": "open_interest", "clock": "time_of_day", "entry": "taker", "exit": "stop", "side": "follow", "verified": True},
]
def cand(**k):
    c = {"market": "crypto_perp", "signal": "funding_rate", "clock": "print", "entry": "taker", "exit": "next_print", "side": "follow"}; c.update(k); return c

def tr(sid, window, day, ts, mkt, net, traded=True, gross=None, cost=None, n1=None, n2=None):
    g = net + 0.0012 if gross is None else gross; c = round(g - net, 9) if cost is None else cost
    return {"sig_id": sid, "window": window, "day": day, "entry_end": ts, "market_id": mkt, "traded": traded, "gross": g, "cost": c, "net": net, "net_1c": n1, "net_2c": n2}
def head(sig, thr=1.5, cal=35, units="bp", primary="bp", **k):
    h = {"sig": sig, "settings": 1, "primary": primary, "units": units, "tail": "abs", "threshold_value": thr, "calendar_days_search": cal, "calendar_days_validate": 20, "search_from": "2026-09-02", "search_to": "2026-10-06", "validate_from": "2026-10-07", "validate_to": "2026-10-26", "half1_to": "2026-09-28", "half2_from": "2026-09-29", "data": "perps_candles"}; h.update(k); return h

class T(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(m.classify(cand(signal="price_change", clock="any_minute"), REG)[:2], ("DECLINED", "P1"))
        self.assertEqual(m.classify(cand(signal="volume", clock="any_minute", tickers=["KXAAA"]), REG)[:2], ("DECLINED", "PT"))
        r = m.classify(cand(signal="volume", clock="any_minute", tickers=["KXAAA", "KXBBB"]), REG); self.assertEqual((r[0], r[3]["excluded_tickers"], r[3]["provisional"]), ("NEW", ["KXAAA"], True))
        self.assertEqual(m.classify(cand(signal="volume", clock="any_minute"), REG)[0], "NEW")                         # a ticker ban needs a candidate that names tickers
        self.assertEqual(m.classify(cand(signal="volume", clock="any_minute", tickers=["KXAAA"], idea="ok_idea"), REG)[0], "NEW")   # exception skips the pattern
        self.assertEqual(m.classify(cand(), REG)[:2], ("DUPLICATE", "R1"))
        self.assertEqual(m.classify(cand(market="index_perp"), REG)[:2], ("VERSION_NEW_MARKET", "R1"))
        self.assertEqual(m.classify(cand(market="index_perp", exit="fixed_time"), REG)[0], "NEW")                      # a new exit logic is NEW
        self.assertEqual(m.classify(cand(entry="maker_touch", side="fade"), REG)[:2], ("DUPLICATE", "R1"))             # entry and side never make it new
        self.assertEqual(m.classify(cand(market="stock_perp", signal="tape_flow", clock="any_minute", exit="fixed_time"), REG)[:2], ("DUPLICATE", "R2"))
        with self.assertRaises(ValueError): m.classify(cand(signal="bogus"), REG)
    def test_unverified_match(self):
        r = m.classify(cand(market="politics", signal="spread", clock="time_of_day", exit="stop"), REG); self.assertEqual((r[0], r[1], r[3]["provisional"]), ("DUPLICATE" if False else "UNVERIFIED_MATCH", "U1", True))   # only an unverified row matches, same market too
        r = m.classify(cand(market="weather", signal="spread", clock="time_of_day", exit="stop"), REG); self.assertEqual((r[0], r[1]), ("UNVERIFIED_MATCH", "U1"))
        r = m.classify(cand(market="sports", signal="open_interest", clock="time_of_day", exit="stop"), REG); self.assertEqual((r[0], r[1]), ("DUPLICATE", "V2"))        # a verified row decides, the unverified U2 before it is skipped
        r = m.classify(cand(market="weather", signal="open_interest", clock="time_of_day", exit="stop"), REG); self.assertEqual((r[0], r[1]), ("VERSION_NEW_MARKET", "V2"))  # verified version beats the unverified match
    def test_tail_and_days(self):
        self.assertEqual(m.tail_threshold([5, 1, 3, 2, 4, 10, 9, 8, 7, 6]), 9); self.assertEqual(m.tail_threshold([-3, 2, -1, 0.5, 4, -6, 7]), 7)   # n = 10 -> index 8; n = 7 -> ceil(6.3) - 1 = 6
        self.assertEqual(m.tail_threshold([-2]), 2); self.assertIsNone(m.tail_threshold([]))
        self.assertEqual(m.days_inclusive("2026-09-02", "2026-10-26"), 55)
    def test_halves_calendar(self):
        t = [{"day": d, "entry_end": 1, "market_id": "A", "net": 1.0} for d in ("2026-09-02", "2026-09-28", "2026-09-29", "2026-10-26")]
        a, b = m.halves(t, "2026-09-02", "2026-10-26"); self.assertEqual([x["day"] for x in a], ["2026-09-02", "2026-09-28"]); self.assertEqual([x["day"] for x in b], ["2026-09-29", "2026-10-26"])
    def test_pf_and_z(self):
        self.assertAlmostEqual(m.pf([2, -1, 1, -1]), 1.5, 12); self.assertEqual(m.pf([1, 2]), "inf"); self.assertIsNone(m.pf([])); self.assertIsNone(m.pf([0, 0]))
        z, p = m.day_z_p([{"day": "a", "net": 1.0}, {"day": "b", "net": 3.0}, {"day": "c", "net": 2.0}]); self.assertAlmostEqual(z, 2 * math.sqrt(3), 12); self.assertAlmostEqual(p, 0.5 * math.erfc(math.sqrt(6)), 12)
        self.assertEqual(m.day_z_p([{"day": "a", "net": 1.0}, {"day": "a", "net": 1.0}]), (None, None)); self.assertEqual(m.day_z_p([{"day": "a", "net": 1.0}, {"day": "b", "net": 1.0}]), (None, None))
    def test_fmt(self):
        self.assertEqual(m.fmt({"b": 3.0, "a": [1, None, True, "inf", 0.1]}), '{"a":[1,null,true,"inf",0.10000000000000001],"b":3}')
    def test_sig_id(self):
        c = cand(); self.assertEqual(m.sig_id(c), __import__("hashlib").sha256(b"crypto_perp|funding_rate|print|taker|next_print|follow").hexdigest()[:16])

def build(nets_by_day, sig, thr=2.0, window="search"):
    """one signature: header and trades from {day: [nets]}"""
    sid = m.sig_id(sig); L = [json.dumps(head(sig, thr))]; i = 0
    for d, nets in nets_by_day.items():
        for n in nets: i += 1; L.append(json.dumps(tr(sid, window, d, 1000 + i, "M%d" % (i % 3), n)))
    return sid, L

class T2(unittest.TestCase):
    W = {"search": ["2026-09-02", "2026-10-06"], "validate": ["2026-10-07", "2026-10-26"]}
    def run_sig(self, sig, days, extra=(), carried=100):
        sid, L = build(days, sig); return sid, m.run(L + list(extra), REG, self.W, carried)
    def test_screen1_threshold(self):
        # 105 traded trades over 35 calendar days = 3.0 a day: passes; 104 = 2.97 fails; mean net must be strictly positive
        sig = cand(market="index_perp", signal="open_interest", clock="any_minute")
        days = {"2026-09-%02d" % (2 + i % 28): [0.001] for i in range(105)}; sid, out = self.run_sig(sig, {"2026-09-02": [0.001] * 105})
        d = json.loads(out[0]); self.assertTrue(d["screen1"]); self.assertEqual(d["search"]["n"], 105); self.assertAlmostEqual(d["search"]["trades_per_day"], 3.0, 12)
        sid, out = self.run_sig(sig, {"2026-09-02": [0.001] * 104}); self.assertFalse(json.loads(out[0])["screen1"])
        sid, out = self.run_sig(sig, {"2026-09-02": [0.001] * 52 + [-0.001] * 53}); self.assertFalse(json.loads(out[0])["screen1"])      # mean < 0
        sid, out = self.run_sig(sig, {"2026-09-02": [0.001] * 52 + [-0.001] * 52 + [0.0, 0.0, 0.0]}); self.assertFalse(json.loads(out[0])["screen1"])     # mean exactly 0 fails (strict)
    def test_untraded_not_counted(self):
        sig = cand(market="index_perp", signal="open_interest", clock="any_minute"); sid = m.sig_id(sig)
        L = [json.dumps(head(sig))] + [json.dumps(tr(sid, "search", "2026-09-02", i, "M", 0.01, traded=(i % 2 == 0))) for i in range(10)]
        d = json.loads(m.run(L, REG, self.W, 100)[0]); self.assertEqual(d["search"]["n"], 5)
    def test_screen2_and_bh(self):
        sig = cand(market="index_perp", signal="open_interest", clock="any_minute"); sid = m.sig_id(sig)
        L = [json.dumps(head(sig, 2.0, 35))]; i = 0
        for k in range(120):                                       # 120 trades over 20 days in SEARCH (days 09-02 ..)
            i += 1; day = "2026-09-%02d" % (2 + k % 20); L.append(json.dumps(tr(sid, "search", day, i, "M%d" % (k % 3), 0.003 if k % 4 else -0.001)))
        for k in range(20):
            i += 1; L.append(json.dumps(tr(sid, "validate", "2026-10-%02d" % (7 + k), i, "M", 0.002)))
        out = m.run(L, REG, self.W, 100); d = json.loads(out[0]); s = json.loads(out[1])["summary"]
        self.assertTrue(d["screen1"]); self.assertTrue(d["screen2"]); self.assertEqual((s["tried"], s["settings_counted"], s["m_total"], d["m"]), (1, 1, 101, 101))
        self.assertEqual(d["search"]["pf_2c"], None); self.assertEqual(d["validate"]["pf_1c"], "inf"); self.assertTrue(d["bh_survivor"])
        self.assertEqual(s["screen1_pass"], 1); self.assertEqual(s["bh_survivors"], 1)
        # a signature that fails screen 2 (too few trades) keeps its rank slot and is no survivor
        out2 = m.run(L[:60], REG, self.W, 100); self.assertFalse(json.loads(out2[0])["screen2"]); self.assertFalse(json.loads(out2[0])["bh_survivor"])
    def test_bh_rank_slot(self):
        # three scored signatures; p of the first tiny, others large: m_total 1000 + 3
        sigs = [cand(market="index_perp", signal=s, clock="any_minute") for s in ("open_interest", "spread", "volume")]; L = []
        for si, sig in enumerate(sigs):
            sid = m.sig_id(sig); L.append(json.dumps(head(sig, 1.0, 35)))
            for k in range(120): L.append(json.dumps(tr(sid, "search", "2026-09-%02d" % (2 + k % 20), si * 1000 + k, "M", 0.01 + (0.0001 * k if si == 0 else 0.0) * (1 if k % 2 else -1) * (si == 0) + (0.0 if si == 0 else (0.01 if k % 2 else -0.0099)))))
        out = m.run(L, REG, self.W, 1000); s = json.loads(out[-1])["summary"]; self.assertEqual((s["tried"], s["m_total"]), (3, 1003))
    def test_unscored_lines(self):
        sig = cand(signal="price_change", clock="any_minute"); sid = m.sig_id(sig)
        out = m.run([json.dumps(head(sig, None, 35, data="held"))], REG, self.W, 100); d = json.loads(out[0])
        self.assertEqual((d["class"], d["class_ref"], d["scored"], d["data"], d["setting"], d["search"], d["screen1"], d["bh_survivor"], d["m"], d["heldout_read"], d["provisional"]), ("DECLINED", "P1", False, "held", None, None, False, False, 100, False, False))
        self.assertEqual(json.loads(out[1])["summary"]["tried"], 0)
    def test_binary_pf_fields(self):
        sig = cand(market="15m_crypto", signal="spread", clock="fixed_time_to_close", exit="hold_to_settle"); sid = m.sig_id(sig)
        h = head(sig, 1.0, 35, units="usd10", primary="1c")
        L = [json.dumps(h)] + [json.dumps(tr(sid, "search", "2026-09-02", i, "M", n1, n1=n1, n2=n1 - 0.1, gross=n1 + 0.5, cost=0.5)) for i, n1 in enumerate((1.0, -0.5, 0.5))]
        d = json.loads(m.run(L, REG, self.W, 100)[0]); self.assertAlmostEqual(d["search"]["pf_1c"], 1.5 / 0.5, 12); self.assertAlmostEqual(d["search"]["pf_2c"], (0.9 + 0.4) / 0.6, 12)
        self.assertAlmostEqual(d["search"]["gross_edge_c"], (1.5 + 0.0 + 1.0) / 3 * 10.0, 9); self.assertAlmostEqual(d["search"]["net_edge_c"], (1.0 - 0.5 + 0.5) / 3 * 10, 9)
    def test_missing_field_raises(self):
        sig = cand(); sid = m.sig_id(sig); t = tr(sid, "search", "2026-09-02", 1, "M", 0.1); del t["gross"]
        with self.assertRaises(ValueError): m.run([json.dumps(head(sig)), json.dumps(t)], REG, self.W, 1)
        t = tr(sid, "search", "2026-09-02", 1, "M", 0.1); t["net"] = None
        with self.assertRaises(ValueError): m.run([json.dumps(head(sig)), json.dumps(t)], REG, self.W, 1)
        with self.assertRaises(ValueError): m.run([json.dumps(head(cand(), units="usd10")), json.dumps(tr(sid, "search", "2026-09-02", 1, "M", 0.1))], REG, self.W, 1)   # binary without net_1c
    def test_option_b_version_not_scored(self):
        sig = cand(market="index_perp"); out = m.run([json.dumps(head(sig))], REG, self.W, 5, option_a=False); self.assertFalse(json.loads(out[0])["scored"])
        out = m.run([json.dumps(head(sig))], REG, self.W, 5, option_a=True); d = json.loads(out[0]); self.assertEqual((d["class"], d["scored"]), ("VERSION_NEW_MARKET", True))


class T3(unittest.TestCase):
    W = {"search": ["2026-09-02", "2026-10-06"], "validate": ["2026-10-07", "2026-10-26"]}
    SIG = cand(market="index_perp", signal="open_interest", clock="any_minute")
    def lines(self, search_days, per_day, val_days=(), val_per=0, cal=20, neg_every=7, sig=None):
        sig = sig or self.SIG; sid = m.sig_id(sig); L = [json.dumps(head(sig, 2.0, cal))]; i = 0
        for d in search_days:
            for k in range(per_day): i += 1; L.append(json.dumps(tr(sid, "search", d, i, "M", 0.01 if i % neg_every else -0.001)))
        for d in val_days:
            for k in range(val_per): i += 1; L.append(json.dumps(tr(sid, "validate", d, i, "M", 0.01 if i % neg_every else -0.001)))
        return L
    SD = ["2026-09-%02d" % d for d in range(2, 12)]            # 10 days, all in half 1 (before 09-29)
    def test_screen2_boundaries(self):
        # 10 days x 10 trades = 100 trades in SEARCH, half 2 empty -> PF half 2 is null: fails. so use days across both halves
        days = ["2026-09-%02d" % d for d in (2, 3, 4, 5, 6, 29, 30)] + ["2026-10-01", "2026-10-02", "2026-10-05"]        # 10 days, 5 in half 1 and 5 in half 2
        out = m.run(self.lines(days, 10), REG, self.W, 100); d = json.loads(out[0]); self.assertEqual((d["search"]["n"], d["search"]["trade_days"], d["screen1"], d["screen2"]), (100, 10, True, True))
        out = m.run(self.lines(days, 10)[:-1], REG, self.W, 100); d = json.loads(out[0]); self.assertEqual((d["search"]["n"], d["screen1"], d["screen2"]), (99, True, False))      # 99 trades
        L = self.lines(days[:9], 12); d = json.loads(m.run(L, REG, self.W, 100)[0]); self.assertEqual((d["search"]["n"], d["search"]["trade_days"], d["screen2"]), (108, 9, False))       # 9 days
    def test_screen2_needs_screen1(self):
        days = ["2026-09-%02d" % d for d in (2, 3, 4, 5, 6, 29, 30)] + ["2026-10-01", "2026-10-02", "2026-10-05"]
        L = self.lines(days, 5, ["2026-10-%02d" % d for d in range(7, 17)], 6, cal=35)      # SEARCH 50 trades / 35 days < 3 a day: screen 1 fails; 110 trades over 20 days: screen 2 conditions hold otherwise
        d = json.loads(m.run(L, REG, self.W, 100)[0]); self.assertEqual((d["screen1"], d["screen2"]), (False, False))
    def test_screen2_total_mean_strict(self):
        sig = self.SIG; sid = m.sig_id(sig); L = [json.dumps(head(sig, 2.0, 20))]; i = 0
        def add(w, d, net):
            nonlocal i; i += 1; L.append(json.dumps(tr(sid, w, d, i, "M", net)))
        for d in ["2026-09-%02d" % x for x in range(2, 12)]:                # half 1: 10 days, +1 and -1 on each day x 5 pairs: PF 1, sum 0
            for k in range(5): add("search", d, 1.0); add("search", d, -1.0)
        for d in ["2026-09-%02d" % x for x in range(29, 31)] + ["2026-10-%02d" % x for x in range(1, 4)]:     # half 2 in SEARCH: +1 x 12 each day
            for k in range(12): add("search", d, 1.0)
        for k in range(60): add("validate", "2026-10-10", -1.0)             # half 2 in VALIDATE: 60 losses: half 2 sum = 60 - 60 = 0, PF 1.0
        d = json.loads(m.run(L, REG, self.W, 100)[0]); self.assertTrue(d["screen1"]); self.assertEqual(d["screen2"], False)    # total mean exactly 0: strict
        L[-1] = json.dumps(tr(sid, "validate", "2026-10-10", i, "M", -0.9)); d = json.loads(m.run(L, REG, self.W, 100)[0]); self.assertEqual(d["screen2"], True)
    def test_null_threshold_not_scored(self):
        sig = cand(market="index_perp", signal="spread", clock="any_minute"); out = m.run([json.dumps(head(sig, None, 20, data="no_threshold"))], REG, self.W, 9)
        d = json.loads(out[0]); self.assertEqual((d["class"], d["scored"], d["m"]), ("NEW", False, 9)); self.assertEqual(json.loads(out[1])["summary"]["tried"], 0)
    def test_bh_equal_p_both_survive_and_failing_s2_keeps_slot(self):
        days = ["2026-09-%02d" % d for d in (2, 3, 4, 5, 6, 29, 30)] + ["2026-10-01", "2026-10-02", "2026-10-05"]
        a = cand(market="index_perp", signal="spread", clock="any_minute"); b = cand(market="index_perp", signal="book_depth_imbalance", clock="any_minute")
        L = self.lines(days, 10, sig=a, neg_every=7) + self.lines(days, 10, sig=b, neg_every=7)[:-1]       # b has 99 trades: fails screen 2
        out = m.run(L, REG, self.W, 0); s = json.loads(out[-1])["summary"]; ds = [json.loads(x) for x in out[:-1]]
        self.assertEqual((s["tried"], s["m_total"], s["screen2_pass"]), (2, 2, 1)); self.assertEqual(sum(1 for x in ds if x["bh_survivor"]), 1)
        self.assertEqual([x["bh_survivor"] for x in ds if x["screen2"] is False], [False])


class T4(unittest.TestCase):
    W = {"search": ["2026-09-02", "2026-10-06"], "validate": ["2026-10-07", "2026-10-26"]}
    def test_each_half_needs_pf_ok(self):
        sig = cand(market="index_perp", signal="open_interest", clock="any_minute"); sid = m.sig_id(sig); L = [json.dumps(head(sig, 2.0, 20))]; i = 0
        def add(d, net):
            nonlocal i; i += 1; L.append(json.dumps(tr(sid, "search", d, i, "M", net)))
        for d in ["2026-09-%02d" % x for x in range(2, 7)]:
            for k in range(10): add(d, 2.0); add(d, -0.5)                      # half 1: PF 4
        for d in ["2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02", "2026-10-05"]:
            for k in range(5): add(d, 1.0); add(d, -1.2)                       # half 2: PF 0.83 (< 1) but the total mean is positive
        d = json.loads(m.run(L, REG, self.W, 100)[0]); self.assertTrue(d["screen1"]); self.assertLess(d["search"]["pf_half2"], 1.0); self.assertGreater(d["search"]["pf_half1"], 1.0); self.assertFalse(d["screen2"])


class T5(unittest.TestCase):
    W = {"search": ["2026-09-02", "2026-10-06"], "validate": ["2026-10-07", "2026-10-26"]}
    def test_explicit_halves_and_new_fields(self):
        t = [{"day": d, "entry_end": 1, "market_id": "A", "net": 1.0} for d in ("2026-09-28", "2026-09-29", "2026-10-05")]
        a, b = m.halves_at(t, "2026-09-28", "2026-09-29"); self.assertEqual((len(a), len(b)), (1, 2))
        sig = cand(market="index_perp", signal="open_interest", clock="any_minute"); sid = m.sig_id(sig); L = [json.dumps(head(sig, 2.0, 20, half1_to="2026-09-05", half2_from="2026-09-06"))]; i = 0
        for d in ["2026-09-%02d" % x for x in range(2, 12)]:
            for k in range(12): i += 1; L.append(json.dumps(tr(sid, "search", d, i, "M", 1.0 if k % 2 else -0.5)))
        d = json.loads(m.run(L, REG, self.W, 100)[0])
        self.assertEqual((d["screen2_pf_half1"], d["screen2_pf_half2"]), (2.0, 2.0)); self.assertTrue(d["screen2"]); self.assertIn("p_union", d)
        L2 = [json.dumps(head(sig, 2.0, 20, half1_to="2026-09-30", half2_from="2026-10-01"))] + L[1:]; d2 = json.loads(m.run(L2, REG, self.W, 100)[0])
        self.assertIsNone(d2["screen2_pf_half2"]); self.assertFalse(d2["screen2"])              # half 2 empty: PF null, fails
    def test_header_requires_window_fields(self):
        sig = cand(); h = head(sig); del h["half1_to"]
        with self.assertRaises(ValueError): m.run([json.dumps(h)], REG, self.W, 1)
    def test_unverified_is_scored(self):
        sig = cand(market="weather", signal="spread", clock="time_of_day", exit="stop"); d = json.loads(m.run([json.dumps(head(sig))], REG, self.W, 5)[0])
        self.assertEqual((d["class"], d["class_ref"], d["scored"], d["provisional"]), ("UNVERIFIED_MATCH", "U1", True, True))
