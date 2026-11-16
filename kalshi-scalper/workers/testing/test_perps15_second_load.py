import hashlib, lzma, os, sqlite3, tempfile, perps15_second_load as L
d = tempfile.mkdtemp(); T = L.FIRST_TS
def mk(path, ddl, rows):
    db = sqlite3.connect(path); db.execute(ddl); [db.execute("insert into %s values (%s)" % (ddl.split()[2].split("(")[0], ",".join("?" * len(r))), r) for r in rows]; db.commit(); db.close()
cdb = os.path.join(d, "c.sqlite"); fdb = os.path.join(d, "f.sqlite")
days = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10]          # ten UTC days from the start: D = 10, last SEARCH = the fifth date = day 5 (index 4)
rows = []
for k in days:
    for j in range(3): rows.append(("KXMUPERP", T + k * 86400 + 60 * (j + 1), 10.0 + k, 10.1 + k, None, 5, None))
rows += [("KXMUPERP", T - 60, 1.0, 2.0, None, 1, None), ("KXUSTECH100PERP", T + 60, "BAD", "BAD", None, None, None), ("KXMUPERP", T + 60, 10.0, 99.0, None, 5, None), ("KXTSLAPERP", T + 86400 + 60, 20.0, 20.2, None, 5, None), ("KXTSLAPERP", T + 86400 + 120, 20.0, 20.2, None, 5, None)]
mk(cdb, "create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)", rows)
mk(fdb, "create table funding(ticker, ts, rate)", [("KXMUPERP", T + 21 * 3600, 0.0001), ("KXMUPERP", T + 86400 + 21 * 3600, -0.0002), ("KXMUPERP", T + 22 * 3600, 0.5), ("KXMUPERP", T - 3 * 3600, 0.5), ("KXAAPLPERP", T + 21 * 3600, 0.9)])
files = {}
for src, name in ((cdb, L.CANDLE_XZ), (fdb, L.FUNDING_XZ)):
    raw = lzma.compress(open(src, "rb").read()); open(os.path.join(d, name), "wb").write(raw); files[name] = hashlib.sha256(raw).hexdigest()
allow = os.path.join(d, "allow.md"); line = lambda sha, xz: "- " + L.ALLOW_MARK + ": perps15_second_load.py sha256 " + sha + " " + " ".join(xz.values())
def refused(msg, **kw):
    try: L.load(d, allow, files, wall=("KXMUPERP", "KXTSLAPERP"), **kw); raise AssertionError("must refuse")
    except SystemExit as e: assert msg in str(e), str(e)
open(allow, "w").write("x\n"); refused("no allow-list line")
open(allow, "w").write(line("0" * 64, files) + "\n"); refused("no allow-list line")
open(allow, "w").write(line(L.self_sha(), {L.CANDLE_XZ: files[L.CANDLE_XZ]}) + "\n"); refused("does not name the xz sha256")
open(allow, "w").write(line(L.self_sha(), files) + "\n")
bad = dict(files); bad[L.CANDLE_XZ] = "0" * 64; open(allow, "w").write(line(L.self_sha(), bad) + "\n")
try: L.load(d, allow, bad, wall=("KXMUPERP",)); raise AssertionError("must refuse")
except SystemExit as e: assert "does not match the allowed xz sha256" in str(e)
open(allow, "w").write(line(L.self_sha(), files) + "\n")
s, f, c = L.load(d, allow, files, wall=("KXMUPERP", "KXTSLAPERP"))
assert c["candle row outside the wall (not parsed)"] == 1 and c["candle before 2026-11-06 (dropped)"] == 1 and c["duplicate candle differs (first kept)"] == 1 and c["funding row outside the wall (not parsed)"] == 1 and c["funding row before the start or without a rate (dropped)"] == 1, c
assert s["KXMUPERP"][T + 60] == (10.0, 10.1) and len(s["KXMUPERP"]) == 30 and len(s["KXTSLAPERP"]) == 2          # the US Tech row and the pre-start row never enter; the first of a differing duplicate is kept
assert f["KXMUPERP"] == {T + 21 * 3600: 0.0001, T + 86400 + 21 * 3600: -0.0002, T + 22 * 3600: 0.5} and f["KXTSLAPERP"] == {}          # the print timestamps are the extract's own, any hour
sp = L.splits(s); D, last, B = sp["KXMUPERP"]
assert D == 10 and last == L.day(T) + 5 and B == (L.day(T) + 6) * 86400          # hand: the dates are offsets 0, 2, 3, 4, 5, 6, 7, 8, 9, 10; floor(10/2) = 5, the fifth is offset 5

assert L.splits({"X": {T + 60: (1, 2)}}) == {} and L.splits({"X": {T + 60: (1, 2), T + 86400 + 60: (1, 2)}})["X"][1] == L.day(T)          # one date: no split; two dates: SEARCH is the first
print("perps15 loader tests passed")
# the runner: counts and splits first, then the driver's report, on the invented extract with the loader's wall narrowed to two names
import perps15_second_run as R, json
spec = {"data": {"ticker_wall": ["KXMUPERP", "KXTSLAPERP", "KXNOTLOADED"]}, "grid": {"filters": ["none"], "side_rules": ["long"], "exits": ["T3"]}, "costs": {"haircuts_primary": [0.0002, 0.0005], "haircuts_stress": [0.001, 0.002]}, "gates": {"min_n": 100, "pf_primary": 1.3, "pf_secondary": 1.0, "min_trade_days": 10, "bh_alpha": 0.05}}
lines, out = R.run(spec, d, 50, allow, files, wall=("KXMUPERP", "KXTSLAPERP"))
assert lines[0].startswith("counts ") and lines[1] == "names KXMUPERP,KXTSLAPERP" and json.loads(lines[2][len("splits "):]) == {"KXMUPERP": [10, L.iso_day(L.day(T) + 5)]} and any(l.startswith("m 51 ") for l in lines), lines          # TSLA has two candles on one date: D 1, no split, not run
