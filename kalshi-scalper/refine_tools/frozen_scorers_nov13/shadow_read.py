#!/usr/bin/env python3 -I
"""Read shadow rows (collection kalshiShadowRows) and print one status line per rule.
Input: rows JSON (a list of row objects, or {"rows": [...]}) or a nightly report JSON (uses report.shadow.rules as is,
since the report carries per-rule aggregates only, not rows). --demo uses FABRICATED rows (DEMO).
Row fields used (functions/kalshiShadowLib.js): rule, ticker, side, price, wouldFill, atMs, closeMs, settled, result, pnl.
Settlement: the logger writes result/won/pnl itself once settled. For unsettled rows with closeMs 2+ min past, --settle looks up the
public GET https://api.elections.kalshi.com/trade-api/v2/markets/<ticker> (no key; field market.result) with a cache and rate limit.
Cash per contract: 1-p-fee if side==result else -p-fee, unrounded fee 0.07*p*(1-p). No token is read or printed."""
import json, sys, time, random, urllib.request, os
DAY = 86400000
RULES = ["ETHNO6","BTCHI6","XRPYES10","ETHL1","GOLDALL","XRPFAV6","GOLDHI6S","BTCHI10","XRPFAV10"]
API = "https://api.elections.kalshi.com/trade-api/v2/markets/"

def fee(p): return 0.07 * p * (1 - p)
def cash(side, p, res): return (1 - p - fee(p)) if side == res else (-p - fee(p))
def pf(v):
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return None if l == 0 else w / l
def f(x): return "n/a" if x is None else "%.2f" % x

def lookup(ticker, cache, path, gap=0.6):
    if ticker in cache: return cache[ticker]
    time.sleep(gap)
    try:
        with urllib.request.urlopen(API + ticker, timeout=10) as r:
            res = (json.load(r).get("market", {}).get("result") or "").lower()
    except Exception:
        return None  # retry next run; not cached
    if res in ("yes", "no"):
        cache[ticker] = res
        json.dump(cache, open(path, "w"))
        return res
    return None

def score(rid, rows, now):
    mine = sorted([r for r in rows if r.get("rule") == rid], key=lambda r: r["atMs"])
    sig = len(mine)
    if not sig: return "%-9s no signals yet: collecting" % rid
    days = (now - mine[0]["atMs"]) / DAY
    perwk = sig / max(days, 1e-9) * 7 if days >= 1 else None
    fillshare = sum(1 for r in mine if r.get("wouldFill") is True) / sig
    st = [r for r in mine if r.get("pnl") is not None and r.get("wouldFill") is True]
    v = [r["pnl"] for r in st]
    n = len(v); a = pf(v)
    h = pf(v[n // 2:]) if n >= 2 else None
    first = pf(v[:n // 2]) if n >= 2 else None
    net = sum(v); byday = {}
    for r in st: byday[r["atMs"] // DAY] = byday.get(r["atMs"] // DAY, 0) + r["pnl"]
    top = max(byday.values()) / net if net > 0 else None
    netc = net / n * 100 if n else None
    l30 = sum(1 for r in mine if r["atMs"] >= now - 30 * DAY)
    s = "collecting"
    if n >= 50 and netc < -1: s = "KILL net %.1fc/contract after %d" % (netc, n)
    elif days >= 30 and l30 < 40: s = "RETIRE %d signals in 30d" % l30
    elif n >= 150 and days >= 14 and a and a >= 1.3 and h and h >= 1.2 and top is not None and top <= 0.3: s = "READY pass rule met"
    return "%-9s sig %d (%s/wk) fill %.0f%% settled %d PF %s halves %s/%s top-day %s days %.1f -> %s" % (
        rid, sig, "%.1f" % perwk if perwk else "n/a", fillshare * 100, n, f(a), f(first), f(h),
        "n/a" if top is None else "%.0f%%" % (top * 100), days, s)

def demo():
    random.seed(7); now = 1_800_000_000_000; rows = []
    for i, rid in enumerate(RULES):
        for k in range(30 + 20 * i):
            p = round(random.uniform(.88, .97), 2); side = random.choice(["yes", "no"])
            res = side if random.random() < p + 0.02 else ("no" if side == "yes" else "yes")
            at = now - 20 * DAY + k * (20 * DAY // (30 + 20 * i))
            rows.append(dict(rule=rid, ticker="DEMO-%s-%d" % (rid, k), side=side, price=p, wouldFill=random.random() < .8,
                             atMs=at, closeMs=at + 400000, settled=True, pnl=round(cash(side, p, res), 4)))
    return rows, now

def main(a):
    if "--demo" in a:
        rows, now = demo(); print("DEMO: fabricated rows, not real results")
    else:
        paths = [x for x in a if not x.startswith("--")]
        if not paths: sys.exit("usage: shadow_read.py FILE.json [--settle] | --demo")
        d = json.load(open(paths[0])); now = int(time.time() * 1000)
        if isinstance(d, dict) and "rows" not in d:
            for r in (d.get("shadow") or {}).get("rules", []):
                print("%-9s sig %s settled %s PF %s fillablePF %s net %sc days %s -> %s (report aggregate)" % (
                    r["rule"], r["signals"], r["settled"], r["pf"], r["pfFillable"], r["netCentsPerContract"], r["days"], r["status"]))
            return
        rows = d["rows"] if isinstance(d, dict) else d
        if "--settle" in a:
            cp = os.path.join(os.path.dirname(os.path.abspath(paths[0])), "shadow_result_cache.json")
            cache = json.load(open(cp)) if os.path.exists(cp) else {}
            for r in rows:
                if r.get("pnl") is None and r.get("closeMs", 9e18) + 120000 <= now:
                    res = lookup(r["ticker"], cache, cp)
                    if res: r["pnl"] = round(cash(r["side"], r["price"], res), 4)
    for rid in RULES: print(score(rid, rows, now))
main(sys.argv[1:])
