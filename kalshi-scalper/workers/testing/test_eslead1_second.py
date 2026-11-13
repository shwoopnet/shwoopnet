"""Test for eslead1_second.py: INVENTED rows only (ESLEAD1_SECOND_HAND_CASE.md). Run: python3 -B -W ignore test_eslead1_second.py"""
import calendar, inspect, math, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eslead1_second as e

D = lambda day, h=21, mi=0, s=0: calendar.timegm((2026, 11, day, h, mi, s))
LAGS = e.LAGS
S1 = [1, -1, 1, 1, -1, -1]                              # ES change signs for m = 1..6
ES_CLOSES = [1000.0, 1001.0, 1000.0, 1001.0, 1002.001, 1001.0, 1000.0]          # log changes +a, -a, +a, +a, -a, -a with a = ln(1.001)
def mids_follow(signs, base=0.50, step=0.02, shift=0.0):
    """mids for m = 1..6 with dA[m] = step x signs[m - 2] (+ shift) for m = 2..6: Kalshi follows ES by one minute when signs are s(m - 1)."""
    m = [base]
    for i in range(5): m.append(round(m[-1] + step * signs[i] + shift, 10))
    return m
M1 = mids_follow(S1[:5])                                  # .02 x s(m - 1)
assert [round(x, 2) for x in M1] == [0.50, 0.52, 0.50, 0.52, 0.54, 0.52]
def window(tk, close, mids, es_closes=ES_CLOSES, drop_ask=(), drop_es=()):
    o = close - 900
    cs = [{"ts": o + 60 * (i + 1), "bid": round(mids[i] - 0.01, 10), "ask": (None if (i + 1) in drop_ask else round(mids[i] + 0.01, 10))} for i in range(len(mids))]
    es = {o + 60 * m: (1, c) for m, c in enumerate(es_closes) if m not in drop_es}
    return {"ticker": tk, "close": close}, cs, es
def assemble(*ws):
    mk, cs, es = {}, {}, {}
    for m, c, x in ws:
        mk[m["ticker"]] = {"series": "KXINX15M", "ticker": m["ticker"], "close": m["close"]}; cs[m["ticker"]] = c; es.update(x)
    return mk, cs, es
W1 = window("KXINX15M-W1", D(5), M1)
mk, cs, es = assemble(W1)
r = e.measure(mk, cs, es, 3)
exp = {-3: None, -2: 0.5, -1: -2 / math.sqrt(12), 0: -0.8 / 4.8, 1: 1.0, 2: -2 / math.sqrt(12), 3: -0.5}
for k_ in LAGS:
    got = r["lags"][k_]["corr"]
    assert (got is None) if exp[k_] is None else abs(got - exp[k_]) < 1e-9, (k_, got, exp[k_])
assert [r["lags"][k_]["n_pairs"] for k_ in LAGS] == [2, 3, 4, 5, 5, 4, 3] and r["na_lags"] == [-3] and r["lags"][-3]["na_reason"].startswith("under the floor")
assert r["line"] == "lead_lag (positive lag = Kalshi lags ES): -3:n/a -2:0.500 -1:-0.577 +0:-0.167 +1:1.000 +2:-0.577 +3:-0.500", r["line"]
assert r["prediction_peak_at_lag_0_passed"] is False and r["defined_peak_lag"] == 1          # Kalshi lags ES by one minute: positive peak lag
assert r["counts"]["windows_used"] == 1 and r["counts"]["dA_missing_lookback"] == 1 and r["counts"]["dB_missing_bar"] == 0          # dA at the first candle has no mid before it
# the floor is an argument: at 5 only the lags with 5 pairs survive
r5 = e.measure(mk, cs, es, 5); assert r5["na_lags"] == [-3, -2, -1, 2, 3] and r5["lags"][0]["corr"] is not None and r5["lags"][1]["corr"] is not None
# W1 + W2 (the same data again): pairs double, correlations unchanged, lag -3 has 4 pairs but zero variance (n/a)
W2 = window("KXINX15M-W2", D(6), M1)
mk2, cs2, es2 = assemble(W1, W2); r2 = e.measure(mk2, cs2, es2, 3)
assert [r2["lags"][k_]["n_pairs"] for k_ in LAGS] == [4, 6, 8, 10, 10, 8, 6] and r2["lags"][-3]["na_reason"] == "zero variance" and r2["lags"][-3]["n_pairs"] == 4
for k_ in LAGS[1:]: assert abs(r2["lags"][k_]["corr"] - exp[k_]) < 1e-9
# pooling: W3 = W1's signs with every dA shifted by +0.1: its own correlations equal W1's, the POOLED one does not
M3 = mids_follow(S1[:5], base=0.10, shift=0.10)
assert [round(x, 2) for x in M3] == [0.10, 0.22, 0.30, 0.42, 0.54, 0.62]
W3 = window("KXINX15M-W3", D(7), M3)
mk3, cs3, es3 = assemble(W1, W3); r13 = e.measure(mk3, cs3, es3, 3)
r3only = e.measure(*assemble(W3), 3)
for k_ in LAGS[1:]: assert abs(r3only["lags"][k_]["corr"] - exp[k_]) < 1e-9 or k_ == -3, k_          # within one window the constant shift does not matter
def direct(k_):          # an independent pooled Pearson on the raw changes
    xs, ys = [], []
    for M in (M1, M3):
        dA = {m: M[m - 1] - M[m - 2] for m in range(2, 7)}
        dB = {m: math.log(ES_CLOSES[m] / ES_CLOSES[m - 1]) for m in range(1, 7)}
        for t in range(2, 7):
            tb = t - k_
            if 1 <= tb <= 6 and t in dA and tb in dB: xs.append(dA[t]); ys.append(dB[tb])
    n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)), n
