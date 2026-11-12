"""CFRTI-K development scorer (workers/CFRTI_K_REGISTRATION.md sections 7 and 8). Idea Desk A, written Nov 12 2026 BEFORE its data landed.
Kalshi-only: KXBTC15M 1 minute candles for the decision price, PERPBTC1M reference price for the index. DEVELOPMENT only: closes before 2026-11-05T00:00:00Z.
  python3 -I cfrti_k.py selftest                                  synthetic candles with a planted edge; checks the arithmetic and prints every line
  python3 -I cfrti_k.py dev <lists dir> <binary candles dir> <perp candles file> [<kraken minute csv>]
        <lists dir>/<binary candles dir>: kalshi-pull run folders (manifest.json + gz bodies); <perp candles>: the PERPBTC1M kalshi-pull run folder (index = mid of bid and ask close, CFRTI_K_REGISTRATION section 9) or a json/csv file; <kraken minute csv>: ts,price per whole minute for the lead/lag line (optional).
Rules fixed in the registration: decision candle = end_period_ts == close - 120 s; ask = yes_ask close, bid = yes_bid close, spread <= 0.03, cheap side band 0.05 to 0.30;
index = perp reference at close-120 s and the 10 earlier whole minutes, >= 6 log changes, sample sd * sqrt(4/3); model chance Phi(ln(index/strike)/sd); edge >= 0.05;
1 contract held to settlement, fee 0.07 p (1-p) unrounded. Thirds = three contiguous groups of UTC close days. z = day-clustered mean/se (bar 5.46)."""
import gzip, json, csv, math, os, sys, random, glob, datetime, collections, re, calendar, time
from statistics import NormalDist
Phi = NormalDist().cdf
CUTOFF = calendar.timegm(time.strptime("2026-11-05", "%Y-%m-%d"))
Z_BAR, EDGE, SPREAD, LO, HI = 5.46, 0.05, 0.03, 0.05, 0.30
def fee(p): return 0.07 * p * (1 - p)
def pf(v):
    a = sum(x for x in v if x > 0); b = -sum(x for x in v if x < 0); return a / b if b else float("inf")
def iso(s): return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
def num(d, k):
    """candle price field: {'close': x} or {'close_dollars': 'x'} or a bare number"""
    if d is None: return None
    for key in (k, k + "_dollars"):
        if isinstance(d, dict) and d.get(key) not in (None, ""): return float(d[key])
    return None
# ---------------------------------------------------------------- loaders (kalshi-pull run folders)
def bodies(folder):
    man = json.load(open(os.path.join(folder, "manifest.json")))
    for row in man["rows"]:
        if row.get("status") == 200 and "file" in row:
            yield json.load(gzip.open(os.path.join(folder, row["file"])))
def load_markets(folder):
    out = {}
    for b in bodies(folder):
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            if m.get("ticker", "").startswith("KXBTC15M-") and m.get("result") in ("yes", "no") and m.get("floor_strike") is not None:
                c = iso(m["close_time"])
                if c < CUTOFF: out[m["ticker"]] = dict(close=c, strike=float(m["floor_strike"]), yes=m["result"] == "yes")
    return out
def load_binary(folder):
    out = collections.defaultdict(dict)   # ticker -> end_ts -> (bid, ask)
    for b in bodies(folder):
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            tk = m.get("market_ticker") or m.get("ticker")
            for c in m.get("candlesticks", []):
                bid, ask = num(c.get("yes_bid"), "close"), num(c.get("yes_ask"), "close")
                if bid is not None and ask is not None: out[tk][int(c["end_period_ts"])] = (bid, ask)
    return out
