"""COMBOPRICE1: offline pricing helpers for combo (parlay) markets. Pure functions, no network, numpy only.

Every probability here is the chance the BOUGHT side of each leg wins (a NO leg enters as 1 minus the YES mid).
The fee formula is the standard taker formula, NOT a verified combo-specific fee (see workers/COMBOPRICE1_DESIGN.md).
"""
import math
from statistics import NormalDist

import numpy as np

_ND = NormalDist()


def _check(probs):
    p = [float(x) for x in probs]
    if not p or any(not (0.0 < x < 1.0) for x in p):
        raise ValueError("leg probabilities must be in (0, 1) and non-empty")
    return p


def independence_product(probs):
    r = 1.0
    for x in _check(probs):
        r *= x
    return r


def frechet_bounds(probs):
    """(lower, upper) of the joint win chance of all legs for ANY dependence: max(0, sum - (n-1)) and min."""
    p = _check(probs)
    return max(0.0, sum(p) - (len(p) - 1)), min(p)


def copula_joint(probs, rho, nodes=200):
    """P(all legs win) under a one-factor Gaussian copula with common correlation rho in [0, 1].
    Leg i wins when sqrt(rho) Z + sqrt(1-rho) e_i < c_i, c_i = Phi^-1(p_i); integrate over Z by Gauss-Hermite."""
    p = _check(probs)
    rho = float(rho)
    if not (0.0 <= rho <= 1.0):
        raise ValueError("rho must be in [0, 1]")
    if rho == 0.0:
        return independence_product(p)
    if rho >= 1.0:
        return min(p)
    c = np.array([_ND.inv_cdf(x) for x in p])
    x, w = np.polynomial.hermite_e.hermegauss(nodes)  # weight exp(-x^2/2)
    arg = (c[None, :] - math.sqrt(rho) * x[:, None]) / math.sqrt(1.0 - rho)
    cdf = 0.5 * (1.0 + np.vectorize(math.erf)(arg / math.sqrt(2.0)))
    return float(np.sum(w * np.prod(cdf, axis=1)) / math.sqrt(2.0 * math.pi))


def taker_fee(price, rounded=True):
    """Standard taker fee per contract on the combo price: 0.07 p (1-p), ceiled to the cent when rounded."""
    f = 0.07 * price * (1.0 - price)
    return math.ceil(f * 100 - 1e-9) / 100 if rounded else f


def edge_per_dollar(win_prob, ask, rounded_fee=True):
    """Net cash per dollar staked for one contract bought at `ask`, held to settlement, after the fee:
    (win_prob - ask - fee) / (ask + fee). Cost includes the fee."""
    if not (0.0 < ask < 1.0):
        raise ValueError("ask must be in (0, 1)")
    fee = taker_fee(ask, rounded_fee)
    return (win_prob - ask - fee) / (ask + fee)


def return_per_dollar_year(edge, years):
    if years <= 0:
        raise ValueError("years must be positive")
    return edge / years


def breakeven_rho(probs, ask, rho_grid=None):
    """Smallest rho on a grid at which the copula joint covers ask + fee (edge 0), or None."""
    grid = rho_grid or [i / 20 for i in range(21)]
    need = ask + taker_fee(ask)
    for r in grid:
        if copula_joint(probs, r) >= need:
            return r
    return None


def sensitivity(probs, ask, years=1.0, rhos=(0.0, 0.1, 0.3, 0.5, 0.7)):
    """Rows of (label, joint, edge per dollar, per dollar-year) for the independence product, each rho and both Frechet bounds."""
    lo, hi = frechet_bounds(probs)
    rows = []
    for r in rhos:
        j = copula_joint(probs, r)
        e = edge_per_dollar(j, ask)
        rows.append((f"rho {r:g}", j, e, return_per_dollar_year(e, years)))
    for lab, j in (("Frechet lower", lo), ("Frechet upper", hi)):
        e = edge_per_dollar(j, ask)
        rows.append((lab, j, e, return_per_dollar_year(e, years)))
    return rows


def format_popup_spec(legs, ask, side, close_date, years, rho_assumed, link_text, stake=2.0, total_stop=40.0):
    """One-page owner popup text. legs = [(ticker, 'YES'|'NO', prob_of_bought_side)]."""
    probs = [l[2] for l in legs]
    n = len(probs)
    ind = independence_product(probs)
    lo, hi = frechet_bounds(probs)
    out = [f"COMBO PROBE SPEC ({n} legs, buy {side} at {ask:.2f}, ${stake:.2f} per parlay, stop ${total_stop:.0f} total)",
           "LOCK-UP: MONEY IS HELD UNTIL SETTLEMENT, expected " + str(close_date) + f" (about {years:.2f} years). Hold to settlement, no early exit assumed.",
           "LEGS:"]
    out += [f"  {t} {s} (mid-based chance {p:.3f})" for t, s, p in legs]
    out.append("LINK (written): " + link_text)
    out.append(f"WIN CHANCE: independence {ind:.4f}; assumed rho {rho_assumed:g}: {copula_joint(probs, rho_assumed):.4f}; Frechet range {lo:.4f} to {hi:.4f}")
    out.append("PAPER EDGE per dollar (after fee, standard taker formula, combo fee UNVERIFIED) and per dollar-year:")
    for lab, j, e, y in sensitivity(probs, ask, years):
        out.append(f"  {lab:14s} joint {j:.4f}  edge {e:+.3f}  per year {y:+.3f}")
    be = breakeven_rho(probs, ask)
    out.append("BREAK-EVEN rho: " + ("none up to 1" if be is None else f"{be:g}"))
    out.append("HONESTY: win chance falls fast with legs; the edge depends on the correlation assumption, and the 0.10 bar is judged at the stated rho and at rho 0.")
    return "\n".join(out)
