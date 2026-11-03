"""MAKERMID1 (workers/MAKERMID1_REGISTRATION.md): MAKERTAIL1's resting-bid model for the cheap-side mid band 16c to 40c of the
hourly Bitcoin ladder (KXBTCD), held to settlement. Two rules: MR1 base, MR2 cancel when the bid falls 2c or more before the fill.
OWNER RULE: no bid above 40c is ever placed, scored or printed; the taker comparison is limited to asks at or below 40c.
Research only; there is no promote verb.
    python -m scalper.makermid1 count | run | forward [--force-info]
"""
from __future__ import annotations

import copy
import sys

from . import makertail1 as mt
from .mm1 import central_date

RESULT = mt.DATA_DIR / "makermid1_result.txt"
BAND = (0.16, 0.40)
DROP = 0.02
BOUNDS = ("pess", "opt", "mid")


def make_orders(ticker, close, polls):
    """MAKERTAIL1's own order construction with this band; its band constant is swapped only for the call, and every order is re-checked."""
    old = mt.BAND
    mt.BAND = BAND
    try:
        out = mt.make_orders(ticker, close, polls)
    finally:
        mt.BAND = old
    for o in out:
        assert BAND[0] - 1e-9 <= o.price <= BAND[1] + 1e-9 and o.price <= 0.40 + 1e-9
        if o.ask is not None and o.ask > 0.40 + 1e-9:
            o.ask = o.ask_size = None          # never a column above 40c
        o.cancel_t = cancel_time(o, polls)
    return out


def cancel_time(order, polls):
    """MR2: time of the first poll after the order is live at which our side's best bid is at or below price - 0.02 (or the side is empty)."""
    live = order.look_t + mt.LIVE_DELAY_S
    for p in polls:
        if p.t <= live or p.t > order.close - mt.CANCEL_S:
            continue
        px = p.yp if order.side == "yes" else p.np
        if not px or px[0] <= order.price - DROP + 1e-9:
            return p.t
    return None


def fill_time(order, trades, bound):
    """Time of the first fill under the bound, or None. Same arithmetic as makertail1.filled, which returns only a bool."""
    if bound != "opt" and order.gap:
        return None
    t0, t1 = order.look_t + mt.LIVE_DELAY_S, order.close - mt.CANCEL_S
    ahead = {"pess": order.q0, "opt": 0.0, "mid": order.q0 / 2}[bound]
    cum = 0.0
    for t, yp, c, side in sorted(trades):
        if t <= t0 or t > t1:
            continue
        if order.side == "yes":
            if side != "no":
                continue
            px = yp
        else:
            if side != "yes":
                continue
            px = 1 - yp
        if px < order.price - 1e-9:
            return t
        if abs(px - order.price) < 1e-9:
            cum += c
            if cum > ahead + 1e-9 or bound == "opt":
                return t
    return None


def score_fills(order, trades):
    for b in BOUNDS:
        t = fill_time(order, trades, b)
        order.fill[b] = t is not None
        order.fill[b + "_g"] = t is not None and (order.cancel_t is None or t < order.cancel_t)


def guard_view(orders):
    """Copies whose fill dict carries the MR2 (guarded) fills under the plain bound names, so makertail1.summarise applies unchanged."""
    out = []
    for o in orders:
        c = copy.copy(o)
        c.fill = {b: o.fill.get(b + "_g", False) for b in BOUNDS}
        out.append(c)
    return out


def build(span, with_outcome):
    polls, closes, trades, tpolls = mt.load()
    res = mt.results() if with_outcome else {}
    orders = []
    for tk, cl in closes.items():
        if not (span[0] <= cl < span[1]):
            continue
        for o in make_orders(tk, cl, polls[tk]):
            o.gap = mt.tape_gap(o, tpolls)
            if with_outcome:
                r = res.get(tk)
                o.won = None if r not in ("yes", "no") else (r == o.side)
                score_fills(o, trades.get(tk, []))
            orders.append(o)
    return orders


def taker_summary(orders, mult=1.0):
    return mt.taker_summary([o for o in orders if o.ask is not None and o.ask <= 0.40 + 1e-9], mult)


