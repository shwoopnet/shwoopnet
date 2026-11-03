"""BOOKIMB1 forward read (workers/BOOKIMB1_REGISTRATION.md). Research only; nothing here means trade; no promote verb.

    python -m scalper.bookimb1_fwd forward [--force-info]     (also: python -m scalper.bookimb1 forward)

Reads ONLY closes from 2026-11-03 16:00Z (bookimb1.FWD_FROM) up to the read time with bookimb1's own DEV code path. Read ONCE, on the first moment
150 settled ON trades exist, or on 2026-12-15 if fewer by then. Refuses a second read; prints the README line to append.
"""
from __future__ import annotations

import sys

from . import bookimb1 as bi
from . import fwdread as fr
from .mm1 import central_date

DEADLINE = fr.utc(2026, 12, 15)

SPEC = fr.Spec(
    id="BOOKIMB1F",
    title="forward read of the book depth imbalance filter on the cheap KXBTCD tail, closes from 2026-11-03 16:00Z",
    sources=["workers/BOOKIMB1_REGISTRATION.md"],
    rule=[
        "**NOT_ENOUGH_DATA:** under 150 ON trades in DEV (checked first).",
        "**FALSIFIED:** the ON group's PF after fees (C = 10, fee x1.0) is under 1.5 in either DEV half, OR (ON per-trade mean minus OFF per-trade mean) is not above 0 in both DEV halves.",
        "read ONCE, on the first moment 150 settled ON trades exist in the forward set, or on 2026-12-15 if fewer by then",
    ],
    window=[
        "closes of KXBTCD tickers in [2026-11-03 16:00Z, read time) from origin/quote-data book/ (git history), outcomes from data/conf2_lad.sqlite",
        "DEV (2026-10-29 to 2026-11-02 00:00Z) and HOLDOUT (2026-11-02 to 2026-11-03 16:00Z) are not read (asserted in code)",
    ],
    due=None,
    due_note="at 150 settled forward ON trades, or 2026-12-15 if fewer by then",
)


def forward_trades(hi_ts, with_result):
    assert bi.FWD_FROM >= bi.HOLD_TO, "the forward window must start at or after the end of the holdout"
    return bi.build((bi.FWD_FROM, hi_ts), with_result)


def report(trades, hi_ts):
    L, h1, h2 = bi.report_lines(trades, "BOOKIMB1 FORWARD closes %s 16:00Z to %s" % (fr.day_of(bi.FWD_FROM), fr.day_of(hi_ts)))
    v = bi.verdict(trades, h1, h2)
    on, off = bi.split(trades)
    a, b = bi.summarise(on), bi.summarise(off)
    L.append("VERDICT: %s; kill rule information: %s" % (v, bi.verdict_kill(trades, h1, h2)))
    L.append("day-clustered z (ON) %.2f against the registered bar %.2f; a result under the bar is not a pass. No promote verb." % (a["z"], bi.Z_BAR))
    body = ("window closes %s 16:00Z to %s; ON n %d win %.1f%% at ask %.1f%% PF %.2f per trade %+.2fc z %.2f; OFF n %d PF %.2f per trade %+.2fc; ON-OFF %+.2fc; fee x1.0, C=10; VERDICT %s"
            % (fr.day_of(bi.FWD_FROM), fr.day_of(hi_ts), a["n"], 100 * a["win"], 100 * a["price"], a["pf"], a["mean"], a["z"], b["n"], b["pf"], b["mean"], a["mean"] - b["mean"], v))
    return L, body


def forward(argv, now=None):
    now_ = now or fr.datetime.now(fr.UTC)
    hi = now_.timestamp()

    def info():
        t = forward_trades(hi, False)
        ok = [x for x in t if x.ok]
        return ["forward candidates %d, tradable %d (ON %d, OFF %d); settled ON trades need a result, 150 are needed (or 2026-12-15)"
                % (len(t), len(ok), sum(1 for x in ok if x.on), sum(1 for x in ok if not x.on))]

    def ready(n):
        if n >= DEADLINE:
            return None
        s = bi.summarise([x for x in forward_trades(hi, True) if x.on])
        return None if s["n"] >= bi.NEEDED else "only %d settled ON forward trades; the registration says read at %d or on 2026-12-15" % (s["n"], bi.NEEDED)

    return fr.run(SPEC, argv, lambda: report(forward_trades(hi, True), hi), info, now=now_, ready=ready)


main = fr.cli(forward)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
