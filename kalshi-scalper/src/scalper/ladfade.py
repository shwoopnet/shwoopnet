"""LADFADE: fade the Bitcoin 15 minute book's first-minute overshoot past the hourly KXBTCD ladder (research only).

Registration: workers/LADFADE_REGISTRATION.md (pushed before any holdout fill or outcome was read).
Origin: NEWH9's information look I1 (post hoc), so discovery and validation are SPENT for this rule; the only clean history is the
NEWH9 frozen holdout (closes 2026-10-18 00:00 to 2026-10-30 00:00 UTC), then forward windows.

    PYTHONPATH=src python -m scalper.ladfade holdout     (scored once)

Forward: `forward_eval` (source `candles`, KXBTC15M) reads the hourly ladder from the book recorder (origin/quote-data book/).
Nothing here places an order, reads a key or decides anything live.
"""
from __future__ import annotations

import sys
from collections import defaultdict

from . import newh8, newh9
from .fwdeval import NoData

BTC = "KXBTC15M"
LEAN = 0.05            # |ladder p - 0.5| >= 0.05, the population I1 was observed on
GAP = 0.03             # ladder chance of the faded side minus its 15 minute ask at the signal candle, at least 3c
BAND = (0.30, 0.70)    # the fill ask (next candle) must be inside
SIG, FILL = -840, -780  # candle end offsets from the 15 minute close: the window's first minute, then the next one

N_RUNNING_BEFORE = 627_845   # after NEWH9 (NEWH9_RESULT.md)
N_THIS = 1


def decide(close, strike, c, q):
    """c: {offset: (bid, ask, vol)} for the 15 minute market; q: {ladder strike: (bid, ask, vol)} at the signal minute.
    Returns (trade dict or None, reason). Uses only the signal candle to decide and the NEXT candle's ask to fill."""
    if close % 3600 not in (1800, 2700):
        return None, "clock"
    if c.get(SIG) is None or c.get(FILL) is None or strike is None or not q:
        return None, "gap"
    p = newh9.ladder_p(q, float(strike))
    if p is None:
        return None, "gap"
    if p >= 0.5 + LEAN - 1e-9:
        side, chance = "no", 1 - p          # the book leans YES with the ladder; fade it: buy NO
    elif p <= 0.5 - LEAN + 1e-9:
        side, chance = "yes", p
    else:
        return None, "flat"
    a_sig = newh8.side_ask(c[SIG], side)
    if a_sig is None:
        return None, "gap"
    if chance - a_sig < GAP - 1e-9:
        return None, "nogap"
    a = newh8.side_ask(c[FILL], side)
    if a is None:
        return None, "nofill"
    if not (BAND[0] - 1e-9 <= a <= BAND[1] + 1e-9):
        return None, "band"
    return {"side": side, "entry": a, "p": p, "chance": chance, "a_sig": a_sig,
            "zv": (c[SIG][2] or 0) <= 0 or (c[FILL][2] or 0) <= 0}, "trade"


def history(stage_want):
    W = newh9.load15(BTC)
    EV = newh9.load_ladder("conf2_lad.sqlite", "lad2.sqlite")
    tr, info = [], defaultdict(int)
    for close, w in sorted(W.items()):
        if newh9.stage(close) != stage_want:
            continue
        H = close - close % 3600 + 3600
        q = EV[H]["q"].get(close + SIG) if H in EV else None
        d, why = decide(close, w["strike"], w["c"], q)
        info[why] += 1
        if d:
            tr.append({"close": close, "stage": stage_want, "legs": [d["entry"]], "payoff": 1 if w["result"] == d["side"] else 0,
                       "zv": d["zv"], **d})
    return tr, dict(info)


def verdict(s, z):
    if s["n"] < 30:
        return "NOT_ENOUGH_DATA"
    if s["pf10"] < 1.5 or s["netx"] <= 0:
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED (forward only: day z %.2f cannot reach the deflated bar on 12 days)" % z


