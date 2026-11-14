"""Test for spxscalp_second.py: INVENTED rows only (SPXSCALP_SECOND_HAND_CASE.md). Run: python3 -B -W ignore test_spxscalp_second.py"""
import calendar, math, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spxscalp_second as q

D = lambda day, h=18, mi=0, mo=11: calendar.timegm((2026, mo, day, h, mi, 0))
def window(tk, close, es_list, cmap, result="yes", omit=()):
    """es_list: ES closes for m = 0..15 (None = no bar); cmap: {m: (bid, ask)}; unlisted minutes 1..15 carry (.15, .17); omit = minutes with no candle."""
    O = close - 900
    es = {O + 60 * m: (1, v) for m, v in enumerate(es_list) if v is not None}
    cands = [{"ts": O + 60 * m, "bid": cmap.get(m, (0.15, 0.17))[0], "ask": cmap.get(m, (0.15, 0.17))[1]} for m in range(1, 16) if m not in omit]
    return {"ticker": tk, "series": "KXINX15M", "close": close, "result": result}, cands, es
def assemble(*ws):
    mk, cs, es = {}, {}, {}
    for m, c, x in ws: mk[m["ticker"]] = m; cs[m["ticker"]] = c; es.update(x)
    return mk, cs, es
near = lambda a, b: abs(a - b) < 1e-9
# --- the hand case ---
X1 = window("KXINX15M-X1", D(5), [1000, 1000.2] + [1001.0] * 14, {1: (.20, .22), 2: (.20, .22), 3: (.30, .32), 4: (.35, .37), 5: (.40, .42), 6: (.47, .49), 7: (.50, .52), 8: (.60, .62), 9: (.82, .84), 10: (.70, .72)}, "yes")
X2 = window("KXINX15M-X2", D(6), [1000, 1000.7, 1000.8, 1000.9] + [1000.9] * 12, {1: (.26, .28), 2: (.25, .27), 3: (.22, .24), 4: (.22, .24), 5: (.22, .24), 6: (.22, .24), 7: (.22, .24), 8: (.22, .24), 9: (.22, .24), 10: (.15, .17)}, "no")
X3 = window("KXINX15M-X3", D(8), [1000, 999.4, 999.3] + [999.3] * 13, {m: (.60, .62) for m in range(1, 6)}, "yes")
X4 = window("KXINX15M-X4", D(8, 19), [1000] + [1000.4] * 15, {m: (.20, .22) for m in range(1, 6)}, "yes")
X5 = window("KXINX15M-X5", D(9), [1000, 1000.7] + [1000.7] * 14, {1: (.20, .22), **{m: (.38, .40) for m in range(2, 10)}}, "yes", omit=(10, 11, 12, 13, 14, 15))
X6 = window("KXINX15M-X6", D(11), [None, 1000.7] + [1000.7] * 14, {1: (.20, .22)}, "yes")
X7 = window("KXINX15M-X7", D(10), [1000, 1000.6] + [1000.6] * 14, {1: (.19, .21), **{m: (.38, .40) for m in range(2, 10)}, 10: (.30, .32)}, "void")
X8 = window("KXINX15M-X8", calendar.timegm((2026, 12, 1, 0, 0, 0)), [1000, 1002] + [1002] * 14, {1: (.20, .22)}, "yes")
class Poison(dict):
    def get(self, key, default=None):
        if key == "KXINX15M-X8": raise AssertionError("touched a window on or after 2026-12-01")
        return super().get(key, default)
