#!/usr/bin/env python3
"""FAV10-X, INDEPENDENT BUILD 2 (Forensics desk, Nov 15, 2026). Written from XRPFAV10_SHADOW_SPEC_NOV15.md (claude/idea-desk-a) and the History Miner's rule text and hand case ONLY; the Miner's code and prints were not opened.
Rule: the LAST candle whose end is 570 to 640 s before the close (inclusive); two-sided 0 < yes_bid < yes_ask < 1 else no trade; favourite YES (at its ask) if yes_ask >= 1 - yes_bid, else NO at 1 - yes_bid; trade only if the favourite's price e is 0.88 to 0.92 inclusive (compared after rounding to 4 places, so exactly 0.88 and 0.92 count);
1 contract held to settlement. Entry price = min(0.99, e + h). Fee per order = ceil(round(100 * 0.07 * c * p * (1 - p), 9)) / 100 with p = the entry price, per contract = fee / c. Win pays 1; a void (result not yes or no) refunds the price and keeps the fee.
Labelled extra: the shadow logger's FIRST minute look in the span (the earliest candle in 570 to 640 s where the favourite is in the band, same band test), printed beside the primary.
usage: python3 -I fav10x_b2.py <archive_dir> <comma separated series> [--selftest]
Sources, first wins: l1b, book, e3b, alts4, alts2, alts3, rep. Markets closing before 2026-10-03T00:00Z (KXSOL15M before 1790760600). All thirds. Candles ending after the close are dropped. No result is read for a series not named on the command line."""
import sys, os, sqlite3, math, collections

SOURCES = ["l1b", "book", "e3b", "alts4", "alts2", "alts3", "rep"]
CUT, SOL_CUT = 1790985600, 1790760600
NC15 = {"KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXNATGAS15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M", "KXAUDUSD15M", "KXUSDCAD15M"}
LO, HI, LEFT_MIN, LEFT_MAX = 0.88, 0.92, 570, 640


def fee(p, c):
    return math.ceil(round(100 * 0.07 * c * p * (1 - p), 9)) / 100


def pick(cands, close, last=True):
    """cands: [(end, bid, ask)]. Returns (side, e) or None per the rule; last=True: the last candle in the span (primary); False: the first candle in the span whose favourite is in the band (shadow logger extra)."""
    span = sorted(((e, b, a) for e, b, a in cands if LEFT_MIN <= close - e <= LEFT_MAX), key=lambda x: x[0])
    if not span: return None
    for e, b, a in (reversed(span) if last else span):
        if b is None or a is None or not (0 < b < a < 1):
            if last: return None
            continue
        side, p = ("yes", a) if a >= 1 - b else ("no", round(1 - b, 4))
        p = round(p, 4)
        if LO <= p <= HI: return side, p
        if last: return None
    return None


def net(side, e, result, h, c):
    p = min(0.99, round(e + h, 4)); f = fee(p, c) / c
    if result not in ("yes", "no"): return -f
    return (1 - p - f) if result == side else (-p - f)


def pf(xs):
    g = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 and g > 0 else (g / l if l else float("nan"))


def load(arch, series):
    mk = {}
    for s in SOURCES:
        p = os.path.join(arch, s + ".sqlite")
        if not os.path.exists(p): continue
        db = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
        cut = SOL_CUT if series == "KXSOL15M" else CUT
        for tk, close, res in db.execute("select ticker, close_ts, result from market where series=? and close_ts<?", (series, cut)):
            if tk in mk: continue
            mk[tk] = {"close": close, "res": res, "src": s, "c": []}
        for tk, end, b, a in db.execute("select c.ticker, c.end_ts, c.bid_c, c.ask_c from candle c join market m on m.ticker=c.ticker where m.series=? and m.close_ts<? order by c.ticker, c.end_ts", (series, cut)):
            if tk in mk and mk[tk]["src"] == s and end <= mk[tk]["close"]: mk[tk]["c"].append((end, b, a))
    return mk


