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
X5 = window("KXINX15M-X5", D(9), [1000, 1000.7] + [1000.7] * 14, {1: (.20, .22), **{m: (.38, .40) for m in range(2, 10)}}, "yes", omit=(10,))
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
assert c["windows_listed"] == 8 and c["not_touched_on_or_after_2026-12-01"] == 1 and c["no_es_start_bar"] == 1, c
h = A["band_25_headline"]
assert h["entries_found"] == 4 and h["windows_without_entry"] == 2 and h["dropped_no_time_exit_candle"] == 1, h
assert h["1c"]["n"] == 3 and near(h["1c"]["net"], 0.19 - 0.14 + 0.03) and near(h["1c"]["pf"], 0.22 / 0.14) and near(h["1c"]["pf"], 1.5714285714)
assert h["1c"]["n_half1"] == 1 and h["1c"]["n_half2"] == 2 and h["1c"]["half1_pf"] == float("inf") and near(h["1c"]["half2_pf"], 0.03 / 0.14)
assert near(h["2c"]["pf"], 0.21 / 0.16) and near(h["2c"]["net"], 0.20 - 0.16 + 0.01) and h["counts_the_bar"] is False and h["label"].startswith("FALSIFIED (fewer than 100 entries, n = 3)") and h["label"].endswith("(upper bound, not fill-checked)")
d = A["band_25_hold"]
assert d["1c"]["n"] == 4 and near(d["1c"]["net"], 0.75 - 0.27 + 0.75 - 0.02) and near(d["1c"]["pf"], 1.5 / 0.29) and near(d["1c"]["half1_pf"], 0.75 / 0.27) and near(d["1c"]["half2_pf"], 0.75 / 0.02) and d["voids"] == 1
assert near(d["2c"]["pf"], 1.48 / 0.30) and d["dropped_no_time_exit_candle"] == 0
v = A["band_25_variant"]
assert v["1c"]["n"] == 3 and near(v["1c"]["pf"], 0.81 / 0.27) and near(v["1c"]["net"], 0.74 - 0.27 + 0.07) and v["1c"]["half1_pf"] == float("inf") and near(v["1c"]["half2_pf"], 0.07 / 0.27) and v["dropped_no_time_exit_candle"] == 1
h30 = A["band_30_headline"]
assert h30["1c"]["n"] == 3 and near(h30["1c"]["net"], 0.19 - 0.18 + 0.03) and near(h30["1c"]["pf"], 0.22 / 0.18) and near(h30["1c"]["pf"], 1.2222222222)
# C1: the share of look candles with both sides and the spread distribution (nothing missing here; spreads are 2c except the 2c-candles .22/.24 and .38/.40 and .60/.62)
c1 = rep["C1_candles_two_sided_and_spread"]; assert c1["look_candles"] == 30 and c1["two_sided"] == 30 and c1["two_sided_share"] == 1.0 and c1["spread_cents_median"] == 2.0 and c1["spread_cents_p90"] == 2.0
# --- the individual numbers of the hand case through the pure functions ---
def pathfor(cmap, t0=0):
    return [(60 * m, cmap[m]) for m in sorted(cmap)]