mk, cs, es = assemble(X1, X2, X3, X4, X5, X6, X7, X8)
rep = q.run_windows(mk, Poison(cs), es)
A = rep["arms"]
c = rep["counts"]
assert c["windows_listed"] == 8 and c["not_touched_on_or_after_2026-12-01"] == 1 and c["outside_2026-11-05_to_2026-11-13_not_touched"] == 0 and c["no_es_start_bar"] == 1, c
assert list(A) == ["B25 HEADLINE", "B25 HALF2X", "B25 HOLD", "B30 HEADLINE", "B30 HALF2X", "B30 HOLD"]
assert rep["lines"][0] == "B25 HEADLINE | 1c n=4 PF=6.9286 net=0.83 h1=1.3571 h2=inf | 2c n=4 PF=5.9375 net=0.79 | FALSIFIED (fewer than 100 entries, n = 4) (upper bound, not fill-checked)", rep["lines"][0]
assert [l.split(" |")[0] for l in rep["lines"]] == list(A)
h = A["B25 HEADLINE"]
assert h["entries_found"] == 4 and h["windows_without_entry"] == 2, h
assert h["settled_at_close_count"] == 1 and h["settled_at_close_share"] == 0.25 and near(h["settled_at_close_entry_fill_sum_1c"], 0.23) and h["time_exit_moved_count"] == 0 and A["B25 HOLD"].get("settled_at_close_count") is None and "settlement" in h["settled_at_close_note"]
assert h["1c"]["n"] == 4 and near(h["1c"]["net"], 0.19 - 0.14 + 0.75 + 0.03) and near(h["1c"]["pf"], 0.97 / 0.14) and near(h["1c"]["pf"], 6.9285714286)
assert h["1c"]["n_half1"] == 2 and h["1c"]["n_half2"] == 2 and near(h["1c"]["half1_pf"], 0.19 / 0.14) and h["1c"]["half2_pf"] == float("inf")
assert near(h["2c"]["pf"], 0.95 / 0.16) and near(h["2c"]["net"], 0.20 - 0.16 + 0.74 + 0.01) and near(h["2c"]["pf"], 5.9375) and h["counts_the_bar"] is False and h["label"].startswith("FALSIFIED (fewer than 100 entries, n = 4)") and h["label"].endswith("(upper bound, not fill-checked)")
d = A["B25 HOLD"]
assert d["1c"]["n"] == 4 and near(d["1c"]["net"], 0.75 - 0.27 + 0.75 - 0.02) and near(d["1c"]["pf"], 1.5 / 0.29) and near(d["1c"]["half1_pf"], 0.75 / 0.27) and near(d["1c"]["half2_pf"], 0.75 / 0.02) and d["voids"] == 1
assert near(d["2c"]["pf"], 1.48 / 0.30)
v = A["B25 HALF2X"]
assert v["1c"]["n"] == 4 and near(v["1c"]["pf"], 2.32 / 0.27) and near(v["1c"]["net"], 0.74 - 0.27 + 1.51 + 0.07) and near(v["1c"]["half1_pf"], 0.74 / 0.27) and v["1c"]["half2_pf"] == float("inf") and v["settled_at_close_count"] == 1
h30 = A["B30 HEADLINE"]
assert h30["1c"]["n"] == 4 and near(h30["1c"]["net"], 0.19 - 0.18 + 0.75 + 0.03) and near(h30["1c"]["pf"], 0.97 / 0.18) and near(h30["1c"]["pf"], 5.3888888889)
# C1: the share of look candles with both sides and the spread distribution (nothing missing here; spreads are 2c except the 2c-candles .22/.24 and .38/.40 and .60/.62)
c1 = rep["C1_candles_two_sided_and_spread"]; assert c1["look_candles"] == 30 and c1["two_sided"] == 30 and c1["two_sided_share"] == 1.0 and c1["spread_cents_median"] == 2.0 and c1["spread_cents_p90"] == 2.0
# --- the individual numbers of the hand case through the pure functions ---
def pathfor(cmap, t0=0):
    return [(60 * m, cmap[m]) for m in sorted(cmap)]
X1p = {3: .30, 4: .35, 5: .40, 6: .47, 7: .50, 8: .60, 9: .82, 10: .70}
TE = ("bid", 0.70, False)
assert near(q.headline(0.23, 0.01, pathfor(X1p), TE, "yes", "yes"), 0.19) and near(q.headline(0.24, 0.02, pathfor(X1p), TE, "yes", "yes"), 0.20)
assert near(q.variant(0.23, 0.01, pathfor(X1p), TE, "yes", "yes"), 0.74) and near(q.variant(0.24, 0.02, pathfor(X1p), TE, "yes", "yes"), 0.73)
assert near(q.hold(0.23, "yes", "yes"), 0.75) and near(q.hold(0.24, "yes", "yes"), 0.74) and near(q.hold(0.25, "yes", "no"), -0.27) and near(q.hold(0.22, "yes", "void"), -0.02) and near(q.hold(0.22, "no", "no"), 0.76)
assert near(q.fee(0.23), 0.02) and near(q.fee(0.23, 2), 0.03) and near(q.fee(0.25, 2), 0.03) and near(q.fee(0.46), 0.02) and near(q.fee(0.14), 0.01) and near(q.fee(0.81), 0.02)
# --- looks, thresholds, bands, sides ---
def one(es_list, cmap, close=D(5)):
    mkx, csx, esx = assemble(window("KXINX15M-T", close, es_list, cmap))
    cnt = {"look_no_es_bar": 0, "look_es_roll": 0, "look_no_price": 0, "look_not_two_sided": 0}
    return q.find_entries(close, esx, csx["KXINX15M-T"], cnt), cnt
