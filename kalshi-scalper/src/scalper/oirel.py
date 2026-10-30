"""OIREL: the Bitcoin open interest core with a RELATIVE jump threshold, as a forward ledger evaluator (research only).
Definition: workers/FALS5_REGISTRATION.md check 2 and workers/FALS5_RESULT.md. Nothing here places an order, reads a key or
decides anything live. NOT independent of REF_GEN6_OICORE (it shares 59% to 80% of its trades with the fixed-threshold core).

    PYTHONPATH=src python -m scalper.oirel parity    (history Aug 6 to Oct 27 against fals5's check 2; no forward window)

Rule: KXBTC15M; level = oi at the candle ending 360 s before the close; doi = oi at the candle ending 180 s before the close minus
level; trade when doi / level > RTHR (0.26764675317954373, the discovery quantile matched to the core's count of windows above
86,299.56: 941 of 4,357 discovery windows); cheap side at the signal candle (ask 5c to 50c, YES first); fill at that side's ask on
the candle ending 120 s before the close; held to settlement. A missing signal, back or fill candle, or an open interest of 0 at
either (the ledger stores a missing oi as 0), is NoData, never a no-trade.
"""
from __future__ import annotations

import sys

from .fwdeval import NoData

SERIES = "KXBTC15M"
LOOK, BACK, FILL = 180, 360, 120
LO, HI = 0.05, 0.50
RTHR = 0.26764675317954373


def side_ask(q, side):
    return q[1] if side == "yes" else round(1 - q[0], 6)


def decide(window: dict, rthr: float = RTHR):
    if window.get("series") != SERIES:
        return None
    cs, close = window["candles"], window["close_ts"]
    s, p = cs.get(close - LOOK), cs.get(close - BACK)
    if s is None or p is None or not s[3] or not p[3] or p[3] <= 0:
        raise NoData("signal or back candle (or its open interest) missing")
    doi = s[3] - p[3]
    if not doi / p[3] > rthr:
        return None
    side = next((sd for sd in ("yes", "no") if s[0] is not None and s[1] is not None and LO <= side_ask(s, sd) <= HI), None)
    if side is None:
        return None
    f = cs.get(close - FILL)
    if f is None or f[0] is None or f[1] is None:
        raise NoData("fill candle missing")
    fill = side_ask(f, side)
    if not 0 < fill < 1:
        return None
    return {"side": side, "entry": float(fill), "exit": None, "t": close - FILL, "zero_volume": (s[2] or 0) <= 0 or (f[2] or 0) <= 0,
            "note": f"doi {doi:.0f} = {doi / p[3]:.1%} of level {p[3]:.0f} > {rthr:.2%}, signal ask {side_ask(s, side):.2f}"}


def forward_eval(window: dict, params: dict):
    if window.get("series") != params.get("series", SERIES):
        return None
    return decide(window, float(params.get("rthr", RTHR)))


# ---------------------------------------------------------------- parity (history only, nothing closing on or after 2026-10-28)

def parity():
    from . import fals4, fals5
    from .fwdledger import net_per_contract, pf
    from .oidrift import _ledger_windows
    mine, nodata = {}, 0
    for w in _ledger_windows(fals4.START, fals4.FORWARD_TS):
        try:
            tr = decide(w)
        except NoData:
            nodata += 1
            continue
        if tr:
            mine[w["ticker"]] = (tr, net_per_contract(tr, w["result"], 10))
    win = fals4.load()

    def cond(w, sg):
        lv = fals5.level(w)
        return bool(lv and lv > 0 and sg["doi"] / lv > RTHR)
    ref = {t["t"]: t for t in fals4.trades(win, cond=cond)}
    only_m = sorted(set(mine) - set(ref)); only_r = sorted(set(ref) - set(mine))
    diff = [t for t in set(mine) & set(ref) if mine[t][0]["side"] != ref[t]["side"] or abs(mine[t][0]["entry"] - ref[t]["fill"]) > 1e-9]
    line = (f"OIREL parity (Aug 6 to Oct 27): evaluator n {len(mine)} PF10 {pf([x[1] for x in mine.values()]):.2f}; "
            f"fals5 check 2 n {len(ref)} PF10 {fals4.pf([t['net'] for t in ref.values()]):.2f}; "
            f"only evaluator {len(only_m)}, only fals5 {len(only_r)}, side or fill differs {len(diff)}; NoData windows {nodata}")
    print(line)
    for t in only_m[:10] + only_r[:10] + diff[:10]:
        print("  mismatch", t)
    return {"n": len(mine), "ref_n": len(ref), "only_m": only_m, "only_r": only_r, "diff": diff, "nodata": nodata}


if __name__ == "__main__":
    {"parity": parity}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
