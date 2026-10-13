"""Plain assert tests for WX1 (src/scalper/wx1.py); run with: python tests/test_wx1.py. Each states a consequence, not a mechanism."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import wx1 as W
from scalper.scalps import fee

H = 3600
# The registered seven cities and their series, no more (another city would be an unregistered try); history goes to its own file.
assert set(W.CITIES) == {"KXHIGHCHI", "KXHIGHNY", "KXHIGHMIA", "KXHIGHAUS", "KXHIGHDEN", "KXHIGHLAX", "KXHIGHPHIL"} and W.WX_DB.name == "weather.sqlite"
assert (W.DECISION_LEFT_S, W.ENTRY_LEFT_S) == (26 * H, 25 * H) and W.ENTRY_LEFT_S < W.DECISION_LEFT_S, "the entry candle is strictly later than the decision candle"

# Buckets: integer rounding, and a full partition of the day's temperatures adds up to one.
assert W.bucket_range("between", 69, 70) == (68.5, 70.5) and W.bucket_range("less", None, 69) == (-1e9, 68.5) and W.bucket_range("greater", 76, None) == (76.5, 1e9)
parts = [W.bucket_range("less", None, 62), W.bucket_range("between", 62, 63), W.bucket_range("between", 64, 65), W.bucket_range("greater", 65, None)]
parts = [(-1e9, 61.5), (61.5, 63.5), (63.5, 65.5), (65.5, 1e9)]
assert abs(sum(W.bucket_prob(64.0, 2.0, r) for r in parts) - 1.0) < 1e-12
assert abs(W.bucket_prob(70.0, 2.0, (68.5, 70.5)) - (W.ncdf(0.25) - W.ncdf(-0.75))) < 1e-12
assert W.observed("between", 69, 70) == 69.5 and W.observed("less", None, 69) is None and W.observed("greater", 76, None) is None

# Calibration: too few days gives nothing; a perfect forecast still gets the sigma floor, never an overconfident zero.
assert W.calibrate([(70.0, 70.0)] * 9) is None
bias, sigma = W.calibrate([(70.0, 70.0)] * 12)
assert bias == 0 and sigma == W.SIGMA_FLOOR
assert abs(W.calibrate([(70.0, 71.0)] * 10 + [(70.0, 69.0)] * 10)[0]) < 1e-12 and W.calibrate([(70.0, 72.0)] * 10)[0] == 2.0

# The forecast max covers exactly the 24 hours ending at the close, and a missing hour means no forecast, not a guess.
C = 1_800_000_000
fc = {t: 60.0 for t in range(C - 86400, C, H)}
fc[C - 5 * H] = 75.0
fc[C] = 99.0                    # the close hour itself and the hour before the window are outside it
fc[C - 86400 - H] = 99.0
assert W.climate_mu(fc, C) == 75.0
fc[C - 20 * H] = 80.0           # an early hour of the climate day is inside the window too
assert W.climate_mu(fc, C) == 80.0
del fc[C - 20 * H]
del fc[C - 7 * H]
assert W.climate_mu(fc, C) is None

# Trade choice: the larger edge after the fee, at least 3c, price inside 5c to 95c.
yes = W.pick_trade(0.70, 0.50, 0.52)
assert yes[0] == "yes" and abs(yes[2] - (0.70 - 0.52 - fee(0.52))) < 1e-12
no = W.pick_trade(0.20, 0.55, 0.57)
assert no[0] == "no" and abs(no[1] - 0.45) < 1e-12 and abs(no[2] - (0.80 - 0.45 - fee(0.45))) < 1e-12
assert W.pick_trade(0.99, 0.01, 0.02) is None, "a price outside 5c to 95c is never taken, however big the model's edge"
assert W.pick_trade(0.51, 0.50, 0.51) is None, "no edge, no trade"


def build(n_days, fc_bias=0.0, mod=None):
    """n_days of one city: six buckets a day, the forecast mu = 70 + fc_bias, the true high alternating 69 / 71, quotes at the entry candle (and a poisoned one at the decision candle)."""
    by = {}
    fcd = {}
    for k in range(n_days):
        c = C + k * 86400
        for t in range(c - 86400, c, H):
            fcd[t] = 70.0 + fc_bias
        hi = 71 if k % 2 else 69
        bks = []
        for i, (stype, fl, cp) in enumerate([("less", None, 66), ("between", 66, 67), ("between", 68, 69), ("between", 70, 71), ("between", 72, 73), ("greater", 73, None)]):
            win = (stype == "between" and fl <= hi <= cp) if stype == "between" else False
            if win:
                res = "yes"
            else:
                res = "no"
            bks.append({"ticker": f"X-{k}-{i}", "result": res, "type": stype, "floor": fl, "cap": cp,
                        "q": {c - W.ENTRY_LEFT_S: (0.30, 0.31, 10.0), c - W.DECISION_LEFT_S: (0.01, 0.99, 10.0)}})
        # a resolved day must have exactly one YES bucket for the fit; the alternating high lands in a between bucket
        by[c] = bks
    if mod:
        mod(by, fcd)
    return {"KXHIGHCHI": by}, {"KXHIGHCHI": fcd}


# Days before the 20th prior resolved day have no trades or scored buckets; the first test day is the 21st.
days, fcd = build(25)
trades, brier = W.simulate(days, fcd)
assert trades and brier, "the fixture must produce trades or the checks below prove nothing"
assert min(t["close_ts"] for t in trades) >= C + 20 * 86400 and min(b["close_ts"] for b in brier) >= C + 20 * 86400, "a test day needs 20 prior resolved days"

# The lookahead guard: the previous day's own result closes two hours AFTER the decision, so it must not move the fit.
def flip_previous(by, fcd):
    c = C + 24 * 86400
    p = c - 86400
    for b in by[p]:
        b["result"] = "yes" if b["ticker"].endswith("-5") else "no"      # the previous day now "resolved" on the top tail instead
d0, f0 = build(25)
d1, f1 = build(25, mod=flip_previous)
t0 = [t for t in W.simulate(d0, f0)[0] if t["close_ts"] == C + 24 * 86400]
t1 = [t for t in W.simulate(d1, f1)[0] if t["close_ts"] == C + 24 * 86400]
assert t0 and t0 == t1, "day D-1 closes after day D's decision, so changing its result cannot change day D's trades"

# ... while day D-2 (known by then) does move the fit.
def shift_two_back(by, fcd):
    c = C + 24 * 86400 - 2 * 86400
    for b in by[c]:
        b["result"] = "yes" if b["ticker"].endswith("-4") else "no"       # observed 72.5 instead of 69.5/71.5
d2, f2 = build(25, mod=shift_two_back)
a = W.simulate(d0, f0)[1]
b = W.simulate(d2, f2)[1]
last = C + 24 * 86400
assert [x["model"] for x in a if x["close_ts"] == last] != [x["model"] for x in b if x["close_ts"] == last], "a result known before the decision does enter the fit"

# The entry candle is the one used: poisoning the DECISION candle's quote changes nothing, poisoning the ENTRY candle's does.
def poison_entry(by, fcd):
    for c, bks in by.items():
        for b in bks:
            b["q"][c - W.ENTRY_LEFT_S] = (0.01, 0.02, 1.0)
tp, _ = W.simulate(*build(25, mod=poison_entry))
base = W.simulate(d0, f0)[0]
assert base and tp != base, "the entry candle is the quote that is used"
poison_decision = lambda by, fcd: [b["q"].__setitem__(c - W.DECISION_LEFT_S, (0.50, 0.51, 1.0)) for c, bks in by.items() for b in bks]
assert W.simulate(*build(25, mod=poison_decision))[0] == base, "the decision candle quote is never used"

# Verdict: the registered conditions, each necessary. Words are only the three.
def mk(n, net=0.05, days=30):
    return [{"day": f"2026-09-{1 + (i % days):02d}" if days <= 28 else f"2026-{9 + (i % days) // 28:02d}-{1 + (i % days) % 28:02d}", "net": net, "stress": net - 0.003, "mid": 0.5, "price": 0.5} for i in range(n)]
assert W.verdict(mk(50), [0.0])[0] == "NOT_ENOUGH_DATA" and W.verdict(mk(300, days=10), [0.0])[0] == "NOT_ENOUGH_DATA"
def strong(n=300, days=25, **over):
    ts = []
    for i in range(n):
        net = 0.25 + 0.01 * (i % 5)
        ts.append({"day": f"2026-09-{1 + (i % days):02d}", "net": net, "stress": net - 0.003, "mid": 0.5, "price": 0.5})
    for t in ts:
        t.update({k: v(t) if callable(v) else v for k, v in over.items()})
    return ts
v, s_ = W.verdict(strong(), [-0.02] * 200)
assert v == "NOT_YET_FALSIFIED" and s_["z"] >= W.Z_BAR, "the positive path exists, so the checks below are not vacuous"
assert W.verdict(strong(), [0.30] * 200)[0] == "FALSIFIED", "a mean inside the placebo band falsifies even when positive"
assert W.verdict(strong(net=lambda t: -abs(t["net"]), stress=lambda t: -0.3), [-0.5] * 200)[0] == "FALSIFIED", "a negative mean falsifies"
assert W.verdict(strong(stress=-0.01), [-0.02] * 200)[0] == "FALSIFIED", "a stressed-fee loss falsifies"
first_half = lambda t: -0.01 if int(t["day"][-2:]) <= 12 else 0.5
assert W.verdict(strong(net=first_half), [-0.02] * 200)[0] == "FALSIFIED", "a negative first half falsifies"
second_half = lambda t: 0.5 if int(t["day"][-2:]) <= 12 else -0.01
assert W.verdict(strong(net=second_half), [-0.02] * 200)[0] == "FALSIFIED", "a negative second half falsifies"
assert W.verdict(strong(n=150), [-0.02] * 200)[0] == "NOT_ENOUGH_DATA"
parity = lambda t: 0.40 if int(t["day"][-2:]) % 2 == 0 else -0.30
vp, sp = W.verdict(strong(net=parity), [-0.5] * 200)
assert sp["mean"] > 0 and sp["h1"] > 0 and sp["h2"] > 0 and sp["stress"] > 0 and sp["z"] < W.Z_BAR and vp == "FALSIFIED", "a small positive mean with a big day-to-day swing fails on z alone"
# The placebo is reproducible and a fair market earns about minus the cost.
pm = W.placebo_means([{"mid": 0.5, "price": 0.5}] * 400)
assert pm == W.placebo_means([{"mid": 0.5, "price": 0.5}] * 400) and abs(sum(pm) / len(pm) + fee(0.5)) < 0.02

# The fit uses the last 20 usable days only: early odd days older than that must not move today's probabilities.
def drift(by, fcd):
    for k, c in enumerate(sorted(by)):
        if k < 15:
            for b in by[c]:
                b["result"] = "yes" if b["ticker"].endswith("-4") else "no"       # early days observed at 72.5
dd, ff = build(40, mod=drift)
last_c = max(dd["KXHIGHCHI"])
sim = [x for x in W.simulate(dd, ff)[1] if x["close_ts"] == last_c]
closes = sorted(dd["KXHIGHCHI"])
prior = [c for c in closes if c <= last_c - W.DECISION_LEFT_S]
hist = []
for c in prior[-20:]:
    wn = [b for b in dd["KXHIGHCHI"][c] if b["result"] == "yes"][0]
    hist.append((70.0, W.observed(wn["type"], wn["floor"], wn["cap"])))
bias, sigma = W.calibrate(hist)
exp = []
for b in dd["KXHIGHCHI"][last_c]:
    q = b["q"][last_c - W.ENTRY_LEFT_S]
    p = W.bucket_prob(70.0 + bias, sigma, W.bucket_range(b["type"], b["floor"], b["cap"]))
    mid = (q[0] + q[1]) / 2
    exp.append((p - (1.0 if b["result"] == "yes" else 0.0)) ** 2)
assert len(sim) == 6 and all(abs(x["model"] - e) < 1e-12 for x, e in zip(sim, exp)), "the fit is the last 20 prior days, nothing older"

code = "\n".join(l.split("#")[0] for l in Path(W.__file__).read_text().splitlines())
assert "promote" not in code.lower() and "NOT SHOWN" in code
print("WX1 passed")
