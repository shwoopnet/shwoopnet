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
    """Least squares over (home rate, away rate) in [0.01, 6]: a coarse grid (step 0.05), coordinate refinement halving the step to 1e-7, then the Nov 14 Gauss-Newton polish. Returns (home, away, sse, iters, cap_hit, on_bound). Deterministic; ties keep the first point."""
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


LO, HI = 0.01, 6.0


def derivs(lh, la, winner_mids, total_mids):
    """Exact first and second derivatives of the residuals in (home rate, away rate) (FIT_POLISH_NOTE_NOV14.md, option (a)).
    Returns r, J (list of (d/dh, d/da)), Hr (list of (d2/dh2, d2/da2, d2/dhda)), in the order of residuals()."""
    ph, pa = pmf(lh), pmf(la)
    g = lambda q, n: q[n] if 0 <= n <= MAXG else 0.0
    d1 = lambda q, n: g(q, n - 1) - g(q, n)
    d2 = lambda q, n: g(q, n - 2) - 2 * g(q, n - 1) + g(q, n)
    hh = ha_ = hd = 0.0
    H = [0.0] * 5        # home_h, home_a, home_hh, home_aa, home_ha
    D = [0.0] * 5        # draw_h, draw_a, draw_hh, draw_aa, draw_ha
    cum = 0.0
    for jj in range(MAXG + 1):
        cum += ph[jj]
        S = 1.0 - cum                                        # P(home > jj), as in winner_probs()
        H[0] += pa[jj] * ph[jj]; H[1] += d1(pa, jj) * S; H[2] += pa[jj] * (g(ph, jj - 1) - ph[jj]); H[3] += d2(pa, jj) * S; H[4] += d1(pa, jj) * ph[jj]
        D[0] += d1(ph, jj) * pa[jj]; D[1] += ph[jj] * d1(pa, jj); D[2] += d2(ph, jj) * pa[jj]; D[3] += ph[jj] * d2(pa, jj); D[4] += d1(ph, jj) * d1(pa, jj)
    A = [-(H[k] + D[k]) for k in range(5)]
    r = residuals(lh, la, winner_mids, total_mids)
    J = [(H[0], H[1]), (D[0], D[1]), (A[0], A[1])]
    Hr = [(H[2], H[3], H[4]), (D[2], D[3], D[4]), (A[2], A[3], A[4])]
    pt = pmf(lh + la)
    for line, _mid in total_mids:
        k = math.floor(line)
        if k > MAXG:
            J.append((0.0, 0.0)); Hr.append((0.0, 0.0, 0.0))
            continue
        f1 = g(pt, k); f2 = g(pt, k - 1) - g(pt, k)
        J.append((f1, f1)); Hr.append((f2, f2, f2))
    return r, J, Hr


LO, HI = 0.01, 6.0
GRAD_STOP = 1e-12


def polish(lh, la, v0, winner_mids, total_mids):
    """Option (a) (the owner's pick, the Head 2026-11-15 14:19Z): Newton on SSE with exact derivatives from the refinement point. Stops ONLY when |dSSE/drate| is under
    1e-12 on every free rate, or after POLISH_CAP steps (cap_hit). A rate that the full step would put outside the box moves alone to its bound and is held; the other
    rate is then stepped alone. Returns (home, away, sse, iters, cap_hit, on_bound); used only if its SSE is not above the refinement's + 1e-15."""
    x, y, v = lh, la, v0
    held = [x in (LO, HI), y in (LO, HI)]
    it = 0
    inbox = lambda a: LO <= a <= HI
    clip = lambda a: min(HI, max(LO, a))
    while True:
        if held[0] and held[1]:
            break
        r, J, Hr = derivs(x, y, winner_mids, total_mids)
        G = [2 * sum(q * jv[k] for q, jv in zip(r, J)) for k in (0, 1)]
        if all(held[k] or abs(G[k]) < GRAD_STOP for k in (0, 1)):
            break
        if it >= POLISH_CAP:
            break
        it += 1
        jtj = [[sum(jv[a] * jv[b] for jv in J) for b in (0, 1)] for a in (0, 1)]
        rh = [sum(q * hv[k] for q, hv in zip(r, Hr)) for k in (0, 1, 2)]     # sum r_i x d2r_i: hh, aa, ha
        Hs = [[2 * (jtj[0][0] + rh[0]), 2 * (jtj[0][1] + rh[2])], [2 * (jtj[1][0] + rh[2]), 2 * (jtj[1][1] + rh[1])]]
        if not held[0] and not held[1]:
            det = Hs[0][0] * Hs[1][1] - Hs[0][1] * Hs[1][0]
            M_ = Hs if (det > 0 and Hs[0][0] > 0 and Hs[1][1] > 0) else [[2 * jtj[0][0], 2 * jtj[0][1]], [2 * jtj[1][0], 2 * jtj[1][1]]]
            det = M_[0][0] * M_[1][1] - M_[0][1] * M_[1][0]
            if det <= 0:
                POLISH_FLAGS["singular"] += 1
                continue
            dx = -(M_[1][1] * G[0] - M_[0][1] * G[1]) / det; dy = -(M_[0][0] * G[1] - M_[1][0] * G[0]) / det
        else:
            k = 1 if held[0] else 0
            c = Hs[k][k] if Hs[k][k] > 0 else 2 * jtj[k][k]
            if c <= 0:
                POLISH_FLAGS["singular"] += 1
                continue
            d = -G[k] / c
            dx, dy = (0.0, d) if held[0] else (d, 0.0)
        moved = False
        if not (inbox(x + dx) and inbox(y + dy)):                   # the full step leaves the box: only the leaving rate moves, to its bound
            cx = clip(x + dx) if not inbox(x + dx) else x
            cy = clip(y + dy) if not inbox(y + dy) else y
            cv = sse(cx, cy, winner_mids, total_mids)
            if cv <= v + 1e-15 * (1 + v):
                x, y, v, moved = cx, cy, cv, True
                held = [held[0] or cx in (LO, HI), held[1] or cy in (LO, HI)]
        if not moved:
            for _h in range(41):
                nx, ny = x + dx, y + dy
                if inbox(nx) and inbox(ny):
                    nv = sse(nx, ny, winner_mids, total_mids)
                    if nv <= v + 1e-15 * (1 + v):
                        x, y, v = nx, ny, nv
                        break
                dx /= 2; dy /= 2
    cap_hit = it >= POLISH_CAP and not (all(held[k] or abs(G[k]) < GRAD_STOP for k in (0, 1)) if not (held[0] and held[1]) else True)
    if v > v0 + 1e-15:
        POLISH_FLAGS["rejected"] += 1
        return lh, la, v0, it, cap_hit, lh in (LO, HI) or la in (LO, HI)
    return x, y, v, it, cap_hit, held[0] or held[1]