def load_perp(path):
    """a kalshi-pull run folder (PERPBTC1M: manifest.json + gz bodies, candlesticks with bid/ask/open_interest) or a json/csv file with end_period_ts and a mark.
    The index is the MIDDLE of bid close and ask close (CFRTI_K_REGISTRATION section 9); a minute missing either is a missing mark."""
    out = {}
    def put(c):
        ts = c.get("end_period_ts", c.get("ts"))
        bid, ask = num(c.get("bid"), "close"), num(c.get("ask"), "close")
        if ts is None: return
        if bid is not None and ask is not None and bid > 0 and ask > 0: out[int(float(ts))] = (bid + ask) / 2
        elif c.get("reference_price") not in (None, ""): out[int(float(ts))] = float(c["reference_price"])
    if os.path.isdir(path):
        for b in bodies(path):
            for c in (b.get("candlesticks", []) if isinstance(b, dict) else []): put(c)
        return out
    rows = json.load(open(path)) if path.endswith(".json") else list(csv.DictReader(open(path)))
    if isinstance(rows, dict): rows = rows.get("candlesticks", rows.get("rows", []))
    for r in rows: put(r)
    return out
# ---------------------------------------------------------------- the rule
def decide(mk, cands, perp):
    t0 = mk["close"] - 120
    c = cands.get(t0)
    if not c: return None, "no decision candle"
    bid, ask = c
    if ask <= bid or ask - bid > SPREAD + 1e-9: return None, "spread over 3c or crossed"
    side = "yes" if LO <= ask <= HI else ("no" if LO <= 1 - bid <= HI else None)
    if side is None: return None, "not cheap"
    xs = [perp.get(t0 - 60 * k) for k in range(11)]
    lr = [math.log(xs[k] / xs[k + 1]) for k in range(10) if xs[k] and xs[k + 1]]
    if len(lr) < 6: return None, "under 6 changes"
    m = sum(lr) / len(lr); sd = math.sqrt(sum((x - m) ** 2 for x in lr) / (len(lr) - 1)) * math.sqrt(4 / 3)
    if sd <= 0 or not xs[0]: return None, "no volatility"
    py = Phi(math.log(xs[0] / mk["strike"]) / sd)
    p = ask if side == "yes" else 1 - bid
    chance = py if side == "yes" else 1 - py
    if chance - p < EDGE: return None, "no edge"
    win = mk["yes"] == (side == "yes")
    return dict(close=mk["close"], day=datetime.datetime.fromtimestamp(mk["close"], datetime.timezone.utc).date(), p=p, win=win, pnl=(1 if win else 0) - p - fee(p)), "trade"
def thirds(trades):
    days = sorted({t["day"] for t in trades}); n = len(days); k = [0, math.ceil(n / 3), math.ceil(2 * n / 3), n]
    return [[t for t in trades if t["day"] in set(days[k[i]:k[i + 1]])] for i in range(3)]
def zscore(trades):
    d = collections.defaultdict(float)
    for t in trades: d[t["day"]] += t["pnl"]
    v = list(d.values())
    if len(v) < 3: return float("nan")
    m = sum(v) / len(v); s = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    return m / (s / math.sqrt(len(v))) if s > 0 else float("inf")
