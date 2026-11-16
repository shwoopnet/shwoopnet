#!/usr/bin/env python3
"""NBAREBLADDER wrapper check (synthetic): the wrapper retargets the audited plugin and the audited hand case still holds under the new names."""
import gzip, json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbaladder_reb as R
import test_nbaladder as T

N = R.N


class Wrap(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(N.SERIES, ("KXNBAREB",))
        self.assertEqual(N.LIST_JOB, "KXNBAREB_LISTS_A")
        self.assertEqual(N.N_RULES, 624)

    def test_hand_under_reb_names(self):
        root, O, D, Tk = T.fixture()
        base = os.path.join(root, "pull")
        os.rename(os.path.join(base, "KXNBAPTS_LISTS_A"), os.path.join(base, "KXNBAREB_LISTS_A"))
        os.rename(os.path.join(base, "NBALADDER_CANDLES_P1"), os.path.join(base, "NBAREB_CANDLES_P1"))
        # rewrite series and list id in the stored fixture
        for d, _, fs in os.walk(base):
            for f in fs:
                p = os.path.join(d, f)
                if f.endswith(".json.gz"):
                    s = gzip.open(p, "rt").read().replace("KXNBAPTS", "KXNBAREB")
                    gzip.open(p, "wt").write(s)
                elif f == "manifest.json":
                    s = open(p).read().replace("dev_KXNBAPTS", "dev_KXNBAREB")
                    open(p, "w").write(s)
        dec, counts, g = N.decisions(root)
        self.assertEqual(counts["games"], 1)
        self.assertEqual(len([x for x in dec if x["D_off"] == 3600]), 4)


if __name__ == "__main__":
    unittest.main()
