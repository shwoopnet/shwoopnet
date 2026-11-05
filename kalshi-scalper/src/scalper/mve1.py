"""MVE1 census: settled Kalshi multivariate combo (KXMVE*) markets, metadata only.

Census mode stores NO outcome (the `result`, `settlement_value_dollars` and `expiration_value`
fields are dropped on read) so counts can be fixed before any scoring. Research only.
"""
from __future__ import annotations
import json, sys, time, collections
from scalper.api import _get

DROP = {"result", "settlement_value_dollars", "expiration_value", "rules_primary", "rules_secondary"}

def census(out: str, max_pages: int = 60):
    cur, rows, pages = None, [], 0
    while pages < max_pages:
        p = {"limit": 1000, "mve_filter": "only", "status": "settled"}
        if cur: p["cursor"] = cur
        r = _get("/markets", p); pages += 1
        for m in r["markets"]:
            m = {k: v for k, v in m.items() if k not in DROP}
            m["nlegs"] = len(m.get("mve_selected_legs") or [])
            rows.append({k: m.get(k) for k in ("ticker", "mve_collection_ticker", "created_time", "close_time", "last_price_dollars", "volume_fp", "nlegs")} | {"legs": [l["market_ticker"] + "|" + l["side"] for l in m.get("mve_selected_legs") or []]})
        cur = r.get("cursor")
        if not cur: break
        time.sleep(0.6)
    json.dump(rows, open(out, "w"))
    traded = [x for x in rows if float(x["volume_fp"] or 0) > 0]
    print("settled combos", len(rows), "traded", len(traded), "pages", pages)
    print("oldest created", min(x["created_time"] for x in rows), "newest", max(x["created_time"] for x in rows))
    print("by collection", collections.Counter(x["mve_collection_ticker"] for x in traded).most_common(8))
    lp = [float(x["last_price_dollars"]) for x in traded]
    print("traded last price: <3c", sum(p < .03 for p in lp), "3-30c", sum(.03 <= p <= .30 for p in lp), ">30c", sum(p > .30 for p in lp))

if __name__ == "__main__":
    if sys.argv[1] == "census": census(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 60)
