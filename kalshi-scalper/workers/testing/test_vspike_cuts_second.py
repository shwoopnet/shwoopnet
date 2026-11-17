import unittest, calendar, time
import vspike_cuts_second as v

def ts(s): return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
def cand(e, vols, bid=0.4, ask=0.5):
    """vols = volumes at e-300 ... e (six values; None = null; missing key if the entry is the string 'missing')"""
    d = {}
    for k, x in zip(range(5, -1, -1), vols):
        if x == "missing": continue
        d[e - 60 * k] = (e - 60 * k, bid, ask, 0.5, x, 1)
    return d

class T(unittest.TestCase):
    def test_cuts(self):
        self.assertEqual(v.cuts([1, 2, 3, 4, 5, 6, 7]), (3, 5)); self.assertEqual(v.cuts([2.5]), (2.5, 2.5)); self.assertEqual(v.cuts([9, 4]), (4, 9))
        self.assertEqual(v.cuts([3, 1, 2]), (1, 2)); self.assertEqual(v.cuts([1, 2, 3, 4]), (2, 3)); self.assertEqual(v.cuts([1, 2, 3, 4, 5, 6]), (2, 4)); self.assertIsNone(v.cuts([]))
    def test_ratio(self):
        e = 10000
        self.assertAlmostEqual(v.vspike(cand(e, [10, 20, 30, 40, 50, 90]), e), 3.0, 12); self.assertAlmostEqual(v.vspike(cand(e, [10, 20, 30, 0, 50, 90]), e), 90 / 22, 12)
        self.assertIsNone(v.vspike(cand(e, [0, 0, 0, 0, 0, 90]), e)); self.assertIsNone(v.vspike(cand(e, [10, None, 30, 40, 50, 90]), e)); self.assertIsNone(v.vspike(cand(e, ["missing", 20, 30, 40, 50, 90]), e))
        self.assertEqual(v.vspike(cand(e, [10, 20, 30, 40, 50, 0]), e), 0.0)           # a zero volume at e is a value
    def test_quote(self):
        e = 10000
        for b, a in ((0.4, 0.4), (0.0, 0.5), (0.4, 1.0), (0.5, 0.4)): self.assertIsNone(v.vspike(cand(e, [10, 20, 30, 40, 50, 90], b, a), e))
        d = cand(e, [10, 20, 30, 40, 50, 90]); d[e - 120] = (e - 120, 0.9, 0.1, 0.5, 40, 1); self.assertAlmostEqual(v.vspike(d, e), 3.0, 12)       # earlier candles are not quote-tested
    def test_search_phase_and_short(self):
        self.assertEqual(v.short("KXBNB15M"), "BNB"); self.assertTrue(v.is_search("KXBNB15M", ts("2026-09-03T23:59:59Z"))); self.assertFalse(v.is_search("KXBNB15M", ts("2026-09-04T00:00:00Z")))
        self.assertTrue(v.is_search("KXCOPPER15M", ts("2026-09-13T12:00:00Z"))); self.assertFalse(v.is_search("KXCOPPER15M", ts("2026-09-14T00:00:00Z")))
    def test_table_hand5(self):
        C = ts("2026-09-01T12:00:00Z"); e = C - 420; mk = [("M", C, "KXBNB15M"), ("X", C, "KXFOO15M")]
        t = v.table(mk, {"M": cand(e, [50, 40, 30, 20, 10, 90]), "X": cand(e, [50, 40, 30, 20, 10, 90])})
        self.assertEqual(list(t), ["KXBNB15M"]); self.assertEqual(t["KXBNB15M"]["420"], {"c1": 3.0, "c2": 3.0})
        self.assertTrue(all(t["KXBNB15M"][str(b)]["c1"] is None for b in v.BUCKETS if b != 420))
    def test_validate_market_excluded(self):
        C = ts("2026-09-04T12:00:00Z"); e = C - 420
        t = v.table([("M", C, "KXBNB15M")], {"M": cand(e, [50, 40, 30, 20, 10, 90])}); self.assertEqual(t["KXBNB15M"]["420"], {"c1": None, "c2": None})
    def test_all_buckets_and_sorted_cut(self):
        C = ts("2026-09-01T12:00:00Z"); mk = []; cd = {}
        for i, vol in enumerate([6, 2, 5, 1, 4, 3, 7]):
            tk = "M%d" % i; mk.append((tk, C + i, "KXETH15M")); e = C + i - 180; cd[tk] = cand(e, [10, 10, 10, 10, 10, 10 * vol])
        t = v.table(mk, cd); self.assertEqual(t["KXETH15M"]["180"], {"c1": 3.0, "c2": 5.0}); self.assertEqual(len(t["KXETH15M"]), 13)
