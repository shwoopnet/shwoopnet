"""python3 -I engine1_enum_test.py : the enumerator against ENGINE1_ENUMERATOR_HAND_CASE_NOV15.md."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_enum as N
C = 100000
rows = [(-660, .40, .42, 5, 100), (-600, .41, .43, 4, 102), (-540, .42, .44, 3, 104), (-480, .44, .46, 2, 105), (-420, .46, .48, 6, 108), (-360, .48, .50, 1, 110), (-300, .50, .52, 7, 114)]
cs = [(C + d, b, a, (a + b) / 2, v, o) for d, b, a, v, o in rows]
ent = lambda **k: N.entries(cs, C, 300, k.get("band", 10), k["side"], k.get("filt"), k.get("cuts"))
assert N.RULES_PER_SERIES == 123552 and len(N.FILTERS) == 22
r = ent(side="cheap", filt=("oi3", "up")); assert r[0] == {"side": "no", "ask": .50, "entry_end": C - 300, "whole_cent": True}, r      # 1
assert ent(side="cheap", filt=("oi3", "down"))[0] is None
assert ent(side="yes", filt=("mom1", "up"))[0] == {"side": "yes", "ask": .52, "entry_end": C - 300, "whole_cent": True}                  # 2
assert ent(side="no", filt=("mom1", "up"))[0] is None and ent(side="no", filt=("mom1", "down"))[0]["side"] == "no"
assert ent(side="favourite", filt=("vol3", "up"))[0]["side"] == "yes" and ent(side="favourite", filt=("oi6", "flat"))[0] is None   # 3
for s in N.SIDES: assert ent(side=s, band=9)[0] is None                                                              # 4
cuts = N.spread_cuts([1, 2, 2, 3, 4, 5]); assert cuts == (2, 3)                                                        # 5
assert N.spread_class(2, cuts) == "low" and N.spread_class(3, cuts) == "mid" and N.spread_class(4, cuts) == "high"
assert ent(side="cheap", filt=("spread", "low"), cuts=cuts)[0] and ent(side="cheap", filt=("spread", "high"), cuts=cuts)[0] is None
cs2 = [c for c in cs if c[0] != C - 600]                                                                               # 6: W2 lacks the C-600 candle
missing = [f for f in N.FILTERS if f and f[0] != "spread" and N.entries(cs2, C, 300, 10, "cheap", f)[1] == "missing feature candle"]
assert sorted(set(f[0] for f in missing)) == ["mom5", "vol3"] and len(missing) == 6, missing
assert N.entries(cs2, C, 300, 10, "cheap", ("oi6", "up"))[1] == "ok" and N.entries(cs2, C, 300, 10, "cheap", ("mom3", "down"))[1] in ("ok", "filter")
cs3 = cs + [(C - 240, .10, .12, .11, 9, 999)]                                                                          # 8: a later candle never changes bucket 300's features
for f in N.FILTERS: assert N.entries(cs3, C, 300, 10, "cheap", f, cuts)[0] == N.entries(cs, C, 300, 10, "cheap", f, cuts)[0]
assert N.entries(cs, C, 240, 10, "cheap", None)[1] == "no entry candle" and N.entries(cs3, C, 240, 2, "cheap", None)[1] == "ok"
# Auditor B: the entry is scored at the RAW ask, the band uses whole cents rounded UP
def at(bid, ask): return [c for c in cs[:-1]] + [(C - 300, bid, ask, .5, 7, 114)]
r1 = N.entries(at(.50, .5249), C, 300, 10, "yes", None); assert r1[0]["ask"] == .5249 and r1[0]["whole_cent"] is False, r1      # 52.49c is band 10 (53c rounded up)
assert N.cents(.5249) == 53 and N.cents(.52) == 52 and N.cents(.5251) == 53 and N.cents(.5) == 50 and N.cents(.51) == 51
assert N.entries(at(.50, .5249), C, 300, 10, "yes", None)[0]["ask"] == .5249 and N.entries(at(.50, .5251), C, 300, 10, "yes", None)[0]["ask"] == .5251
assert abs(N.entries(at(.4749, .52), C, 300, 10, "no", None)[0]["ask"] - (1 - .4749)) < 1e-12                            # NO raw ask = 1 - yes_bid
# NULL in a feature field is a missing feature, not a crash
csn = [c if c[0] != C - 480 else (c[0], c[1], c[2], c[3], c[4], None) for c in cs]
assert N.entries(csn, C, 300, 10, "cheap", ("oi3", "up"))[1] == "missing feature candle" and N.entries(csn, C, 300, 10, "cheap", ("oi6", "up"))[1] == "ok"
csv = [c if c[0] != C - 540 else (c[0], c[1], c[2], c[3], None, c[5]) for c in cs]
assert N.entries(csv, C, 300, 10, "cheap", ("vol3", "up"))[1] == "missing feature candle"
print("ALL OK")
