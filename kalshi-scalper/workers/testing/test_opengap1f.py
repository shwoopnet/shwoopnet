import csv, datetime, gzip, math, os, tempfile, opengap1f as f
def near(a, b, t=1e-7): return abs(a - b) < t
# the same invented events E1..E9 as the frozen test (OPENGAP1_HAND_CASE.md), with day names d1.. and one name
def ev(day, o, ub, uo, cands): return {"name": "KXSPYPERP", "day": day, "open_ts": o, "prev16_ts": o - 66000, "u_open": uo, "u_prev": ub, "c": cands}
def mk(o, prev, p25, rest):
    c = {}
    if prev: c[o - 66000] = prev
    if p25: c[o - 300] = p25
    c.update({o + k: v for k, v in rest.items()}); return c
E1 = ev("d1", 100000, 100, 101, mk(100000, (9.99, 10.01), (10.04, 10.06), {0: (10.20, 10.22), 60: (10.06, 10.08), 120: (10.07, 10.09), 180: (10.30, 10.32)}))
E2 = ev("d2", 200000, 50, 49.5, mk(200000, (4.995, 5.005), (4.995, 5.005), {60: (4.99, 5.01), 120: (4.99, 5.00), 300: (4.98, 4.99), 900: (4.98, 4.99), 960: (4.00, 4.01)}))
E3 = ev("d3", 300000, 200, 202, mk(300000, (19.99, 20.01), (19.99, 20.01), {60: (20.01, 20.03), 120: (20.05, 20.07), 360: (20.14, 20.16)}))
E4 = ev("d4", 400000, 100, 100.15, mk(400000, (99.99, 100.01), (99.99, 100.01), {60: (99.90, 100.20), 120: (99.9, 100.1)}))
E9 = ev("d5", 500000, 100, 100.2, mk(500000, (99.99, 100.01), (99.99, 100.01), {60: (99.90, 100.10), 120: (99.9, 100.1)}))
E5 = ev("d6", 600000, 100, None, mk(600000, (9.99, 10.01), (10.04, 10.06), {60: (10.06, 10.08)}))
E6 = ev("d7", 700000, 100, 101, mk(700000, (9.99, 10.01), None, {60: (10.06, 10.08)}))
E7 = ev("d8", 800000, 100, 101, mk(800000, None, (10.04, 10.06), {60: (10.06, 10.08)}))
E8 = ev("d9", 900000, 200, 202, mk(900000, (19.99, 20.01), (19.99, 20.01), {60: (20.01, 20.03)}))
evs = [E1, E2, E3, E4, E9, E5, E6, E7, E8]
# relative haircut figures (hand case)
rel = {0.001: (-0.0029881, -0.0020020, 0.0034828), 0.002: (-0.0049802, -0.0040080, 0.0014778)}
for r, rr in rel.items():
    out = sorted(f.run(evs, "rel", r, 0.0), key=lambda x: x["open_ts"]); assert [o["day"] for o in out] == ["d1", "d2", "d3"]
    for o, x in zip(out, rr): assert near(o["ret"], x), (r, o, x)
    for fee in (0.0012, 0.0005):
        b = f.block(f.run(evs, "rel", r, fee)); v = [x - 2 * fee for x in rr]
        assert near(b["pf"], sum(x for x in v if x > 0) / max(1e-18, -sum(x for x in v if x < 0)), 1e-5) or (b["pf"] == 0.0 and sum(1 for x in v if x > 0) == 0), (r, fee, b)
assert abs(f.block(f.run(evs, "rel", 0.001, 0.0012))["pf"] - 0.1106) < 5e-5 and f.block(f.run(evs, "rel", 0.002, 0.0012))["pf"] == 0.0 and abs(f.block(f.run(evs, "rel", 0.001, 0.0005))["pf"] - 0.3552) < 5e-5
# the literal price-unit lines equal the frozen OPENGAP1 figures (hand case: E1 -0.00297324 at 1c)
ab = sorted(f.run(evs, "abs", 0.01, 0.0), key=lambda x: x["open_ts"]); assert near(ab[0]["ret"], -0.00297324) and near(ab[1]["ret"], -0.00401606) and near(ab[2]["ret"], 0.00449102)
import opengap1_second as g          # the frozen core gives the same numbers on the same events
for h in (0.0, 0.01, 0.02):
    o1 = sorted(f.run(evs, "abs", h, 0.0012), key=lambda x: x["open_ts"]); o2, _ = g.run(evs); assert [round(x["net"], 12) for x in o1] == [round(x["net"], 12) for x in o2[h]]
