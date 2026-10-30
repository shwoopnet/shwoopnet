"""NEWH12: cross-asset lead and lag among Kalshi's 15 minute crypto books in the same window (research only).

Registration: workers/NEWH12_REGISTRATION.md (pushed before any scoring).

    PYTHONPATH=src python -m scalper.newh12 counts    (paired windows and trigger counts per stage from SIGNAL quotes only;
                                                       no fill quote, no quote after the signal, no result)
    PYTHONPATH=src python -m scalper.newh12 dv        (discovery and validation, scored once)
    PYTHONPATH=src python -m scalper.newh12 holdout NAME...   (frozen holdout, read once, only for rules that passed dv)

Tries (4): XLAG-ETH (Bitcoin leads, Ethereum lags), XLAG-DOGE (Bitcoin leads, Dogecoin lags), XLAG2-DOGE (Bitcoin and
Ethereum both lead, Dogecoin lags), XLAG-BTC (Ethereum leads, Bitcoin lags; the control for the lag story).
Information looks (2, counted): I1 same-window outcome agreement between the three coins; I2 does the lagging book catch up
in the minutes after a trigger (quotes only).

Every entry is filled at the NEXT candle's ask of the lagging book, at least 420 s before the close, band 20c to 80c, held to
settlement. No 88c to 97c favourite, no side above 50c bought in the last 6 minutes, no price-band choice of a cheap side: the
side is chosen by the other market's move.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict

from . import newh8
from .newh9 import START, DISC_END, VAL_END, END, stage, day, net, pf, dayz, summ, fmt, zbar

BTC, ETH, DOGE = "KXBTC15M", "KXETH15M", "KXDOGE15M"
FILES = {BTC: ("l1b", "book", "fresh"), ETH: ("l1b", "book", "fresh"), DOGE: ("e3b", "alts2", "fresh")}

N_RUNNING_BEFORE = 678_923            # ledger after GEN9
N_THIS = 6                            # 4 tries + 2 information looks (registered)

SIGNALS = (-720, -660, -600, -540, -480)   # signal candle end, seconds before the close (minutes 3 to 7 of the window)
LOOK = 120                                 # the move is the YES mid now minus the YES mid two candles earlier
LEAD1 = 0.15                               # one leader: at least 15c in 2 minutes
LEAD2 = 0.10                               # two leaders: each at least 10c, the same sign
FLAT = 0.05                                # the lagging book moved at most 5c over the same 2 minutes
MAX_SPREAD = 0.10                          # every mid read needs a spread of at most 10c (a cost filter, seen before the trade)
BAND = (0.20, 0.80)                        # fill band on the lagging book's side

RULES = {
    "XLAG-ETH": {"leaders": (BTC,), "lagger": ETH, "th": LEAD1},
    "XLAG-DOGE": {"leaders": (BTC,), "lagger": DOGE, "th": LEAD1},
    "XLAG2-DOGE": {"leaders": (BTC, ETH), "lagger": DOGE, "th": LEAD2},
    "XLAG-BTC": {"leaders": (ETH,), "lagger": BTC, "th": LEAD1},
}


def load(series):
    newh8.FILES[series] = FILES[series]
    return newh8.load(series, START, END)


def mid(q):
    """YES mid of a candle quote, or None when the book is unreadable (missing, inverted, empty or wider than MAX_SPREAD)."""
    if q is None:
        return None
    b, a = q[0], q[1]
    if b is None or a is None or not (0 <= b <= a <= 1) or a <= 0 or b >= 1 or a - b > MAX_SPREAD + 1e-9:
        return None
    return (a + b) / 2


def move(c, s):
    m1, m0 = mid(c.get(s)), mid(c.get(s - LOOK))
    if m1 is None or m0 is None:
        return None
    return m1 - m0


def signals(W, rule):
    """For every paired window, the FIRST signal candle that triggers, decided from quotes at and before the signal only.
    Returns {close: (s, side)} and a funnel of what happened to the rest."""
    leaders, lagger, th = rule["leaders"], rule["lagger"], rule["th"]
    out, fun = {}, Counter()
    for close in sorted(W[lagger]):
        if any(close not in W[x] for x in leaders):
            fun["unpaired"] += 1
            continue
        fun["paired"] += 1
        hit = None
        for s in SIGNALS:
            dl = [move(W[x][close]["c"], s) for x in leaders]
            dg = move(W[lagger][close]["c"], s)
            if any(d is None for d in dl) or dg is None:
                fun["candle unreadable"] += 1
                continue
            fun["candles read"] += 1
            if not all(abs(d) >= th - 1e-9 for d in dl):
                continue
            if len(set(d > 0 for d in dl)) != 1:
                fun["leaders disagree"] += 1
                continue
            if abs(dg) > FLAT + 1e-9:
                fun["lagger moved too"] += 1
                continue
            hit = (s, "yes" if dl[0] > 0 else "no", dl, dg)
            break
        if hit is None:
            fun["no trigger"] += 1
        else:
            out[close] = hit
            fun["trigger"] += 1
    return out, fun


def trades(W, rule, sig):
    """Fill at the lagging book's side ask on the candle after the signal, inside BAND, held to settlement."""
    lagger = rule["lagger"]
    tr, fun = [], Counter()
    for close, (s, side, dl, dg) in sorted(sig.items()):
        w = W[lagger][close]
        c = w["c"]
        f = c.get(s + 60)
        a = newh8.side_ask(f, side) if f is not None else None
        if a is None:
            fun["no fill"] += 1
            continue
        if not (BAND[0] - 1e-9 <= a <= BAND[1] + 1e-9):
            fun["band"] += 1
            continue
        sq = c.get(s)
        tr.append({"close": close, "stage": stage(close), "legs": [a], "payoff": 1 if w["result"] == side else 0,
                   "zv": (sq[2] <= 0) or (f[2] <= 0), "side": side, "s": s, "dl": dl[0], "dg": dg,
                   "sig_ask": newh8.side_ask(sq, side)})
        fun["trade"] += 1
    return tr, fun


