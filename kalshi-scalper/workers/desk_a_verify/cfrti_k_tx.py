"""CFRTI-K-TX (the time exit), Idea Desk A, Nov 12 2026. ONE new try, registered in workers/CFRTI_K_TX_REGISTRATION.md BEFORE any exit price was read. DEVELOPMENT only (closes 2026-09-12 to before 2026-11-05); label "selected on development: it can falsify, not support".
The entry is CFRTI-K's exactly (cfrti_k_vectors.explain: same windows, look, band, spread, edge). The exit: sell at the BID of the candle ending close minus 60 s; both fees rounded up as charged for 1 contract; a missing or zero exit bid means HELD TO SETTLEMENT, counted that way.
  python3 -I cfrti_k_tx.py selftest
  python3 -I cfrti_k_tx.py dev <lists dir> <binary candles dir> <perp candles dir>                  (candle read only)
  python3 -I cfrti_k_tx.py r6 <lists dir> <binary candles dir> <perp candles dir> <root holding book15r6/> --depth1-result <DEPTH1 result file>     (ADDENDUM: refuses before 2026-11-14T00:00Z and without DEPTH1's result file)
ORDER (fixed): 1) cost screen from prices only, no result touched: median round trip (entry ask minus mid, plus mid minus exit bid, plus both fees) over the trades with a valid exit bid; above 0.05 the try CLOSES UNREAD (0 tries) and the script stops before any result is read; 2) only then the results: cash PF, mean per contract and day-clustered z for the exit version BESIDE the hold version on the identical fills, and the difference with a paired test clustered by day (one-sided z over per-day sums of exit minus hold, fixed bar 1.645); the exit version 'helps' only if its mean per contract is higher AND the paired z is at least 1.645, else 'hold stays'."""
import sys, os, math, collections, datetime, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cfrti_k as K, cfrti_k_vectors as V
RT_KILL = 0.05; Z_BAR = 1.645
DEPTH1_READ_NOT_BEFORE = __import__("calendar").timegm((2026, 11, 14, 0, 0, 0))     # the R6 book line never runs before DEPTH1 has been read
def fee_up(p): return math.ceil(0.07 * p * (1 - p) * 100 - 1e-9) / 100.0
def pf(v):
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0); return (w / l) if l > 0 else float("inf") if w else float("nan")
def day_z(vals_by_day):
    v = list(vals_by_day.values())
    if len(v) < 3: return float("nan")
    m = sum(v) / len(v); s = st.stdev(v); return m / (s / math.sqrt(len(v))) if s > 0 else float("inf")
def side_quote(side, bid, ask): return (bid, ask) if side == "yes" else (1 - ask, 1 - bid)
def trades_of(mks, binary, perp):
    """fired CFRTI-K trades with entry price and the exit bid of the held side at the candle ending close-60 s (None = hold). NO outcome is read here."""
    out = []
    for tk, mk in sorted(mks.items(), key=lambda kv: kv[1]["close"]):
        if mk["close"] < K.DEV_FROM or mk["close"] >= K.CUTOFF: continue
        e = V.explain(mk, binary.get(tk, {}), perp)
        if not e["decision"].startswith("BUY"): continue
        side = e["side"]; eb, ea = side_quote(side, e["yes_bid"], e["yes_ask"]); p = e["side_price"]; n = binary.get(tk, {}).get(mk["close"] - 60)
        xb = xa = None
        if n:
            xb, xa = side_quote(side, n[0], n[1])
            if not (xb and xb > 0): xb = None
        rt = None
        if xb is not None: rt = (ea - (eb + ea) / 2) + (((xb + xa) / 2) - xb) + fee_up(p) + fee_up(xb)
        out.append(dict(tk=tk, close=mk["close"], side=side, p=p, xb=xb, rt=rt, day=datetime.datetime.fromtimestamp(mk["close"], datetime.timezone.utc).date()))
    return out
