"""NEWH13: cross-market consistency and arbitrage, the same event priced twice, on gold and Bitcoin (research only).

Registration: workers/NEWH13_REGISTRATION.md (pushed with this file before any scoring).

    PYTHONPATH=src python -m scalper.newh13 dv            (H1 GLOCKH and H2 GLADX-L, discovery and validation, scored once;
                                                           I2, I3 and I4 information counts)
    PYTHONPATH=src python -m scalper.newh13 holdout NAME  (frozen holdout, read once, only for a rule that passed dv)
    PYTHONPATH=src python -m scalper.newh13 book DIR      (I1: the recorded 5 level KXBTCD book's consistency at depth;
                                                           DIR holds book/<date>/<run>/book.csv.gz from origin/quote-data)

Tries (3): GLOCKH (a lock between gold's 15 minute contract and the hourly gold ladder at the shared close, both legs filled at
the next candle), GLADX-L (the gold LADDER leg bought toward the 15 minute book when monotonicity is violated at the mids),
BTCDIGI-F (registered forward only; nothing here scores it). H4 (a Dutch book inside one market) is NOT_RUNNABLE by the
exchange's structure and has no code. Information looks (4, counted): I1 book consistency at depth, I2 Bitcoin lock count on
LOCK2H's unread days, I3 gold lock count over the whole window, I4 the base rate of H2's legs without a violation.

Nothing here buys the 88c to 97c favourite, nothing is bought in the last 6 minutes (every fill candle ends 420 s or more
before the close), no side is chosen by a price band, nothing is sold.
"""
from __future__ import annotations

import csv
import gzip
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import newh8
from .newh9 import (BTC, DISC_END, END, GOLD, START, VAL_END, day, dayz, fee, fmt, load15, load_ladder, net, stage, summ,
                    zbar)

N_RUNNING_BEFORE = 700_154            # ledger after GEN10
N_THIS = 7                            # 3 tries + 4 information looks (registered)

LOCK_MIN = 0.01                                   # per contract after C = 10 fees on both legs
LOCK_SIGNALS = tuple(range(-840, -480 + 1, 60))   # H1 signal candles (minutes 1 to 7); the fill candle ends 780 to 420 s before
FULL_MINUTES = tuple(range(-840, -60 + 1, 60))    # I2, I3 count only (minutes 1 to 14), no fill, no trade

SIGNALS2 = (-660, -600, -540, -480)               # H2 signal candles; fills end 600 to 420 s before the close
VIOL = 0.03                                       # a monotonicity violation at the mids of at least 3c
SPREAD15 = 0.04                                   # the 15 minute quote must be at most 4c wide
SPREADLAD = 0.06                                  # the ladder strike's quote at most 6c wide
BAND2 = (0.05, 0.85)                              # H2 fill band; nothing at L1's 88c to 97c

FILES15 = {GOLD: ("l1b", "book", "fresh", "five"), BTC: ("l1b", "book", "fresh")}
LADDER_FILES = {GOLD: ("newh2_goldh.sqlite",), BTC: ("conf2_lad.sqlite", "lad2.sqlite")}
I2_START = int(datetime(2026, 8, 24, tzinfo=timezone.utc).timestamp())
I2_END = int(datetime(2026, 9, 26, tzinfo=timezone.utc).timestamp())    # LOCK2H read Sep 26 to Oct 26


# ---------------------------------------------------------------- quotes

def readable(q):
    if q is None:
        return False
    b, a = q[0], q[1]
    return b is not None and a is not None and 0 <= b <= a <= 1 and a > 0 and b < 1


def mid(q):
    return (q[0] + q[1]) / 2


def spread(q):
    return q[1] - q[0]


def pairs(W, EV):
    """Top-of-hour 15 minute closes with a settled ladder event at the same instant and a numeric 15 minute strike."""
    return sorted(c for c in W if c % 3600 == 0 and c in EV and W[c]["strike"] is not None)


