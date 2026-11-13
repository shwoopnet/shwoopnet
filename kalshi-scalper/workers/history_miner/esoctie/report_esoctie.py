#!/usr/bin/env python3
"""ESOCTIE result page (reporting only; the frozen esoctie.py is imported unchanged).
Adds, beside n (Forensics' requests, Nov 12): UTC days with a bet (the z clusters) and bets after base-building, and the NOTE 10 line.
Usage: python3 -I report_esoctie.py --lists <folder>... --candles <folder>..."""
import hashlib, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import esoctie as E
FROZEN = {"esoctie.py": "1646f54274f3a370ae8cf39e969d8c958da1b3fa9177ed854372fc7207baf8e8", "ESOCTIE_SERIES.json": "5c766fdd7e30a2fac038247798b1f81ed4d36e87b9c90ec2ea50b6bda4e10612"}
for f, h in FROZEN.items():
    if hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest() != h:
        sys.exit("refused: %s is not the frozen file" % f)
E.check_hashes()
a = sys.argv[1:]
lists, cands = a[a.index("--lists") + 1:a.index("--candles")], a[a.index("--candles") + 1:]
res = E.score(lists, cands)
m = res["measurement"]
out = {"note": "Development only. The half split was moved to 2026-10-15T12:00Z after the lists landed and before any price or result was read (registration NOTE 10). About 7,100 development events: this read can falsify or show a lead; it cannot reach the research bar alone.",
       "measurement": m}
if isinstance(res["rule"], dict):
    r = res["rule"]
    # days with a bet and bets after base-building, recomputed from the same frozen functions
    rep, rows = E.measure(lists, cands)
    bets = [x for x in rows if x["b"] is not None and x["gap"] >= E.GAP and x["spread"] <= E.SPREAD]
    out["bets_after_base_building"] = len(bets)
    out["utc_days_with_a_bet"] = len({time.strftime("%Y-%m-%d", time.gmtime(x["S"])) for x in bets})
    out["rule"] = r
else:
    out["rule"] = res["rule"]; out["kill"] = res.get("kill")
print(json.dumps(out, indent=1, default=str))
