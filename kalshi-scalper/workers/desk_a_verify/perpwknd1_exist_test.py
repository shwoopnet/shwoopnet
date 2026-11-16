"""python3 -I perpwknd1_exist_test.py : the existence count on an invented 3 name weekend (usable, missing Sunday, no ask on Monday)."""
import sys, os, gzip, csv, tempfile, datetime, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perpwknd1_exist as X, engine1_perps as P
base = tempfile.mkdtemp(); os.makedirs(base + "/kalshi1m")
f = datetime.date(2026, 11, 6); tms = [X.et_epoch(f, 16), X.et_epoch(datetime.date(2026, 11, 8), 18), X.et_epoch(datetime.date(2026, 11, 9), 10)]
assert [(t - P.et_day0(t)) // 3600 for t in tms] == [16, 18, 10] and [t % 86400 // 3600 for t in tms] == [21, 23, 15]      # EST: 16:00 ET is 21:00Z
def w(d, rows):
    with gzip.open("%s/kalshi1m/%s.csv.gz" % (base, d), "wt") as fh:
        wr = csv.writer(fh); wr.writerow(["ticker", "end_period_ts", "bid_close", "ask_close"]); wr.writerows(rows)
w("2026-11-06", [("KXAAAPERP", tms[0], 100.0, 100.1), ("KXBBBPERP", tms[0], 50.0, 50.1), ("KXCCCPERP", tms[0], 10.0, 10.1)])
w("2026-11-08", [("KXAAAPERP", tms[1], 101.0, 101.2), ("KXCCCPERP", tms[1], 10.1, 10.2)])
w("2026-11-09", [("KXAAAPERP", tms[2], 100.5, 100.7), ("KXBBBPERP", tms[2], 50.0, 50.1), ("KXCCCPERP", tms[2], 10.0, 922337203685477.5807)])
tsv = base + "/pm.tsv"; open(tsv, "w").write("ticker\tclass\tpage_max\nKXAAAPERP\tEquities\t4\nKXBBBPERP\tEquities\t4\nKXCCCPERP\tIndices\t4\nKXDDDPERP\tCrypto\t4\n")
X.main(base, tsv, "2026-11-06", "2026-11-06", base + "/o.json", check_allow=False); r = json.load(open(base + "/o.json"))
assert r["total_usable_name_weekends"] == 1 and r["weekends"]["2026-11-06"]["counts"]["Equities:listed"] == 2
fb = r["weekends"]["2026-11-06"]["fail_by_leg_reason"]; assert fb["Equities:sun18:missing"] == 1 and fb["Indices:mon10:unusable"] == 1, fb
try: X.main(base, tsv, "2026-11-06", "2026-11-06", base + "/o2.json"); raise AssertionError("ran without an allow line")
except SystemExit: pass
print("PERPWKND1 EXISTENCE COUNT OK")
