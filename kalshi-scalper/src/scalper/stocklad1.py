"""STOCKLAD1: single-stock close ladders priced against realised vol with student-t tails.

Skeleton only. The census (2026-11-04) found NO Kalshi single-stock price ladder or
range series, so nothing here has been run on market data. Kept so the rule is
fixed in code if such a series is ever listed. Cheap side only (ask 3c to 30c)."""
from __future__ import annotations

import math

CHEAP_LO, CHEAP_HI = 0.03, 0.30
MIN_RATIO = 3.0
MAX_PER_EVENT = 2


def realised_vol(closes: list[float], n: int = 20) -> float | None:
    """Daily stdev of log returns over the last n returns (needs n+1 closes)."""
    if len(closes) < n + 1:
        return None
    r = [math.log(closes[i] / closes[i - 1]) for i in range(len(closes) - n, len(closes))]
    m = sum(r) / n
    return math.sqrt(sum((x - m) ** 2 for x in r) / (n - 1))


def t_cdf(x: float, df: float) -> float:
    """Student t CDF by numeric integration (no scipy). df > 2."""
    if x == 0:
        return 0.5
    c = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi)
    a, steps = abs(x), 2000
    h = a / steps
    s = 0.0
    for i in range(steps + 1):
        w = 1 if i in (0, steps) else (4 if i % 2 else 2)
        s += w * (1 + (i * h) ** 2 / df) ** (-(df + 1) / 2)
    area = c * s * h / 3
    return 0.5 + area if x > 0 else 0.5 - area


def prob_above(spot: float, strike: float, daily_vol: float, days: float, df: float) -> float:
    """P(close >= strike) with t tails scaled to unit variance over the horizon."""
    if daily_vol <= 0 or days <= 0 or df <= 2:
        raise ValueError("bad inputs")
    scale = daily_vol * math.sqrt(days) * math.sqrt((df - 2) / df)
    z = math.log(strike / spot) / scale
    return 1.0 - t_cdf(z, df)


def pick(candidates: list[dict]) -> list[dict]:
    """candidates: {ask, p_side}. Cheap side only, p >= 3x ask, best ratio first, max 2."""
    ok = [c for c in candidates if CHEAP_LO <= c["ask"] <= CHEAP_HI and c["p_side"] >= MIN_RATIO * c["ask"]]
    ok.sort(key=lambda c: c["p_side"] / c["ask"], reverse=True)
    return ok[:MAX_PER_EVENT]
