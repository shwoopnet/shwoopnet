#!/usr/bin/env python3
"""XRPFAV6 / XRPFAV10 haircut recompute, BUILD 2 (Testing Desk, Nov 15, 2026). Research only: reads one sqlite extract, sends nothing, writes nothing, prints aggregates only (no ticker).
Built from the card (regime_b2.py rows XRPFAV6 and XRPFAV10, README:9192), the haircut rule (rnd-queue C1 to C10) and Desk A's input list ONLY; not from Desk A's reader. Hand case: XRPFAV_SECOND_HAND_CASE.md (committed first). Test: test_xrpfav_second.py (INVENTED rows only).
Usage: xrpfav_second.py <extract.sqlite> <XRPFAV6|XRPFAV10>      (the raw sha256 of the extract file is printed)
"""
import hashlib, math, sqlite3, sys

SERIES, LO, HI, CONTRACTS, CAP, TOL = "KXXRP15M", 0.88, 0.92, 10, 0.99, 1e-9
RULES = {"XRPFAV6": (330, 400, 0.02), "XRPFAV10": (570, 640, None)}          # left_lo, left_hi, maxspread
HAIRCUTS = (0.0, 0.01, 0.02)
BAR_PF1, BAR_HALF, BAR_PF2 = 1.3, 1.0, 1.0


def fee_up_order(p, n=CONTRACTS): return math.ceil(0.07 * n * p * (1 - p) * 100 - 1e-9) / 100


def load(path):
    with open(path, "rb") as fh: sha = hashlib.sha256(fh.read()).hexdigest()
    db = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    markets = db.execute("select ticker, series, close_ts, result from market order by close_ts, ticker").fetchall()
    close_of = {m[0]: m[2] for m in markets}; cands, dropped = {}, 0
    for tk, end, bid, ask in db.execute("select ticker, end_ts, bid_c, ask_c from candle"):
        if tk not in close_of: continue
        if end > close_of[tk]: dropped += 1; continue
        cands.setdefault(tk, {})[end] = (bid, ask)
    return sha, markets, cands, dropped


def pick_trade(cs, close, rule):
    """-> (kind, side, p): kind in nocandle, badquote, spread, band, trade"""
    lo, hi, msp = RULES[rule]
    ends = [e for e in cs if lo <= close - e <= hi]
    if not ends: return ("nocandle", None, None)
    b, a = cs[max(ends)]
    if b is None or a is None or b <= 0 or a >= 1 or a <= b: return ("badquote", None, None)
    if msp is not None and a - b > msp + TOL: return ("spread", None, None)
    ysp, nsp = a, round(1 - b, 6)
    side, p = ("yes", ysp) if ysp >= nsp else ("no", nsp)
    if not (LO - TOL <= p <= HI + TOL): return ("band", None, None)
    return ("trade", side, p)


def cash_of(side, p, result, h):
    price = min(round(p + h, 6), CAP); fee = fee_up_order(price)
    return CONTRACTS * ((1.0 if result == side else 0.0) - price) - fee


def pf(vals):
    pos = sum(v for v in vals if v > 0); neg = abs(sum(v for v in vals if v < 0))
    return math.inf if neg == 0 else (None if pos == 0 else pos / neg)


def run(path, rule):
    if rule not in RULES: raise SystemExit("STOP: rule must be one of " + ", ".join(RULES))
    sha, markets, cands, dropped = load(path)
    cnt = {"markets_in_extract": len(markets), "other_series_ignored": 0, "excluded_result": 0, "windows": 0, "trades": 0, "nocandle": 0, "badquote": 0, "spread": 0, "band": 0, "candles_dropped_after_close": dropped}
    trades = []
    for tk, series, close, result in markets:
        if series != SERIES: cnt["other_series_ignored"] += 1; continue
        if result not in ("yes", "no"): cnt["excluded_result"] += 1; continue
        cnt["windows"] += 1
        kind, side, p = pick_trade(cands.get(tk, {}), close, rule)
        if kind != "trade": cnt[kind] += 1; continue
        trades.append({"tk": tk, "close": close, "side": side, "p": p, "result": result})
    trades.sort(key=lambda t: (t["close"], t["tk"])); cnt["trades"] = len(trades); n = len(trades); h2 = n // 2
    out = {"rule": rule, "extract_sha256": sha, "counts": cnt, "label": "upper bound, not fill-checked; fee mode per-order rounded"}
    for h in HAIRCUTS:
        cs = [cash_of(t["side"], t["p"], t["result"], h) for t in trades]; f, s = cs[:h2], cs[h2:]
        out["h%.2f" % h] = {"n": n, "wins": sum(1 for v in cs if v > 0), "net": sum(cs), "pf": pf(cs) if cs else None, "half1_pf": pf(f) if f else None, "half2_pf": pf(s) if s else None, "half1_net": sum(f), "half2_net": sum(s)}
    ge = lambda x, y: x is not None and x >= y - TOL
    r1, r2 = out["h0.01"], out["h0.02"]
    out["counts_toward_20_to_30"] = bool(ge(r1["pf"], BAR_PF1) and ge(r1["half1_pf"], BAR_HALF) and ge(r1["half2_pf"], BAR_HALF) and ge(r2["pf"], BAR_PF2))
    out["primary_haircut_note"] = "C8: the entry candle is 330 to 640 s before the close (not in the last 2 minutes), so 1c is primary and 2c is printed beside it"
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2:
        import json
        print(json.dumps(run(a[0], a[1]), indent=1))
    else: print(__doc__)
