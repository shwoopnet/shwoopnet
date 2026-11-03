"""USWEEP1 forward command for the five watch items (workers/USWEEP1_RESULT.md, freeze 2026-11-03 17:00Z). Research only; no promote verb.

    python -m scalper.usweep1_fwd forward --owner-asked [--daily-dir DIR] [--force-info]

These are favourite-and-hold items (ask 0.85 to 0.97, held to settlement) and the owner's 2026-10-28 instruction bans further research on that shape, so the command
prints OWNER RULING NEEDED and REFUSES (even with --force-info) unless it is run with --owner-asked. It reads the RECDAILY quotes through scalper.recdaily (branch
claude/v2-recorder-daily, not merged into this branch; if the module is absent the command says so and stops) from DIR = a checkout of origin/quote-data's daily/ folder
(default: git archive of origin/quote-data into a scratch folder), applies usweep1.forward_eval to each settled market at its registered look, and reports per item.
"""
from __future__ import annotations

import importlib
import sys
import tempfile
from pathlib import Path

from . import fwdread as fr
from . import usweep1
from .fwdeval import NoData
from .fwdledger import net_per_contract

KILL_FILLS = 40
KILL_NET_USD = -3.00
Z_BAR = 5.27

SPEC = fr.Spec(
    id="USWEEP1F",
    title="forward watch of the five daily favourite items (KXNATGASD, KXGOLDD, KXSILVERD, KXBRENTD, KXHIGHTSATX)",
    sources=["workers/USWEEP1_RESULT.md"],
    rule=[
        "Rule for all: favourite (ask 0.85 to 0.97, hard limit 0.97), taker, held to settlement, fee 7% x C x p x (1-p) rounded up.",
        "Capped probe: **1 contract, hard limit 0.97, kill at 40 fills with PF under 1.0** (or net under -$3).",
    ],
    window=[
        "markets of the five series with close_ts >= 2026-11-03 17:00Z (usweep1.FWD_FREEZE) and a recorded settlement, from RECDAILY quotes (daily/quotes, daily/results)",
        "look = usweep1.FWD minutes before the close (360 gold, silver, gas; 60 Brent; 1440 Texas high), nearest recorded poll within 25 minutes, else NoData",
    ],
    owner_ruling="the owner's 2026-10-28 instruction bans further research on buy-the-favourite-and-hold (README, Owner instruction 2026-10-28). Run only with --owner-asked after a written ruling.",
)


def recdaily():
    return importlib.import_module("scalper.recdaily")


def item_rows(rd, rows, results, series, look):
    """One row per settled market of the series that closes after the freeze and passes forward_eval; NoData and no-trade are counted."""
    out, nodata, notrade = [], 0, 0
    for tk in rd.tickers(rows, series):
        w = rd.usweep1_window(rows, results, tk, look)
        if w is None or w["close_ts"] < usweep1.FWD_FREEZE or w.get("result") not in ("yes", "no"):
            continue
        try:
            tr = usweep1.forward_eval(w, None)
        except NoData:
            nodata += 1
            continue
        if tr is None:
            notrade += 1
            continue
        out.append({"ticker": tk, "close_ts": w["close_ts"], "side": tr["side"], "entry": tr["entry"],
                    "net1": net_per_contract(tr, w["result"], 1), "net10": net_per_contract(tr, w["result"], 10)})
    return sorted(out, key=lambda r: r["close_ts"]), nodata, notrade


def judge(fills):
    """Per item, registered probe rule: kill at 40 fills with PF under 1.0 or net under -$3 (1 contract, dollars). Fewer fills: NOT_ENOUGH_DATA."""
    n = len(fills)
    net = sum(r["net1"] for r in fills)
    p = fr.pf([r["net1"] for r in fills])
    if n < KILL_FILLS:
        return "NOT_ENOUGH_DATA", n, net, p
    return ("FALSIFIED" if (p < 1.0 or net < KILL_NET_USD) else "NOT_YET_FALSIFIED"), n, net, p


def load(daily_dir):
    rd = recdaily()
    return rd, rd.load_quotes(daily_dir), rd.load_results(daily_dir)


def forward(argv, now=None):
    f = fr.flags(argv)
    daily = f["rest"][f["rest"].index("--daily-dir") + 1] if "--daily-dir" in f["rest"] else None
    state = {}

    def get():
        if "d" not in state:
            try:
                recdaily()
            except ImportError:
                raise SystemExit("scalper.recdaily is not on this branch (it lives on claude/v2-recorder-daily, unmerged). Nothing was read.")
            d = daily
            if not d:
                tmp = tempfile.mkdtemp(prefix="usweep1f_")
                fr.checkout_quote_data(["daily"], tmp)
                d = str(Path(tmp) / "daily")
            state["d"] = load(d)
        return state["d"]

    def per_item():
        rd, rows, results = get()
        return {s: item_rows(rd, rows, results, s, m) for s, m in usweep1.FWD.items()}

    def info():
        return [f"{s}: {len(r)} forward fills so far, {nd} NoData, {nt} not in the 0.85 to 0.97 band (counts only; the kill needs {KILL_FILLS} fills)" for s, (r, nd, nt) in per_item().items()]

    def ready(n):
        if all(len(v[0]) < KILL_FILLS for v in per_item().values()):
            return f"no item has {KILL_FILLS} fills yet (the registered kill and read point); use --force-info for counts"
        return None

    def real():
        lines, pooled, parts = [], [], []
        for s, (rows, nd, nt) in per_item().items():
            w, n, net, p = judge(rows)
            pooled += rows
            lines.append(f"{s}: {w}; fills {n}, NoData {nd}, no-trade {nt}; net at 1 contract ${net:+.2f}; PF {fr.fpf(p)}; probe kill {KILL_FILLS} fills with PF under 1.0 or net under ${-KILL_NET_USD:.2f} loss")
            parts.append(f"{s} {w} n{n} PF{fr.fpf(p)} net${net:+.2f}")
        m, z = fr.clustered([(fr.day_of(r["close_ts"]), r["net1"]) for r in pooled])
        lines.append(f"pooled {len(pooled)} fills, day-clustered z {z:.2f} against the deflated bar {Z_BAR}: not a lead whatever the sign. Fee 7% x C x p x (1-p) rounded up, per contract at C = 1 and 10. No promote verb.")
        return lines, "owner asked; window closes after 2026-11-03 17:00Z; " + "; ".join(parts) + f"; cost fee 7% x C x p x (1-p) at C 1 and 10; pooled z {z:.2f} vs bar {Z_BAR}"

    return fr.run(SPEC, argv, real, info, now=now, ready=ready)


main = fr.cli(forward)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
