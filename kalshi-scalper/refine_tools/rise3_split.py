#!/usr/bin/env python3 -I
"""rise3_split.py: read-time rise3 split for shadow rows (GOLDALL pre-registered split: |rise3| >= 0.05 moving vs still).

rise3 is computed at read time from PUBLIC one minute candles with the exact live definition (functions/kalshiLiveLib.js riseFromCandles):
mid = (yes_bid close + yes_ask close) / 2, dir = -1 for NO, latest candle must be under 150 s old (relative to the row's atMs), rise3 = dir * (mid_now - mid_(now-180s)).
Public GET only: no key, no auth header, 0.5 s between calls, per-ticker cache, backoff on 429. Missing or stale candles are reported, never imputed.

  python3 -I rise3_split.py rows.json [--cache DIR] [--fill-only]
  python3 -I rise3_split.py --demo SCRATCH_DIR          (DEMO: rows rebuilt from the gold candle cache, no network)
rows.json: a list of shadow rows (rule, ticker, series, side, price, size, secondsLeft, closeTime, atMs, wouldFill, optional result/won/pnl).
"""
import json, os, sys, time, math, urllib.request, urllib.parse, urllib.error

BASE = "https://external-api.kalshi.com/trade-api/v2"
THRESH = 0.05

def rise_from_candles(candles, side, now_sec):
    mids = {}
    for c in candles or []:
        try:
            end = float(c["end_period_ts"]); b = float(c["yes_bid"]["close_dollars"]); a = float(c["yes_ask"]["close_dollars"])
        except (KeyError, TypeError, ValueError):
            continue
        if end <= now_sec + 60: mids[end] = (b + a) / 2
    if not mids: return None, "no candles"
    latest = max(mids)
    if now_sec - latest > 150: return None, "stale"
    then = mids.get(latest - 180)
    if then is None: return None, "no candle 180s earlier"
    d = -1 if side == "no" else 1
    return round(d * (mids[latest] - then), 4), None

_last = [0.0]
def get_candles(row, cache_dir):
    t = row["ticker"]; p = os.path.join(cache_dir, t.replace("/", "_") + ".json")
    if os.path.exists(p): return json.load(open(p))
    close = int(row.get("closeMs", 0) / 1000) if row.get("closeMs") else int(time.mktime(time.strptime(row["closeTime"][:19], "%Y-%m-%dT%H:%M:%S"))) - time.timezone
    q = urllib.parse.urlencode({"start_ts": close - 7200, "end_ts": close + 60, "period_interval": 1})
    url = BASE + "/series/%s/markets/%s/candlesticks?%s" % (urllib.parse.quote(row["series"]), urllib.parse.quote(t), q)
    wait = 2
    for _ in range(6):
        time.sleep(max(0, 0.5 - (time.time() - _last[0]))); _last[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=20) as r:
                cs = json.load(r).get("candlesticks", [])
            json.dump(cs, open(p, "w")); return cs
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(wait); wait = min(wait * 2, 30); continue
            return None
        except Exception:
            return None
    return None

def fee(p): return 0.07 * p * (1 - p)
def pnl_of(row):
    p = float(row["price"]); won = None
    if row.get("result") in ("yes", "no"): won = row["result"] == row["side"]
    elif isinstance(row.get("won"), bool): won = row["won"]
    elif row.get("pnl") is not None: won = float(row["pnl"]) > 0
    if won is None: return None
    return (1 - p - fee(p)) if won else -(p + fee(p))

def pf(v):
    g = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return (g / l) if l else (float("inf") if g else float("nan"))
def cell(v):
    return "n%d PF %.2f net %+.2fc/c" % (len(v), pf(v), 100 * sum(v) / len(v)) if v else "n0"

