"""XVENUE1 (README, Result: XVENUE1): no-trade measurement of how often Kalshi's and Polymarket's 15 minute Bitcoin and Ethereum markets resolve differently. Research only, public data, no trade.
Usage: python -m scalper.xvenue1 fetch   (Polymarket outcomes into data/xvenue1_pm.json)
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.request

from .paths import DATA_DIR

OUT = DATA_DIR / "xvenue1_pm.json"
DBS = ["l1b", "book", "fresh"]
PFX = {"KXBTC15M": "btc", "KXETH15M": "eth"}


def g(u):
    for i in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "research"}), timeout=30))
        except Exception:
            time.sleep(2 + i * 2)
    raise RuntimeError(u)


def kalshi_windows():
    w = {}
    for d in DBS:
        c = sqlite3.connect(DATA_DIR / f"{d}.sqlite")
        for t, s, o, cl, r, k in c.execute("select ticker,series,open_ts,close_ts,result,strike from market where series in ('KXBTC15M','KXETH15M')"):
            w[(s, cl)] = (t, o, r, k, d)
    return w


def fetch():
    w = kalshi_windows()
    have = json.load(open(OUT)) if OUT.exists() else {}
    keys = [k for k in sorted(w) if f"{PFX[k[0]]}-updown-15m-{k[1]-900}" not in have]
    print(len(w), "kalshi windows", len(keys), "to fetch")
    for i in range(0, len(keys), 20):
        ch = keys[i:i + 20]
        sl = [f"{PFX[s]}-updown-15m-{cl-900}" for s, cl in ch]
        r = g("https://gamma-api.polymarket.com/events?" + "&".join("slug=" + x for x in sl) + "&limit=100")
        got = set()
        for e in r:
            m = e["markets"][0]
            got.add(e["slug"])
            have[e["slug"]] = {"op": m.get("outcomePrices"), "tok": m.get("clobTokenIds"), "uma": m.get("umaResolutionStatus"), "end": m.get("endDate"), "outs": m.get("outcomes")}
        for x in sl:
            if x not in got:
                have[x] = None
        if (i // 20) % 25 == 0:
            json.dump(have, open(OUT, "w")); print(i, len(have), flush=True)
        time.sleep(0.3)
    json.dump(have, open(OUT, "w"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        fetch()
