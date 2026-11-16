import csv, gzip, hashlib, os, shutil, tempfile
import lane4_load as L
t = tempfile.mkdtemp(); os.makedirs(os.path.join(t, "kalshi1m")); os.makedirs(os.path.join(t, "funding"))
def wgz(rel, header, rows):
    with gzip.open(os.path.join(t, rel), "wt", newline="") as fh: w = csv.writer(fh); w.writerow(header); w.writerows(rows)
CH = ["ticker", "end_period_ts", "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close"]
def crow(tk, e, b, a): return [tk, e, 9, 9, 9, b, 9, 9, 9, a]
g, s, o = "KXGOLDPERP", L.STOCKS[0], "KXBTCPERP"
wgz("kalshi1m/2026-09-10.only.csv.gz", CH, [crow(g, L.START3, 1.0, 1.1), crow(g, L.START3 - 60, 2.0, 2.1), crow(o, L.START3, 7.0, 7.1), crow(g, L.START3 + 60, "", 1.2), crow(g, L.CUT, 5.0, 5.1), crow(g, L.CUT - 60, 3.0, 3.1)])
wgz("kalshi1m/2026-11-06.csv.gz", CH, [crow(s, L.START_STOCK, 10.0, 10.1), crow(s, L.START_STOCK - 60, 11.0, 11.1), crow(s, L.START_STOCK + 60, 12.0, 12.1), crow(s, L.START_STOCK + 60, 12.5, 12.6), crow(g, L.START3 + 120, 4.0, 4.1)])
FH = ["ticker", "funding_time", "funding_rate", "mark_price"]
wgz("funding/2026-11-06.csv.gz", FH, [[s, "2026-11-07T21:00:00Z", "0.0001", "99"], [s, "2026-11-08T21:00:00Z", "0.0002", "99"], [s, "2026-11-01T21:00:00Z", "0.0003", "99"], [s, "2026-11-04T21:00:00Z", "0.0004", "99"], [o, "2026-11-07T21:00:00Z", "0.5", "1"], [g, "2026-11-08T21:00:00Z", "", "1"], [g, "2026-11-17T00:00:00Z", "0.1", "1"], [s, __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(1793903940 - 3 * 86400)), "0.0007", "1"]])
man = {}
for sub in ("kalshi1m", "funding"):
    for f in sorted(os.listdir(os.path.join(t, sub))): man["%s/%s" % (sub, f)] = hashlib.sha256(open(os.path.join(t, sub, f), "rb").read()).hexdigest()
mp = os.path.join(t, "manifest.txt"); open(mp, "w").write("\n".join("%s  %s" % (h, r) for r, h in man.items()) + "\n"); msha = hashlib.sha256(open(mp, "rb").read()).hexdigest()
allow = os.path.join(t, "allow.md")
def refused(**kw):
    try: L.load(t, **kw)
    except SystemExit as e: return str(e)
    return None
assert "cannot be read" in refused(allow_file=os.path.join(t, "none.md"), manifest=mp)
open(allow, "w").write("nothing\n"); assert "no allow-list line" in refused(allow_file=allow, manifest=mp)
open(allow, "w").write("| %s lane4_load.py %s |\n" % (L.ALLOW_MARK, L.self_sha())); assert "does not name the sha256 of the files manifest" in refused(allow_file=allow, manifest=mp)
open(allow, "w").write("| %s lane4_load.py WRONG %s |\n" % (L.ALLOW_MARK, msha)); assert "no allow-list line" in refused(allow_file=allow, manifest=mp)
open(allow, "w").write("| %s lane4_load.py %s %s |\n" % (L.ALLOW_MARK, L.self_sha(), msha))
d, f, c, wk = L.load(t, allow, mp)
assert d[g] == {L.START3: (1.0, 1.1), L.CUT - 60: (3.0, 3.1), L.START3 + 120: (4.0, 4.1)}, d[g]
assert d[s] == {L.START_STOCK: (10.0, 10.1), L.START_STOCK + 60: (12.0, 12.1)} and o not in d
assert L.START3 == 1788998400 and L.START_STOCK == 1793903940 and L.CUT == 1794873600 and len(L.STOCKS) == 94 and len(L.INDEX3) == 3
assert f[s] == {1793903940 - 3 * 86400: 0.0007, L.iso("2026-11-07T21:00:00Z"): 0.0001, L.iso("2026-11-08T21:00:00Z"): 0.0002, L.iso("2026-11-04T21:00:00Z"): 0.0004} and f[g] == {}
assert c == {"candle before the name's start (dropped)": 2, "candle row outside the wall (not parsed)": 1, "candle without a bid or ask (dropped)": 1, "candle at or after the cut (dropped)": 1, "duplicate candle differs (first kept)": 1, "funding row more than 3 days before the start (dropped)": 1, "funding row outside the wall (not parsed)": 1, "funding row without a rate (dropped)": 1, "funding row at or after the cut (dropped)": 1}, c
assert wk == {5: 1, 6: 1, 2: 1, 0: 1}, wk          # Saturday 11-07 = 5, Sunday 11-08 = 6, Wednesday 11-04 = 2
# a file changed after the manifest is refused before any row is read
with gzip.open(os.path.join(t, "funding/2026-11-06.csv.gz"), "wt") as fh: fh.write("ticker,funding_time,funding_rate,mark_price\n")
assert "does not match the manifest" in refused(allow_file=allow, manifest=mp)
shutil.rmtree(t); print("lane4 loader tests passed")
