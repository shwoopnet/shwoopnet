"""Checks tempblend2.py against expected_by_hand.json on three invented sets: (1) rows_madeup.jsonl in dev and held modes, (2) rows_pass.jsonl (a PASS),
(3) the refusals (duplicate row, an unknown result, the held-out read before 2026-12-10 and with the read-once marker present). Exit 1 on any mismatch."""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tempblend2 as T
E = json.load(open(os.path.join(HERE, "expected_by_hand.json")))
bad = []
def close(a, b):
    return abs(a - b) <= 1e-6 if isinstance(b, float) else a == b
def cmp(tag, got, want):
    for k, v in want.items():
        if isinstance(v, dict):
            cmp(tag + "." + k, got[k], v)
        elif k != "note" and not close(got[k], v):
            bad.append((tag, k, got[k], v))
AFTER = T.iso("2026-12-10T00:00:00Z") + 1
def held(path):
    m = os.path.join(tempfile.mkdtemp(), "HELD_READ_DONE")
    return T.run("held", os.path.join(HERE, path), now=AFTER, marker=m), m
# set 1, dev
o = T.run("dev", os.path.join(HERE, "rows_madeup.jsonl"))
dec = {d["city"]: d for d in o["decisions"]}
for c, x in E["per_row"].items():
    if x[0] == "outside windows" or c in ("C12", "C13"):
        bad += [("leaked", c)] if c in dec else []
        continue
    d = dec[c]
    if d["status"] != x[0]:
        bad.append((c, d["status"])); continue
    if x[0] == "bet":
        b = d["bet"]
        if (b["side"], b["K"]) != (x[1], x[2]) or abs(b["pnl"] - x[3]) > 1e-9 or (len(x) > 4) != b["void"]:
            bad.append((c, b))
cmp("dev", o["development"], E["development"])
cmp("devmode", o, E["dev_mode"])
# set 1, held
o, m = held("rows_madeup.jsonl")
cmp("held1", o["held_out"], E["held_mode_set1"])
for c in ("C12", "C13"):
    d = {x["city"]: x for x in o["decisions"]}[c]
    if not d["bet"] or abs(d["bet"]["pnl"] - E["per_row"][c][3]) > 1e-9:
        bad.append(("held row", c))
# set 2, PASS
o, m = held("rows_pass.jsonl")
cmp("pass.dev", o["development"], E["set2_pass"]["development"])
cmp("pass.held", o["held_out"], E["set2_pass"]["held_out"])
# set 3, refusals
def refused(fn, words):
    try:
        fn()
    except T.Stop as e:
        if words not in str(e):
            bad.append(("refusal text", words, str(e)))
        return
    bad.append(("not refused", words))
refused(lambda: T.run("dev", os.path.join(HERE, "rows_dup.jsonl")), E["set3_refusals"]["rows_dup.jsonl"])
refused(lambda: T.run("dev", os.path.join(HERE, "rows_badresult.jsonl")), E["set3_refusals"]["rows_badresult.jsonl"])
refused(lambda: T.run("held", os.path.join(HERE, "rows_madeup.jsonl"), now=T.iso("2026-12-09T23:59:59Z"), marker=os.path.join(tempfile.mkdtemp(), "M")), E["set3_refusals"]["held before 2026-12-10"])
o, m = held("rows_pass.jsonl")
refused(lambda: T.run("held", os.path.join(HERE, "rows_pass.jsonl"), now=AFTER, marker=m), E["set3_refusals"]["held with marker present"])
# F1: an unrounded PF just under 1.5 must not pass (1.49996 shown as 1.49996, tested raw)
if not (T.pf_raw([1.49996, -1.0]) < 1.5):
    bad.append(("F1",))
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
