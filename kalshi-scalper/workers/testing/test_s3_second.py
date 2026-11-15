#!/usr/bin/env python3
"""Tests for s3_second.py on INVENTED gzip CSV files (hand cases in S3_SECOND_HAND_CASE.md)."""
import calendar, csv, gzip, io, math, os, random, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s3_second as s
HDR = "t_send_ms,t_recv_ms,server_date_header,ticker,event_ticker,exchange_index,open_time,close_time,yes_bid,yes_ask,no_bid,no_ask,yes_bid_size,yes_ask_size,last_price,volume,open_interest,legs,leg_tickers".split(",")
def ms(y, mo, d, h=0, mi=0, se=0): return calendar.timegm((y, mo, d, h, mi, se)) * 1000
def iso(t): return __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(t // 1000))
assert s.DEV_START_MS == ms(2026, 11, 13) and s.DEV_END_MS == ms(2026, 11, 26) and s.HELD_START_MS == ms(2026, 11, 26) and s.HELD_END_MS == ms(2026, 12, 10)
assert s.READ_NOT_BEFORE["dev"] == ms(2026, 11, 26) // 1000 and s.READ_NOT_BEFORE["held"] == ms(2026, 12, 12) // 1000
def row(ticker, no_ask, recv, close_after_s=2 * 86400, event=None, size=5, vol=3, legs=3, legcell="", close=None, **kw):
    r = {c: "" for c in HDR}; r.update(t_recv_ms=str(recv), ticker=ticker, event_ticker=ticker + "-E" if event is None else event, close_time=iso(recv + close_after_s * 1000) if close is None else close, no_ask="%.4f" % no_ask if no_ask is not None else "",
         yes_bid_size=str(size), volume=str(vol), legs=str(legs), leg_tickers=legcell); r.update({k: str(v) for k, v in kw.items()}); return r
def put(root, date, hhmm, name, rows, hdr):
    d = os.path.join(root, "combo", date, hhmm); os.makedirs(d, exist_ok=True)
    with gzip.open(os.path.join(d, name), "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=hdr); w.writeheader(); [w.writerow({c: r.get(c, "") for c in hdr}) for r in rows]
def quotes(root, date, hhmm, rows): put(root, date, hhmm, "quotes.csv.gz", rows, HDR)
def results(root, date, hhmm, rows): put(root, date, hhmm, "results.csv.gz", [{"ticker": t, "result": r} for t, r in rows], ["ticker", "result"])
T0 = ms(2026, 11, 13, 12)
def fills_of(root, mode="dev"): return s.walk(root, mode)
# 1. price band edges, 2. other gates
with tempfile.TemporaryDirectory() as root:
    rows = [row("A1", 0.59, T0), row("A2", 0.5899, T0), row("A3", 0.89, T0), row("A4", 0.8901, T0), row("A5", 0.90, T0), row("A6", 1.0, T0), row("A7", None, T0),
            row("B1", 0.70, T0, size=2), row("B2", 0.70, T0, size=3), row("B3", 0.70, T0, vol=0), row("B4", 0.70, T0, legs=1), row("B5", 0.70, T0, legs=2), row("B6", 0.70, T0, legs=30), row("B7", 0.70, T0, legs=31),
            row("C1", 0.70, T0, close_after_s=3599), row("C2", 0.70, T0, close_after_s=3600), row("C3", 0.70, T0, close_after_s=1209600), row("C4", 0.70, T0, close_after_s=1209601), row("C5", 0.70, T0, close="garbage"),
            row("D1", 0.70, s.DEV_START_MS - 1), row("D2", 0.70, s.DEV_START_MS), row("D3", 0.70, s.DEV_END_MS - 1), row("D4", 0.70, s.DEV_END_MS)]
    quotes(root, "2026-11-13", "1200", rows)
    got = sorted(f["ticker"] for f in fills_of(root))
    # D3's receive instant is inside the window but belongs to a file whose other rows are earlier; cap of 10 applies (see below)
    qual = ["A1", "A3", "B2", "B5", "B6", "C2", "C3", "D2", "D3"]
    assert got == sorted(qual)[:10] and len(got) == 9, got
# 3. cap and blocking
with tempfile.TemporaryDirectory() as root:
    quotes(root, "2026-11-13", "1200", [row("K%02d" % i, 0.70, T0) for i in range(12)])
    quotes(root, "2026-11-13", "1230", [row("K%02d" % i, 0.70, T0 + 1800000) for i in range(12)])
    f = fills_of(root); assert [x["ticker"] for x in f] == ["K%02d" % i for i in range(10)] + ["K10", "K11"] and f[10]["ts"] == T0 + 1800000
with tempfile.TemporaryDirectory() as root:
    quotes(root, "2026-11-13", "1200", [row("E1", 0.70, T0, event="EV"), row("E2", 0.70, T0, event="EV"), row("N1", 0.70, T0, event=""), row("N2", 0.70, T0, event="")])
    quotes(root, "2026-11-13", "1230", [row("E2", 0.70, T0 + 1800000, event="EV"), row("E1", 0.70, T0 + 1800000, event="EV"), row("E3", 0.70, T0 + 1800000, event="EV")])
    assert sorted(x["ticker"] for x in fills_of(root)) == ["E1", "N1", "N2"]
with tempfile.TemporaryDirectory() as root:          # a duplicate ticker inside one snapshot fills once
    quotes(root, "2026-11-13", "1200", [row("Z", 0.70, T0), row("Z", 0.71, T0)]); f = fills_of(root); assert len(f) == 1 and abs(f[0]["p"] - 0.71) < 1e-12          # the first row of a ticker is used
# 4. cost and net
p = 0.80; c = p + 0.07 * p * (1 - p); assert abs(c - 0.8112) < 1e-12 and abs(s.cost_of(0.8) - 0.8112) < 1e-12
with tempfile.TemporaryDirectory() as root:
    quotes(root, "2026-11-13", "1200", [row("W", 0.79, T0, close_after_s=86400), row("L", 0.79, T0, close_after_s=86400)]); results(root, "2026-11-15", "0000", [("W", "no"), ("L", "yes")])
    fs = s.classify(fills_of(root), s.results_map(root), ms(2026, 11, 20))
    w = [f for f in fs if f["ticker"] == "W"][0]; l = [f for f in fs if f["ticker"] == "L"][0]
    assert abs(w["net"] - 0.1888) < 1e-9 and abs(l["net"] + 0.8112) < 1e-9 and abs(w["paper"] - 2 * 0.1888 / 0.8112) < 1e-9 and abs(l["paper"] + 2) < 1e-9 and abs(2 * 0.1888 / 0.8112 - 0.46548) < 1e-4
# 5. due and unresolved, other result
with tempfile.TemporaryDirectory() as root:
    close = ms(2026, 11, 14); recv = close - 86400000
    quotes(root, "2026-11-13", "1200", [row("U", 0.79, recv, close=iso(close)), row("O", 0.79, recv, close=iso(close)), row("S", 0.79, recv, close=iso(close))]); results(root, "2026-11-16", "0000", [("O", "maybe"), ("S", " NO ")])
    due = close + 48 * 3600000
    a = {f["ticker"]: f["status"] for f in s.classify(fills_of(root), s.results_map(root), due - 1000)}; assert set(a.values()) == {"not_due"}
    b = {f["ticker"]: f["status"] for f in s.classify(fills_of(root), s.results_map(root), due)}; assert b == {"U": "unresolved", "O": "other", "S": "settled"}, b
# 6. results precedence
with tempfile.TemporaryDirectory() as root:
    results(root, "2026-11-15", "0000", [("T", "yes")]); results(root, "2026-11-16", "0000", [("T", "no")]); assert s.results_map(root) == {"T": "yes"}
# 7/8/9. kill 1, kill 2, bar arithmetic on constructed fills (independent expected values)
def mk(n_win, n_loss, p=0.80, days=None, order="wl"):
    fs = []; c = s.cost_of(p)
    seq = ([1] * n_win + [0] * n_loss) if order == "wl" else ([0] * n_loss + [1] * n_win)
    for i, w in enumerate(seq):
        fs.append({"ticker": "T%03d" % i, "ts": i, "close": 0, "p": p, "cost": c, "legs": None, "due": True, "status": "settled", "net": (1 - c) if w else -c, "paper": ((1 - c) if w else -c) * 2 / c, "day": (days[i] if days else i % 12)})
    return fs
o = s.evaluate(mk(0, 21), "dev"); assert o["kill1_at"] == 21, o["kill1_at"]
o = s.evaluate(mk(0, 20), "dev"); assert o["kill1_at"] is None
o = s.evaluate(mk(40, 60), "dev"); assert abs(o["kill2_pf"] - 40 * 0.1888 / (60 * 0.8112)) < 1e-12 and o["kill2_fired"] and o["label"].startswith("KILLED")
o = s.evaluate(mk(100, 0), "dev"); assert o["kill2_pf"] == math.inf and not o["kill2_fired"]
o = s.evaluate(mk(90, 10), "dev"); assert abs(o["bar"]["net_per_dollar"] - 8.880 / 81.12) < 1e-9 and o["bar"]["net_ok"] and abs(8.880 / 81.12 - 0.109467) < 1e-6
o = s.evaluate(mk(89, 11), "dev"); assert abs(o["bar"]["net_per_dollar"] - 7.88 / 81.12) < 1e-9 and not o["bar"]["net_ok"] and o["label"] == "bar not met"
# bootstrap independent recomputation
fs = mk(90, 10, days=[i % 12 for i in range(100)]); days = sorted({f["day"] for f in fs}); rng = random.Random(20261112); out = []
for _ in range(2000):
    ch = [rng.choice(days) for _ in days]; sel = [f for d in ch for f in fs if f["day"] == d]; out.append(sum(f["net"] for f in sel) / sum(f["cost"] for f in sel))
out.sort(); assert abs(s.bootstrap(fs) - out[100]) < 1e-15 and s.bootstrap(fs) == s.bootstrap(list(reversed(fs)))
# date share and halves and distinct dates
fs = mk(90, 10, days=[0] * 50 + list(range(1, 51))); o = s.evaluate(fs, "dev"); tot = sum(f["net"] for f in fs); d0 = sum(f["net"] for f in fs if f["day"] == 0); assert abs(o["bar"]["share"] - d0 / tot) < 1e-12
fs = mk(90, 10, days=[i % 9 for i in range(100)]); o = s.evaluate(fs, "dev"); assert o["bar"]["dates"] == 9 and not o["bar"]["dates_ok"] and o["label"] == "bar not met"
fs = mk(90, 10, order="lw"); o = s.evaluate(fs, "dev"); assert o["bar"]["halves"][0] is not None
fs = mk(50, 50, order="wl"); fs2 = [dict(f) for f in fs]; o = s.evaluate(fs2, "dev"); h = 50; assert abs(o["bar"]["halves"][0] - sum(f["net"] for f in fs2[:h]) / sum(f["cost"] for f in fs2[:h])) < 1e-12 and o["bar"]["halves"][0] > 0 and o["bar"]["halves"][1] < 0 and not o["bar"]["halves_ok"]
# 10. labels
assert s.evaluate(mk(60, 39), "dev")["label"] == "no evidence at n = 99"
def withres(fs, due_unres):
    out = [dict(f) for f in fs]
    for i in range(due_unres): out.append({"ticker": "X%d" % i, "ts": 10 ** 6 + i, "close": 0, "p": 0.8, "cost": 0.8112, "legs": None, "due": True, "status": "unresolved"})
    return out
o = s.evaluate(withres(mk(90, 10), 20), "dev"); assert o["settled"] == 100 and o["due"] == 120 and abs(o["unresolved_share"] - 20 / 120) < 1e-15 and o["L1"] and o["label"] == "NOT_ENOUGH_DATA"
o = s.evaluate(withres(mk(90, 10), 11), "dev"); assert o["L1"] is False and abs(o["unresolved_share"] - 11 / 111) < 1e-15          # 9.9 percent
o = s.evaluate(withres(mk(90, 10), 10), "dev"); assert abs(o["unresolved_share"] - 10 / 110) < 1e-15 and o["L1"] is False
o = s.evaluate(withres(mk(135, 5), 15), "dev"); assert o["due"] == 155 and o["unresolved"] == 15  # 9.68 percent
assert s.evaluate(withres(mk(100, 0), 12), "dev")["L1"] is True          # 12 of 112 = 10.7 percent
# 12. weather and legs
with tempfile.TemporaryDirectory() as root:
    quotes(root, "2026-11-13", "1200", [row("WX", 0.70, T0, legcell="KXHIGHNY-26NOV15-T70:yes|KXNBAGAME-X-Y:no"), row("NW", 0.70, T0, legcell="KXNBAGAME-A-B:yes|KXMLBGAME-C-D:no|..."), row("UK", 0.70, T0), row("LT", 0.70, T0)])
    quotes(root, "2026-11-13", "1230", [row("LT", 0.70, T0 + 1800000, legcell="KXRAINSF-Z:yes")])
    fs = {f["ticker"]: f for f in fills_of(root)}
    assert s.is_weather(fs["WX"]) and not s.is_weather(fs["NW"]) and fs["UK"]["legs"] is None and fs["LT"]["legs"] == ["KXRAINSF-Z"] and fs["NW"]["legs"] == ["KXNBAGAME-A-B", "KXMLBGAME-C-D"]
    assert fs["NW"]["legs_complete"] is False and fs["WX"]["legs_complete"] is True and fs["LT"]["legs_complete"] is True and fs["UK"]["legs_complete"] is False
# 13. refusals and 14. printed output
with tempfile.TemporaryDirectory() as root:
    quotes(root, "2026-11-13", "1200", [row("SECRETTICKER1", 0.79, T0, close_after_s=86400)]); results(root, "2026-11-15", "0000", [("SECRETTICKER1", "no")])
    for mode, asof in (("dev", "2026-11-25T23:59:59Z"), ("held", "2026-12-11T23:59:59Z"), ("dev", "garbage")):
        try: s.run(mode, asof, root); raise AssertionError("not refused")
        except SystemExit as e: assert "STOP" in str(e)
    out = "\n".join(s.run("dev", "2026-11-26T00:00:00Z", root)); assert "ALL COMBOS (the registered line)" in out and "information only; the registered verdict is the all-combos line" in out and "SECRETTICKER1" not in out and "LABEL: no evidence at n = 1" in out and "would read: no evidence at n = 0" in out
    mon = "\n".join(s.run("monitor", "2026-11-14T00:00:00Z", root)); assert mon.startswith("MONITOR, not the registered verdict; the Nov 26 read is the verdict") and "SECRETTICKER1" not in mon and "LABEL" not in mon and "KILL" not in mon
    out2 = "\n".join(s.run("dev", "2026-11-26T00:00:00Z", root)); assert out == out2
# held mode: blocking from dev fills, window by receive instant
with tempfile.TemporaryDirectory() as root:
    quotes(root, "2026-11-13", "1200", [row("DEVF", 0.70, T0)]); quotes(root, "2026-11-26", "1200", [row("DEVF", 0.70, s.HELD_START_MS + 1000), row("HELDF", 0.70, s.HELD_START_MS + 1000), row("LATE", 0.70, s.HELD_END_MS)])
    assert [f["ticker"] for f in s.walk(root, "held")] == ["HELDF"] and [f["ticker"] for f in s.walk(root, "dev")] == ["DEVF"]
# a quotes file missing a required column stops
with tempfile.TemporaryDirectory() as root:
    put(root, "2026-11-13", "1200", "quotes.csv.gz", [{"ticker": "A"}], ["ticker"])
    try: s.walk(root, "dev"); raise AssertionError("not stopped")
    except SystemExit: pass
# ---- extra pins (mutation survivors) ----
def cf(net, cost=0.8, day=0, i=0): return {"ticker": "Q%d" % i, "ts": i, "close": 0, "p": 0.8, "cost": cost, "legs": None, "due": True, "status": "settled", "net": net, "paper": net * 2 / cost, "day": day}
# kill 2 at PF exactly 1.2 (6.0 over 5.0) is NOT killed (strictly under)
fs = [cf(0.5, i=i) for i in range(12)] + [cf(-1.0, i=20 + i) for i in range(5)] + [cf(0.0, i=40 + i) for i in range(83)]; o = s.evaluate(fs, "dev"); assert o["kill2_pf"] == 1.2 and o["kill2_fired"] is False
fs = [cf(0.5, i=i) for i in range(11)] + [cf(-1.0, i=20 + i) for i in range(5)] + [cf(0.0, i=40 + i) for i in range(84)]; assert s.evaluate(fs, "dev")["kill2_fired"] is True
# unresolved exactly 10 percent of due (12 of 120) is NOT over; 13 of 121 is
def mixed(ns, nu): return [cf(0.2, i=i, day=i % 12) for i in range(ns)] + [{"ticker": "X%d" % i, "ts": 10 ** 6 + i, "close": 0, "p": 0.8, "cost": 0.8, "legs": None, "due": True, "status": "unresolved"} for i in range(nu)]
assert s.evaluate(mixed(108, 12), "dev")["L1"] is False and s.evaluate(mixed(108, 13), "dev")["L1"] is True
# odd n: halves are the first floor(n/2) and the rest (n = 101: 50 and 51)
fs = [cf(0.3 if i < 50 else -0.1, cost=1.0, i=i, day=i % 12) for i in range(101)]; o = s.evaluate(fs, "dev"); assert abs(o["bar"]["halves"][0] - 15.0 / 50) < 1e-12 and abs(o["bar"]["halves"][1] - (-5.1) / 51) < 1e-12, o["bar"]["halves"]
# date share exactly 0.30 passes (30 of 100 equal nets on one date), 31 does not
fs = [cf(0.25, cost=1.0, i=i, day=0 if i < 30 else 1 + (i % 20)) for i in range(100)]; o = s.evaluate(fs, "dev"); assert abs(o["bar"]["share"] - 0.30) < 1e-12 and (o["bar"]["share"] <= 0.30) == o["bar"]["share_ok"]
fs = [cf(0.25, cost=1.0, i=i, day=0 if i < 31 else 1 + (i % 20)) for i in range(100)]; assert s.evaluate(fs, "dev")["bar"]["share_ok"] is False
# a full pass gives the label; bootstrap index with many varied dates matches an independent draw
rr = random.Random(5); fs = [cf(rr.choice([0.35, -0.5, 0.30, 0.31]), cost=1.0, i=i, day=i % 37) for i in range(300)]; days = sorted({f["day"] for f in fs}); rng = random.Random(20261112); out = []
for _ in range(2000):
    ch = [rng.choice(days) for _ in days]; sel = [f for d in ch for f in fs if f["day"] == d]; out.append(sum(f["net"] for f in sel) / sum(f["cost"] for f in sel))
out.sort(); assert s.bootstrap(fs) == out[100] and out[100] != out[101] and out[100] != out[99]
fs = [cf(0.25 if i % 10 else -0.4, cost=1.0, i=i, day=i % 13) for i in range(100)]; o = s.evaluate(fs, "dev"); assert o["bar_met"] and o["label"] == "paper edge shown (unproven)" and s.evaluate(fs, "held")["label"] == "bar met on the held-out read"
# every weather prefix
for pre in s.WEATHER: assert s.is_weather({"legs": [pre + "X-1"]}) and not s.is_weather({"legs": ["Q" + pre + "X-1"]})
assert s.WEATHER == ("KXHIGH", "KXLOW", "KXTEMP", "KXRAIN", "KXSNOW", "KXHURR", "KXTORN", "KXWIND")
# kill 1 threshold exactly -40: paper -2.05 a loss gives -41 after 20 (fires at 20); paper -1.9 gives -38 after 20 and -39.9 after 21 and -41.8 after 22 (fires at 22)
fs = [dict(cf(-0.5, cost=0.5, i=i, day=i), paper=-2.05) for i in range(20)]; assert s.evaluate(fs, "dev")["kill1_at"] == 20
fs = [dict(cf(-0.5, cost=0.5, i=i, day=i), paper=-1.9) for i in range(30)]; assert s.evaluate(fs, "dev")["kill1_at"] == 22
fs = [dict(cf(-0.5, cost=0.5, i=i, day=i), paper=-2.0) for i in range(20)]; assert s.evaluate(fs, "dev")["kill1_at"] is None
# ---- addendum 1: incomplete leg lists ----
def lg_case(cells):
    with tempfile.TemporaryDirectory() as root:
        for i, cell in enumerate(cells):
            quotes(root, "2026-11-13", "%02d00" % (12 + i), [row("INC", 0.70, T0 + i * 3600000, legcell=cell)])
        fs = fills_of(root); assert len(fs) == 1; f = fs[0]
        known = f["legs"] and f["legs_complete"] and not s.is_weather(f)
        return f["legs"], f["legs_complete"], bool(known), s.is_weather(f)
assert lg_case(["KXNBAGAME-A-B:yes|KXMLBGAME-C-D:no|..."]) == (["KXNBAGAME-A-B", "KXMLBGAME-C-D"], False, False, False)          # (a)
assert lg_case(["KXNBAGAME-A-B:yes|KXMLBGAME-C-D:no|...", "KXNBAGAME-A-B:yes|KXMLBGAME-C-D:no|KXNFLGAME-E-F:yes"]) == (["KXNBAGAME-A-B", "KXMLBGAME-C-D", "KXNFLGAME-E-F"], True, True, False)          # (b)
assert lg_case(["KXHIGHNY-X:yes|..."]) == (["KXHIGHNY-X"], False, False, True)          # (c)
assert lg_case(["KXNBAGAME-A-B:yes|KXMLBGAME-C-D:no", "KXNBAGAME-A-B:yes|..."]) == (["KXNBAGAME-A-B", "KXMLBGAME-C-D"], True, True, False)          # (d)
assert lg_case(["|..."]) == (None, False, False, False) and lg_case([""]) == (None, False, False, False)          # (e)
with tempfile.TemporaryDirectory() as root:
    quotes(root, "2026-11-13", "1200", [row("I1", 0.70, T0, legcell="KXNBAGAME-A-B:yes|..."), row("I2", 0.70, T0, legcell="KXNBAGAME-A-B:yes|KXMLBGAME-C-D:no"), row("I3", 0.70, T0), row("I4", 0.70, T0, legcell="KXHIGHNY-X:yes|...")])
    out = "\n".join(s.run("dev", "2026-11-26T00:00:00Z", root)); assert "legs incomplete (a cut list; in the all-combos line only): 2" in out and "combos with no stored legs (in the all-combos line only): 1" in out
    assert "paper fills 4," in out.split("COMBOS WITH LEGS KNOWN")[0] and "paper fills 1," in out.split("COMBOS WITH LEGS KNOWN")[1]
print("s3 build 2 tests passed")
