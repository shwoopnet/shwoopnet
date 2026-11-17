"""Pooled BH over the same held-out window (Auditor B's multiplicity line): the standard step-up at 5% over m = the total number of rules in the reads given, every rule ranked, on the p values of the print files named (the 190's corrected print, batch B's, batch C's). Prints counts only; it changes no verdict of any read.
  python3 -I engine1_heldout_pooled_bh.py <print.json> [<print.json> ...]"""
import sys, json
def main(paths):
    ps = []; src = []
    for p in paths:
        for r in json.load(open(p))["rows"]: ps.append(r["p"]); src.append((p, bool(r.get("holds_bar"))))
    m = len(ps); order = sorted(range(m), key=lambda i: (ps[i], i)); k = 0
    for rank, i in enumerate(order, 1):
        if ps[i] <= 0.05 * rank / m: k = rank
    keep = set(order[:k])
    print("pooled BH over m = %d: %d survivors (%d with holds)" % (m, k, sum(1 for i in keep if src[i][1])))
    for p in paths: print("  ", p, "survivors", sum(1 for i in keep if src[i][0] == p))
if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(sys.argv[1:])
