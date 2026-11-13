#!/usr/bin/env python3
"""Compares the first build's printed block lines (Desk A, wheel_block_reader.py, a text file) with this second scorer's printed lines (nc15_wheel_second.py), block by block:
verdict, n, first and last ticker, wins, losses, voids, net, profit factor, both halves, days, span, top day's share, the set of fail reasons, the confirmation and its
profit factor; then each place's state. usage: python3 -I nc15_wheel_block_compare.py <their block lines .txt> <my output .txt>     Printed output only; no code is read.
Print conventions that differ and are mapped here: the first build's waiting state counts the pending signal in block_n (mine counts the signals before it)."""
import sys, re, ast
B = re.compile(r"^(KX\w+) BLOCK (\d+): (CLEARED|FAILED) \| n (\d+) \((\S+) to (\S+)\) wins (\d+) losses (\d+) voids (\d+) \| net (\S+) PF (\S+) halves (\S+) / (\S+) \| days (\d+) span (\S+) top day (\S+?)(?: \| fails: (.*?))?(?: \| confirmation: (.*?))?(?: \| whole cents.*)?(?: \| exact tenths.*)?$")
E = re.compile(r"^(KX\w+) BLOCK (\d+): EXPIRED \(.*?\) \| n (\d+) span (\S+) days \| (\S+) to (\S+)")
def parse(path):
    blocks = {}; state = {}
    for l in open(path):
        l = l.rstrip("\n")
        g = B.match(l)
        if g:
            conf = (g.group(18) or "").strip().lower(); conf = re.sub(r"\s+", " ", conf)
            if conf.startswith("in progress") or conf.startswith("waits"): conf = ""          # the place's state line carries these
            conf = re.sub(r"^(confirmation )?expired.*", "confirmation expired", conf)
            blocks[(g.group(1), int(g.group(2)))] = ("read", g.group(3)) + g.groups()[3:16] + (frozenset(x.strip() for x in (g.group(17) or "").split(";") if x.strip()), conf)
            continue
        g = E.match(l)
        if g: blocks[(g.group(1), int(g.group(2)))] = ("expired",) + g.groups()[2:]; continue
        g = re.match(r"^(KX\w+) STATE: (.*)$", l)
        if g:
            t = g.group(2)
            if t.startswith("{"):
                d = ast.literal_eval(t)
                if d.get("qualified"): state[g.group(1)] = ("qualified",)
                elif "confirmation_in_progress" in d: state[g.group(1)] = ("confirmation in progress", d["confirmation_in_progress"])
                elif d.get("waiting") and "confirmation_n" in d: state[g.group(1)] = ("confirmation waits",)
                elif d.get("waiting"): state[g.group(1)] = ("waits", d.get("block_n", 0) - 1) if "block_n" in d else ("waits", t)
                elif "block_in_progress" in d: state[g.group(1)] = ("in progress", d["block_in_progress"], d.get("days"), d.get("wins"), d.get("losses"))
                else: state[g.group(1)] = ("other", t)
            else:
                m = re.match(r"block in progress: (\d+) signals, (\d+) days, (\d+) wins, (\d+) losses", t)
                if t.startswith("QUALIFIED"): state[g.group(1)] = ("qualified",)
                elif t.startswith("WAITS"): state[g.group(1)] = ("waits", int(re.search(r"block holds (\d+) ", t).group(1)))
                elif t.startswith("cleared block, confirmation waits"): state[g.group(1)] = ("confirmation waits",)
                elif t.startswith("cleared block, confirmation in progress"): state[g.group(1)] = ("confirmation in progress", int(re.search(r"(\d+) of 30", t).group(1)))
                elif m: state[g.group(1)] = ("in progress",) + tuple(int(x) for x in m.groups())
                else: state[g.group(1)] = ("other", t.split(" (fillable")[0])
                continue
    return blocks, state
(tb, ts), (mb, ms) = parse(sys.argv[1]), parse(sys.argv[2]); bad = 0; fig = 0
for k in sorted(set(tb) | set(mb)):
    a, b = tb.get(k), mb.get(k)
    if a is None or b is None or a[0] != b[0] or len(a) != len(b): bad += 1; print("BLOCK DIFFERS", k, "theirs", a, "mine", b); continue
    for i, (x, y) in enumerate(zip(a, b)):
        fig += 1
        if x != y: bad += 1; print("BLOCK DIFFERS", k, "item", i, "theirs", x, "mine", y)
sb = 0
for p in sorted(set(ts) | set(ms)):
    if ts.get(p) != ms.get(p): sb += 1; print("STATE DIFFERS", p, "theirs", ts.get(p), "mine", ms.get(p))
print("%s: blocks theirs %d, mine %d; block figures compared %d, differ %d; place states compared %d, differ %d" % (sys.argv[1].split("/")[-1], len(tb), len(mb), fig, bad, len(set(ts) | set(ms)), sb))
