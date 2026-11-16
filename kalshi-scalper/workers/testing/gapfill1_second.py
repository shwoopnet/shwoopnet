#!/usr/bin/env python3
"""GAPFILL1 (Testing Desk, Nov 16, 2026). Research only: reads one sqlite extract, writes nothing, prints aggregates only.
Rule: GAPFILL1_REGISTRATION.md. Hand case: GAPFILL1_HAND_CASE.md (committed first). Test: test_gapfill1_second.py (invented rows only).
Usage: gapfill1_second.py <extract.sqlite>
"""
import hashlib, math, sqlite3, sys, datetime

NC15 = ("KXGOLD15M", "KXSILVER15M", "KXCOPPER15M", "KXPLATINUM15M", "KXPALLADIUM15M", "KXWTI15M", "KXNATGAS15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M")
LOOK, HALT, WIN, LO, HI, N, CAP = 600, 1800, 900, 0.35, 0.65, 10, 0.99
HAIRCUTS = (0.0, 0.01, 0.02)
CUT_TS = 1791043200          # Auditor B: drop close_ts >= this first (2026-10-03T16:00Z freeze), print the count
STANDARD = ("KXGOLD15M", "KXPLATINUM15M", "KXPALLADIUM15M")          # C11 standard series: print both the 1c and 2c bars as flags


def fee_up_order(p, n=N): return math.ceil(round(0.07 * n * p * (1 - p) * 100, 9)) / 100


def pf(v):
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    if neg == 0: return math.inf if pos > 0 else math.nan
    return pos / neg


def day_z(rows):
    by = {}
    for d, c in rows: by[d] = by.get(d, 0.0) + c
    v = list(by.values())
    if len(v) < 2: return None
    m = sum(v) / len(v); sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    return None if sd == 0 else m / (sd / math.sqrt(len(v)))


def trades(markets, cands):
    """markets: [(ticker, series, close_ts, result, strike)]; cands {ticker: {end_ts: (bid, ask)}} -> (trades (close, ticker, side, ask, result), skips)"""
    out, sk = [], {"band": 0, "zero_gap": 0, "no_candle": 0, "no_strike": 0}
    by = {}
    for m in markets: by.setdefault(m[1], []).append(m)
    for s, ms in by.items():
        ms.sort(key=lambda m: (m[2], m[0]))
        for i in range(1, len(ms)):
            if ms[i][2] - ms[i - 1][2] < HALT: continue
            ref = ms[i - 1][4]
            ks = [ms[i]]
            if i + 1 < len(ms) and ms[i + 1][2] == ms[i][2] + WIN: ks.append(ms[i + 1])     # K2: the next close, 900 s later (a step of 900 is never a halt)
            for k in ks:
                tk, _, c, r, strike = k
                if strike is None or ref is None: sk["no_strike"] += 1; continue
                gap = strike - ref
                if gap == 0: sk["zero_gap"] += 1; continue
                q = cands.get(tk, {}).get(c - LOOK)
                if q is None or q[0] is None or q[1] is None or not (0 < q[0] < q[1] < 1): sk["no_candle"] += 1; continue
                side = "no" if gap > 0 else "yes"
                ask = q[1] if side == "yes" else round(1 - q[0], 6)
                if not (LO <= ask <= HI): sk["band"] += 1; continue
                out.append((c, tk, side, ask, r))
    out.sort(key=lambda t: (t[0], t[1]))
    return out, sk


def cash(t, h):
    price = min(round(t[3] + h, 6), CAP)
    if t[4] not in ("yes", "no"): return round(-fee_up_order(price), 9)          # void: price refunded, entry fee kept
    return round(N * ((1.0 if t[2] == t[4] else 0.0) - price) - fee_up_order(price), 9)


def utc_day(ts): return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")


def block(tr, h, day_of=utc_day):
    cs = [cash(t, h) for t in tr]; k = len(cs); h2 = k // 2
    return {"n": k, "wins": sum(1 for v in cs if v > 0), "net": sum(cs), "pf": pf(cs), "h1": pf(cs[:h2]), "h2": pf(cs[h2:]), "z": day_z([(day_of(t[0]), c) for t, c in zip(tr, cs)])}


def verdict(b1, b2):
    return b2["n"] >= 80 and b2["pf"] >= 1.5 and b2["h1"] >= 1.0 and b2["h2"] >= 1.0 and b1["pf"] >= 1.5 and b2["z"] is not None and b2["z"] >= 2.0


CUT_DROPPED = 0


def load(path):
    with open(path, "rb") as fh: sha = hashlib.sha256(fh.read()).hexdigest()
    db = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    allm = [m for m in db.execute("select ticker, series, close_ts, result, strike from market") if m[1] in NC15]
    late = [m for m in allm if m[2] >= CUT_TS]
    if late: raise SystemExit("REFUSED: %d selected markets close at or after the 2026-10-03T16:00Z cut; close_ts min %d max %d" % (len(late), min(m[2] for m in allm), max(m[2] for m in allm)))
    ms = allm; global CUT_DROPPED; CUT_DROPPED = 0
    close_of = {m[0]: m[2] for m in ms}; cands, dropped = {}, 0
    for tk, end, bid, ask in db.execute("select ticker, end_ts, bid_c, ask_c from candle"):
        if tk not in close_of: continue
        if end > close_of[tk]: dropped += 1; continue
        cands[tk] = cands.get(tk, {}); cands[tk][end] = (bid, ask)
    return sha, ms, cands, dropped


def main(path):
    sha, ms, cands, dropped = load(path)
    print("GAPFILL1 extract sha256", sha, "markets", len(ms), "series", len(set(m[1] for m in ms)), "candles after close dropped", dropped, "close_ts min", min(m[2] for m in ms), "max", max(m[2] for m in ms), "(refused if any >= %d)" % CUT_TS)
    tr, sk = trades(ms, cands)
    bs = {h: block(tr, h) for h in HAIRCUTS}
    print(f"n {len(tr)} skips {sk}")
    for h in HAIRCUTS:
        b = bs[h]; print(f"  h {h:.2f}: wins {b['wins']} net {b['net']:.2f} PF {b['pf']:.4f} half1 {b['h1']:.4f} half2 {b['h2']:.4f} dayz {b['z'] if b['z'] is None else round(b['z'], 4)}")
    print(f"  pass (2c primary bar): {verdict(bs[0.01], bs[0.02])}   (development data already read for OIREL-X: a pass is a lead for the forward shadow, not a pass; nested with ADJWIN1's momentum arm, not independent)")
    std = [t for t in tr if t[1].split("-")[0] in STANDARD]
    if std:
        sb = {h: block(std, h) for h in HAIRCUTS}
        print(f"  standard series (gold, platinum, palladium; C11, both bars as flags): n {len(std)} 1c PF {sb[0.01]['pf']:.4f} 2c PF {sb[0.02]['pf']:.4f} halves(2c) {sb[0.02]['h1']:.4f} {sb[0.02]['h2']:.4f}")


if __name__ == "__main__":
    main(sys.argv[1])
