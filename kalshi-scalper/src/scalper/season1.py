"""SEASON1: season win-total ladders (KXNFLWINS-*, KXMLBWINS-*, KXNBAWINS), cheap YES rungs, held to settlement.
Usage: python3 -I src/scalper/season1.py fetch OUT.jsonl SERIES_FILE   (listings, then one hourly-candle window per market ending at the look)
       python3 -I src/scalper/season1.py score OUT.jsonl
Look = last valid two-sided hourly candle ending at least LEAD days before the market close (NFL 14, others 21). Cheap = ask 0.03..0.30.
Never reads markets that closed after the frozen cut 2026-10-03T16:00Z. Control arm only (the treated arm needs a standings join, see result)."""
import sys, os, json, math, random, hashlib, datetime, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from scalper import api

CUT = "2026-10-03T16:00:00Z"
LO, HI, MAXQ = 0.03, 0.30, 0.10


def ts(s):
    return int(datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def lead_days(series):
    return 14 if series.startswith("KXNFLWINS") else 21


def fee(p, c=10):
    return math.ceil(0.07 * c * p * (1 - p) * 100 - 1e-9) / 100.0


def listing(series):
    seen = {}
    for path, q in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cur = None
        while True:
            p = dict(series_ticker=series, limit=1000, **q)
            if cur: p["cursor"] = cur
            d = api._get(path, p)
            for m in d.get("markets", []):
                if (m.get("close_time") or "9") < CUT and m.get("result") in ("yes", "no"):
                    seen[m["ticker"]] = m
            cur = d.get("cursor")
            if not cur: break
    return list(seen.values())


def cmd_fetch(out, sfile):
    done = set()
    if os.path.exists(out):
        for l in open(out): done.add(json.loads(l)["ticker"])
    f = open(out, "a")
    for series in open(sfile).read().split():
        for m in listing(series):
            if m["ticker"] in done: continue
            close = ts(m["close_time"]); look_end = close - lead_days(series) * 86400
            c = None
            for path in (f"/historical/markets/{m['ticker']}/candlesticks", f"/series/{series}/markets/{m['ticker']}/candlesticks"):
                try:
                    c = api._get(path, {"start_ts": look_end - 4 * 86400, "end_ts": look_end, "period_interval": 60}).get("candlesticks", [])
                    if c: break
                except Exception:
                    c = None
            ask = bid = None; et = None
            for r in sorted(c or [], key=lambda r: r["end_period_ts"]):
                a, b = api.f((r.get("yes_ask") or {}).get("close")), api.f((r.get("yes_bid") or {}).get("close"))
                if r["end_period_ts"] <= look_end and a is not None and b is not None and 0 <= b < a <= 1 and a - b <= MAXQ:
                    ask, bid, et = a, b, r["end_period_ts"]
            f.write(json.dumps(dict(ticker=m["ticker"], series=series, event=m["event_ticker"], close=m["close_time"], result=m["result"], ask=ask, bid=bid, look=et, ncandles=len(c or []))) + "\n"); f.flush()


def boot(vals, clusters, n=2000, seed=1):
    rnd = random.Random(seed); keys = sorted(set(clusters)); by = collections.defaultdict(list)
    for v, c in zip(vals, clusters): by[c].append(v)
    ms = []
    for _ in range(n):
        s = []
        for k in (rnd.choice(keys) for _ in keys): s += by[k]
        ms.append(sum(s) / len(s))
    ms.sort(); return ms[int(.025 * n)], ms[int(.975 * n)]


def cmd_score(out):
    rows = [json.loads(l) for l in open(out)]
    team = lambda r: r["series"] + "|" + r["close"][:4] if False else r["series"] + "|" + ("25" if r["close"] < "2026-02" else "26")
    elig = [r for r in rows if r["ask"] is not None and LO <= r["ask"] <= HI]
    byev = collections.defaultdict(list)
    for r in elig: byev[r["event"]].append(r)
    pick = []
    for e, rs in byev.items():
        pick += sorted(rs, key=lambda r: hashlib.sha1(r["ticker"].encode()).hexdigest())[:3]
    def net(r, mult=1.0):
        win = r["result"] == "yes"
        return (100 if win else 0) / 100.0 - r["ask"] - fee(r["ask"]) * mult
    pick.sort(key=lambda r: r["close"])
    print("markets", len(rows), "with look", sum(1 for r in rows if r["ask"] is not None), "cheap", len(elig), "picked (cap 3/event)", len(pick))
    print("events", len(byev), "team-seasons", len({team(r) for r in elig}), "picked team-seasons", len({team(r) for r in pick}))
    res = {}
    for name, S in (("ALL", pick), ("D1", pick[:len(pick) // 2]), ("D2", pick[len(pick) // 2:]), ("NFL", [r for r in pick if r["series"].startswith("KXNFL")]), ("MLB", [r for r in pick if r["series"].startswith("KXMLB")]), ("NBA", [r for r in pick if r["series"].startswith("KXNBA")])):
        if not S: continue
        v = [net(r) for r in S]; v12 = [net(r, 1.2) for r in S]
        w = sum(1 for r in S if r["result"] == "yes"); ask = sum(r["ask"] for r in S) / len(S)
        gp = sum(x for x in v if x > 0); gl = -sum(x for x in v if x < 0)
        lo, hi = boot(v, [team(r) for r in S])
        res[name] = dict(n=len(S), wins=w, mean_ask=round(ask * 100, 2), win_rate=round(100 * w / len(S), 2), net_c=round(100 * sum(v) / len(S), 2), net_c_fee12=round(100 * sum(v12) / len(S), 2), pf=round(gp / gl, 2) if gl else None, boot_lo_c=round(100 * lo, 2), boot_hi_c=round(100 * hi, 2))
        print(name, res[name])
    json.dump(res, open(out.replace(".jsonl", "_score.json"), "w"), indent=1)


if __name__ == "__main__":
    if sys.argv[1] == "fetch": cmd_fetch(sys.argv[2], sys.argv[3])
    else: cmd_score(sys.argv[2])
