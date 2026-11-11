"""BASERATES1 step 1: build eo_list.csv and plaw_list.csv from GovInfo bulk files already downloaded (offline here)."""
import re, glob, csv, json, datetime as dt, sys
X = "/tmp/claude-0/x"
M = {m: i for i, m in enumerate("January February March April May June July August September October November December".split(), 1)}
eo = {}
files = glob.glob(X + "/fr/*.xml") + glob.glob(X + "/frz/*/*.xml") + glob.glob(X + "/frz2/out/*/*.xml")
rx = re.compile(r"<EXECORDR>Executive Order (\d+) of ([A-Z][a-z]+) (\d+), (\d{4})")
for f in files:
    for m in rx.finditer(open(f, encoding="utf8", errors="ignore").read()):
        eo[int(m[1])] = dt.date(int(m[4]), M[m[2]], int(m[3])).isoformat()
old = json.load(open(X + "/eo.json"))
for k, v in old.items(): eo.setdefault(int(k), v)
with open("eo_list.csv", "w") as o:
    o.write("number,signed\n")
    for k in sorted(eo): o.write(f"{k},{eo[k]}\n")
pl = []
for c, d in ((115, "plaw115"), (116, "plaw116"), (119, "plaw")):
    for f in glob.glob(f"{X}/{d}/PLAW-*.xml"):
        t = open(f, encoding="utf8", errors="ignore").read(14000)
        m = re.search(r"<approvedDate>(\d{4}-\d\d-\d\d)<", t)
        n = re.search(r"PLAW-(\d+)publ(\d+)", f)
        if m and (c != 119 or n[1] == "119"): pl.append((int(n[1]), int(n[2]), m[1]))
pl = sorted(set(pl))
with open("plaw_list.csv", "w") as o:
    o.write("congress,law,approved\n")
    for a in pl: o.write("%d,%d,%s\n" % a)
print(len(eo), min(eo.values()), max(eo.values()), len(pl))
