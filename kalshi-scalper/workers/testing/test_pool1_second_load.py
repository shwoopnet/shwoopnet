import hashlib, lzma, os, shutil, sqlite3, tempfile
import pool1_second_load as L, pool1_second_run as R
t = tempfile.mkdtemp(); n1, n2 = L.WALL[0], L.WALL[1]; E0 = L.FIRST_TS
cp, fp = os.path.join(t, "c.sqlite"), os.path.join(t, "f.sqlite")
db = sqlite3.connect(cp); db.execute("create table market(ticker, series, close_ts, result, src)"); db.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
rows = [(n1, E0 + 60, 1.0, 1.1, 9, 9, 9), (n1, E0 + 120, None, None, 9, 9, 9), (n1, E0 - 1, 5.0, 5.1, 9, 9, 9), (n1, L.CUTOFF, 5.0, 5.1, 9, 9, 9), (n1, L.CUTOFF - 60, 2.0, 2.1, 9, 9, 9), ("KXOUTSIDE", E0 + 60, 7.0, 7.1, 9, 9, 9), (n2, E0 + 60, 3.0, 3.1, 1, 1, 1), (n2, E0 + 60, 3.5, 3.6, 1, 1, 1), (n2, E0, 4.0, 4.1, 1, 1, 1)]
db.executemany("insert into candle values (?,?,?,?,?,?,?)", rows); db.commit(); db.close()
fdb = sqlite3.connect(fp); fdb.execute("create table funding(ticker, ts, rate)"); fdb.executemany("insert into funding values (?,?,?)", [(n1, E0 + 100, 0.0001), (n1, L.CUTOFF + 5, 0.0002), (n1, L.CUTOFF, 0.0004), (n1, E0 - 5, 0.0003), (n1, E0 + 200, None), ("KXOUTSIDE", E0 + 100, 0.5)]); fdb.commit(); fdb.close()
shas = {}
for p, name in ((cp, L.CANDLE_XZ), (fp, L.FUNDING_XZ)):
    open(os.path.join(t, name), "wb").write(lzma.compress(open(p, "rb").read())); shas[name] = hashlib.sha256(open(os.path.join(t, name), "rb").read()).hexdigest()
allow = os.path.join(t, "allow.md")
def refused(**kw):
    try: L.load(t, **kw)
    except SystemExit as e: return str(e)
    return None
assert "cannot be read" in refused(allow_file=os.path.join(t, "none.md"), xz_sha=shas)
open(allow, "w").write("no line here\n"); assert "no allow-list line" in refused(allow_file=allow, xz_sha=shas)
open(allow, "w").write("| x | %s pool1_second_load.py %s |\n" % (L.ALLOW_MARK, L.self_sha())); assert "does not name the xz sha256" in refused(allow_file=allow, xz_sha=shas)
open(allow, "w").write("| x | %s pool1_second_load.py wrongsha %s %s |\n" % (L.ALLOW_MARK, *shas.values())); assert "no allow-list line" in refused(allow_file=allow, xz_sha=shas)
open(allow, "w").write("| x | %s pool1_second_load.py %s %s %s |\n" % (L.ALLOW_MARK, L.self_sha(), *shas.values()))
bad = dict(shas); bad[L.CANDLE_XZ] = "0" * 64; open(allow, "w").write("| x | %s pool1_second_load.py %s %s %s |\n" % (L.ALLOW_MARK, L.self_sha(), *bad.values())); assert "does not match the allowed xz sha256" in refused(allow_file=allow, xz_sha=bad)
open(allow, "w").write("| x | %s pool1_second_load.py %s %s %s |\n" % (L.ALLOW_MARK, L.self_sha(), *shas.values()))
data, fund, c = L.load(t, allow, shas)
assert data[n1] == {E0 + 60: (1.0, 1.1), E0 + 120: (None, None), L.CUTOFF - 60: (2.0, 2.1)} and data[n2] == {E0 + 60: (3.0, 3.1), E0: (4.0, 4.1)}, data[n1]
assert fund[n1] == {E0 + 100: 0.0001} and "KXOUTSIDE" not in data
assert c == {"candle before 2026-11-05T18:39Z (dropped)": 1, "candle at or after 2026-11-17 (dropped)": 1, "candle row outside the wall (not parsed)": 1, "duplicate candle differs (first kept)": 1, "funding row at or after 2026-11-17 (dropped)": 2, "funding row before 2026-11-05T18:39Z or without a ts or rate (dropped)": 2, "funding row outside the wall (not parsed)": 1}, c
assert L.FIRST_TS == 1793903940 and L.CUTOFF == 1794873600 and len(L.WALL) == 94 and len(set(L.WALL)) == 94 and all(w.endswith("PERP") for w in L.WALL)
lines = R.run(t, allow, shas); assert lines[1].startswith("names with candles 2") and len(lines) == 2 + 220
shutil.rmtree(t); print("pool1 second loader tests passed")
