"""CHART1: daily-lead rule on weekly rank markets (see workers/CHART1_REGISTRATION.md).

Only the pure rule and fee are built. The daily ranking history needed to score it is not
obtainable (FlixPatrol 403, Netflix and kworb publish only the current day), so there is no run().
"""
import math
from collections import Counter


def fee(price, contracts=1):
    return math.ceil(round(0.07 * contracts * price * (1 - price) * 100, 9)) / 100


def lead_title(daily_rank1):
    """Mode of the rank-1 titles on Mon..Thu; None on a tie or fewer than 3 days."""
    if len(daily_rank1) < 3:
        return None
    c = Counter(daily_rank1).most_common(2)
    if len(c) > 1 and c[0][1] == c[1][1]:
        return None
    return c[0][0]


def decide(daily_rank1, asks, hit_rate, edge=0.08):
    """asks: {title: yes ask}. Returns (title, ask) or None. hit_rate fit on discovery only."""
    t = lead_title(daily_rank1)
    if t is None or t not in asks:
        return None
    a = asks[t]
    return (t, a) if a + fee(a) <= hit_rate - edge else None


def pnl(ask, won):
    return (1.0 if won else 0.0) - ask - fee(ask)