def core(mks, binary, perp, out=print):
    T = trades_of(mks, binary, perp); v = [t for t in T if t["xb"] is not None]
    out("CAVEAT: the exit is a 1 contract sale at the DISPLAYED candle bid with no haircut or slip; candle freshness was measured on the Bitcoin 15 minute market only, not on the perp or on this exit minute.")
    out("CFRTI-K-TX | selected on development (closes %s to before %s): it can falsify, not support | fired trades %d | with a valid exit bid %d | held for want of an exit bid %d" % (datetime.datetime.fromtimestamp(K.DEV_FROM, datetime.timezone.utc).date(), datetime.datetime.fromtimestamp(K.CUTOFF, datetime.timezone.utc).date(), len(T), len(v), len(T) - len(v)))
    if not v: out("COST SCREEN: no trade has an exit bid; nothing to cost. No result read."); return None
    med = st.median(t["rt"] for t in v)
    out("COST SCREEN (prices only, no result read): median round trip %.4f over %d trades (kill above %.2f)" % (med, len(v), RT_KILL))
    if med > RT_KILL + 1e-9: out("CLOSED ON COST, UNREAD: 0 tries. No result was read."); return None
    rows = []
    for t in T:
        mk = mks[t["tk"]]; win = 1.0 if mk["yes"] == (t["side"] == "yes") else 0.0; hold = win - t["p"] - fee_up(t["p"])
        ex = (t["xb"] - t["p"] - fee_up(t["p"]) - fee_up(t["xb"])) if t["xb"] is not None else hold
        rows.append(dict(day=t["day"], hold=hold, ex=ex, held=t["xb"] is None))
    n = len(rows); H = [r["hold"] for r in rows]; X = [r["ex"] for r in rows]
    dh = collections.defaultdict(float); dx = collections.defaultdict(float); dd = collections.defaultdict(float)
    for r in rows: dh[r["day"]] += r["hold"]; dx[r["day"]] += r["ex"]; dd[r["day"]] += r["ex"] - r["hold"]
    zd = day_z(dd); mh, mx = 100 * sum(H) / n, 100 * sum(X) / n
    out("HOLD version (rounded entry fee): n %d | cash PF %.2f | mean %+.2fc | day-clustered z %.2f" % (n, pf(H), mh, day_z(dh)))
    out("EXIT version (sell at the bid of the candle ending close-60 s; held when no exit bid): n %d | cash PF %.2f | mean %+.2fc | day-clustered z %.2f" % (n, pf(X), mx, day_z(dx)))
    out("PAIRED difference (exit minus hold) %+.2fc per contract | day-clustered paired z %.2f (bar %.3f, one-sided)" % (mx - mh, zd, Z_BAR))
    helps = (mx > mh) and (zd >= Z_BAR); out("VERDICT: " + ("the exit version HELPS (mean higher and paired z at the bar), on development only" if helps else "HOLD STAYS"))
    return dict(n=n, hold=mh, exit=mx, z=zd, helps=helps)
def r6_line(mks, binary, perp, root, out=print):
    """separate line: exit at the R6 book bid at the first poll at or after close-60 s (within 4 s, else held), entry by the IOC convention at the ask seen, 6 s delay, on the development trades that have an R6 book."""
    import heldout_guard_v2 as heldout_guard; heldout_guard.refuse_heldout(root, "cfrti_k_tx.r6_line")
    import cfrti_b; cfrti_b.load_book(root, before="2026-11-05"); B = cfrti_b.book                       # only run folders dated before the cutoff are opened
    rows = []
    for t in trades_of(mks, binary, perp):
        mk = mks[t["tk"]]; polls = B.get(t["tk"])
        if not polls: continue
        fill = cfrti_b.fill_ioc(polls, t["side"], t["p"], mk["close"] - 120, 6.0)
        if fill is None: continue
        import bisect
        times = [x[0] for x in polls]; j = bisect.bisect_left(times, mk["close"] - 60)
        xb = None
        if j < len(polls) and times[j] - (mk["close"] - 60) <= 4: xb = polls[j][1] if t["side"] == "yes" else polls[j][3]
        win = 1.0 if mk["yes"] == (t["side"] == "yes") else 0.0; hold = win - fill - fee_up(fill)
        ex = (xb - fill - fee_up(fill) - fee_up(xb)) if (xb and xb > 0) else hold
        rows.append((hold, ex))
    if not rows: out("R6 BOOK LINE: no development trade with an R6 book and a fill"); return
    out("R6 BOOK LINE (separate): fills %d | hold PF %.2f mean %+.2fc | exit PF %.2f mean %+.2fc | label: no evidence at n = %d" % (len(rows), pf([r[0] for r in rows]), 100 * sum(r[0] for r in rows) / len(rows), pf([r[1] for r in rows]), 100 * sum(r[1] for r in rows) / len(rows), len(rows)))