for k_ in (0, 1, 2):
    d, n = direct(k_); assert abs(r13["lags"][k_]["corr"] - d) < 1e-9 and r13["lags"][k_]["n_pairs"] == n, (k_, r13["lags"][k_], d)
assert abs(r13["lags"][0]["corr"] - exp[0]) > 0.01 and abs((exp[0] + exp[0]) / 2 - r13["lags"][0]["corr"]) > 0.01          # pooled is not the average of per-window correlations
# a missing ask: the mid at that minute is missing (never carried); dA at it and at the next minute are gone (the lookback needs both)
Wm = window("KXINX15M-M", D(5), M1, drop_ask=(3,)); rm = e.measure(*assemble(Wm), 3)
assert rm["counts"]["dA_missing_lookback"] == 2 and rm["lags"][1]["n_pairs"] == 3 and abs(rm["lags"][1]["corr"] - 1.0) < 1e-9, (rm["counts"], rm["lags"][1])          # dA at m = 1 (no earlier mid) and m = 4 (A(3) missing)
# a missing ES bar at the window start: dB[1] is missing (counted); lag +1 then has t = 3..6 (n 4) and r = +1
We = window("KXINX15M-E", D(5), M1, drop_es=(0,)); re_ = e.measure(*assemble(We), 3)
assert re_["counts"]["dB_missing_bar"] == 1 and re_["lags"][1]["n_pairs"] == 4 and abs(re_["lags"][1]["corr"] - 1.0) < 1e-9, (re_["counts"], re_["lags"][1])
# a roll between two bars drops that dB and is counted
Wr = window("KXINX15M-R", D(5), M1); mkr, csr, esr = assemble(Wr); o = D(5) - 900; esr[o + 180] = (2, esr[o + 180][1])
rr = e.measure(mkr, csr, esr, 3); assert rr["counts"]["dB_roll"] == 2          # the bar at m = 3 has another id: the changes into and out of it
# a lag-0 peak: Kalshi moves with ES (dA[m] = .02 s(m)): lag 0 = +1, the prediction passes over the defined lags
M0 = mids_follow(S1[1:6])
r0 = e.measure(*assemble(window("KXINX15M-P", D(5), M0)), 3)
assert abs(r0["lags"][0]["corr"] - 1.0) < 1e-9 and r0["prediction_peak_at_lag_0_passed"] is True and r0["defined_peak_lag"] == 0 and r0["na_lags"] == [-3]
# Kalshi LEADS ES (dA[m] = .02 s(m + 1)): a NEGATIVE lag peaks, and the prediction fails although no positive lag exceeds lag 0
Ml = [0.50]
for m_ in range(2, 7): Ml.append(round(Ml[-1] + 0.02 * (S1[m_] if m_ < 6 else 1), 10))          # s(m + 1) for m = 2..5; the last change is +
rl = e.measure(*assemble(window("KXINX15M-L", D(5), Ml)), 3)
assert rl["defined_peak_lag"] == -1 and abs(rl["lags"][-1]["corr"] - 1.0) < 1e-9 and rl["prediction_peak_at_lag_0_passed"] is False, rl["line"]          # the Kalshi mid leads: lag -1 = +1.000
# the prediction rule on its own: lag 0 must be the largest of all defined lags, negative lags included; a tie passes
assert e.prediction({0: 0.5, -1: 0.6, 1: 0.1}) is False and e.prediction({0: 0.5, -1: 0.4, 1: 0.5}) is True and e.prediction({0: 0.5, 3: 0.5 + 1e-10}) is True and e.prediction({0: 0.5, 3: 0.51}) is False
assert e.prediction({-1: 0.5, 1: 0.2}) is None and e.prediction({0: -0.1, 1: -0.2, -1: -0.3}) is True and e.prediction({0: -0.1, 1: -0.05}) is False
# lag 0 undefined (zero variance): the prediction is not assessable
rz = e.measure(*assemble(window("KXINX15M-Z", D(5), [0.5] * 6)), 3); assert rz["prediction_peak_at_lag_0_passed"] is None and rz["lags"][0]["na_reason"] == "zero variance"
# dates: closes 2026-11-04T23:59:59Z and 2026-11-13T00:00:00Z are not touched (counted), 2026-11-05T00:00:00Z is in
class Poison(dict):
    def __init__(self, base, bad): super().__init__(base); self.bad = set(bad)
    def get(self, key, default=None):
        if key in self.bad: raise AssertionError("touched an excluded window: " + key)
        return super().get(key, default)
    def __getitem__(self, key):
        if key in self.bad: raise AssertionError("touched an excluded window: " + key)
        return super().__getitem__(key)
