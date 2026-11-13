#!/usr/bin/env python3
"""Compares the DEPTH1 wrapper's printed lines (a text file sent by Desk A) with this second build's saved output (the .json written by `depth1_second.py read`, or by a
fixture run), figure by figure: for each of the 20 tries n, PF, the three block PFs and counts, the halves, net, stress PF, accuracy, mean ask, the corrected z, the control
p and pass or fail, and for gold the without-held count and PF; then the control's 99th percentile and median, the noise lines and the counts.
usage: python3 -I depth1_compare.py <my output .json> <the wrapper's printed lines .txt>
It opens no data file and never reads the wrapper's code: it only formats my saved figures with depth1_second.lines and parses the other build's printed text."""
import sys, re, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import depth1_second as D
out = json.load(open(sys.argv[1])); mine = D.lines(out); theirs = open(sys.argv[2]).read().split("\n")
def parse(lines):
    r = {}; m = None
    for l in lines:
        if l.startswith("-- "): m = l.split()[1].rstrip(":"); continue
        g = re.match(r"^(?:\[closed family\] )?(f\d+_\w+)\s+n\s+(\d+) PF (\S+) blocks (\S+) \(n (\d+)\) / (\S+) \(n (\d+)\) / (\S+) \(n (\d+)\) halves (\S+) / (\S+) net (\S+)c stress PF (\S+) acc (\S+) vs mean ask (\S+) z (\S+) control p\(best of 20\) (\S+) (PASS|fail).*without windows L1 / OICORE holds: n (\d+) PF ([0-9.infa/]+)", l)
        if g and m and (m, g.group(1)) not in r: r[(m, g.group(1))] = [g.group(i) for i in range(2, 21)]
    return r
norm = lambda x: x.lstrip("+")
a, b = parse(mine), parse(theirs); names = ["n","PF","PF A","n A","PF B","n B","PF C","n C","half 1","half 2","net c","stress PF","acc","mean ask","z corrected","control p","control","not-held n","not-held PF"]
tot = bad = 0
for k in sorted(b):
    idx = range(19) if k[0] == "KXGOLD15M" else range(17)          # Bitcoin's without-held figures: the fixture run stubs the mark, mine says unknown
    same = lambda x, y: norm(x) == norm(y) or (x == "n/a" and float(norm(y)) == 0.0)          # an empty set prints n/a here and 0.00 there
    d = [(names[i], a[k][i], b[k][i]) for i in idx if not same(a[k][i], b[k][i])]; tot += len(idx); bad += len(d)
    if d: print(" ".join(k), "DIFFER", d)
print("per-try figures compared: %d, differ: %d (tries %d)" % (tot, bad, len(b)))
# Z BESIDE and ZERO RULE blocks
allt = dict(out["tries"]); allt.update(out["CLOSED-FAMILY FEATURES, REPORTED SEPARATELY"]); zb = zr = 0; nb = nr = 0
for i, l in enumerate(theirs):
    if l.startswith("Z BESIDE") and zb == 0:
        for row in theirs[i+1:i+3]:
            m = row.split(":")[0].strip()
            for part in row.split(":", 1)[1].split(";"):
                g = re.match(r"\s*(f\d+) (\S+) / (\S+)", part); v = [x for k2, x in allt.items() if k2.startswith(m + " " + g.group(1) + "_")][0]; nb += 2
                if norm("%.2f" % v["z_date_clustered"]) != norm(g.group(2)) and "%.2f" % abs(v["z_date_clustered"]) != norm(g.group(2)).lstrip("-"): zb += 1; print("z corrected differs", m, part, v["z_date_clustered"])
                if "%.2f" % abs(v["z_uncorrected_beside"]) != norm(g.group(3)).lstrip("-"): zb += 1; print("z uncorrected differs", m, part, v["z_uncorrected_beside"])
    if l.startswith("ZERO RULE") and nr == 0:
        for row in theirs[i+1:i+3]:
            m = row.split(":")[0].strip()
            for g in re.finditer(r"(f\d+)\w*\s+(\d+)", row.split(":", 1)[1]):
                v = [x for k2, x in allt.items() if k2.startswith(m + " " + g.group(1) + "_")][0]; nr += 1
                if v["scored_windows_with_a_raw_feature_within_1e-12_of_zero_but_not_zero"] != int(g.group(2)): zr += 1; print("zero-rule count differs", m, g.group(0), v["scored_windows_with_a_raw_feature_within_1e-12_of_zero_but_not_zero"])
print("Z BESIDE figures compared %d, differ %d | ZERO RULE counts compared %d, differ %d" % (nb, zb, nr, zr))
c = out["shuffled_book_control"]; hdr = [l for l in theirs if "shuffled-book control" in l][0]
print("control mine: 99th percentile %.4fc, median %.4fc | theirs: %s" % (100 * c["p99_of_best_of_20_mean_net"], 100 * c["median_of_best_of_20"], hdr[hdr.index("99th"):][:60]))
d = out["no_label_description"]
for m in D.MARKETS:
    my = "; ".join("%s %.1f%% of %d" % (f, 100 * v["share_sign_changes_within_two_polls"], v["looks"]) for f, v in sorted(d[m]["noise"].items()) if v["looks"])
    th = [l for l in theirs if l.strip().startswith(m + ":") and "median fill delay" in l][0].split("|")[0].split(":", 1)[1].strip()
    print(m, "noise line:", "same" if my == th else "DIFFERS\n   mine   %s\n   theirs %s" % (my, th))
print("scored", out["windows_with_a_decision_poll"], "| amendment 1 count", out["AMENDMENT 1 COUNT"], "|", out["verdict"][:60])
print([l for l in theirs if l.startswith("usable windows")][0][:300]); print([l for l in theirs if l.startswith("AMENDMENT 1 COUNT")][0][:200])
