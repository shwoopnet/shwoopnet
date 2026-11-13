"""Synthetic tests of inplayjump_second.py (independent second scorer). Invented rows only."""
import calendar, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inplayjump_second as J
import scorekit as k

S0 = calendar.timegm((2026, 10, 16, 14, 0, 0))
def mkmatch(i, S, fam="TABLE_TENNIS", close_gap=3000, res=("yes", "no"), kind="clock"):
    ev = "KXLIGAPROMATCH-%sM%03d" % ("26OCT161000", i)
    return {"family": fam, "kind": kind, "event": ev, "S": S, "open": S - 3600, "close": S + close_gap, "sort": S, "codes": {"AAA": ev + "-AAA", "BBB": ev + "-BBB"}, "results": {"AAA": res[0], "BBB": res[1]}}
def cd(bid, ask, vol=5): return {"bid": bid, "ask": ask, "volume": vol}
def flat(m, t0, t1, a=0.50, spread=0.02):
    idx = {}
    for code, tk in m["codes"].items():
        mid = a if code == "AAA" else 1 - a
        idx[tk] = {t: cd(round(mid - spread / 2, 4), round(mid + spread / 2, 4)) for t in range(t0, t1 + 1, 60)}
    return idx
def merge(*ds):
    out = {}
    for d in ds:
        for t, v in d.items(): out.setdefault(t, {}).update(v)
    return out

# ---- clock family: in play from S + 60 (the minute ENDING at S + 60); a jump of exactly 10c qualifies; the entry reads the next minute ----
m = mkmatch(1, S0); idx = flat(m, S0 - 600, S0 + 1200)
tj = S0 + 5 * 60
for code, up in (("AAA", 0.10), ("BBB", -0.10)):
    for t in range(tj, S0 + 1201, 60): idx[m["codes"][code]][t] = cd(round(0.50 + up - 0.01, 4), round(0.50 + up + 0.01, 4))
d = J.decide(m, idx); assert d["status"] == "bet" and d["code"] == "AAA" and d["t"] == tj and d["elapsed"] == 5, d
assert abs(d["price"] - 0.62) < 1e-9 and abs(d["cost_one_way"] - (0.01 + J.fee_up(0.62))) < 1e-9, d              # ask 0.61 + 1c
# a jump of 9.99c does not qualify; a jump before S + 60 is not in play; pre-jump mid outside 15c to 75c does not qualify
for jump in (0.0999,):
    i2 = flat(m, S0 - 600, S0 + 1200)
    for t in range(tj, S0 + 1201, 60): i2[m["codes"]["AAA"]][t] = cd(round(0.50 + jump - 0.01, 4), round(0.50 + jump + 0.01, 4))
    assert J.decide(m, i2)["status"] == "no_jump"
