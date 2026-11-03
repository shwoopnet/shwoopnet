"""FLOWHR1 (workers/FLOWHR1_REGISTRATION.md): signed taker flow on the contract as a filter on cheap-tail TAKER buys (ask 3c to 30c) of the
hourly Bitcoin ladder KXBTCD, 25 minutes before the close, held to settlement. Cheap side only: an ask above 0.30 is never selected or scored.
Research only; nothing here means trade; there is no promote verb.
    python -m scalper.flowhr1 count   (tails and flow availability by window; no outcome is read)
    python -m scalper.flowhr1 run     (scores DEV once; the holdout only if DEV passes; writes data/flowhr1_result.txt)
    python -m scalper.flowhr1 forward [--force-info]   (see flowhr1_fwd.py)
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
"""
from __future__ import annotations

import math
import sys

from . import makertail1 as mt
from .mm1 import central_date, clustered_z, pf

LOOK_S, LOOK_MAX_AGE_S, LIVE_DELAY_S = 1500, 20.0, 1.0
FLOW_WINDOW_S = 600
FLOW_THRESHOLD = -0.036            # fixed, cited from the S-FLOW1 lead; never tuned here
ASK_LO, ASK_HI = 0.03, 0.30        # cheap side only (hard limit 0.30)
MIN_ASK_SIZE = 10
NEEDED = 150
Z_BAR = 5.27
TAPE_GAP_S = 90.0
RESULT = mt.DATA_DIR / "flowhr1_result.txt"
DEV_FROM, DEV_TO, HOLD_FROM, HOLD_TO, FWD_FROM = mt.DEV_FROM, mt.DEV_TO, mt.HOLD_FROM, mt.HOLD_TO, mt.FWD_FROM


class Tail:
    def __init__(self, ticker, close, side, ask, ask_size, look_t, flow, nodata):
        self.ticker, self.close, self.side, self.ask, self.ask_size = ticker, close, side, ask, ask_size
        self.look_t, self.flow, self.nodata = look_t, flow, nodata   # flow None = NoFlow (no contracts); nodata True = tape hole
        self.won = None

    @property
    def group(self):
        if self.nodata:
            return "nodata"
        if self.flow is None:
            return "noflow"
        return "low" if self.flow <= FLOW_THRESHOLD else "high"


def signed_flow(trades, side, look_t):
    """trades [(t, yes_price, count, taker_outcome_side)]. Contracts takers bought on `side` minus sold, over total, in (look-600, look]. None when none traded.
    A taker who bought the OTHER side sold this one."""
    bought = sold = 0.0
    for t, _yp, c, ts in trades:
        if not (look_t - FLOW_WINDOW_S < t <= look_t):
            continue
        if ts == side:
            bought += c
        elif ts in ("yes", "no"):
            sold += c
    tot = bought + sold
    return None if tot <= 0 else (bought - sold) / tot


def window_gap(tape_polls, look_t):
    """True when the recorded tape polls leave a hole over 90 s in the flow window, or none cover it."""
    lo, hi = look_t - FLOW_WINDOW_S, look_t
    pts = sorted(t for t in tape_polls if lo - TAPE_GAP_S <= t <= hi + TAPE_GAP_S)
    if not pts or pts[0] - lo > TAPE_GAP_S or hi - pts[-1] > TAPE_GAP_S:
        return True
    return any(b - a > TAPE_GAP_S for a, b in zip(pts, pts[1:]))


def ask_of(poll, side):
    """(ask, size) of buying `side` at poll: 1 - best bid of the other side, size = that bid's displayed size."""
    px, sz = (poll.np, poll.ns) if side == "yes" else (poll.yp, poll.ys)
    return (round(1 - px[0], 4), sz[0]) if px else (None, None)


def candidates(ticker, close, polls, trades, tape_polls):
    """Eligible cheap-tail taker buys of one ticker (up to one per side): list of Tail."""
    target = close - LOOK_S
    look = None
    for p in polls:
        if p.t <= target:
            look = p
        else:
            break
    if look is None or target - look.t > LOOK_MAX_AGE_S:
        return []
    live = look.t + LIVE_DELAY_S
    fillp = next((p for p in polls if p.t >= live and p.t - live <= LOOK_MAX_AGE_S), None)
    if fillp is None:
        return []
    gap = window_gap(tape_polls, look.t)
    out = []
    for side in ("yes", "no"):
        ask, size = ask_of(fillp, side)
        if ask is None or size is None or size < MIN_ASK_SIZE or not (ASK_LO - 1e-9 <= ask <= ASK_HI + 1e-9):
            continue
        out.append(Tail(ticker, close, side, ask, size, look.t, None if gap else signed_flow(trades, side, look.t), gap))
    return out


def select(per_close):
    """per_close: [Tail] of one close. One per side: the highest ask (nearest the money, still under 0.30)."""
    best = {}
    for t in per_close:
        if t.side not in best or t.ask > best[t.side].ask:
            best[t.side] = t
    return list(best.values())


def net(t, mult=1.0):
    return 100 * ((1 if t.won else 0) - t.ask - mult * mt.taker_fee_per_contract(t.ask))


def summarise(tails, mult=1.0):
    rows = [t for t in tails if t.won is not None]
    nets = [net(t, mult) for t in rows]
    keys = [central_date(t.close) for t in rows]
    n = len(rows)
    return {"n": n, "win": sum(1 for t in rows if t.won) / n if n else 0.0, "price": sum(t.ask for t in rows) / n if n else 0.0,
            "mean": sum(nets) / n if n else 0.0, "pf": pf(nets), "z": clustered_z(nets, keys) if n else 0.0}


