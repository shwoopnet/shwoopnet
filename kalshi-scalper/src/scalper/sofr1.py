"""SOFR1 (workers/SOFR1_PROTOCOL.md + Amendment 1). list | fetch [--max N] | score (development only)."""
import os, sys, math, time, json, sqlite3, collections, urllib.request, datetime as dt
from statistics import NormalDist
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hist15 as h
DB = os.path.join(h.ROOT, "data", "sofr1.sqlite"); SER = "KXSOFRD"
START = int(dt.datetime(2026, 7, 1, tzinfo=dt.timezone.utc).timestamp())
def con():
    db = sqlite3.connect(DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS mk(ticker TEXT PRIMARY KEY, day TEXT, x REAL, kind TEXT, close_ts INT, result TEXT, src TEXT);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INT, bid_c REAL, ask_c REAL, PRIMARY KEY(ticker,end_ts));
CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INT);
CREATE TABLE IF NOT EXISTS rate(eff TEXT PRIMARY KEY, pct REAL);""")
    return db
def do_list():
    db = con()
    r = json.load(urllib.request.urlopen(urllib.request.Request("https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?startDate=2026-01-01&endDate=2026-12-31&type=rate", headers={"User-Agent": "shwoopnet-research-probe"}), timeout=30))
    for x in r["refRates"]: db.execute("INSERT OR REPLACE INTO rate VALUES(?,?)", (x["effectiveDate"], float(x["percentRate"])))
    for src, ep in (("hist", "/historical/markets"), ("live", "/markets")):
        cur = None
        while True:
            p = {"series_ticker": SER, "limit": 1000}
            if src == "live": p["status"] = "settled"
            if cur: p["cursor"] = cur
            d = h.get(ep, p)
            if d is None: time.sleep(20); continue
            for m in d.get("markets", []):
                if m.get("result") in ("yes", "no") and "-T" in m["ticker"]:
                    tk = m["ticker"]; x = float(tk.split("-T")[-1])
                    kind = "ge" if m.get("floor_strike") is not None else "le"
                    db.execute("INSERT OR IGNORE INTO mk VALUES(?,?,?,?,?,?,?)", (tk, tk.split("-")[1], x, kind, h.ts(m.get("close_time")), m["result"], src))
            db.commit(); cur = d.get("cursor")
            if not cur or not d.get("markets"): break
    print("rates", db.execute("select count(*) from rate").fetchone()[0], "markets", db.execute("select count(*) from mk").fetchone()[0])
def rates(db): return sorted(db.execute("select eff,pct from rate").fetchall())
def model_inputs(db, c):
    """mean and sd for a market closing at close_ts c (decision about 12 h earlier, last effective date before D-1)."""
    R = rates(db); D = dt.datetime.fromtimestamp(c, dt.timezone.utc).date()
    prev = [(e, p) for e, p in R if e < (D - dt.timedelta(days=1)).isoformat()]
    if len(prev) < 61: return None
    ch = [prev[i][1] - prev[i - 1][1] for i in range(len(prev) - 60, len(prev))]
    m = sum(ch) / 60; sd = (sum((v - m) ** 2 for v in ch) / 59) ** .5
    return prev[-1][1], max(0.01, sd)
def universe(db):
    out = []
    for tk, day, x, kind, c in db.execute("select ticker,day,x,kind,close_ts from mk"):
        if c < START: continue
        mi = model_inputs(db, c)
        if mi and abs(x - mi[0]) <= 0.15 + 1e-9: out.append((tk, c))
    return out
def do_fetch(mx):
    db = con(); U = universe(db)
    srcs = dict(db.execute("select ticker,src from mk").fetchall()); done = {r[0] for r in db.execute("select ticker from done")}
    todo = [u for u in U if u[0] not in done]; print(len(U), "universe;", len(todo), "to fetch", flush=True); n = 0
    for tk, c in todo[:mx]:
        path = f"/historical/markets/{tk}/candlesticks" if srcs[tk] == "hist" else f"/series/{SER}/markets/{tk}/candlesticks"
        try: d = h.get(path, {"start_ts": c - 30 * 3600, "end_ts": c, "period_interval": 60})
        except h.Stop: raise
        except Exception: db.execute("INSERT OR REPLACE INTO done VALUES(?,0)", (tk,)); db.commit(); continue
        if d is None: continue
        rs = []
        for x in d.get("candlesticks", []):
            b, a = (x.get("yes_bid") or {}).get("close"), (x.get("yes_ask") or {}).get("close")
            if x.get("end_period_ts") is not None: rs.append((tk, int(x["end_period_ts"]), h.fl(b), h.fl(a)))
        db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", rs); db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (tk, len(rs))); db.commit(); n += 1
    print("fetched", n)
def fee(p): return math.ceil(0.07 * 10 * p * (1 - p) * 100 - 1e-9) / 10 / 100
def do_score():
    db = con(); U = universe(db); Phi = NormalDist().cdf
    info = {tk: (x, kind, res, c) for tk, x, kind, res, c in db.execute("select ticker,x,kind,result,close_ts from mk")}
    cs = collections.defaultdict(list)
    for tk, ts, b, a in db.execute("select ticker,end_ts,bid_c,ask_c from candle"): cs[tk].append((ts, b, a))
    N = 5186; zb = NormalDist().inv_cdf(1 - 0.05 / N); print("N %d z bar %.2f universe %d" % (N, zb, len(U)))
    days = sorted({c for _, c in U}); cut = days[2 * len(days) // 3]; print("dev days", len([d for d in days if d < cut]), "of", len(days))
    tr = []
    for tk, c in U:
        if c >= cut or not cs.get(tk): continue
        x, kind, res, _ = info[tk]; mean, sd = model_inputs(db, c)
        q = [v for v in cs[tk] if v[0] <= c - 12 * 3600 and v[1] is not None and v[2] is not None]
        if not q: continue
        ts, b, a = max(q)
        if b <= 0 or a >= 1 or a <= b or a - b > 0.05 or not (0.03 <= a <= 0.30): continue
        p = 1 - Phi((x - 0.005 - mean) / sd) if kind == "ge" else Phi((x + 0.005 - mean) / sd)
        if p > a + fee(a) + 0.02: tr.append((c, (1.0 if res == "yes" else 0.0) - a - fee(a)))
    n = len(tr)
    if n == 0: print("no trades"); return
    x = [y for _, y in tr]; w = sum(v for v in x if v > 0); l = -sum(v for v in x if v < 0); m = sum(x) / n
    byd = collections.defaultdict(float); cnt = collections.Counter()
    for c, y in tr: byd[c] += y; cnt[c] += 1
    se = math.sqrt(sum((byd[c] - m * cnt[c]) ** 2 for c in byd)) / n
    print("M0 dev: n %d days %d PF %.2f mean %+.2fc z %.2f" % (n, len(byd), w / l if l > 0 else 99, 100 * m, m / se if se > 0 else 0))
if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if c == "list": do_list()
        elif c == "fetch": do_fetch(int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9)
        elif c == "score": do_score()
    except h.Stop as e: print("STOP:", e)
