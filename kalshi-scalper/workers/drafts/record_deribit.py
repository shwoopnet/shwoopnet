#!/usr/bin/env python3
"""DERIBIT1 recorder (draft, research only). Public keyless GETs only: Deribit index price and option book summaries, Kalshi KXBTCD open ladder quotes.
Polls every STEP seconds for DURATION seconds and writes one CSV row per Kalshi strike (7 nearest the index) per poll. No key, no order, no account.
Usage: record_deribit.py OUTDIR [--duration 450] [--step 5]"""
import csv, json, os, re, sys, time, urllib.request
from datetime import datetime, timezone
UA = "shwoopnet-research-recorder"
KAL = "https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=200&series_ticker=KXBTCD"
DER = "https://www.deribit.com/api/v2/public/"
def get(url):
    r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=20)
    return json.load(r)
def now(): return datetime.now(timezone.utc)
def main():
    out = sys.argv[1]; dur = int(sys.argv[sys.argv.index("--duration") + 1]) if "--duration" in sys.argv else 450
    step = int(sys.argv[sys.argv.index("--step") + 1]) if "--step" in sys.argv else 5
    os.makedirs(out, exist_ok=True)
    f = open(os.path.join(out, "deribit_kalshi.csv"), "w", newline=""); w = csv.writer(f)
    w.writerow(["t_utc", "index", "opt_expiry", "opt_strike", "mark_iv_call", "mark_iv_put", "event", "close_time", "strike", "yes_bid", "yes_ask"])
    end = time.time() + dur; fails = 0
    while time.time() < end:
        t0 = time.time()
        try:
            idx = float(get(DER + "get_index_price?index_name=btc_usd")["result"]["index_price"])
            summ = get(DER + "get_book_summary_by_currency?currency=BTC&kind=option")["result"]
            best = {}
            for s in summ:
                m = re.match(r"BTC-(\d+[A-Z]{3}\d+)-(\d+)-([CP])", s["instrument_name"])
                if not m or s.get("mark_iv") is None: continue
                exp = datetime.strptime(m.group(1), "%d%b%y").replace(hour=8, tzinfo=timezone.utc)
                if exp <= now(): continue
                best.setdefault(exp, {})[(int(m.group(2)), m.group(3))] = s["mark_iv"]
            exp = min(best); strikes = sorted({k[0] for k in best[exp]}, key=lambda k: abs(k - idx))[0]
            ivc, ivp = best[exp].get((strikes, "C")), best[exp].get((strikes, "P"))
            ms = get(KAL).get("markets", [])
            ms = [m for m in ms if m.get("close_time") and datetime.fromisoformat(m["close_time"].replace("Z", "+00:00")) > now()]
            ev = min({m["event_ticker"]: m["close_time"] for m in ms}.items(), key=lambda kv: kv[1])[0]
            near = sorted([m for m in ms if m["event_ticker"] == ev and m.get("floor_strike") is not None], key=lambda m: abs(float(m["floor_strike"]) - idx))[:7]
            for m in near:
                w.writerow([now().isoformat(timespec="seconds"), idx, exp.date(), strikes, ivc, ivp, ev, m["close_time"], m["floor_strike"], m.get("yes_bid_dollars"), m.get("yes_ask_dollars")])
            f.flush(); fails = 0
        except Exception as e:
            fails += 1; print("poll failed", str(e)[:80], flush=True)
            if fails >= 3: print("3 failures in a row, stopping (rate limit or outage); not worked around"); break
            time.sleep(30)
        time.sleep(max(0, step - (time.time() - t0)))
    f.close()
main()
