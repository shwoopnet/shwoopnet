#!/usr/bin/env python3 -I
"""Forward read of the registered S1 split (PAXG spot vs Kalshi gold ask) on GOLDALL shadow rows. Read only, keyless.
Usage: python3 -I spot_split.py ROWS.json [--cache DIR] [--now-ms N]   |   python3 -I spot_split.py --demo --scratch S
Input: JSON list of shadow rows (rule, ticker, series, side, price, size, secondsLeft, closeTime, atMs, wouldFill, pnl) or any JSON holding them.
S1 at read time (as W-SPOTGOLD1): ref = PAXG close at window start (close-900); spot = close of the minute ending at or before atMs (ffill <=5 min);
d=ln(spot/ref); sigma=sd of previous 60 one-minute log returns; z=d/(sigma*sqrt(secondsLeft/60)); p_model=Phi(|z|); S1 = side==sign(d) and p_model-price>=0.02.
Rows with a missing candle beyond 5 min are 'unscored' (reported, never imputed). Fee 0.07*p*(1-p) unrounded. Pnl from the row, else the public market result."""
import json, math, sys, os, time, glob, urllib.request, urllib.error, datetime as D
CB = "https://api.exchange.coinbase.com/products/PAXG-USD/candles"
KM = "https://api.elections.kalshi.com/trade-api/v2/markets/"
CHUNK = 300 * 60
Phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))
fee = lambda p: 0.07 * p * (1 - p)
_last = [0.0]

def get(url, tries=6):
    wait = 1.0
    for _ in range(tries):
        dt = time.time() - _last[0]
        if dt < 0.34: time.sleep(0.34 - dt)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "spot-split/1"})
            with urllib.request.urlopen(req, timeout=20) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(wait); wait = min(wait * 2, 30); continue
            return None
        except Exception:
            time.sleep(wait); wait = min(wait * 2, 30)
    return None