# ---------------------------------------------------------------- H1 GLOCKH and the lock counts

def lock_legs(q15, lq, k0, k):
    """The two asks of the monotonicity lock at ladder strike k: (p_15m, p_ladder, side_15m, side_ladder), or None."""
    if not readable(q15) or not readable(lq):
        return None
    if k >= k0:
        p1, p2 = q15[1], round(1 - lq[0], 6)          # 15 minute YES, ladder NO
        s1, s2 = "yes", "no"
    else:
        p1, p2 = round(1 - q15[0], 6), lq[1]          # 15 minute NO, ladder YES
        s1, s2 = "no", "yes"
    if not (0 < p1 < 1 and 0 < p2 < 1):
        return None
    return p1, p2, s1, s2


def lock_value(p1, p2, c=10):
    return 1 - p1 - p2 - (fee(p1, c) + fee(p2, c)) / c


def best_lock(w, e, t):
    """Best lock over the ladder's strikes at the candle ending t (seconds before the close, negative)."""
    q15 = w["c"].get(t)
    lq = e["q"].get(w["close"] + t)
    if q15 is None or not lq:
        return None
    k0 = float(w["strike"])
    best = None
    for k, q in lq.items():
        legs = lock_legs(q15, q, k0, k)
        if legs is None:
            continue
        v = lock_value(legs[0], legs[1])
        if best is None or v > best[0]:
            best = (v, k, legs)
    return best


def glock(W, EV, closes):
    """H1: the first signal candle (minutes 1 to 7) with a lock >= LOCK_MIN decides the close; both legs filled at the
    next candle's asks; payoff is the number of legs that win (1 or 2)."""
    tr, fun = [], Counter()
    for close in closes:
        w, e = W[close], EV[close]
        fun["closes"] += 1
        for t in LOCK_SIGNALS:
            b = best_lock(w, e, t)
            if b is None:
                continue
            fun["candles read"] += 1
            v, k, (p1, p2, s1, s2) = b
            if v < LOCK_MIN - 1e-9:
                continue
            fun["signals"] += 1
            f15 = w["c"].get(t + 60)
            fl = e["q"].get(close + t + 60, {}).get(k)
            legs = lock_legs(f15, fl, float(w["strike"]), k)
            if legs is None:
                fun["no fill"] += 1
                break
            q1, q2 = legs[0], legs[1]
            payoff = (w["result"] == s1) + (e["res"][k] == s2)
            sq, lq = w["c"][t], e["q"][close + t][k]
            zv = min(sq[2], lq[2], f15[2], fl[2]) <= 0
            tr.append({"close": close, "stage": stage(close), "legs": [q1, q2], "payoff": payoff, "zv": zv,
                       "sig_lock": v, "fill_lock": lock_value(q1, q2), "k": k, "t": t})
            fun["trades"] += 1
            break
    return tr, fun


