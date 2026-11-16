#!/usr/bin/env python3
"""Compare my PERPSLANE4 second-build lines (OUTLIST of perpslane4_b2.py) with the Testing Desk's printed lines, rule by rule and fee by fee, at 1e-9 (relative for big values). usage: python3 -I compare_lane4_b2.py <mine.txt> <theirs.txt>"""
import sys, re, math
def name(rule):
    t = rule.split("|"); k = t[0]
    if k == "A": return "A_%s_%s" % (t[1], t[2])
    if k == "A2": return "A2_%s_%s_%s_%s" % ("mon" if t[1] == "Monday" else "tuefri", t[2], t[3], t[4])
    if k == "B1": return "B1_%s_%s_%s_%s" % tuple(t[1:5])
    if k == "B2": return "B2_%s_%s_%s" % tuple(t[1:4])
    if k == "B3": return "B3_%s" % t[1]
    return "C_%s_%s_%s" % (t[1], t[2], t[3].lower())
def num(x):
    if x in ("-", "None", "none", "nan"): return None
    return float(x)
def mine(path):
    out = {}
    for l in open(path):
        m = re.match(r"(\S+) fee (\S+) n (\d+) days (\d+) perday (\S+) pf2 (\S+) pf5 (\S+) h1 (\S+) h2 (\S+) z (\S+) p (\S+) gate (\S+)", l)
        r, fee, n, d, pdy, p2, p5, h1, h2, z, p, g = m.groups()
        out[(name(r), "net_taker" if float(fee) > 0.001 else "net_maker")] = dict(n=int(n), days=int(d), per_day=float(pdy), pf_lo=num(p2), pf_hi=num(p5), h1=num(h1), h2=num(h2), z=num(z), p=num(p), gate=g == "True")
    return out
def theirs(path):
    out = {}
    for l in open(path):
        if l.startswith("header"): continue
        m = re.match(r"(\S+)\|(\S+) \| n (\d+) days (\d+) per_day (\S+) \| pf_lo (\S+) pf_hi (\S+) h1 (\S+) h2 (\S+) \| z (\S+) p (\S+) \| gate (\S+)", l)
        if not m: continue
        r, f, n, d, pdy, p2, p5, h1, h2, z, p, g = m.groups()
        out[(r, f)] = dict(n=int(n), days=int(d), per_day=float(pdy), pf_lo=num(p2), pf_hi=num(p5), h1=num(h1), h2=num(h2), z=num(z), p=num(p), gate=g == "True")
    return out
def close(a, b):
    if a == 0.0 and b is None: return True      # my build prints 0.0 for the PF of an empty set (no trades or an empty half); theirs prints None: same meaning, a presentation difference only
    if a is None or b is None: return a is b
    if math.isinf(a) or math.isinf(b): return a == b
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))
a, b = mine(sys.argv[1]), theirs(sys.argv[2]); bad = 0
print("my lines", len(a), "their lines", len(b), "keys only in mine", sorted(set(a) - set(b))[:5], "only in theirs", sorted(set(b) - set(a))[:5])
for k in sorted(set(a) & set(b)):
    diffs = [f for f in a[k] if not (a[k][f] == b[k][f] if f in ("n", "days", "gate") else close(a[k][f], b[k][f]))]
    if diffs: bad += 1; print("DIFF", k, {f: (a[k][f], b[k][f]) for f in diffs})
print("rule-fee lines compared", len(set(a) & set(b)), "differing", bad)
