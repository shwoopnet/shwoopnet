#!/usr/bin/env python3
"""SOCDRIFT fixture, BUILD 2: 90 invented games over 20 UTC days, 3 winner markets each (home, away, tie), hourly candles from K - 33 h to K (K = occurrence - 3 h); a bad clock, a tie and a live jump in some games, crossed and missing candles, early closes, voids. Invented numbers only.
Usage: socdrift_fixture_second.py <out.json.gz>"""
import calendar, gzip, json, random, sys
MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
def build():
    rng = random.Random(20261118); rungs, candles = [], {}
    base = calendar.timegm((2026, 9, 20, 0, 0, 0))
    for g in range(90):
        day = g // 5; O = base + day * 86400 + rng.choice([12, 13, 14, 15, 16, 17, 18]) * 3600 + rng.choice([0, 900, 1800, 2700]); K = O - 3 * 3600
        t0 = calendar.timegm(__import__("time").gmtime(O - 3 * 3600 - 86400)[:6]) if False else None
        gm = __import__("time").gmtime(O); ev = "KXEPLGAME-%02d%s%02d%s" % (gm.tm_year % 100, MON[gm.tm_mon - 1], gm.tm_mday, "T%02d" % g)
        probs = [rng.uniform(0.2, 0.6), 0.0, 0.0]; probs[2] = rng.uniform(0.15, 0.3); probs[1] = max(0.05, 1 - probs[0] - probs[2]); winner = rng.choices(range(3), weights=probs)[0]
        for oi, out in enumerate(["HOME", "AWAY", "TIE"]):
            tk = "%s-%s" % (ev, out); occ = O + (900 if (g == 7 and oi == 1) else 0) + (600 if (g == 11 and oi == 0) else 0)
            res = "yes" if oi == winner else "no"
            if rng.random() < 0.02: res = "void"
            close = O + 2 * 3600 + rng.choice([0, 600, 1800]) if rng.random() > 0.05 else K - 20 * 3600
            rungs.append({"ticker": tk, "event": ev, "outcome": out, "open_time": K - rng.choice([3, 20, 40, 100]) * 3600, "close_time": close, "occ": occ, "result": res})
            s = {}; mid = min(0.9, max(0.05, probs[oi]))
            for t in range((K - 33 * 3600) // 3600 * 3600 + 3600, K + 1, 3600):
                mid = min(0.95, max(0.03, mid + rng.gauss(0, 0.012)))
                if g in (3, 21) and t >= K // 3600 * 3600: mid = min(0.95, mid + 0.2)
                if g in (5, 17) and oi == 0 and K - 6 * 3600 < t <= K - 3 * 3600 and t == (K // 3600 * 3600 - 4 * 3600): mid = min(0.95, mid + 0.2)
                sp = rng.choice([0.01, 0.02, 0.02, 0.03, 0.05, 0.08]); vol = rng.choice([0, 1, 2, 5, 9]); r = rng.random()
                if r < 0.04: continue
                bid, ask = (mid + sp / 2, mid - sp / 2) if r < 0.06 else (mid - sp / 2, mid + sp / 2)
                s[t] = [round(bid, 4), round(ask, 4), float(vol)]
            candles[tk] = {str(t): v for t, v in s.items()}
    return {"rungs": rungs, "candles": candles}
if __name__ == "__main__":
    with gzip.open(sys.argv[1], "wt") as fh: json.dump(build(), fh, sort_keys=True)
