"""NEWH8: the cheap side late in the window on Kalshi's 15 minute gold and Bitcoin markets (research only).

Registration: workers/NEWH8_REGISTRATION.md (pushed before any scoring).

    PYTHONPATH=src python -m scalper.newh8 describe   (features only: no result, no quote after a signal; pre-registration look)
    PYTHONPATH=src python -m scalper.newh8 run        (scores the registered tries once)
    PYTHONPATH=src python -m scalper.newh8 parity     (forward_eval against the history scorer, survivors only)
"""
from __future__ import annotations

import math
import sqlite3
import statistics
import sys
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timezone

from .paths import DATA_DIR

GOLD, BTC, ETH = "KXGOLD15M", "KXBTC15M", "KXETH15M"
FILES = {BTC: ("l1b", "book", "fresh"), ETH: ("l1b", "book", "fresh"), GOLD: ("l1b", "book", "fresh", "five")}
START = int(datetime(2026, 8, 6, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 9, 21, tzinfo=timezone.utc).timestamp())
END = int(datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp())
OICORE_TH = 86299.56000000001
LO, HI = 0.05, 0.50


def day(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def stage(close):
    return "disc" if close < DISC_END else "val"


# ---------------------------------------------------------------- data

def load(series, start=START, end=END):
    """{close: {ticker, close, result, strike, c: {offset: (bid_c, ask_c, vol, oi)}, x: {offset: (ask_h, ask_l, bid_h, bid_l, price_c)}}}.
    First file wins per close (the order every NEWH worker used). `result` is carried but only `run` reads it."""
    win = {}
    for name in FILES[series]:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        mk = {tk: (close, res, k) for tk, close, res, k in db.execute(
            "select ticker, close_ts, result, strike from market where series=? and close_ts>=? and close_ts<?",
            (series, start, end))}
        rows = defaultdict(list)
        for r in db.execute("select ticker, end_ts, bid_c, ask_c, volume, oi, ask_h, ask_l, bid_h, bid_l, price_c from candle "
                            "where series=? and bid_c is not null and ask_c is not null", (series,)):
            if r[0] in mk:
                rows[r[0]].append(r)
        for tk, (close, res, k) in mk.items():
            if close in win or res not in ("yes", "no") or not rows.get(tk):
                continue
            c, x = {}, {}
            for _, e, b, a, v, oi, ah, al, bh, bl, pc in rows[tk]:
                c[e - close] = (b, a, v or 0.0, oi)
                x[e - close] = (ah, al, bh, bl, pc)
            win[close] = {"ticker": tk, "close": close, "result": res, "strike": k, "c": c, "x": x}
    return win


def side_ask(q, side):
    a = q[1] if side == "yes" else round(1 - q[0], 6)
    return a if 0 < a < 1 else None


def side_bid(q, side):
    return q[0] if side == "yes" else round(1 - q[1], 6)


def side_mid(q, side):
    m = (q[0] + q[1]) / 2
    return m if side == "yes" else 1 - m


def cheap_side(q, lo=LO, hi=HI):
    for s in ("yes", "no"):
        a = side_ask(q, s)
        if a is not None and lo - 1e-9 <= a <= hi + 1e-9:
            return s
    return None


# ---------------------------------------------------------------- features (closes, volume, oi only: forward-evaluable)

def feats(c, side, L=180):
    """Pre-signal features of the side `side` at the candle ending L s before the close; None for a missing input."""
    t = -L
    q = c.get(t)
    f = {}
    q3 = c.get(t - 180)
    f["doi"] = (q[3] - q3[3]) if (q3 is not None and q[3] is not None and q3[3] is not None) else None
    f["spread"] = q[1] - q[0]
    f["ask"] = side_ask(q, side)
    f["vol1"] = q[2]
    v3 = [c.get(t - 60 * j) for j in range(3)]
    f["vol3"] = sum(r[2] for r in v3) if all(r is not None for r in v3) else None
    f["oi"] = q[3]
    # cheap side's mid path from the first candle to the signal
    keys = sorted(k for k in c if -900 < k <= t)
    mids = [(k, side_mid(c[k], side)) for k in keys]
    f["n_candles"] = len(mids)
    # flips: the 0.5 line crossed by the mid (a mid of exactly 0.5 does not count as a side)
    flips, last_lead, prev = 0, None, None
    for k, m in mids:
        s = 1 if m > 0.5 else (-1 if m < 0.5 else 0)
        if s == 0:
            continue
        if prev is not None and s != prev:
            flips += 1
        prev = s
        if s == 1:
            last_lead = k
    f["flips"] = flips
    f["since_lead"] = (t - last_lead) if last_lead is not None else None   # seconds since the cheap side last led (mid > 0.5)
    f["max_mid"] = max(m for _, m in mids) if mids else None
    q6 = c.get(t - 180)
    f["drop3"] = (side_mid(q6, side) - side_mid(q, side)) if q6 is not None else None   # cheap mid fall over 3 min
    return f


# ---------------------------------------------------------------- describe (no result, no quote after the signal)

def _q(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    return xs[min(len(xs) - 1, int(p * (len(xs) - 1) + 0.5))]


def describe():
    print("NEWH8 describe: features at the 180 s signal candle only; no result and no later quote is read.\n")
    for series in (BTC, GOLD):
        W = load(series)
        peers = {s: load(s) for s in (BTC, ETH, GOLD) if s != series}
        for st in ("disc", "val"):
            fire, rest = [], []
            for close, w in W.items():
                if stage(close) != st:
                    continue
                q = w["c"].get(-180)
                if q is None:
                    continue
                s = cheap_side(q)
                if s is None:
                    continue
                f = feats(w["c"], s)
                x = w["x"].get(-180)
                if x is not None and x[4] is not None and q[1] > q[0]:
                    loc = (x[4] - q[0]) / (q[1] - q[0])            # last print in the YES spread (1 = at the YES ask)
                    f["loc_cheap"] = loc if s == "yes" else 1 - loc  # 1 = last print bought the cheap side
                else:
                    f["loc_cheap"] = None
                f["ah_al"] = None if x is None or x[0] is None else (x[0] - x[1] if s == "yes" else x[2] - x[3])
                for ps, PW in peers.items():
                    pw = PW.get(close)
                    a = pw["c"].get(-180) if pw else None
                    b = pw["c"].get(-360) if pw else None
                    f["doi_" + ps] = (a[3] - b[3]) if a and b and a[3] is not None and b[3] is not None else None
                f["hour"] = datetime.fromtimestamp(close, timezone.utc).hour
                f["side_yes"] = 1 if s == "yes" else 0
                if f["doi"] is None:
                    continue
                (fire if (series == BTC and f["doi"] > OICORE_TH) else rest).append(f)
            if series == GOLD:
                # gold has no OICORE; describe its own top decile of doi instead
                th = _q([f["doi"] for f in rest], 0.9)
                fire = [f for f in rest if f["doi"] > th]
                rest = [f for f in rest if f["doi"] <= th]
                print(f"{series} {st}: gold's own doi 90th pct {th:,.0f}")
            print(f"{series} {st}: firing {len(fire)}  rest {len(rest)}")
            keys = ["ask", "spread", "vol1", "vol3", "oi", "doi", "flips", "since_lead", "max_mid", "drop3", "n_candles",
                    "loc_cheap", "ah_al", "hour", "side_yes"] + [k for k in (fire[0] if fire else {}) if k.startswith("doi_K")]
            print(f"  {'feature':14s} {'fire p25':>10s} {'p50':>10s} {'p75':>10s} | {'rest p25':>10s} {'p50':>10s} {'p75':>10s}  fire n/a")
            for k in keys:
                a = [f.get(k) for f in fire]
                b = [f.get(k) for f in rest]
                fmt = lambda v: "-" if v is None else (f"{v:10.3f}" if abs(v) < 100 else f"{v:10,.0f}")
                print(f"  {k:14s} {fmt(_q(a, .25)):>10s} {fmt(_q(a, .5)):>10s} {fmt(_q(a, .75)):>10s} | "
                      f"{fmt(_q(b, .25)):>10s} {fmt(_q(b, .5)):>10s} {fmt(_q(b, .75)):>10s}  {sum(v is None for v in a)}")
            # shares
            for name, fn in (("cheap led within 3 min (since_lead <= 180)", lambda f: f["since_lead"] is not None and f["since_lead"] <= 180),
                             ("cheap ever led", lambda f: f["since_lead"] is not None),
                             ("2+ flips", lambda f: f["flips"] >= 2),
                             ("spread >= 2c", lambda f: f["spread"] >= 0.02 - 1e-9),
                             ("cheap mid fell >= 10c in 3 min", lambda f: f["drop3"] is not None and f["drop3"] >= 0.10)):
                sa = sum(fn(f) for f in fire) / max(1, len(fire))
                sb = sum(fn(f) for f in rest) / max(1, len(rest))
                print(f"  share {name:45s} fire {sa:6.1%}  rest {sb:6.1%}")
            print()


if __name__ == "__main__":
    {"describe": describe}[sys.argv[1]]()