def lock_count(W, EV, closes, minutes):
    """Signal-candle lock count only (no fill, no outcome): closes with a lock >= LOCK_MIN, lock minutes, the largest, the
    longest run of consecutive lock minutes, the median best lock, and the share of closes with a pairable minute."""
    with_lock = minutes_locked = 0
    largest, best_per_close, longest = -9.0, [], 0
    for close in closes:
        w, e = W[close], EV[close]
        best, run, maxrun, seen = -9.0, 0, 0, False
        for t in minutes:
            b = best_lock(w, e, t)
            if b is None:
                run = 0
                continue
            seen = True
            best = max(best, b[0])
            if b[0] >= LOCK_MIN - 1e-9:
                minutes_locked += 1
                run += 1
                maxrun = max(maxrun, run)
            else:
                run = 0
        if seen:
            best_per_close.append(best)
        if best >= LOCK_MIN - 1e-9:
            with_lock += 1
            longest = max(longest, maxrun)
        largest = max(largest, best)
    med = sorted(best_per_close)[len(best_per_close) // 2] if best_per_close else float("nan")
    return {"closes": len(closes), "pairable": len(best_per_close), "closes with lock": with_lock,
            "lock minutes": minutes_locked, "largest c": round(100 * largest, 2), "median best c": round(100 * med, 2),
            "longest run": longest}


# ---------------------------------------------------------------- H2 GLADX-L and I4

def bracket(lq, k0):
    """The quoted ladder strikes just at or above and just below the 15 minute strike, readable and at most SPREADLAD wide."""
    ok = {k: q for k, q in lq.items() if readable(q) and spread(q) <= SPREADLAD + 1e-9}
    hi = [k for k in ok if k >= k0]
    lo = [k for k in ok if k < k0]
    if not hi or not lo:
        return None
    return min(hi), max(lo), ok


def gladx(W, EV, closes):
    """H2: the first signal candle (minutes 4 to 7) where the ladder's mid at k_hi sits >= VIOL above the 15 minute mid (buy
    ladder NO at k_hi) or the ladder's mid at k_lo sits >= VIOL below it (buy ladder YES at k_lo); filled at the next
    candle's ask of that leg inside BAND2, held. Also I4: the same legs at the first readable candle when there is no
    violation by at least VIOL on both sides (the base rate; information)."""
    tr, base, fun = [], [], Counter()
    for close in closes:
        w, e = W[close], EV[close]
        k0 = float(w["strike"])
        fun["closes"] += 1
        based = False
        for t in SIGNALS2:
            q15 = w["c"].get(t)
            lq = e["q"].get(close + t)
            if not readable(q15) or spread(q15) > SPREAD15 + 1e-9 or not lq:
                fun["15m unreadable or wide"] += 1
                continue
            br = bracket(lq, k0)
            if br is None:
                fun["no readable bracket"] += 1
                continue
            khi, klo, ok = br
            m15 = mid(q15)
            va = mid(ok[khi]) - m15            # should be <= 0
            vb = m15 - mid(ok[klo])            # should be <= 0
            fun["candles read"] += 1
            if not based and va <= -VIOL + 1e-9 and vb <= -VIOL + 1e-9:
                based = True
                f = e["q"].get(close + t + 60, {})
                for k, side in ((khi, "no"), (klo, "yes")):
                    fq = f.get(k)
                    a = newh8.side_ask(fq, side) if readable(fq) else None
                    if a is None or not (BAND2[0] - 1e-9 <= a <= BAND2[1] + 1e-9):
                        continue
                    base.append({"close": close, "stage": stage(close), "legs": [a], "payoff": 1 if e["res"][k] == side else 0,
                                 "zv": min(ok[k][2], fq[2]) <= 0, "side": side})
            if max(va, vb) < VIOL - 1e-9:
                continue
            k, side, v = (khi, "no", va) if va >= vb else (klo, "yes", vb)
            fun["triggers"] += 1
            fq = e["q"].get(close + t + 60, {}).get(k)
            a = newh8.side_ask(fq, side) if readable(fq) else None
            if a is None:
                fun["no fill"] += 1
                break
            if not (BAND2[0] - 1e-9 <= a <= BAND2[1] + 1e-9):
                fun["band"] += 1
                break
            tr.append({"close": close, "stage": stage(close), "legs": [a], "payoff": 1 if e["res"][k] == side else 0,
                       "zv": min(q15[2], ok[k][2], fq[2]) <= 0, "side": side, "viol": v, "t": t,
                       "sig_ask": newh8.side_ask(ok[k], side)})
            fun["trades"] += 1
            break
    return tr, base, fun


# ---------------------------------------------------------------- verdicts and commands

def verdict_common(d, v):
    if d["n"] < 100:
        return "NOT_ENOUGH_DATA (discovery under 100)"
    if d["pf10"] < 1.5 or d["netx"] <= 0:
        return "FALSIFIED (discovery)"
    if v["n"] < 50:
        return "NOT_ENOUGH_DATA (validation under 50)"
    if v["pf10"] < 1.5 or v["netx"] <= 0:
        return "FALSIFIED (validation)"
    return "PASSED dv: read the holdout once"


def verdict_lock(fun_dv, d, v):
    if fun_dv["signals"] == 0:
        return "FALSIFIED (zero signal locks in discovery and validation)"
    return verdict_common(d, v)


def load_all(series):
    newh8.FILES[series] = FILES15[series]
    W = load15(series)
    EV = load_ladder(*LADDER_FILES[series])
    return W, EV


def side_stats(tt):
    if not tt:
        return ""
    sa = [t["sig_ask"] for t in tt if t.get("sig_ask") is not None]
    return (f"yes share {sum(t['side'] == 'yes' for t in tt) / len(tt):.2f}; mean violation {sum(t['viol'] for t in tt) / len(tt):.3f}; "
            f"signal ask {sum(sa) / len(sa):.3f} vs fill {sum(t['legs'][0] for t in tt) / len(tt):.3f}; "
            f"by candle {dict(Counter(t['t'] for t in tt))}")


def cmd_dv():
    W, EV = load_all(GOLD)
    closes = pairs(W, EV)
    st = Counter(stage(c) for c in closes)
    print(f"gold: {len(W)} settled 15 minute windows, {len(EV)} KXGOLDH events, {len(closes)} paired top-of-hour closes "
          f"(disc {st['disc']}, val {st['val']}, hold {st['hold']})")
    dv_closes = [c for c in closes if stage(c) != "hold"]

    # H1 GLOCKH
    tr, fun = glock(W, EV, dv_closes)
    d = summ([t for t in tr if t["stage"] == "disc"])
    v = summ([t for t in tr if t["stage"] == "val"])
    print("\n== H1 GLOCKH (gold 15 minute against KXGOLDH, lock >= 1c after fees at the signal, both legs filled next candle)")
    print("  funnel (disc+val):", dict(fun))
    if tr:
        print("  signal locks (c):", [round(100 * t["sig_lock"], 2) for t in tr])
        print("  fill locks (c)  :", [round(100 * t["fill_lock"], 2) for t in tr])
        print("  payoffs         :", [t["payoff"] for t in tr], "closes:", [day(t["close"]) for t in tr])
    print("  discovery  :", fmt(d))
    print("  validation :", fmt(v))
    print("  verdict:", verdict_lock(fun, d, v))

    # I3 gold lock count over the whole window (minutes 14 to 1; the late minutes are information only)
    print("\n== I3 gold lock count, signal candles only, minutes 14 to 1 (no fill, no trade):")
    for lab, cl in (("disc", [c for c in closes if stage(c) == "disc"]), ("val", [c for c in closes if stage(c) == "val"])):
        print(f"  {lab}:", lock_count(W, EV, cl, FULL_MINUTES))
    print("  minutes 1 to 7 only (H1's signal minutes), disc+val:", lock_count(W, EV, dv_closes, LOCK_SIGNALS))

    # H2 GLADX-L and I4
    tr2, base, fun2 = gladx(W, EV, dv_closes)
    d2 = summ([t for t in tr2 if t["stage"] == "disc"])
    v2 = summ([t for t in tr2 if t["stage"] == "val"])
    print("\n== H2 GLADX-L (the gold LADDER leg bought toward the 15 minute book on a 3c monotonicity violation at the mids)")
    print("  funnel (disc+val):", dict(fun2))
    print("  discovery  :", fmt(d2), "|", side_stats([t for t in tr2 if t["stage"] == "disc"]))
    print("  validation :", fmt(v2), "|", side_stats([t for t in tr2 if t["stage"] == "val"]))
    print("  verdict:", verdict_common(d2, v2))
    print("  I4 base rate (same legs, first readable candle, no violation by 3c on either side; information):")
    for lab in ("disc", "val"):
        bb = [t for t in base if t["stage"] == lab]
        for side in ("no", "yes"):
            s = summ([t for t in bb if t["side"] == side])
            print(f"    {lab} ladder {side.upper()} at {'k_hi' if side == 'no' else 'k_lo'}:", fmt(s))

    # I2 Bitcoin lock count on LOCK2H's unread days
    WB, EVB = load_all(BTC)
    cb = [c for c in pairs(WB, EVB) if I2_START <= c < I2_END]
    print(f"\n== I2 Bitcoin lock count (KXBTC15M against KXBTCD), closes Aug 24 to Sep 25 only (LOCK2H read Sep 26 to Oct 26):")
    print("  minutes 14 to 1:", lock_count(WB, EVB, cb, FULL_MINUTES))
    print("  minutes 1 to 7 :", lock_count(WB, EVB, cb, LOCK_SIGNALS))

    print(f"\nN running before {N_RUNNING_BEFORE:,}; this round {N_THIS}; after about {N_RUNNING_BEFORE + N_THIS:,}; "
          f"one-sided z bar {zbar(N_RUNNING_BEFORE + N_THIS):.2f}")


def cmd_holdout(names):
    W, EV = load_all(GOLD)
    closes = pairs(W, EV)
    for name in names:
        if name == "GLOCKH":
            tr, _ = glock(W, EV, closes)
        elif name == "GLADX-L":
            tr, _, _ = gladx(W, EV, closes)
        else:
            print("unknown rule", name)
            continue
        h = summ([t for t in tr if t["stage"] == "hold"])
        print(f"== {name} HOLDOUT (Oct 18 to Oct 30, read once):", fmt(h))
        if h["n"] < 30:
            print("  NOT_ENOUGH_DATA (holdout under 30)")
        elif h["pf10"] < 1.5 or h["netx"] <= 0:
            print("  FALSIFIED (holdout)")
        else:
            allz = dayz(tr)
            bar = zbar(N_RUNNING_BEFORE + N_THIS)
            print(f"  pooled day z {allz:.2f} against bar {bar:.2f}:",
                  "NOT_YET_FALSIFIED (forward registration only)" if allz >= bar else "NOT_ENOUGH_DATA (z under the bar)")


# ---------------------------------------------------------------- I1: the recorded 5 level book's consistency at depth

def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def read_books(root):
    rows = []
    for p in sorted(Path(root).rglob("book.csv.gz")):
        with gzip.open(p, "rt", newline="") as fh:
            for r in csv.DictReader(fh):
                ts = int(r["poll_ts_local_ms"])
                close = int(datetime.fromisoformat(r["close_time"].replace("Z", "+00:00")).timestamp())
                yb = [(_f(r[f"yes_bid_px_{i}"]), _f(r[f"yes_bid_sz_{i}"])) for i in range(1, 6)]
                nb = [(_f(r[f"no_bid_px_{i}"]), _f(r[f"no_bid_sz_{i}"])) for i in range(1, 6)]
                rows.append((ts, close, float(r["strike"]), yb, nb))
    rows.sort()
    return rows


def locked_quantity(no_bids_k1, yes_bids_k2, c=10):
    """Walk the two bid ladders while NO bid(k1) + YES bid(k2) still exceeds 1 plus both fees (buying YES at k1 at
    1 - NO bid and NO at k2 at 1 - YES bid): the contracts that could be locked, and the value of the top pair."""
    nb = [(p, s) for p, s in no_bids_k1 if p is not None and s]
    yb = [(p, s) for p, s in yes_bids_k2 if p is not None and s]
    i = j = 0
    qty = 0.0
    top = None
    ri = nb[0][1] if nb else 0
    rj = yb[0][1] if yb else 0
    while i < len(nb) and j < len(yb):
        p1, p2 = round(1 - nb[i][0], 6), round(1 - yb[j][0], 6)
        v = lock_value(p1, p2, c)
        if top is None:
            top = v
        if v < 0:
            break
        m = min(ri, rj)
        qty += m
        ri -= m
        rj -= m
        if ri <= 0:
            i += 1
            ri = nb[i][1] if i < len(nb) else 0
        if rj <= 0:
            j += 1
            rj = yb[j][1] if j < len(yb) else 0
    return qty, top


def cmd_book(root):
    rows = read_books(root)
    print(f"I1: {len(rows)} book rows from {root}")
    latest = {}                    # (close, strike) -> (ts, yb, nb)
    strikes = defaultdict(set)
    for ts, close, k, yb, nb in rows:
        strikes[close].add(k)
    evals = Counter()
    cross_top = Counter()          # NO bid(k1) + YES bid(k2) > 1 (a lock before fees)
    cross_fee = Counter()          # lock >= 1c after C = 10 fees at the top
    inverted = Counter()           # YES bid(k2) > YES bid(k1)
    qtys = []
    run, runs = defaultdict(int), []
    by_min = defaultdict(lambda: Counter())
    for ts, close, k, yb, nb in rows:
        latest[(close, k)] = (ts, yb, nb)
        ks = sorted(strikes[close])
        i = ks.index(k)
        for k1, k2 in ((ks[i - 1], k) if i > 0 else (None, None)), ((k, ks[i + 1]) if i + 1 < len(ks) else (None, None)):
            if k1 is None:
                continue
            a, b = latest.get((close, k1)), latest.get((close, k2))
            if a is None or b is None or abs(a[0] - b[0]) > 1500:
                continue
            m = int((close - ts / 1000) // 60)
            bucket = f"{5 * (m // 5):02d}-{5 * (m // 5) + 4:02d} min"
            evals[close] += 1
            by_min[bucket]["evals"] += 1
            nb1, yb2 = a[2], b[1]
            yb1 = a[1]
            key = (close, k1, k2)
            if nb1[0][0] is not None and yb2[0][0] is not None and nb1[0][0] + yb2[0][0] > 1 + 1e-9:
                cross_top[close] += 1
                by_min[bucket]["cross"] += 1
                qty, top = locked_quantity(nb1, yb2)
                if top is not None and top >= LOCK_MIN - 1e-9:
                    cross_fee[close] += 1
                    by_min[bucket]["cross after fees"] += 1
                    qtys.append(qty)
                run[key] += 1
            else:
                if run[key]:
                    runs.append(run[key])
                run[key] = 0
            if yb1[0][0] is not None and yb2[0][0] is not None and yb2[0][0] > yb1[0][0] + 1e-9:
                inverted[close] += 1
                by_min[bucket]["mark inversion"] += 1
    runs += [r for r in run.values() if r]
    tot = sum(evals.values())
    print(f"  events {len(strikes)}; adjacent-pair evaluations {tot:,} (both strikes polled within 1.5 s)")
    print(f"  (a) top-of-book cross before fees: {sum(cross_top.values()):,} ({sum(cross_top.values()) / tot:.3%} of evaluations), "
          f"in {sum(1 for c in cross_top if cross_top[c])} events")
    print(f"  (b) lock >= 1c after C = 10 fees : {sum(cross_fee.values()):,} ({sum(cross_fee.values()) / tot:.3%})")
    print(f"  (c) mark inversion YES bid(k2) > YES bid(k1): {sum(inverted.values()):,} ({sum(inverted.values()) / tot:.3%})")
    if qtys:
        q = sorted(qtys)
        print(f"  (d) locked contracts at depth when (b): median {q[len(q) // 2]:.0f}, max {q[-1]:.0f}")
    if runs:
        r = sorted(runs)
        print(f"  (e) cross runs (consecutive evaluations, about 3 s each): n {len(r)}, median {r[len(r) // 2]}, max {r[-1]}")
    print("  by minutes to the close:")
    for b in sorted(by_min, reverse=True):
        print(f"    {b}: {dict(by_min[b])}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "dv":
        cmd_dv()
    elif cmd == "holdout":
        cmd_holdout(sys.argv[2:])
    elif cmd == "book" and len(sys.argv) > 2:
        cmd_book(sys.argv[2])
    else:
        print(__doc__)
