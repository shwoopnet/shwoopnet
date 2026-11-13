"""SOCDERIV second build (History Miner, Nov 13, 2026): the sibling-implied model, from Desk B's registration text only (two independent Poisson goal rates fitted by least squares
to the mids of the three winner markets and every two-sided total-goals strike at the instant). Desk B's and the Testing Desk's code are not read. Pure Python, deterministic."""
import math

MAXG = 20          # goal counts summed to 20 a side (the tail beyond is below 1e-12 for rates under 6)


def pmf(lam):
    """Poisson probabilities 0..MAXG, built by the recurrence p(n) = p(n-1) x lam / n (no factorials)."""
    out = [math.exp(-lam)]
    for n in range(1, MAXG + 1):
        out.append(out[-1] * lam / n)
    return out


def pois(lam, n):
    return pmf(lam)[n] if n <= MAXG else math.exp(-lam) * lam ** n / math.factorial(n)


def cdf(lam, k):
    if k < 0:
        return 0.0
    return sum(pmf(lam)[: int(k) + 1]) if k <= MAXG else 1.0


def winner_probs(lh, la):
    ph, pa = pmf(lh), pmf(la)
    cum = 0.0
    home = 0.0
    draw = 0.0
    for j in range(MAXG + 1):           # home = sum over j of P(away = j) x P(home > j)
        cum += ph[j]
        draw += ph[j] * pa[j]
        home += pa[j] * (1.0 - cum)
    return home, draw, 1.0 - home - draw


def p_total_over(lh, la, line):
    """P(total goals > line) for a half-goal line (line = k + 0.5): 1 - P(total <= k)."""
    return 1.0 - cdf(lh + la, math.floor(line))


def p_btts(lh, la):
    return (1 - math.exp(-lh)) * (1 - math.exp(-la))


def p_team_over(lam, line):
    return 1.0 - cdf(lam, math.floor(line))


def sse(lh, la, winner_mids, total_mids):
    h, d, a = winner_probs(lh, la)
    e = (h - winner_mids[0]) ** 2 + (d - winner_mids[1]) ** 2 + (a - winner_mids[2]) ** 2
    for line, mid in total_mids:
        e += (p_total_over(lh, la, line) - mid) ** 2
    return e


def fit(winner_mids, total_mids):
    """Least squares over (home rate, away rate) in [0.01, 6]: a coarse grid (step 0.05) then coordinate refinement halving the step to 1e-7. Deterministic; ties keep the first point."""
    best = None
    lh = 0.05
    while lh <= 6.0 + 1e-12:
        la = 0.05
        while la <= 6.0 + 1e-12:
            v = sse(lh, la, winner_mids, total_mids)
            if best is None or v < best[0] - 1e-15:
                best = (v, lh, la)
            la = round(la + 0.05, 10)
        lh = round(lh + 0.05, 10)
    v, lh, la = best
    step = 0.05
    while step > 1e-7:
        improved = True
        while improved:
            improved = False
            for dh, da in ((step, 0), (-step, 0), (0, step), (0, -step)):
                nh, na = lh + dh, la + da
                if 0.01 <= nh <= 6 and 0.01 <= na <= 6:
                    nv = sse(nh, na, winner_mids, total_mids)
                    if nv < v - 1e-18:
                        v, lh, la, improved = nv, nh, na, True
        step /= 2
    return lh, la, v
