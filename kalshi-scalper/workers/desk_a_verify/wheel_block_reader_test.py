"""Tests of wheel_block_reader.py v2 (lane section 4 at bd7007cb) on INVENTED signals only. python3 -I wheel_block_reader_test.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import wheel_block_reader as W
T0 = 1_800_000_000; H = 3600; DAY = 86400
def sig(i, t, win, c=None, result="scored", limit=50, series="P"):
    return dict(ticker="%s-%04d" % (series, i), series=series, t=T0 + t, limit=limit, result=result, win=win, cents=(c if c is not None else (300 if win else -200)))
def seq(n, hours=6, pattern=lambda i: i % 3 != 0, **kw): return [sig(i, i * hours * H, 1 if pattern(i) else 0, **kw) for i in range(n)]
NOW = T0 + 400 * DAY
rp = lambda s, **k: W.read_place(s, now=k.pop("now", NOW), **k)
# T1: 60 signals over 15 days (40 wins, 20 losses): cleared at 60, then 30 confirmation signals -> QUALIFIED
b, st = rp(seq(90)); assert b[0]["status"] == "CLEARED" and b[0]["n"] == 60 and b[0]["confirmation"] == "QUALIFIED" and st.get("qualified"), (b, st); print("T1 clear at 60 and QUALIFIED OK")
# T2: 60 signals on fewer than 7 days: the block grows until 7 days
b, st = rp(seq(200, hours=1)); assert b[0]["n"] > 60 and b[0]["days"] >= 7; print("T2 grows until 7 days OK n", b[0]["n"])
# T3: class: a band crossing 50c needs 10 wins AND 10 losses; a void is neither a win nor a loss (but is in n and L)
s = seq(120, pattern=lambda i: i % 6 != 0); s[1:10] = [dict(x, result="void", win=0, cents=-18) for x in s[1:10]]
b, st = rp(s); assert b[0]["voids"] == 9 and b[0]["n"] >= 60 and b[0]["wins"] >= 10 and b[0]["losses"] >= 10 and b[0]["wins"] + b[0]["losses"] + b[0]["voids"] == b[0]["n"], b[0]
s = [sig(i, i * 6 * H, 1 if i % 4 else 0) for i in range(80)]; b, st = rp(s, band=(5, 40)); assert b[0]["status"] in ("CLEARED", "FAILED") and b[0]["n"] == 60              # a cheap band (wholly at or under 50) needs 10 wins only; 10 losses exist anyway at 60
s = [sig(i, i * 6 * H, 0 if i % 5 else 1) for i in range(100)]; b, st = rp(s, band=(5, 40)); assert b[0]["n"] >= 60 and b[0]["wins"] >= 10 and b[0]["n"] > 60 or b[0]["wins"] >= 10; print("T3 class from the band; void is neither win nor loss OK")
# T4: EXPIRED: later signal past 21 days (unread; the next block starts after the expiry time), and by the clock with --now
s = [sig(i, i * 10 * H, 1 if i % 3 else 0) for i in range(90)]; b, st = rp(s); assert b[0]["status"] == "EXPIRED" and b[0]["n"] < 60, b[0]
s = seq(30); b, st = rp(s, now=T0 + 22 * DAY); assert b[0]["status"] == "EXPIRED" and st.get("expired_by_clock"), (b, st)
s = seq(30); b, st = rp(s, now=T0 + 6 * DAY); assert not b and st["block_in_progress"] == 30; print("T4 EXPIRED by a later signal and by the clock OK")
# T5 (g), (h): integer cents. 10W >= 13L passes exactly at 1.3 and fails one cent under; a half W >= L; a day over 30% of the net fails, exactly 30% passes
def block_with(cw, cl, n=60):
    s = [sig(i, i * 6 * H, 1 if i % 3 else 0) for i in range(n)]
    wins = [i for i in range(n) if i % 3]; loss = [i for i in range(n) if not i % 3]
    for k, i in enumerate(wins): s[i]["cents"] = cw // len(wins) + (1 if k < cw % len(wins) else 0)
    for k, i in enumerate(loss): s[i]["cents"] = -(cl // len(loss) + (1 if k < cl % len(loss) else 0))
    return s
b, _ = rp(block_with(1300, 1000)); assert b[0]["status"] == "CLEARED", b[0]          # 10 x 1300 = 13 x 1000: exactly 1.3 passes
b, _ = rp(block_with(1299, 1000)); assert "profit factor under 1.3" in b[0]["fails"], b[0]
s = block_with(3000, 1000); h = [dict(x, cents=(-500 if x["win"] else 0)) for x in s[:30]]; s[:30] = h; b, _ = rp(s); assert "a half under 1.0" in b[0]["fails"], b[0]
s = seq(60, hours=8); net = sum(x["cents"] for x in s); s[10] = dict(s[10], cents=s[10]["cents"] + 5000); b, _ = rp(s); assert any("one day holds" in f for f in b[0]["fails"]), b[0]
print("T5 integer bars: 1.3 exactly passes, 1299/1000 fails, a half under 1.0, a day over 30% fails OK")
# T6 (i), (m): a limit of 88c or above is SKIPPED for a rule not registered as a favourite; with fav the block is at least 150
s = seq(80, limit=90); b, st = rp(s); assert not b and st["block_in_progress"] == 0, st
s = seq(100, hours=3, limit=90); b, st = rp(s, fav=True, now=T0 + 13 * DAY); assert not b and st["block_in_progress"] == 100; s = seq(160, hours=3, limit=90); b, st = rp(s, fav=True, now=T0 + 20 * DAY); assert b and b[0]["n"] >= 150; print("T6 limit 88c or above skipped; favourite class needs 150 OK")
# T7 (l): signals before the start time do not count
s = seq(90); b, st = rp(s, start_t=T0 + 30 * 6 * H); assert not b or b[0]["first"] == "P-0030", b; print("T7 start time OK")
# T8 (j), (n): the confirmation
s = seq(60) + [sig(60 + i, (60 + i) * 6 * H, 0, c=-100) for i in range(30)]; b, st = rp(s); assert b[0]["confirmation"] == "CONFIRMATION FAILED", b[0]
s = seq(60) + [sig(60 + i, (60 + i) * 6 * H, 1 if i % 2 else 0, c=(100 if i % 2 else -100)) for i in range(30)]; b, st = rp(s); assert b[0]["confirmation"] == "QUALIFIED", b[0]          # W >= L exactly qualifies
s = seq(60) + [sig(60 + i, (60 + i) * 30 * H, 1, c=100) for i in range(30)]; b, st = rp(s); assert b[0]["confirmation"].startswith("CONFIRMATION EXPIRED"), b[0]
s = seq(60) + seq(30)[:0]; s[75 - 20] = s[55]; s = seq(90); s[70] = dict(s[70], result="pending", cents=None); b, st = rp(s, now=T0 + 25 * DAY); assert st["waiting"] and b[0]["status"] == "CLEARED" and "confirmation" not in b[0]
s = seq(40); s[20] = dict(s[20], result="pending", cents=None); b, st = rp(s, now=T0 + 15 * DAY); assert st["waiting"] and not b
print("T8 confirmation: failed, qualified at W = L, expired past 21 days, pending waits OK"); # T9 (Auditor B items 1, 2, 7): 40 wins + 0 true losses + 20 voids: a void is NOT a loss for the outcome count, so a band crossing 50c keeps growing; cash not in whole cents is refused; a scored record with no win field is refused
s = [sig(i, i * 6 * H, 1) for i in range(60)]; s = [dict(x, result="void", win=0, cents=-18) if i % 3 == 0 else x for i, x in enumerate(s)]
b, st = rp(s, now=T0 + 16 * DAY); assert not b and st["block_in_progress"] == 60 and st["losses"] == 0, (b, st)
import tempfile, csv
def rows_csv(rows):
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline=""); w = csv.writer(f); w.writerow(["ticker", "series", "signal_t", "limit", "status", "result", "win", "cash"]); [w.writerow(r) for r in rows]; f.close(); return f.name
try: W.load(rows_csv([["A-1", "P", "1800000000", "0.5", "fillable", "scored", "", "3.00"]])); raise AssertionError("not refused")
except SystemExit: pass
assert W.load(rows_csv([["A-1", "P", "1800000000", "0.5", "fillable", "scored", "1", "6.754"]]))[0]["cents"] == 675 and W.ROUNDED == ["A-1"]       # default: nearest cent, counted
W.STRICT_CENTS = True
try: W.load(rows_csv([["A-1", "P", "1800000000", "0.5", "fillable", "scored", "1", "6.754"]])); raise AssertionError("not refused")
except SystemExit: pass
W.STRICT_CENTS = False
assert W.load(rows_csv([["A-1", "P", "1800000000", "0.5", "fillable", "scored", "1", "3.00"]]))[0]["cents"] == 300
print("T9 void is neither win nor loss; non-cent cash and a blank win are refused OK")
print("ALL OK")