# counting: triggered events are trade + no_exit, integers only
assert f.triggered(evs) == (4, {"KXSPYPERP": 4})
# interim: refuses under 50 triggered events; KILL below PF 1.0, CONTINUE at 1.0 or above
try: f.interim(evs, (0.0012,), 0.0012); raise AssertionError("must refuse")
except SystemExit as e: assert "interim look needs 50" in str(e)
def many(k, win):          # k identical triggered events with a clear win or loss
    base = E3 if win else E1; out = []
    for i in range(k): e = dict(base, day="2026-12-%02d" % (i % 28 + 1), open_ts=1000000 + i * 100000, prev16_ts=1000000 + i * 100000 - 66000, c={}); sh = (1000000 + i * 100000) - base["open_ts"]; e["c"] = {t + sh: q for t, q in base["c"].items()}; out.append(e)
    return out
r = f.interim(many(50, True), (0.0012, 0.0005), 0.0012); assert r["verdict"] == "CONTINUE" and r["triggers"] == 50 and r["pf_by_fee"][0.0012] == math.inf
r = f.interim(many(50, False), (0.0012, 0.0005), 0.0012); assert r["verdict"] == "KILL" and r["pf_by_fee"][0.0012] == 0.0
# no verified fee: PF at every fee, no kill; the kill follows the verified fee only (a loss at 12 bps, a win at 5 bps)
r = f.interim(many(50, False), (0.0012, 0.0005)); assert r["verdict"] == "no kill: fee unverified" and set(r["pf_by_fee"]) == {0.0012, 0.0005}
wins5 = many(50, True); r = f.interim(wins5, (0.0012, 0.0005), 0.0005); assert r["verdict"] == "CONTINUE"
mid_ev = [dict(E3, day="2026-12-%02d" % (i % 28 + 1), open_ts=1000000 + i * 100000, prev16_ts=1000000 + i * 100000 - 66000, c={t + (1000000 + i * 100000 - E3["open_ts"]): q for t, q in E3["c"].items()}) for i in range(50)]
r = f.interim(mid_ev, (0.0012, 0.0100), 0.0100); assert r["verdict"] == "KILL" and r["pf_by_fee"][0.0012] == math.inf          # E3 wins at 12 bps, loses at 100 bps: the verified fee decides
r = f.interim(mid_ev, (0.0012, 0.0100), 0.0012); assert r["verdict"] == "CONTINUE"
try: f.interim(many(49, True), (0.0012,), 0.0012); raise AssertionError("must refuse")
except SystemExit as e: assert "49 triggered" in str(e)
# the final read: refused under 100 unless --stop and the last event date is the stop date
try: f.read_ok(many(99, True)); raise AssertionError("must refuse")
except SystemExit as e: assert "99 triggered" in str(e)
assert f.read_ok(many(100, True)) == 100
late = many(10, True); late[0] = dict(late[0], day="2027-01-31")
assert f.read_ok(late, stop=True) == 10
try: f.read_ok(late, stop=False); raise AssertionError("must refuse")
except SystemExit: pass
try: f.read_ok(many(10, True), stop=True); raise AssertionError("must refuse")
except SystemExit: pass
# the interim threshold, with the PF fixed by a stub: exactly 1.0 and 1.05 continue, 0.9999 kills
real = f.block
for pfv, want in ((1.0, "CONTINUE"), (1.05, "CONTINUE"), (0.9999, "KILL")):
    f.block = lambda rows, pfv=pfv: {"n": 50, "wins": 1, "pf": pfv, "h1": 1.0, "h2": 1.0, "z": None}
    assert f.interim(many(50, True), (0.0012,), 0.0012)["verdict"] == want, pfv
