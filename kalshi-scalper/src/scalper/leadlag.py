"""Does Kalshi's Bitcoin price lag the spot price? (exploratory; definitions in the README)

For every usable market minute, regress the change in Kalshi's mid over the NEXT minute on
Bitcoin's log return in that same next minute (contemporaneous), in the minute before
(one minute of lag, the coefficient that matters), two before, and one after (a lead,
a clock check). If Kalshi absorbed spot within the minute the lag coefficient is zero.

Exploratory: no verdict, no kill criterion, nothing here licenses a trade. The only
output that points at action is whether the README's bar for "worth a formal hypothesis"
was cleared, and the answer is printed as that and nothing stronger.

Usage: python -m scalper.leadlag
"""
from __future__ import annotations

import math
import sqlite3
from collections import defaultdict

from .paths import DB

SERIES = "KXBTC15M"
MID_LO, MID_HI = 0.30, 0.70
MIN_LEFT_S = 300
MAX_SPREAD = 0.10
COST = 0.04          # round trip, in dollars per contract, from the earlier verdicts
LAG_SHARE_BAR = 0.15
Z_BAR = 3.0
ALIGN_TOL = 0.001    # median |strike / spot at open - 1|

NAMES = ("const", "r(t+1)", "r(t)", "r(t-1)", "r(t+2)")


def usable(bid, ask) -> bool:
    return (bid is not None and ask is not None and bid >= 0.001 and ask <= 0.999
            and ask >= bid and ask - bid <= MAX_SPREAD)


def solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting; the systems here are 5 x 5."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[p][c]) < 1e-18:
            raise ValueError("singular")
        m[c], m[p] = m[p], m[c]
        for r in range(c + 1, n):
            f = m[r][c] / m[c][c]
            for k in range(c, n + 1):
                m[r][k] -= f * m[c][k]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (m[r][n] - sum(m[r][k] * x[k] for k in range(r + 1, n))) / m[r][r]
    return x


def inverse(a: list[list[float]]) -> list[list[float]]:
    n = len(a)
    cols = [solve(a, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)]
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def ols_clustered(rows: list[tuple[str, list[float], float]]) -> tuple[list[float], list[float]]:
    """rows: (cluster, x, y). Returns (coefficients, standard errors), SEs clustered by
    day (adjacent markets share a regime, so rows are not independent)."""
    k = len(rows[0][1])
    xtx = [[0.0] * k for _ in range(k)]
    xty = [0.0] * k
    for _, x, y in rows:
        for i in range(k):
            xty[i] += x[i] * y
            for j in range(k):
                xtx[i][j] += x[i] * x[j]
    beta = solve(xtx, xty)
    score: dict[str, list[float]] = defaultdict(lambda: [0.0] * k)
    for g, x, y in rows:
        e = y - sum(b * v for b, v in zip(beta, x))
        for i in range(k):
            score[g][i] += x[i] * e
    meat = [[0.0] * k for _ in range(k)]
    for s in score.values():
        for i in range(k):
            for j in range(k):
                meat[i][j] += s[i] * s[j]
    inv = inverse(xtx)
    g = len(score)
    corr = g / (g - 1) if g > 1 else 1.0
    se = []
    for i in range(k):
        v = sum(inv[i][a] * meat[a][b] * inv[b][i] for a in range(k) for b in range(k)) * corr
        se.append(math.sqrt(max(v, 0.0)))
    return beta, se


