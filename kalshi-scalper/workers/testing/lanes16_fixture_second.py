#!/usr/bin/env python3
"""Invented fixture for lanes 1 and 6 (seeded, no real data): the 13 basket names, 7 weekdays from 2026-11-05, minute candles 08:00 to 17:00 ET, a sector factor plus own noise and rare own jumps, spread 1 to 3 ticks of 0.01, funding every 8 h. Writes JSON {data:{name:{end:[bid,ask]}}, funding:{name:{ts:rate}}}."""
import json, random, sys
import lanes16_second as m, pool1_second as P
def build():
    rnd = random.Random(20261116); data, fund = {}, {}
    first = 1793836800 // 86400; days = [d for d in range(first, first + 12) if (d + 4) % 7 < 5][:7]          # 2026-11-05 is a Thursday
    names = [n for b in m.BASKETS.values() for n in b]; px = {n: 50 + 10 * i for i, n in enumerate(names)}
    for n in names: data[n] = {}
    for d in days:
        for t in range(P.et_end(d, 8, 0), P.et_end(d, 17, 0) + 1, 60):
            fac = {b: rnd.gauss(0, 0.0004) for b in m.BASKETS}
            for b, ns in m.BASKETS.items():
                for n in ns:
                    px[n] *= 1 + fac[b] + rnd.gauss(0, 0.0005) + (0.004 * rnd.choice((-1, 1)) if rnd.random() < 0.004 else 0)
                    sp = 0.01 * rnd.choice((1, 2, 3)); q = round(px[n], 2); data[n][t] = [q, round(q + sp, 2)]
    for n in names: fund[n] = {P.et_end(days[0], 0, 0) + 28800 * k: round(rnd.gauss(0.0001, 0.0001), 6) for k in range(0, 25)}
    return {"data": data, "funding": fund}
if __name__ == "__main__": json.dump(build(), open(sys.argv[1], "w"))
