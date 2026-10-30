"""NEWH4 (V2 worker, 2026-10-30, research only): ladder-only mechanisms on KXBTCD and KXGOLDH.

Registration: workers/NEWH4_REGISTRATION.md (pushed before this was run). Run once:
    PYTHONPATH=src python -m scalper.newh4 run
H1/H2 KINK (one strike off the ladder's own probit curve), H3/H4 TAIL (deep longshots held),
H5 NARROW (ladder width against the realised movement of its own centre). Nothing here trades.
"""
from __future__ import annotations

import math
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from statistics import NormalDist

from .newh2 import DISC_END, END, day, summ, line, verdict
from .newh3 import trade
from .paths import DATA_DIR

START = int(datetime(2026, 8, 23, tzinfo=timezone.utc).timestamp())
N01 = NormalDist()
BTC_FILES = (("lad2", "KXBTCD"), ("conf2_lad", "KXBTCD"))
GOLD_FILES = (("newh2_goldh", "KXGOLDH"),)


def load(files, start=START, end=END):
    """{close: [(strike, result, {end_ts: (bid, ask, vol)})]}; first file wins per ticker. Missing bid -> 0, ask -> 1."""
    lad, seen = defaultdict(list), set()
    for name, series in files:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        mk = db.execute("select ticker, close_ts, result, strike from market where series=? and close_ts>=? and close_ts<?",
                        (series, start, end)).fetchall()
        for tk, close, res, k in mk:
            if tk in seen or res not in ("yes", "no") or k is None:
                continue
            cs = {}
            for e, b, a, v in db.execute("select end_ts, bid_c, ask_c, volume from candle where ticker=?", (tk,)):
                if b is None and a is None:
                    continue
                cs[e] = (b or 0.0, 1.0 if a is None else a, v or 0.0)
            seen.add(tk)
            if cs:
                lad[close].append((k, res, cs))
    for c in lad:
        lad[c].sort(key=lambda x: x[0])
    return lad


def quoted(r):
    return r is not None and 0 < r[0] < r[1] < 1


def probit_fit(pts, nmin):
    """pts [(K, mid)] -> (mu, s) of P(above K) = Phi((mu - K) / s), or None."""
    xs, zs = [], []
    for k, m in pts:
        if 0.03 <= m <= 0.97:
            xs.append(k)
            zs.append(N01.inv_cdf(m))
    if len(xs) < nmin:
        return None
    mx, mz = statistics.fmean(xs), statistics.fmean(zs)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    b = sum((x - mx) * (z - mz) for x, z in zip(xs, zs)) / sxx
    if b >= 0:
        return None
    a = mz - b * mx
    return -a / b, -1.0 / b


def side_ask(r, side):
    return r[1] if side == "yes" else round(1 - r[0], 6)


def fill(close, strike, side, t, lo, hi, gaps):
    k, res, cs = strike
    fr = cs.get(t + 60)
    if fr is None:
        gaps["fill_candle_missing"] += 1
        return None
    a = side_ask(fr, side)
    if not (lo - 1e-9 <= a <= hi + 1e-9) or (side == "no" and fr[0] <= 0) or (side == "yes" and fr[1] >= 1):
        gaps["fill_out_of_band"] += 1
        return None
    won = (res == "yes") == (side == "yes")
    return trade(close, side, a, won, fr[2] == 0)


# ---------- H1 / H2 KINK ----------

def kink(L, lead_hi, lead_lo):
    T, gaps = [], defaultdict(int)
    for close in sorted(L):
        strikes = L[close]
        gaps["closes"] += 1
        done = False
        for t in range(close - lead_hi, close - lead_lo + 1, 60):
            rows = [(s, s[2].get(t)) for s in strikes]
            q = [(s, r) for s, r in rows if quoted(r)]
            best = None
            for i, (s, r) in enumerate(q):
                if r[1] - r[0] > 0.05 + 1e-9:
                    continue
                f = probit_fit([(s2[0], (r2[0] + r2[1]) / 2) for j, (s2, r2) in enumerate(q) if j != i], 5)
                if f is None:
                    continue
                mu, sd = f
                fv = N01.cdf((mu - s[0]) / sd)
                for side, gap in (("yes", fv - r[1]), ("no", r[0] - fv)):
                    a = side_ask(r, side)
                    if gap >= 0.05 - 1e-9 and 0.10 - 1e-9 <= a <= 0.85 + 1e-9:
                        if best is None or gap > best[0]:
                            best = (gap, s, side)
            if best:
                gaps["signals"] += 1
                tr = fill(close, best[1], best[2], t, 0.10, 0.85, gaps)
                if tr:
                    T.append(tr)
                done = True
                break
        if not done:
            gaps["no_signal"] += 1
    return T, gaps


