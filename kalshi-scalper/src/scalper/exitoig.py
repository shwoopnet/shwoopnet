"""EXITOI-G: NEWH3's H3 EXITOI exit, unchanged, on gold, Dogecoin and Ethereum, plus a pooled line with Bitcoin (research only).

Registration: workers/EXITOI_G_REGISTRATION.md (pushed before any scoring). Rule and entries are newh3.h3, unchanged.

    PYTHONPATH=src python -m scalper.exitoig run
"""
from __future__ import annotations

import math
import sqlite3
import statistics
from collections import defaultdict

from .newh2 import START, DISC_END, END, pf
from .newh3 import h3, side_bid
from .paths import DATA_DIR

MARKETS = (("gold", "KXGOLD15M", ("l1b", "book", "fresh")),
           ("Dogecoin", "KXDOGE15M", ("e3b", "alts2", "fresh")),
           ("Ethereum", "KXETH15M", ("l1b", "book", "fresh")),
           ("Bitcoin", "KXBTC15M", ("l1b", "book", "fresh")))


def load(series, files, start=START, end=END):
    """newh3.load15 with the series as an argument; first file wins per ticker."""
    win, seen = {}, set()
    for name in files:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        for tk, close, res, k in db.execute(
                "select ticker, close_ts, result, strike from market where series=? and close_ts>=? and close_ts<?",
                (series, start, end)).fetchall():
            if tk in seen or close in win or res not in ("yes", "no"):
                continue
            cs = {e - close: (b, a, v or 0.0, oi) for e, b, a, v, oi in db.execute(
                "select end_ts, bid_c, ask_c, volume, oi from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if not cs:
                continue
            seen.add(tk)
            win[close] = {"ticker": tk, "close": close, "result": res, "strike": k, "c": cs}
    return win


def zero_bid(W, E):
    """Mark triggered entries whose side bid at 120 s is 0 or missing (no sale, held)."""
    for e in E:
        e["zb"] = e["trig"] and not e["sold"]


def report(E, name):
    if not E:
        return {"n": 0, "trig": 0, "dv": []}, f"{name}: n 0"
    pf_ = lambda key, k: pf([e[key][k] for e in E])
    tr = [e for e in E if e["trig"]]
    un = [e for e in E if not e["trig"]]
    dd, ddx = defaultdict(float), defaultdict(float)
    for e in E:
        dd[e["day"]] += e["rule"]["n10"] - e["hold"]["n10"]
        ddx[e["day"]] += e["rule"]["n10x"] - e["hold"]["n10x"]
    lr = lambda xs: 1 - statistics.mean([e["won"] for e in xs]) if xs else float("nan")
    zb = sum(e["zb"] for e in tr)
    nz = [e for e in E if not e["vol0"]]
    out = {"n": len(E), "trig": len(tr), "sold": sum(e["sold"] for e in E), "hold_pf": pf_("hold", "n10"),
           "rule_pf": pf_("rule", "n10"), "diff": sum(dd.values()), "diffx": sum(ddx.values()), "dv": list(dd.values())}
    s = (f"{name}: entries {len(E)} triggered {len(tr)} ({len(tr) / len(E):.1%}) sold {out['sold']} zero-bid {zb}"
         f" ({zb / len(tr) if tr else float('nan'):.0%} of triggered)\n"
         f"    PF10 hold {out['hold_pf']:.3f} rule {out['rule_pf']:.3f} (diff {out['rule_pf'] - out['hold_pf']:+.3f}) | "
         f"PF1 {pf_('hold', 'n1'):.3f} / {pf_('rule', 'n1'):.3f} | x1.2 {pf_('hold', 'n10x'):.3f} / {pf_('rule', 'n10x'):.3f}\n"
         f"    rule minus hold net10 ${out['diff']:+.2f}, at x1.2 ${out['diffx']:+.2f}; hold net10 ${sum(e['hold']['n10'] for e in E):+.2f}\n"
         f"    loss rate triggered {lr(tr):.3f} untriggered {lr(un):.3f}; triggered-only hold ${sum(e['hold']['n10'] for e in tr):+.2f}"
         f" rule ${sum(e['rule']['n10'] for e in tr):+.2f}\n"
         f"    zero-volume fill removed: n {len(nz)} PF10 hold {pf([e['hold']['n10'] for e in nz]):.3f} rule {pf([e['rule']['n10'] for e in nz]):.3f}")
    return out, s


def z_of(v):
    sd = statistics.stdev(v) if len(v) > 2 else 0
    return statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else float("nan")


def judge(od, ov, z):
    if od["trig"] < 50 or ov["trig"] < 50:
        return "NOT_ENOUGH_DATA"
    ok = (od["rule_pf"] >= od["hold_pf"] + 0.03 and ov["rule_pf"] >= ov["hold_pf"] + 0.03 and z >= 2.0
          and od["diffx"] > 0 and ov["diffx"] > 0)
    return "NOT_YET_FALSIFIED" if ok else "FALSIFIED"


def run():
    print("EXITOI-G run (NEWH3 H3 rule unchanged). Nothing on or after 2026-10-28 loaded.\n")
    pooled, verdicts = [], {}
    for name, series, files in MARKETS:
        W = load(series, files)
        E, gaps = h3(W)
        zero_bid(W, E)
        for e in E:
            e["mkt"] = name
        pooled += E
        d = [e for e in E if e["close"] < DISC_END]
        v = [e for e in E if e["close"] >= DISC_END]
        print(f"== {name} {series}: windows {len(W)} (disc {sum(c < DISC_END for c in W)}, val {sum(c >= DISC_END for c in W)}) gaps {gaps}")
        od, sd = report(d, f"{name} disc")
        ov, sv = report(v, f"{name} val")
        z = z_of(od["dv"] + ov["dv"])
        print(sd); print(sv); print(f"    day z of rule minus hold (both windows) {z:+.2f}")
        if name != "Bitcoin":
            verdicts[name] = judge(od, ov, z)
        print()
    # pooled: per-day sums across markets
    d = [e for e in pooled if e["close"] < DISC_END]
    v = [e for e in pooled if e["close"] >= DISC_END]
    od, sd = report(d, "POOLED disc")
    ov, sv = report(v, "POOLED val")
    z = z_of(od["dv"] + ov["dv"])
    print(sd); print(sv); print(f"    day z of rule minus hold (both windows) {z:+.2f}")
    verdicts["pooled"] = judge(od, ov, z)
    print("\nVerdicts (N = 4):")
    for k, x in verdicts.items():
        print(f"  {k}: {x}")


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["run"]:
        run()
