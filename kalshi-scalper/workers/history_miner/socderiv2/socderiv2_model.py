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


def polish(lh, la, v0, winner_mids, total_mids):
    """Gauss-Newton on the residuals from the refinement point (FIT_POLISH_NOTE_NOV14.md, final spec of the Head's 07:10Z): central-difference Jacobian (h 1e-6).
    A rate that lands on a bound (by a clipped full step) is held there and the other rate is polished alone. Stops: |step| under 1e-13 before a move, SSE
    falling by less than 1e-13 relative after a move, or POLISH_CAP passes (2-D and 1-D passes share the cap). Returns (home, away, sse, iters, cap_hit, on_bound);
    used only if its SSE is not above the refinement's + 1e-15."""
    H = 1e-6
    x, y, v = lh, la, v0
    held = [x in (LO, HI), y in (LO, HI)]
    it, stopped = 0, False
    inbox = lambda a: LO <= a <= HI
    clip = lambda a: min(HI, max(LO, a))
    while it < POLISH_CAP:
        if held[0] and held[1]:
            stopped = True
            break
        it += 1
        r = residuals(x, y, winner_mids, total_mids)
        jx = jy = None
        if not held[0]:
            rp, rm = residuals(x + H, y, winner_mids, total_mids), residuals(x - H, y, winner_mids, total_mids)
            jx = [(p_ - m) / (2 * H) for p_, m in zip(rp, rm)]
        if not held[1]:
            rp, rm = residuals(x, y + H, winner_mids, total_mids), residuals(x, y - H, winner_mids, total_mids)
            jy = [(p_ - m) / (2 * H) for p_, m in zip(rp, rm)]
        if jx is not None and jy is not None:
            a11 = sum(t * t for t in jx); a12 = sum(t * u for t, u in zip(jx, jy)); a22 = sum(u * u for u in jy)
            g1 = sum(t * q for t, q in zip(jx, r)); g2 = sum(u * q for u, q in zip(jy, r))
            det = a11 * a22 - a12 * a12
            if det <= 1e-14 * (a11 + a22) ** 2:
                POLISH_FLAGS["singular"] += 1
                return lh, la, v0, it, False, lh in (LO, HI) or la in (LO, HI)
            dx = -(a22 * g1 - a12 * g2) / det; dy = -(a11 * g2 - a12 * g1) / det
        else:
            jj = jx if jx is not None else jy
            K = 1e-4                                                 # 1-D Newton: J'J plus the residuals' second-derivative term (FIT_POLISH_NOTE, B3 correction)
            if jx is not None:
                rp2, rm2 = residuals(x + K, y, winner_mids, total_mids), residuals(x - K, y, winner_mids, total_mids)
            else:
                rp2, rm2 = residuals(x, y + K, winner_mids, total_mids), residuals(x, y - K, winner_mids, total_mids)
            r2 = [(p_ - 2 * q + m) / (K * K) for p_, q, m in zip(rp2, r, rm2)]
            a = sum(t * t for t in jj) + sum(q * s2 for q, s2 in zip(r, r2)); g = sum(t * q for t, q in zip(jj, r))
            if a <= 0:
                stopped = True
                break
            d = -g / a
            dx, dy = (d, 0.0) if jx is not None else (0.0, d)
        if abs(dx) < 1e-13 and abs(dy) < 1e-13:
            stopped = True
            break
        moved, newheld = False, list(held)
        if not (inbox(x + dx) and inbox(y + dy)):                   # the full step leaves the box: try it clipped (a rate lands on its bound)
            cx = clip(x + dx) if not inbox(x + dx) else x            # only the rate that leaves the box moves, to its bound; the other stays this pass
            cy = clip(y + dy) if not inbox(y + dy) else y
            cv = sse(cx, cy, winner_mids, total_mids)
            if cv <= v + 1e-15 * (1 + v):
                nx, ny, nv, moved = cx, cy, cv, True
                newheld = [held[0] or cx in (LO, HI), held[1] or cy in (LO, HI)]
        if not moved:
            for _h in range(41):
                nx, ny = x + dx, y + dy
                if inbox(nx) and inbox(ny):
                    nv = sse(nx, ny, winner_mids, total_mids)
                    if nv <= v + 1e-15 * (1 + v):
                        moved = True
                        break
                dx /= 2; dy /= 2
        if not moved:
            stopped = True
            break
        small = (v - nv) < 1e-13 * v
        landed = newheld != held                                   # a rate landed on a bound on this pass: go on to polish the other alone
        x, y, v, held = nx, ny, nv, newheld
        if small and not landed:
            stopped = True
            break
    cap_hit = not stopped
    if v > v0 + 1e-15:
        POLISH_FLAGS["rejected"] += 1
        return lh, la, v0, it, cap_hit, lh in (LO, HI) or la in (LO, HI)
    return x, y, v, it, cap_hit, held[0] or held[1]
