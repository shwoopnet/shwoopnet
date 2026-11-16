import math, opengap1_second as g
def near(a, b, t=1e-8): return abs(a - b) < t
def ev(name, day, o, ub, uo, cands, up=None):
    return {"name": name, "day": day, "open_ts": o, "prev16_ts": o - 66000, "u_open": uo, "u_prev": ub, "c": cands}
def mk(o, prev, p25, rest):
    c = {}
    if prev: c[o - 66000] = prev
    if p25: c[o - 300] = p25
    c.update({o + k: v for k, v in rest.items()}); return c
E1 = ev("A", "d1", 100000, 100, 101, mk(100000, (9.99, 10.01), (10.04, 10.06), {0: (10.20, 10.22), 60: (10.06, 10.08), 120: (10.07, 10.09), 180: (10.30, 10.32)}))
E2 = ev("A", "d2", 200000, 50, 49.5, mk(200000, (4.995, 5.005), (4.995, 5.005), {60: (4.99, 5.01), 120: (4.99, 5.00), 300: (4.98, 4.99), 900: (4.98, 4.99), 960: (4.00, 4.01)}))
E3 = ev("A", "d3", 300000, 200, 202, mk(300000, (19.99, 20.01), (19.99, 20.01), {60: (20.01, 20.03), 120: (20.05, 20.07), 360: (20.14, 20.16)}))
E4 = ev("A", "d4", 400000, 100, 100.15, mk(400000, (99.99, 100.01), (99.99, 100.01), {60: (99.90, 100.20), 120: (99.9, 100.1)}))
E9 = ev("A", "d5", 500000, 100, 100.2, mk(500000, (99.99, 100.01), (99.99, 100.01), {60: (99.90, 100.10), 120: (99.9, 100.1)}))
E5 = ev("A", "d6", 600000, 100, None, mk(600000, (9.99, 10.01), (10.04, 10.06), {60: (10.06, 10.08)}))
E6 = ev("A", "d7", 700000, 100, 101, mk(700000, (9.99, 10.01), None, {60: (10.06, 10.08)}))
E7 = ev("A", "d8", 800000, 100, 101, mk(800000, None, (10.04, 10.06), {60: (10.06, 10.08)}))
E8 = ev("A", "d9", 900000, 200, 202, mk(900000, (19.99, 20.01), (19.99, 20.01), {60: (20.01, 20.03)}))
evs = [E1, E2, E3, E4, E9, E5, E6, E7, E8]
out, sk = g.run(evs)
assert sk == {"no_underlying": 1, "no_perp": 2, "no_trigger": 2, "no_exit": 1}, sk
rets = {0.0: (-0.00099206, 0.0, 0.00549176), 0.01: (-0.00297324, -0.00401606, 0.00449102), 0.02: (-0.00495050, -0.00804829, 0.00349127)}
for h, rr in rets.items():
    assert [r["day"] for r in out[h]] == ["d1", "d2", "d3"], out[h]
    for r, x in zip(out[h], rr): assert near(r["ret"], x, 1e-7) and near(r["net"], x - 0.0024, 1e-7), (h, r, x)
pfs = {0.0: (0.5338, 1.2882), 0.01: (0.1774, 0.3259), 0.02: (0.0613, 0.1044)}
for h, (p, h2) in pfs.items():
    b = g.block(out[h]); assert abs(b["pf"] - p) < 5e-5 and b["h1"] == 0.0 and abs(b["h2"] - h2) < 5e-5 and b["n"] == 3 and b["wins"] == 1, (h, b)