def buckets(orders, bound):
    out = []
    for lo, hi in ((0.16, 0.25), (0.26, 0.33), (0.34, 0.40)):
        sub = [o for o in orders if lo - 1e-9 <= o.price <= hi + 1e-9]
        out.append("  bid %2d-%2dc: %s" % (round(lo * 100), round(hi * 100), mt.fmt(mt.summarise(sub, bound))))
    return out


def rule_lines(name, orders, h1, h2):
    S = {b: mt.summarise(orders, b) for b in BOUNDS}
    L = [f"--- {name} ---"]
    for b in BOUNDS:
        L.append(f"{b}: {mt.fmt(S[b])}")
    L.append("pess halves: H1 " + mt.fmt(mt.summarise(h1, "pess")))
    L.append("            H2 " + mt.fmt(mt.summarise(h2, "pess")))
    for side in ("yes", "no"):
        sub = [o for o in orders if o.side == side]
        for b in ("pess", "opt"):
            L.append(f"{side.upper()} side, {b}: {mt.fmt(mt.summarise(sub, b))}")
    L.append("pess by bid price:")
    L += buckets(orders, "pess")
    L.append("opt by bid price:")
    L += buckets(orders, "opt")
    v = mt.verdict(S["pess"], mt.summarise(h1, "pess"), mt.summarise(h2, "pess"))
    L.append(f"{name} VERDICT (pessimistic bound): {v}")
    return L, S, v


def report(orders, header):
    cl = sorted({o.close for o in orders})
    cut = cl[len(cl) // 2] if cl else 0
    h1, h2 = [o for o in orders if o.close < cut], [o for o in orders if o.close >= cut]
    L = [header]
    l1, S1, v1 = rule_lines("MR1", orders, h1, h2)
    l2, S2, v2 = rule_lines("MR2 (cancel on a 2c bid drop)", guard_view(orders), guard_view(h1), guard_view(h2))
    L += l1 + l2
    for m in (1.0, 1.2):
        t = taker_summary(orders, m)
        L.append("taker at the ask (ask<=40c, fee x%.1f, size>=10): orders %d win %.1f%% at mean ask %.1f%% per order %+.2fc PF %.2f"
                 % (m, t["orders"], 100 * t["win"], 100 * t["price"], t["per_order"], t["pf"]))
    days = max(1, len({central_date(o.close) for o in orders}))
    for nm, S in (("MR1", S1), ("MR2", S2)):
        rate = max(S["pess"]["fills"] / days, 1e-9)
        L.append(f"{nm} pessimistic fills per day {rate:.1f}; days to {mt.NEEDED} fills {mt.NEEDED / rate:.0f}; day z {S['pess']['z']:.2f} vs bar {mt.Z_BAR}")
    return L, v1, v2


def count():
    for name, span in (("DEV", (mt.DEV_FROM, mt.DEV_TO)), ("HOLDOUT", (mt.HOLD_FROM, mt.HOLD_TO)), ("FORWARD", (mt.FWD_FROM, 4e9))):
        o = build(span, False)
        print(name, "orders", len(o), "closes", len({x.close for x in o}), "yes", sum(1 for x in o if x.side == "yes"), "no", sum(1 for x in o if x.side == "no"))


def run():
    if RESULT.exists():
        sys.exit("refused: MAKERMID1 DEV was already scored once (data/makermid1_result.txt)")
    dev = build((mt.DEV_FROM, mt.DEV_TO), True)
    L, v1, v2 = report(dev, "MAKERMID1 DEV (closes 2026-10-29 to 2026-11-01), %d orders, %d without a result" % (len(dev), sum(1 for o in dev if o.won is None)))
    if "NOT_YET_FALSIFIED" in (v1, v2):
        ho = build((mt.HOLD_FROM, mt.HOLD_TO), True)
        L.append("HOLDOUT pess MR1: " + mt.fmt(mt.summarise(ho, "pess")))
        L.append("HOLDOUT pess MR2: " + mt.fmt(mt.summarise(guard_view(ho), "pess")))
    else:
        L.append("HOLDOUT not opened (no rule passed DEV)")
    RESULT.write_text("\n".join(L) + "\n")
    print("\n".join(L))


def main(argv):
    if len(argv) > 1 and argv[1] == "count":
        count()
    elif len(argv) > 1 and argv[1] == "run":
        run()
    elif len(argv) > 1 and argv[1] == "forward":
        from . import makermid1_fwd
        sys.exit(makermid1_fwd.main(argv))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
