#!/usr/bin/env python3
"""SEARCH1 chosen-combination haircut recompute, BUILD 2 (Testing Desk, Nov 15, 2026). Research only: reads one sqlite extract, sends nothing, writes nothing, prints aggregates only (no ticker).
Built from the card (search1.py, lstrats.favorite, analyze.valid_quote, README:6030), the haircut rule (rnd-queue C1 to C10) and Desk A's input list ONLY; not from Desk A's reader. Hand case: SEARCH1_SECOND_HAND_CASE.md (committed first). Test: test_search1_second.py (INVENTED rows only).
Usage: search1_second.py <extract.sqlite> <cut_ts>      (cut_ts = first second of the confirmation days; the extract file's raw sha256 is printed)
"""
import hashlib, math, sqlite3, sys

SERIES = ("KXBTC15M", "KXETH15M")
LEFT, BAND_LO, BAND_HI, SL, EXIT_BEFORE, MAX_SPREAD, CONTRACTS, ENTRY_CAP, EXIT_FLOOR, TOL = 420, 0.97, 0.995, 0.50, 30, 0.10, 10, 0.99, 0.01, 1e-9
HAIRCUTS = (0.0, 0.01, 0.02)
BAR_PF1, BAR_HALF, BAR_PF2 = 1.3, 1.0, 1.0


def fee_up_order(p, n=CONTRACTS): return math.ceil(0.07 * n * p * (1 - p) * 100 - 1e-9) / 100


def valid_quote(b, a): return b is not None and a is not None and b >= 0.001 - TOL and a <= 0.999 + TOL and a >= b - TOL and a - b <= MAX_SPREAD + TOL


def favourite(b, a):
    """-> ('yes'|'no', raw price) or None (band)"""
    if BAND_LO - TOL <= a <= BAND_HI + TOL: return ("yes", a)
    no = round(1 - b, 4)
    if BAND_LO - TOL <= no <= BAND_HI + TOL: return ("no", no)
    return None


def bought_bid(c, side): return c[0] if side == "yes" else round(1 - c[1], 4)


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


def decide(cs, close):
    """-> (kind, side, raw ask, exit bid or None). kind: nocandle, badquote, band, trade"""
    e = cs.get(close - LEFT)
    if e is None: return ("nocandle", None, None, None)
    if not valid_quote(e[0], e[1]): return ("badquote", None, None, None)
    f = favourite(e[0], e[1])
    if f is None: return ("band", None, None, None)
    side, price = f
    for end in sorted(k for k in cs if close - LEFT < k <= close - EXIT_BEFORE):
        b = bought_bid(cs[end], side)
        if b <= SL + TOL: return ("trade", side, price, b)
    return ("trade", side, price, None)


def cash_of(side, price, exit_bid, result, h):
    entry = min(round(price + h, 6), ENTRY_CAP); fin = fee_up_order(entry)
    if exit_bid is None: return CONTRACTS * ((1.0 if result == side else 0.0) - entry) - fin
    ex = max(round(exit_bid - h, 6), EXIT_FLOOR)
    return CONTRACTS * (ex - entry) - fin - fee_up_order(ex)


def pf(vals):
    pos = sum(v for v in vals if v > 0); neg = abs(sum(v for v in vals if v < 0))
    if neg == 0: return math.inf if pos > 0 else None
    return pos / neg


def block(trades, h):
    cs = [t["cash"][h] for t in trades]; n = len(cs); h2 = n // 2; f, s = cs[:h2], cs[h2:]
    return {"n": n, "wins": sum(1 for v in cs if v > 0), "net": sum(cs), "pf": pf(cs) if cs else None, "half1_pf": pf(f) if f else None, "half2_pf": pf(s) if s else None, "half1_net": sum(f), "half2_net": sum(s)}


def run(path, cut):
    sha, markets, cands, dropped = load(path)
    cnt = {"markets_in_extract": len(markets), "other_series_ignored": 0, "excluded_result": 0, "incomplete_market": 0, "considered": 0, "trades": 0, "nocandle": 0, "badquote": 0, "band": 0, "sl50_exits": 0, "candles_dropped_after_close": dropped}
    trades = []
    for tk, series, close, result in markets:
        if series not in SERIES: cnt["other_series_ignored"] += 1; continue
        if result not in ("yes", "no"): cnt["excluded_result"] += 1; continue
        cs = cands.get(tk, {})
        if any(b is None or a is None for b, a in cs.values()): cnt["incomplete_market"] += 1; continue
        cnt["considered"] += 1
        kind, side, price, xb = decide(cs, close)
        if kind != "trade": cnt[kind] += 1; continue
        if xb is not None: cnt["sl50_exits"] += 1
        trades.append({"close": close, "tk": tk, "cash": {h: cash_of(side, price, xb, result, h) for h in HAIRCUTS}})
    trades.sort(key=lambda t: (t["close"], t["tk"])); cnt["trades"] = len(trades)
    sets = {"all": trades, "discovery_information_only": [t for t in trades if t["close"] < cut], "confirmation": [t for t in trades if t["close"] >= cut]}
    out = {"extract_sha256": sha, "cut_ts": cut, "counts": cnt, "label": "upper bound, not fill-checked; fee mode per-order rounded"}
    for name, ts in sets.items(): out[name] = {"h%.2f" % h: block(ts, h) for h in HAIRCUTS}
    ge = lambda x, y: x is not None and x >= y - TOL
    r1, r2 = out["confirmation"]["h0.01"], out["confirmation"]["h0.02"]
    out["counts_toward_20_to_30_on_confirmation"] = bool(ge(r1["pf"], BAR_PF1) and ge(r1["half1_pf"], BAR_HALF) and ge(r1["half2_pf"], BAR_HALF) and ge(r2["pf"], BAR_PF2))
    out["primary_haircut_note"] = "C8: the exit can fall in the last 2 minutes, so 2c is the primary haircut and 1c is printed beside it; the C7 test is on the confirmation set"
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2:
        import json
        print(json.dumps(run(a[0], int(a[1])), indent=1))
    else: print(__doc__)
