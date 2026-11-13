"""NC15DEPTH1 scorer test on a MADE-UP fixture (hand-computed). python3 -I nc15depth1_test.py"""
import sys, os, csv, gzip, tempfile, calendar, time, importlib.util
from email.utils import formatdate
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import nc15depth1 as S
COLS = ["t_recv_ms", "server_date_header", "ticker", "series", "close_time"] + ["%s_%s_%d" % (a, b, i) for a in ("yes_bid", "no_bid") for b in ("px", "sz") for i in range(1, 6)]
def iso(t): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
def row(t, tk, ser, close, yes=None, no=None):
    """exchange time t (true), header = t - 0.5 truncated so offset ~ 0.5 - ... : set t_recv = t*1000 and header = t - 0.5 => offset exactly 0 (median of h + 0.5 - recv)."""
    r = dict(t_recv_ms=int(t * 1000), server_date_header=formatdate(t - 0.5, usegmt=True), ticker=tk, series=ser, close_time=iso(close))
    for pre, lv in (("yes_bid", yes or []), ("no_bid", no or [])):
        for i in range(1, 6):
            p, s = lv[i - 1] if i <= len(lv) else ("", "")
            r["%s_px_%d" % (pre, i)] = p; r["%s_sz_%d" % (pre, i)] = s
    return r
d = tempfile.mkdtemp(); os.makedirs(d + "/2026-11-20/0000"); open(d + "/MADE_UP_DATA", "w").write("x")
base = calendar.timegm(time.strptime("2026-11-20", "%Y-%m-%d")) + 3600
rows, cov = [], []
def window(name, close, look_book, fill_book, fill_dt=1.0, result="yes", ser="KXCOPPER15M"):
    tk = ser + "-" + name; D = close - 600
    rows.append(row(D - 2, tk, ser, close, *look_book)); rows.append(row(D, tk, ser, close, *look_book))
    if fill_dt is not None: rows.append(row(D + fill_dt, tk, ser, close, *fill_book))
    cov.append(dict(ticker=tk, result=result))
# A: YES side. look: yes sizes 90 vs no 10 -> imb 0.8; fill: NO best bid 0.60 -> ask 0.40, size 5 -> p 0.40, win (yes)
window("A", base + 900, ([(0.55, 60), (0.54, 30)], [(0.60, 10)]), ([(0.55, 60)], [(0.60, 5)]), result="yes")
# B: NO side. look: yes 10, no 90 -> imb -0.8; NO buys at 1 - best YES bid 0.30 -> 0.70, result yes -> NO loses
window("B", base + 1800, ([(0.30, 10)], [(0.65, 60), (0.64, 30)]), ([(0.30, 4)], [(0.65, 60)]), result="yes")
# C: out of the cell (imb 0.2)
window("C", base + 2700, ([(0.55, 60)], [(0.40, 40)]), ([(0.55, 60)], [(0.60, 5)]), result="yes")
# D: ask outside the band (NO bid 0.05 -> ask 0.95)
window("D", base + 3600, ([(0.55, 90)], [(0.05, 10)]), ([(0.55, 90)], [(0.05, 5)]), result="yes")
# E: fill poll too early only (+0.5 s) -> no entry poll in 1 s to 20 s
window("E", base + 4500, ([(0.55, 90)], [(0.60, 10)]), ([(0.55, 90)], [(0.60, 5)]), fill_dt=0.5)
# F: void result
window("F", base + 5400, ([(0.55, 90)], [(0.60, 10)]), ([(0.55, 90)], [(0.60, 5)]), result="void")
# G: closes before 2026-11-19: never scored
window("G", calendar.timegm(time.strptime("2026-11-18", "%Y-%m-%d")) + 3600, ([(0.55, 90)], [(0.60, 10)]), ([(0.55, 90)], [(0.60, 5)]))
# H: displayed size 0 at the ask
window("H", base + 6300, ([(0.55, 90)], [(0.60, 10)]), ([(0.55, 90)], [(0.60, 0)]))
# I: fill poll at exactly +1.0 s picks that poll, not a later one at +3 s with a different price
tk = "KXWTI15M-I"; close = base + 7200; D = close - 600
for t, no in ((D - 1, [(0.60, 10)]), (D, [(0.60, 10)]), (D + 1.0, [(0.50, 5)]), (D + 3.0, [(0.10, 5)])): rows.append(row(t, tk, "KXWTI15M", close, [(0.55, 90)], no))
cov.append(dict(ticker=tk, result="no"))
with gzip.open(d + "/2026-11-20/0000/book.csv.gz", "wt", newline="") as f:
    w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)
