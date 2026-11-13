#!/usr/bin/env python3
"""Compares the first build's printed records (Desk A, nc15_wheel_replay_records.py, a text file) with this second scorer's records file (--records), record by record:
status and result, then side, ask, limit, imb5 and, for a fillable signal, fill price, fee and cash; then the first build's per-series report lines against the same totals
taken from my records. usage: python3 -I nc15_wheel_compare.py <their printed lines .txt> <my records .csv>     It reads printed output only, never the first build's code."""
import sys, re, csv, collections
theirs = {}
for l in open(sys.argv[1]):
    g = re.match(r"^(KX\S+) status=(.+?) side=(\S+) ask=(\S+) limit=(\S+) imb5=(\S+) price=(\S+) fee=(\S+) cash=(\S+) result=(\S+)", l)
    if g: theirs[g.group(1)] = dict(zip(("status", "side", "ask", "limit", "imb5", "price", "fee", "cash", "result"), g.groups()[1:]))
mine = {r["ticker"]: r for r in csv.DictReader(open(sys.argv[2]))}
MAP = {"fillable, scored": ("fillable", "scored"), "fillable, void": ("fillable", "void"), "fillable, open": ("fillable", "pending"), "miss": ("miss", None), "not fill-checked": ("not fill-checked", None),
       "not in the cell": None, "no signal: no poll in the window": None, "no signal: a missing side of the book": None, "in the cell, ask outside 0.10 to 0.90": None, "no signal: no clock": None}
print("their status values:", collections.Counter((v["status"], v["result"]) for v in theirs.values()).most_common(12))
diff = collections.Counter(); ex = collections.defaultdict(list); same = 0; fig = 0; figbad = 0
for tk in sorted(set(theirs) | set(mine)):
    t = theirs.get(tk); m = mine.get(tk); ms = m["status"] if m else "(no record)"; ts = (t["status"] + ("/" + t["result"] if t["result"] != "-" else "")) if t else "(no line)"
    exp = MAP.get(ms) if m else None
    if t is None and (m is None or exp is None): same += 1; continue
    ok = t is not None and exp is not None and t["status"] == exp[0] and (exp[1] is None or t["result"] == exp[1])
    if not ok:
        diff[(ts, ms)] += 1
        if len(ex[(ts, ms)]) < 3: ex[(ts, ms)].append(tk)
        continue
    same += 1
    pairs = [("side", m["side"], t["side"], None), ("ask", m["ask"], t["ask"], 4), ("limit", m["limit"], t["limit"], 4), ("imb5", m["imb5"], t["imb5"], 4)]
    if exp[0] == "fillable": pairs += [("price", m["fill"], t["price"], 6), ("fee", m["fee"], t["fee"], 2)] + ([("cash", m["cash"], t["cash"], 4)] if exp[1] != "pending" else [])
    for name, a, b, dp in pairs:
        fig += 1
        good = (a == b) if dp is None else (b not in ("-", "") and a != "" and abs(float(a) - float(b)) <= 0.5 * 10 ** -dp + 1e-9)
        if not good:
            figbad += 1
            if figbad <= 8: print("FIGURE DIFFERS", tk, name, "mine", a, "theirs", b)
# per-series report lines of the first build against totals from my records
tot = totbad = 0
def pf(v):
    w = sum(x for x in v if x > 1e-9); l = -sum(x for x in v if x < -1e-9)
    return None if (w == 0 and l == 0) else (float("inf") if l == 0 else w / l)
for l in open(sys.argv[1]):
    g = re.match(r"^(KX\w+): signals (\d+) \| fillable (\d+) \| miss (\d+) \| not fill-checked (\d+) \| scored (\d+) \(void (\d+)\) pending (\d+) \| net \$(\S+) \| cash PF (\S+)", l)
    if not g: continue
    rs = [r for r in mine.values() if r["series"] == g.group(1)]; st = collections.Counter(r["status"] for r in rs)
    fl = st["fillable, scored"] + st["fillable, void"] + st["fillable, open"]; cash = [float(r["cash"]) for r in rs if r["status"] in ("fillable, scored", "fillable, void")]
    my = [fl + st["miss"] + st["not fill-checked"], fl, st["miss"], st["not fill-checked"], st["fillable, scored"] + st["fillable, void"], st["fillable, void"], st["fillable, open"]]
    th = [int(x) for x in g.groups()[1:8]]
    for name, a, b in zip(("signals", "fillable", "miss", "not fill-checked", "scored", "void", "pending"), my, th):
        tot += 1
        if a != b: totbad += 1; print("SERIES TOTAL DIFFERS", g.group(1), name, "mine", a, "theirs", b)
    p = pf(cash)
    for name, a, b in (("net", "%.2f" % sum(cash), g.group(9)), ("cash PF", "n/a" if p is None else ("inf" if p == float("inf") else "%.2f" % p), g.group(10))):
        tot += 1
        if a != b and not (name == "net" and abs(float(a) - float(b)) < 0.005 + 1e-9): totbad += 1; print("SERIES TOTAL DIFFERS", g.group(1), name, "mine", a, "theirs", b)
print("per-series report figures compared: %d, differ: %d" % (tot, totbad))
print("records the same in status: %d; status differs: %d; figures compared on matching records: %d, differ: %d" % (same, sum(diff.values()), fig, figbad))
for k, v in diff.most_common(): print("  theirs %-28s mine %-40s %5d   e.g. %s" % (k[0], k[1], v, ", ".join(ex[k])))