def selftest():
    import random
    t0c = K.CUTOFF - 86400 * 20; rng = random.Random(3); mks, binary, perp = {}, {}, {}
    def window(i, spread_exit, win):
        close = t0c + 900 * i; tk = "KXBTC15M-S%d" % i; mks[tk] = dict(tk=tk, close=close, strike=100.0, yes=win, rules="")
        # YES side cheap: ask 0.15, bid 0.13; the perp has risen strongly so the model chance is high
        t0 = close - 120; binary[tk] = {t0: (0.13, 0.15), close - 60: (0.20 - spread_exit, 0.20 + spread_exit)}
        for k in range(11): perp[t0 - 60 * k] = 101.0 - 0.05 * k + (0.02 if k % 2 else 0)
        perp[close - 900] = 100.0
    for i in range(60): window(i, 0.01, i % 6 == 0)
    lines = []; r = core(mks, binary, perp, out=lines.append); assert r is not None and r["n"] == 60, lines
    assert any(l.startswith("COST SCREEN") for l in lines) and not any("CLOSED ON COST" in l for l in lines), lines
    mks2, b2, p2 = {}, {}, {}; mks, binary, perp = mks2, b2, p2
    for i in range(60): window(i, 0.08, i % 6 == 0)                               # a wide exit spread (16c) must close the try UNREAD
    lines2 = []; assert core(mks, binary, perp, out=lines2.append) is None and any("CLOSED ON COST, UNREAD" in l for l in lines2) and not any(l.startswith("HOLD version") for l in lines2), lines2
    # no outcome is touched before the screen closes: poison the results and the closed path must still work
    for m in mks.values(): m["yes"] = None
    assert core(mks, binary, perp, out=lambda s: None) is None
    # missing exit candle = held to settlement, counted
    mks3, b3, p3 = {}, {}, {}; mks, binary, perp = mks3, b3, p3
    for i in range(30): window(i, 0.01, i % 6 == 0)
    for tk in list(binary)[:10]: del binary[tk][mks[tk]["close"] - 60]
    l3 = []; core(mks, binary, perp, out=l3.append); assert any("held for want of an exit bid 10" in l for l in l3), l3
    assert fee_up(0.15) == 0.01 and fee_up(0.5) == 0.02
    print("CFRTI-K-TX SELFTEST OK (cost screen first and unread on a wide spread, both fees rounded up, missing exit = held and counted, paired test)")
if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["selftest"]: selftest()
    elif a[:1] == ["dev"] and len(a) >= 4:
        if "--r6" in a: sys.exit("REFUSED: the R6 book line is a separate command (r6) that runs only after DEPTH1's read (Head, Nov 12)")
        mks = K.load_markets(a[1]); binary = K.load_binary(a[2]); perp = K.load_perp(a[3]); core(mks, binary, perp)
    elif a[:1] == ["r6"] and len(a) >= 5:                                  # r6 <lists> <candles> <perp> <R6 root> --depth1-result <DEPTH1_RESULT.md or depth1_result.txt>
        import time as _t
        if _t.time() < DEPTH1_READ_NOT_BEFORE: sys.exit("REFUSED: the R6 book line runs only on or after 2026-11-14T00:00Z, after DEPTH1's read")
        if "--depth1-result" not in a or not os.path.isfile(a[a.index("--depth1-result") + 1]): sys.exit("REFUSED: DEPTH1's read marker (its result file) must exist: pass --depth1-result <path>")
        mks = K.load_markets(a[1]); binary = K.load_binary(a[2]); perp = K.load_perp(a[3]); r6_line(mks, binary, perp, a[4])
    else: sys.exit(__doc__)
