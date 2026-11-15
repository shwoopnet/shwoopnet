#!/usr/bin/env python3
"""QR1 JUMPFADE600 (Testing Desk, Nov 15, 2026): a quick first read, rule registered BEFORE any data was read (QR1_JUMPFADE_REGISTRATION.md). Research only: reads one sqlite extract, sends nothing, writes nothing, prints aggregates only (no ticker).
Usage: qr1_jumpfade.py <extract.sqlite>      (the extract's raw sha256 is printed)
"""
import hashlib, math, sqlite3, sys
from datetime import datetime, timezone

C11 = ("KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXNATGAS15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXAUDUSD15M", "KXUSDCAD15M", "KXHYPE15M", "KXBNB15M", "KXINX15M")
D_LEFT, P_LEFT, JUMP, MAX_SPREAD, BAND_LO, BAND_HI, CONTRACTS, CAP, TOL = 600, 660, 0.10, 0.04, 0.10, 0.60, 10, 0.99, 1e-9
HAIRCUTS = (0.0, 0.01, 0.02)
MIN_N, BAR_PF, BAR_HALF, BAR_PF2 = 100, 1.3, 1.0, 1.0


def fee_up_order(p, n=CONTRACTS): return math.ceil(0.07 * n * p * (1 - p) * 100 - 1e-9) / 100


def two_sided(c): return 0 < c[0] < c[1] < 1


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


def decide(cs, close):
    d, p = cs.get(close - D_LEFT), cs.get(close - P_LEFT)
    if d is None: return ("nodecision", None, None)
    if p is None: return ("noprevious", None, None)
    if not two_sided(d) or not two_sided(p): return ("badquote", None, None)
    if d[1] - d[0] > MAX_SPREAD + TOL: return ("spread", None, None)
    jump = (d[0] + d[1]) / 2 - (p[0] + p[1]) / 2
    if abs(jump) < JUMP - TOL: return ("nofire", None, None)
    side, price = ("no", round(1 - d[0], 4)) if jump > 0 else ("yes", d[1])
    if not (BAND_LO - TOL <= price <= BAND_HI + TOL): return ("band", None, None)
    return ("trade", side, price)


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


def blocks(trades): return {"h%.2f" % h: block(trades, h) for h in HAIRCUTS}


def ge(x, y): return x is not None and x >= y - TOL


def flags(trades):
    b = blocks(trades); n = b["h0.01"]["n"]
    std = n >= MIN_N and ge(b["h0.01"]["pf"], BAR_PF) and ge(b["h0.01"]["half1_pf"], BAR_HALF) and ge(b["h0.01"]["half2_pf"], BAR_HALF) and ge(b["h0.02"]["pf"], BAR_PF2)
    c11 = n >= MIN_N and ge(b["h0.02"]["pf"], BAR_PF) and ge(b["h0.02"]["half1_pf"], BAR_HALF) and ge(b["h0.02"]["half2_pf"], BAR_HALF)
    return b, bool(std), bool(c11)


def run(path):
    sha, markets, cands, dropped, incomplete = load(path)
    cnt = {"markets_in_extract": len(markets), "excluded_result": 0, "considered": 0, "trades": 0, "nodecision": 0, "noprevious": 0, "badquote": 0, "spread": 0, "nofire": 0, "band": 0,
           "candles_dropped_after_close": dropped, "candles_dropped_incomplete": incomplete}
    trades = []
    for tk, series, close, result in markets:
        if result not in ("yes", "no"): cnt["excluded_result"] += 1; continue
        cnt["considered"] += 1
        kind, side, price = decide(cands.get(tk, {}), close)
        if kind != "trade": cnt[kind] += 1; continue
        trades.append({"close": close, "tk": tk, "series": series, "day": datetime.fromtimestamp(close, timezone.utc).strftime("%Y-%m-%d"), "cash": {h: cash_of(side, price, result, h) for h in HAIRCUTS}})
    trades.sort(key=lambda t: (t["close"], t["tk"])); cnt["trades"] = len(trades)
    std = [t for t in trades if t["series"] not in C11]; c11 = [t for t in trades if t["series"] in C11]
    out = {"extract_sha256": sha, "counts": cnt, "label": "upper bound, not fill-checked; fee mode per-order rounded", "tries": "1 rule, read as 2 groups (standard, C11)"}
    out["pooled_information_only"] = blocks(trades)
    b, ps, _ = flags(std); out["standard_group"] = {**b, "pass_standard": ps}
    b, _, pc = flags(c11); out["c11_group"] = {**b, "pass_c11": pc}
    days = sorted({t["day"] for t in trades}); cut = int(len(days) * 2 / 3)
    out["first_two_thirds_of_days_information_only"] = blocks([t for t in trades if t["day"] in days[:cut]]); out["last_third_of_days_information_only"] = blocks([t for t in trades if t["day"] in days[cut:]])
    out["by_series_information_only"] = {s: {"h0.01": block(ts, 0.01), "h0.02": block(ts, 0.02)} for s in sorted({t["series"] for t in trades}) for ts in [[t for t in trades if t["series"] == s]]}
    out["PASS"] = bool(ps or pc)
    out["evidence"] = {"standard_group": "no evidence at n = %d" % len(std) if len(std) < MIN_N else "n >= 100", "c11_group": "no evidence at n = %d" % len(c11) if len(c11) < MIN_N else "n >= 100"}
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 1:
        import json
        print(json.dumps(run(a[0]), indent=1))
    else: print(__doc__)
