"""AAASPREAD1 (workers/AAASPREAD1_PROTOCOL.md): daily vs weekly AAA gas ladder, same observation, locked pair. list | fetch | score"""
import os, sys, math, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hist15 as h, aaagas1 as a
SER = "KXAAAGASW"
def con():
    db = a.con()
    db.executescript("""CREATE TABLE IF NOT EXISTS mkw(ticker TEXT PRIMARY KEY, day TEXT, strike REAL, close_ts INT, result TEXT, src TEXT);
CREATE TABLE IF NOT EXISTS candlew(ticker TEXT, end_ts INT, bid_c REAL, ask_c REAL, PRIMARY KEY(ticker,end_ts));
CREATE TABLE IF NOT EXISTS donew(ticker TEXT PRIMARY KEY, n INT);""")
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
                    db.execute("INSERT OR IGNORE INTO mkw VALUES(?,?,?,?,?,?)", (m["ticker"], m["ticker"].split("-")[1], float(m["floor_strike"]), h.ts(m.get("close_time")), m["result"], src))
            db.commit(); cur = d.get("cursor")
            if not cur or not d.get("markets"): break
    print("weekly settled markets", db.execute("select count(*) from mkw").fetchone()[0])
def pairs(db):
    vals, keys, rows = a.universe(db)
    uni = {tk for tk, c in rows}
    wk = {(day, round(k, 3)): tk for tk, day, k in db.execute("select ticker,day,strike from mkw")}
    out = []
    for tk, day, k in db.execute("select ticker,day,strike from mk"):
        if tk in uni and (day, round(k, 3)) in wk: out.append((tk, wk[(day, round(k, 3))], day))
    return out
def do_fetch(mx):
    db = con(); P = pairs(db)
    src = dict(db.execute("select ticker,src from mkw").fetchall()); close = dict(db.execute("select ticker,close_ts from mkw").fetchall())
    done = {r[0] for r in db.execute("select ticker from donew")}
    todo = [w for _, w, _ in P if w not in done]
    print(len(P), "pairs;", len(todo), "weekly candles to fetch", flush=True); n = 0
    for w in todo[:mx]:
        c = close[w]; path = f"/historical/markets/{w}/candlesticks" if src[w] == "hist" else f"/series/{SER}/markets/{w}/candlesticks"
        try: d = h.get(path, {"start_ts": c - 30 * 3600, "end_ts": c, "period_interval": 60})
        except h.Stop: raise
        except Exception: db.execute("INSERT OR REPLACE INTO donew VALUES(?,0)", (w,)); db.commit(); continue
        if d is None: continue
        rs = []
        for x in d.get("candlesticks", []):
            b, aa = (x.get("yes_bid") or {}).get("close"), (x.get("yes_ask") or {}).get("close")
            if x.get("end_period_ts") is not None: rs.append((w, int(x["end_period_ts"]), h.fl(b), h.fl(aa)))
        db.executemany("INSERT OR REPLACE INTO candlew VALUES(?,?,?,?)", rs); db.execute("INSERT OR REPLACE INTO donew VALUES(?,?)", (w, len(rs))); db.commit(); n += 1
    print("fetched", n)
def fee(p): return math.ceil(0.07 * 10 * p * (1 - p) * 100 - 1e-9) / 10 / 100
def do_score():
    db = con(); P = pairs(db)
    close = dict(db.execute("select ticker,close_ts from mk").fetchall())
    def quote(table, tk):
        c = close.get(tk) or dict(db.execute("select ticker,close_ts from mkw")).get(tk)
        q = [x for x in db.execute(f"select end_ts,bid_c,ask_c from {table} where ticker=?", (tk,)) if x[0] <= c - 12 * 3600 and x[1] is not None and x[2] is not None]
        if not q: return None
        ts, b, aa = max(q)
        if b <= 0 or aa >= 1 or aa <= b or aa - b > 0.05: return None
        return b, aa
    scored = []; days = set()
    for d_tk, w_tk, day in P:
        qd, qw = quote("candle", d_tk), quote("candlew", w_tk)
        if not qd or not qw: continue
        best = None
        for (A, B, lab) in ((qd, qw, "buy YES daily, NO weekly"), (qw, qd, "buy YES weekly, NO daily")):
            ya, nb = A[1], B[0]                      # ask of YES in A; bid of YES in B
            prof = nb - ya - fee(ya) - fee(1 - nb)
            if best is None or prof > best[0]: best = (prof, ya, lab)
        scored.append((day, best)); days.add(day)
    pos = [s for s in scored if s[1][0] > 0]; cheap = [s for s in scored if 0.03 <= s[1][1] <= 0.30]
    print("pairs in the universe", len(P), "with both quotes", len(scored), "on", len(days), "dates")
    print("locked profit > 0 after both fees:", len(pos), "on", len({s[0] for s in pos}), "dates; cheap-leg pairs", len(cheap), "of which positive", len([s for s in cheap if s[1][0] > 0]))
    if scored:
        pr = sorted(s[1][0] for s in scored); print("best-direction locked profit per pair: median %+.2fc, max %+.2fc, mean %+.2fc" % (100 * pr[len(pr)//2], 100 * pr[-1], 100 * sum(pr) / len(pr)))
        for s in sorted(pos, key=lambda s: -s[1][0])[:5]: print("  ", s[0], "%+.2fc" % (100 * s[1][0]), s[1][2])
if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if c == "list": do_list()
        elif c == "fetch": do_fetch(int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9)
        elif c == "score": do_score()
    except h.Stop as e: print("STOP:", e)
