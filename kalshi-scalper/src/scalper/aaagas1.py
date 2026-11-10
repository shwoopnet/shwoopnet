"""AAAGAS1 ingest and scorer (workers/AAAGAS1_PROTOCOL.md). 
  list    all settled KXAAAGASD markets (historical and live lists) -> data/aaagas1.sqlite
  fetch [--max N]   hourly candles for the registered strike universe (chosen from earlier-day values only)
  score   development only (first two thirds of scored days); holdout is read only if dev passes (not done here)
"""
import os, sys, sqlite3, math, collections, time
from statistics import NormalDist
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hist15 as h
DB = os.path.join(h.ROOT, "data", "aaagas1.sqlite")
SER = "KXAAAGASD"
import datetime as _dt
START_TS = int(_dt.datetime(2026, 7, 1, tzinfo=_dt.timezone.utc).timestamp())   # Amendment 1
def con():
    db = sqlite3.connect(DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS mk(ticker TEXT PRIMARY KEY, day TEXT, strike REAL, close_ts INT, result TEXT, src TEXT);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INT, bid_c REAL, ask_c REAL, PRIMARY KEY(ticker,end_ts));
CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INT);""")
    return db
def do_list():
    db = con()
    for src, ep in (("hist", "/historical/markets"), ("live", "/markets")):
        cur = None
        while True:
            p = {"series_ticker": SER, "limit": 1000}
            if src == "live": p["status"] = "settled"
            if cur: p["cursor"] = cur
            d = h.get(ep, p)
            if d is None: time.sleep(20); continue
            for m in d.get("markets", []):
                if m.get("result") in ("yes", "no") and m.get("floor_strike") is not None:
                    c = h.ts(m.get("close_time"))
                    db.execute("INSERT OR IGNORE INTO mk VALUES(?,?,?,?,?,?)", (m["ticker"], m["ticker"].split("-")[1], float(m["floor_strike"]), c, m["result"], src))
            db.commit(); cur = d.get("cursor")
            if not cur or not d.get("markets"): break
        print(src, db.execute("select count(*) from mk where src=?", (src,)).fetchone()[0], flush=True)
def values(db):
    """v_D per day from the settled ladder: midpoint of the highest YES-settled and the lowest NO-settled strike."""
    out = {}
    days = collections.defaultdict(list)
    for tk, day, k, c, res in db.execute("select ticker,day,strike,close_ts,result from mk"): days[(c, day)].append((k, res))
    for (c, day), v in days.items():
        ys = [k for k, r in v if r == "yes"]; ns = [k for k, r in v if r == "no"]
        if ys and ns and max(ys) < min(ns): out[c] = (max(ys) + min(ns)) / 2
    return dict(sorted(out.items()))
def universe(db):
    vals = values(db); keys = list(vals)
    rows = []
    for i in range(1, len(keys)):
        c = keys[i]; vprev = vals[keys[i - 1]]
        for tk, k in db.execute("select ticker,strike from mk where close_ts=?", (c,)):
            if c >= START_TS and vprev - 0.020 - 1e-9 <= k <= vprev + 0.060 + 1e-9: rows.append((tk, c))
    return vals, keys, rows
def do_fetch(mx):
    db = con(); vals, keys, rows = universe(db)
    srcs = dict(db.execute("select ticker,src from mk").fetchall())
    todo = [r for r in rows if r[0] not in {x[0] for x in db.execute("select ticker from done")}]
    print(len(rows), "universe markets,", len(todo), "to fetch", flush=True)
    n = 0
    for tk, c in todo[:mx]:
        if srcs[tk] == "hist":
            path = f"/historical/markets/{tk}/candlesticks"
        else:
            path = f"/series/{SER}/markets/{tk}/candlesticks"
        try:
            d = h.get(path, {"start_ts": c - 30 * 3600, "end_ts": c, "period_interval": 60})
        except h.Stop: raise
        except Exception as e:
            print("skipped", tk, str(e)[:50], flush=True); db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (tk, 0)); db.commit(); continue
        if d is None: continue
        rs = []
        for x in d.get("candlesticks", []):
            b, a = (x.get("yes_bid") or {}).get("close"), (x.get("yes_ask") or {}).get("close")
            if x.get("end_period_ts") is not None: rs.append((tk, int(x["end_period_ts"]), h.fl(b), h.fl(a)))
        db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", rs)
        db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (tk, len(rs))); db.commit(); n += 1
        if n % 100 == 0: print(n, "fetched", flush=True)
    print("fetched", n)
def fee(p): return math.ceil(0.07 * 10 * p * (1 - p) * 100 - 1e-9) / 10 / 100
def pf(x):
    w = sum(v for v in x if v > 0); l = -sum(v for v in x if v < 0); return w / l if l > 0 else 99.0
def do_score():
    db = con(); vals, keys, rows = universe(db)
    res = dict(db.execute("select ticker,result from mk").fetchall())
    strike = dict(db.execute("select ticker,strike from mk").fetchall())
    cs = collections.defaultdict(list)
    for tk, ts, b, a in db.execute("select ticker,end_ts,bid_c,ask_c from candle"): cs[tk].append((ts, b, a))
    N = 5158; zb = NormalDist().inv_cdf(1 - 0.05 / N); print("N %d z bar %.2f; days with a value %d" % (N, zb, len(keys)))
    Phi = NormalDist().cdf
    scored_days = [c for c in keys[21:] if c >= START_TS]   # 20 earlier changes needed; Amendment 1 start
    cut = scored_days[2 * len(scored_days) // 3]  # dev = days before this close_ts
    out = {"M0": [], "M1": []}
    for tk, c in rows:
        if c not in scored_days or c >= cut or not cs.get(tk): continue
        i = keys.index(c); v1 = vals[keys[i - 1]]; v2 = vals[keys[i - 2]]
        ch = [vals[keys[j]] - vals[keys[j - 1]] for j in range(i - 20, i)]
        m = sum(ch) / len(ch); sd = max(0.003, (sum((x - m) ** 2 for x in ch) / (len(ch) - 1)) ** .5)
        tgt = c - 12 * 3600
        q = [x for x in cs[tk] if x[0] <= tgt and x[1] is not None and x[2] is not None]
        if not q: continue
        ts, b, a = max(q)
        if b <= 0 or a >= 1 or a <= b or a - b > 0.05 or not (0.03 <= a <= 0.30): continue
        for name, mean in (("M0", v1), ("M1", v1 + 0.5 * (v1 - v2))):
            p = 1 - Phi((strike[tk] - mean) / sd)
            if p > a + fee(a) + 0.02:
                out[name].append((c, (1.0 if res[tk] == "yes" else 0.0) - a - fee(a)))
    for name, v in out.items():
        n = len(v); days = len({c for c, _ in v})
        if n == 0: print(name, "no trades"); continue
        x = [y for _, y in v]; mean = sum(x) / n
        byd = collections.defaultdict(float)
        for c, y in v: byd[c] += y
        se = (sum((byd[c] - mean * sum(1 for cc, _ in v if cc == c)) ** 2 for c in byd)) ** .5 / n
        print("%s dev: n %d days %d PF %.2f mean %+.2fc z %.2f" % (name, n, days, pf(x), 100 * mean, mean / se if se > 0 else 0))
if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if c == "list": do_list()
        elif c == "fetch": do_fetch(int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9)
        elif c == "score": do_score()
        else: print(__doc__)
    except h.Stop as e: print("STOP:", e)
