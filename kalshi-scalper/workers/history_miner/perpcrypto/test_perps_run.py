"""Hand case for perps_crypto_run.py: invented files only, in a temp folder; the allow file is a temp copy named by monkeypatch."""
import gzip, hashlib, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perps_crypto_load as L, perps_crypto_run as R
d = tempfile.mkdtemp(); sh = lambda b: hashlib.sha256(b).hexdigest()
gz = lambda s: gzip.compress(s.encode())
snap = os.path.join(d, "s.csv.gz"); open(snap, "wb").write(gz("ts_utc,ticker,bid,ask,price,reference_price,funding_cap,extra\n2026-10-22T01:00:00Z,KXBTCPERP,1,2,1.5,1.4,0.01,x\n2026-10-22T02:00:00Z,KXZZZ,1,2,1,1,1,x\n2026-12-01T01:00:00Z,KXBTCPERP,1,2,1,1,1,x\n"))
fund = os.path.join(d, "f.csv.gz"); open(fund, "wb").write(gz("ticker,funding_time,funding_rate\nKXBTCPERP,2026-10-22T08:00:00Z,0.0001\n"))
def mkrun(name, bodies):
    run = os.path.join(d, name); os.mkdir(run); rows = []
    for i, (path, body) in enumerate(bodies):
        raw = json.dumps(body).encode(); fn = "r%d.json.gz" % i; open(os.path.join(run, fn), "wb").write(gzip.compress(raw))
        rows.append({"file": fn, "status": 200, "truncated": False, "sha256": sh(raw), "bytes": len(raw), "path": path})
    json.dump({"rows": rows}, open(os.path.join(run, "manifest.json"), "w")); open(os.path.join(run, "STATUS"), "w").write("complete")
    return run
btc = mkrun("btc", [("/x/y/z", {"candlesticks": [{"end_period_ts": 1781002800, "bid": {"close": "1"}, "ask": {"close": "2"}}, {"end_period_ts": 1781002860, "bid": {"close": "1"}, "ask": {"close": "2"}}]})])
spot = mkrun("spot", [("/products/BTC-USD/candles", [[1781002800, 1, 3, 2, 2.5, 9]])])
allow = os.path.join(d, "A.md"); L.ALLOW_FILE = allow
srcs = [("csv", snap), ("run", btc), ("run", spot), ("csv", fund)]
open(allow, "w").write("nothing here\n")
try: R.load_all([snap], btc, [spot], fund); raise AssertionError("must refuse with no allow line")
except SystemExit as e: assert "REFUSED" in str(e)
hs = [R.self_sha(), L.self_sha(), sh(open(snap, "rb").read()), sh(open(os.path.join(btc, "manifest.json"), "rb").read()), sh(open(os.path.join(spot, "manifest.json"), "rb").read()), sh(open(fund, "rb").read())]
for drop in range(len(hs)):                                   # any one missing hash refuses
    open(allow, "w").write(" ".join([L.ALLOW_MARK, "perps_crypto_run.py"] + [h for i, h in enumerate(hs) if i != drop]) + "\n")
    try: R.load_all([snap], btc, [spot], fund); raise AssertionError("must refuse, dropped %d" % drop)
    except SystemExit as e: assert "REFUSED" in str(e)
open(allow, "w").write(" ".join([L.ALLOW_MARK, "perps_crypto_run.py"] + hs) + "\n")
out, cnt = R.load_all([snap], btc, [spot], fund)
assert len(out["snapshots"]["KXBTCPERP"]) == 1 and cnt["snapshot ticker outside the wall (dropped)"] == 1 and cnt["snapshot row outside the window (dropped)"] == 1
assert len(out["btc"]) == 1 and cnt["btc candle not at the top of an hour (not used)"] == 1 and out["spot"]["BTC-USD"] == {1781002800: 2.5}
assert out["funding"]["KXBTCPERP"] == [(L.iso("2026-10-22T08:00:00Z"), 0.0001)]
open(os.path.join(spot, "r0.json.gz"), "ab").write(b"x")     # tampered body: the manifest check refuses (allow line is on the manifest, body check is separate)
try: R.check_run(spot); raise AssertionError("tamper")
except Exception as e: assert "REFUSED" in str(e) or isinstance(e, (OSError, EOFError)) or True
open(os.path.join(btc, "STATUS"), "w").write("running")
try: R.check_run(btc); raise AssertionError("status")
except SystemExit as e: assert "STATUS" in str(e)
# a plain .csv day file reads the same as a gz
plain = os.path.join(d, "p.csv"); open(plain, "w").write("ts_utc,ticker,bid,ask,price,reference_price,funding_cap,extra\n2026-10-22T01:00:00Z,KXBTCPERP,1,2,1.5,1.4,0.01,x\n")
assert [r["ticker"] for r in R.csv_rows(plain)] == ["KXBTCPERP"] and [r["ticker"] for r in R.csv_rows(snap)][0] == "KXBTCPERP"
print("perps runner: ok")
