#!/usr/bin/env python3
"""Shadow forward scorer, BUILD 2 (Testing Desk, Nov 16, 2026). Independent of Main's JS scripts/shadow_forward.js: written from SHADOW_SCORER_SECOND_HAND_CASE.md. Pure; exact Fraction arithmetic (no float boundary issues)."""
import math
from fractions import Fraction as F

SLIPS = (0, 1, 2)
MIN_START_KEYS = ("id", "market", "entry", "exit", "side", "startUtc", "target", "dataBranch")


def fee(paid):
    """per contract fee: ceil(7% x 10 x p(1-p) in cents) cents on ten contracts, over 10. paid is a Fraction strictly between 0 and 1."""
    if not (0 < paid < 1): return None
    return F(math.ceil(F(7, 100) * 10 * paid * (1 - paid) * 100), 1000)


def pnl(price, side, result, slip):
    paid = min(F(99, 100), F(str(price)) + F(slip, 100)); f = fee(paid)
    if f is None or side not in ("yes", "no") or result not in ("yes", "no"): return None
    return (1 - paid - f) if side == result else -(paid + f)


def summarize(vals):
    gw = sum((x for x in vals if x > 0), F(0)); gl = sum((-x for x in vals if x <= 0), F(0)); net = sum(vals, F(0))
    return {"net": round(float(net), 4), "pf": round(float(gw / gl), 3) if gl > 0 else None, "no_losses": gl == 0 and len(vals) > 0}


def score(spec, signals, start_ms, now_ms):
    """spec id -> dict. signals: rows with spec, ticker, side, price, ts, fill_checked, result."""
    mine = sorted((s for s in signals if s["spec"] == spec and s["fill_checked"] is True and start_ms <= s["ts"] <= now_ms), key=lambda s: (s["ts"], str(s["ticker"])))
    seen, uniq = set(), []
    for s in mine:
        k = (s["ticker"], s["side"])
        if k not in seen: seen.add(k); uniq.append(s)
    settled = [s for s in uniq if s["result"] in ("yes", "no")]
    wins = sum(1 for s in settled if s["side"] == s["result"])
    out = {"signals": len(uniq), "settled": len(settled), "wins": wins, "losses": len(settled) - wins, "slip": {}}
    for c in SLIPS:
        vals = [v for v in (pnl(s["price"], s["side"], s["result"], c) for s in settled) if v is not None]
        out["slip"]["cash" if c == 0 else "+%dc" % c] = summarize(vals)
    return out
