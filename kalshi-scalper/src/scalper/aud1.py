"""AUD1: independent audit of G3H1's fill model, a standalone re-implementation read straight from the candle file (not GEN3's code).
Research only. Usage: python -m scalper.aud1 lad1|lad2
"""
from __future__ import annotations

import math
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone

from .paths import DATA_DIR

W_HI, W_LO, ASK_MAX, TP, EXIT_LEFT = 3060, 2760, 0.10, 0.03, 60
DISC_D, VAL_D = 15, 23


def fee(p, c=10):
    return math.ceil(0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def quotes(c, side):
    b, a = c[0], c[1]
    return (b, a) if side == "yes" else (round(1 - a, 4), round(1 - b, 4))


def run(name):
    db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
    mk = defaultdict(list)
    for tk, close in db.execute("select ticker, close_ts from market"):
        mk[close].append(tk)
    cd = defaultdict(dict)
    for tk, e, b, a, v in db.execute("select ticker, end_ts, bid_c, ask_c, volume from candle where bid_c is not null and ask_c is not null"):
        cd[tk][e] = (b, a, v or 0.0)
    days = sorted({datetime.fromtimestamp(c, timezone.utc).strftime("%Y-%m-%d") for c in mk}); didx = {d: i for i, d in enumerate(days)}
    variants = {"same-candle fill (registered)": (0, "keep"), "next-candle fill": (60, "keep"), "zero-volume dropped": (0, "drop"), "zero-volume unfillable": (0, "unfill")}
    out = {v: defaultdict(list) for v in variants}
    for close, tks in mk.items():
        win = "discovery" if didx[datetime.fromtimestamp(close, timezone.utc).strftime("%Y-%m-%d")] < DISC_D else ("validation" if didx[datetime.fromtimestamp(close, timezone.utc).strftime("%Y-%m-%d")] < VAL_D else "holdout")
        for tk in tks:
            cs = cd[tk]
            sig = None
            for L in range(W_HI, W_LO - 1, -60):
                t = close - L
                if t not in cs or (t - 120) not in cs:
                    continue
                for side in ("yes", "no"):
                    b, a = quotes(cs[t], side)
                    if 0.03 <= a <= ASK_MAX and b - quotes(cs[t - 120], side)[0] > 0:
                        sig = (t, side); break
                if sig:
                    break
            if not sig:
                continue
            t, side = sig
            for vname, (lag, zmode) in variants.items():
                te = t + lag
                if te not in cs:
                    if zmode == "unfill" or lag:
                        out[vname][win].append((close, None)); continue
                ent = cs[te]
                e = quotes(ent, side)[1]
                if lag and not (0.03 <= e <= 0.85):
                    out[vname][win].append((close, None)); continue
                later = sorted(k for k in cs if te < k <= close - EXIT_LEFT)
                if not later:
                    continue
                if zmode == "drop" and ent[2] <= 0:
                    continue
                if zmode == "unfill" and ent[2] <= 0:
                    out[vname][win].append((close, None)); continue
                x = None
                for k in later:
                    b, a = quotes(cs[k], side)
                    if zmode in ("drop", "unfill") and cs[k][2] <= 0 and k != later[-1]:
                        continue  # a zero-volume minute cannot be sold into; wait for a minute with volume
                    if b >= e + TP - 1e-9 or a - b >= 0.03 - 1e-9:
                        x = b; break
                if x is None:
                    x = quotes(cs[later[-1]], side)[0]
                out[vname][win].append((close, x - e - fee(e) - fee(x)))
    lines = [f"AUD1 on {name}.sqlite: {len(mk)} closes"]
    for vname, d in out.items():
        for w in ("discovery", "validation", "holdout"):
            v = [x for _, x in d[w] if x is not None]; miss = sum(1 for _, x in d[w] if x is None)
            g = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
            lines.append(f"  {vname:30s} {w:10s}: PF {g / l if l else 99:.2f} n={len(v)} closes {len({c for c, x in d[w] if x is not None})} mean {100 * sum(v) / max(len(v), 1):+.2f}c" + (f", unfilled {miss}" if miss else ""))
    txt = "\n".join(lines) + "\n"
    (DATA_DIR / f"aud1_{name}.txt").write_text(txt); print(txt)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "lad1")
