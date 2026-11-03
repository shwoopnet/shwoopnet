"""ENTER1 (workers/ENTER1_REGISTRATION.md): cheap side on markets that resolve on a public count, against a count-so-far model.
Research only. Only the pure rule and the fee are built: STEP 1 found no series with 100 settled markets AND a dated reference
(NOT_RUNNABLE), so there is no run(). Verdict words: FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. No promote verb.
"""
import math

LIMIT, LO, RATIO, OVERDISP = 0.30, 0.03, 3.0, 2.0


def fee(price, contracts=1):
    return math.ceil(round(0.07 * contracts * price * (1 - price) * 100, 9)) / 100


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def p_above(strike, so_far, rate_per_hour, hours_left):
    """P(final count > strike) given the count so far; remainder ~ Normal(m, (2 sqrt m)^2), clipped to [0.01, 0.99]."""
    m = max(0.0, rate_per_hour * hours_left)
    s = max(1e-9, OVERDISP * math.sqrt(m)) if m > 0 else 1e-9
    p = 1 - phi((strike + 0.5 - so_far - m) / s)
    return min(0.99, max(0.01, p))


def decide(p_yes, yes_ask, no_ask):
    """('yes'|'no', ask) for the cheap side with implied probability >= RATIO x ask and ask in [LO, LIMIT]; else None."""
    best = None
    for side, p, ask in (("yes", p_yes, yes_ask), ("no", 1 - p_yes, no_ask)):
        if ask is not None and LO <= ask <= LIMIT and p >= RATIO * ask:
            if best is None or p / ask > best[2]:
                best = (side, ask, p / ask)
    return best[:2] if best else None


def pnl(ask, won):
    return (1.0 if won else 0.0) - ask - fee(ask)