with gzip.open(d + "/2026-11-20/0000/coverage.csv.gz", "wt", newline="") as f:
    w = csv.DictWriter(f, ["ticker", "result"]); w.writeheader(); w.writerows(cov)
# J: look poll exactly at D-10 (inside), K: look poll at D-10.001 (outside), L: fill at exactly +20 s (inside), M: fill at +20.001 s (outside)
def custom(name, close, polls, result="yes", ser="KXBNB15M"):
    tk = ser + "-" + name
    for t, yes, no in polls: rows.append(row(t + 0.5, tk, ser, close, yes, no))      # the fixture's exchange offset is -0.5 s for every integer-second row (header truncation), so recv = exchange + 0.5; these few fractional rows stay a minority of the rolling median
    cov.append(dict(ticker=tk, result=result))
Y, N0 = [(0.55, 90)], [(0.60, 10)]; NF = [(0.60, 5)]
cj = base + 8100; custom("J", cj, [(cj - 600 - 10, Y, N0), (cj - 600 + 1.0, Y, NF)])      # the later poll is after D, so the poll at exactly D-10 is the look
ck = base + 9000; custom("K", ck, [(ck - 600 - 10.001, Y, N0), (ck - 600 + 1.0, Y, NF)])
cl = base + 9900; custom("L", cl, [(cl - 600, Y, N0), (cl - 600 + 20.0, Y, NF)])
cm = base + 10800; custom("M", cm, [(cm - 600, Y, N0), (cm - 600 + 20.001, Y, NF)])
cp = base + 11700; custom("P", cp, [(cp - 600, Y, N0), (cp - 600 + 1.0, Y, NF)], result="")           # empty result: UNRESOLVED (Head F2), also long after the close
with gzip.open(d + "/2026-11-20/0000/book.csv.gz", "wt", newline="") as f:
    w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)
with gzip.open(d + "/2026-11-20/0000/coverage.csv.gz", "wt", newline="") as f:
    w = csv.DictWriter(f, ["ticker", "result"]); w.writeheader(); w.writerows(cov)
