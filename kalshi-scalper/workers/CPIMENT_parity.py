"""Parity check for CPIMENT-RERUN. Reads NO outcome (no result, no P/L). Run: PYTHONPATH=src python3 workers/CPIMENT_parity.py [raw|counts]"""
import json, sys
from datetime import datetime
from scalper import api
from scalper.candlefield import quote_close
from scalper.paths import DATA_DIR

def ts(s): return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())

def raw():
    ms = json.loads((DATA_DIR / "cpi1/markets_head.json").read_text())
    pick = ["CPI-24JUN-T0.1", "CPI-22MAR-T0.5", "CPI-25JAN-T0.2"]
    pick = [t for t in pick if t in ms] or list(ms)[:3]
    pick += [t for t in list(ms) if ms[t]["src"] == "live"][:1]
    for tk in pick:
        m = ms[tk]; close = ts(m["close"])
        path = f"/historical/markets/{tk}/candlesticks" if m["src"] == "hist" else f"/series/{tk.split('-')[0]}/markets/{tk}/candlesticks"
        cs = api._get(path, {"start_ts": close - 6 * 86400, "end_ts": close, "period_interval": 60}).get("candlesticks", [])
        old = sum(1 for c in cs if api.f((c.get("yes_bid") or {}).get("close_dollars")) is not None and api.f((c.get("yes_ask") or {}).get("close_dollars")) is not None)
        new = sum(1 for c in cs if quote_close(c.get("yes_bid")) is not None and quote_close(c.get("yes_ask")) is not None)
        print(f"{tk} src={m['src']}: candles {len(cs)}, with bid+ask OLD extraction {old}, FIXED {new}")

def counts():
    lead = 86400
    for kind in ("head", "core"):
        ms = json.loads((DATA_DIR / f"cpi1/markets_{kind}.json").read_text()); cd = json.loads((DATA_DIR / f"cpi1/candles_{kind}.json").read_text())
        n = q = 0; evs = set(); evq = set()
        for tk, m in ms.items():
            if m["type"] != "greater" or m["strike"] is None: continue
            n += 1; evs.add(m["ev"]); target = ts(m["close"]) - lead
            ok = [c for c in cd.get(tk, []) if c[0] <= target and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1]
            if ok: q += 1; evq.add(m["ev"])
        print(f"CPI1 {kind}: 'above' markets {n} on {len(evs)} events; with a bid+ask quote at the registered look (last candle >=24h before close) {q} on {len(evq)} events")
    ms = json.loads((DATA_DIR / "ment1/markets.json").read_text()); cd = {}
    for f in sorted((DATA_DIR / "ment1").glob("candles*.json")): cd.update(json.loads(f.read_text()))
    from collections import defaultdict
    evc = defaultdict(list)
    for m in ms.values(): evc[m["ev"]].append(ts(m["close"]))
    n = q = 0; evq = set()
    for m in ms.values():
        n += 1; dec = min(evc[m["ev"]]) - 8 * 3600
        if any(x[0] <= dec and x[1] is not None and x[2] is not None and 0 < x[1] < x[2] < 1 for x in cd.get(m["t"], [])): q += 1; evq.add(m["ev"])
    print(f"MENT1: markets {n} on {len(evc)} events, candles fetched for {sum(1 for t in ms if t in cd)}; with a bid+ask quote at the registered look {q} on {len(evq)} events")

{"raw": raw, "counts": counts}[sys.argv[1] if len(sys.argv) > 1 else "raw"]()