def holdout():
    tr, info = history("hold")
    N = N_RUNNING_BEFORE + N_THIS
    s = newh9.summ(tr)
    print(f"LADFADE holdout (read once). running N {N:,}; deflated one-sided z bar {newh9.zbar(N):.2f}")
    print("funnel", info)
    print(newh9.fmt(s))
    if s["n"]:
        import statistics as st
        print(f"mean ladder chance of the faded side {st.mean(t['chance'] for t in tr):.3f}, mean signal ask {st.mean(t['a_sig'] for t in tr):.3f}, "
              f"mean fill ask {st.mean(t['entry'] for t in tr):.3f}, win rate {st.mean(t['payoff'] for t in tr):.3f}")
        for side in ("yes", "no"):
            x = [t for t in tr if t["side"] == side]
            if x:
                print(f"  bought {side}: {newh9.fmt(newh9.summ(x))}")
        nz = [t for t in tr if not t["zv"]]
        print("without zero-volume trades:", newh9.fmt(newh9.summ(nz)) if nz else "n 0")
    print("VERDICT:", verdict(s, s.get("z", float("nan"))) if s["n"] else "NOT_ENOUGH_DATA")


# ---------------------------------------------------------------- forward (fwdledger, source "candles")

_BOOK = {}


def _ladder_at(H, t_end):
    """{strike: (yes_bid, yes_ask, 1)} from the book recorder: per strike the last poll inside the minute ending at t_end (the
    same minute a 1 minute candle's close describes). YES ask = 1 - best NO bid. None when the hour was not recorded."""
    from .mm1 import _csv, _git
    from datetime import datetime, timezone
    if H not in _BOOK:
        if not _BOOK:
            _git("fetch", "-q", "origin", "quote-data")
        iso = datetime.fromtimestamp(H, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows = []
        files = _BOOK.setdefault("_files", [f for f in _git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split()
                                            if f.startswith("book/") and f.endswith("/book.csv.gz")])
        day = datetime.fromtimestamp(H - 3600, timezone.utc).strftime("%Y-%m-%d")
        for f in files:
            if f.split("/")[1] < day:
                continue
            for r in _csv(f):
                if r.get("close_time") == iso:
                    rows.append(r)
        _BOOK[H] = rows
    best = {}
    lo, hi = (t_end - 60) * 1000, t_end * 1000
    for r in _BOOK[H]:
        ms = int(r["poll_ts_local_ms"])
        if not (lo < ms <= hi) or r.get("yes_bid_px_1") in (None, "") or r.get("no_bid_px_1") in (None, ""):
            continue
        k = float(r["strike"])
        if k not in best or ms > best[k][0]:
            best[k] = (ms, float(r["yes_bid_px_1"]), round(1 - float(r["no_bid_px_1"]), 6))
    return {k: (b, a, 1.0) for k, (ms, b, a) in best.items()} or None


def forward_eval(window, params):
    if window.get("series") != BTC:
        return None
    close = window["close_ts"]
    if close % 3600 not in (1800, 2700):
        return None
    cs = window["candles"]
    c = {SIG: cs.get(close + SIG), FILL: cs.get(close + FILL)}
    if c[SIG] is None or c[FILL] is None:
        raise NoData("no 15 minute candle at the first or second minute")
    c = {k: (v[0], v[1], v[2]) for k, v in c.items()}
    H = close - close % 3600 + 3600
    q = _ladder_at(H, close + SIG)
    if not q:
        raise NoData("no ladder poll in the signal minute (book recorder)")
    d, why = decide(close, window.get("strike"), c, q)
    if why == "gap":
        raise NoData("ladder does not bracket the 15 minute strike")
    if not d:
        return None
    return {"side": d["side"], "entry": float(d["entry"]), "exit": None, "t": close + FILL, "zero_volume": d["zv"],
            "note": f"ladder p {d['p']:.3f}, signal ask {d['a_sig']:.2f}"}


if __name__ == "__main__":
    if sys.argv[1] == "holdout":
        holdout()