def haircut(trades, seed=20261114, draws=1000, frac=0.34):
    rng = random.Random(seed); pnl = [t["pnl"] for t in trades]; res = []
    for _ in range(draws):
        keep = [x for x in pnl if rng.random() >= frac]
        if keep: res.append(pf(keep))
    res.sort()
    rest = sorted(pnl)[: len(pnl) - int(round(frac * len(pnl)))]    # drop the best 34% of outcomes first
    return res[len(res) // 2], res[int(0.05 * len(res))], res[int(0.95 * len(res)) - 1], pf(rest)
def lead_lag(perp, kraken):
    """correlation of 1 minute log changes, perp vs Kraken last trade, at lags -2..+2 minutes (positive lag: perp lags Kraken)"""
    ts = sorted(set(perp) & set(kraken)); out = {}
    dp = {t: math.log(perp[t] / perp[t - 60]) for t in ts if (t - 60) in perp}
    dk = {t: math.log(kraken[t] / kraken[t - 60]) for t in ts if (t - 60) in kraken}
    for lag in range(-2, 3):
        pairs = [(dp[t], dk[t - 60 * lag]) for t in dp if (t - 60 * lag) in dk]
        if len(pairs) < 30: out[lag] = None; continue
        a, b = zip(*pairs); ma, mb = sum(a) / len(a), sum(b) / len(b)
        sa = math.sqrt(sum((x - ma) ** 2 for x in a)); sb = math.sqrt(sum((x - mb) ** 2 for x in b))
        out[lag] = sum((x - ma) * (y - mb) for x, y in pairs) / (sa * sb) if sa and sb else None
    return out
def report(markets, binary, perp, kraken=None):
    trades, why = [], collections.Counter()
    for tk, mk in markets.items():
        t, w = decide(mk, binary.get(tk, {}), perp)
        why[w] += 1
        if t: trades.append(t)
    trades.sort(key=lambda t: t["close"])
    L = ["CFRTI-K DEVELOPMENT | markets %d | decisions: %s" % (len(markets), dict(why))]
    pn = [t["pnl"] for t in trades]; n = len(trades)
    if not n: L.append("no trades"); return L, trades
    th = thirds(trades); tpf = [pf([t["pnl"] for t in x]) for x in th]
    z = zscore(trades); hm, h5, h95, hb = haircut(trades)
    L.append("registered line: n %d | cash PF %.2f | mean %+.2fc | win %.1f%% | days %d | z %.2f (bar %.2f)" % (n, pf(pn), 100 * sum(pn) / n, 100 * sum(t["win"] for t in trades) / n, len({t["day"] for t in trades}), z, Z_BAR))
    L.append("thirds by date: " + " / ".join("n %d PF %.2f" % (len(x), p) for x, p in zip(th, tpf)))
    L.append("haircut (a) random 34%% drop, 1,000 draws seed 20261114: median PF %.2f (5th %.2f, 95th %.2f)" % (hm, h5, h95))
    L.append("haircut (b) best 34%% of outcomes dropped first: PF %.2f" % hb)
    label = "no evidence at n = %d" % n if n < 100 else ("FALSIFIED on development (cash PF under 1.0)" if pf(pn) < 1.0 else
            ("cleared the research bar on development" if all(p >= 1.5 for p in tpf) and z >= Z_BAR else "carried: not falsified, research bar not cleared"))
    L.append("LABEL: " + label + (" | note: the research bar is unlikely to be reachable at this size" if n < 6000 else ""))
    met = all(p >= 1.3 for p in tpf) and hm > 1.0 and hb > 1.0
    L.append("BLOCK P condition (cash PF 1.3 or better in EACH third AND both haircut lines above 1.0): %s" % ("MET" if met else "NOT MET"))
    if kraken:
        ll = lead_lag(perp, kraken)
        L.append("lead/lag, 1 minute log-change correlation perp vs Kraken at lags -2..+2: " + ", ".join("%+d: %s" % (k, "n/a" if v is None else "%.3f" % v) for k, v in ll.items()))
        ok = {k: v for k, v in ll.items() if v is not None}
        if ok:
            pk = max(ok, key=lambda k: ok[k]); L.append("peak at lag %+d%s" % (pk, " | THE PERP LAGS KRAKEN by %d minute(s)" % pk if pk >= 1 else ""))
    return L, trades
# ---------------------------------------------------------------- self test on synthetic candles
def synth(days=60, edge=True, seed=7):
    """a random-walk perpetual (every whole minute), one KXBTC15M market a quarter hour; with edge=True the book ask sits 8c under fair value in 30% of windows"""
    rng = random.Random(seed); markets, binary, perp = {}, {}, {}
    t0 = calendar.timegm(time.strptime("2026-08-01", "%Y-%m-%d")); p = 100000.0
    for m in range(days * 1440 + 30):
        p *= math.exp(rng.gauss(0, 0.0005)); perp[t0 + 60 * m] = p
    vol = 0.0005 * math.sqrt(2)      # the true two-minute volatility of the synthetic walk
    for q in range(1, days * 96):
        close = t0 + 900 * q; strike = perp[close - 900] * (1 + rng.uniform(-0.0015, 0.0015))
        final = perp[close]; yes = final > strike
        fair = Phi(math.log(perp[close - 120] / strike) / (vol * math.sqrt(1.0)))
        ask = fair - 0.08 if (edge and rng.random() < 0.3) else fair + 0.02
        ask = min(max(ask, 0.02), 0.98)
        tk = "KXBTC15M-S%d" % close
        markets[tk] = dict(close=close, strike=strike, yes=yes)
        binary[tk] = {close - 120: (round(max(ask - 0.02, 0.01), 4), round(ask, 4))}
    return markets, binary, perp
def selftest():
    # 1. hand-checked arithmetic on one trade
    mk = dict(close=10_000_000, strike=100.0, yes=True)
    perp = {mk["close"] - 120 - 60 * k: 101.0 + (0.05 if k % 2 else -0.05) for k in range(11)}
    cands = {mk["close"] - 120: (0.10, 0.12)}
    t, w = decide(mk, cands, perp)
    assert t and w == "trade" and abs(t["p"] - 0.12) < 1e-12 and t["win"] and abs(t["pnl"] - (1 - 0.12 - fee(0.12))) < 1e-12, (t, w)
    assert decide(mk, {mk["close"] - 120: (0.10, 0.16)}, perp)[1] == "spread over 3c or crossed"
    assert decide(mk, {mk["close"] - 90: (0.10, 0.12)}, perp)[1] == "no decision candle"
    assert decide(mk, cands, {k: v for k, v in perp.items() if k < mk["close"] - 120 - 300})[1] in ("under 6 changes",)
    assert pf([0.9, -0.3, -0.3]) == 1.5 and abs(thirds([dict(day=i, pnl=1) for i in range(7)] and [dict(day=i, pnl=1) for i in range(7)])[0][-1]["day"] - 2) == 0
    # 2. end to end on synthetic candles with a planted edge, and without
    for edge in (True, False):
        M, B, P = synth(edge=edge)
        kr = {ts: v * (1 + 0.00001) for ts, v in P.items()}
        L, tr = report(M, B, P, kr)
        print("--- synthetic, planted edge" if edge else "--- synthetic, no planted edge"); print("\n".join(L))
    # 3. the held-out guard: markets closing on/after the cutoff never load
    d = os.path.join(os.environ.get("TMPDIR", "/tmp"), "cfrti_k_selftest"); os.makedirs(d, exist_ok=True)
    json.dump({"rows": [{"status": 200, "file": "a.json.gz"}]}, open(d + "/manifest.json", "w"))
    json.dump({"markets": [{"ticker": "KXBTC15M-A", "close_time": "2026-11-04T23:45:00Z", "result": "yes", "floor_strike": 1.0},
                           {"ticker": "KXBTC15M-B", "close_time": "2026-11-05T00:00:00Z", "result": "yes", "floor_strike": 1.0}]}, gzip.open(d + "/a.json.gz", "wt"))
    assert list(load_markets(d)) == ["KXBTC15M-A"]
    print("SELFTEST OK (arithmetic, guards, cutoff)")
if __name__ == "__main__":
    if sys.argv[1] == "selftest": selftest()
    elif sys.argv[1] == "dev":
        kr = None
        if len(sys.argv) > 5: kr = {int(r["ts"]): float(r["price"]) for r in csv.DictReader(open(sys.argv[5]))}
        print("\n".join(report(load_markets(sys.argv[2]), load_binary(sys.argv[3]), load_perp(sys.argv[4]), kr)[0]))
    else: sys.exit(__doc__)
