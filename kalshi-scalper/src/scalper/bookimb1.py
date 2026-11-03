"""BOOKIMB1 (workers/BOOKIMB1_REGISTRATION.md): five-level book depth imbalance as the filter on the cheap tail taker trade (ask 3c to 30c)
of the hourly Bitcoin ladder KXBTCD, 25 minutes before the close, held to settlement. Book only (no tape). Research only; no promote verb.
    python -m scalper.bookimb1 count   (trades and ON/OFF counts; no outcome is read)
    python -m scalper.bookimb1 run     (scores DEV once; the holdout only if DEV passes; writes data/bookimb1_result.txt)
    python -m scalper.bookimb1 forward [--force-info]   (see bookimb1_fwd.py)
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
"""
from __future__ import annotations

import sys

from . import makertail1 as mt
from .mm1 import central_date, clustered_z, pf
from .paths import DATA_DIR

RESULT = DATA_DIR / "bookimb1_result.txt"
ASK_LO, ASK_HI, MIN_ASK_SIZE, WINDOW_TICKS, TICK = 0.03, 0.30, 10.0, 3, 0.01
NEEDED, Z_BAR = 150, 5.27
LOOK_S, LOOK_MAX_AGE_S, LIVE_DELAY_S = mt.LOOK_S, mt.LOOK_MAX_AGE_S, mt.LIVE_DELAY_S
DEV_FROM, DEV_TO, HOLD_FROM, HOLD_TO, FWD_FROM = mt.DEV_FROM, mt.DEV_TO, mt.HOLD_FROM, mt.HOLD_TO, mt.FWD_FROM


def depth_near_best(px, sz, ticks=WINDOW_TICKS):
    """Sum of sizes at levels within `ticks` ticks of the best (highest) bid. 0.0 for an empty side."""
    if not px:
        return 0.0
    best = max(px)
    return float(sum(s for p, s in zip(px, sz) if p >= best - ticks * TICK - 1e-9))


def imbalance(own_px, own_sz, opp_px, opp_sz):
    """(D_own - D_opp) / (D_own + D_opp) in [-1, 1]; None when the opposite side has no bid (no ask) or both are empty."""
    if not opp_px:
        return None
    d_own, d_opp = depth_near_best(own_px, own_sz), depth_near_best(opp_px, opp_sz)
    tot = d_own + d_opp
    return None if tot <= 0 else (d_own - d_opp) / tot


def feature_on(imb):
    """Registered sign, fixed before any outcome: ON when imb > 0 strictly."""
    return imb is not None and imb > 0


class Trade:
    def __init__(self, ticker, close, side, ask_look, imb, ask, ask_size):
        self.ticker, self.close, self.side, self.ask_look, self.imb = ticker, close, side, ask_look, imb
        self.ask, self.ask_size, self.won = ask, ask_size, None
        self.on = feature_on(imb)

    @property
    def ok(self):
        return self.ask is not None and ASK_LO - 1e-9 <= self.ask <= ASK_HI + 1e-9 and (self.ask_size or 0) >= MIN_ASK_SIZE


def candidates_at_close(per_ticker_polls, close):
    """per_ticker_polls {ticker: [Poll]}. Returns the Trade list (<= 1 per side) for one close, before NoFill filtering.
    Per side, the candidate with the highest look ask in [0.03, 0.30]; ties by the lower ticker string."""
    target = close - LOOK_S
    best = {}
    for tk in sorted(per_ticker_polls):
        polls = per_ticker_polls[tk]
        look = None
        for p in polls:
            if p.t <= target:
                look = p
            else:
                break
        if look is None or target - look.t > LOOK_MAX_AGE_S:
            continue
        live = look.t + LIVE_DELAY_S
        fillp = next((p for p in polls if p.t >= live and p.t - live <= LOOK_MAX_AGE_S), None)
        for side, own_px, own_sz, opp_px, opp_sz in (("yes", look.yp, look.ys, look.np, look.ns), ("no", look.np, look.ns, look.yp, look.ys)):
            if not opp_px:
                continue
            ask = round(1 - max(opp_px), 4)
            if not (ASK_LO - 1e-9 <= ask <= ASK_HI + 1e-9):
                continue
            if side in best and best[side][0] >= ask - 1e-9:
                continue                                   # strictly higher ask wins; ties keep the lower ticker (sorted order)
            imb = imbalance(own_px, own_sz, opp_px, opp_sz)
            if imb is None:
                continue
            fa = fs = None
            if fillp is not None:
                fpx, fsz = (fillp.np, fillp.ns) if side == "yes" else (fillp.yp, fillp.ys)
                if fpx:
                    fa, fs = round(1 - max(fpx), 4), fsz[fpx.index(max(fpx))]
            best[side] = (ask, Trade(tk, close, side, ask, imb, fa, fs))
    return [v[1] for v in best.values()]


def fee_per_contract(p):
    return mt.taker_fee_per_contract(p)


def net_cents(t, mult=1.0):
    return 100 * ((1 if t.won else 0) - t.ask - mult * fee_per_contract(t.ask))