flat = [1000.0] * 16
for m_ok, expect in ((5, 5), (6, None)):          # only m = 5 qualifies (inclusive: end at close - 600 s); m = 6 is past the looks
    es_l = [1000.0] * m_ok + [1001.0] * (16 - m_ok)
    f, _ = one(es_l, {m_ok: (.20, .22)})
    assert (f[0.25][0] == expect) if expect else (f == {}), (m_ok, f)
f, _ = one([1000.0, 1000.5] + [1000.5] * 14, {1: (.20, .22)}); assert f[0.25][:2] == (1, "yes")          # a move of exactly 0.0005 x 1000 = 0.5 qualifies (1e-9)
f, _ = one([40040.0, 40060.02] + [40060.02] * 14, {1: (.20, .22)}); assert f[0.25][0] == 1          # float noise: |move| = 20.0199999999968 against 0.0005 x 40040 = 20.02 still qualifies (1e-9)
f, _ = one([1000.0, 1000.4999] + [1000.4999] * 14, {1: (.20, .22)}); assert f == {}
f, _ = one([1000.0, 999.5] + [999.5] * 14, {1: (.77, .79)}); assert f[0.25][1] == "no" and near(f[0.25][2], 0.23)          # down = NO, NO ask = 1 - yes bid = .23
for ask, b25, b30 in ((0.20, True, True), (0.19, False, False), (0.25, True, True), (0.251, False, True), (0.30, False, True), (0.31, False, False)):
    f, _ = one([1000.0, 1001.0] + [1001.0] * 14, {1: (ask - 0.02, ask)})
    assert (0.25 in f) is b25 and (0.30 in f) is b30, (ask, f)
