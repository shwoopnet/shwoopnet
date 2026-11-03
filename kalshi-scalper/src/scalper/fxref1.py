"""FXREF1: distance-to-strike nowcast against an outside spot reference, cheap side only.
Registration: workers/FXREF1_REGISTRATION.md. Pure functions; no network, no result access."""
from __future__ import annotations
import math

FEE_RATE = 0.07
LO, HI, RATIO, MINUTES = 0.03, 0.30, 3.0, 10.0


def ncdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def vol_per_minute(closes: list[float]) -> float | None:
    """Std of the last 60 one-minute log returns; needs at least 40."""
    r = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a > 0 and b > 0][-60:]
    if len(r) < 40:
        return None
    m = sum(r) / len(r)
    v = (sum((x - m) ** 2 for x in r) / (len(r) - 1)) ** 0.5
    return v if v > 0 else None


def p_yes(spot: float, strike: float, sig_min: float, minutes: float = MINUTES) -> float:
    return ncdf(math.log(spot / strike) / (sig_min * math.sqrt(minutes)))


def fee_per_contract(p: float, c: int = 10) -> float:
    return math.ceil(FEE_RATE * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def decide(yes_ask: float, no_ask: float, py: float):
    """Cheap side only. Returns (side, ask, model_prob) or None."""
    side, ask, pm = ("yes", yes_ask, py) if yes_ask <= no_ask else ("no", no_ask, 1 - py)
    if not (LO <= ask <= HI) or pm < RATIO * ask:
        return None
    return side, ask, pm


def net(side: str, ask: float, result: str, mult: float = 1.0) -> float:
    return (1.0 if side == result else 0.0) - ask - fee_per_contract(ask) * mult
