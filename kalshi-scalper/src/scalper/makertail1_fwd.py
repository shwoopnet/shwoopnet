"""MAKERTAIL1 forward read (workers/MAKERTAIL1_REGISTRATION.md, Amendment 1). Research only; nothing here means trade; no promote verb.

    python -m scalper.makertail1_fwd forward [--force-info]     (also: python -m scalper.makertail1 forward)

Reads ONLY closes from 2026-11-03 16:00Z (makertail1.FWD_FROM) up to the read time, with makertail1's own DEV code path (make_orders, tape_gap, filled, summarise,
verdict). DEV and HOLDOUT closes are never touched (asserted). Reports the combined result under the pessimistic and optimistic bounds, then the YES-side tails
and NO-side tails separately under both bounds (Amendment 1). Refuses before 2026-11-12, refuses until 150 pessimistic forward fills exist (the registration says
"whichever is later"), refuses a second read, prints the README line to append.
"""
from __future__ import annotations

import sys

from . import fwdread as fr
from . import makertail1 as mt
from .mm1 import central_date

SPEC = fr.Spec(
    id="MAKERTAIL1F",
    title="forward read of the far-tail resting buy on KXBTCD, closes from 2026-11-03 16:00Z (with the Amendment 1 YES/NO side split)",
    sources=["workers/MAKERTAIL1_REGISTRATION.md"],
    rule=[
        "**FALSIFIED:** mean net per resting order not above 0 under the PESSIMISTIC bound in DEV, or PF on pessimistic fills under 1.5, or either half of DEV not positive.",
        "**NOT_ENOUGH_DATA:** under 150 pessimistic fills in DEV.",
        "the same rule on closes from 2026-11-03 16:00Z, read once on 2026-11-12 (or when 150 pessimistic forward fills exist, whichever is later)",
        "the side result counts only if the COMBINED forward pessimistic net per resting order and the NO-side forward pessimistic net per resting order are both above 0, with at least 150 forward pessimistic fills on EACH side.",
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
        for o in mt.make_orders(tk, cl, polls[tk]):
            o.gap = mt.tape_gap(o, tpolls)
            for b in ("pess", "opt", "mid"):
                o.fill[b] = mt.filled(o, trades.get(tk, []), b)
            if with_result:
                r = res.get(tk)
                o.won = None if r not in ("yes", "no") else (r == o.side)
            out.append(o)
    return out


def side_claim(orders):
    """Amendment 1 counting rule, applied to the pessimistic bound. Returns (word, detail)."""
    comb = mt.summarise(orders, "pess")
    yes = mt.summarise([o for o in orders if o.side == "yes"], "pess")
    no = mt.summarise([o for o in orders if o.side == "no"], "pess")
    if yes["fills"] < mt.NEEDED or no["fills"] < mt.NEEDED:
        return "NOT_ENOUGH_DATA", f"YES fills {yes['fills']}, NO fills {no['fills']}, needs {mt.NEEDED} on EACH side"
    if comb["per_order"] > 0 and no["per_order"] > 0:
        return "CLAIM_COUNTS", f"combined {comb['per_order']:+.2f}c and NO {no['per_order']:+.2f}c per resting order, both above 0 (a count, not a pass: z bar {mt.Z_BAR})"
    return "FALSIFIED", f"combined {comb['per_order']:+.2f}c, NO {no['per_order']:+.2f}c per resting order; both must be above 0"


def report(orders, lo_ts, hi_ts):
    mid = sorted({o.close for o in orders if o.won is not None})
    cut = mid[len(mid) // 2] if mid else 0
    h1, h2 = [o for o in orders if o.close < cut], [o for o in orders if o.close >= cut]
    S = {b: mt.summarise(orders, b) for b in ("pess", "opt", "mid")}
    L = [f"MAKERTAIL1 FORWARD closes {fr.day_of(lo_ts)} 16:00Z to {fr.day_of(hi_ts)}: {len(orders)} orders, {sum(1 for o in orders if o.won is None)} without a result"]
    for b in ("pess", "opt", "mid"):
        L.append(f"{b}: {mt.fmt(S[b])}")
    L.append("pess halves: H1 " + mt.fmt(mt.summarise(h1, "pess")))
    L.append("            H2 " + mt.fmt(mt.summarise(h2, "pess")))
    for side in ("yes", "no"):
        sub = [o for o in orders if o.side == side]
        for b in ("pess", "opt"):
            L.append(f"{side.upper()}-side tails, {b}: " + mt.fmt(mt.summarise(sub, b)))
    for m in (1.0, 1.2):
        t = mt.taker_summary(orders, m)
        L.append("taker at the ask (fee x%.1f, size>=10): orders %d win %.1f%% at mean ask %.1f%% per order %+.2fc PF %.2f" % (m, t["orders"], 100 * t["win"], 100 * t["price"], t["per_order"], t["pf"]))
    v = mt.verdict(S["pess"], mt.summarise(h1, "pess"), mt.summarise(h2, "pess"))
    sw, sd = side_claim(orders)
    L.append(f"VERDICT (pessimistic bound, combined): {v}")
    L.append(f"SIDE CLAIM (NO tails beat YES tails, Amendment 1): {sw}: {sd}")
    L.append(f"day-clustered z {S['pess']['z']:.2f} against the registered bar {mt.Z_BAR}; a result under the bar is not a pass. No promote verb.")
    body = (f"window closes {fr.day_of(lo_ts)} 16:00Z to {fr.day_of(hi_ts)}; n {S['pess']['orders']} resting orders on {len({central_date(o.close) for o in orders})} days, pess fills {S['pess']['fills']} "
            f"(YES {mt.summarise([o for o in orders if o.side == 'yes'], 'pess')['fills']}, NO {mt.summarise([o for o in orders if o.side == 'no'], 'pess')['fills']}); cost maker fee 0, taker comparison fee x1.0 and x1.2; "
            f"pess PF {fr.fpf(S['pess']['pf'])}, per order {S['pess']['per_order']:+.2f}c, z {S['pess']['z']:.2f} vs bar {mt.Z_BAR}; opt per order {S['opt']['per_order']:+.2f}c; "
            f"VERDICT {v}; side claim {sw} ({sd})")
    return L, body


def forward(argv, now=None):
    now_ = now or fr.datetime.now(fr.UTC)
    hi = now_.timestamp()

    def info():
        o = forward_orders(hi, False)
        pess = sum(1 for x in o if x.fill.get("pess") and not x.gap)
        return [f"forward orders {len(o)} (YES {sum(1 for x in o if x.side == 'yes')}, NO {sum(1 for x in o if x.side == 'no')}); pessimistic fills so far {pess} of the {mt.NEEDED} needed (fills need the tape, not a result)"]

    def ready(n):
        o = forward_orders(hi, True)
        fills = mt.summarise(o, "pess")["fills"]
        return None if fills >= mt.NEEDED else f"only {fills} settled pessimistic forward fills; the registration says read on 2026-11-12 or at {mt.NEEDED} fills, whichever is later"

    return fr.run(SPEC, argv, lambda: report(forward_orders(hi, True), mt.FWD_FROM, hi), info, now=now_, ready=ready)


main = fr.cli(forward)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
