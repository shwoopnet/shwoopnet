"""Synthetic leak tests for Refinement's NOSIDE1 scorer (Forensics, 2026-11-12). No real data: made-up events and hourly candles in the scorer's own input shape.
usage: python3 -I leak_noside1.py <path to refine_tools>
"""
import sys, os, json, random, tempfile, io, contextlib
sys.path.insert(0, sys.argv[1])
import noside1_score as N
res = []
def check(name, ok, detail=""):
    res.append(ok); print("%-92s %s %s" % (name, "PASS" if ok else "FAIL", detail))
rng = random.Random(4); T0 = 1_750_000_000
def build(flip=False, after=None, at_look=None, n=90):
    rows, TH = [], {}
    for i in range(n):
        e = "KXAPRPOTUS-E%03d" % i; ct = T0 + 86400 * 7 * i; TH[e] = 0 if i < 30 else (1 if i < 60 else 2)
        for j, bid in enumerate((0.12, 0.20, 0.45, 0.82)):
            t = "%s-T%d" % (e, j); look = ct - 86400
            c = [[look - 3600 * h, "%.4f" % (bid + 0.02), "%.4f" % (bid + 0.001 * h), None, "5"] for h in (30, 5, 2, 1)]
            if at_look is not None: c[-1][2] = "%.4f" % (bid + at_look)
            c += [[look + 3600 * h, "%.4f" % (after if after is not None else bid + 0.3), "%.4f" % ((after - 0.02) if after is not None else bid + 0.28), None, "5"] for h in (1, 6, 20)]
            r = "yes" if (i * 7 + j) % 3 == 0 else "no"
            if flip: r = "no" if r == "yes" else "yes"
            rows.append({"t": t, "e": e, "s": "KXAPRPOTUS", "ct": ct, "res": r, "c": c})
    return rows, TH
def obs(rows, TH):
    d = tempfile.mkdtemp(); p = os.path.join(d, "cand_no.jsonl"); open(p, "w").write("\n".join(json.dumps(r) for r in rows) + "\n")
    ob = N.load(p, TH); return {k: (v["t"], round(v["p"], 6), v["qt"]) for k, v in ob.items()}, {k: v["win"] for k, v in ob.items()}
rows, TH = build(); o0, w0 = obs(rows, TH)
o1, w1 = obs(build(flip=True)[0], TH)
check("NOSIDE1: results flipped -> same observations, markets and prices", o1 == o0, "n %d" % len(o0))
check("NOSIDE1: results flipped -> wins do change (control)", w1 != w0)
check("NOSIDE1: every candle AFTER the look changed -> same observations", obs(build(after=0.95)[0], TH)[0] == o0)
check("NOSIDE1: the candle AT the look changed -> observations change (control)", obs(build(at_look=0.05)[0], TH)[0] != o0)
check("NOSIDE1: held-out events (third 2) and unlisted events never load", all(TH[e] < 2 for (e, a) in o0) and obs(rows, {e: t for e, t in TH.items() if t == 0})[0].keys() <= {k for k in o0 if TH[k[0]] == 0})
k0 = next(iter(o0)); r0 = [r for r in rows if r["t"] == o0[k0][0]][0]; look = r0["ct"] - 86400
bid_at = [float(c[2]) for c in sorted(r0["c"]) if c[0] <= look][-1]
check("NOSIDE1: price paid is 1 minus the YES bid of the last candle at or before the look (the NO ask), never a mid or a later candle", abs(o0[k0][1] - (1 - bid_at)) < 1e-9 and o0[k0][2] <= look)
check("NOSIDE1: one observation per event per arm", len(o0) == len({k for k in o0}))
# the read-once marker
d = tempfile.mkdtemp(); open(os.path.join(d, "cand_no.jsonl"), "w").write("\n".join(json.dumps(r) for r in rows) + "\n")
cuts = os.path.join(d, "cuts.json"); json.dump({"series": {"KXAPRPOTUS": {"events": [[e, t] for e, t in TH.items()]}}}, open(cuts, "w"))
def run():
    b = io.StringIO()
    with contextlib.redirect_stdout(b): N.main([d, "--cuts", cuts])
    return b.getvalue()
a = run(); check("NOSIDE1: without the pull-complete marker nothing is scored", a.strip() == "pull incomplete")
open(os.path.join(d, N.MARKER), "w").write(str(N.REQUESTS)); b1 = run(); b2 = run()
check("NOSIDE1: scored once, then refuses a second run", "VERDICT" in b1 and b2.strip() == "already read")
print("\n%d checks, %d FAIL" % (len(res), sum(1 for x in res if not x)))
