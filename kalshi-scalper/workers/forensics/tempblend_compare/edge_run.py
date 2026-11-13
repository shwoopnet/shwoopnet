#!/usr/bin/env python3
"""Run both TEMPBLEND builds on the third (edge) set and compare each row's decision with the hand expectation (edge_hand_expected.json, committed before any run) and with the other build.
usage: python3 -I edge_run.py <edge dir from edge_rows.py> <build 1 dir (c/)> <build 2 dir (m/)>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import map_and_compare as MC

edge, cdir, mdir = sys.argv[1:4]
C = MC.load(os.path.join(cdir, "tempblend_score.py"), "tb1"); M = MC.load(os.path.join(mdir, "tempblend2.py"), "tb2")
rows_c = json.load(open(os.path.join(edge, "edge_rows_build1_layout.json"))); watched = json.load(open(os.path.join(edge, "edge_watched.json")))
rows_m = [json.loads(l) for l in open(os.path.join(edge, "edge_rows_build2_layout.jsonl")) if l.strip()]
hand = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_hand_expected.json")))["rows"]
o1 = C.score(rows_c, watched); o2 = M.run(os.path.join(edge, "edge_rows_build2_layout.jsonl"))
json.dump(o1, open(os.path.join(edge, "edge_build1_output.json"), "w"), indent=1, sort_keys=True); json.dump(o2, open(os.path.join(edge, "edge_build2_output.json"), "w"), indent=1, sort_keys=True)
def one(b, why, kind):
    if b is None: return {"expect": "skip", "class": MC.cls(why)}
    return {"expect": "bet", "side": b["side"], "K": b["K"], "ask": b["ask"], "fee": b["fee"] if kind == 1 else None, "pnl": b["pnl"], "void": b["void"], "member": b["member"], "day2": (b["calib"] == "day2_on") if kind == 1 else b["day2"]}
bad = {1: [], 2: [], "x": []}; n = 0
for rc, rm in zip(rows_c, rows_m):
    rid = rc["city"]; e = hand[rid]
    b1, w1 = C.decide(rc, watched); s2, b2 = M.decide(rm)
    S2 = rm["S"]; outside = not ((M.iso(M.DEV[0]) <= S2 < M.iso(M.DEV[1])) or (M.iso(M.HELD[0]) <= S2 < M.iso(M.HELD[1])))
    r1 = one(b1, w1, 1); r2 = {"expect": "skip", "class": "outside windows"} if outside else one(b2, s2 if b2 is None else None, 2)
    for tag, r in ((1, r1), (2, r2)):
        n += 1
        if r["expect"] != e["expect"] or (e["expect"] == "skip" and r["class"] != e["class"]): bad[tag].append("%s: hand %s, build %s %s" % (rid, e.get("class", "bet"), tag, r.get("class", "bet"))); continue
        if e["expect"] == "bet":
            for f in ("side", "K", "ask", "pnl", "void", "member", "day2"):
                x, y = e[f], r[f]
                if (abs(x - y) > 1e-9 if isinstance(x, float) or isinstance(y, float) else x != y) and not (isinstance(x, bool) or isinstance(y, bool)) or (isinstance(x, bool) and x != y): bad[tag].append("%s: field %s hand %r, build %s %r" % (rid, f, x, tag, y))
            if r1["expect"] == "bet" and tag == 1 and abs(r1["fee"] - e["fee"]) > 1e-12: bad[1].append("%s: fee hand %r, build 1 %r" % (rid, e["fee"], r1["fee"]))
    if r1 != r2 and not (r1.get("expect") == "bet" and r2.get("expect") == "bet" and all(abs(r1[f] - r2[f]) < 1e-9 if isinstance(r1[f], float) else r1[f] == r2[f] for f in ("side", "K", "ask", "pnl", "void", "member", "day2"))): bad["x"].append("%s: build 1 %s | build 2 %s" % (rid, r1, r2))
print("rows %d; checked against the hand file: build 1 %d difference(s), build 2 %d difference(s); build 1 against build 2: %d difference(s)" % (len(rows_c), len(bad[1]), len(bad[2]), len(bad["x"])))
for k in (1, 2, "x"):
    for line in bad[k]: print("  [%s] %s" % (k if k != "x" else "1 vs 2", line))
print("build 1 skips:", o1["skips"]); print("build 2 statuses:", o2["statuses"], "outside windows:", o2["outside_windows"])
