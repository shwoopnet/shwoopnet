"""Losing-streak arithmetic for a trade sequence (research helper, no data, no network, no live code).

A "trade" is a win with probability p_win and a loss otherwise, independent of the others. All results are exact
(dynamic programming over the length of the current losing run) unless a function says it simulates.

    prob_run_at_least(k, p_win, n)             chance of at least one run of k straight losses in n trades
    longest_losing_run_distribution(p_win, n)  exact pmf and mean / median / 95th / 99th percentile of the longest losing run
    empirical_streaks(outcomes)                longest losing run and histogram of losing runs in a realised sequence
    expected_trades_between_runs(k, p_win)     mean number of trades until a run of k losses is first completed

Independence is an assumption: a real strategy's losses cluster (the live record has windows where two markets lose together),
so read these as a floor for how long a bad run can look, never a ceiling.
"""
from __future__ import annotations

import random


def _check(p_win, n=None, k=None):
    if not 0.0 <= p_win <= 1.0:
        raise ValueError("p_win must be in [0, 1]")
    if n is not None and (int(n) != n or n < 0):
        raise ValueError("n must be a non-negative integer")
    if k is not None and (int(k) != k or k < 1):
        raise ValueError("k must be an integer of at least 1")


def prob_run_at_least(k, p_win, n):
    """Exact chance of at least one run of k or more consecutive losses in n trades.

    State = length of the current losing run (0 .. k-1); reaching k is absorbing. O(n * k)."""
    _check(p_win, n=n, k=k)
    q = 1.0 - p_win
    if n < k:
        return 0.0
    state = [0.0] * k          # state[j] = P(current losing run is j, no run of k yet)
    state[0] = 1.0
    hit = 0.0
    for _ in range(int(n)):
        new = [0.0] * k
        total_ok = sum(state)
        new[0] = total_ok * p_win          # a win resets the run
        for j in range(k - 1):
            new[j + 1] += state[j] * q     # a loss extends it
        hit += state[k - 1] * q            # a loss from k-1 completes a run of k
        state = new
    return hit


def longest_losing_run_distribution(p_win, n, sims=None, seed=1):
    """Distribution of the longest losing run in n trades.

    Exact by default: P(longest <= m) = 1 - prob_run_at_least(m + 1, p_win, n). With sims=N it instead draws N sequences
    (a cross-check, not needed for use). Returns a dict: mean, median, p95, p99, pmf (list, index = run length), cdf, n, p_win."""
    _check(p_win, n=n)
    n = int(n)
    if sims:
        rng = random.Random(seed)
        counts = [0] * (n + 1)
        for _ in range(int(sims)):
            best = cur = 0
            for _t in range(n):
                if rng.random() < p_win:
                    cur = 0
                else:
                    cur += 1
                    if cur > best:
                        best = cur
            counts[best] += 1
        pmf = [c / sims for c in counts]
    else:
        # cdf[m] = P(longest <= m)
        cdf = [1.0 - prob_run_at_least(m + 1, p_win, n) for m in range(n)] + [1.0]
        pmf = [cdf[0]] + [max(0.0, cdf[m] - cdf[m - 1]) for m in range(1, n + 1)]
    cdf = []
    run = 0.0
    for x in pmf:
        run += x
        cdf.append(run)

    def pct(q):
        for m, c in enumerate(cdf):
            if c >= q - 1e-12:
                return m
        return n

    mean = sum(m * x for m, x in enumerate(pmf))
    return {"p_win": p_win, "n": n, "mean": mean, "median": pct(0.5), "p95": pct(0.95), "p99": pct(0.99),
            "pmf": pmf, "cdf": cdf, "sims": int(sims) if sims else None}


def empirical_streaks(outcomes):
    """Streaks in a realised sequence. outcomes: iterable of win flags (truthy = win, falsy = loss), oldest first.

    Returns longest_losing_run, longest_winning_run, losing_run_histogram {length: how many runs of exactly that length},
    n, losses, and current_losing_run (the run still open at the end)."""
    seq = [bool(x) for x in outcomes]
    hist = {}
    longest_loss = longest_win = cur_loss = cur_win = 0
    for w in seq:
        if w:
            if cur_loss:
                hist[cur_loss] = hist.get(cur_loss, 0) + 1
            cur_loss = 0
            cur_win += 1
            longest_win = max(longest_win, cur_win)
        else:
            cur_win = 0
            cur_loss += 1
            longest_loss = max(longest_loss, cur_loss)
    current = cur_loss
    if cur_loss:
        hist[cur_loss] = hist.get(cur_loss, 0) + 1
    return {"n": len(seq), "losses": sum(1 for w in seq if not w), "longest_losing_run": longest_loss,
            "longest_winning_run": longest_win, "losing_run_histogram": dict(sorted(hist.items())),
            "current_losing_run": current}


def expected_trades_between_runs(k, p_win):
    """Mean number of trades until a run of k straight losses is first completed (and, by renewal, the mean gap between
    successive non-overlapping runs): (1 - q^k) / (p_win * q^k) with q = 1 - p_win. Infinite if p_win is 1 (a loss never
    comes) and k if p_win is 0."""
    _check(p_win, k=k)
    q = 1.0 - p_win
    if p_win == 1.0:
        return float("inf")
    if p_win == 0.0:
        return float(k)
    return (1.0 - q ** k) / (p_win * q ** k)


if __name__ == "__main__":
    import sys
    p = float(sys.argv[1]) if len(sys.argv) > 1 else 0.28
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    d = longest_losing_run_distribution(p, n)
    print(f"p_win {p}, n {n}: longest losing run mean {d['mean']:.2f}, median {d['median']}, p95 {d['p95']}, p99 {d['p99']}")
    for k in (5, 10, 15, 20):
        print(f"  P(run of {k}+ losses in {n} trades) = {prob_run_at_least(k, p, n):.4f}; "
              f"mean trades until a run of {k}: {expected_trades_between_runs(k, p):,.0f}")
