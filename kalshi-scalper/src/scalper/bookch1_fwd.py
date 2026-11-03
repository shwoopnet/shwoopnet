"""BOOKCH1 pooled forward verdict (workers/BOOKCH1_REGISTRATION.md). Research only; nothing here means trade; no promote verb.

    python -m scalper.bookch1_fwd forward [--force-info] [--trades PATH]     (also: python -m scalper.bookch1 forward)

Pools the forward-ledger trades of the PRIMARY (BOOKCH1_BTC + BOOKCH1_XRP) and, as its own verdict, the ALTERNATIVE (BOOKCH1B_BTC + BOOKCH1B_XRP). The trades
come from scalper.fwdledger (the same evaluator `bookch1:forward_eval`, windows closing strictly after 2026-11-04 00:00Z). With --trades PATH it reads a trades JSON
in the data/fwdledger_trades.json shape instead (tests, or the file the hourly pass wrote). Without it, it runs the ledger on the four BOOKCH1 candidates only,
into a scratch file, so the hourly pass's own dump is never overwritten.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from . import fwdread as fr

FREEZE = int(fr.utc(2026, 11, 4).timestamp())
LAST_ALLOWED = fr.utc(2026, 11, 14)
NEEDED, MIN_DAYS, Z_BAR = 150, 7, 5.27
PRIMARY, ALT = ("BOOKCH1_BTC", "BOOKCH1_XRP"), ("BOOKCH1B_BTC", "BOOKCH1B_XRP")

SPEC = fr.Spec(
    id="BOOKCH1F",
    title="pooled forward verdict, Bitcoin + XRP 15 minute cheap-side imbalance (primary), alternative separately",
    sources=["workers/BOOKCH1_REGISTRATION.md"],
    rule=[
        "**NOT_ENOUGH_DATA:** fewer than 150 pooled trades at the read, or fewer than 7 trade days. Nothing is called.",
        "**FALSIFIED:** forward PF below 1.0 after 150 trades, OR PF below 1.5 in either of two equal halves (equal trade count, in time order), OR (at 1 contract) mean net per trade not above 0, OR PF at fees x1.2 below 1.0.",
        "**NOT_YET_FALSIFIED** only if none of the above and PF is 1.5 or better in both halves.",
        "the last third of the forward period by close time (the verdict cutoff is the read date) is the holdout; it is read once, at the verdict, together with the other two thirds, and counts only if its own PF is above 1.0.",
    ],
    window=[
        "ledger trades of BOOKCH1_BTC, BOOKCH1_XRP (primary) and BOOKCH1B_BTC, BOOKCH1B_XRP (alternative) with close_ts > 2026-11-04 00:00Z and <= the read time",
        "PF at C = 10 and fee included (net10), mean at 1 contract (net1), fees x1.2 (net10s); halves are equal trade counts in time order",
    ],
    due=fr.utc(2026, 11, 12),
    due_note="expected about 2026-11-12; last allowed 2026-11-14 00:00 UTC; before 2026-11-14 it also waits for 150 trades and 7 trade days",
)


def pooled(trades_by_id, ids, hi_ts):
    t = [x for i in ids for x in trades_by_id.get(i, []) if FREEZE < x["close_ts"] <= hi_ts]
    return sorted(t, key=lambda x: (x["close_ts"], x["ticker"]))


def verdict(t):
    """Pure registered rule on a time-ordered pooled list. Returns (word, facts dict)."""
    n = len(t)
    days = len({fr.day_of(x["close_ts"]) for x in t})
    nets10 = [x["net10"] for x in t]
    h = n // 2
    facts = {"n": n, "days": days, "pf10": fr.pf(nets10), "pf10s": fr.pf([x["net10s"] for x in t]),
             "mean1": sum(x["net1"] for x in t) / n if n else 0.0,
             "pf_h1": fr.pf([x["net10"] for x in t[:h]]), "pf_h2": fr.pf([x["net10"] for x in t[h:]])}
    m, z = fr.clustered([(fr.day_of(x["close_ts"]), x["net10"]) for x in t])
    facts["z"] = z
    k = (2 * n) // 3
    facts["pf_holdout"] = fr.pf([x["net10"] for x in t[k:]]) if n else 0.0
    facts["holdout_n"] = n - k
    if n < NEEDED or days < MIN_DAYS:
        return "NOT_ENOUGH_DATA", facts
    if facts["pf10"] < 1.0 or facts["pf_h1"] < 1.5 or facts["pf_h2"] < 1.5 or facts["mean1"] <= 0 or facts["pf10s"] < 1.0:
        return "FALSIFIED", facts
    return "NOT_YET_FALSIFIED", facts


def fmt(label, word, f):
    s = (f"{label}: {word}; n {f['n']} on {f['days']} trade days; PF10 {fr.fpf(f['pf10'])}, halves {fr.fpf(f['pf_h1'])} / {fr.fpf(f['pf_h2'])}, "
         f"mean at 1 contract {100 * f['mean1']:+.2f}c, PF at fees x1.2 {fr.fpf(f['pf10s'])}, day-clustered z {f['z']:.2f} vs bar {Z_BAR}; "
         f"last third ({f['holdout_n']} trades) PF {fr.fpf(f['pf_holdout'])}")
    if word == "NOT_YET_FALSIFIED":
        s += ("; HOLDOUT COUNTS" if f["pf_holdout"] > 1.0 else "; HOLDOUT DOES NOT COUNT (its PF is not above 1.0): no pass") + (" ; z under the bar: not a pass" if f["z"] < Z_BAR else "")
    return s


def load_trades(path=None):
    if path:
        return json.loads(Path(path).read_text())
    from . import fwdledger as fl
    tmp = Path(tempfile.mkdtemp(prefix="bookch1f_"))
    (tmp / "c").mkdir()
    for i in PRIMARY + ALT:
        (tmp / "c" / f"{i}.json").write_text((fl.CAND_DIR / f"{i}.json").read_text())
    old = fl.TRADES_OUT
    fl.TRADES_OUT = tmp / "trades.json"      # never overwrite the hourly pass's data/fwdledger_trades.json
    try:
        fl.run(cand_dir=tmp / "c", out=tmp / "ledger.md")
    finally:
        fl.TRADES_OUT = old
    return json.loads((tmp / "trades.json").read_text())


def oicore_overlap(by_id, prim):
    ref = by_id.get("REF_GEN6_OICORE")
    if not ref:
        return "OICORE overlap: REF_GEN6_OICORE trades not in this file (not reported)"
    keys = {(x["ticker"], x["side"]) for x in ref}
    k = sum(1 for x in prim if (x["ticker"], x["side"]) in keys)
    return f"OICORE overlap (same ticker and side): {k} of {len(prim)} primary trades; never changes the verdict; a pass that is only these is paper only"


def forward(argv, now=None):
    now_ = now or fr.datetime.now(fr.UTC)
    hi = now_.timestamp()
    f = fr.flags(argv)
    path = f["rest"][f["rest"].index("--trades") + 1] if "--trades" in f["rest"] else None
    cache = {}

    def data():
        if "d" not in cache:
            cache["d"] = load_trades(path)
        return cache["d"]

    def info():
        d = data()
        p, a = pooled(d, PRIMARY, hi), pooled(d, ALT, hi)
        return [f"primary pooled trades so far {len(p)} on {len({fr.day_of(x['close_ts']) for x in p})} trade days (needs {NEEDED} and {MIN_DAYS}); alternative {len(a)}"]

    def ready(n):
        w, fa = verdict(pooled(data(), PRIMARY, hi))
        if w == "NOT_ENOUGH_DATA" and n < LAST_ALLOWED:
            return f"primary has {fa['n']} trades on {fa['days']} days (needs {NEEDED} and {MIN_DAYS}); wait, the last allowed read is {LAST_ALLOWED:%Y-%m-%d} 00:00 UTC"
        return None

    def real():
        d = data()
        p, a = pooled(d, PRIMARY, hi), pooled(d, ALT, hi)
        (wp, fp), (wa, fa) = verdict(p), verdict(a)
        lines = [fmt("PRIMARY (Bitcoin + XRP pooled)", wp, fp), fmt("ALTERNATIVE (BOOKCH1B, own verdict)", wa, fa), oicore_overlap(d, p),
                 "Cost: fee 7% x C x p x (1-p) rounded up per order, C = 10 (PF10), C = 1 (mean), x1.2 stress. No promote verb."]
        body = (f"window closes after 2026-11-04 00:00Z to {fr.day_of(hi)}; n {fp['n']} pooled primary trades on {fp['days']} days; cost fee 7% x C x p x (1-p) at C 10 and 1, x1.2 stress; "
                f"PF10 {fr.fpf(fp['pf10'])}, halves {fr.fpf(fp['pf_h1'])}/{fr.fpf(fp['pf_h2'])}, z {fp['z']:.2f} vs bar {Z_BAR}, VERDICT {wp}; alternative n {fa['n']} VERDICT {wa}")
        return lines, body

    return fr.run(SPEC, argv, real, info, now=now_, ready=ready)


main = fr.cli(forward)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
