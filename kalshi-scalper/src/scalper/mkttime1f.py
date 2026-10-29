"""MKTTIME1-F (README, Pre-registration: MKTTIME1-F): forward read of gold's 20:00 to 24:00 US Central block on L1's rule. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. A pass is a question for the owner, never a live change.
Usage: python -m scalper.mkttime1f count   readiness only: entries and LOSSES in the block (the registered trigger); computes no PF, no net, no mean
       python -m scalper.mkttime1f read    the registered read, once; refused until the block holds 15 losses, and refused a second time
Data: data/fresh.sqlite (run `python -m scalper.fresh_update` first; public candles). Population: settled KXGOLD15M markets closing after
2026-10-30 00:00 UTC. Rule: L1 (the candle ending exactly 6 minutes before the close, favourite with ask 0.88 to 0.97, held to settlement,
1 contract, fee 7% x p x (1-p) rounded up to the cent per order). Entry time = close - 360 s, in US Central; block = hour 20 to 23.
Choices this file makes that the registration does not spell out (fixed before any forward entry exists): every hold_rule entry is
kept (no extra candle-history filter, unlike tstop1.load); the day-clustered z is the cluster-robust z of (mean of the rest minus mean of
the block), clustered by the entry's Central date, with the within-day covariance of the two means included; net rule as MKTTIME1's
check (net without >= 70% of net with when net with > 0, otherwise net without >= net with).
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from . import lstrats as L
from .fwd_reads import FRESH_DB, load_fresh
from .l1studies import fee, pf
from .paths import DATA_DIR

CT = ZoneInfo("America/Chicago")
SERIES, LEFT = "KXGOLD15M", 360
START_TS = int(datetime(2026, 10, 30, tzinfo=timezone.utc).timestamp())   # closes AFTER this instant
LOSSES_NEEDED, PF_LIFT, NET_SHARE, Z_BAR = 15, 0.10, 0.70, 2.0
RESULT = DATA_DIR / "mkttime1f_result.txt"


def entries():
    mk = [m for m in load_fresh(FRESH_DB, [SERIES], START_TS + 1) if m[3] > START_TS]
    out = []
    for e in L.hold_rule(mk, LEFT, L.L1["band"]):
        t = datetime.fromtimestamp(e["close_ts"] - LEFT, CT)
        e["block"] = 20 <= t.hour < 24
        e["cday"] = t.strftime("%Y-%m-%d")
        e["lost"] = e["gross"] < 0
        out.append(e)
    return out


def count(quiet=False):
    E = entries()
    blk = [e for e in E if e["block"]]
    n_loss = sum(1 for e in blk if e["lost"])
    line = f"MKTTIME1-F readiness: {len(E)} gold entries since 2026-10-30, block 20-24 CT {len(blk)} entries with {n_loss} losses ({LOSSES_NEEDED} needed); no PF computed"
    if not quiet:
        print(line)
    return n_loss, line


def diff_z(rest, block):
    """Cluster-robust z of mean(rest) - mean(block), clusters = Central date; rest and block are lists of (day, value)."""
    nr, nb = len(rest), len(block)
    if nr < 2 or nb < 2:
        return 0.0, 0.0
    mr, mb = sum(v for _, v in rest) / nr, sum(v for _, v in block) / nb
    u = defaultdict(float)
    for d, v in rest:
        u[d] += (v - mr) / nr
    for d, v in block:
        u[d] -= (v - mb) / nb
    se = math.sqrt(sum(x * x for x in u.values()))
    return mr - mb, ((mr - mb) / se if se > 0 else 0.0)


def read():
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists"); return
    n_loss, line = count(quiet=True)
    if n_loss < LOSSES_NEEDED:
        print("Refused: " + line + " -> NOT_ENOUGH_DATA, not read"); return
    E = entries()
    v = lambda e, m=1.0: e["gross"] - m * fee(e["price"], 1)
    allv = [v(e) for e in E]
    rest = [e for e in E if not e["block"]]
    blk = [e for e in E if e["block"]]
    restv = [v(e) for e in rest]
    pf_with, pf_without = pf(allv), pf(restv)
    net_with, net_without = sum(allv), sum(restv)
    net_ok = (net_without >= NET_SHARE * net_with) if net_with > 0 else (net_without >= net_with)
    d, z = diff_z([(e["cday"], v(e)) for e in rest], [(e["cday"], v(e)) for e in blk])
    ok = (pf_without - pf_with >= PF_LIFT) and net_ok and z >= Z_BAR
    verdict = "NOT_YET_FALSIFIED (a question for the owner, never a live change by itself)" if ok else "FALSIFIED"
    lines = [f"MKTTIME1-F VERDICT: {verdict}",
             f"  entries {len(E)} (block {len(blk)}, {n_loss} block losses), closes {datetime.fromtimestamp(min(e['close_ts'] for e in E), timezone.utc):%Y-%m-%d} to {datetime.fromtimestamp(max(e['close_ts'] for e in E), timezone.utc):%Y-%m-%d} UTC",
             f"  gold PF with the block {pf_with:.3f}, without {pf_without:.3f} (lift {pf_without - pf_with:+.3f}, needs +{PF_LIFT:.2f})",
             f"  net with {100 * net_with:+.1f}c, without {100 * net_without:+.1f}c ({'ok' if net_ok else 'fails'} the 70% rule)",
             f"  mean per entry: rest {100 * sum(restv) / max(1, len(restv)):+.2f}c, block {100 * sum(v(e) for e in blk) / max(1, len(blk)):+.2f}c; rest minus block {100 * d:+.2f}c, day-clustered z {z:+.2f} (needs {Z_BAR})",
             f"  information: fees x1.2 PF with {pf([v(e, 1.2) for e in E]):.3f}, without {pf([v(e, 1.2) for e in rest]):.3f}; block PF {pf([v(e) for e in blk]):.3f}"]
    RESULT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    {"count": count, "read": read}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
