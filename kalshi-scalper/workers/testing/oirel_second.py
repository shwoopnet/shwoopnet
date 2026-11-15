#!/usr/bin/env python3
"""OIREL haircut recompute, BUILD 2 (Testing Desk, Nov 15, 2026). Research only: reads one sqlite extract, sends nothing, writes nothing, prints aggregates only (no ticker).
Built from the card (oirel.py docstring and decide(), FALS5 check 2), the haircut rule (rnd-queue C1 to C11) and Desk A's input list ONLY; not from Desk A's reader. Hand case: OIREL_SECOND_HAND_CASE.md (committed first). Test: test_oirel_second.py (INVENTED rows only).
Usage: oirel_second.py <extract.sqlite> <split_ts>      (the extract is decompressed from OIREL_extract.sqlite.xz by the caller; its raw sha256 is printed)
"""
import hashlib, math, sqlite3, sys

SERIES, RTHR, BACK, LOOK, FILL, LO, HI, CONTRACTS, CAP = "KXBTC15M", 0.26764675317954373, 360, 180, 120, 0.05, 0.50, 10, 0.99
HAIRCUTS = (0.0, 0.01, 0.02)
BAR_PF1, BAR_HALF, BAR_PF2, TOL = 1.3, 1.0, 1.0, 1e-9


def fee_up_order(p, n=CONTRACTS): return math.ceil(0.07 * n * p * (1 - p) * 100 - 1e-9) / 100


def two_sided(c): return c is not None and c[0] is not None and c[1] is not None and 0 < c[0] < c[1] < 1


def side_ask(c, side): return c[1] if side == "yes" else round(1 - c[0], 6)


def load(path):
    with open(path, "rb") as fh: raw = fh.read()
    sha = hashlib.sha256(raw).hexdigest()
    db = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    markets = db.execute("select ticker, series, close_ts, result from market order by close_ts, ticker").fetchall()
    cands, dropped = {}, 0
    close_of = {m[0]: m[2] for m in markets}
    for tk, end, bid, ask, vol, oi in db.execute("select ticker, end_ts, bid_c, ask_c, volume, oi from candle"):
        if tk not in close_of: continue
        if end > close_of[tk]: dropped += 1; continue
        cands.setdefault(tk, {})[end] = (bid, ask, vol, oi)
    return sha, markets, cands, dropped


def decide(cs, close):
    """-> ('nodata'|'nofire'|'nottwo'|'noside'|'trade', side, raw ask on the fill candle)"""
    s, p = cs.get(close - LOOK), cs.get(close - BACK)
    if s is None or p is None or not s[3] or not p[3] or p[3] <= 0: return ("nodata", None, None)
    doi = s[3] - p[3]
    if not doi / p[3] > RTHR: return ("nofire", None, None)
    if not two_sided(s): return ("nottwo", None, None)
    side = next((sd for sd in ("yes", "no") if LO <= side_ask(s, sd) <= HI), None)
    if side is None: return ("noside", None, None)
    f = cs.get(close - FILL)
    if f is None or f[0] is None or f[1] is None: return ("nodata", None, None)
    if not two_sided(f): return ("nottwo", None, None)
    a = side_ask(f, side)
    if not 0 < a < 1: return ("nottwo", None, None)
    return ("trade", side, a)


def pf(vals):
    pos = sum(v for v in vals if v > 0); neg = abs(sum(v for v in vals if v < 0))
    return math.inf if neg == 0 else (None if pos == 0 else pos / neg)


def cash_of(side, a, result, h):
    p = min(round(a + h, 6), CAP); fee = fee_up_order(p)
    if result not in ("yes", "no"): return -fee, p, True           # a void refunds the price and keeps the fee
    return CONTRACTS * ((1.0 if result == side else 0.0) - p) - fee, p, False


def run(path, split):
    sha, markets, cands, dropped = load(path)
    cnt = {"markets_in_extract": len(markets), "other_series_ignored": 0, "windows": 0, "trades": 0, "nodata": 0, "nofire": 0, "nottwo": 0, "noside": 0, "voids": 0, "candles_dropped_after_close": dropped}
    trades = []
    for tk, series, close, result in markets:
        if series != SERIES: cnt["other_series_ignored"] += 1; continue
        cnt["windows"] += 1
        kind, side, a = decide(cands.get(tk, {}), close)
        if kind != "trade": cnt[kind] += 1; continue
        trades.append({"tk": tk, "fill_t": close - FILL, "close": close, "side": side, "a": a, "result": result})
    trades.sort(key=lambda t: (t["fill_t"], t["tk"])); cnt["trades"] = len(trades)
    for t in trades:
        t["cash"] = {}
        for h in HAIRCUTS: t["cash"][h], _, v = cash_of(t["side"], t["a"], t["result"], h)
        cnt["voids"] += 1 if t["result"] not in ("yes", "no") else 0
    out = {"extract_sha256": sha, "split_ts": split, "counts": cnt, "label": "upper bound, not fill-checked; fee mode per-order rounded"}
    n = len(trades); h2 = n // 2
    for h in HAIRCUTS:
        allc = [t["cash"][h] for t in trades]; first, second = allc[:h2], allc[h2:]
        disc = [t["cash"][h] for t in trades if t["close"] < split]; val = [t["cash"][h] for t in trades if t["close"] >= split]
        out["h%.2f" % h] = {"n": n, "wins": sum(1 for v in allc if v > 0), "net": sum(allc), "pf": pf(allc) if allc else None, "half1_pf": pf(first) if first else None, "half2_pf": pf(second) if second else None,
                            "half1_net": sum(first), "half2_net": sum(second), "discovery_n": len(disc), "discovery_pf": pf(disc) if disc else None, "discovery_net": sum(disc), "validation_n": len(val), "validation_pf": pf(val) if val else None, "validation_net": sum(val)}
    ge = lambda x, y: x is not None and x >= y - TOL
    r1, r2 = out["h0.01"], out["h0.02"]
    out["counts_toward_20_to_30"] = bool(ge(r1["pf"], BAR_PF1) and ge(r1["half1_pf"], BAR_HALF) and ge(r1["half2_pf"], BAR_HALF) and ge(r2["pf"], BAR_PF2))
    out["primary_haircut_note"] = "C8: the fill candle ends 120 s before the close, so 2c is also printed as primary; the C7 rule needs 1c PF >= 1.3 with both halves >= 1.0 and 2c PF >= 1.0"
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2:
        import json
        print(json.dumps(run(a[0], int(a[1])), indent=1, default=lambda x: "inf" if x == math.inf else str(x)))
    else: print(__doc__)