def score(mk, last=True):
    rows = []
    for tk, m in sorted(mk.items(), key=lambda kv: (kv[1]["close"], kv[0])):
        t = pick(m["c"], m["close"], last)
        if t: rows.append((m["close"], t[0], t[1], m["res"]))
    return rows


def report(series, rows, label):
    n = len(rows); wins = sum(1 for r in rows if r[1] == r[3]); voids = sum(1 for r in rows if r[3] not in ("yes", "no"))
    out = ["%s %s: n %d wins %d voids %d" % (series, label, n, wins, voids)]
    if n < 100: out[0] += "  -> no evidence at n = %d" % n
    for c in (1, 10):
        for h in (0.0, 0.01, 0.02):
            xs = [net(s, e, res, h, c) for _, s, e, res in rows]
            k = n // 2; a, b = xs[:k], xs[k:]
            out.append("  c %2d h %.2f: PF %.3f  halves %.3f / %.3f  mean %+.4f" % (c, h, pf(xs), pf(a), pf(b), (sum(xs) / n if n else float("nan"))))
    if n >= 100:
        def at(h):
            xs = [net(s, e, res, h, 1) for _, s, e, res in rows]; k = n // 2
            return pf(xs), pf(xs[:k]), pf(xs[k:])
        if series in NC15:
            p2, a2, b2 = at(0.02); ok = p2 >= 1.3 and a2 >= 1.0 and b2 >= 1.0; out.append("  PASS flag (NC15, 2c): %s" % ok)
        else:
            p1, a1, b1 = at(0.01); p2 = at(0.02)[0]; ok = p1 >= 1.3 and a1 >= 1.0 and b1 >= 1.0 and p2 >= 1.0; out.append("  PASS flag (non-NC15, 1c and 2c): %s" % ok)
    return "\n".join(out)


def selftest():
    # the Miner's hand case H1 to H6 (invented numbers), written out by hand
    assert abs(net("yes", 0.90, "yes", 0, 1) - 0.09) < 1e-9 and abs(net("yes", 0.90, "yes", 0.01, 1) - 0.08) < 1e-9 and abs(net("yes", 0.90, "yes", 0.02, 1) - 0.07) < 1e-9
    assert abs(net("yes", 0.90, "yes", 0, 10) - 0.093) < 1e-9 and fee(0.90, 10) == 0.07
    # H2: last candle bid 0.11 ask 0.13 -> NO at 0.89, result no
    close = 10000; side, e = pick([(close - 600, 0.11, 0.13)], close); assert side == "no" and e == 0.89 and abs(net(side, e, "no", 0, 1) - 0.10) < 1e-9
    assert abs(net("yes", 0.88, "no", 0, 1) + 0.89) < 1e-9                                    # H3
    assert abs(net("yes", 0.90, "void", 0, 1) + 0.01) < 1e-9                                  # H4
    both = [(close - 640, 0.85, 0.89), (close - 570, 0.89, 0.91)]; assert pick(both, close) == ("yes", 0.91)   # H5: the 570 one
    assert pick([(close - 560, 0.89, 0.91)], close) is None and pick([(close - 600, 0.92, 0.93)], close) is None and pick([(close - 600, 0.0, 0.9)], close) is None
    assert pick([(close - 640, 0.87, 0.89), (close - 570, 0.80, 0.82)], close) is None      # last candle governs
    assert pick([(close - 640, 0.87, 0.89), (close - 570, 0.80, 0.82)], close, last=False) == ("yes", 0.89)  # logger extra: first look in band
    assert abs(pf([1.3, -1.0]) - 1.3) < 1e-9
    print("selftest ok")


def main(a):
    if "--selftest" in a: return selftest()
    arch = a[0]; ser = [s for s in a[1].split(",") if s]
    print("tries =", len(ser))
    for s in ser:
        mk = load(arch, s)
        print(report(s, score(mk, True), "PRIMARY (last candle in 570-640 s)"))
        print(report(s, score(mk, False), "EXTRA, labelled: shadow logger first look in the span"))
        print()

if __name__ == "__main__": main(sys.argv[1:])