def summarise(trades, mult=1.0):
    rows = [t for t in trades if t.ok and t.won is not None]
    nets = [net_cents(t, mult) for t in rows]
    keys = [central_date(t.close) for t in rows]
    return {"n": len(rows), "win": sum(1 for t in rows if t.won) / len(rows) if rows else 0.0,
            "price": sum(t.ask for t in rows) / len(rows) if rows else 0.0,
            "mean": sum(nets) / len(nets) if nets else 0.0, "pf": pf(nets),
            "z": clustered_z(nets, keys) if nets else 0.0}


def split(trades):
    return [t for t in trades if t.on], [t for t in trades if not t.on]


def verdict(dev_trades, h1, h2):
    on, off = split(dev_trades)
    non = sum(1 for t in on if t.ok and t.won is not None)
    if non < NEEDED:
        return "NOT_ENOUGH_DATA"
    for half in (h1, h2):
        hon, hoff = split(half)
        a, b = summarise(hon), summarise(hoff)
        if a["pf"] < 1.5 or not (a["mean"] - b["mean"] > 0):
            return "FALSIFIED"
    return "NOT_YET_FALSIFIED"


def verdict_kill(dev_trades, h1, h2):
    """FALSIFIED check that ignores the sample-size gate (used to print what the kill rule would say, information only)."""
    for half in (h1, h2):
        hon, hoff = split(half)
        a, b = summarise(hon), summarise(hoff)
        if a["pf"] < 1.5 or not (a["mean"] - b["mean"] > 0):
            return "kill rule met"
    return "kill rule not met"


def build(span, with_outcome):
    polls, closes, _tr, _tp = mt.load()
    res = mt.results() if with_outcome else {}
    by_close = {}
    for tk, cl in closes.items():
        if span[0] <= cl < span[1]:
            by_close.setdefault(cl, {})[tk] = polls[tk]
    out = []
    for cl in sorted(by_close):
        for t in candidates_at_close(by_close[cl], cl):
            if with_outcome:
                r = res.get(t.ticker)
                t.won = None if r not in ("yes", "no") else (r == t.side)
            out.append(t)
    return out


def fmt(s):
    return "n %d win %.1f%% at mean ask %.1f%% per trade %+.2fc PF %.2f z %.2f" % (s["n"], 100 * s["win"], 100 * s["price"], s["mean"], s["pf"], s["z"])


def report_lines(trades, label):
    cut_set = sorted({t.close for t in trades if t.ok})
    cut = cut_set[len(cut_set) // 2] if cut_set else 0
    h1, h2 = [t for t in trades if t.close < cut], [t for t in trades if t.close >= cut]
    on, off = split(trades)
    L = ["%s: %d candidate trades, %d tradable (ask in 3c-30c at the fill poll, size>=10), %d without a result" % (
        label, len(trades), sum(1 for t in trades if t.ok), sum(1 for t in trades if t.ok and t.won is None))]
    for m in (1.0, 1.2):
        L.append("fee x%.1f  ON : %s" % (m, fmt(summarise(on, m))))
        L.append("fee x%.1f  OFF: %s" % (m, fmt(summarise(off, m))))
    for nm, hh in (("H1", h1), ("H2", h2)):
        a, b = split(hh)
        sa, sb = summarise(a), summarise(b)
        L.append("%s ON : %s | OFF: %s | ON-OFF %+.2fc" % (nm, fmt(sa), fmt(sb), sa["mean"] - sb["mean"]))
    for side in ("yes", "no"):
        a, b = split([t for t in trades if t.side == side])
        L.append("%s side  ON : %s" % (side.upper(), fmt(summarise(a))))
        L.append("%s side  OFF: %s" % (side.upper(), fmt(summarise(b))))
    return L, h1, h2


def count():
    for name, span in (("DEV", (DEV_FROM, DEV_TO)), ("HOLDOUT", (HOLD_FROM, HOLD_TO)), ("FORWARD", (FWD_FROM, 4e9))):
        t = build(span, False)
        ok = [x for x in t if x.ok]
        print(name, "candidates", len(t), "tradable", len(ok), "ON", sum(1 for x in ok if x.on), "OFF", sum(1 for x in ok if not x.on),
              "closes", len({x.close for x in t}), "yes", sum(1 for x in ok if x.side == "yes"), "no", sum(1 for x in ok if x.side == "no"))


def run():
    if RESULT.exists():
        sys.exit("refused: BOOKIMB1 DEV was already scored once (data/bookimb1_result.txt)")
    dev = build((DEV_FROM, DEV_TO), True)
    L, h1, h2 = report_lines(dev, "BOOKIMB1 DEV (closes 2026-10-29 to 2026-11-01)")
    v = verdict(dev, h1, h2)
    on = summarise(split(dev)[0])
    L.append("VERDICT: " + v + " (information: " + verdict_kill(dev, h1, h2) + " if the ON-trade gate were ignored)")
    days = max(1, len({central_date(t.close) for t in dev}))
    L.append("ON trades per day %.1f; days to %d ON trades %.0f" % (on["n"] / days, NEEDED, NEEDED / max(on["n"] / days, 1e-9)))
    if v == "NOT_YET_FALSIFIED":
        ho = build((HOLD_FROM, HOLD_TO), True)
        a, b = split(ho)
        L.append("HOLDOUT ON : " + fmt(summarise(a)))
        L.append("HOLDOUT OFF: " + fmt(summarise(b)))
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
        from . import bookimb1_fwd
        sys.exit(bookimb1_fwd.main(argv))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
