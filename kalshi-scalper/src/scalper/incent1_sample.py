"""Sampler for INCENT1 (registered sampling plan). usage: incent1_sample.py ACTIVE_JSON OUTDIR NPASS GAP_MIN"""
import json, random, sys, time, datetime as D
sys.path.insert(0, __file__.rsplit("/scalper/", 1)[0])
from scalper.incent1 import get

def dt(s): return D.datetime.fromisoformat(s.replace("Z", "+00:00"))

def main(a, out, npass, gap):
    progs = json.load(open(a))
    for p in progs:
        p["days"] = (dt(p["end_date"]) - dt(p["start_date"])).total_seconds() / 86400
        p["pool_day"] = p["period_reward"] / 1e4 / p["days"]
    progs.sort(key=lambda p: p["pool_day"])
    n = len(progs); rng = random.Random(20261103)
    cand = []
    for b in range(6):
        band = progs[b * n // 6:(b + 1) * n // 6]
        cand += rng.sample(band, 60)
    rng.shuffle(cand)
    chosen = []
    for p in cand:
        if len(chosen) >= 240: break
        m = get("/markets/" + p["market_ticker"])
        if not m: continue
        m = m["market"]
        if m.get("status") != "active": continue
        chosen.append(p); time.sleep(0.3)
    json.dump(chosen, open(out + "/chosen.json", "w"))
    print("chosen", len(chosen), flush=True)
    for k in range(npass):
        rows = []
        for p in chosen:
            m = get("/markets/" + p["market_ticker"]); b = get("/markets/%s/orderbook" % p["market_ticker"])
            if m and b:
                mm = m["market"]
                rows.append({"t": time.time(), "ticker": p["market_ticker"], "last": mm.get("last_price_dollars"),
                             "vol24": mm.get("volume_24h_fp"), "bid": mm.get("yes_bid_dollars"), "ask": mm.get("yes_ask_dollars"),
                             "oi": mm.get("open_interest_fp"), "status": mm.get("status"), "book": b["orderbook_fp"]})
            time.sleep(0.25)
        json.dump(rows, open("%s/pass%d.json" % (out, k), "w"))
        print("pass", k, len(rows), flush=True)
        if k < npass - 1: time.sleep(gap * 60)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]))
