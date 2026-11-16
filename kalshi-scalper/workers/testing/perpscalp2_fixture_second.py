#!/usr/bin/env python3
"""Invented PERPSCALP2 fixture (seeded, no real data): 3 names, 12 weekdays from 2026-11-02, 1 minute candles 08:00 to 16:00 ET, funding every 8h. Writes JSON {data:{name:{end:[bid,ask,vol]}}, funding:{name:{ts:rate}}, ticks:{name:tick}}."""
import json, random, sys
import lane4_plugin as L4
def build():
    rnd = random.Random(20261116); data, fund = {}, {}
    day0 = 1793664000 // 86400 - 1; days = [d for d in range(day0, day0 + 16) if L4.is_session(d)][:12]
    for name, base in (("KXAAA", 100.0), ("KXBBB", 250.0), ("KXCCC", 40.0)):
        s, px = {}, base
        for d in days:
            a, b = L4.et_end(d, 8, 0), L4.et_end(d, 16, 0)
            for t in range(a, b + 1, 60):
                px *= 1 + rnd.gauss(0, 0.0006) + (0.002 * rnd.choice((-1, 1)) if rnd.random() < 0.01 else 0)
                tick = 0.01; sp = tick * rnd.choice((2, 2, 3, 4)); q = round(px / tick) * tick
                s[t] = [round(q - sp / 2, 4), round(q + sp / 2, 4), rnd.choice((0, 5, 10, 20, 60, 200)) + (400 if rnd.random() < 0.02 else 0)]
        data[name] = s; fund[name] = {days[0] * 86400 + 28800 * k: round(rnd.gauss(0.0001, 0.0001), 6) for k in range(0, 40)}
    return {"data": data, "funding": fund, "ticks": {n: 0.01 for n in data}}
if __name__ == "__main__": json.dump(build(), open(sys.argv[1], "w"))
