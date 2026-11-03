"""LADDERARB1: kink / arb consistency inside one strike ladder, cheap side only (ask 3c-30c).

Only the trigger detection and an OUTCOME-FREE census live here (no result column is read).
The scorer is deliberately not written: the census below fails the 150-trade floor.
Usage: python3 -I -m scalper.ladderarb1 census   (read-only, local caches)
"""
import math, os, sqlite3, sys

LO, HI = 0.03, 0.30          # cheap-side ask band (fixed)
KINK_RATIO = 3.0             # ask at least 3x below the log-linear neighbour interpolation (fixed)
MIN_STRIKES = 5              # strikes quoted at the look (fixed)
MAX_PER_EVENT = 2            # fixed
FROZEN_TS = 1791043200       # 2026-10-03T16:00Z, never joined


def sides(q):
    """q: {strike: (bid, ask)} YES quotes. Returns {strike: {'Y': yes_ask, 'N': no_ask}} (no_ask = 1 - yes bid)."""
    out = {}
    for k, (b, a) in q.items():
        if a is None or b is None or not (0 < a < 1) or not (0 <= b < 1):
            continue
        out[k] = {"Y": a, "N": 1.0 - b}
    return out


def kink_triggers(q):
    """Cheap-side kink: ask in band and ask * KINK_RATIO <= log-linear interpolation of the two neighbouring strikes' asks (same side)."""
    s = sides(q)
    ks = sorted(s)
    res = []
    for i in range(1, len(ks) - 1):
        k0, k, k1 = ks[i - 1], ks[i], ks[i + 1]
        for side in ("Y", "N"):
            a, a0, a1 = s[k][side], s[k0][side], s[k1][side]
            if not (LO <= a <= HI) or a0 <= 0 or a1 <= 0:
                continue
            w = (k - k0) / (k1 - k0)
            hat = math.exp((1 - w) * math.log(a0) + w * math.log(a1))
            if a * KINK_RATIO <= hat:
                res.append((k, side, a, hat))
    return res


def arb_triggers(q):
    """Arb-inconsistent pair K1<K2: YES ask(K1) <= YES bid(K2). Buy whichever leg is in the cheap band."""
    ks = sorted(q)
    res = []
    for i, k1 in enumerate(ks):
        for k2 in ks[i + 1:]:
            b1, a1 = q[k1]; b2, a2 = q[k2]
            if a1 is None or b2 is None or not (0 < a1 < 1) or b2 <= 0:
                continue
            if a1 <= b2:
                if LO <= a1 <= HI:
                    res.append((k1, "Y", a1, b2))
                if b2 is not None and LO <= 1 - b2 <= HI:
                    res.append((k2, "N", 1 - b2, a1))
    return res


def select(q):
    """Up to MAX_PER_EVENT triggers, the larger kink gap first; ladder needs MIN_STRIKES quoted strikes."""
    if len(sides(q)) < MIN_STRIKES:
        return []
    t = [(h / a, k, s, a) for k, s, a, h in kink_triggers(q)] + [(1e9, k, s, a) for k, s, a, _ in arb_triggers(q)]
    t.sort(reverse=True)
    seen, out = set(), []
    for g, k, s, a in t:
        if (k, s) in seen:
            continue
        seen.add((k, s)); out.append((k, s, a))
        if len(out) == MAX_PER_EVENT:
            break
    return out


def census(db, series, looks=(3600, 1200), tol=600, root=None):
    root = root or os.path.join(os.path.dirname(__file__), "..", "..", "data")
    c = sqlite3.connect(f"file:{os.path.abspath(os.path.join(root, db))}?mode=ro", uri=True)
    ev = {}
    for look in looks:
        rows = c.execute(
            """select m.close_ts, m.strike, k.bid_c, k.ask_c from market m join candle k on k.ticker=m.ticker
               where m.series=? and m.close_ts<? and k.end_ts<=m.close_ts-? and k.end_ts>m.close_ts-?-?
               order by k.end_ts""", (series, FROZEN_TS, look, look, tol)).fetchall()
        d = {}
        for ct, strike, b, a in rows:
            d.setdefault(ct, {})[strike] = (b, a)   # latest candle in the window wins
        n_ev = sum(1 for q in d.values() if len(sides(q)) >= MIN_STRIKES)
        n_tr = sum(len(select(q)) for q in d.values())
        ev[look] = (n_ev, n_tr)
    return ev


if __name__ == "__main__":
    for db, s in [("inx1.sqlite", "KXINXU"), ("inx1.sqlite", "KXNASDAQ100U"), ("xladder1.sqlite", "KXINX"),
                  ("conf2_lad.sqlite", "KXBTCD"), ("lad2.sqlite", "KXBTCD")]:
        print(db, s, census(db, s))