recs0, _ = S.replay(d, now=base + 12000)
assert {r["ticker"].split("-")[1]: r["result"] for r in recs0 if r["ticker"].split("-")[1] in "JLP"} == {"J": "scored", "L": "scored", "P": "unresolved"}, recs0      # F2: no recorded result is unresolved at once, never pending, never booked
recs, why = S.replay(d, now=base + 10 ** 6)
assert "K" not in {r["ticker"].split("-")[1] for r in recs} and "M" not in {r["ticker"].split("-")[1] for r in recs}
assert {r["ticker"].split("-")[1]: r["result"] for r in recs}["P"] == "unresolved" and "cash" not in [r for r in recs if r["ticker"].endswith("-P")][0]
recs = [r for r in recs if r["ticker"].split("-")[1] not in ("J", "L", "P")]; why = {k: v for k, v in why.items()}
by = {r["ticker"].split("-")[1]: r for r in recs}
assert sorted(by) == ["A", "B", "F", "I"], sorted(by)
a = by["A"]; assert a["side"] == "yes" and abs(a["p"] - 0.40) < 1e-12 and a["win"] == 1 and a["fee"] == 0.02 and abs(a["cash"] - (1 - 0.40 - 0.02)) < 1e-12 and abs(a["cash12"] - (1 - 0.40 - 0.024)) < 1e-12, a   # fee 0.07*.4*.6=0.0168 -> 0.02
b = by["B"]; assert b["side"] == "no" and abs(b["p"] - 0.70) < 1e-12 and b["win"] == 0 and b["fee"] == 0.02 and abs(b["cash"] - (0 - 0.70 - 0.02)) < 1e-12, b                    # 0.07*.7*.3=0.0147 -> 0.02
f_ = by["F"]; assert f_["result"] == "void" and abs(f_["cash"] + f_["fee"]) < 1e-12, f_
i_ = by["I"]; assert i_["side"] == "yes" and abs(i_["p"] - 0.50) < 1e-12 and i_["win"] == 0, i_                                     # the +1.0 s poll (ask 0.50), result no -> yes loses
assert why["not in the cell"] == 1 and why["ask outside 0.10 to 0.90 or under 1 contract displayed"] == 2 and why["no look poll"] == 1 and why["no entry poll in 1 s to 20 s"] == 2 and why["closes before 2026-11-19 (never scored)"] == 1, dict(why)
L = S.report(recs, why); assert "no evidence at n = 4" in L[1] and "BELOW THE REGISTERED MINIMUM" in L[1] and len(L) == 2 and "UNRESOLVED" in L[0], L           # four trades: no figure is read
S.MIN_N = 3; L2 = S.report(recs, why); assert any(x.startswith("LABEL: SURVIVES") or x.startswith("LABEL: FALSIFIED") for x in L2), L2
# F1: an empty group fails every bar test; inf only for wins and no loss
assert S.pf([]) is None and S.pf([0.5, 0.2]) == float("inf") and not S.ge(S.pf([]), 1.5) and not S.gt(S.pf([]), 1.0) and S.ge(float("inf"), 1.5)
# groups and the bar on synthetic trades (n >= MIN_N lowered to 40 for the test only)
import datetime
def mk(day, cash, win=1): return dict(day=datetime.date(2026, 11, 19) + datetime.timedelta(days=day), cash=cash, cash12=cash - 0.004, win=win, result="scored")
good = [mk(i % 10, 0.30 if j % 4 else -0.20, 1 if j % 4 else 0) for i in range(10) for j in range(4)] + [mk(i % 10, 0.05) for i in range(10)]
assert [len(g) for g in S.groups(good, 3)] == [20, 20, 10] and [len(g) for g in S.groups(good, 2)] == [25, 25]
S.MIN_N = 40; Lg = S.report(good, {}); assert any(x.startswith("LABEL: SURVIVES") or x.startswith("LABEL: FALSIFIED") for x in Lg), Lg
bad = [mk(i % 10, -0.3, 0) for i in range(60)]; S.MIN_N = 40; Lb = S.report(bad, {}); assert any(x.startswith("LABEL: FALSIFIED") for x in Lb), Lb
S.MIN_N = 3
assert S.fee_up(0.5) == 0.02 and S.fee_up(0.1) == 0.01 and S.fee_up(0.4) == 0.02
# read-once marker: the second figure-printing run refuses
mk_ = os.path.join(tempfile.mkdtemp(), "m.txt"); S.read_once(mk_)
try: S.read_once(mk_); raise AssertionError("second read not refused")
except SystemExit: pass
# a void: a present result that is neither yes nor no (window F above); an empty result is unresolved (window P above)
# default-closed and the guard
import subprocess
r = subprocess.run([sys.executable, "-I", os.path.join(here, "nc15depth1.py"), tempfile.mkdtemp()], capture_output=True, text=True); assert r.returncode != 0 and "REFUSED" in (r.stderr + r.stdout)
print("NC15DEPTH1 TEST OK (side, price, fee rounding, stress fee, void, unresolved, cutoff, entry poll rule, edges, size 0, band, minimum, bar logic, empty group, read-once, default-closed)")
print("\n".join(L2))
