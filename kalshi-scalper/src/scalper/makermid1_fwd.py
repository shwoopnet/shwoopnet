"""MAKERMID1 forward read (workers/MAKERMID1_REGISTRATION.md). Research only; nothing here means trade; no promote verb.

    python -m scalper.makermid1 forward [--force-info]

Reads ONLY closes from 2026-11-03 16:00Z (makertail1.FWD_FROM) to the read time, with makermid1's DEV code path (band 16c to 40c, MR1 and MR2).
DEV and HOLDOUT closes are never touched (asserted). Refuses before 2026-11-12 and until 150 pessimistic forward fills exist under MR1 (whichever is
later), refuses a second read (fwdread guard), prints the README line to append. No bid above 40c is ever built or printed.
"""
from __future__ import annotations

import sys

from . import fwdread as fr
from . import makermid1 as mm
from . import makertail1 as mt
from .mm1 import central_date

SPEC = fr.Spec(
    id="MAKERMID1F",
    title="forward read of the mid-band (16c to 40c) resting buy on KXBTCD, closes from 2026-11-03 16:00Z, rules MR1 and MR2",
    sources=["workers/MAKERMID1_REGISTRATION.md"],
    rule=[
        "**FALSIFIED:** mean net per resting order not above 0 in DEV, or PF on pessimistic fills under 1.5, or either DEV half not positive.",
        "**NOT_ENOUGH_DATA:** under 150 pessimistic fills in DEV",
        "FORWARD = closes from 2026-11-03 16:00Z, read once on 2026-11-12 (or at 150 pessimistic forward fills, whichever is later)",
        "Every resting bid is at or below 40c (cheap side of its strike only).",
    ],
    window=[
        "closes of KXBTCD tickers in [2026-11-03 16:00Z, read time) from origin/quote-data book/ (git history), outcomes from data/conf2_lad.sqlite",
        "DEV (2026-10-29 to 2026-11-02 00:00Z) and HOLDOUT (2026-11-02 to 2026-11-03 16:00Z) are not read (asserted in code)",
    ],
    due=fr.utc(2026, 11, 12),
    due_note="and 150 pessimistic forward fills; whichever is later",
)


def forward_orders(hi_ts, with_result):
    lo = mt.FWD_FROM
    assert lo >= mt.HOLD_TO, "the forward window must start at or after the end of the holdout"
    polls, closes, trades, tpolls = mt.load()
    res = mt.results() if with_result else {}
    out = []
    for tk, cl in closes.items():
        if not (lo <= cl < hi_ts):
            continue
        for o in mm.make_orders(tk, cl, polls[tk]):
            o.gap = mt.tape_gap(o, tpolls)
            mm.score_fills(o, trades.get(tk, []))
            if with_result:
                r = res.get(tk)
                o.won = None if r not in ("yes", "no") else (r == o.side)
            out.append(o)
    return out


def report(orders, lo_ts, hi_ts):
    L, v1, v2 = mm.report(orders, f"MAKERMID1 FORWARD closes {fr.day_of(lo_ts)} 16:00Z to {fr.day_of(hi_ts)}: {len(orders)} orders, {sum(1 for o in orders if o.won is None)} without a result")
    S1, S2 = mt.summarise(orders, "pess"), mt.summarise(mm.guard_view(orders), "pess")
    L.append("day-clustered z against the registered bar %.2f; a result under the bar is not a pass. No promote verb." % mt.Z_BAR)
    body = (f"window closes {fr.day_of(lo_ts)} 16:00Z to {fr.day_of(hi_ts)}; n {S1['orders']} resting orders on {len({central_date(o.close) for o in orders})} days; "
            f"MR1 pess fills {S1['fills']}, per order {S1['per_order']:+.2f}c, PF {fr.fpf(S1['pf'])}, z {S1['z']:.2f}, VERDICT {v1}; "
            f"MR2 pess fills {S2['fills']}, per order {S2['per_order']:+.2f}c, PF {fr.fpf(S2['pf'])}, z {S2['z']:.2f}, VERDICT {v2}; bar {mt.Z_BAR}; cost maker fee 0")
    return L, body


def forward(argv, now=None):
    now_ = now or fr.datetime.now(fr.UTC)
    hi = now_.timestamp()

    def info():
        o = forward_orders(hi, False)
        pess = sum(1 for x in o if x.fill.get("pess") and not x.gap)
        return [f"forward orders {len(o)} (YES {sum(1 for x in o if x.side == 'yes')}, NO {sum(1 for x in o if x.side == 'no')}); MR1 pessimistic fills so far {pess} of {mt.NEEDED} needed"]

    def ready(n):
        fills = mt.summarise(forward_orders(hi, True), "pess")["fills"]
        return None if fills >= mt.NEEDED else f"only {fills} settled pessimistic forward fills; read on 2026-11-12 or at {mt.NEEDED} fills, whichever is later"

    return fr.run(SPEC, argv, lambda: report(forward_orders(hi, True), mt.FWD_FROM, hi), info, now=now_, ready=ready)


main = fr.cli(forward)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
