"""COUNT2 forward command (workers/COUNT2_REGISTRATION.md, "Forward freeze"). Research only; no promote verb.

    python -m scalper.count2_fwd forward [--force-info]

Applies the frozen COUNT2 rule (r from the one calibration, 0.5/0.5 blend, 14 day trail, climatology 2015 to 2022, look at the midpoint, 3x, hard limit 0.30, 2 per month,
fee) to KXTORNADO months starting after 2026-11-03 (the November 2026 event first, look 2026-11-16 12:00 ET). Refuses unless workers/COUNT2_RESULT.md exists and its
development verdict is NOT_ENOUGH_DATA (the freeze applies only then; the development run had not happened when this was written), refuses before 2026-11-16 17:00Z, and
refuses a real read until 40 forward trades exist. Inputs are count2's own cache (COUNT2_CACHE): c_KXTORNADO.json (market list incl. forward events), candles_tornado_fwd.json
(1 minute candles in [look-60min, look+15min] per forward market, same shape as candles_tornado.json) and count2_r.json. The development universe and its frozen holdout
(events before 2026-11) are never read: forward events are selected by period >= (2026, 11) and asserted.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from . import count2 as c2
from . import fwdread as fr

WORKERS = fr.ROOT / "workers"
FIRST = (2026, 11)
NEEDED, Z_BAR = 40, 5.27

SPEC = fr.Spec(
    id="COUNT2F",
    title="forward read of KXTORNADO monthly thresholds against SPC daily reports (months starting after 2026-11-03)",
    sources=["workers/COUNT2_REGISTRATION.md"],
    rule=[
        "A side qualifies if its FILL ask is in [0.03, 0.30] (hard limit 0.30) and its model probability is at least 3 x the fill ask.",
        "This exact rule (frozen constants r, 0.5/0.5 blend, 14 day trail, climatology 2015 to 2022, look at the midpoint, 3x, 0.30, 2 per month, fee) is frozen from this commit for months starting after 2026-11-03",
    ],
    window=["KXTORNADO events with period >= 2026-11 whose markets are all settled; look = midpoint of the ET month; candles in [look-60min, look+15min]; the development universe and its frozen last third are not read"],
    due=fr.utc(2026, 11, 16, 17),
    due_note="first forward look is 2026-11-16 12:00 ET; a real read also needs 40 forward trades",
)


def dev_gate():
    p = WORKERS / "COUNT2_RESULT.md"
    if not p.exists():
        return "workers/COUNT2_RESULT.md does not exist: the development run has not happened, and the forward freeze applies only if the development verdict is NOT_ENOUGH_DATA"
    return None if "NOT_ENOUGH_DATA" in p.read_text(errors="replace") else "COUNT2_RESULT.md does not record NOT_ENOUGH_DATA; the forward freeze applies only then"


def forward_events(markets):
    ev = {}
    for m in markets:
        ev.setdefault(m["event_ticker"], []).append(m)
    out = []
    for e, L in ev.items():
        y, mo = c2.event_period(L)
        if (y, mo) >= FIRST:
            out.append(((y, mo), e, L))
    assert all(k >= FIRST for k, _, _ in out), "the forward read must not touch the development universe or its frozen third"
    return sorted(out, key=lambda x: x[0])


def event_trades(y, mo, L, cand, r, clim):
    """Frozen rule on one forward month: up to 2 sides by p_model / ask. Markets not open at look - 60 min are skipped (as registered)."""
    look = c2.look_of(y, mo)
    if any(datetime.fromisoformat(m["open_time"].replace("Z", "+00:00")) > look - timedelta(minutes=60) for m in L):
        return []
    if not all(m.get("result") in ("yes", "no") for m in L):
        return []
    _, c, mu, pmf = c2.model(y, mo, clim, r)
    rows = []
    for m in L:
        for side in ("yes", "no"):
            q = c2.fills(cand.get(m["ticker"]) or [], look, side)
            if not q:
                continue
            pm = c2.strike_prob(m, c, pmf)
            pm = pm if side == "yes" else 1 - pm
            pay = 1.0 if (m["result"] == "yes") == (side == "yes") else 0.0
            rows.append(((m["ticker"], side), pm, q[1], pay))
    out = []
    for key, pm, ask in c2.select([(x[0], x[1], x[2]) for x in rows]):
        pay = [x[3] for x in rows if x[0] == key][0]
        out.append({"month": f"{y}-{mo:02d}", "key": key, "p": pm, "ask": ask, "net": pay - ask - c2.fee(ask)})
    return out


def all_trades():
    cache = c2.CACHE
    r = json.loads((cache / "count2_r.json").read_text())["r"]
    cand = json.loads((cache / "candles_tornado_fwd.json").read_text())
    clim = c2.climatology()
    tr = []
    for (y, mo), e, L in forward_events(c2.load_markets()):
        tr += event_trades(y, mo, L, cand, r, clim)
    return tr


def forward(argv, now=None):
    spec = SPEC
    g = dev_gate()
    if g:
        spec = fr.Spec(**{**SPEC.__dict__, "blocker": g})

    def info():
        ev = forward_events(c2.load_markets())
        return [f"forward events on file {len(ev)} ({', '.join(f'{y}-{m:02d}' for (y, m), _, _ in ev) or 'none'}); a real read needs {NEEDED} forward trades (a multi-year wait at 12 events a year)"]

    def ready(n):
        k = len(all_trades())
        return None if k >= NEEDED else f"only {k} forward trades; the real read waits for {NEEDED}"

    def real():
        tr = all_trades()
        nets = [t["net"] for t in tr]
        m, z = fr.clustered([(t["month"], t["net"]) for t in tr])
        w = "NOT_ENOUGH_DATA" if len(tr) < 150 else ("NOT_YET_FALSIFIED" if (nets and fr.pf(nets) >= 1.5 and m > 0) else "FALSIFIED")
        L = [f"COUNT2 FORWARD {w}: {len(tr)} trades on {len({t['month'] for t in tr})} months; PF {fr.fpf(fr.pf(nets)) if nets else 'n/a'}; mean {100 * m:+.2f}c; month-clustered z {z:+.2f} vs bar {Z_BAR}"]
        return L, f"months from 2026-11; n {len(tr)} trades on {len({t['month'] for t in tr})} months; cost fee 7% x C x p x (1-p) at C 10; PF {fr.fpf(fr.pf(nets)) if nets else 'n/a'}, z {z:+.2f} vs bar {Z_BAR}; VERDICT {w}"

    return fr.run(spec, argv, real, info, now=now, ready=ready)


main = fr.cli(forward)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
