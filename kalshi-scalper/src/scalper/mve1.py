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


# ---------------- scoring (registered 2026-11-05, workers/MVE1_REGISTRATION.md) ----------------
import datetime, hashlib, math, os, random

CUT = int(datetime.datetime(2026, 10, 3, 16, 0, tzinfo=datetime.timezone.utc).timestamp())
D2 = int(datetime.datetime(2026, 9, 20, tzinfo=datetime.timezone.utc).timestamp())
CAP = 400
MAX_PROCESS = 1800

def _ts(s): return int(datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())

def fee(p, c=10, mult=1.0):
    return math.ceil(mult * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100

def windows():
    d = datetime.date(2026, 9, 6)
    while d <= datetime.date(2026, 10, 3):
        for h in (12, 20):
            a = int(datetime.datetime(d.year, d.month, d.day, h, tzinfo=datetime.timezone.utc).timestamp())
            if a + 1200 < CUT: yield a, a + 1200
        d += datetime.timedelta(days=1)

def list_window(a, b):
    r = _get("/markets", {"limit": 1000, "mve_filter": "only", "status": "settled", "min_close_ts": a, "max_close_ts": b})
    return r["markets"]

def candles(series, ticker, a, b):
    return _get(f"/series/{series}/markets/{ticker}/candlesticks", {"start_ts": a, "end_ts": b, "period_interval": 1}).get("candlesticks", [])

def fl(x):
    try: return float(x)
    except Exception: return None

def score(cache):
    pool = {}
    if os.path.exists(cache + ".pool.json"):
        pool = json.load(open(cache + ".pool.json"))
    else:
        for a, b in windows():
            for m in list_window(a, b):
                legs = m.get("mve_selected_legs") or []
                if not (2 <= len(legs) <= 5) or any(l["side"] != "yes" for l in legs): continue
                if (fl(m["volume_fp"]) or 0) <= 0: continue
                ct = _ts(m["close_time"])
                if ct >= CUT: continue
                pool[m["ticker"]] = {"created": _ts(m["created_time"]), "close": ct, "res": m["result"],
                                     "legs": [(l["event_ticker"], l["market_ticker"]) for l in legs]}
            time.sleep(0.4)
        json.dump(pool, open(cache + ".pool.json", "w"))
    print("pool (2-5 yes legs, traded, before cut):", len(pool), flush=True)
    order = sorted(pool, key=lambda t: hashlib.md5(t.encode()).hexdigest())
    done = {}
    if os.path.exists(cache + ".done.json"): done = json.load(open(cache + ".done.json"))
    ncheap = sum(1 for v in done.values() if v.get("cheap"))
    for t in order[:MAX_PROCESS]:
        if t in done: continue
        if ncheap >= CAP: break
        p = pool[t]
        try:
            cs = candles("KXMVECROSSCATEGORY", t, p["created"] - 60, p["close"] + 120)
        except Exception as e:
            done[t] = {"err": str(e)[:60]}; continue
        first = next((c for c in cs if (fl(c.get("volume_fp")) or 0) > 0), None)
        pr = fl(first["price"].get("open_dollars")) if first else None
        if pr is None or not (0.03 <= pr <= 0.30):
            done[t] = {"cheap": False, "price": pr}; continue
        end = first["end_period_ts"]
        mids, bad = [], False
        for ev, mt in p["legs"]:
            try:
                lc = candles(ev.split("-")[0], mt, end - 900, end + 60)
            except Exception:
                bad = True; break
            lc = [c for c in lc if c["end_period_ts"] <= end + 60]
            m = None
            for c in reversed(lc):
                bid, ask = fl(c["yes_bid"].get("close_dollars")), fl(c["yes_ask"].get("close_dollars"))
                if bid is not None and ask is not None and ask > 0: m = (bid + ask) / 2; break
                if ask: m = ask; break
            if m is None or m <= 0: bad = True; break
            mids.append(m)
        done[t] = {"cheap": True, "price": pr, "end": end, "mids": None if bad else mids}
        ncheap += 1
        if len(done) % 25 == 0:
            json.dump(done, open(cache + ".done.json", "w")); print("processed", len(done), "cheap", ncheap, flush=True)
    json.dump(done, open(cache + ".done.json", "w"))
    rows = []
    for t, d in done.items():
        if d.get("cheap") and d.get("mids"):
            prod = 1.0
            for m in d["mids"]: prod *= m
            rows.append({"t": t, "p": d["price"], "R": d["price"] / prod, "win": pool[t]["res"] == "yes",
                         "close": pool[t]["close"], "hour": pool[t]["created"] // 3600, "n": len(d["mids"])})
    json.dump(rows, open(cache + ".rows.json", "w"))
    report(rows, ncheap, sum(1 for d in done.values() if d.get("cheap") and not d.get("mids")))

def stats(rows, mult=1.0):
    if not rows: return None
    net = [(1.0 if r["win"] else 0.0) * 10 - 10 * r["p"] - fee(r["p"], 10, mult) for r in rows]  # dollars per 10 contracts
    per = [x / 10 * 100 for x in net]  # cents per contract
    g = sum(x for x in net if x > 0); l = -sum(x for x in net if x < 0)
    byh = {}
    for r, x in zip(rows, per): byh.setdefault(r["hour"], []).append(x)
    hm = [sum(v) / len(v) for v in byh.values()]
    mean = sum(per) / len(per)
    se = (sum((x - sum(hm) / len(hm)) ** 2 for x in hm) / max(1, len(hm) - 1)) ** .5 / max(1, len(hm)) ** .5 if len(hm) > 1 else float("nan")
    # cluster z: weighted mean of per by hour sums
    sums = {h: sum(v) for h, v in byh.items()}
    tot = sum(sums.values()); n = len(per)
    var = sum((s - mean * len(byh[h])) ** 2 for h, s in sums.items())
    z = mean / ((var ** .5) / n) if var > 0 else float("nan")
    return {"n": n, "hours": len(byh), "win": sum(r["win"] for r in rows) / n, "avg_p": sum(r["p"] for r in rows) / n,
            "net_c": mean, "pf": (g / l if l else float("inf")), "z": z}

def report(rows, ncheap, nlegfail):
    print("cheap candidates", ncheap, "with legs priced", len(rows), "leg-price failures", nlegfail)
    arms = {"CONTROL": rows, "A R<=0.80": [r for r in rows if r["R"] <= 0.8], "B R<=0.50": [r for r in rows if r["R"] <= 0.5],
            "info R>=1.25": [r for r in rows if r["R"] >= 1.25]}
    print("mean R", sum(r["R"] for r in rows) / max(1, len(rows)))
    for k, rs in arms.items():
        for name, sub in (("all", rs), ("D1", [r for r in rs if r["close"] < D2]), ("D2", [r for r in rs if r["close"] >= D2])):
            print(k, name, stats(sub))
        print(k, "fees x1.2", stats(rs, 1.2))

if __name__ == "__main__" and sys.argv[1] == "score":
    score(sys.argv[2])