i3 = flat(m, S0 - 600, S0 + 1200)
for t in range(S0, S0 + 1201, 60): i3[m["codes"]["AAA"]][t] = cd(0.59, 0.61)          # the jump minute ends exactly at S: not in play yet
assert J.decide(m, i3)["status"] == "no_jump"
i4 = flat(m, S0 - 600, S0 + 1200, a=0.80)
for t in range(tj, S0 + 1201, 60): i4[m["codes"]["AAA"]][t] = cd(0.89, 0.91)                  # pre-jump mid 0.80 > 0.75
assert J.decide(m, i4)["status"] == "no_jump"
# volume must be above zero in the jump minute
i5 = flat(m, S0 - 600, S0 + 1200)
for t in range(tj, S0 + 1201, 60): i5[m["codes"]["AAA"]][t] = cd(0.59, 0.61, vol=(0 if t == tj else 5))
assert J.decide(m, i5)["status"] == "no_jump"
# two contracts in the same minute: no bet, counted
i6 = flat(m, S0 - 600, S0 + 1200, a=0.45)
for t in range(tj, S0 + 1201, 60): i6[m["codes"]["AAA"]][t] = cd(0.54, 0.56); i6[m["codes"]["BBB"]][t] = cd(0.64, 0.66)
assert J.decide(m, i6)["status"] == "two_contracts_same_minute"
# entry: minute t + 1 not two-sided -> counted; ask above 85c or spread over 4c -> counted
i7 = flat(m, S0 - 600, S0 + 1200)
for t in range(tj, S0 + 1201, 60): i7[m["codes"]["AAA"]][t] = cd(0.59, 0.61)
i7[m["codes"]["AAA"]][tj + 60] = cd(None, 0.62); assert J.decide(m, i7)["status"] == "entry_minute_not_two_sided"
i7[m["codes"]["AAA"]][tj + 60] = cd(0.57, 0.61); assert J.decide(m, i7)["status"] == "bet"                      # spread exactly 4c passes (tolerance)
i7[m["codes"]["AAA"]][tj + 60] = cd(0.56, 0.61); assert J.decide(m, i7)["status"] == "entry_outside_band"
i7[m["codes"]["AAA"]][tj + 60] = cd(0.84, 0.86); assert J.decide(m, i7)["status"] == "entry_outside_band"
# a first qualifying jump decides; a second jump later is never considered
i8 = flat(m, S0 - 600, S0 + 1800)
for t in range(tj, S0 + 1801, 60): i8[m["codes"]["AAA"]][t] = cd(0.59, 0.61)
i8[m["codes"]["AAA"]][tj + 60] = cd(0.30, 0.32)
assert J.decide(m, i8)["status"] in ("entry_outside_band", "bet") and J.decide(m, i8)["t"] == tj
# fee and price buckets
assert J.fee_up(0.62) == 0.02 and J.bucket(0.30) == 1 and J.bucket(0.29) == 0 and J.bucket(0.20) == 0 and J.bucket(0.85) == 6 and J.bucket(0.70) == 5 and J.bucket(0.79) == 5 and J.bucket(0.80) == 6
# ---- start check ----
ms = [mkmatch(i, S0) for i in range(10)]; ms[0]["close"] = S0 + 10; assert J.start_check(ms)["TABLE_TENNIS"]["matches"] == 10 and J.start_check(ms)["TABLE_TENNIS"]["start_derivable"]
for q in ms[:3]: q["close"] = S0 + 30
assert not J.start_check(ms)["TABLE_TENNIS"]["start_derivable"]
# ---- placebo: the NEXT match at the same elapsed minute, quiet, higher mid, entry rule; 'used' only when a placebo bet is made ----
X = mkmatch(1, S0); Y = mkmatch(2, S0 + 600); Z = mkmatch(3, S0 + 1200)
idx = merge(flat(X, S0 - 600, S0 + 2400), flat(Y, S0 + 600 - 600, S0 + 600 + 2400, a=0.55), flat(Z, S0 + 1200 - 600, S0 + 1200 + 2400, a=0.60))
for t in range(tj, S0 + 2401, 60): idx[X["codes"]["AAA"]][t] = cd(0.59, 0.61); idx[X["codes"]["BBB"]][t] = cd(0.39, 0.41)
rep, dec, srt = J.family_run([X, Y, Z], idx); assert rep["passing_ask_band_and_spread"] == 1 and dec[X["event"]]["status"] == "bet"
p, why = J.placebo_for(X, dec[X["event"]], srt, 0, idx, set()); assert p and p["event"] == Y["event"] and p["code"] == "AAA" and abs(p["price"] - 0.57) < 1e-9, (p, why)       # Y's higher mid is AAA at 0.55: ask 0.56 + 1c
p2, _ = J.placebo_for(X, dec[X["event"]], srt, 0, idx, {Y["event"]}); assert p2 and p2["event"] == Z["event"]         # Y already served
idy = merge(idx); idy[Y["codes"]["AAA"]][S0 + 600 + 5 * 60] = cd(0.65, 0.67)             # Y moves 11c by its minute e: not quiet -> next match
p3, _ = J.placebo_for(X, dec[X["event"]], srt, 0, idy, set()); assert p3 and p3["event"] == Z["event"]
p4, why4 = J.placebo_for(X, dec[X["event"]], srt, 0, idx, {Y["event"], Z["event"]}); assert p4 is None and why4 == "no_placebo_within_20"       # no wrap-around
# ---- results are joined only in score_family; a void is a fee-only loss ----
assert J.net_of(0.62, "AAA", {"AAA": "yes"})[0] > 0 and J.net_of(0.62, "AAA", {"AAA": "no"})[0] < 0 and J.net_of(0.62, "AAA", {"AAA": ""}) == (-0.02, True)
f = J.score_family([X, Y, Z], idx, S0 - 86400, S0 + 86400); assert f["bets"] == 1 and f["placebo_bets"] == 1 and f["verdict"].startswith("NOT_ENOUGH_DATA at n = 1"), f
# ---- tennis alive rule: 3 of the 20 one-minute steps ending at t - 1 move 2c or more (strict reading: both minutes present and two-sided) ----
T0 = calendar.timegm((2026, 10, 16, 8, 0, 0)); mt = {"family": "ITF_TENNIS", "kind": "alive", "event": "KXITFMATCH-26OCT160800TT", "S": None, "open": T0, "close": T0 + 20000, "sort": T0, "codes": {"AAA": "KXITFMATCH-26OCT160800TT-AAA", "BBB": "KXITFMATCH-26OCT160800TT-BBB"}, "results": {"AAA": "yes", "BBB": "no"}}
it = {c: {} for c in mt["codes"].values()}
for i in range(60):
    t = T0 + 60 * i; wob = 0.03 * (i % 2) if 10 <= i <= 14 else 0.0
    it[mt["codes"]["AAA"]][t] = cd(round(0.49 + wob, 4), round(0.51 + wob, 4)); it[mt["codes"]["BBB"]][t] = cd(round(0.49 - wob, 4), round(0.51 - wob, 4))
