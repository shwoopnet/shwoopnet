#!/usr/bin/env python3
"""FLIPS0-X haircut recompute, BUILD 2 (Testing Desk, Nov 15, 2026). Research only: reads one sqlite extract, sends nothing, writes nothing, prints aggregates only (no ticker).
Built from the card (flips0x.py, ideas100.py ENTRIES L1360 / FLIPS_0 / flips / path / side_mid, ideas20.py load_btc / at / entries, lstrats.favorite, analyze.valid_quote, README:6084), the haircut rule (rnd-queue C1 to C11) and Desk A's input list ONLY; not from Desk A's reader. Hand case: FLIPS0X_SECOND_HAND_CASE.md (committed first). Test: test_flips0x_second.py (INVENTED rows only).
Usage: flips0x_second.py <extract.sqlite>      (the raw sha256 of the extract file is printed)
"""
import hashlib, math, sqlite3, sys

SERIES = ("KXXRP15M", "KXDOGE15M", "KXGOLD15M", "KXBNB15M", "KXHYPE15M", "KXNEAR15M", "KXZEC15M", "KXSILVER15M", "KXPLATINUM15M", "KXPALLADIUM15M", "KXCOPPER15M", "KXWTI15M", "KXNATGAS15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M")
LEFT, BAND_LO, BAND_HI, MAX_SPREAD, MIN_EARLIER, MOVE, CONTRACTS, CAP, TOL = 360, 0.88, 0.97, 0.10, 4, 0.004, 10, 0.99, 1e-9
HAIRCUTS = (0.0, 0.01, 0.02)
BAR_PF1, BAR_HALF, BAR_PF2 = 1.3, 1.0, 1.0


def fee_up_order(p, n=CONTRACTS): return math.ceil(0.07 * n * p * (1 - p) * 100 - 1e-9) / 100


def valid_quote(b, a): return b >= 0.001 - TOL and a <= 0.999 + TOL and a >= b - TOL and a - b <= MAX_SPREAD + TOL


def favourite(b, a):
    if BAND_LO - TOL <= a <= BAND_HI + TOL: return ("yes", a)
    no = round(1 - b, 4)
    if BAND_LO - TOL <= no <= BAND_HI + TOL: return ("no", no)
    return None


def side_mid(c, side): return (c[0] + c[1]) / 2 if side == "yes" else 1 - (c[0] + c[1]) / 2


def flips(path, literal=False):
    """literal=False (PRIMARY, the decimal-exact words): a change is ignored when |x| <= 0.004 + 1e-9. literal=True (SENSITIVITY, the research code's plain floats): ignored only when abs(x) > 0.004 is false."""
    ch = [b - a for a, b in zip(path, path[1:])]
    mv = [x for x in ch if abs(x) > (MOVE if literal else MOVE + TOL)]
    return sum(1 for a, b in zip(mv, mv[1:]) if (a > 0) != (b > 0))


def ambiguous(path): return any(abs(abs(b - a) - MOVE) <= TOL for a, b in zip(path, path[1:]))


def load(path):
    with open(path, "rb") as fh: sha = hashlib.sha256(fh.read()).hexdigest()
    db = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    markets = db.execute("select ticker, series, close_ts, result from market order by close_ts, ticker").fetchall()
    close_of = {m[0]: m[2] for m in markets}; cands, dropped, incomplete = {}, 0, 0
    for tk, end, bid, ask in db.execute("select ticker, end_ts, bid_c, ask_c from candle"):
        if tk not in close_of: continue
        if end > close_of[tk]: dropped += 1; continue
        if bid is None or ask is None: incomplete += 1; continue
        cands.setdefault(tk, {})[end] = (bid, ask)
    return sha, markets, cands, dropped, incomplete


def decide(cs, close, literal=False):
    """-> (kind, side, price, ambiguous); `ambiguous` is set for every path that reaches the flip test"""
    d = cs.get(close - LEFT)
    if d is None: return ("nodecision", None, None, False)
    if not valid_quote(*d): return ("badquote", None, None, False)
    f = favourite(*d)
    if f is None: return ("band", None, None, False)
    side, price = f
    earlier = [cs[k] for k in sorted(cs) if k < close - LEFT]
    if len(earlier) < MIN_EARLIER: return ("fewearlier", None, None, False)
    path = [side_mid(c, side) for c in earlier] + [side_mid(d, side)]; amb = ambiguous(path)
    if flips(path, literal) != 0: return ("flips", None, None, amb)
    return ("trade", side, price, amb)


