#!/usr/bin/env python3
"""Invented CHEAPFLIP fixture (seeded, no real data): 3 series x 12 markets with 2 second polls over 15 minutes, a wandering cheap side, results yes/no/void/none. Writes JSON {markets: {ticker: [series, close, [[recv_ms, yes_bids, no_bids]...]]}, results}."""
import json, random, sys
def build():
    rnd = random.Random(20261117); mk, res = {}, {}; base = 1794355200
    for si, s in enumerate(("KXHYPE15M", "KXBNB15M", "KXNATGAS15M")):
        for m in range(12):
            tk = "%s-%02d" % (s, m); close = base + 900 * (m + 1) + 86400 * si; polls = []; y = rnd.choice((2, 3, 4, 6, 9, 15, 40))
            for i in range(0, 900, 2):
                y = max(1, min(99, y + rnd.choice((0, 0, 0, 1, -1, 2, -2, 5 if rnd.random() < 0.02 else 0)))); sp = rnd.choice((1, 1, 2))
                yb, nb = y, max(1, 100 - y - sp)
                lv = lambda p: [[p / 100.0, rnd.choice((1, 3, 5, 9, 20))]] + [[max(1, p - j) / 100.0, 5] for j in range(1, 3)] + [[None, None], [None, None]]
                polls.append([int((close - 900 + i) * 1000) + rnd.choice((0, 0, 13)), lv(yb), lv(nb)])
            polls.append([int((close + 3) * 1000), [[0.5, 5]] + [[None, None]] * 4, [[0.4, 5]] + [[None, None]] * 4])
            mk[tk] = [s, close, polls]; res[tk] = rnd.choice(("yes", "no", "yes", "void", None, "no"))
    return {"markets": mk, "results": {k: v for k, v in res.items() if v}}
if __name__ == "__main__": json.dump(build(), open(sys.argv[1], "w"))