def catchup(W, rule, sig, stages):
    """I2 (quotes only, no result): the lagging book's side mid change from the signal candle to +60 s and +180 s,
    signed in the leader's direction, and the leader's own further move over the same minutes."""
    lagger, leaders = rule["lagger"], rule["leaders"]
    acc = defaultdict(list)
    for close, (s, side, dl, dg) in sig.items():
        if stage(close) not in stages:
            continue
        sgn = 1 if side == "yes" else -1
        c = W[lagger][close]["c"]
        cl = W[leaders[0]][close]["c"]
        m0, ml0 = mid(c.get(s)), mid(cl.get(s))
        for dt in (60, 180):
            m1, ml1 = mid(c.get(s + dt)), mid(cl.get(s + dt))
            if m0 is not None and m1 is not None:
                acc[("lagger", dt)].append(sgn * (m1 - m0))
            if ml0 is not None and ml1 is not None:
                acc[("leader", dt)].append(sgn * (ml1 - ml0))
    return {k: (len(v), sum(v) / len(v) if v else float("nan")) for k, v in acc.items()}


def agreement(W, stages):
    """I1: share of paired windows where both coins settled the same way (the same side won), per pair."""
    out = {}
    for a, b in ((BTC, ETH), (BTC, DOGE), (ETH, DOGE)):
        n = same = 0
        for close, w in W[a].items():
            v = W[b].get(close)
            if v is None or stage(close) not in stages:
                continue
            n += 1
            same += w["result"] == v["result"]
        out[(a, b)] = (n, same / n if n else float("nan"))
    return out


def load_all():
    return {x: load(x) for x in (BTC, ETH, DOGE)}


def cmd_counts():
    W = load_all()
    for x, w in W.items():
        st = Counter(stage(c) for c in w)
        print(f"{x}: {len(w)} settled windows (disc {st['disc']}, val {st['val']}, hold {st['hold']})")
    for name, rule in RULES.items():
        sig, fun = signals(W, rule)
        st = Counter(stage(c) for c in sig)
        print(f"\n{name}: leaders {rule['leaders']} lagger {rule['lagger']} threshold {rule['th']}")
        print("  funnel:", dict(fun))
        print(f"  first-trigger windows: disc {st['disc']}, val {st['val']}, hold {st['hold']}")
        print("  by signal candle:", dict(Counter(v[0] for v in sig.values())))
    print(f"\nN running before {N_RUNNING_BEFORE:,}; this round {N_THIS}; after about {N_RUNNING_BEFORE + N_THIS:,}; "
          f"one-sided z bar {zbar(N_RUNNING_BEFORE + N_THIS):.2f}")


