"""Test of the BTC page reader on INVENTED pages (no real data). python3 -I mech1_generate_btc_test.py"""
import os, sys, gzip, json, random, tempfile, hashlib, datetime
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import mech1_generate_btc as B, mech1_generate as G
random.seed(3); base = tempfile.mkdtemp(); d0 = datetime.date(2026, 6, 3); rows = []
for k in range(1, 164):
    d = d0 + datetime.timedelta(days=k - 1); ts0 = int(datetime.datetime(d.year, d.month, d.day, tzinfo=datetime.timezone.utc).timestamp())
    fn = "%04d.json.gz" % k; p = os.path.join(base, fn)
    if k > B.LAST_PAGE: open(p, "wb").write(b"NOT A GZIP FILE: a held-out page must never be opened")
    else:
        cs = []; price = 60000.0; oi = 5000.0
        if k == 5: price = 60000.0
        for m in range(1, 1441):
            if random.random() < 0.3: continue                                           # absent minutes
            price *= 1 + random.gauss(0, 0.0004); oi *= 1 + random.gauss(0, 0.003); v = abs(random.gauss(20, 8)) + (200 if random.random() < 0.02 else 0)
            cs.append({"end_period_ts": ts0 + 60 * m, "bid": {"open": "%.2f" % (price - 1), "close": "%.2f" % (price - 1)}, "ask": {"open": "%.2f" % (price + 1), "close": "%.2f" % (price + 1)}, "price": {}, "volume": "%.2f" % v, "open_interest": "%.2f" % oi})
        cs.append(dict(cs[-1]))                                                          # a repeated boundary candle
        with gzip.open(p, "wt") as fo: json.dump({"candlesticks": cs, "ticker": "KXBTCPERP"}, fo)
    rows.append({"index": k, "id": "KXBTCPERP_" + d.isoformat(), "status": 200, "file": fn, "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "truncated": False})
json.dump({"job": {}, "rows": rows}, open(os.path.join(base, "manifest.json"), "w"))
allow = os.path.join(base, "ALLOW.md"); B.ALLOW_FILE = allow; out = os.path.join(base, "rec.jsonl")
open(allow, "w").write("nothing\n")
try: B.main(base, out); raise SystemExit("ran without an allow line")
except SystemExit as e: assert str(e).startswith("REFUSED"), e
open(allow, "w").write(B.ALLOW_MARK + " mech1_generate_btc.py " + B.sha(B.__file__) + " " + B.sha(os.path.join(base, "manifest.json")) + "\n")
B.main(base, out)                                                                        # raises if page 109 or later is opened
L = [json.loads(x) for x in open(out)]; heads = [x for x in L if "sig" in x]; trades = [x for x in L if "sig" not in x]
assert len(heads) == 4 and all(h["sig"]["market"] == "crypto_perp" and h["half1_to"] == "2026-07-26" for h in heads), len(heads)
assert trades and all("2026-06-03" <= t["day"] <= "2026-09-18" for t in trades)
lg = json.load(open(out + ".log.json")); assert lg["pages_read"] == 108 and lg["counts"].get("candle_duplicate_first_kept", 0) >= 100, lg
# a page whose sha does not match its manifest row is refused
rows[2]["sha256"] = "0" * 64; json.dump({"job": {}, "rows": rows}, open(os.path.join(base, "manifest.json"), "w"))
open(allow, "w").write(B.ALLOW_MARK + " mech1_generate_btc.py " + B.sha(B.__file__) + " " + B.sha(os.path.join(base, "manifest.json")) + "\n")
try: B.main(base, out); raise SystemExit("accepted a page with a wrong sha")
except SystemExit as e: assert "manifest sha256" in str(e), e
print("ok: 4 signatures, %d trade lines, held-out pages never opened, bad page refused" % len(trades))
