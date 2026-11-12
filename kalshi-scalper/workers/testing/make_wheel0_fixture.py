"""Writes a synthetic kalshi-pull style fixture for the WHEEL0 same-output check (lists + candles folders). No real data. Usage: make_wheel0_fixture.py <outdir> [seed]"""
import calendar, gzip, json, os, random, sys, time
out = sys.argv[1]; seed = int(sys.argv[2]) if len(sys.argv) > 2 else 11
rnd = random.Random(seed); os.makedirs(out, exist_ok=True)
def iso(ts): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
def write(folder, bodies):
    os.makedirs(folder, exist_ok=True); rows = []
    for i, b in enumerate(bodies, 1):
        fn = "%04d.json.gz" % i; gzip.open(os.path.join(folder, fn), "wt").write(json.dumps(b)); rows.append({"id": b.get("_id", "r%d" % i), "status": 200, "file": fn})
    json.dump({"rows": rows, "status": "complete", "job": {}}, open(os.path.join(folder, "manifest.json"), "w"))
START = calendar.timegm((2026, 10, 20, 0, 0, 0)); N = 2200            # 23 days of 15 minute markets: Oct 20 to Nov 12, so Bitcoin/Ethereum cross the Oct 29 cut
lists, cands = {}, {}
for ser in ("KXXRP15M", "KXDOGE15M", "KXGOLD15M", "KXETH15M", "KXBTC15M"):
    mk, cd = [], []
    for i in range(N):
        close = START + 900 * (i + 1); t = "%s-%s-15" % (ser, time.strftime("%y%b%d%H%M", time.gmtime(close)).upper())
        mid = 0.08 + 0.84 * rnd.random(); yes = rnd.random() < mid
        mk.append({"ticker": t, "event_ticker": t.rsplit("-", 1)[0], "close_time": iso(close), "open_time": iso(close - 900), "result": "yes" if yes else ("no" if rnd.random() > 0.01 else ""), "strike_type": "greater", "title": "x"})
        series = []
        for L in (600, 360, 180):
            if rnd.random() < 0.03: continue                                   # a missing candle
            sp = rnd.choice([0.01, 0.02, 0.03, 0.04, 0.04, 0.05]); a = min(0.99, round(mid + sp / 2 + rnd.choice([0, 0.01, -0.01]) , 2)); b = max(0.01, round(a - sp, 2))
            series.append({"end_period_ts": close - L, "yes_bid": {"close_dollars": "%.2f" % b}, "yes_ask": {"close_dollars": "%.2f" % a}, "volume_fp": "1"})
        cd.append({"market_ticker": t, "candlesticks": series})
    lists[ser], cands[ser] = mk, cd
write(os.path.join(out, "lists"), [{"markets": v, "_id": "live_" + s} for s, v in lists.items()])
write(os.path.join(out, "candles"), [{"markets": v, "_id": "c_" + s} for s, v in cands.items()])
print("fixture written", out)