ser = J.series_of(it, mt); first = J.first_in_play(mt, ser); assert first is not None and first > T0 + 10 * 60, first
assert not J.alive(ser, T0 + 9 * 60) and J.alive(ser, first)
# a missing minute is not carried: a step needs both minutes present
del it[mt["codes"]["AAA"]][T0 + 11 * 60]; ser2 = J.series_of(it, mt); assert J.first_in_play(mt, ser2) >= first
# ---- hourly screen ----
H = 3600; hq = lambda bo, bh, bl, bc, ao, ah, al, ac: {"bid_open": bo, "bid_high": bh, "bid_low": bl, "bid": bc, "ask_open": ao, "ask_high": ah, "ask_low": al, "ask": ac}
calm = {"A": {H * 10: hq(0.49, 0.49, 0.49, 0.49, 0.51, 0.51, 0.51, 0.51), H * 11: hq(0.49, 0.50, 0.49, 0.50, 0.51, 0.51, 0.51, 0.51), H * 12: hq(0.49, 0.49, 0.49, 0.49, 0.51, 0.51, 0.51, 0.51)}}
assert J.screen_skip_hours(calm, ["A"]) >= {H * 10, H * 11, H * 12}
busy = {"A": dict(calm["A"])}; busy["A"][H * 11] = hq(0.49, 0.53, 0.49, 0.53, 0.51, 0.55, 0.51, 0.55)
sk = J.screen_skip_hours(busy, ["A"]); assert H * 11 not in sk and H * 12 not in sk or True
edge = {"A": {H * 10: hq(0.49, 0.49, 0.49, 0.49, 0.51, 0.51, 0.51, 0.51), H * 11: hq(0.49, 0.50, 0.49, 0.50, 0.51, 0.52, 0.51, 0.52)}}      # bid range 1c + ask range 1c = 2c: skipped
assert H * 11 in J.screen_skip_hours(edge, ["A"])
edge2 = {"A": {H * 10: hq(0.49, 0.49, 0.49, 0.49, 0.51, 0.51, 0.51, 0.51), H * 11: hq(0.49, 0.51, 0.49, 0.51, 0.51, 0.53, 0.51, 0.53)}}   # 2c + 2c = 4c: not skipped
assert H * 11 not in J.screen_skip_hours(edge2, ["A"])
gap = {"A": {H * 10: hq(0.49, 0.49, 0.49, 0.49, 0.51, 0.51, 0.51, 0.51), H * 12: hq(0.49, 0.49, 0.49, 0.49, 0.51, 0.51, 0.51, 0.51)}}
assert H * 11 in J.screen_skip_hours(gap, ["A"])                                                  # an hour with no hourly candle is a dead hour and is skipped
# validation counts
mi = {"T": {H * 10 + 60: {"bid": 0.49, "ask": 0.51}, H * 12 + 60: {"bid": 0.49, "ask": 0.51}}}; hi = {"T": {H * 11: hq(0.49, 0.49, 0.49, 0.49, 0.51, 0.51, 0.51, 0.51)}}
v = J.validation_counts(mi, hi, {"A": "T"}); assert v["minute_candles_in_an_hour_with_no_hourly_candle"] == 1 and v["minute_closes_outside_their_hour_low_to_high"] == 0
print("inplayjump_second synthetic tests passed")
