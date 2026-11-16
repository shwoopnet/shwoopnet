#!/usr/bin/env python3
"""PERPSLANE4 real-data run (Testing Desk): loader (allow line, manifest), the pool filter of the definitions (a name needs candles on at least 5 ET dates and at least 2 prints), the signed plugin and driver, m_carried as an argument, A2 only if a ratio table is given. Output to scratch; its sha256 is committed BEFORE it is read.
  python3 -I lane4_run.py <dir with kalshi1m/ and funding/> <m_carried> [allow file] [under_ratio.json]"""
import hashlib, json, sys
import engine1_perps_second as p
import lane4_load as L, lane4_driver as D


def pool(data, funding):
    out = []
    for n in sorted(data):
        days = set(p.et_local_day(t) for t in data[n])
        if len(days) >= 5 and len(funding.get(n, {})) >= 2: out.append(n)
    return out


def run(directory, m_carried, allow_file=None, ratios=None):
    data, funding, counts, wk = L.load(directory, allow_file)
    names = pool(data, funding); data = {n: data[n] for n in names}; funding = {n: funding[n] for n in names}
    under = {} if ratios is None else {n: {int(k): (v, 1.0) for k, v in d.items()} for n, d in ratios.items() if n in data}
    head = ["loader counts " + repr(sorted(counts.items())), "pool %d names: %s" % (len(names), ",".join(names)), "prints by UTC weekday (Mon=0) " + repr(sorted(wk.items())), "A2 underlyings %s" % ("given for %d names" % len(under) if ratios is not None else "NOT given: A2 rules print n 0")]
    return head + D.run(data, funding, under, m_carried)


if __name__ == "__main__":
    a = sys.argv[1:]; m = int(a[1]); allow = a[2] if len(a) > 2 else None; rat = json.load(open(a[3])) if len(a) > 3 else None
    text = "\n".join(run(a[0], m, allow, rat)) + "\n"; sys.stdout.write(text); sys.stderr.write("print sha256 %s\n" % hashlib.sha256(text.encode()).hexdigest())