f, _ = one([1000.0, 1001.0, 999.0] + [999.0] * 13, {1: (.50, .60), 2: (.77, .79)})          # m = 1 up but the ask .60 is out; m = 2 down, NO ask .23 in: the direction is re-evaluated
assert f[0.25][:2] == (2, "no")
f, cnt = one([1000.0, None, 1001.0] + [1001.0] * 13, {2: (.20, .22)}); assert f[0.25][0] == 2 and cnt["look_no_es_bar"] == 1
f, cnt = one([1000.0, 1001.0] + [1001.0] * 14, {1: (None, .22)}); assert f == {} and cnt["look_no_price"] == 1
mkr, csr, esr = assemble(window("KXINX15M-T", D(5), [1000.0, 1001.0] + [1001.0] * 14, {1: (.20, .22)})); esr[D(5) - 900 + 60] = (2, 1001.0)
cnt = {"look_no_es_bar": 0, "look_es_roll": 0, "look_no_price": 0, "look_not_two_sided": 0}; assert q.find_entries(D(5), esr, csr["KXINX15M-T"], cnt) == {} and cnt["look_es_roll"] == 1
# the first look wins even if a later look is also in band; one entry per band
f, _ = one([1000.0, 1001.0, 1001.0] + [1001.0] * 13, {1: (.20, .22), 2: (.22, .24)}); assert f[0.25][0] == 1
# --- exits: target range, tolerance, time exit, drops ---
Cl = D(5); O = Cl - 900
cands = lambda m2b: [{"ts": O + 60 * m, "bid": b, "ask": b + 0.02} for m, b in sorted(m2b.items())]
p = q.after_entry(cands({m: .15 for m in range(1, 16)}), O + 120, Cl); assert [t for t, _ in p] == [O + 60 * m for m in range(3, 11)]          # after the entry candle, through the minute ending close - 300 s (m = 10)
fill = 0.23
TB = lambda b: ("bid", b, False); ST = ("settle", None, True)
hit10 = [(O + 60 * m, .15) for m in range(3, 10)] + [(O + 600, 0.46)]; assert near(q.headline(fill, 0.01, hit10, TB(0.46), "yes", "yes"), 0.45 - 0.23 - q.fee(fill) - q.fee(0.45))          # the m = 10 candle can be the target (inclusive)
nohit = [(O + 60 * m, .15) for m in range(3, 11)]; assert near(q.headline(fill, 0.01, nohit, TB(0.15), "yes", "yes"), (0.14 - 0.23) - q.fee(fill) - q.fee(0.14))
# settlement: yes wins, no loses, void refunds; no exit fee; entry fee kept
assert near(q.headline(fill, 0.01, nohit, ST, "yes", "yes"), 1 - 0.23 - q.fee(fill)) and near(q.headline(fill, 0.01, nohit, ST, "yes", "no"), -0.23 - q.fee(fill)) and near(q.headline(fill, 0.01, nohit, ST, "yes", "void"), -q.fee(fill)) and near(q.headline(fill, 0.01, nohit, ST, "no", "no"), 1 - 0.23 - q.fee(fill))
assert near(q.variant(fill, 0.01, nohit, ST, "yes", "yes"), 2 * (1 - 0.23) - q.fee(fill, 2)) and near(q.variant(fill, 0.01, nohit, ST, "yes", "no"), -2 * 0.23 - q.fee(fill, 2)) and near(q.variant(fill, 0.01, nohit, ST, "yes", "void"), -q.fee(fill, 2))
assert near(q.headline(fill, 0.01, [(O + 180, 0.46)], ST, "yes", "no"), 0.45 - 0.23 - q.fee(fill) - q.fee(0.45))          # a target hit needs no time exit
assert near(q.headline(0.25, 0.01, [(O + 180, 0.50)], ST, "yes", "no"), 0.49 - 0.25 - q.fee(0.25) - q.fee(0.49))          # exactly 2 x fill hits
assert near(q.headline(0.25, 0.01, [(O + 180, 0.4999)], ST, "yes", "no"), -0.25 - q.fee(0.25))          # just under 2 x: no hit, settles
assert q.headline(fill, 0.02, nohit, TB(0.005), "yes", "yes") is not None          # an exit price below 0: the fee is clamped, no error
# variant: only 2x hit (no 80c): half at 2x, the rest at the time exit; neither: both at the time exit
only2x = [(O + 240, 0.50)] + [(O + 60 * m, .15) for m in range(6, 11)]
assert near(q.variant(fill, 0.01, only2x, TB(0.15), "yes", "yes"), (0.49 - fill) + (0.14 - fill) - q.fee(fill, 2) - q.fee(0.49) - q.fee(0.14))
assert near(q.variant(fill, 0.01, nohit, TB(0.15), "yes", "yes"), 2 * (0.14 - fill) - q.fee(fill, 2) - 2 * q.fee(0.14))
assert near(q.variant(fill, 0.01, only2x, ST, "yes", "yes"), (0.49 - fill) - q.fee(0.49) + (1 - fill) - q.fee(fill, 2))          # half A sold at 2x, half B settles
exact80 = [(O + 240, 0.46), (O + 300, 0.80)]; assert near(q.variant(fill, 0.01, exact80, TB(0.15), "yes", "yes"), (0.45 - fill) + (0.79 - fill) - q.fee(fill, 2) - q.fee(0.45) - q.fee(0.79))          # 0.80 exactly counts
# time_exit: the candle ending close - 300 s if two-sided, else the next two-sided one through the close, else settle
cd = lambda t, b, a: {"ts": t, "bid": b, "ask": a}
assert q.time_exit([cd(Cl - 300, .30, .32)], Cl) == ("bid", .30, False)
assert q.time_exit([cd(Cl - 300, 0.0, .02), cd(Cl - 240, .15, .17)], Cl) == ("bid", .15, True)
assert q.time_exit([cd(Cl - 300, .30, 1.0), cd(Cl - 180, .30, .30), cd(Cl - 120, .35, .33), cd(Cl, .12, .14)], Cl) == ("bid", .12, True)          # empty ask, locked, crossed move on; the candle ending at the close counts
assert q.time_exit([cd(Cl - 360, .30, .32), cd(Cl - 240, 0.0, .02)], Cl) == ("settle", None, True) and q.time_exit([], Cl) == ("settle", None, True)          # a candle before close - 300 s is not an exit minute
assert q.time_exit([cd(Cl + 60, .30, .32)], Cl) == ("settle", None, True)
assert q.settles(nohit, fill, ST, "headline") and not q.settles(hit10, fill, ST, "headline") and not q.settles(nohit, fill, TB(.15), "headline") and q.settles(only2x, fill, ST, "variant") and q.settles(exact80, fill, ST, "variant") is False
# --- arm verdict rules ---
def rows(nets): return [((i, "t"), n) for i, n in enumerate(nets)]
mix = ([0.3, -0.1, -0.1] * 34)[:100]          # 34 wins and 66 losses interleaved
good = q.arm_report({0.01: rows(mix), 0.02: rows(mix)})
assert good["1c"]["n"] == 100 and good["counts_the_bar"] is True and good["label"].startswith("counts the bar")          # PF 10.2 / 6.6 = 1.545, both halves above 1.3
bad_half = q.arm_report({0.01: rows([0.3] * 50 + [-0.1] * 50), 0.02: rows([0.3] * 100)})
assert bad_half["label"].startswith("FALSIFIED (a half PF under 1.0") and bad_half["counts_the_bar"] is False
two_c = q.arm_report({0.01: rows([0.3, -0.1] * 50), 0.02: rows([-0.3, 0.1] * 50)}); assert two_c["label"].startswith("FALSIFIED (a half PF under 1.0 at 1c, or 2c PF under 1.0)")
noev = q.arm_report({0.01: rows([0.12, -0.1] * 50), 0.02: rows([0.12, -0.1] * 50)}); assert noev["label"].startswith("no evidence") and near(noev["1c"]["pf"], 1.2) and noev["counts_the_bar"] is False          # PF 1.2: both halves above 1.0 but under the 1.3 bar
exact13 = q.arm_report({0.01: rows([0.13, -0.1] * 50), 0.02: rows([0.13, -0.1] * 50)}); assert exact13["counts_the_bar"] is True          # PF 1.3 counts (inside 1e-9)
odd = q.arm_report({0.01: rows([0.3, -0.1, 0.2, 0.1, -0.05]), 0.02: rows([0.3, -0.1, 0.2, 0.1, -0.05])}); assert odd["1c"]["n_half1"] == 2 and odd["1c"]["n_half2"] == 3 and near(odd["1c"]["half1_pf"], 0.3 / 0.1) and near(odd["1c"]["half2_pf"], 0.3 / 0.05)          # floor(5 / 2) = 2 first
empty = q.arm_report({0.01: [], 0.02: []}); assert empty["label"].startswith("FALSIFIED (fewer than 100") and empty["1c"]["pf"] is None
# --- ADDENDUM 3: the window range of Amendment 4, [2026-11-05, 2026-11-13); outside windows are not touched ---
T = lambda *a: calendar.timegm(a)
class PoisonSet(dict):
    def __init__(self, d, bad): super().__init__(d); self.bad = bad
    def get(self, key, default=None):
        if key in self.bad: raise AssertionError("touched an outside window " + key)
        return super().get(key, default)
