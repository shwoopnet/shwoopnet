"""Hand case for fundx2_thresholds.py: a tiny INVENTED funding file with known cuts, an invented allow file, a temp output. No real data."""
import gzip, hashlib, json, os, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perps_crypto_load as L, perps_crypto_run as R, fundx2_events as F, fundx2_thresholds as TH
d = tempfile.mkdtemp(); sh = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
iso = lambda t: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
rows = ["ticker,funding_time,funding_rate,mark_price"]
for i in range(200):                                   # BTC: 200 SEARCH prints, rates 1..200 (invented)
    rows.append("KXBTCPERP,%s,%s,100" % (iso(F.SEARCH_START + 28800 * i), float(i + 1)))
rows.append("KXBTCPERP,%s,500.0,100" % iso(F.SEARCH_END + 3600))     # a VALIDATE print above the 5 percent upper cut (191)
rows.append("KXBTCPERP,%s,-3.0,100" % iso(F.SEARCH_END + 7200))      # a VALIDATE print below zero (not an upper-tail extreme; lower cut is 10, but rate < 0 and 10 > 0 so lower needs rate <= 10 and < 0: yes -3 is at or below 10 and below 0)
for i in range(50):                                    # ETH: only 50 SEARCH prints: no threshold
    rows.append("KXETHPERP,%s,%s,100" % (iso(F.SEARCH_START + 28800 * i), float(i + 1)))
rows.append("KXBNBPERP,%s,9.0,100" % iso(F.SEARCH_START + 3600))      # BNB is outside the six: dropped by the loader wall
fund = os.path.join(d, "f.csv.gz"); open(fund, "wb").write(gzip.compress("\n".join(rows).encode()))
allow = os.path.join(d, "A.md"); L.ALLOW_FILE = allow; out = os.path.join(d, "T.json")
open(allow, "w").write("nothing\n")
try: TH.main(fund, out); raise AssertionError("must refuse with no allow line")
except SystemExit as e: assert "REFUSED" in str(e)
hs = [sh(TH.__file__), R.self_sha(), L.self_sha(), sh(os.path.join(os.path.dirname(TH.__file__), "fundx2_events.py")), sh(fund)]
for drop in range(5):                                  # any one hash missing refuses
    open(allow, "w").write(" ".join([L.ALLOW_MARK, "fundx2_thresholds.py", "perps_crypto_run.py"] + [h for i, h in enumerate(hs) if i != drop]) + "\n")
    try: TH.main(fund, out); raise AssertionError("must refuse, dropped %d" % drop)
    except SystemExit as e: assert "REFUSED" in str(e)
# the run's own line needs its own mark/names too: one line carries everything
open(allow, "w").write(" ".join([L.ALLOW_MARK, "fundx2_thresholds.py", "perps_crypto_run.py", "perps_crypto_load.py"] + hs) + "\n")
h = TH.main(fund, out); assert h == sh(out)
doc = json.load(open(out)); b = doc["cuts"]["KXBTCPERP"]["5"]
assert (b["lower"], b["upper"], b["search_n"], b["has_threshold"]) == (10.0, 191.0, 200, True), b
c10 = doc["cuts"]["KXBTCPERP"]["10"]; assert (c10["lower"], c10["upper"]) == (20.0, 181.0)
# extremes: SEARCH prints at or above 191 and above 0: 10 (191..200); the lower tail needs rate < 0: none. VALIDATE: 500 is an extreme (upper), -3 is a lower extreme (-3 <= 10 and < 0)
assert b["search_extremes"] == 10 and b["validate_prints"] == 2 and b["validate_extremes"] == 2, b
assert doc["cuts"]["KXETHPERP"]["5"]["has_threshold"] is False and doc["cuts"]["KXETHPERP"]["5"]["lower"] is None and doc["cuts"]["KXETHPERP"]["5"]["search_n"] == 50
assert doc["cuts"]["KXSOLPERP"]["5"]["search_n"] == 0 and "KXBNBPERP" not in doc["cuts"] and doc["load_counts"].get("funding ticker outside the window (dropped)", 0) >= 0
txt = open(out).read()
assert "500.0" not in txt and "mark_price" not in txt and "funding_time" not in txt          # no per-print rate, time or mark price in the output
print("fundx2 thresholds: ok")
