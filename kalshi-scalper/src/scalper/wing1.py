"""WING1 ingest and scorer (workers/WING1_PROTOCOL.md). list | fetch [--max N] | score (development only)."""
import os, sys, json, re, sqlite3, hashlib, math, time, collections
from statistics import NormalDist
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hist15 as h
DB = os.path.join(h.ROOT, "data", "wing1.sqlite")
SERIES_JSON = "/tmp/claude-0/-home-user-shwoopnet/026f6e8f-6dc4-5e3b-8c3b-e0089b12fb94/scratchpad/series.json"
COMMODITY = ["KXNATGASMON","KXSOYBEANW","KXCOFFEEEOY","KXPJMDOMM","KXPJMDOMW","KXMISOINDW","KXWTIMINM"]
INDEX = ["KXNIFTYL","KXKOSPI","KXRUTPOS"]
md5 = lambda s: hashlib.md5(s.encode()).hexdigest()
def con():
    db = sqlite3.connect(DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS ser(series TEXT PRIMARY KEY, listed INT);
CREATE TABLE IF NOT EXISTS mk(ticker TEXT PRIMARY KEY, series TEXT, close_ts INT, result TEXT, src TEXT, chosen INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INT, bid_c REAL, ask_c REAL, PRIMARY KEY(ticker,end_ts));
CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INT);""")
    return db
def do_list():
    db = con()
    S = COMMODITY + INDEX
    for ser in S:
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
                        db.execute("INSERT OR IGNORE INTO mk(ticker,series,close_ts,result,src) VALUES(?,?,?,?,?)", (m["ticker"], ser, h.ts(m.get("close_time")), m["result"], src))
                cur = d.get("cursor")
                if not cur or not d.get("markets"): break
        db.execute("INSERT OR REPLACE INTO ser VALUES(?,1)", (ser,)); db.commit()
    # choose: at most 12 per series by md5, then the first 500 by md5 (registered, no price or result used)
    db.execute("update mk set chosen=0")
    per = collections.defaultdict(list)
    for tk, ser in db.execute("select ticker,series from mk"): per[ser].append(tk)
    pick = []
    for ser, v in per.items(): pick += sorted(v, key=md5)[:50]
    for tk in pick: db.execute("update mk set chosen=1 where ticker=?", (tk,))
    db.commit()
    print("series listed", db.execute("select count(*) from ser").fetchone()[0], "settled markets", db.execute("select count(*) from mk").fetchone()[0], "chosen", len(pick))
def do_fetch(mx):
    db = con()
    todo = db.execute("select ticker,series,close_ts,src from mk where chosen=1 and ticker not in (select ticker from done)").fetchall()
    print(len(todo), "to fetch", flush=True); n = 0
    for tk, ser, c, src in todo[:mx]:
        path = f"/historical/markets/{tk}/candlesticks" if src == "hist" else f"/series/{ser}/markets/{tk}/candlesticks"
        try: d = h.get(path, {"start_ts": c - 30 * 3600, "end_ts": c, "period_interval": 60})
        except h.Stop: raise
        except Exception as e:
            db.execute("INSERT OR REPLACE INTO done VALUES(?,0)", (tk,)); db.commit(); continue
        if d is None: continue
        rs = []
        for x in d.get("candlesticks", []):
            b, a = (x.get("yes_bid") or {}).get("close"), (x.get("yes_ask") or {}).get("close")
            if x.get("end_period_ts") is not None: rs.append((tk, int(x["end_period_ts"]), h.fl(b), h.fl(a)))
        db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", rs)
        db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (tk, len(rs))); db.commit(); n += 1
    print("fetched", n)
def fee(p): return math.ceil(0.07 * 10 * p * (1 - p) * 100 - 1e-9) / 10 / 100
def do_score():
    sys.path.insert(0, "src/scalper"); import leg1
    db = con()
    cs = collections.defaultdict(list)
    for tk, ts, b, a in db.execute("select ticker,end_ts,bid_c,ask_c from candle"): cs[tk].append((ts, b, a))
    rows = []
    for tk, ser, c, res in db.execute("select ticker,series,close_ts,result from mk where chosen=1"):
        grp = "COMMODITY" if ser in COMMODITY else "INDEX"
        rows.append((grp, tk, tk.rsplit("-", 1)[0], c, res))
    N = 5184; zb = NormalDist().inv_cdf(1 - 0.05 / N); print("N %d z bar %.2f; chosen %d" % (N, zb, len(rows)))
    bygrp = collections.defaultdict(list)
    for r in rows: bygrp[r[0]].append(r)
    cells = collections.defaultdict(list); usable = collections.Counter(); held = collections.Counter()
    BANDS = [(0.04, 0.12), (0.12, 0.20), (0.20, 0.30)]
    for g, L in bygrp.items():
        L.sort(key=lambda r: r[3]); cut = 2 * len(L) // 3
        for i, (grp, tk, ev, c, res) in enumerate(L):
            if i >= cut: held[g] += 1; continue
            q = [x for x in cs.get(tk, []) if x[0] <= c - 4 * 3600 and x[1] is not None and x[2] is not None]
            if not q: continue
            ts, b, a = max(q)
            if b <= 0 or a >= 1 or a <= b or a - b > 0.05: continue
            usable[g] += 1
            for side, p, won in (("yes", a, res == "yes"), ("no", 1 - b, res == "no")):
                for lo, hi in BANDS:
                    if lo <= p < hi: cells[(g, side, (lo, hi))].append((ev, (1.0 if won else 0.0) - p - fee(p)))
    print("dev markets with a usable quote", dict(usable), "held out", dict(held))
    out = []
    for k, v in cells.items():
        n, ncl, m, z = leg1.clustered(v); x = [y for _, y in v]
        w = sum(t for t in x if t > 0); l = -sum(t for t in x if t < 0)
        out.append((m, k, n, ncl, z, w / l if l > 0 else 99.0))
    out.sort(reverse=True)
    for m, k, n, ncl, z, p in out:
        if n >= 20: print("%-5s %-3s %.2f-%.2f n %4d ev %4d PF %.2f mean %+.3f z %.2f" % (k[0], k[1], k[2][0], k[2][1], n, ncl, p, m, z))
    print("SHORTLIST:", len([o for o in out if o[2] >= 100 and o[3] >= 30 and o[0] >= 0.02 and o[4] >= zb]))
if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if c == "list": do_list()
        elif c == "fetch": do_fetch(int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9)
        elif c == "score": do_score()
    except h.Stop as e: print("STOP:", e)