def fmt(s):
    return "n %d win %.1f%% at mean price paid %.1f%% net %+.2fc/contract PF %.2f z %.2f" % (s["n"], 100 * s["win"], 100 * s["price"], s["mean"], s["pf"], s["z"])


def groups(tails):
    return {"low": [t for t in tails if t.group == "low"], "high": [t for t in tails if t.group == "high"],
            "all": [t for t in tails if t.group != "nodata"]}


def verdict(tails, cut):
    """tails: selected tails with a result. cut: the close time splitting the halves. Returns (word, detail)."""
    g = groups(tails)
    low, high = summarise(g["low"]), summarise(g["high"])
    h1 = summarise([t for t in g["low"] if t.close < cut])
    h2 = summarise([t for t in g["low"] if t.close >= cut])
    diff = low["mean"] - high["mean"]
    kill = h1["pf"] < 1.5 or h2["pf"] < 1.5 or not diff > 0
    detail = "low n %d, halves PF %.2f / %.2f, low-minus-high %+.2fc" % (low["n"], h1["pf"], h2["pf"], diff)
    if low["n"] < NEEDED:
        return "NOT_ENOUGH_DATA", detail + ("; sign check only: a kill rule would already fire" if kill else "; sign check only: no kill rule fires yet")
    return ("FALSIFIED" if kill else "NOT_YET_FALSIFIED"), detail


def build(span, with_outcome):
    polls, closes, trades, tpolls = mt.load()
    res = mt.results() if with_outcome else {}
    by_close = {}
    for tk, cl in closes.items():
        if not (span[0] <= cl < span[1]):
            continue
        by_close.setdefault(cl, []).extend(candidates(tk, cl, polls[tk], trades.get(tk, []), tpolls))
    out = []
    for cl, cands in by_close.items():
        for t in select(cands):
            if with_outcome:
                r = res.get(t.ticker)
                t.won = None if r not in ("yes", "no") else (r == t.side)
            out.append(t)
    return out


def count():
    for name, span in (("DEV", (DEV_FROM, DEV_TO)), ("HOLDOUT", (HOLD_FROM, HOLD_TO)), ("FORWARD", (FWD_FROM, 4e9))):
        o = build(span, False)
        c = {k: sum(1 for t in o if t.group == k) for k in ("low", "high", "noflow", "nodata")}
        print(name, "selected tails", len(o), c, "closes", len({t.close for t in o}))


def report_lines(tails, title):
    ok = [t for t in tails if t.won is not None]
    cut = sorted({t.close for t in ok})[len({t.close for t in ok}) // 2] if ok else 0
    g = groups(ok)
    L = [f"{title}: {len(tails)} selected tails, {len(tails) - len(ok)} without a result, NoData {sum(1 for t in ok if t.group == 'nodata')}, NoFlow {sum(1 for t in ok if t.group == 'noflow')}"]
    for name in ("low", "high", "all"):
        L.append(f"{name}-flow: {fmt(summarise(g[name]))}; fee x1.2: net {summarise(g[name], 1.2)['mean']:+.2f}c PF {summarise(g[name], 1.2)['pf']:.2f}")
    L.append("low halves: H1 " + fmt(summarise([t for t in g["low"] if t.close < cut])))
    L.append("            H2 " + fmt(summarise([t for t in g["low"] if t.close >= cut])))
    for name in ("low", "high"):
        for side in ("yes", "no"):
            L.append(f"{name}-flow {side.upper()}-side: " + fmt(summarise([t for t in g[name] if t.side == side])))
    for name in ("low", "high"):
        for lo, hi in ((0.03, 0.09), (0.10, 0.19), (0.20, 0.30)):
            L.append(f"{name}-flow ask {round(lo*100)}-{round(hi*100)}c: " + fmt(summarise([t for t in g[name] if lo - 1e-9 <= t.ask <= hi + 1e-9])))
    w, d = verdict(ok, cut)
    days = max(1, len({central_date(t.close) for t in ok}))
    per_day = len(g["low"]) / days
    L.append(f"VERDICT: {w} ({d})")
    L.append(f"low-flow trades per day {per_day:.1f}; days to {NEEDED} at that rate {NEEDED / max(per_day, 1e-9):.0f}")
    return L, w


def run():
    if RESULT.exists():
        sys.exit("refused: FLOWHR1 DEV was already scored once (data/flowhr1_result.txt)")
    dev = build((DEV_FROM, DEV_TO), True)
    L, w = report_lines(dev, "FLOWHR1 DEV (closes 2026-10-29 to 2026-11-01)")
    if w == "NOT_YET_FALSIFIED":
        L += report_lines(build((HOLD_FROM, HOLD_TO), True), "FLOWHR1 HOLDOUT")[0]
    else:
        L.append("HOLDOUT not opened (DEV did not pass)")
    RESULT.write_text("\n".join(L) + "\n")
    print("\n".join(L))


def main(argv):
    if len(argv) > 1 and argv[1] == "count":
        count()
    elif len(argv) > 1 and argv[1] == "run":
        run()
    elif len(argv) > 1 and argv[1] == "forward":
        from . import flowhr1_fwd
        sys.exit(flowhr1_fwd.main(argv))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