def build_rows(markets: dict, spot: dict) -> tuple[list[tuple], int]:
    """markets: ticker -> (open_ts, close_ts, [(end_ts, bid, ask), ...]); spot: start_ts -> close.
    Returns rows (day, close_ts, [1, r(t+1), r(t), r(t-1), r(t+2)], dmid, r(t)) and the
    number dropped for a missing spot minute."""
    def price(end):  # close of the candle that CLOSES at `end`
        return spot.get(end - 60)

    def ret(end):
        a, b = price(end - 60), price(end)
        return math.log(b / a) if a and b else None

    rows, dropped = [], 0
    for _, (_, close_ts, cs) in markets.items():
        by = {c[0]: c for c in cs}
        for end, bid, ask in cs:
            nxt = by.get(end + 60)
            if nxt is None or not (usable(bid, ask) and usable(nxt[1], nxt[2])):
                continue
            mid, mid2 = (bid + ask) / 2, (nxt[1] + nxt[2]) / 2
            if not (MID_LO <= mid <= MID_HI) or close_ts - end < MIN_LEFT_S:
                continue
            rs = [ret(end + 60), ret(end), ret(end - 60), ret(end + 120)]
            if any(r is None for r in rs):
                dropped += 1
                continue
            day = str(end // 86400)
            rows.append((day, close_ts, [1.0] + rs, mid2 - mid, rs[1]))
    return rows, dropped


def fit(rows: list[tuple]) -> tuple[list[float], list[float]]:
    return ols_clustered([(r[0], r[2], r[3]) for r in rows])


def alignment(db) -> tuple[float | None, int]:
    """Median |strike / spot at the market's open - 1| over Bitcoin markets."""
    gaps = []
    for open_ts, strike in db.execute("SELECT open_ts, strike FROM market WHERE series=? AND strike IS NOT NULL", (SERIES,)):
        row = db.execute("SELECT c FROM spot WHERE ts = ?", ((open_ts // 60) * 60 - 60,)).fetchone()
        if row and row[0] and strike:
            gaps.append(abs(strike / row[0] - 1))
    if not gaps:
        return None, 0
    gaps.sort()
    return gaps[len(gaps) // 2], len(gaps)


def load(db) -> tuple[dict, dict]:
    markets: dict = {}
    for t, o, c in db.execute("SELECT ticker, open_ts, close_ts FROM market WHERE series=?", (SERIES,)):
        markets[t] = (o, c, [])
    for t, end, b, a in db.execute("SELECT ticker, end_ts, bid_c, ask_c FROM candle WHERE series=? ORDER BY ticker, end_ts", (SERIES,)):
        if t in markets:
            markets[t][2].append((end, b, a))
    spot = dict(db.execute("SELECT ts, c FROM spot"))
    return markets, spot


def report(rows: list[tuple]) -> dict:
    beta, se = fit(rows)
    z = [b / s if s else 0.0 for b, s in zip(beta, se)]
    mid_t = sorted(r[1] for r in rows)[len(rows) // 2]
    halves = [fit([r for r in rows if r[1] < mid_t]), fit([r for r in rows if r[1] >= mid_t])]
    return {"beta": beta, "se": se, "z": z, "halves": halves, "n": len(rows)}


def decile_move(rows: list[tuple]) -> tuple[float, int]:
    """Mean next minute move in the direction of the last minute's spot move, for the top
    decile of |spot move|, in dollars per contract."""
    ranked = sorted(rows, key=lambda r: abs(r[4]), reverse=True)
    top = ranked[: max(1, len(ranked) // 10)]
    return sum((1 if r[4] > 0 else -1) * r[3] for r in top) / len(top), len(top)


def verdict(rep: dict, top_move: float) -> tuple[bool, list[str]]:
    """Whether the README's bar for a formal hypothesis was cleared, with the reasons."""
    why = []
    b0, b1 = rep["beta"][1], rep["beta"][2]
    if b0 <= 0:
        return False, ["the contemporaneous coefficient is not positive: Kalshi does not track spot here, so the clocks or the data are wrong"]
    share = b1 / b0
    ok = True
    if share < LAG_SHARE_BAR:
        ok = False
        why.append(f"lag is {share:.1%} of the contemporaneous effect, under the {LAG_SHARE_BAR:.0%} bar")
    for i, (hb, hs) in enumerate(rep["halves"]):
        z = hb[2] / hs[2] if hs[2] else 0.0
        if z < Z_BAR:
            ok = False
            why.append(f"half {i + 1}: lag z is {z:.1f}, under {Z_BAR}")
    if top_move <= COST:
        ok = False
        why.append(f"after a top-decile spot move Kalshi moves {top_move * 100:.2f}c, not more than the {COST * 100:.0f}c cost")
    return ok, why


def main() -> None:
    db = sqlite3.connect(DB)
    have = db.execute("SELECT name FROM sqlite_master WHERE name='spot'").fetchone()
    if not have:
        print("No spot data. Run: python -m scalper.spot")
        return
    gap, n = alignment(db)
    print(f"Clock check: median |strike / Coinbase at open - 1| = {gap:.4%} over {n} markets (needs under {ALIGN_TOL:.1%})")
    if gap is None or gap > ALIGN_TOL:
        print("The clocks do not line up. Nothing below is read.")
        return
    markets, spot = load(db)
    rows, dropped = build_rows(markets, spot)
    print(f"{len(rows):,} market minutes used, {dropped:,} dropped for a missing spot minute\n")
    rep = report(rows)
    print(f"{'term':8} {'coef':>12} {'z':>7}   half 1 z   half 2 z")
    for i, name in enumerate(NAMES):
        h = [hb[i] / hs[i] if hs[i] else 0.0 for hb, hs in rep["halves"]]
        print(f"{name:8} {rep['beta'][i]:>12.4f} {rep['z'][i]:>7.1f}   {h[0]:>8.1f}   {h[1]:>8.1f}")
    print("\nr(t+1) is the same minute as the Kalshi move; r(t) is one minute earlier (the lag);")
    print("r(t+2) is a minute AFTER, a clock check: it should be about zero.")
    top, k = decile_move(rows)
    print(f"\nAfter a top-decile spot move (n={k:,}), Kalshi's next-minute move in that direction: {top * 100:+.2f}c "
          f"(round trip cost {COST * 100:.0f}c)")
    ok, why = verdict(rep, top)
    print("\nWorth a formal hypothesis?" + (" YES, by the README's bar." if ok else " No."))
    for w in why:
        print("  " + w)
    if not ok:
        print("  No lag visible at one minute. Information strategies need sub-minute data and are out of reach for this bot.")


if __name__ == "__main__":
    main()