def verdict(d, v):
    if d["n"] < 100:
        return "NOT_ENOUGH_DATA (discovery under 100)"
    if d["pf10"] < 1.5 or d["netx"] <= 0:
        return "FALSIFIED (discovery)"
    if v["n"] < 50:
        return "NOT_ENOUGH_DATA (validation under 50)"
    if v["pf10"] < 1.5 or v["netx"] <= 0:
        return "FALSIFIED (validation)"
    return "PASSED dv: read the holdout once"


def cmd_dv():
    W = load_all()
    print(f"windows: " + ", ".join(f"{x} {len(w)}" for x, w in W.items()))
    for name, rule in RULES.items():
        sig, fun = signals(W, rule)
        tr, tfun = trades(W, rule, sig)
        d = summ([t for t in tr if t["stage"] == "disc"])
        v = summ([t for t in tr if t["stage"] == "val"])
        print(f"\n== {name}: leaders {rule['leaders']} lagger {rule['lagger']} threshold {rule['th']}")
        print("  signal funnel:", dict(fun))
        print("  fill funnel (all stages):", dict(tfun))
        print("  discovery  :", fmt(d))
        print("  validation :", fmt(v))
        for lab, st in (("disc", "disc"), ("val", "val")):
            tt = [t for t in tr if t["stage"] == st]
            if tt:
                ys = sum(t["side"] == "yes" for t in tt) / len(tt)
                sa = [t["sig_ask"] for t in tt if t["sig_ask"] is not None]
                print(f"  {lab}: yes share {ys:.2f}; mean signal ask {sum(sa) / len(sa):.3f} vs fill {sum(t['legs'][0] for t in tt) / len(tt):.3f}; "
                      f"by candle {dict(Counter(t['s'] for t in tt))}")
        print("  I2 catch-up (disc+val, signed in the leader's direction; n, mean mid change):",
              {f"{k[0]} +{k[1]}s": (n, round(m, 4)) for k, (n, m) in sorted(catchup(W, rule, sig, ("disc", "val")).items())})
        print("  verdict:", verdict(d, v))
    print("\nI1 same-window outcome agreement (n paired windows, share settled the same way):")
    for st in (("disc",), ("val",)):
        print(f"  {st[0]}:", {f"{a}/{b}": (n, round(s, 3)) for (a, b), (n, s) in agreement(W, st).items()})
    print(f"\nN running before {N_RUNNING_BEFORE:,}; this round {N_THIS}; after about {N_RUNNING_BEFORE + N_THIS:,}; "
          f"one-sided z bar {zbar(N_RUNNING_BEFORE + N_THIS):.2f}")


def cmd_holdout(names):
    W = load_all()
    for name in names:
        rule = RULES[name]
        sig, _ = signals(W, rule)
        tr, _ = trades(W, rule, sig)
        h = summ([t for t in tr if t["stage"] == "hold"])
        print(f"== {name} HOLDOUT (Oct 18 to Oct 30, read once):", fmt(h))
        if h["n"] < 30:
            print("  NOT_ENOUGH_DATA (holdout under 30)")
        elif h["pf10"] < 1.5 or h["netx"] <= 0:
            print("  FALSIFIED (holdout)")
        else:
            allz = dayz(tr)
            print(f"  pooled day z {allz:.2f} against bar {zbar(N_RUNNING_BEFORE + N_THIS):.2f}:",
                  "NOT_YET_FALSIFIED (forward registration only)" if allz >= zbar(N_RUNNING_BEFORE + N_THIS) else "NOT_ENOUGH_DATA (z under the bar)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "counts"
    if cmd == "counts":
        cmd_counts()
    elif cmd == "dv":
        cmd_dv()
    elif cmd == "holdout":
        cmd_holdout(sys.argv[2:])
    else:
        print(__doc__)
