"""XVENUE1 scoring (no trade, information only). Needs data/xvenue1_pm.json, data/xvenue1_cb.json and the Polymarket history cache (path argv[1], from the candidate list)."""
from __future__ import annotations

import json
import sqlite3
import statistics as st
import sys
from collections import defaultdict

from .paths import DATA_DIR
from .xvenue1 import DBS, PFX, joined


def main(S):
    rows = joined()
    cb = json.load(open(DATA_DIR / "xvenue1_cb.json"))
    out = []
    print("== agreement")
    tot = defaultdict(lambda: [0, 0, 0, 0])
    for x in rows:
        a = x["series"]; d = x["k_yes"] != x["pm_up"]
        tot[a][0] += 1; tot[a][1] += d
        tot[a][2] += d and x["k_yes"] == 1; tot[a][3] += d and x["k_yes"] == 0
    for a, (n, d, ky, kn) in tot.items():
        print(f"{a} joined {n} agree {n-d} disagree {d} share {100*d/n:.2f}% (kalshi yes/pm down {ky}, kalshi no/pm up {kn})")
    n = sum(v[0] for v in tot.values()); d = sum(v[1] for v in tot.values())
    print(f"ALL joined {n} agree {n-d} disagree {d} share {100*d/n:.2f}%")
    # spot distance: Coinbase close of the minute starting close-60 (price at the close) in basis points of the strike
    def dist(x):
        s = cb[x["series"]].get(str(x["close"] - 60))
        return None if s is None or not x["strike"] else 1e4 * (s - x["strike"]) / x["strike"]
    for x in rows:
        x["dbp"] = dist(x)
    print("== |spot at close - strike| in basis points (Coinbase 1 minute close)")
    for a in PFX:
        dis = [abs(x["dbp"]) for x in rows if x["series"] == a and x["k_yes"] != x["pm_up"] and x["dbp"] is not None]
        al = [abs(x["dbp"]) for x in rows if x["series"] == a and x["dbp"] is not None]
        q = lambda v, p: sorted(v)[int(p * (len(v) - 1))]
        print(a, "disagree n", len(dis), "median %.2f p25 %.2f p75 %.2f p90 %.2f" % (st.median(dis), q(dis, .25), q(dis, .75), q(dis, .9)),
              "| all windows n", len(al), "median %.2f p25 %.2f p75 %.2f" % (st.median(al), q(al, .25), q(al, .75)))
        for lim in (1, 2, 5, 10):
            nd = sum(1 for v in dis if v <= lim); na = sum(1 for v in al if v <= lim)
            print(f"  within {lim} bp of strike: disagreements {nd}/{len(dis)} = {100*nd/len(dis):.0f}%; all windows {na}/{len(al)} = {100*na/len(al):.0f}%; disagreement rate inside {100*nd/na:.2f}%")
    # both 80c+
    cons = {d: sqlite3.connect(DATA_DIR / f"{d}.sqlite") for d in DBS}
    H = json.load(open(S + "pmhist.json"))
    c = {"n": 0, "nopm": 0, "side_mismatch": 0, "both": 0, "dis": 0}
    per = defaultdict(lambda: [0, 0]); both = []
    for x in rows:
        q = None
        for d in DBS:
            q = cons[d].execute("select bid_c,ask_c from candle where ticker=? and end_ts=?", (x["ticker"], x["close"] - 360)).fetchone()
            if q: break
        if not q or q[0] is None or q[1] is None: continue
        if q[1] >= .80: side, kp = 1, q[1]
        elif 1 - q[0] >= .80: side, kp = 0, 1 - q[0]
        else: continue
        c["n"] += 1
        h = H.get(x["ticker"])
        pts = [(r["t"], r["p"]) for r in (h or []) if r["t"] <= x["close"] - 360 and x["close"] - 360 - r["t"] <= 150]
        if not pts: c["nopm"] += 1; continue
        pu = pts[-1][1]; ppx = pu if side else 1 - pu
        if ppx < .80: c["side_mismatch"] += 1; continue
        c["both"] += 1
        dd = (x["k_yes"] != x["pm_up"])
        c["dis"] += dd; per[x["series"]][0] += 1; per[x["series"]][1] += dd
        both.append((x["ticker"], side, kp, ppx, x["k_yes"], x["pm_up"], dd))
    print("== Kalshi side >= 0.80 at close-360:", c)
    for a, (n, dd) in per.items(): print(a, "both-80c+ n", n, "disagree", dd)
    if c["both"]:
        print("both-80c+ share disagree %.2f%%" % (100 * c["dis"] / c["both"]))
        # outcome of the Kalshi side among both-80c+ for context is NOT reported
        for t in [b for b in both if b[6]]: print("  dis", t[0], "side", "yes" if t[1] else "no", "kalshi %.2f pm %.3f" % (t[2], t[3]), "kalshi_yes", t[4], "pm_up", t[5])


if __name__ == "__main__":
    main(sys.argv[1])
