"""THETA1 (README, Pre-registration: THETA1): favourite drift sold before settlement in long-dated markets. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
    python -m scalper.theta1 search    (discovery and validation; freezes survivors)
    python -m scalper.theta1 holdout   (once, frozen survivors only)
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from datetime import datetime, timezone
from itertools import product

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .gen1 import _norm_ppf
from .paths import DATA_DIR

DB = DATA_DIR / "theta1.sqlite"
FROZEN = DATA_DIR / "theta1_survivors.json"
RESULT = DATA_DIR / "theta1_result.txt"
HOLD_RESULT = DATA_DIR / "theta1_holdout_result.txt"
ENTRY = (168, 72, 48)
EXIT = (24, 12, 6)
BANDS = ((0.60, 0.75), (0.75, 0.88), (0.88, 0.97))
VAL_FROM = int(datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp())
HOLD_FROM = int(datetime(2026, 10, 15, tzinfo=timezone.utc).timestamp())
N_PRIOR = 411_000


def fee(p, c=10, m=1.0):
    return math.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def load():
    db = sqlite3.connect(DB)
    mk = {t: (ev, c) for t, ev, c in db.execute("SELECT ticker, event, close_ts FROM market")}
    cd = {(t, l): (b, a) for t, l, b, a in db.execute("SELECT ticker, lead_h, bid_c, ask_c FROM candle")}
    return mk, cd


def trades(mk, cd, e, x, band, span):
    out = []
    for t, (ev, close) in mk.items():
        if not span(close):
            continue
        q = cd.get((t, e))
        if not q or not valid_quote(q[0], q[1]):
            continue
        b, a = q
        if band[0] - 1e-9 <= a <= band[1] + 1e-9:
            yes, price = True, a
        elif band[0] - 1e-9 <= 1 - b <= band[1] + 1e-9:
            yes, price = False, round(1 - b, 4)
        else:
            continue
        qx = cd.get((t, x))
        if qx and qx[0] is not None and qx[1] is not None:
            sell = qx[0] if yes else round(1 - qx[1], 4)
        else:
            sell = 0.0  # no bid at the exit hour: worst case, not dropped
        sell = max(sell, 0.0)
        out.append((ev, sell - price - fee(price) - (fee(sell) if sell > 0 else 0.0), sell - price - fee(price, m=1.2) - (fee(sell, m=1.2) if sell > 0 else 0.0)))
    return out


def stats(tr):
    if not tr:
        return {"n": 0, "events": 0, "pf": 0.0, "pfs": 0.0, "z": 0.0, "mean_c": 0.0}
    v = [x for _, x, _ in tr]; s = [y for _, _, y in tr]
    pf = lambda xs: (sum(a for a in xs if a > 0) / -sum(a for a in xs if a < 0)) if any(a < 0 for a in xs) else 99.0
    _, _, z = cluster_mean_z([(ev, x) for ev, x, _ in tr])
    return {"n": len(tr), "events": len({ev for ev, _, _ in tr}), "pf": pf(v), "pfs": pf(s), "z": z, "mean_c": 100 * sum(v) / len(v)}


def search():
    mk, cd = load()
    disc = lambda c: c < VAL_FROM
    val = lambda c: VAL_FROM <= c < HOLD_FROM
    zbar = _norm_ppf(1 - 0.05 / (N_PRIOR + 27))
    lines = [f"THETA1: {len(mk)} markets on file; discovery closes before 2026-10-01, validation 10-01 to 10-15; Bonferroni z bar {zbar:.2f}"]
    frozen = []
    for e, x, band in product(ENTRY, EXIT, BANDS):
        d = stats(trades(mk, cd, e, x, band, disc))
        tag = f"entry {e}h exit {x}h band {band[0]:.2f}-{band[1]:.2f}"
        if not (d["pf"] >= 1.5 and d["n"] >= 100 and d["events"] >= 40):
            lines.append(f"  {tag}: FAILED discovery: PF {d['pf']:.2f} stress {d['pfs']:.2f} n={d['n']} events {d['events']} mean {d['mean_c']:+.2f}c z {d['z']:+.2f}")
            continue
        v = stats(trades(mk, cd, e, x, band, val))
        ok = v["pf"] >= 1.5 and v["n"] >= 40 and v["events"] >= 20 and v["pfs"] >= 1.2 and v["z"] >= zbar
        lines.append(f"  {tag}: discovery PF {d['pf']:.2f} n={d['n']} | validation PF {v['pf']:.2f} stress {v['pfs']:.2f} n={v['n']} events {v['events']} z {v['z']:+.2f} {'PASS (frozen)' if ok else 'FAILED validation'}")
        if ok:
            frozen.append({"entry": e, "exit": x, "band": band})
    FROZEN.write_text(json.dumps({"frozen_at": datetime.now(timezone.utc).isoformat(), "survivors": frozen}))
    lines.insert(0, "THETA1 VERDICT so far: " + ("NO_WINNER (FALSIFIED before the holdout)" if not frozen else f"{len(frozen)} frozen for the holdout"))
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


def holdout():
    if HOLD_RESULT.exists():
        print("Refusing to run again"); return
    mk, cd = load()
    fz = json.loads(FROZEN.read_text())["survivors"]
    lines = [f"THETA1 holdout (closes from 2026-10-15), {len(fz)} frozen"]
    for s in fz:
        h = stats(trades(mk, cd, s["entry"], s["exit"], tuple(s["band"]), lambda c: c >= HOLD_FROM))
        ok = h["pf"] >= 1.5 and h["n"] >= 30 and h["events"] >= 15 and h["pfs"] >= 1.2
        lines.append(f"  {s}: PF {h['pf']:.2f} stress {h['pfs']:.2f} n={h['n']} events {h['events']} {'HOLDOUT-PASS' if ok else 'holdout-fail'}")
    HOLD_RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"search": search, "holdout": holdout}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