X1p = {3: .30, 4: .35, 5: .40, 6: .47, 7: .50, 8: .60, 9: .82, 10: .70}
assert near(q.headline(0.23, 0.01, pathfor(X1p), 0.70), 0.19) and near(q.headline(0.24, 0.02, pathfor(X1p), 0.70), 0.20)
assert near(q.variant(0.23, 0.01, pathfor(X1p), 0.70), 0.74) and near(q.variant(0.24, 0.02, pathfor(X1p), 0.70), 0.73)
assert near(q.hold(0.23, "yes", "yes"), 0.75) and near(q.hold(0.24, "yes", "yes"), 0.74) and near(q.hold(0.25, "yes", "no"), -0.27) and near(q.hold(0.22, "yes", "void"), -0.02) and near(q.hold(0.22, "no", "no"), 0.76)
assert near(q.fee(0.23), 0.02) and near(q.fee(0.23, 2), 0.03) and near(q.fee(0.25, 2), 0.03) and near(q.fee(0.46), 0.02) and near(q.fee(0.14), 0.01) and near(q.fee(0.81), 0.02)
# --- looks, thresholds, bands, sides ---
def one(es_list, cmap, close=D(5)):
    mkx, csx, esx = assemble(window("KXINX15M-T", close, es_list, cmap))
    cnt = {"look_no_es_bar": 0, "look_es_roll": 0, "look_no_price": 0}
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
cnt = {"look_no_es_bar": 0, "look_es_roll": 0, "look_no_price": 0}; assert q.find_entries(D(5), esr, csr["KXINX15M-T"], cnt) == {} and cnt["look_es_roll"] == 1
# the first look wins even if a later look is also in band; one entry per band
f, _ = one([1000.0, 1001.0, 1001.0] + [1001.0] * 13, {1: (.20, .22), 2: (.22, .24)}); assert f[0.25][0] == 1
# --- exits: target range, tolerance, time exit, drops ---
Cl = D(5); O = Cl - 900
cands = lambda m2b: [{"ts": O + 60 * m, "bid": b, "ask": 1} for m, b in sorted(m2b.items())]
p = q.after_entry(cands({m: .15 for m in range(1, 16)}), O + 120, Cl); assert [t for t, _ in p] == [O + 60 * m for m in range(3, 11)]          # after the entry candle, through the minute ending close - 300 s (m = 10)
fill = 0.23
hit10 = [(O + 60 * m, .15) for m in range(3, 10)] + [(O + 600, 0.46)]; assert near(q.headline(fill, 0.01, hit10, 0.46), 0.45 - 0.23 - q.fee(fill) - q.fee(0.45))          # the m = 10 candle can be the target (inclusive)
nohit = [(O + 60 * m, .15) for m in range(3, 11)]; assert near(q.headline(fill, 0.01, nohit, 0.15), (0.14 - 0.23) - q.fee(fill) - q.fee(0.14))
assert q.headline(fill, 0.01, nohit, None) is None and q.variant(fill, 0.01, nohit, None) is None          # no time-exit bid and no target: dropped
assert q.headline(fill, 0.01, [(O + 180, 0.46)], None) is not None          # a target hit needs no time-exit candle
assert near(q.headline(0.25, 0.01, [(O + 180, 0.50)], None), 0.49 - 0.25 - q.fee(0.25) - q.fee(0.49))          # exactly 2 x fill hits
assert q.headline(0.25, 0.01, [(O + 180, 0.4999)], None) is None
assert q.headline(fill, 0.02, nohit, 0.005) is not None          # an exit price below 0: the fee is clamped, no error
# variant: only 2x hit (no 80c): half at 2x, the rest at the time exit; neither: both at the time exit
only2x = [(O + 240, 0.50)] + [(O + 60 * m, .15) for m in range(6, 11)]
assert near(q.variant(fill, 0.01, only2x, 0.15), (0.49 - fill) + (0.14 - fill) - q.fee(fill, 2) - q.fee(0.49) - q.fee(0.14))
assert near(q.variant(fill, 0.01, nohit, 0.15), 2 * (0.14 - fill) - q.fee(fill, 2) - 2 * q.fee(0.14))
exact80 = [(O + 240, 0.46), (O + 300, 0.80)]; assert near(q.variant(fill, 0.01, exact80, 0.15), (0.45 - fill) + (0.79 - fill) - q.fee(fill, 2) - q.fee(0.45) - q.fee(0.79))          # 0.80 exactly counts
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
empty = q.arm_report({0.01: [], 0.02: []}); assert empty["label"].startswith("FALSIFIED (fewer than 100") and empty["1c"]["pf"] is None
print("test_spxscalp_second: all checks passed")
