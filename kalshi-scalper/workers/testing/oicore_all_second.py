#!/usr/bin/env python3
"""OICORE on every market, SECOND (blind) build, Testing Desk, Nov 17 2026. Built from README SLOT-OICORE and the readings list O1 to O11 only.
Pure function run(markets, candles, splits): markets = [(ticker, close_ts, result, series)], candles = {(ticker, end_ts): (yes_bid, yes_ask, oi)}.
splits = {series: last SEARCH UTC date}: a market is SEARCH if its UTC close date is at or before its series' date, else VALIDATE (Desk A's ENGINE1 constants; the archive ends before any held-out window)."""
import math, datetime
FLOOR_N = 20; LO, HI = 0.08, 0.50; N_CONTRACTS = 10; EPS = 1e-9

def fee_order(p, n=N_CONTRACTS): return math.ceil(round(0.07 * n * p * (1 - p) * 100, 9)) / 100          # per order, dollars (Desk A's text of the rule: ceil of the value rounded to 9 places)

def num(x):
    if x is None or isinstance(x, bool): return None
    try: v = float(x)
    except (TypeError, ValueError): return None
    return v if math.isfinite(v) else None

def rise(tk, close, candles):
    a = candles.get((tk, close - 180)); b = candles.get((tk, close - 360))
    if a is None or b is None: return None
    oa, ob = num(a[2]), num(b[2])
    return None if oa is None or ob is None else oa - ob

def quote(c):
    """two sided (0 < bid < ask < 1) -> (yes_ask, no_ask) else None; NO ask = 1 - yes bid"""
    if c is None: return None
    bid, ask = num(c[0]), num(c[1])
    if bid is None or ask is None or not (0 < bid < ask < 1): return None
    return ask, 1 - bid

def nearest_rank(vals, q):
    s = sorted(vals); k = max(1, math.ceil(q * len(s) - 1e-12)); return s[k - 1]

def day(ts): return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).date()

def entry(tk, close, candles):
    """-> ('ok', side, price) or ('no', reason)"""
    qs = quote(candles.get((tk, close - 180)))
    if qs is None: return ("no", "quote_signal")
    side = "yes" if qs[0] <= qs[1] else "no"                    # cheaper side by ask, ties YES
    price = qs[0] if side == "yes" else qs[1]                   # O5 (the Head): side AND price on the candle ending 180 s before the close
    if price < LO - EPS or price > HI + EPS: return ("no", "band")
    return ("ok", side, price)

def net(side, price, result, h):
    p = min(price + h, 0.99); pay = 1.0 if result == side else 0.0
    return pay - p - fee_order(p) / N_CONTRACTS

def pf(xs):
    g = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return None if l == 0 else g / l

def stats(rows, days):
    out = {"n": len(rows), "wins": sum(1 for r in rows if r["won"]), "days": days}
    for h, nm in ((0.01, "1c"), (0.02, "2c")):
        xs = [r["net" + nm] for r in rows]
        out["pf_" + nm] = pf(xs) if xs else None; out["net_cents_" + nm] = 100 * sum(xs) / len(xs) if xs else None
    out["signals_a_day"] = len(rows) / days if days else None
    return out

def run(markets, candles, splits, floor_n=FLOOR_N):
    res = {}
    for s in sorted({m[3] for m in markets}) + ["ALL"]:
        ms = [m for m in markets if s == "ALL" or m[3] == s]; info = {"T": None, "search_rises": 0, "no_signal": {}, "windows": {}}
        def bump(k): info["no_signal"][k] = info["no_signal"].get(k, 0) + 1
        rows = []; ds = set()
        for ser in sorted({m[3] for m in ms}):
            sm = [m for m in ms if m[3] == ser]; last = splits[ser]
            rs = [r for r in (rise(m[0], m[1], candles) for m in sm if day(m[1]) <= last) if r is not None]
            T = nearest_rank(rs, 0.9) if len(rs) >= floor_n else None
            if s != "ALL": info["T"] = T; info["search_rises"] = len(rs)
            for tk, close, result, _ in sm:
                if day(close) <= last: continue
                ds.add(day(close))
                if T is None: bump("not_seated"); continue
                r = rise(tk, close, candles)
                if r is None: bump("no_candle"); continue
                if r < T - EPS: continue
                e = entry(tk, close, candles)
                if e[0] == "no": bump(e[1]); continue
                if result not in ("yes", "no"): bump("no_result"); continue
                rows.append({"won": result == e[1], "net1c": net(e[1], e[2], result, 0.01), "net2c": net(e[1], e[2], result, 0.02)})
        info["windows"]["VALIDATE"] = stats(rows, ((max(ds) - min(ds)).days + 1) if ds else 0)
        res[s] = info
    return res

def fmt(v): return "null" if v is None else ("%.17g" % v if isinstance(v, float) else str(v))

def lines(res):
    L = []
    for s in sorted(res):
        i = res[s]; L.append("%s T %s search_rises %s no_signal %s" % (s, fmt(i["T"]), i["search_rises"], ";".join("%s=%d" % kv for kv in sorted(i["no_signal"].items()))))
        x = i["windows"]["VALIDATE"]; L.append("%s VALIDATE n %d wins %d days %d signals_a_day %s pf_1c %s pf_2c %s net_cents_1c %s net_cents_2c %s" % (s, x["n"], x["wins"], x["days"], fmt(x["signals_a_day"]), fmt(x["pf_1c"]), fmt(x["pf_2c"]), fmt(x["net_cents_1c"]), fmt(x["net_cents_2c"])))
    return L
