#!/usr/bin/env python3
"""POOL1 compare: my 220 driver lines (pool1_driver_second.run) against Desk A's printed lines file, rule by rule at 1e-9. Usage: pool1_compare_second.py <fixture.json.gz | my printed lines file .txt> <desk A lines file>   (a .txt first argument is the output of pool1_second_run.py or of pool1_driver_second on a fixture, compared as printed)"""
import gzip, json, re, sys, math
import pool1_driver_second as d

def mine(path):
    if path.endswith(".txt"):
        out = {}
        for l in open(path).read().splitlines():
            if " | trades_lo " in l: out[l.split(" | ")[0].strip()] = l
        return out, None, None
    J = json.load(gzip.open(path)); data = {n: {int(t): tuple(v) for t, v in s.items()} for n, s in J["data"].items()}; fund = {n: {int(t): r for t, r in f.items()} for n, f in J["funding"].items()}
    out = {}
    for l in d.run(data, fund)[2:]:
        h = l.split(" | ")[0].strip()
        out[h] = l
    return out, data, fund

def key_mine(h):
    m = re.fullmatch(r"gap(\d+)_(follow|fade)_k(\d)_(\d)_T(\d+)", h)
    if m: return "gap:%s:%s|%s-%s-%s" % m.groups()
    m = re.fullmatch(r"fund(level|change)_(follow|fade)_k(\d)_(\d)_T(\d+)", h)
    if m: return "%s:%s|%s-%s-%s" % (("fl" if m.group(1) == "level" else "fc"), m.group(2), m.group(3), m.group(4), m.group(5))
    m = re.fullmatch(r"tr(\d+)_c(\d)_(trend|rev)_k(\d)_(\d)_T(\d+)", h)
    if m: return "tr:%s:%s:%s|%s-%s-%s" % m.groups()
    m = re.fullmatch(r"carry([AB])", h)
    if m: return "carry:%s|carry" % m.group(1)
    raise ValueError(h)

def parse_a(path):
    out = {}
    for l in open(path).read().splitlines()[2:]:
        f = l.split("|"); k = "|".join(f[:2]); v = {x.split("=", 1)[0]: x.split("=", 1)[1] for x in f[2:6] + f[6:7]} if False else {}
        for x in f[2:]:
            if "=" in x: a, b = x.split("=", 1); v[a] = b
        out[k] = v
    return out

def num(x):
    return float("nan") if x in ("nan", "None") else float(x)

if __name__ == "__main__":
    mm, data, fund = mine(sys.argv[1]); A = parse_a(sys.argv[2]); diffs = []; seen = 0
    for h, l in mm.items():
        k = key_mine(h); a = A.get(k)
        if a is None: diffs.append((h, "no Desk A line")); continue
        seen += 1
        parts = [x.strip() for x in l.split(" | ")]; t = re.findall(r"trades_lo (\d+) booked_lo (\d+)", l)[0], re.findall(r"trades_hi (\d+) booked_hi (\d+)", l)[0]
        nets = re.findall(r"net_lo (\S+) net_hi (\S+)", l)[0]; pfs = re.findall(r"pf_lo (\S+) pf_hi (\S+)", l)[0]
        mine_v = {"t1": int(t[0][0]), "b1": int(t[0][1]), "t2": int(t[1][0]), "b2": int(t[1][1]), "net1": float(nets[0]), "net2": float(nets[1]), "pf1": num(pfs[0]), "pf2": num(pfs[1])}
        for kk, v in mine_v.items():
            av = num(a[kk]) if kk not in ("t1", "b1", "t2", "b2") else int(a[kk])
            ok = (v == av) if isinstance(v, int) else ((math.isnan(v) and (math.isnan(av) or av == 0.0)) or (math.isinf(v) and math.isinf(av)) or abs(v - av) < 1e-9 * max(1, abs(av)) or (math.isnan(v) and av in (0.0,)))
            if not ok: diffs.append((h, kk, v, av))
    print("compared", seen, "rules; differing cells", len(diffs), "in", len(set(x[0] for x in diffs)), "rules")
    for x in diffs: print(x)