def cash_of(side, price, result, h):
    p = min(round(price + h, 6), CAP)
    return CONTRACTS * ((1.0 if result == side else 0.0) - p) - fee_up_order(p)


def pf(vals):
    pos = sum(v for v in vals if v > 0); neg = abs(sum(v for v in vals if v < 0))
    if neg == 0: return math.inf if pos > 0 else None
    return pos / neg


def block(trades, h):
    cs = [t["cash"][h] for t in trades]; n = len(cs); h2 = n // 2; f, s = cs[:h2], cs[h2:]
    return {"n": n, "wins": sum(1 for v in cs if v > 0), "net": sum(cs), "pf": pf(cs) if cs else None, "half1_pf": pf(f) if f else None, "half2_pf": pf(s) if s else None, "half1_net": sum(f), "half2_net": sum(s)}


def variant(markets, cands, literal):
    cnt = {"considered": 0, "trades": 0, "nodecision": 0, "badquote": 0, "band": 0, "fewearlier": 0, "flips": 0, "ambiguous_paths": 0}; trades = []
    for tk, series, close, result in markets:
        if series not in SERIES or result not in ("yes", "no"): continue
        cnt["considered"] += 1
        kind, side, price, amb = decide(cands.get(tk, {}), close, literal)
        cnt["ambiguous_paths"] += 1 if amb else 0
        if kind != "trade": cnt[kind] += 1; continue
        trades.append({"close": close, "tk": tk, "series": series, "cash": {h: cash_of(side, price, result, h) for h in HAIRCUTS}})
    trades.sort(key=lambda t: (t["close"], t["tk"])); cnt["trades"] = len(trades)
    out = {"counts": cnt, "all": {"h%.2f" % h: block(trades, h) for h in HAIRCUTS}, "by_series_information_only": {}}
    for s in SERIES:
        ts = [t for t in trades if t["series"] == s]
        if ts: out["by_series_information_only"][s] = {"h0.01": block(ts, 0.01), "h0.02": block(ts, 0.02)}
    ge = lambda x, y: x is not None and x >= y - TOL
    r1, r2 = out["all"]["h0.01"], out["all"]["h0.02"]
    out["counts_toward_20_to_30"] = bool(ge(r1["pf"], BAR_PF1) and ge(r1["half1_pf"], BAR_HALF) and ge(r1["half2_pf"], BAR_HALF) and ge(r2["pf"], BAR_PF2))
    return out


def run(path):
    sha, markets, cands, dropped, incomplete = load(path)
    base = {"markets_in_extract": len(markets), "other_series_ignored": sum(1 for m in markets if m[1] not in SERIES), "excluded_result": sum(1 for m in markets if m[1] in SERIES and m[3] not in ("yes", "no")),
            "candles_dropped_after_close": dropped, "candles_dropped_incomplete": incomplete}
    prim = variant(markets, cands, False); sens = variant(markets, cands, True)
    prim["counts"] = {**base, **prim["counts"]}; sens["counts"] = {**base, **sens["counts"]}
    out = {"extract_sha256": sha, "label": "upper bound, not fill-checked; fee mode per-order rounded", "flip_move_reading_primary": "a minute change is ignored when |x| <= 0.004 + 1e-9 (the decimal-exact words)", **prim,
           "sensitivity_literal_float": {"reading": "a minute change is ignored only when abs(x) > 0.004 is false in plain floats (the research code)", **sens}}
    out["primary_haircut_note"] = "C8: the decision candle is 360 s before the close, so 1c is primary and 2c is printed; C11: an NC15-type series takes 2c primary, so the per-series rows carry 1c and 2c"
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 1:
        import json
        print(json.dumps(run(a[0]), indent=1, default=str))
    else: print(__doc__)
