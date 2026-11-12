"""PERPBIN1 development scorer (workers/PERPBIN1_REGISTRATION.md). Idea Desk A, written Nov 12 2026 BEFORE any candle value was scored.
  python3 -I perpbin1.py selftest
  python3 -I perpbin1.py dev <lists dir> <binary candles dir> <PERPBTC1M run folder>
OIchg = perp open_interest at the candle ending at close-900 minus its value 900 s earlier; the top-tercile cutoff is computed from the perp candles alone (no binary, no result) over development windows
and frozen. Entry: binary candle ending close-840 s, spread <= 0.03, each try buys its own side only if that side's ask is 0.40 to 0.60; A buys YES, B buys NO when OI is rising."""
import sys, os, json, math, random, collections, datetime, calendar, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfrti_k as K
def load_oi(folder):
    out = {}
    for b in K.bodies(folder):
        for c in (b.get("candlesticks", []) if isinstance(b, dict) else []):
            if c.get("open_interest") not in (None, ""): out[int(c["end_period_ts"])] = float(c["open_interest"])
    return out
def tercile_cut(markets, oi):
    v = sorted(oi[m["close"] - 900] - oi[m["close"] - 1800] for m in markets.values() if (m["close"] - 900) in oi and (m["close"] - 1800) in oi)
    return v[(2 * len(v)) // 3] if len(v) >= 30 else None, len(v)
def rows(markets, binary, oi, cut):
    out, why = {"A": [], "B": []}, collections.Counter()
    for tk, mk in markets.items():
        a, b = oi.get(mk["close"] - 900), oi.get(mk["close"] - 1800)
        if a is None or b is None: why["no OI"] += 1; continue
        if a - b < cut: why["not rising"] += 1; continue
        c = binary.get(tk, {}).get(mk["close"] - 840)
        if not c: why["no entry candle"] += 1; continue
        bid, ask = c
        if ask <= bid or ask - bid > 0.03 + 1e-9: why["spread"] += 1; continue
        day = datetime.datetime.fromtimestamp(mk["close"], datetime.timezone.utc).date()
        took = False
        for arm, buy_yes in (("A", True), ("B", False)):
            p = ask if buy_yes else 1 - bid
            if not 0.40 - 1e-9 <= p <= 0.60 + 1e-9: continue      # cent-inclusive compare
            win = mk["yes"] == buy_yes; took = True
            out[arm].append(dict(close=mk["close"], day=day, p=p, win=win, pnl=(1 if win else 0) - p - K.fee(p)))
        if not took: why["not mid-band"] += 1; continue
        why["entered"] += 1
    return out, why
def report(markets, binary, oi):
    cut, n_oi = tercile_cut(markets, oi)
    if cut is None: return ["PERPBIN1: only %d windows with an OI change; no tercile cut" % n_oi]
    R, why = rows(markets, binary, oi, cut)
    L = ["PERPBIN1 DEVELOPMENT | markets %d | OIchg top-tercile cut %.1f over %d windows | %s" % (len(markets), cut, n_oi, dict(why))]
    for arm, label in (("A", "buy YES when OI rising"), ("B", "buy NO when OI rising")):
        t = sorted(R[arm], key=lambda x: x["close"]); n = len(t); pn = [x["pnl"] for x in t]
        if not n: L.append("try %s (%s): no trades" % (arm, label)); continue
        th = K.thirds(t); tpf = [K.pf([x["pnl"] for x in g]) for g in th]; z = K.zscore(t)
        lab = "FALSIFIED on development (cash PF under 1.0)" if n >= 100 and K.pf(pn) < 1.0 else ("no evidence at n = %d" % n if n < 100 else (
              "cleared the research bar on development" if all(p >= 1.5 for p in tpf) and K.pf(pn) >= 1.5 and z >= K.Z_BAR else "carried to the held-out"))
        L.append("try %s (%s): n %d | cash PF %.2f | mean %+.2fc | win %.1f%% | thirds %s | z %.2f (bar %.2f) | %s" % (arm, label, n, K.pf(pn), 100 * sum(pn) / n, 100 * sum(x["win"] for x in t) / n, " / ".join("n %d PF %.2f" % (len(g), p) for g, p in zip(th, tpf)), z, K.Z_BAR, lab))
    return L
def selftest():
    rng = random.Random(3); markets, binary, oi = {}, {}, {}
    t0 = calendar.timegm(time.strptime("2026-08-01", "%Y-%m-%d")); v = 1000.0
    for m in range(60 * 1440 + 40): v += rng.gauss(0, 5); oi[t0 + 60 * m] = v
    # planted: windows with rising OI have the YES side win 80% of the time at a mid-band ask
    for q in range(3, 60 * 96):
        close = t0 + 900 * q; tk = "KXBTC15M-S%d" % close
        rising = oi[close - 900] - oi[close - 1800] > 6
        yes = rng.random() < (0.8 if rising else 0.5)
        markets[tk] = dict(close=close, strike=1.0, yes=yes); binary[tk] = {close - 840: (0.48, 0.50)}
    L = report(markets, binary, oi); print("\n".join(L))
    assert "try A" in L[1] and "PF" in L[1]
    a = [l for l in L if l.startswith("try A")][0]; b = [l for l in L if l.startswith("try B")][0]
    assert float(a.split("cash PF ")[1].split()[0]) > 1.5 and float(b.split("cash PF ")[1].split()[0]) < 0.5, (a, b)
    # a market closing on/after the cutoff never loads
    assert K.load_markets.__name__ == "load_markets"      # the cutoff guard itself is tested in cfrti_k.py's selftest (a market closing at or after 2026-11-05 never loads)
    print("SELFTEST OK (tercile cut, entry rule, arms A and B)")
if __name__ == "__main__":
    if sys.argv[1] == "selftest": selftest()
    elif sys.argv[1] == "dev":
        mk_ = {tk: m for tk, m in K.load_markets(sys.argv[2]).items() if m["close"] > K.DEV_FROM}      # post-cutover development sample (CFRTI_K_REGISTRATION section 13)
        print("\n".join(report(mk_, K.load_binary(sys.argv[3]), load_oi(sys.argv[4]))))
    else: sys.exit(__doc__)
