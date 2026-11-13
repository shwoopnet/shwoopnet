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
recs, why = S.replay(d, now=base + 10 ** 6)
by = {r["ticker"].split("-")[1]: r for r in recs}
assert sorted(by) == ["A", "B", "F", "I"], sorted(by)
a = by["A"]; assert a["side"] == "yes" and abs(a["p"] - 0.40) < 1e-12 and a["win"] == 1 and a["fee"] == 0.02 and abs(a["cash"] - (1 - 0.40 - 0.02)) < 1e-12 and abs(a["cash12"] - (1 - 0.40 - 0.024)) < 1e-12, a   # fee 0.07*.4*.6=0.0168 -> 0.02
b = by["B"]; assert b["side"] == "no" and abs(b["p"] - 0.70) < 1e-12 and b["win"] == 0 and b["fee"] == 0.02 and abs(b["cash"] - (0 - 0.70 - 0.02)) < 1e-12, b                    # 0.07*.7*.3=0.0147 -> 0.02
f_ = by["F"]; assert f_["result"] == "void" and abs(f_["cash"] + f_["fee"]) < 1e-12, f_
i_ = by["I"]; assert i_["side"] == "yes" and abs(i_["p"] - 0.50) < 1e-12 and i_["win"] == 0, i_                                     # the +1.0 s poll (ask 0.50), result no -> yes loses
assert why["not in the cell"] == 1 and why["ask outside 0.10 to 0.90 or under 1 contract displayed"] == 2 and why["no entry poll in 1 s to 20 s"] == 1 and why["closes before 2026-11-19 (never scored)"] == 1, dict(why)
L = S.report(recs, why); assert "BELOW THE REGISTERED MINIMUM" in L[1] and len(L) == 2, L           # four trades: no figure is read
S.MIN_N = 3; L2 = S.report(recs, why); assert any(x.startswith("LABEL: keep recording") or x.startswith("LABEL: cleared") or x.startswith("LABEL: FALSIFIED") for x in L2), L2
assert S.fee_up(0.5) == 0.02 and S.fee_up(0.1) == 0.01 and S.fee_up(0.4) == 0.02
# default-closed and the guard
import subprocess
r = subprocess.run([sys.executable, "-I", os.path.join(here, "nc15depth1.py"), tempfile.mkdtemp()], capture_output=True, text=True); assert r.returncode != 0 and "REFUSED" in (r.stderr + r.stdout)
print("NC15DEPTH1 TEST OK (side, price, fee rounding, stress fee, void, cutoff, entry poll rule, size 0, band, minimum, default-closed)")
print("\n".join(L2))