Wa, Wb, Wc = window("KXINX15M-A", D(4, 23, 59, 59), M1), window("KXINX15M-B", D(13, 0, 0, 0), M1), window("KXINX15M-C", D(5, 0, 0, 0), M1)
mkd, csd, esd = assemble(Wa, Wb, Wc)
rd = e.measure(mkd, Poison(csd, ("KXINX15M-A", "KXINX15M-B")), esd, 3)
assert rd["counts"]["windows_listed"] == 3 and rd["counts"]["outside_dates_not_touched"] == 2 and rd["counts"]["windows_used"] == 1
# another series is ignored; a window with no candles is counted
mko = dict(mkd); mko["KXBTC15M-X"] = {"series": "KXBTC15M", "ticker": "KXBTC15M-X", "close": D(5)}
assert e.measure(mko, csd, esd, 3)["counts"]["windows_listed"] == 3
mkn = {"KXINX15M-N": {"series": "KXINX15M", "ticker": "KXINX15M-N", "close": D(5)}}; assert e.measure(mkn, {}, {}, 3)["counts"]["windows_without_candles"] == 1
# pearson unit cases
assert abs(e.pearson([1, 2, 3], [2, 4, 6], 3)[0] - 1.0) < 1e-12 and abs(e.pearson([1, 2, 3], [3, 2, 1], 3)[0] + 1.0) < 1e-12
assert e.pearson([1, 2], [1, 2], 3)[0] is None and e.pearson([1, 1, 1], [1, 2, 3], 3) == (None, "zero variance") and e.pearson([1, 2, 3], [5, 5, 5], 3) == (None, "zero variance")
# the ES loader: the stamp is the bar START, so the minute END is ts_event + 60 s; a duplicate ts_event stops the run
with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "es.csv")
    open(f, "w").write("ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume\n2026-11-05T14:44:00.000000000Z,33,1,7,1,1,1,1000.5,10\n2026-11-05T14:45:00.000000000Z,33,1,7,1,1,1,1001.5,10\n")
    got = e.load_es(f); end = D(5, 14, 45)
    assert got == {end: (7, 1000.5), end + 60: (7, 1001.5)}, got
    open(f, "a").write("2026-11-05T14:45:00.000000000Z,33,1,7,1,1,1,1002.5,10\n")
    try: e.load_es(f); assert 0
    except SystemExit as ex: assert "duplicate ES ts_event 2026-11-05T14:45:00" in str(ex)
# nothing is written and the floor has no default
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "eslead1_second.py")).read()
assert '"w"' not in src and "'w'" not in src and "write(" not in src.replace("sys.stdout.write", "")
assert inspect.signature(e.measure).parameters["min_pairs"].default is inspect.Parameter.empty and inspect.signature(e.run).parameters["min_pairs"].default is inspect.Parameter.empty
print("test_eslead1_second: all checks passed")