class Candles:
    def __init__(s, cache, extra=(), offline=False):
        s.cache, s.cl, s.offline, s.done = cache, {}, offline, set()
        os.makedirs(cache, exist_ok=True)
        for d in (cache, *extra):
            for f in glob.glob(os.path.join(d, "*.json")):
                try:
                    for r in json.load(open(f)): s.cl[int(r[0])] = float(r[4])
                except Exception: pass
    def need(s, a, b, now):
        c = a - a % CHUNK
        while c < b:
            if c not in s.done:
                s.done.add(c)
                have = sum(1 for t in range(c, c + CHUNK, 60) if t in s.cl)
                if have < CHUNK // 60 * 0.5 and not s.offline:
                    end = min(c + CHUNK, now)
                    iso = lambda t: D.datetime.fromtimestamp(t, D.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    j = get("%s?granularity=60&start=%s&end=%s" % (CB, iso(c), iso(end)))
                    if isinstance(j, list):
                        for r in j: s.cl[int(r[0])] = float(r[4])
                        if c + CHUNK <= now - 60: json.dump(j, open(os.path.join(s.cache, "c%d.json" % c), "w"))
                    else: s.done.discard(c)
            c += CHUNK
    def spot(s, end, maxgap=5):  # close of the minute ending at or before `end`; only candles that ended by then
        for i in range(maxgap + 1):
            v = s.cl.get(end - 60 - 60 * i)
            if v is not None: return v

def find_rows(o, out):
    if isinstance(o, dict):
        if "rule" in o and "ticker" in o and "atMs" in o: out.append(o)
        else:
            for v in o.values(): find_rows(v, out)
    elif isinstance(o, list):
        for v in o: find_rows(v, out)
    return out

def pf(v):
    g = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return None if not v else (g / l if l else float("inf"))
F = lambda x: "n/a" if x is None else ("inf" if x == float("inf") else "%.2f" % x)

def score(rows, cd, now, outcome):
    res = []
    for r in rows:
        try:
            look = int(r["atMs"] // 1000); end = look - look % 60
            cm = r["closeTime"]; close = int(D.datetime.fromisoformat(cm.replace("Z", "+00:00")).timestamp()) if isinstance(cm, str) else int(cm // 1000 if cm > 1e11 else cm)
            p = float(r["price"]); side = r["side"]
            cd.need(close - 900 - 600, end + 60, now)
            ref = cd.spot(close - 900); sp = cd.spot(end)
            ps = [cd.spot(end - 60 * i) for i in range(61)]
            if ref is None or sp is None or any(x is None for x in ps): res.append(dict(r=r, s1=None)); continue
            rets = [math.log(ps[i] / ps[i + 1]) for i in range(60)]
            mu = sum(rets) / 60; sd = math.sqrt(sum((x - mu) ** 2 for x in rets) / 59)
            if sd == 0: res.append(dict(r=r, s1=None)); continue
            d = math.log(sp / ref); z = d / (sd * math.sqrt(max(float(r["secondsLeft"]), 1) / 60))
            pm = Phi(abs(z)); sgn = "yes" if d > 0 else "no"
            s1 = side == sgn and pm - p >= 0.02
            won = outcome(r)
            pnl = None if won is None else ((1 - p) if won else -p) - fee(p)
            res.append(dict(r=r, s1=s1, pnl=pnl, t=r["atMs"]))
        except Exception:
            res.append(dict(r=r, s1=None))
    return res

def report(res):
    rules = sorted({x["r"]["rule"] for x in res})
    for rule in rules:
        xs = [x for x in res if x["r"]["rule"] == rule]
        un = [x for x in xs if x["s1"] is None]
        sc = [x for x in xs if x["s1"] is not None and x.get("pnl") is not None]
        s1 = [x for x in sc if x["s1"]]; ns = [x for x in sc if not x["s1"]]
        pend = len([x for x in xs if x["s1"] is not None and x.get("pnl") is None])
        print("rule %s: signals %d | S1 n %d, not-S1 n %d, unscored %d, scored-unsettled %d" % (rule, len(xs), len(s1), len(ns), len(un), pend))
        cut = sorted(x["t"] for x in sc)[len(sc) // 2] if sc else 0
        for nm, g in (("ALL scored", sc), ("S1", s1), ("not-S1", ns)):
            v = [x["pnl"] for x in g]
            a = [x["pnl"] for x in g if x["t"] < cut]; b = [x["pnl"] for x in g if x["t"] >= cut]
            print("  %-10s PF %s (n %d) net %+.2fc/contract | half1 %s (%d) half2 %s (%d)" % (nm, F(pf(v)), len(v), 100 * sum(v) / len(v) if v else 0, F(pf(a)), len(a), F(pf(b)), len(b)))
        v = [x["pnl"] for x in s1]; b = [x["pnl"] for x in s1 if x["t"] >= cut]
        net = 100 * sum(v) / len(v) if v else 0
        print("  registered pass: S1 PF>=1.3 over >=60 S1 signals and 2nd half PF>=1.2; kill: net < -1c/contract after 50 S1 signals")
        if len(v) >= 50 and net < -1: st = "KILL: S1 net %+.2fc after %d signals" % (net, len(v))
        elif len(v) >= 60 and (pf(v) or 0) >= 1.3 and (pf(b) or 0) >= 1.2: st = "PASS: S1 PF %s, half2 %s over %d" % (F(pf(v)), F(pf(b)), len(v))
        else: st = "COLLECTING: %d of 60 S1 signals, PF %s" % (len(v), F(pf(v)))
        print("  STATUS " + st)

def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    demo = "--demo" in a
    S = opt("--scratch", "/tmp")
    now = int(int(opt("--now-ms", time.time() * 1000)) // 1000)
    if demo:
        print("*** DEMO: rows rebuilt from the gold candle cache (historical, not forward shadow rows) ***")
        cd = Candles(os.path.join(S, "w_spottool/cache"), extra=[os.path.join(S, "w_spotgold/cache")], offline=True)
        W = {}
        for l in open(os.path.join(S, "w_indep3/gold_hist.jsonl")):
            r = json.loads(l)
            if r["res"] in ("yes", "no") and "360" in r["c"]:
                b, ak = map(float, r["c"]["360"]); W[r["t"]] = (r["close"], r["res"], b, ak)
            elif r["res"] in ("yes", "no"): W.setdefault(r["t"], (r["close"], r["res"], None, None))
        for fn in ("oi/gold.jsonl", "w_golddecay/ext2_gold.jsonl"):
            for l in open(os.path.join(S, fn)):
                r = json.loads(l)
                if r.get("r") not in ("yes", "no"): continue
                k = {int(q["e"]): q for q in r["k"] if q.get("ac") and q.get("bc")}.get(r["c"] - 360)
                W[r["t"]] = (r["c"], r["r"], float(k["bc"]) if k else None, float(k["ac"]) if k else None)
        rows = []; truth = {}
        for t, (c, res, b, ak) in W.items():
            if b is None or not (0 < b < ak < 1): continue
            y, n = ak, 1 - b; side = "yes" if y >= n else "no"; p = y if side == "yes" else n
            if not .88 - 1e-9 <= p <= .97 + 1e-9: continue
            rows.append(dict(rule="GOLDALL", ticker=t, series="KXGOLD15M", side=side, price=round(p, 4), size=1, secondsLeft=360, closeTime=D.datetime.fromtimestamp(c, D.timezone.utc).isoformat(), atMs=(c - 360) * 1000, wouldFill=True))
            truth[t] = res
        outcome = lambda r: truth[r["ticker"]] == r["side"]
    else:
        src = [x for x in a if not x.startswith("--") and a[a.index(x) - 1] not in ("--cache", "--now-ms", "--scratch")]
        if not src: sys.exit(__doc__)
        rows = [x for x in find_rows(json.load(open(src[0])), []) if x.get("rule") == "GOLDALL"]
        cd = Candles(opt("--cache", "./spot_cache"))
        memo = {}
        def outcome(r):
            if r.get("pnl") is not None: return float(r["pnl"]) > 0
            t = r["ticker"]
            if t not in memo:
                j = get(KM + t); m = (j or {}).get("market", {}); memo[t] = m.get("result") if m.get("result") in ("yes", "no") else None
            return None if memo[t] is None else memo[t] == r["side"]
    report(score(rows, cd, now, outcome))
main()