f.block = real
# the closure edge (gap closed to exactly half counts), as in the frozen test
E3e = dict(E3, c=dict(E3["c"])); E3e["c"][300000 + 120] = (20.09, 20.11)
st, r = f.score_event(E3e, "abs", 0.0, 0.0); assert st == "trade" and near(r["ret"], (20.09 - 20.03) / 20.03, 1e-9), r
# main: the bar line marks which fee is verified; the interim prints the verdict only on the verified fee
import io, contextlib
real_load = f.load; f.load = lambda d, u: many(100, True)
buf = io.StringIO()
with contextlib.redirect_stdout(buf): f.main("read", "d", "u", [0.0012, 0.0005, 0.0003], False, 0.0003)
out = buf.getvalue(); assert "fee/side 0.0003 (VERIFIED) bar" in out and "fee/side 0.0012 (assumed, not verified) bar" in out and "(primary)" in out and "(information only)" in out and "triggered events pooled 100" in out
buf = io.StringIO()
with contextlib.redirect_stdout(buf): f.main("interim", "d", "u", [0.0012, 0.0005], False, None)
assert "no kill: fee unverified" in buf.getvalue()
buf = io.StringIO()
with contextlib.redirect_stdout(buf): f.main("count", "d", "u", [0.0012], False, None)
assert buf.getvalue().strip().startswith("OPENGAP1-F triggered events pooled 100") and "PF" not in buf.getvalue()
f.load = real_load
# verdict
ok = {"n": 100, "pf": 1.3, "h1": 1.0, "h2": 1.0}; assert f.verdict(ok, {"pf": 1.0}) is True and f.verdict(dict(ok, n=99), {"pf": 1.0}) is False and f.verdict(dict(ok, pf=1.29), {"pf": 1.0}) is False and f.verdict(dict(ok, h1=.99), {"pf": 1.0}) is False and f.verdict(dict(ok, h2=.99), {"pf": 1.0}) is False and f.verdict(ok, {"pf": .99}) is False
# loader: window, ticker wall, FIRST_TS, DST refusal
d = tempfile.mkdtemp(); hdr = "ticker,end_period_ts,bid_open,bid_high,bid_low,bid_close,ask_open,ask_high,ask_low,ask_close,price_open,price_high,price_low,price_close,price_mean,price_previous,open_interest,volume"
def row(t, ts, b, a): return f"{t},{ts},0,0,0,{b},0,0,0,{a},0,0,0,0,0,0,0,0"
t16, t25, t31 = f._ts("2026-11-16", 16, 0), f._ts("2026-11-17", 9, 25), f._ts("2026-11-17", 9, 31)
bad = "KXUS500PERP,NOT_A_TS,x,x,x,BAD,x,x,x,BAD,x,x,x,x,x,x,x,x"
with gzip.open(os.path.join(d, "2026-11-16.csv.gz"), "wt") as fh: fh.write(hdr + "\n" + row("KXSPYPERP", t16, 9.99, 10.01) + "\n" + bad + ",extra\n" + "KXUS500PERP,1\n" + row("KXSPYPERP", f.FIRST_TS - 60, 1.0, 2.0) + "\n")
with gzip.open(os.path.join(d, "2026-11-17.csv.gz"), "wt") as fh: fh.write(hdr + "\n" + row("KXSPYPERP", t25, 10.04, 10.06) + "\n" + row("KXSPYPERP", t31, 10.06, 10.08) + "\n" + row("KXOTHERPERP", t31, 1, 2) + "\n")
uf = os.path.join(d, "u.csv")
def w(rows): open(uf, "w").write("perp,date,prev_date,u_open,u_prev_close,x_open,x_prev_close\n" + "".join(rows))
w(["KXSPYPERP,2026-11-17,2026-11-16,101,100,101,100\n", "KXSPYPERP,2026-11-16,2026-11-13,101,100,101,100\n", "KXSPYPERP,2027-02-01,2027-01-29,101,100,101,100\n"])
lv = f.load(d, uf); assert len(lv) == 1 and lv[0]["day"] == "2026-11-17" and len(lv[0]["c"]) == 3 and (f.FIRST_TS - 60) not in lv[0]["c"] and "KXOTHERPERP" not in str(lv[0]["c"])
w(["KXSPYPERP,2027-03-14,2027-03-12,101,100,101,100\n"])
try: f.load(d, uf); raise AssertionError("must refuse")
except SystemExit as e: assert "DST" in str(e)
w(["KXSPYPERP,2027-01-31,2027-01-29,101,100,101,100\n"]); assert len(f.load(d, uf)) == 1
assert (f.FEES, f.REL, f.ABS, f.FWD_FROM, f.FWD_TO, f.DST_CHANGE, f.FIRST_TS, f.TRIGGERS_FINAL, f.TRIGGERS_INTERIM) == ((0.0012, 0.0005), (0.001, 0.002), (0.01, 0.02), "2026-11-17", "2027-01-31", "2027-03-14", 1793923200, 100, 50)
print("opengap1f tests passed")