bw = [window("KXINX15M-B1", T(2026, 11, 5, 0, 0, 0), [1000, 1001] + [1001.0] * 14, {1: (.20, .22)}),
      window("KXINX15M-B2", T(2026, 11, 4, 23, 59, 59), [1000, 1001] + [1001.0] * 14, {1: (.20, .22)}),
      window("KXINX15M-B3", T(2026, 11, 12, 23, 59, 59), [1000, 1001] + [1001.0] * 14, {1: (.20, .22)}),
      window("KXINX15M-B4", T(2026, 11, 13, 0, 0, 0), [1000, 1001] + [1001.0] * 14, {1: (.20, .22)}),
      window("KXINX15M-B5", T(2026, 11, 20, 12, 0, 0), [1000, 1001] + [1001.0] * 14, {1: (.20, .22)}),
      window("KXINX15M-B6", T(2026, 12, 1, 0, 0, 0), [1000, 1001] + [1001.0] * 14, {1: (.20, .22)})]
mkb, csb, esb = assemble(*bw)
rb = q.run_windows(mkb, PoisonSet(csb, {"KXINX15M-B2", "KXINX15M-B4", "KXINX15M-B5", "KXINX15M-B6"}), esb)
assert rb["counts"]["windows_listed"] == 6 and rb["counts"]["outside_2026-11-05_to_2026-11-13_not_touched"] == 3 and rb["counts"]["not_touched_on_or_after_2026-12-01"] == 1, rb["counts"]
assert rb["arms"]["B25 HOLD"]["entries_found"] == 2 and rb["arms"]["B25 HOLD"]["1c"]["n"] == 2
mkn = {"KXINX15M-N": {"ticker": "KXINX15M-N", "series": "KXINX15M", "close": None, "result": "yes"}}
assert q.run_windows(mkn, {}, {})["counts"]["outside_2026-11-05_to_2026-11-13_not_touched"] == 1          # no close: listed and not touched
# an n/a or infinite PF prints as text in the lines
assert q.line_of("K", {"1c": {"n": 0, "pf": None, "net": 0.0, "half1_pf": None, "half2_pf": None}, "2c": {"n": 0, "pf": float("inf"), "net": 0.0}, "label": "L"}) == "K | 1c n=0 PF=n/a net=0.00 h1=n/a h2=n/a | 2c n=0 PF=inf net=0.00 | L"
# --- ADDENDUM: F1 rule 18 at entry ---
f, cnt = one([1000.0, 1001.0] + [1001.0] * 14, {1: (0.0, .22), 2: (.20, .22)}); assert f[0.25][:3] == (2, "yes", 0.22) and cnt["look_not_two_sided"] == 1          # Z1
for cm in ({1: (0.0, .30)}, {1: (.78, 1.0)}, {1: (.22, .22)}, {1: (.23, .21)}):
    f, cnt = one([1000.0, 999.0] + [999.0] * 14, cm); assert f == {} and cnt["look_not_two_sided"] == 1, (cm, f, cnt)          # Z1b down moves: no NO entry at 1 - .78 = .22
