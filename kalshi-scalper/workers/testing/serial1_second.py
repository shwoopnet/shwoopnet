#!/usr/bin/env python3
"""SERIAL1 (Testing Desk, Nov 16, 2026). Research only: reads one sqlite extract, writes nothing, prints aggregates only (no ticker).
Rule: SERIAL1_REGISTRATION.md. Hand case: SERIAL1_HAND_CASE.md (committed first). Test: test_serial1_second.py (invented rows only).
Usage: serial1_second.py <extract.sqlite>
"""
import hashlib, math, sqlite3, sys, datetime

NC15 = ("KXGOLD15M", "KXSILVER15M", "KXCOPPER15M", "KXPLATINUM15M", "KXPALLADIUM15M", "KXWTI15M", "KXNATGAS15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M")
LOOK, WIN, LO, HI, N, CAP = 600, 900, 0.35, 0.65, 10, 0.99
HAIRCUTS = (0.0, 0.01, 0.02)


def fee_up_order(p, n=N): return math.ceil(round(0.07 * n * p * (1 - p) * 100, 9)) / 100


def pf(v):
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    if neg == 0: return math.inf if pos > 0 else math.nan
    return pos / neg


def day_z(rows):
    by = {}
    for r in rows: by[r[0]] = by.get(r[0], 0.0) + r[1]
    v = list(by.values())
    if len(v) < 2: return None
    m = sum(v) / len(v); sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    return None if sd == 0 else m / (sd / math.sqrt(len(v)))


def trades(markets, cands, variant):
    """markets: [(ticker, series, close_ts, result)] ; cands: {ticker: {end_ts: (bid, ask)}} (candles after close already dropped).
    -> (list of (close_ts, ticker, side, ask, result), skip counts)"""
    res = {}
    for tk, s, c, r in markets: res[(s, c)] = r
    out, sk = [], {"no_prev": 0, "no_candle": 0, "band": 0}
    for tk, s, c, r in sorted(markets, key=lambda m: (m[2], m[0])):
        pr = res.get((s, c - WIN))
        if pr not in ("yes", "no"): sk["no_prev"] += 1; continue
        q = cands.get(tk, {}).get(c - LOOK)
        if q is None or q[0] is None or q[1] is None or not (q[0] > 0 and q[1] < 1 and q[1] > q[0]): sk["no_candle"] += 1; continue
        side = pr if variant == "C" else ("no" if pr == "yes" else "yes")
        ask = q[1] if side == "yes" else round(1 - q[0], 6)
        if not (LO <= ask <= HI): sk["band"] += 1; continue
        out.append((c, tk, side, ask, r))
    return out, sk


def cash(t, h):
    price = min(round(t[3] + h, 6), CAP)
    if t[4] not in ("yes", "no"): return round(-fee_up_order(price), 9)          # void: price refunded, entry fee kept
    return round(N * ((1.0 if t[2] == t[4] else 0.0) - price) - fee_up_order(price), 9)


def block(tr, h):
    cs = [cash(t, h) for t in tr]; k = len(cs); h2 = k // 2
    days = [(datetime.datetime.fromtimestamp(t[0], datetime.timezone.utc).strftime("%Y-%m-%d"), c) for t, c in zip(tr, cs)]
    return {"n": k, "wins": sum(1 for v in cs if v > 0), "net": sum(cs), "pf": pf(cs), "h1": pf(cs[:h2]), "h2": pf(cs[h2:]), "z": day_z(days)}


def verdict(b1, b2, k):
    return k >= 300 and b2["pf"] >= 1.3 and b2["h1"] >= 1.0 and b2["h2"] >= 1.0 and b1["pf"] >= 1.3 and b2["z"] is not None and b2["z"] >= 2.0


def load(path):
    with open(path, "rb") as fh: sha = hashlib.sha256(fh.read()).hexdigest()
    db = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    ms = [m for m in db.execute("select ticker, series, close_ts, result from market") if m[1] in NC15]
    close_of = {m[0]: m[2] for m in ms}; cands, dropped = {}, 0
    for tk, end, bid, ask in db.execute("select ticker, end_ts, bid_c, ask_c from candle"):
        if tk not in close_of: continue
        if end > close_of[tk]: dropped += 1; continue
        cands.setdefault(tk, {})[end] = (bid, ask)
    return sha, ms, cands, dropped


def main(path):
    sha, ms, cands, dropped = load(path)
    print("SERIAL1 extract sha256", sha, "markets", len(ms), "series", len(set(m[1] for m in ms)), "candles after close dropped", dropped)
    for v in ("C", "F"):
        tr, sk = trades(ms, cands, v)
        bs = {h: block(tr, h) for h in HAIRCUTS}
        print(f"variant {v}: n {len(tr)} skips {sk}")
        for h in HAIRCUTS:
            b = bs[h]; print(f"  h {h:.2f}: wins {b['wins']} net {b['net']:.2f} PF {b['pf']:.4f} half1 {b['h1']:.4f} half2 {b['h2']:.4f} dayz {b['z'] if b['z'] is None else round(b['z'], 4)}")
        print(f"  pass: {verdict(bs[0.01], bs[0.02], len(tr))}")


if __name__ == "__main__":
    main(sys.argv[1])