# ---------- H3 / H4 TAIL ----------

def tail(L, lead):
    T, gaps = [], defaultdict(int)
    for close in sorted(L):
        gaps["closes"] += 1
        t = close - lead
        ys, ns = [], []
        for s in L[close]:
            r = s[2].get(t)
            if r is None:
                continue
            if r[1] < 1 and 0.02 - 1e-9 <= r[1] <= 0.06 + 1e-9:
                ys.append(s)
            if r[0] > 0 and 0.02 - 1e-9 <= 1 - r[0] <= 0.06 + 1e-9:
                ns.append(s)
        if not ys and not ns:
            gaps["no_signal"] += 1
        for pick, side in ((min(ys, key=lambda s: s[0]) if ys else None, "yes"),
                           (max(ns, key=lambda s: s[0]) if ns else None, "no")):
            if pick is None:
                continue
            gaps["signals"] += 1
            tr = fill(close, pick, side, t, 0.01, 0.08, gaps)
            if tr:
                T.append(tr)
    return T, gaps


# ---------- H5 NARROW ----------

def narrow(L):
    T, gaps = [], defaultdict(int)
    for close in sorted(L):
        gaps["closes"] += 1
        strikes = L[close]
        fits = {}
        for t in range(close - 3300, close - 600 + 1, 60):
            pts = [(s[0], (r[0] + r[1]) / 2) for s in strikes for r in [s[2].get(t)] if quoted(r)]
            f = probit_fit(pts, 3)
            if f:
                fits[t] = f
        done = False
        for t in range(close - 2100, close - 600 + 1, 60):
            if t not in fits:
                continue
            d = [fits[u][0] - fits[u - 60][0] for u in range(t - 1080, t + 1, 60) if u in fits and u - 60 in fits]
            if len(d) < 15:
                continue
            sd1 = statistics.stdev(d)
            real = sd1 * math.sqrt((close - t) / 60)
            if real <= 0:
                continue
            mu, s_t = fits[t]
            if s_t / real > 0.6:
                continue
            best = None
            for s in strikes:
                r = s[2].get(t)
                if not quoted(r) or r[1] - r[0] > 0.05 + 1e-9 or s[0] == mu:
                    continue
                side = "yes" if s[0] > mu else "no"
                a = side_ask(r, side)
                if 0.10 - 1e-9 <= a <= 0.35 + 1e-9:
                    key = (abs(a - 0.20), s[0])
                    if best is None or key < best[0]:
                        best = (key, s, side)
            if best is None:
                gaps["narrow_no_candidate"] += 1
                continue
            gaps["signals"] += 1
            tr = fill(close, best[1], best[2], t, 0.10, 0.35, gaps)
            if tr:
                T.append(tr)
            done = True
            break
        if not done:
            gaps["no_signal"] += 1
    return T, gaps


def split(T):
    return [t for t in T if t["close"] < DISC_END], [t for t in T if t["close"] >= DISC_END]


def run():
    out = []
    p = out.append
    btc, gold = load(BTC_FILES), load(GOLD_FILES)
    for nm, L in (("KXBTCD", btc), ("KXGOLDH", gold)):
        dc = sum(1 for c in L if c < DISC_END)
        p(f"{nm}: closes {len(L)} (discovery {dc}, validation {len(L) - dc}), first {day(min(L))}, last {day(max(L))}")
    jobs = [("H1 KINK-BTC", lambda: kink(btc, 3000, 600)), ("H2 KINK-GOLD", lambda: kink(gold, 840, 180)),
            ("H3 TAIL-BTC", lambda: tail(btc, 1800)), ("H4 TAIL-GOLD", lambda: tail(gold, 600)),
            ("H5 NARROW-BTC", lambda: narrow(btc))]
    for name, fn in jobs:
        T, gaps = fn()
        D, V = split(T)
        sd, sv = summ(D), summ(V)
        p("")
        p(f"== {name}  gaps {dict(gaps)}")
        p(line("  discovery", sd))
        p(line("  validation", sv))
        for lab, sub in (("disc", D), ("val", V)):
            for side in ("yes", "no"):
                ss = summ([t for t in sub if t["side"] == side])
                p(line(f"    {lab} {side}", ss))
        p(f"  VERDICT {name}: {verdict(sd, sv)}")
    txt = "\n".join(out)
    print(txt)
    return txt


if __name__ == "__main__":
    if sys.argv[1:] == ["run"]:
        run()
    else:
        print(__doc__)