f, cnt = one([1000.0, 1001.0] + [1001.0] * 14, {1: (.23, .21)}); assert f == {} and cnt["look_not_two_sided"] == 1
f, cnt = one([1000.0, 1001.0] + [1001.0] * 14, {1: (.22, .22)}); assert f == {} and cnt["look_not_two_sided"] == 1
f, cnt = one([1000.0, 1001.0] + [1001.0] * 14, {1: (.01, .22)}); assert f[0.25][2] == 0.22 and cnt["look_not_two_sided"] == 0          # wide but two-sided
f, cnt = one([1000.0, 1001.0] + [1001.0] * 14, {1: (.22 - 4e-10, .22)}); assert cnt["look_not_two_sided"] == 1          # a 0.5e-9 spread is locked
# a candle that is not two-sided is no price even where the ES move does not qualify: not counted
f, cnt = one([1000.0, 1000.1] + [1000.1] * 14, {1: (0.0, .22)}); assert f == {} and cnt["look_not_two_sided"] == 0
# --- F2 / Amendment 3: a no-bid or one-sided candle is no exit price; the exit minute moves, else the position settles ---
pp = q.after_entry([cd(O + 180, .50, 1.0), cd(O + 240, 0.0, .02), cd(O + 300, .50, .52)], O + 120, Cl); assert pp == [(O + 300, .50)]
def zrun(cmap_extra, result="yes", late=True):
    cm = {1: (.20, .22), **{m: (.30, .32) for m in range(2, 10)}, 10: (0.0, .02), **cmap_extra}
    om = () if late else (11, 12, 13, 14, 15)
    cm.update({m: (0.0, .02) for m in om})
    return q.run_windows(*assemble(window("KXINX15M-Z", D(5), [1000, 1001] + [1001.0] * 14, cm, result)))["arms"]
