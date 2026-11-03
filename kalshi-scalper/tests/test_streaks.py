"""Plain assert tests for src/scalper/streaks.py (losing-streak arithmetic). Synthetic only, no data.
Run with: cd kalshi-scalper && PYTHONPATH=src python tests/test_streaks.py"""
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import streaks as S


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol


# 1. tiny cases checked by brute force over every sequence
for p, n, k in [(0.5, 8, 3), (0.28, 10, 2), (0.28, 10, 4), (0.9, 7, 1), (0.3, 6, 6), (0.3, 5, 6)]:
    exact = 0.0
    for seq in itertools.product([0, 1], repeat=n):          # 1 = win
        pr = 1.0
        for w in seq:
            pr *= p if w else (1 - p)
        if S.empirical_streaks(seq)["longest_losing_run"] >= k:
            exact += pr
    assert close(S.prob_run_at_least(k, p, n), exact), (p, n, k, S.prob_run_at_least(k, p, n), exact)

# 2. closed forms and edges
assert S.prob_run_at_least(1, 0.28, 1) == 0.72                    # one trade, one loss
assert close(S.prob_run_at_least(3, 0.5, 3), 0.125)               # LLL
assert close(S.prob_run_at_least(3, 0.5, 4), 0.1875)              # LLLx or xLLL: 1/8 + 1/16
assert S.prob_run_at_least(5, 0.5, 4) == 0.0                      # fewer trades than the run
assert S.prob_run_at_least(2, 1.0, 50) == 0.0                     # never loses
assert close(S.prob_run_at_least(2, 0.0, 2), 1.0)                 # always loses

# 3. the owner's numbers: a coin, 10 straight losses in 100 trades. Exact value, then a simulation agrees.
exact_coin = S.prob_run_at_least(10, 0.5, 100)
assert 0.043 < exact_coin < 0.046, exact_coin                     # 0.0441 (the owner's remembered 0.0485 to 0.05 is a little high)
rng = random.Random(7)
sims, hits = 40000, 0
for _ in range(sims):
    cur = best = 0
    for _t in range(100):
        if rng.random() < 0.5:
            cur = 0
        else:
            cur += 1
            best = max(best, cur)
    hits += best >= 10
est = hits / sims
assert abs(est - exact_coin) < 4 * (exact_coin * (1 - exact_coin) / sims) ** 0.5, (est, exact_coin)

# 4. p_win 0.28 (OICORE-like): exact against simulation, monotone in k and n
p28 = S.prob_run_at_least(10, 0.28, 100)
assert 0.66 < p28 < 0.68, p28
hits = 0
for _ in range(sims):
    cur = best = 0
    for _t in range(100):
        if rng.random() < 0.28:
            cur = 0
        else:
            cur += 1
            best = max(best, cur)
    hits += best >= 10
assert abs(hits / sims - p28) < 4 * (p28 * (1 - p28) / sims) ** 0.5
assert S.prob_run_at_least(11, 0.28, 100) < p28 < S.prob_run_at_least(9, 0.28, 100)
assert S.prob_run_at_least(10, 0.28, 200) > p28

# 5. distribution: pmf sums to 1, cdf consistent with prob_run_at_least, percentile order, exact vs simulated
d = S.longest_losing_run_distribution(0.28, 100)
assert close(sum(d["pmf"]), 1.0) and close(d["cdf"][-1], 1.0)
assert close(d["cdf"][9], 1 - p28)                                # P(longest <= 9) = 1 - P(run of 10)
assert d["median"] <= d["p95"] <= d["p99"]
assert (d["median"], d["p95"], d["p99"]) == (11, 18, 23), (d["median"], d["p95"], d["p99"])
assert 11.2 < d["mean"] < 11.7, d["mean"]
sim = S.longest_losing_run_distribution(0.28, 100, sims=20000, seed=3)
assert abs(sim["mean"] - d["mean"]) < 0.15 and abs(sim["p95"] - d["p95"]) <= 1
dc = S.longest_losing_run_distribution(0.5, 100)
assert (dc["median"], dc["p95"], dc["p99"]) == (6, 9, 12), (dc["median"], dc["p95"], dc["p99"])
assert S.longest_losing_run_distribution(1.0, 50)["mean"] == 0.0
assert S.longest_losing_run_distribution(0.5, 0)["p95"] == 0

# 6. realised sequence
e = S.empirical_streaks([1, 0, 0, 1, 1, 0, 0, 0, 1, 0])
assert e["longest_losing_run"] == 3 and e["longest_winning_run"] == 2
assert e["losing_run_histogram"] == {1: 1, 2: 1, 3: 1} and e["n"] == 10 and e["losses"] == 6
assert e["current_losing_run"] == 1
e2 = S.empirical_streaks([True, False, False, False])
assert e2["current_losing_run"] == 3 and e2["losing_run_histogram"] == {3: 1}
e3 = S.empirical_streaks([])
assert e3["longest_losing_run"] == 0 and e3["losing_run_histogram"] == {}
assert S.empirical_streaks([1, 1, 1])["longest_losing_run"] == 0

# 7. expected trades until a run: coin k=2 is 6, k=1 is 1/p_loss; matches a simulation at p_win 0.28, k=10
assert close(S.expected_trades_between_runs(2, 0.5), 6.0)
assert close(S.expected_trades_between_runs(1, 0.28), 1 / 0.72)
assert close(S.expected_trades_between_runs(3, 0.5), 14.0)
assert S.expected_trades_between_runs(4, 1.0) == float("inf") and S.expected_trades_between_runs(4, 0.0) == 4.0
ev = S.expected_trades_between_runs(10, 0.28)
assert 90 < ev < 94, ev
tot, runs = 0, 3000
for _ in range(runs):
    cur = t = 0
    while cur < 10:
        t += 1
        cur = 0 if rng.random() < 0.28 else cur + 1
    tot += t
assert abs(tot / runs - ev) < 0.1 * ev

# 8. bad input
for bad in (lambda: S.prob_run_at_least(0, 0.3, 10), lambda: S.prob_run_at_least(2, 1.2, 10), lambda: S.prob_run_at_least(2, 0.3, -1)):
    try:
        bad()
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

# 9. a reference point for the live core: 19 straight losses at a 28% win rate over 555 trades (FALS4 check 6)
assert 0.2 < S.prob_run_at_least(19, 0.28, 555) < 0.3   # about 26%: "normal" as FALS4 wrote
print("test_streaks: all passed")
print(f"  p_win 0.28, n 100: mean {d['mean']:.2f}, median {d['median']}, p95 {d['p95']}, p99 {d['p99']}; P(10+ losses) {p28:.4f}")
print(f"  coin, n 100: P(10+ losses) {exact_coin:.4f}; P(19+ losses in 555 at 0.28) {S.prob_run_at_least(19, 0.28, 555):.3f}")
