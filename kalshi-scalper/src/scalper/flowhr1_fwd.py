"""FLOWHR1 forward read (workers/FLOWHR1_REGISTRATION.md). Research only; nothing here means trade; no promote verb.

    python -m scalper.flowhr1_fwd forward [--force-info]     (also: python -m scalper.flowhr1 forward)

Reads ONLY closes from 2026-11-03 16:00Z up to the read time, with flowhr1's own code path. DEV and HOLDOUT are never touched (asserted). Read once, when 150
low-flow trades with a result exist or on 2026-12-15, whichever comes first. Prints the README line to append.
"""
from __future__ import annotations

import sys

from . import flowhr1 as fh
from . import fwdread as fr

DUE = fr.utc(2026, 12, 15)

SPEC = fr.Spec(
    id="FLOWHR1F",
    title="forward read of signed taker flow on cheap-tail taker buys of KXBTCD, closes from 2026-11-03 16:00Z",
    sources=["workers/FLOWHR1_REGISTRATION.md"],
    rule=[
        "**NOT_ENOUGH_DATA:** under 150 low-flow trades with a result in the window.",
        "**FALSIFIED:** (low-flow PF under 1.5 after the fee in EITHER half) OR (mean net per contract of the low-flow set minus that of the high-flow set not above 0).",
        "read ONCE when 150 low-flow trades with a result exist or on 2026-12-15, whichever comes first",
    ],
    window=[
        "closes of KXBTCD tickers in [2026-11-03 16:00Z, read time) from origin/quote-data book/ (git history), outcomes from data/conf2_lad.sqlite",
        "DEV (2026-10-29 to 2026-11-02 00:00Z) and HOLDOUT (2026-11-02 to 2026-11-03 16:00Z) are not read (asserted in code)",
    ],
    due=None,
    due_note="at 150 low-flow trades with a result, or on 2026-12-15, whichever comes first",
)


def forward_tails(hi_ts, with_result):
    assert fh.FWD_FROM >= fh.HOLD_TO, "the forward window must start at or after the end of the holdout"
    return fh.build((fh.FWD_FROM, hi_ts), with_result)


def forward(argv, now=None):
    now_ = now or fr.datetime.now(fr.UTC)
    hi = now_.timestamp()

    def info():
        o = forward_tails(hi, False)
        c = {k: sum(1 for t in o if t.group == k) for k in ("low", "high", "noflow", "nodata")}
        return [f"forward selected tails {len(o)} {c}; low-flow trades need a result: {fh.NEEDED} wanted, or the read happens on 2026-12-15"]

    def ready(n):
        if n >= DUE:
            return None
        low = sum(1 for t in forward_tails(hi, True) if t.won is not None and t.group == "low")
        return None if low >= fh.NEEDED else f"only {low} settled low-flow forward trades; read at {fh.NEEDED} or on 2026-12-15"

    def real():
        o = forward_tails(hi, True)
        L, w = fh.report_lines(o, f"FLOWHR1 FORWARD closes 2026-11-03 16:00Z to {fr.day_of(hi)}")
        L.append("day-clustered z against the registered bar %.2f; a result under the bar is not a pass. No promote verb." % fh.Z_BAR)
        ok = [t for t in o if t.won is not None]
        g = fh.groups(ok)
        body = (f"closes 2026-11-03 16:00Z to {fr.day_of(hi)}; low-flow {fh.fmt(fh.summarise(g['low']))}; high-flow {fh.fmt(fh.summarise(g['high']))}; VERDICT {w}")
        return L, body

    return fr.run(SPEC, argv, real, info, now=now_, ready=ready)


main = fr.cli(forward)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