Za = zrun({})          # Z2a: m = 10 has no bid: moves to m = 11 (bid .15)
assert near(Za["B25 HEADLINE"]["1c"]["net"], -0.12) and near(Za["B25 HALF2X"]["1c"]["net"], -0.23) and near(Za["B25 HOLD"]["1c"]["net"], 0.75)
assert Za["B25 HEADLINE"]["settled_at_close_count"] == 0 and Za["B25 HEADLINE"]["time_exit_moved_count"] == 1 and Za["B25 HALF2X"]["time_exit_moved_count"] == 1 and Za["B25 HEADLINE"]["1c"]["n"] == 1
Zb = zrun({4: (.50, .52)})          # Z2b: a target hit at m = 4; the variant's second half goes at the moved time exit
assert near(Zb["B25 HEADLINE"]["1c"]["net"], 0.22) and near(Zb["B25 HALF2X"]["1c"]["net"], 0.11) and Zb["B25 HEADLINE"]["time_exit_moved_count"] == 0 and Zb["B25 HALF2X"]["time_exit_moved_count"] == 1
Zc = zrun({4: (.50, 1.0)}); assert near(Zc["B25 HEADLINE"]["1c"]["net"], -0.12)          # a hit candle with an empty ask is not a hit
for res, hn, vn in (("yes", 0.75, 1.51), ("no", -0.25, -0.49), ("void", -0.02, -0.03)):          # Z2d: nothing two-sided from m = 10 to the close: held to the close
    Zd = zrun({}, res, late=False)
    assert near(Zd["B25 HEADLINE"]["1c"]["net"], hn) and near(Zd["B25 HALF2X"]["1c"]["net"], vn), (res, Zd["B25 HEADLINE"]["1c"]["net"], Zd["B25 HALF2X"]["1c"]["net"])
    assert Zd["B25 HEADLINE"]["settled_at_close_count"] == 1 and Zd["B25 HEADLINE"]["time_exit_moved_count"] == 0 and Zd["B25 HALF2X"]["settled_at_close_count"] == 1
# --- C1 on two-sided candles only (Z3) ---
Z3 = {1: (0.0, .22), 2: (.20, .22), 3: (.30, 1.0)}
rz = q.run_windows(*assemble(window("KXINX15M-Q", D(5), [1000, 1001] + [1001.0] * 14, Z3, omit=(4, 5))))["C1_candles_two_sided_and_spread"]
assert rz["look_candles"] == 3 and rz["two_sided"] == 1 and abs(rz["two_sided_share"] - 1 / 3) < 1e-12 and rz["spread_cents_median"] == 2.0, rz
# --- F3: counted ES rows ---
HDR = "ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume\n"
good = lambda i: "2026-11-05T%02d:%02d:00.000000000Z,33,1,7,1,1,1,1000.5,10\n" % (14 + i // 60, i % 60)
bad = ["1762354800000000000,33,1,7,1,1,1,1000.5,10\n", "2026-11-06T14:00:00.000000000Z,33,1,abc,1,1,1,1000.5,10\n", "2026-11-06T14:01:00.000000000Z,33,1,7,1,1,1,,10\n"]
with tempfile.TemporaryDirectory() as tmpd:
    def es_file(rows):
        f = os.path.join(tmpd, "x.csv"); open(f, "w").write(HDR + "".join(rows)); return f
    out, st = q.load_es_counted(es_file([good(0), good(1)] + bad)); assert st == {"rows_read": 5, "rows_kept": 2, "skipped_ts": 1, "skipped_value": 2, "skipped_instrument": 0} and len(out) == 2
    try: q.check_es_rows(st); assert 0
    except SystemExit as ex: assert "rows_read 5" in str(ex) and "skipped_ts 1" in str(ex) and "skipped_value 2" in str(ex)
    inst = lambda i, iid: good(i).replace(",33,1,7,", ",33,1,%d," % iid)
    out, sti = q.load_es_counted(es_file([inst(0, 7), inst(1, 7), inst(2, 7), inst(3, 7), inst(4, 8)]))
    assert sti == {"rows_read": 5, "rows_kept": 4, "skipped_ts": 0, "skipped_value": 0, "skipped_instrument": 1} and len(out) == 4 and all(v[0] == 7 for v in out.values())
    try: q.check_es_rows(sti); assert 0          # 1 of 5 = 20%
    except SystemExit as ex: assert "skipped_instrument 1" in str(ex)
    try: q.load_es_counted(es_file([inst(0, 7), inst(1, 8)])); assert 0
    except SystemExit as ex: assert "tie" in str(ex) and "7" in str(ex) and "8" in str(ex)
    ok = [good(i) for i in range(100)]
    assert q.check_es_rows(q.load_es_counted(es_file(ok + bad[:1]))[1]) is None
    assert q.check_es_rows(q.load_es_counted(es_file([good(i) for i in range(95)] + [bad[0]] * 5))[1]) is None          # exactly 5%
    for rows in (ok + [bad[0]] * 6, [], bad):
        try: q.check_es_rows(q.load_es_counted(es_file(rows))[1]); assert 0
        except SystemExit: pass
    mkw, csw, esw = assemble(window("KXINX15M-F", D(5), [1000, 1001] + [1001.0] * 14, {1: (.20, .22)}))
    saved = (q.k.guard, q.k.markets, q.k.candles, q.check_candle_overlap); q.k.guard = lambda f: None; q.k.markets = lambda l: mkw; q.k.candles = lambda c: csw; q.check_candle_overlap = lambda r: None
    try:
        ro = q.run(["l"], ["c"], es_file([good(i) for i in range(10)])); assert ro["es_rows"]["rows_read"] == 10 and ro["es_rows"]["rows_kept"] == 10
        try: q.run(["l"], ["c"], es_file(bad)); assert 0
        except SystemExit as ex: assert "skipped" in str(ex)
    finally:
        q.k.guard, q.k.markets, q.k.candles, q.check_candle_overlap = saved
assert q.MAX_SKIP_SHARE == 0.05
# --- ADDENDUM 4 (Amendment 5): a market_ticker in more than one candle file (or answer) STOPS the run, before the ES file is opened ---
import gzip, json
def mkrun_c(d, bodies):
    os.makedirs(d); rows = []
    for i, (rid, body) in enumerate(bodies):
        f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(body)); rows.append({"id": rid, "page": 1, "status": 200, "file": f})
    json.dump({"job": {}, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))