def report(rule, rows, miss):
    rows = sorted(rows, key=lambda r: r["atMs"]); h = len(rows) // 2
    mv = [r["pnl"] for r in rows if abs(r["rise"]) >= THRESH]; st = [r["pnl"] for r in rows if abs(r["rise"]) < THRESH]
    rises = sum(1 for r in rows if r["rise"] >= THRESH)
    print("RULE %s: signals %d (scored %d, unscored %d)  moving n%d (rises %d)  still n%d" % (rule, len(rows) + len(miss), len(rows), len(miss), len(mv), rises, len(st)))
    print("  moving %s | still %s" % (cell(mv), cell(st)))
    for nm, R in (("H1", rows[:h]), ("H2", rows[h:])):
        print("  %s moving %s | still %s" % (nm, cell([r["pnl"] for r in R if abs(r["rise"]) >= THRESH]), cell([r["pnl"] for r in R if abs(r["rise"]) < THRESH])))
    h2 = [r["pnl"] for r in rows[h:] if abs(r["rise"]) >= THRESH]
    days = (rows[-1]["atMs"] - rows[0]["atMs"]) / 86400000 if rows else 0
    ok = [pf(mv) >= 1.3, len(h2) > 0 and pf(h2) >= 1.2, len(mv) >= 50, len(rows) + len(miss) >= 150, days >= 14]
    print("  PASS TEXT: moving PF>=1.3 [%s], H2 moving PF>=1.2 [%s], moving>=50 [%s], total>=150 [%s], span>=14d [%s] (%.1f d) => %s" % (*("Y" if x else "N" for x in ok), days, "PASS" if all(ok) else "NOT YET/FAIL"))
    net = 100 * sum(mv) / len(mv) if mv else 0
    print("  KILL (moving net < -1c/contract after 50 moving): %s" % ("TRIGGERED" if len(mv) >= 50 and net < -1 else "not triggered (n%d, %+.2fc)" % (len(mv), net)))
    for r in miss: print("  UNSCORED %s atMs %s: %s" % (r["ticker"], r["atMs"], r["why"]))

def demo(S):
    rows = []; seen = set()
    for f in ("oi/gold.jsonl", "w_golddecay/ext2_gold.jsonl"):
        for l in open(os.path.join(S, f)):
            r = json.loads(l)
            if not r.get("k") or r["t"] in seen: continue
            seen.add(r["t"]); m = {k["e"]: k for k in r["k"] if k.get("ac") and k.get("bc")}
            look = r["c"] - 360
            if look not in m: continue
            ac = float(m[look]["ac"]); bc = float(m[look]["bc"])
            if .88 <= ac <= .97: side, price = "yes", ac
            elif .88 <= 1 - bc <= .97: side, price = "no", 1 - bc
            else: continue
            cs = [{"end_period_ts": k["e"], "yes_bid": {"close_dollars": k["bc"]}, "yes_ask": {"close_dollars": k["ac"]}} for k in r["k"] if k.get("ac") and k.get("bc") and k["e"] <= look]
            rows.append(({"rule": "GOLDALL_DEMO", "ticker": r["t"], "series": "KXGOLD15M", "side": side, "price": round(price, 2), "result": r["r"], "atMs": look * 1000, "wouldFill": True}, cs))
    return rows

def main():
    a = sys.argv[1:]
    cache = a[a.index("--cache") + 1] if "--cache" in a else "cache"
    if "--demo" in a:
        print("*** DEMO: rows rebuilt from the gold candle cache, not shadow rows; PF is hold to settlement cash, unrounded fee ***")
        pairs = demo(a[a.index("--demo") + 1])
    else:
        src = [x for x in a if not x.startswith("--") and x != cache][0]
        os.makedirs(cache, exist_ok=True); data = json.load(open(src)); pairs = []
        for r in data:
            if "--fill-only" in a and r.get("wouldFill") is not True: continue
            pairs.append((r, None))
    by = {}
    for r, cs in pairs:
        if cs is None: cs = get_candles(r, cache)
        s = by.setdefault(r["rule"], ([], []))
        if cs is None: s[1].append({**r, "why": "candle read failed"}); continue
        rise, why = rise_from_candles(cs, r["side"], int(r["atMs"] // 1000))
        p = pnl_of(r)
        if rise is None: s[1].append({**r, "why": why}); continue
        if p is None: s[1].append({**r, "why": "no result or pnl yet"}); continue
        s[0].append({**r, "rise": rise, "pnl": p})
    for rule, (rows, miss) in by.items(): report(rule, rows, miss)
main()