assert abs(g.block(out[0.02])["z"] - (-1.6151)) < 5e-5
o0, _ = g.run(evs, 0.0); assert abs(g.block(o0[0.0])["pf"] - 5.5355) < 5e-4 and near(g.block(o0[0.0])["breakeven_fee"], 0.00074995, 1e-8)
# the exit is E2's 09:45 candle, E3's closure candle at O+360, and an early closure beats a later candle; sides
st, r = g.score_event(E2, 0.0); assert st == "trade" and near(r["ret"], 0.0)
assert g.score_event(E4, 0.0)[0] == "no_trigger" and g.score_event(E9, 0.0)[0] == "no_trigger"
# a candle after 09:45 is never used for the exit; the 09:45 candle is
E2b = dict(E2, c=dict(E2["c"])); E2b["c"][200900] = (4.97, 4.98); st, r = g.score_event(E2b, 0.0); assert st == "trade" and near(r["ret"], (4.99 - 4.98) / 4.99, 1e-9)
# strict threshold: a gap just above 2 x half spread triggers
E9b = dict(E9, u_open=100.21); assert g.score_event(E9b, 0.0)[0] == "trade"
# a one-sided candle at 16:00 or 09:25 is no_perp
c1 = dict(E1["c"]); c1[100000 - 300] = (0.0, 10.06); assert g.score_event(dict(E1, c=c1), 0.0)[0] == "no_perp"
# timestamps: 09:30 ET on 2026-11-09 is 14:30Z
import datetime
assert g._ts("2026-11-09", 9, 30) == int(datetime.datetime(2026, 11, 9, 14, 30, tzinfo=datetime.timezone.utc).timestamp()) and g._ts("2026-11-06", 16, 0) == int(datetime.datetime(2026, 11, 6, 21, 0, tzinfo=datetime.timezone.utc).timestamp())
assert (g.FEE, g.HAIRCUTS, g.DEV_FROM, g.DEV_TO, g.FIRST_TS) == (0.0012, (0.0, 0.01, 0.02), "2026-11-06", "2026-11-30", 1793923200)
print("opengap1 tests passed")
# loader on invented files: kalshi1m gz per UTC day, underlying csv; days outside the development range are dropped; non-listed perps ignored
import csv, gzip, os, tempfile
d = tempfile.mkdtemp(); hdr = "ticker,end_period_ts,bid_open,bid_high,bid_low,bid_close,ask_open,ask_high,ask_low,ask_close,price_open,price_high,price_low,price_close,price_mean,price_previous,open_interest,volume"
def row(t, ts, b, a): return f"{t},{ts},0,0,0,{b},0,0,0,{a},0,0,0,0,0,0,0,0"
t16, t25, t31, t32 = g._ts("2026-11-06", 16, 0), g._ts("2026-11-09", 9, 25), g._ts("2026-11-09", 9, 31), g._ts("2026-11-09", 9, 32)
bad = "KXUS500PERP,NOT_A_TS,x,x,x,BAD,x,x,x,BAD,x,x,x,x,x,x,x,x"          # a US500 row that raises on any column but ticker
with gzip.open(os.path.join(d, "2026-11-06.csv.gz"), "wt") as f: f.write(hdr + "\n" + row("KXSPYPERP", t16, 9.99, 10.01) + "\n" + row("KXOTHERPERP", t16, 1, 2) + "\n" + bad + "\n" + row("KXSPYPERP", g.FIRST_TS - 60, 1.0, 2.0) + "\n")
with gzip.open(os.path.join(d, "2026-11-09.csv.gz"), "wt") as f: f.write(hdr + "\n" + row("KXSPYPERP", t25, 10.04, 10.06) + "\n" + row("KXSPYPERP", t31, 10.06, 10.08) + "\n" + row("KXSPYPERP", t32, 10.07, 10.09) + "\n")
uf = os.path.join(d, "u.csv")
with open(uf, "w") as f: f.write("perp,date,prev_date,u_open,u_prev_close,x_open,x_prev_close\nKXSPYPERP,2026-11-09,2026-11-06,101,100,101.01,100\nKXSPYPERP,2026-12-02,2026-11-30,101,100,101,100\n")
evs = g.load(d, uf); assert len(evs) == 1 and evs[0]["open_ts"] == g._ts("2026-11-09", 9, 30) and evs[0]["u_open"] == 101.0 and "KXOTHERPERP" not in str(evs[0]["c"]) and len(evs[0]["c"]) == 4 and (g.FIRST_TS - 60) not in evs[0]["c"]
o, sk = g.run(evs); assert len(o[0.0]) == 1 and near(o[0.0][0]["ret"], -0.00099206, 1e-7)
g.main(d, uf)
# the closure edge: a gap closed to exactly half counts (mid 20.10: gap_t = 0.005 = half of 0.01), so the exit is that candle's bid, not the later one
E3e = dict(E3, c=dict(E3["c"])); E3e["c"][300000 + 120] = (20.09, 20.11)
st, r = g.score_event(E3e, 0.0); assert st == "trade" and near(r["ret"], (20.09 - 20.03) / 20.03, 1e-9), r
# a zero or negative previous close is no_underlying, not a crash
assert g.score_event(dict(E1, u_prev=0.0), 0.0)[0] == "no_underlying" and g.score_event(dict(E1, u_prev=-1.0), 0.0)[0] == "no_underlying"
