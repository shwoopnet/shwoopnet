"""Standard BH over all 190 p-values (the plan's wording: BH at 5% over m = 190 on the one-sided day-clustered p of the 1c cash, every rule ranked, no-evidence rules included), applied to the held-out print's own p values. No new data: the print's numbers were confirmed 1e-9 by two builds; only the BH flag differs from the run script's holds-only BH. Prints a summary and writes the corrected rows.
  python3 -I engine1_heldout_bh_fix.py <print.json> <out.json>"""
import sys, json, collections
def bh_all(ps, m=190, alpha=0.05):
    order = sorted(range(len(ps)), key=lambda i: (ps[i], i)); k = 0
    for r, i in enumerate(order, 1):
        if ps[i] <= alpha * r / m: k = r
    return {order[j] for j in range(k)}, k
def main(src, out):
    d = json.load(open(src)); rows = d["rows"]; assert len(rows) == 190
    keep, k = bh_all([r["p"] for r in rows])
    for i, r in enumerate(rows):
        r["bh_all190"] = i in keep
        r["verdict_bh_all190"] = r["verdict"] + (", BH survivor at 5% over 190 (all ranked)" if i in keep and r["holds_bar"] else (", BH-rank survivor but no evidence at n = %d" % r["n"] if i in keep and r["verdict"].startswith("no evidence") else (", BH-rank survivor but does not hold" if i in keep else "")))
    d["bh_survivors_all190"] = k; d["bh_note"] = "standard BH ranking every one of the 190 p-values (the plan's wording); the run script's own bh flag ranked holds rules only and is superseded"
    json.dump(d, open(out, "w"), indent=1)
    c = collections.Counter(r["verdict"].split(" at ")[0] for r in rows)
    print("verdicts", dict(c), "BH survivors (all 190 ranked)", k, "of which holds", sum(1 for r in rows if r["bh_all190"] and r["holds_bar"]))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])
