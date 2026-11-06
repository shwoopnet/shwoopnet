"""STOCKPERP1..6 scorer (frozen before any outcome). Usage: python3 -I score.py <datadir> pilot|dev
datadir holds candles_1m.csv.gz (fetch.py), funding.json, cash.gz-style files cash_*.csv.gz (Yahoo 1 minute, origin/perp-data cash1m).
pilot: ONLY trading date 2026-11-05 is loaded. dev: refuses to run before 2026-12-01 and never loads 2026-12-01 or later (held out).
Held-out dates are never read by this file at all."""
import sys, os, gzip, csv, json, math, glob, statistics as st, collections, datetime as D
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York")
DATADIR, MODE = sys.argv[1], sys.argv[2]
PILOT = {"2026-11-05"}
if MODE == "dev":
    if D.date.today() < D.date(2026, 12, 1): sys.exit("dev read date is 2026-12-01")
    ALLOWED = lambda d: "2026-11-06" <= d < "2026-12-01"
else:
    ALLOWED = lambda d: d in PILOT
U = "XOM QQQ AAPL SPY SPCX GOOGL MU NFLX NVDA TSLA KO MSFT COST AMZN VZ CVX PG PLTR META".split()
CM = {r["ticker"]: float(r["median_spread_bp"]) for r in csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PERPEQ_COSTMAP.csv")))}
def et(ts): return D.datetime.fromtimestamp(ts, NY)
def dkey(ts): return et(ts).strftime("%Y-%m-%d")
def hm(ts): e = et(ts); return e.hour * 60 + e.minute
def ts_at(date, h, m): return int(D.datetime.strptime(date, "%Y-%m-%d").replace(hour=h, minute=m, tzinfo=NY).timestamp())
perp = collections.defaultdict(dict)
for r in csv.DictReader(gzip.open(os.path.join(DATADIR, "candles_1m.csv.gz"), "rt")):
    tk = r["ticker"][2:-4]
    if tk in U and r["ok"] == "1":
        ts = int(r["ts"])
        if ALLOWED(dkey(ts)) or (MODE == "pilot" and False): perp[tk][ts] = (float(r["bid_c"]), float(r["ask_c"]))
cash = collections.defaultdict(dict)
for f in glob.glob(os.path.join(DATADIR, "cash*.csv.gz")):
    for r in csv.DictReader(gzip.open(f, "rt")):
        if r["symbol"] in U and ALLOWED(dkey(int(r["ts_unix"]))): cash[r["symbol"]][int(r["ts_unix"])] = (float(r["open"]), float(r["close"]))
def mid(tk, T): q = perp[tk].get(T); return None if q is None else (q[0] + q[1]) / 2
def spr(tk, T): q = perp[tk].get(T); return None if q is None else (q[1] - q[0]) / ((q[0] + q[1]) / 2) * 1e4
def cp(tk, T): b = cash[tk].get(T - 60); return None if b is None else b[1]       # cash(T) = close of the bar starting T-60
def okq(tk, T):
    s = spr(tk, T); return s is not None and s <= 3 * CM["KX" + tk + "PERP"] and mid(tk, T) is not None
def trade(tk, Te, Tx, d):
    qe, qx = perp[tk].get(Te), perp[tk].get(Tx)
    if not (qe and qx): return None
    fill_e = qe[1] if d > 0 else qe[0]; fill_x = qx[0] if d > 0 else qx[1]
    gm = d * math.log(((qx[0] + qx[1]) / 2) / ((qe[0] + qe[1]) / 2)) * 1e4
    gc = d * math.log(fill_x / fill_e) * 1e4
    return gm, gc
events = collections.defaultdict(list)       # test -> [(date, gross_mid, gross_cross, dir)]
counts = collections.Counter()
def add(test, tk, Te, Tx, d):
    r = trade(tk, Te, Tx, d)
    if r is None: counts[test + ":missing_exit"] += 1; return
    events[test].append((dkey(Te), r[0], r[1])); rc = trade(tk, Te, Tx, -d)
    events[test + "_ctl"].append((dkey(Te), rc[0], rc[1]))
dates = sorted({dkey(ts) for tk in perp for ts in perp[tk]})
def scale(tk, date, lo, hi):
    xs = []
    for m in range(lo, hi, 5):
        T = ts_at(date, m // 60, m % 60); a, b = cp(tk, T), mid(tk, T)
        if a and b: xs.append(math.log(a / b))
    return st.median(xs) if len(xs) >= 20 else None
# SPLAG1: perp lags the cash tape in cash hours
for tk in U:
    for date in dates:
        nxt = 0
        for m in range(9 * 60 + 36, 15 * 60 + 55):
            T = ts_at(date, m // 60, m % 60)
            if T < nxt or not okq(tk, T): continue
            a, a0, b, b0 = cp(tk, T), cp(tk, T - 180), mid(tk, T), mid(tk, T - 180)
            if None in (a, a0, b, b0): continue
            sc, rp = math.log(a / a0) * 1e4, math.log(b / b0) * 1e4; gap = sc - rp
            if abs(sc) >= 15 and gap * sc > 0 and abs(gap) >= max(10, 3 * spr(tk, T)):
                counts["SPLAG1:trigger"] += 1; add("SPLAG1", tk, T, T + 180, 1 if gap > 0 else -1); nxt = T + 900
# SPAUCT1: convergence to the cash auction prints (slot open 09:31 with the previous day's scale, slot close 16:00 with the same day's morning scale)
for tk in U:
    for i, date in enumerate(dates):
        for slot, (h, mm) in (("open", (9, 31)), ("close", (16, 0))):
            T = ts_at(date, h, mm)
            if slot == "open":
                prev = (D.datetime.strptime(date, "%Y-%m-%d") - D.timedelta(days=1)).strftime("%Y-%m-%d")
                sc = None
                for k in range(1, 5):
                    prev = (D.datetime.strptime(date, "%Y-%m-%d") - D.timedelta(days=k)).strftime("%Y-%m-%d")
                    if ALLOWED(prev): sc = scale(tk, prev, 600, 930); break
            else: sc = scale(tk, date, 600, 900)
            if sc is None: counts["SPAUCT1:%s:no_scale" % slot] += 1; continue
            a, b = cp(tk, T), mid(tk, T)
            if a is None or b is None or not okq(tk, T): counts["SPAUCT1:%s:missing" % slot] += 1; continue
            dd = (math.log(a / b) - sc) * 1e4
            if abs(dd) >= max(15, 3 * spr(tk, T)):
                counts["SPAUCT1:%s:trigger" % slot] += 1; add("SPAUCT1", tk, T, T + 300, 1 if dd > 0 else -1); events["SPAUCT1_" + slot].append(events["SPAUCT1"][-1]) if events["SPAUCT1"] and events["SPAUCT1"][-1][0] == date else None
# SPLIQ1: perp-only jump, cash flat, fade
for tk in U:
    for date in dates:
        nxt = 0
        for m in range(9 * 60 + 40, 15 * 60 + 50):
            T = ts_at(date, m // 60, m % 60)
            if T < nxt or not okq(tk, T): continue
            b, b1, a, a1 = mid(tk, T), mid(tk, T - 60), cp(tk, T), cp(tk, T - 60)
            if None in (b1, a, a1): continue
            r1, c1 = math.log(b / b1) * 1e4, math.log(a / a1) * 1e4
            if abs(r1) >= max(15, 5 * spr(tk, T)) and abs(c1) <= 0.25 * abs(r1):
                counts["SPLIQ1:trigger"] += 1; add("SPLIQ1", tk, T, T + 300, -1 if r1 > 0 else 1); nxt = T + 1800
# SPFUND1: previous funding at least 2 bp (longs paid): buy after the settlement, hold 30 minutes
fr = json.load(open(os.path.join(DATADIR, "funding.json")))
for tk in U:
    rows = sorted((r["funding_time"], r["funding_rate"]) for r in fr.get("KX" + tk + "PERP", []))
    for i in range(1, len(rows)):
        ft = int(D.datetime.strptime(rows[i][0], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=D.timezone.utc).timestamp())
        if not ALLOWED(dkey(ft)) or rows[i - 1][1] < 0.0002: continue
        T = ft + 60
        if okq(tk, T): counts["SPFUND1:trigger"] += 1; add("SPFUND1", tk, T, T + 1800, 1)
# SPW1: Sunday reopen gap fade to Monday 09:25 (needs a weekend inside the allowed dates)
for tk in U:
    for date in dates:
        if D.datetime.strptime(date, "%Y-%m-%d").weekday() != 0: continue
        sun = (D.datetime.strptime(date, "%Y-%m-%d") - D.timedelta(days=1)).strftime("%Y-%m-%d"); fri = (D.datetime.strptime(date, "%Y-%m-%d") - D.timedelta(days=3)).strftime("%Y-%m-%d")
        Te, Tx, Tf = ts_at(sun, 18, 10), ts_at(date, 9, 25), None
        for m in range(16 * 60 + 55, 16 * 60 + 30, -1):
            if mid(tk, ts_at(fri, m // 60, m % 60)): Tf = ts_at(fri, m // 60, m % 60); break
        if Tf is None or not okq(tk, Te): counts["SPW1:missing"] += 1; continue
        g = math.log(mid(tk, Te) / mid(tk, Tf)) * 1e4
        if abs(g) >= max(25, 5 * spr(tk, Te)): counts["SPW1:trigger"] += 1; add("SPW1", tk, Te, Tx, -1 if g > 0 else 1)
# SPHALT1: cash print gap of 5+ minutes in a name that otherwise prints, perp quoted through it
for tk in U:
    for date in dates:
        mins = [ts_at(date, m // 60, m % 60) for m in range(9 * 60 + 30, 16 * 60)]
        have = [T in cash[tk] for T in mins]
        if sum(have) < 0.9 * len(mins): counts["SPHALT1:thin_day"] += 1; continue
        i = 6
        while i < len(mins) - 6:
            if not have[i] and have[i - 1]:
                j = i
                while j < len(mins) and not have[j]: j += 1
                if j - i >= 5 and j < len(mins) - 5:
                    counts["SPHALT1:gap"] += 1; T = mins[j] + 60; sc = scale(tk, date, 600, 900)
                    a, b = cp(tk, T), mid(tk, T)
                    if sc is not None and a and b and okq(tk, T):
                        dd = (math.log(a / b) - sc) * 1e4
                        if abs(dd) >= 20: counts["SPHALT1:trigger"] += 1; add("SPHALT1", tk, T, T + 300, 1 if dd > 0 else -1)
                i = j
            i += 1
def pf(x): w = sum(v for v in x if v > 0); l = -sum(v for v in x if v < 0); return w / l if l else float("inf") if w else 0.0
def line(name):
    ev = events.get(name, [])
    if not ev: return "%-14s n=0" % name
    out = ["%-14s n=%d dates=%d gross_mid=%+.1f gross_cross=%+.1f bp" % (name, len(ev), len({e[0] for e in ev}), st.mean(e[1] for e in ev), st.mean(e[2] for e in ev))]
    for fee in (12, 14.4, 24):
        nets = [e[2] - 2 * fee for e in ev]; out.append("net@%g=%+.1f PF %.2f" % (fee, st.mean(nets), pf(nets)))
    out.append("breakeven_fee_per_side=%+.1f bp win=%.0f%%" % (st.mean(e[2] for e in ev) / 2, 100 * sum(e[2] > 24 for e in ev) / len(ev)))
    return " | ".join(out)
print("MODE", MODE, "dates", dates, "perp names", len(perp), "cash names", len(cash))
for t in ("SPLAG1", "SPAUCT1", "SPLIQ1", "SPFUND1", "SPW1", "SPHALT1"):
    print(line(t)); print(line(t + "_ctl"))
for k in sorted(counts): print(k, counts[k])
# information: lead lag of 1 minute returns, perp mid against cash tape, shifts -3..+3 (perp shifted)
import statistics
for sh in range(-3, 4):
    xs, ys = [], []
    for tk in U:
        for date in dates:
            for m in range(9 * 60 + 40, 15 * 60 + 50):
                T = ts_at(date, m // 60, m % 60)
                a, a1, b, b1 = cp(tk, T), cp(tk, T - 60), mid(tk, T + 60 * sh), mid(tk, T + 60 * sh - 60)
                if None in (a, a1, b, b1): continue
                xs.append(math.log(a / a1)); ys.append(math.log(b / b1))
    if len(xs) > 30:
        mx, my = st.mean(xs), st.mean(ys); c = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
        print("LEADLAG shift %+d min corr %.3f n %d" % (sh, c, len(xs)))
# information: funding carry per name (daily rate in bp, share positive)
print("CARRY0 name, n_days, mean_bp_per_day, share_positive")
for tk in U:
    v = [r["funding_rate"] * 1e4 for r in fr.get("KX" + tk + "PERP", [])]
    if v: print("CARRY0", tk, len(v), "%.2f" % st.mean(v), "%.2f" % (sum(x > 0 for x in v) / len(v)))