cn = lambda tk: {"markets": [{"market_ticker": tk, "candlesticks": [{"end_period_ts": D(5) - 840, "yes_bid": {"close_dollars": "0.40"}, "yes_ask": {"close_dollars": "0.42"}}]}]}
with tempfile.TemporaryDirectory() as td:
    a1, a2, a3, a4 = (os.path.join(td, n) for n in ("a1", "a2", "a3", "a4"))
    mkrun_c(a1, [("c1", cn("KXINX15M-A")), ("c2", cn("KXINX15M-B"))]); mkrun_c(a2, [("c3", cn("KXINX15M-C"))]); mkrun_c(a3, [("c4", cn("KXINX15M-B"))])
    mkrun_c(a4, [("c5", {"markets": [cn("KXINX15M-D")["markets"][0], cn("KXINX15M-D")["markets"][0]]})])
    assert q.check_candle_overlap([a1, a2]) is None
    b1, b2, b3, b4 = (os.path.join(td, n) for n in ("b1", "b2", "b3", "b4"))
    cnode = lambda extra: dict(extra, candlesticks=cn("X")["markets"][0]["candlesticks"])
    mkrun_c(b1, [("REQ-1", cnode({}))]); mkrun_c(b2, [("REQ-1", cnode({}))]); mkrun_c(b3, [("r7", cnode({"ticker": "KXINX15M-T"}))]); mkrun_c(b4, [("r8", cnode({"ticker": "KXINX15M-T"}))])
    for runs, name in (([b1, b2], "REQ-1"), ([b3, b4], "KXINX15M-T")):          # a single-market answer: ticker, else the request id
        try: q.check_candle_overlap(runs); assert 0
        except SystemExit as ex: assert name in str(ex), str(ex)
    for runs, name in (([a1, a3], "KXINX15M-B"), ([a4], "KXINX15M-D")):
        try: q.check_candle_overlap(runs); assert 0
        except SystemExit as ex: assert name in str(ex) and "STOP" in str(ex), str(ex)
    saved = (q.k.guard, q.k.markets, q.k.candles, q.load_es_counted); q.k.guard = lambda f: None; q.k.markets = lambda l: {}; q.k.candles = lambda c: {}
    opened = []; q.load_es_counted = lambda path: opened.append(path) or ({}, {"rows_read": 1, "rows_kept": 1, "skipped_ts": 0, "skipped_value": 0, "skipped_instrument": 0})
    try:
        try: q.run(["l"], [a1, a3], "es.csv"); assert 0
        except SystemExit: pass
        assert opened == []
        q.run(["l"], [a1, a2], "es.csv"); assert opened == ["es.csv"]
    finally:
        q.k.guard, q.k.markets, q.k.candles, q.load_es_counted = saved
print("test_spxscalp_second: all checks passed")
