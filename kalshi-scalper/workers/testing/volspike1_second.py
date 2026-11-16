#!/usr/bin/env python3
"""VOLSPIKE1 (Testing Desk, Nov 16, 2026). Research only: reads one sqlite extract, writes nothing, prints aggregates only.
Rule: VOLSPIKE1_REGISTRATION.md. Hand case: VOLSPIKE1_HAND_CASE.md (committed first). Test: test_volspike1_second.py (invented rows only).
Usage: volspike1_second.py <extract.sqlite>
"""
import hashlib, math, sqlite3, sys, datetime

NC15 = ("KXGOLD15M", "KXSILVER15M", "KXCOPPER15M", "KXPLATINUM15M", "KXPALLADIUM15M", "KXWTI15M", "KXNATGAS15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M")
STANDARD = ("KXGOLD15M", "KXPLATINUM15M", "KXPALLADIUM15M")
CUT_TS = 1791043200
E_LOOK, P_LOOK, MIN_PRIOR, MULT, STILL, LO, HI, N, CAP = 600, 660, 5, 3.0, 0.01, 0.50, 0.80, 10, 0.99
HAIRCUTS = (0.0, 0.01, 0.02)


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


def two_sided(q): return q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1] < 1


def median(v):
    s = sorted(v); k = len(s)
    return s[k // 2] if k % 2 else (s[k // 2 - 1] + s[k // 2]) / 2


def mid(q): return round((q[0] + q[1]) / 2, 6)


def trades(markets, cands):
    """markets: [(ticker, series, close_ts, result)]; cands {ticker: {end_ts: (bid, ask, volume)}} -> (trades, baseline trades, skips)"""
    out, base, sk = [], [], {"no_candle": 0, "no_prior": 0, "no_spike": 0, "moved": 0, "band": 0}
    for tk, s, c, r in sorted(markets, key=lambda m: (m[2], m[0])):
        cs = cands.get(tk, {}); e, p = cs.get(c - E_LOOK), cs.get(c - P_LOOK)
        side = ask = None
        if two_sided(e):
            side = "yes" if mid(e) >= 0.5 else "no"
            ask = e[1] if side == "yes" else round(1 - e[0], 6)
            if LO <= ask <= HI: base.append((c, tk, side, ask, r))
        if not (two_sided(e) and two_sided(p)): sk["no_candle"] += 1; continue
        prior = [q[2] for end, q in cs.items() if end <= c - P_LOOK and q[2] is not None and q[2] > 0]
        if len(prior) < MIN_PRIOR: sk["no_prior"] += 1; continue
        if not (e[2] is not None and e[2] >= MULT * median(prior)): sk["no_spike"] += 1; continue
        if round(abs(mid(e) - mid(p)), 6) > STILL: sk["moved"] += 1; continue
        if not (LO <= ask <= HI): sk["band"] += 1; continue
        out.append((c, tk, side, ask, r))
    return out, base, sk


def cash(t, h):
    price = min(round(t[3] + h, 6), CAP)
    if t[4] not in ("yes", "no"): return round(-fee_up_order(price), 9)          # void: price refunded, entry fee kept
    return round(N * ((1.0 if t[2] == t[4] else 0.0) - price) - fee_up_order(price), 9)


def utc_day(ts): return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")


def block(tr, h, day_of=utc_day):
    cs = [cash(t, h) for t in tr]; k = len(cs); h2 = k // 2
    return {"n": k, "wins": sum(1 for v in cs if v > 0), "net": sum(cs), "pf": pf(cs), "h1": pf(cs[:h2]), "h2": pf(cs[h2:]), "z": day_z([(day_of(t[0]), c) for t, c in zip(tr, cs)])}


def verdict(b1, b2, base1=None, base2=None):
    """base1, base2: the no-spike baseline blocks at 1c and 2c; a spike result that clears 1.5 while the baseline also clears it is not a spike finding (Auditor B)"""
    if base1 is not None and (base1["pf"] >= 1.5 or base2["pf"] >= 1.5): return False
    return b2["n"] >= 80 and b2["pf"] >= 1.5 and b1["pf"] >= 1.5 and b2["h1"] >= 1.0 and b2["h2"] >= 1.0 and b2["z"] is not None and b2["z"] >= 2.0


def load(path):
    with open(path, "rb") as fh: sha = hashlib.sha256(fh.read()).hexdigest()
    db = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    ms = [m for m in db.execute("select ticker, series, close_ts, result from market") if m[1] in NC15]
    late = [m for m in ms if m[2] >= CUT_TS]
    if late: raise SystemExit("REFUSED: %d selected markets close at or after the 2026-10-03T16:00Z cut; close_ts min %d max %d" % (len(late), min(m[2] for m in ms), max(m[2] for m in ms)))
    close_of = {m[0]: m[2] for m in ms}; cands, dropped = {}, 0
    for tk, end, bid, ask, vol in db.execute("select ticker, end_ts, bid_c, ask_c, volume from candle"):
        if tk not in close_of: continue
        if end > close_of[tk]: dropped += 1; continue
        cands.setdefault(tk, {})[end] = (bid, ask, vol)
    return sha, ms, cands, dropped


def show(label, tr):
    bs = {h: block(tr, h) for h in HAIRCUTS}
    print(f"{label}: n {len(tr)}")
    for h in HAIRCUTS:
        b = bs[h]; print(f"  h {h:.2f}: wins {b['wins']} net {b['net']:.2f} PF {b['pf']:.4f} half1 {b['h1']:.4f} half2 {b['h2']:.4f} dayz {b['z'] if b['z'] is None else round(b['z'], 4)}")
    return bs


def main(path):
    sha, ms, cands, dropped = load(path)
    print("VOLSPIKE1 extract sha256", sha, "markets", len(ms), "series", len(set(m[1] for m in ms)), "candles after close dropped", dropped, "close_ts min", min(m[2] for m in ms), "max", max(m[2] for m in ms), "(refused if any >= %d)" % CUT_TS)
    tr, base, sk = trades(ms, cands)
    print("skips", sk)
    bs = show("VOLSPIKE1", tr)
    bb = {h: block(base, h) for h in HAIRCUTS}
    print(f"  baseline (same E candle and band, no spike or still-price condition) n {len(base)}: 1c PF {bb[0.01]['pf']:.4f} 2c PF {bb[0.02]['pf']:.4f}; spike minus baseline PF: 1c {bs[0.01]['pf'] - bb[0.01]['pf']:.4f} 2c {bs[0.02]['pf'] - bb[0.02]['pf']:.4f}")
    print(f"  pass (1c and 2c bars, and the baseline must not itself clear 1.5): {verdict(bs[0.01], bs[0.02], bb[0.01], bb[0.02])}   (development data already read for OIREL-X, no held-out inside: a pass is a lead for the forward shadow, not a pass; favourite-late family, a closed family, only the spike is new)")
    std = [t for t in tr if t[1].split("-")[0] in STANDARD]
    if std:
        sb = {h: block(std, h) for h in HAIRCUTS}
        print(f"  standard series (gold, platinum, palladium; both bars as flags): n {len(std)} 1c PF {sb[0.01]['pf']:.4f} 2c PF {sb[0.02]['pf']:.4f}")
    show("baseline detail", base)


if __name__ == "__main__":
    main(sys.argv[1])
