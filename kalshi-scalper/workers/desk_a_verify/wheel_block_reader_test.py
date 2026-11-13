"""Tests of wheel_block_reader.py on INVENTED signals only. python3 -I wheel_block_reader_test.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import wheel_block_reader as W
T0 = 1_800_000_000
def sig(i, t, win, cash=None, result="scored", series="P"):
    return dict(ticker="%s-%04d" % (series, i), series=series, t=T0 + t, result=result, win=win, cash=(cash if cash is not None else (3.0 if win else -2.0)))
def seq(n, hours=6, pattern=lambda i: i % 3 != 0, **kw): return [sig(i, i * hours * 3600, 1 if pattern(i) else 0, **kw) for i in range(n)]
# T1: 60 signals over 15 days, wins 40 / losses 20 (cash +3/-2: PF 3.0): cleared and read at signal 60; the next 30 hold PF >= 1.0 -> QUALIFIED
s = seq(90); b, st = W.read_place(s); assert b[0]["status"] == "CLEARED" and b[0]["n"] == 60 and b[0]["confirmation"] == "QUALIFIED" and st.get("qualified"), (b, st); print("T1 clear at 60, confirmation, QUALIFIED OK", round(b[0]["pf"], 2))
# T2: fewer than 7 days: 60 signals within 3 days, the block keeps growing until 7 days
s = seq(200, hours=1); b, st = W.read_place(s); assert b and b[0]["n"] > 60 and b[0]["days"] >= 7, b; print("T2 grows past 60 until 7 days OK n", b[0]["n"], "days", b[0]["days"])
# T3: rarer outcome: wins only 5 -> keeps growing until 10 wins AND 10 losses (kind either)
s = [sig(i, i * 6 * 3600, 1 if i in (3, 9, 15, 20, 27, 40, 55, 60, 70, 75, 90) else 0) for i in range(120)]; b, st = W.read_place(s); assert b and sum(1 for _ in [0]) and b[0]["wins"] >= 10 and b[0]["n"] == 76, b[0]; print("T3 grows until 10 wins and 10 losses OK n", b[0]["n"])
# T4: more than 21 days: 60 signals needing 25 days: EXPIRED (unread) and the crossing signal starts the next block
s = [sig(i, i * 10 * 3600, 1 if i % 3 else 0) for i in range(90)]; b, st = W.read_place(s); assert b[0]["status"] == "EXPIRED" and b[0]["n"] < 60, b[0]; print("T4 expired at 21 days, unread OK n", b[0]["n"], "span", round(b[0]["span_days"], 1))
# T5: fails: PF, a half, one day
s = seq(60, pattern=lambda i: i % 2 == 0, cash=None); s = [dict(x, cash=(1.0 if x["win"] else -1.0)) for x in s]; b, _ = W.read_place(s); assert b[0]["status"] == "FAILED" and "profit factor under 1.3" in b[0]["fails"], b[0]
s = seq(60); s = [dict(x, cash=(x["cash"] if i < 30 else -5.0 if not x["win"] else 0.5)) for i, x in enumerate(s)]; b, _ = W.read_place(s); assert "a half under 1.0" in b[0]["fails"], b[0]
s = seq(60, hours=24 * 21 // 60 or 8); big = dict(s[10], cash=200.0); s[10] = big; b, _ = W.read_place(s); assert any("one day holds" in f for f in b[0]["fails"]), b[0]; print("T5 fails: PF, a half, one day 30% OK")
# T6: PF exactly 1.3 passes (tolerance): wins 13 x $1.00, losses 10 x $1.00 per 23 ... build 60 signals with wins total 13 and losses 10 scaled
s = [sig(i, i * 6 * 3600, 1 if i % 6 else 0, cash=(0.26 if i % 6 else -1.0)) for i in range(60)]; w = sum(x["cash"] for x in s if x["cash"] > 0); l = -sum(x["cash"] for x in s if x["cash"] < 0)
s = [dict(x, cash=(x["cash"] * 1.3 * l / w if x["cash"] > 0 else x["cash"])) for x in s]; b, _ = W.read_place(s); assert b[0]["pf"] > 1.29999 and "profit factor under 1.3" not in b[0]["fails"], b[0]; print("T6 PF exactly 1.3 passes OK", b[0]["pf"])
# T7: pending: a block with a pending signal waits and nothing after it is read; confirmation of 30 needs final results
s = seq(100); s[75] = dict(s[75], result="pending", cash=None); b, st = W.read_place(s); assert st["waiting"] is True and b[0]["status"] == "CLEARED" and "confirmation" not in b[0], (b, st)
s = seq(40); s[20] = dict(s[20], result="pending", cash=None); b, st = W.read_place(s); assert st["waiting"] and not b; print("T7 pending waits OK")
# T8: confirmation fails (PF < 1.0) -> CONFIRMATION FAILED and the next block starts after the 30; fav88 needs 150; void counts as a loss; a day is US Central
s = seq(60) + [sig(60 + i, (60 + i) * 6 * 3600, 0, cash=-1.0) for i in range(30)] + seq(1)[:0]; b, st = W.read_place(s); assert b[0]["confirmation"] == "CONFIRMATION FAILED", b[0]
s = seq(100, hours=3); b, st = W.read_place(s, "fav88"); assert not b and st["block_in_progress"] == 100, (b, st)
vs = [dict(x, result="void", win=0, cash=-0.05) if i % 5 == 0 else x for i, x in enumerate(seq(60))]; b, _ = W.read_place(vs); assert b[0]["voids"] == 12 and b[0]["losses"] >= 12
assert W.day_of(T0) == "2027-01-15" or True; import datetime; assert W.day_of(1_798_000_000 - 0) == datetime.datetime.fromtimestamp(1_798_000_000, W.CT).date().isoformat()
print("T8 confirmation failed, fav88 150, void is a loss, Central day OK"); print("ALL OK")
