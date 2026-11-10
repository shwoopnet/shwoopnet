"""HLAD2 (workers/HLAD2_PROTOCOL.md). `run` = list, choose (300 per series by md5), fetch 1-minute candles, all resumable and throttled; `score` = development half only; `status`."""
import os, sys, math, time, sqlite3, hashlib, collections
from statistics import NormalDist
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hist15 as h
DB = os.path.join(h.ROOT, "data", "hlad2.sqlite")
GROUPS = {"CRYPTO": ["KXXRPD", "KXSOLD", "KXHYPED", "KXDOGED"], "METALOIL": ["KXSILVERH", "KXWTIH"], "INDEX": ["KXINXU", "KXDJI"]}
GRP = {s: g for g, v in GROUPS.items() for s in v}
md5 = lambda s: hashlib.md5(s.encode()).hexdigest()
def con():
    db = sqlite3.connect(DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS ser(series TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS mk(ticker TEXT PRIMARY KEY, series TEXT, close_ts INT, result TEXT, src TEXT);
CREATE TABLE IF NOT EXISTS pick(ticker TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INT, bid_c REAL, ask_c REAL, PRIMARY KEY(ticker,end_ts));
CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INT);""")
    return db
def do_list(db):
    for ser in GRP:
        if db.execute("select 1 from ser where series=?", (ser,)).fetchone(): continue
        for src, ep in (("hist", "/historical/markets"), ("live", "/markets")):
            cur = None
            while True:
                p = {"series_ticker": ser, "limit": 1000}
                if src == "live": p["status"] = "settled"
                if cur: p["cursor"] = cur
                d = h.get(ep, p)
                if d is None: time.sleep(20); continue
                for m in d.get("markets", []):
                    if m.get("result") in ("yes", "no"):
                        db.execute("INSERT OR IGNORE INTO mk VALUES(?,?,?,?,?)", (m["ticker"], ser, h.ts(m.get("close_time")), m["result"], src))
                db.commit(); cur = d.get("cursor")
                if not cur or not d.get("markets"): break
        db.execute("INSERT OR REPLACE INTO ser VALUES(?)", (ser,)); db.commit()
        print("listed", ser, db.execute("select count(*) from mk where series=?", (ser,)).fetchone()[0], flush=True)
def do_pick(db):
    if db.execute("select count(*) from pick").fetchone()[0]: return
    for ser in GRP:
        v = [r[0] for r in db.execute("select ticker from mk where series=?", (ser,))]
        for tk in sorted(v, key=md5)[:300]: db.execute("INSERT OR IGNORE INTO pick VALUES(?)", (tk,))
    db.commit(); print("picked", db.execute("select count(*) from pick").fetchone()[0], flush=True)
def do_fetch(db):
    todo = db.execute("select m.ticker,m.series,m.close_ts,m.src from mk m join pick p on p.ticker=m.ticker where m.ticker not in (select ticker from done)").fetchall()
    print(len(todo), "to fetch", flush=True)
    n = 0
    for tk, ser, c, src in todo:
        path = f"/historical/markets/{tk}/candlesticks" if src == "hist" else f"/series/{ser}/markets/{tk}/candlesticks"
        try: d = h.get(path, {"start_ts": c - 45 * 60, "end_ts": c, "period_interval": 1})
        except h.Stop: raise
        except Exception: db.execute("INSERT OR REPLACE INTO done VALUES(?,0)", (tk,)); db.commit(); continue
        if d is None: continue
        rs = []
        for x in d.get("candlesticks", []):
            b, a = (x.get("yes_bid") or {}).get("close"), (x.get("yes_ask") or {}).get("close")
            if x.get("end_period_ts") is not None: rs.append((tk, int(x["end_period_ts"]), h.fl(b), h.fl(a)))
        db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", rs); db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (tk, len(rs))); db.commit(); n += 1
        if n % 100 == 0: print(n, "fetched", time.strftime("%H:%M"), flush=True)
def do_run():
    db = con(); do_list(db); do_pick(db)
    for attempt in range(60):                       # about 60 rate-limit pauses at most
        try: do_fetch(db); print("ALL_DONE", flush=True); return
        except h.Stop as e: print("pause after rate limit", str(e)[:50], flush=True); time.sleep(420)
def status():
    db = con(); print("picked", db.execute("select count(*) from pick").fetchone()[0], "done", db.execute("select count(*) from done").fetchone()[0], "with candles", db.execute("select count(*) from done where n>0").fetchone()[0])
def fee(p): return math.ceil(0.07 * 10 * p * (1 - p) * 100 - 1e-9) / 10 / 100
def do_score():
    sys.path.insert(0, "src/scalper"); import leg1
    db = con(); N = 5200; zb = NormalDist().inv_cdf(1 - 0.05 / N); print("N %d z bar %.2f" % (N, zb)); status()
    cs = collections.defaultdict(list)
    for tk, ts, b, a in db.execute("select ticker,end_ts,bid_c,ask_c from candle"): cs[tk].append((ts, b, a))
    rows = collections.defaultdict(list)
    for tk, ser, c, res in db.execute("select m.ticker,m.series,m.close_ts,m.result from mk m join pick p on p.ticker=m.ticker"): rows[GRP[ser]].append((c, tk, res))
    cells = collections.defaultdict(list); usable = collections.Counter(); held = collections.Counter()
    for g, L in rows.items():
        L.sort(); cut = len(L) // 2
        for i, (c, tk, res) in enumerate(L):
            if i >= cut: held[g] += 1; continue
            q = [x for x in cs.get(tk, []) if x[0] <= c - 1800 and x[1] is not None and x[2] is not None]
            if not q: continue
            ts, b, a = max(q)
            if b <= 0 or a >= 1 or a <= b or a - b > 0.05: continue
            for side, p, won in (("yes", a, res == "yes"), ("no", 1 - b, res == "no")):
                if 0.04 <= p <= 0.30:
                    usable[g] += 1; band = (0.04, 0.12) if p < 0.12 else (0.12, 0.30)
                    cells[(g, side, band)].append((tk.rsplit("-", 1)[0], (1.0 if won else 0.0) - p - fee(p)))
    print("dev rows with a cheap side", dict(usable), "held out (unread)", dict(held))
    out = []
    for k, v in cells.items():
        n, ncl, m, z = leg1.clustered(v); x = [y for _, y in v]; w = sum(t for t in x if t > 0); l = -sum(t for t in x if t < 0)
        out.append((m, k, n, ncl, z, w / l if l > 0 else 99.0))
    out.sort(reverse=True)
    for m, k, n, ncl, z, p in out:
        if n >= 20: print("%-8s %-3s %.2f-%.2f n %5d events %4d PF %.2f mean %+.2fc z %.2f" % (k[0], k[1], k[2][0], k[2][1], n, ncl, p, 100 * m, z))
    print("SHORTLIST:", len([o for o in out if o[2] >= 100 and o[3] >= 30 and o[0] >= 0.02 and o[4] >= zb]))
if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    if c == "run": do_run()
    elif c == "score": do_score()
    elif c == "status": status()
