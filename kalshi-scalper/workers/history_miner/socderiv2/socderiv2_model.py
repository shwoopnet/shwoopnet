"""SOCDERIV second build (History Miner, Nov 13, 2026): the sibling-implied model, from Desk B's registration text only (two independent Poisson goal rates fitted by least squares
to the mids of the three winner markets and every two-sided total-goals strike at the instant). Desk B's and the Testing Desk's code are not read. Pure Python, deterministic."""
import math

MAXG = 40          # goal counts summed to 40 a side (Head's ruling 02:59Z, Nov 14): the tail beyond is under 1e-15 for rates in the box [0.01, 6]
POLISH_CAP = 200   # Head's ruling 02:59Z: at most 200 Gauss-Newton iterations


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
    """Least squares over (home rate, away rate) in [0.01, 6]: a coarse grid (step 0.05), coordinate refinement halving the step to 1e-7, then the Nov 14 Gauss-Newton polish. Returns (home, away, sse, iters, cap_hit). Deterministic; ties keep the first point."""
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
    return polish(lh, la, v, winner_mids, total_mids)


POLISH_FLAGS = {"singular": 0, "rejected": 0}     # counted, never silent (FIT_POLISH_NOTE_NOV14.md)


def residuals(lh, la, winner_mids, total_mids):
    h, d, a = winner_probs(lh, la)
    return [h - winner_mids[0], d - winner_mids[1], a - winner_mids[2]] + [p_total_over(lh, la, line) - mid for line, mid in total_mids]


def polish(lh, la, v0, winner_mids, total_mids):
    """Gauss-Newton on the residuals from the refinement point (FIT_POLISH_NOTE_NOV14.md, amended for the Head's 02:59Z rulings): central-difference Jacobian (h 1e-6),
    stop before moving if both step parts are under 1e-13, stop after a move that lowered SSE by under 1e-13 relative, at most POLISH_CAP passes.
    Returns (home, away, sse, iters, cap_hit); used only if its SSE is not above the refinement's + 1e-15."""
    H = 1e-6
    x, y, v = lh, la, v0
    it, stopped = 0, False
    while it < POLISH_CAP:
        it += 1
        r = residuals(x, y, winner_mids, total_mids)
        rxp = residuals(x + H, y, winner_mids, total_mids); rxm = residuals(x - H, y, winner_mids, total_mids)
        ryp = residuals(x, y + H, winner_mids, total_mids); rym = residuals(x, y - H, winner_mids, total_mids)
        jx = [(p - m) / (2 * H) for p, m in zip(rxp, rxm)]; jy = [(p - m) / (2 * H) for p, m in zip(ryp, rym)]
        a11 = sum(t * t for t in jx); a12 = sum(t * u for t, u in zip(jx, jy)); a22 = sum(u * u for u in jy)
        g1 = sum(t * q for t, q in zip(jx, r)); g2 = sum(u * q for u, q in zip(jy, r))
        det = a11 * a22 - a12 * a12
        if det <= 1e-14 * (a11 + a22) ** 2:
            POLISH_FLAGS["singular"] += 1
            return lh, la, v0, it, False
        dx = -(a22 * g1 - a12 * g2) / det; dy = -(a11 * g2 - a12 * g1) / det
        if abs(dx) < 1e-13 and abs(dy) < 1e-13:
            stopped = True
            break
        moved = False
        for _h in range(41):
            nx, ny = x + dx, y + dy
            if 0.01 <= nx <= 6 and 0.01 <= ny <= 6:
                nv = sse(nx, ny, winner_mids, total_mids)
                if nv <= v + 1e-15 * (1 + v):
                    moved = True
                    break
            dx /= 2; dy /= 2
        if not moved:
            stopped = True
            break
        small = (v - nv) < 1e-13 * v
        x, y, v = nx, ny, nv
        if small:
            stopped = True
            break
    cap_hit = not stopped
    if v > v0 + 1e-15:
        POLISH_FLAGS["rejected"] += 1
        return lh, la, v0, it, cap_hit
    return x, y, v, it, cap_hit
