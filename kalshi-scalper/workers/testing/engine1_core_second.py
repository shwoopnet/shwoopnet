#!/usr/bin/env python3
"""ENGINE1 scorer core, BUILD 2 (Testing Desk, Nov 15, 2026). A pure scorer: no file, no network, no clock. Written from ENGINE1_SPEC_NOV15.md and Desk A's interface message ONLY (not from Desk A's core).
Hand case: ENGINE1_CORE_SECOND_HAND_CASE.md (committed first). Test: test_engine1_core_second.py (INVENTED entries only).
API: score_entry(entry, path, exit_kind, h, n=None) -> {"status": "scored"|"no_mark", "cash": float, "reason": "settle"|"target"|"stop"|"time"}; aggregate(scored, ...) -> the per-rule block.
"""
import math

CAP, FLOOR, TOL_DEC = 0.99, 0.01, 6
HAIRCUTS = (0.0, 0.01, 0.02)
EXITS = ("H", "T", "S", "B", "M180", "M60")


def fee_up_order(p, n): return math.ceil(round(0.07 * n * p * (1 - p) * 100, 9)) / 100


def sellable(c): return 0 < c[1] < c[2] < 1


def side_bid(c, side): return c[1] if side == "yes" else 1 - c[2]


def r6(x): return round(x, TOL_DEC)


def score_entry(e, path, kind, h, n=None):
    n = e["n"] if n is None else n
    path = [c for c in path if e["entry_end"] < c[0] <= e["close_ts"]]          # only candles strictly after the entry candle and at or before the close (Auditor B)
    paid = min(r6(e["ask"] + h), CAP); fee_in = fee_up_order(paid, n); close = e["close_ts"]; side = e["side"]
    def exit_at(bid, reason):
        px = max(r6(bid - h), FLOOR)
        return {"status": "scored", "cash": round(n * px - n * paid - fee_in - fee_up_order(px, n), 9), "reason": reason}          # rounded to 9 places so float noise (8.7e-18) is not a win
    def settle():
        if e["result"] not in ("yes", "no"): return {"status": "scored", "cash": round(-fee_in, 9), "reason": "settle"}          # a void refunds the price and keeps the entry fee
        return {"status": "scored", "cash": round((n * 1.0 if e["result"] == side else 0.0) - n * paid - fee_in, 9), "reason": "settle"}
    if kind == "H": return settle()
    if kind in ("T", "S", "B"):
        tgt, stp = r6(min(2 * paid, CAP)), r6(paid / 2)
        for c in path:
            if not sellable(c): continue
            b = r6(side_bid(c, side))
            hit_s = kind in ("S", "B") and b <= stp
            hit_t = kind in ("T", "B") and b >= tgt
            if hit_s: return exit_at(side_bid(c, side), "stop")          # both on one candle: the stop wins
            if hit_t: return exit_at(side_bid(c, side), "target")
        return settle()
    mark = {"M180": 180, "M60": 60}[kind]
    if e["entry_end"] > close - mark: return {"status": "no_mark", "cash": 0.0, "reason": "no_mark"}
    for c in path:
        if c[0] == close - mark:
            if not sellable(c): break
            return exit_at(side_bid(c, side), "time")
    return {"status": "no_mark", "cash": 0.0, "reason": "no_mark"}


def pf(vals):
    pos = sum(v for v in vals if v > 0); neg = abs(sum(v for v in vals if v < 0))
    if neg == 0: return math.inf if pos > 0 else math.nan
    return pos / neg


def day_z(rows):
    by = {}
    for r in rows: by[r["day"]] = by.get(r["day"], 0.0) + r["cash"]
    v = list(by.values())
    if len(v) < 2: return None, len(v)
    m = sum(v) / len(v); sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    return (None if sd == 0 else m / (sd / math.sqrt(len(v)))), len(v)


def aggregate(entries, paths, kind, h, n=None):
    """entries: list of entry records; paths: {id: path}; -> the block for one rule at one haircut and contract count"""
    rows, counts = [], {"target": 0, "stop": 0, "time": 0, "settle": 0, "no_mark": 0}
    for e in entries:
        r = score_entry(e, paths.get(e["id"], []), kind, h, n)
        counts["no_mark" if r["status"] == "no_mark" else r["reason"]] += 1
        if r["status"] == "scored": rows.append({"id": e["id"], "close_ts": e["close_ts"], "day": e["day"], "cash": r["cash"]})
    rows.sort(key=lambda r: (r["close_ts"], r["id"])); cs = [r["cash"] for r in rows]; k = len(cs); h2 = k // 2
    z, days = day_z(rows)
    return {"n": k, "wins": sum(1 for v in cs if v > 0), "net": sum(cs), "pf": pf(cs), "half1_pf": pf(cs[:h2]), "half2_pf": pf(cs[h2:]), "half1_net": sum(cs[:h2]), "half2_net": sum(cs[h2:]),
            "day_clustered_z": z, "trade_days": days, "exit_counts": counts, "cash_per_contract_mean": (sum(cs) / (k * (e["n"] if n is None else n))) if k and entries else None}
