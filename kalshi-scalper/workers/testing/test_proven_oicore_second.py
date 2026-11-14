"""Test for proven_oicore_second.py (extract-only input): INVENTED rows only (PROVEN_OICORE_HAND_CASE.md and ..._ADDENDUM3.md). Run: python3 -B -W ignore test_proven_oicore_second.py"""
import hashlib, os, re, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proven_oicore_second as p

HDR = "ts,ticker,side,count,avgFill,avgFee,result"
def ts(i): return "2026-11-14T%02d:%02d:%02dZ" % (i // 3600, (i % 3600) // 60, i % 60)
def line(i, side, count, fill, fee, res, tk=None):
    c = "%d" % count if count == int(count) else "%.6f" % count
    return "%s,%s,%s,%s,%.6f,%.6f,%s" % (ts(i), tk or "KXBTC15M-T%03d" % i, side, c, fill, fee, res)
def std(i, win):          # count 10, fee .02, side price .20: win +7.80, loss -2.20
    side = "yes" if i % 2 == 0 else "no"
    return line(i, side, 10, 0.20 if side == "yes" else 0.80, 0.02, side if win else ("no" if side == "yes" else "yes"))
def w13(i, win): return line(i, "yes", 2, 0.33, 0.02, "yes") if win else line(i, "yes", 1, 0.98, 0.02, "no")          # +1.30 / -1.00
def win_rows(start, n, w, kind=std): return [kind(start + j, j < w) for j in range(n)]
def text(lines, header=HDR): return header + "\n" + "".join(l + "\n" for l in lines)
near = lambda a, b: abs(a - b) < 1e-9
tmp = tempfile.mkdtemp()
def wr(name, content, binary=False):
    f = os.path.join(tmp, name); open(f, "wb").write(content if binary else content.encode()); return f

# --- the cash basis through the row scorer ---
def one(side, count, fill, fee, res): return p.cash_net(dict(side=side, count=count, fill=fill, fee=fee, result=res))
assert near(one("yes", 10, 0.20, 0.02, "yes")[0], 7.8) and near(one("no", 10, 0.80, 0.02, "no")[0], 7.8) and near(one("yes", 10, 0.20, 0.02, "no")[0], -2.2) and near(one("no", 10, 0.80, 0.02, "yes")[0], -2.2)
assert near(one("no", 10, 0.60, 0.0, "no")[0], 10 - 4.0)          # a NO fill of .60 costs 1 - .60 = .40 a contract
assert near(one("yes", 2, 0.33, 0.02, "yes")[0], 1.3) and near(one("yes", 1, 0.98, 0.02, "no")[0], -1.0)
for bad in (one("yes", 0, 0.2, 0.02, "yes"), one("yes", 1, 1.2, 0.02, "yes"), one("yes", 1, 0.0, 0.02, "yes"), one("yes", 1, 1.0, 0.02, "yes"), one("yes", 1, 0.5, 1.5, "yes"), one("yes", 1, 0.5, -0.1, "yes")):
    assert bad[0] is None and bad[1]
assert one("yes", 1, 0.5, 1.0, "yes")[0] is None and one("yes", 1, 0.5, 0.999999, "yes")[0] is not None          # fee 1 is not usable
assert one("yes", 1, 0.5, 0.0, "yes")[0] is not None          # fee 0 is usable
# --- Sets P, N, E at P = 100 (windows 33, 33, 34) ---
P = win_rows(0, 33, 12) + win_rows(33, 33, 9) + win_rows(66, 34, 8)
f = wr("P.csv", text(P)); r = p.score_rows(p.parse_extract(f)["rows"], 100)
assert [w["n"] for w in r["windows"]] == [33, 33, 34]
for w, e in zip(r["windows"], (93.6 / 46.2, 70.2 / 52.8, 62.4 / 57.2)): assert near(w["cash_pf_unrounded"], e), (w, e)
assert [w["counts"] for w in r["windows"]] == [True, True, False] and r["windows_counting"] == 2 and r["VERDICT"] == "PROVEN"
assert near(r["windows"][0]["win_rate"], 12 / 33) and near(r["windows"][0]["net"], 12 * 7.8 - 21 * 2.2) and r["windows"][0]["n"] == 33
assert abs(r["windows"][0]["cash_pf_unrounded"] - 2.0260) < 5e-5 and abs(r["windows"][1]["cash_pf_unrounded"] - 1.3295) < 5e-5 and abs(r["windows"][2]["cash_pf_unrounded"] - 1.0909) < 5e-5
Nn = win_rows(0, 33, 12) + win_rows(33, 33, 8) + win_rows(66, 34, 8)
rn = p.score_rows(p.parse_extract(wr("N.csv", text(Nn)))["rows"], 100); assert rn["VERDICT"] == "NOT YET" and rn["windows_counting"] == 1 and near(rn["windows"][1]["cash_pf_unrounded"], 62.4 / 55)
E = win_rows(0, 33, 12) + win_rows(33, 33, 8) + win_rows(66, 34, 17, w13)
E = E[:66] + [w13(66 + j, j % 2 == 0) for j in range(34)]          # 17 wins and 17 losses interleaved
re_ = p.score_rows(p.parse_extract(wr("E.csv", text(E)))["rows"], 100)
assert abs(re_["windows"][2]["cash_pf_unrounded"] - 1.3) < 1e-9 and re_["windows"][2]["counts"] is True and re_["VERDICT"] == "PROVEN" and re_["windows_counting"] == 2
# the 1e-9 tolerance on the net lists directly
assert p.window_ok([1.3] * 65 + [-1.0] * 65) and not p.window_ok([1.2999] * 65 + [-1.0] * 65) and p.window_ok([1.3 - 5e-10] * 10 + [-1.0] * 10) and not p.window_ok([1.3 - 2e-9] * 10 + [-1.0] * 10)
assert p.window_ok([1.0] * 5 + [-0.5] * 2) and p.pf_of([1.0] * 100) == float("inf") and p.pf_of([]) is None and not p.window_ok([]) and not p.window_ok([-1.0]) and p.pf_of([-1.0, 1.0]) == 1.0
assert [len(x) for x in p.split(list(range(100)))] == [33, 33, 34] and [len(x) for x in p.split(list(range(150)))] == [50, 50, 50] and [len(x) for x in p.split(list(range(10)))] == [3, 3, 4]
# --- P = 150 (windows of 50) ---
R = win_rows(0, 50, 30) + win_rows(50, 50, 20) + win_rows(100, 50, 10)
rr = p.score_rows(p.parse_extract(wr("R.csv", text(R)))["rows"], 150)
for w, e in zip(rr["windows"], (234 / 44, 156 / 66, 78 / 88)): assert near(w["cash_pf_unrounded"], e)
assert rr["VERDICT"] == "PROVEN" and [w["n"] for w in rr["windows"]] == [50, 50, 50] and abs(rr["windows"][0]["cash_pf_unrounded"] - 5.3182) < 5e-5
S = win_rows(0, 50, 30) + win_rows(50, 50, 10) + win_rows(100, 50, 12)
rs = p.score_rows(p.parse_extract(wr("S.csv", text(S)))["rows"], 150); assert rs["VERDICT"] == "NOT YET" and near(rs["windows"][2]["cash_pf_unrounded"], 93.6 / 83.6) and rs["windows_counting"] == 1
# --- the format is strict: each violation STOPs naming the line ---
def stops(content, why, binary=False):
    f = wr("bad.csv", content, binary)
    try: p.parse_extract(f); assert 0, why
    except SystemExit as e: assert "STOP" in str(e) and why in str(e), (why, str(e))
good = [std(i, True) for i in range(3)]
stops(text(good, "ts,ticker,side,count,avgFill,avgFee"), "header")
stops(text(good).replace("\n", "\r\n"), "CR")
stops(text(good)[:-1], "final")
stops(text(good[:1] + ["a,b,c,d,e,f"] + good[1:]), "line 3")
stops(text([good[0].replace(",yes,", ",maybe,", 1)]), "side")
stops(text([good[0].rsplit(",", 1)[0] + ",void"]), "result")
stops(text([good[0].rsplit(",", 1)[0] + ",exit"]), "result")
stops(text([line(0, "yes", 10, 0.2, 0.02, "yes").replace("0.200000", "0.2")]), "avgFill")
stops(text([line(0, "yes", 10, 0.2, 0.02, "yes").replace(",0.020000,", ",0.02,")]), "avgFee")
stops(text([line(0, "yes", 10, 0.2, 0.02, "yes").replace(",10,", ",10.5,")]), "count")
stops(text([good[1], good[0]]), "order")
stops(text([line(0, "yes", 10, 0.2, 0.02, "yes").replace("KXBTC15M-T000", "")]), "ticker")
stops("\xff\xfe".encode("latin-1"), "utf", binary=True)
# ties: same ts, ticker order kept (allowed); the same (ts, ticker) twice is allowed
t1 = line(0, "yes", 10, 0.2, 0.02, "yes", tk="A"); t2 = line(0, "yes", 10, 0.2, 0.02, "no", tk="B")
assert len(p.parse_extract(wr("t.csv", text([t1, t2])))["rows"]) == 2 and len(p.parse_extract(wr("t2.csv", text([t1, t1])))["rows"]) == 2
stops(text([t2, t1]), "order")
# the sha256 is of the raw bytes
sh = p.parse_extract(f if False else wr("P.csv", text(P)))["sha256"]; assert sh == hashlib.sha256(text(P).encode()).hexdigest()
# --- row count against the read point; usable shortfall ---
too_many = P + [std(100, True)]
try: p.score_rows(p.parse_extract(wr("m.csv", text(too_many)))["rows"], 100); assert 0
except SystemExit as e: assert "101" in str(e) and "STOP" in str(e)
short = p.score_rows(p.parse_extract(wr("s.csv", text(P[:99])))["rows"], 100); assert short["VERDICT"] == "NOT_ENOUGH_DATA" and short["rows_usable"] == 99
empty = p.score_rows(p.parse_extract(wr("e.csv", text([])))["rows"], 100); assert empty["VERDICT"] == "NOT_ENOUGH_DATA" and empty["rows_usable"] == 0 and empty["windows"][0]["cash_pf_unrounded"] is None
badfill = P[:50] + [line(50, "yes", 10, 1.2, 0.02, "yes")] + P[51:]
sf = p.score_rows(p.parse_extract(wr("bf.csv", text(badfill)))["rows"], 100); assert sf["VERDICT"] == "NOT_ENOUGH_DATA" and sf["rows_usable"] == 99 and sf["excluded_unusable"] == 1
assert r["excluded_unusable"] == 0          # always printed, zero included
# --- read points: markers (refusals before the file is looked at; NOT_ENOUGH_DATA does not spend; sha256 in the marker) ---
HP = P
with tempfile.TemporaryDirectory() as d:
    fa = wr("ok100.csv", text(HP))
    r100 = p.read_point(fa, 100, marker_dir=d)
    assert r100["read_point"] == 100 and r100["VERDICT"] == "PROVEN" and r100["extract_sha256"] == hashlib.sha256(text(HP).encode()).hexdigest() and r100["python"].startswith(sys.version.split()[0])
    m = open(os.path.join(d, "PROVEN_OICORE_READ_100.local")).read(); assert "verdict: PROVEN" in m and r100["extract_sha256"] in m
    assert "KXBTC15M" not in repr(r100)          # no per-row detail
    for bad, why in ((100, "already"), (150, "PROVEN")):
        try: p.read_point(fa, bad, marker_dir=d); assert 0
        except SystemExit as e: assert why in str(e), (bad, str(e))
    assert not os.path.exists(os.path.join(d, "PROVEN_OICORE_READ_150.local"))
with tempfile.TemporaryDirectory() as d:
    try: p.read_point(wr("none.csv", text(S)), 150, marker_dir=d); assert 0          # no point-100 marker
    except SystemExit as e: assert "100" in str(e)
    fshort = wr("short.csv", text(Nn[:99]))
    sh0 = p.read_point(fshort, 100, marker_dir=d); assert sh0["VERDICT"] == "NOT_ENOUGH_DATA" and not os.path.exists(os.path.join(d, "PROVEN_OICORE_READ_100.local"))
    n1 = p.read_point(wr("n100.csv", text(Nn)), 100, marker_dir=d); assert n1["VERDICT"] == "NOT YET" and os.path.exists(os.path.join(d, "PROVEN_OICORE_READ_100.local"))
    s150 = p.read_point(wr("s120.csv", text(S[:120])), 150, marker_dir=d); assert s150["VERDICT"] == "NOT_ENOUGH_DATA" and not os.path.exists(os.path.join(d, "PROVEN_OICORE_READ_150.local"))
    r150 = p.read_point(wr("s150.csv", text(S)), 150, marker_dir=d); assert r150["VERDICT"] == "NOT YET" and r150["read_point"] == 150 and os.path.exists(os.path.join(d, "PROVEN_OICORE_READ_150.local"))
    try: p.read_point(wr("s150b.csv", text(S)), 150, marker_dir=d); assert 0
    except SystemExit as e: assert "already" in str(e)
    try: p.read_point(fa, 175, marker_dir=d); assert 0
    except SystemExit as e: assert "read point" in str(e)
    # a refusal comes before the file is looked at: a missing file still reports the marker refusal
    try: p.read_point(os.path.join(d, "nonexistent.csv"), 100, marker_dir=d); assert 0
    except SystemExit as e: assert "already" in str(e)
# the source reads only the extract format: no JSON path
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "proven_oicore_second.py")).read()
assert "json.load" not in src and "slotOrders" not in src.split('"""', 2)[2]          # the input is the CSV extract only
print("test_proven_oicore_second: all checks passed")
