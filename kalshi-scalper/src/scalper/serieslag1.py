"""SERIESLAG1 (workers/SERIESLAG1_PROTOCOL.md, registered e8da8e6 before any candle).
  python3 -I src/scalper/serieslag1.py list    series (KXNBASERIES, KXNHLSERIES, KXMLBSERIES) and game (KXNBAGAME, KXNHLGAME, KXMLBGAME) listings into data/serieslag1.sqlite
  python3 -I src/scalper/serieslag1.py match   join games to series by the two team codes inside the series dates; census (no price, no outcome statistic)
  python3 -I src/scalper/serieslag1.py fetch [--max N]   1 minute candles of both series markets from G-20 to G+90 minutes for each matched game (resumable)
  python3 -I src/scalper/serieslag1.py score [--holdout]   lag profile (information) + the registered rule on DEVELOPMENT series (first 2/3 by date); --holdout reads the last third ONCE
"""
from __future__ import annotations
import math, os, sqlite3, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hist15 as h  # noqa: E402

DB = os.path.join(h.ROOT, "data", "serieslag1.sqlite")
PAIRS = (("KXNBASERIES", "KXNBAGAME", 4), ("KXNHLSERIES", "KXNHLGAME", 4), ("KXMLBSERIES", "KXMLBGAME", 2))   # wins needed


def connect():
    db = sqlite3.connect(DB)
    db.executescript("""
CREATE TABLE IF NOT EXISTS km(ticker TEXT PRIMARY KEY, series TEXT, event TEXT, code TEXT, open_ts INT, close_ts INT, result TEXT);
CREATE TABLE IF NOT EXISTS game(gev TEXT PRIMARY KEY, sev TEXT, ser TEXT, G INT, winner TEXT, idx INT);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, G INT, end_ts INT, bid_c REAL, ask_c REAL, PRIMARY KEY(ticker, G, end_ts));
CREATE TABLE IF NOT EXISTS done(ticker TEXT, G INT, n INT, PRIMARY KEY(ticker, G));
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);""")
    return db


def do_list():
    db = connect()
    for ser in [p[0] for p in PAIRS] + [p[1] for p in PAIRS]:
        if db.execute("SELECT v FROM meta WHERE k=?", ("list_" + ser,)).fetchone():
            continue
        cur = None
        while True:
            p = {"series_ticker": ser, "limit": 1000}
            if cur:
                p["cursor"] = cur
            d = h.get("/historical/markets", p)
            if d is None:
                time.sleep(20); continue
            for m in d.get("markets", []):
                c, o = h.ts(m.get("close_time")), h.ts(m.get("open_time"))
                if c and m.get("result") in ("yes", "no"):
                    parts = m["ticker"].split("-")
                    db.execute("INSERT OR IGNORE INTO km VALUES(?,?,?,?,?,?,?)", (m["ticker"], ser, m.get("event_ticker"), parts[-1], o, c, m["result"]))
            db.commit()
            cur = d.get("cursor")
            if not cur or not d.get("markets"):
                break
        db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", ("list_" + ser, "1")); db.commit()
        print(ser, db.execute("SELECT count(*) FROM km WHERE series=?", (ser,)).fetchone()[0], "settled markets", flush=True)


def do_match():
    db = connect()
    db.execute("DELETE FROM game")
    for sser, gser, need in PAIRS:
        sev = {}
        for tk, e, code, o, c, res in db.execute("SELECT ticker, event, code, open_ts, close_ts, result FROM km WHERE series=?", (sser,)):
            sev.setdefault(e, []).append((tk, code, o, c, res))
        gev = {}
        for tk, e, code, o, c, res in db.execute("SELECT ticker, event, code, open_ts, close_ts, result FROM km WHERE series=?", (gser,)):
            gev.setdefault(e, []).append((tk, code, c, res))
        nm = ng = 0
        for e, mk in sev.items():
            if len(mk) != 2:
                continue
            a, b = mk[0][1], mk[1][1]
            lo, hi = min(m[2] for m in mk), max(m[3] for m in mk)
            games = []
            for ge, gm in gev.items():
                ev_codes = ge.split("-")[-1][7:]                    # 26JUN13NYKSAS -> NYKSAS
                if ev_codes in (a + b, b + a):
                    G = max(m[2] for m in gm)
                    win = [m[1] for m in gm if m[3] == "yes"]
                    if lo - 3600 <= G <= hi + 3600 and len(win) == 1:
                        games.append((G, ge, win[0]))
            games.sort()
            for i, (G, ge, w) in enumerate(games):
                db.execute("INSERT OR REPLACE INTO game VALUES(?,?,?,?,?,?)", (ge, e, sser, G, w, i))
            nm += 1; ng += len(games)
        print(sser, "series events", len(sev), "with 2 markets matched", nm, "games matched", ng)
    db.commit()


def do_fetch(mx):
    db = connect()
    todo = []
    for gev, sev, ser, G, w, idx in db.execute("SELECT * FROM game ORDER BY G"):
        for tk, in db.execute("SELECT ticker FROM km WHERE event=?", (sev,)):
            if not db.execute("SELECT 1 FROM done WHERE ticker=? AND G=?", (tk, G)).fetchone():
                todo.append((tk, G))
    print(len(todo), "series-market windows still to fetch", flush=True)
    t0 = time.time(); n = 0
    for tk, G in todo[:mx]:
        d = h.get(f"/historical/markets/{tk}/candlesticks", {"start_ts": G - 20 * 60, "end_ts": G + 90 * 60, "period_interval": 1})
        if d is None:
            continue
        rows = []
        for x in d.get("candlesticks", []):
            b, a = (x.get("yes_bid") or {}).get("close"), (x.get("yes_ask") or {}).get("close")
            if x.get("end_period_ts") is not None:
                rows.append((tk, G, int(x["end_period_ts"]), h.fl(b), h.fl(a)))
        db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?)", rows)
        db.execute("INSERT OR REPLACE INTO done VALUES(?,?,?)", (tk, G, len(rows))); db.commit(); n += 1
        if n % 100 == 0:
            print(n, "fetched", int(time.time() - t0), "s", flush=True)
    print("fetched", n, "this run")


def series_prob(a, b, need):
    """P(team A wins the series | A has a wins, B has b wins, each remaining game a fair coin)."""
    if a >= need: return 1.0
    if b >= need: return 0.0
    return 0.5 * series_prob(a + 1, b, need) + 0.5 * series_prob(a, b + 1, need)


def fee(p, c=10, mult=1.0):
    return math.ceil(mult * 0.07 * c * p * (1 - p) * 100 - 1e-9) / c


def quote_at(db, tk, G, t):
    r = db.execute("SELECT end_ts, bid_c, ask_c FROM candle WHERE ticker=? AND G=? AND end_ts<=? ORDER BY end_ts DESC", (tk, G, t)).fetchall()
    for e, b, a in r:
        if b is not None and a is not None and a >= b and a - b <= 0.10 and 0.01 <= a < 0.999:
            return e, b, a
    return None


def quote_after(db, tk, G, t):
    r = db.execute("SELECT end_ts, bid_c, ask_c FROM candle WHERE ticker=? AND G=? AND end_ts>=? ORDER BY end_ts", (tk, G, t)).fetchall()
    for e, b, a in r:
        if b is not None and a is not None and a >= b and a - b <= 0.10 and 0.01 <= a < 0.999:
            return e, b, a
    return None


def pf(v):
    g = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return g / l if l > 0 else float("inf")


def do_score(hold):
    db = connect()
    sers = [r[0] for r in db.execute("SELECT DISTINCT sev FROM game")]
    order = sorted(sers, key=lambda s: db.execute("SELECT min(G) FROM game WHERE sev=?", (s,)).fetchone()[0])
    k = int(len(order) * 2 / 3)
    use = set(order[k:] if hold else order[:k])
    if hold:
        print("WARNING: reading the HELD-OUT last third; allowed once, only if the development line is NOT_YET_FALSIFIED")
    need_of = {p[0]: p[2] for p in PAIRS}
    lag = {m: [] for m in (1, 3, 5, 10, 30, 60)}
    trades = []; nq = 0; ngames = 0
    for sev in use:
        g = db.execute("SELECT gev, ser, G, winner, idx FROM game WHERE sev=? ORDER BY G", (sev,)).fetchall()
        mk = {c: t for t, c in db.execute("SELECT ticker, code FROM km WHERE event=?", (sev,))}
        res = {t: r for t, r in db.execute("SELECT ticker, result FROM km WHERE event=?", (sev,))}
        if len(mk) != 2:
            continue
        codes = list(mk)
        wins = {c: 0 for c in codes}
        for gev, ser, G, w, idx in g:
            ngames += 1
            wins[w] = wins.get(w, 0) + 1
            need = need_of[ser]
            wtk = mk.get(w)
            if wtk is None:
                continue
            q0 = quote_at(db, wtk, G, G - 300)
            if q0 is not None:
                mid0 = (q0[1] + q0[2]) / 2
                q60 = quote_at(db, wtk, G, G + 3600)
                if q60 is not None:
                    jump = (q60[1] + q60[2]) / 2 - mid0
                    if abs(jump) >= 0.03:
                        for m in lag:
                            qm = quote_at(db, wtk, G, G + 60 * m)
                            if qm is not None:
                                lag[m].append(((qm[1] + qm[2]) / 2 - mid0) / jump)
            for c in codes:
                tk = mk[c]
                qa = quote_after(db, tk, G, G + 180)
                if qa is None:
                    continue
                nq += 1
                ask = qa[2]
                if not (0.03 <= ask <= 0.30):
                    continue
                other = [x for x in codes if x != c][0]
                q = series_prob(wins[c], wins[other], need)
                if q - ask - fee(ask) / 100 >= 0.05:
                    won = 1.0 if res[tk] == "yes" else 0.0
                    trades.append(dict(sev=sev, net=(won - ask) * 100 - fee(ask), net2=(won - ask) * 100 - fee(ask, 10, 1.2), q=q, ask=ask))
    print("series used %d, games %d, quoted team-windows %d, rule trades %d" % (len(use), ngames, nq, len(trades)))
    for m, v in lag.items():
        if v:
            v.sort(); print("lag +%2d min: share of the eventual jump already priced median %.2f p25 %.2f p75 %.2f (n %d)" % (m, v[len(v) // 2], v[len(v) // 4], v[3 * len(v) // 4], len(v)))
    if trades:
        net = [t["net"] for t in trades]; bs = {}
        for t in trades:
            bs.setdefault(t["sev"], []).append(t["net"])
        gm = [sum(v) / len(v) for v in bs.values()]; m = sum(gm) / len(gm); sd = (sum((x - m) ** 2 for x in gm) / max(1, len(gm) - 1)) ** 0.5
        print("RULE: n %d series %d mean %+.2fc PF %.3f series-z %.2f stress PF %.3f" % (len(net), len(bs), sum(net) / len(net), pf(net), m / (sd / len(gm) ** 0.5) if sd > 0 else float("nan"), pf([t["net2"] for t in trades])))
        print("verdict: " + ("NOT_ENOUGH_DATA (n %d < 150)" % len(net) if len(net) < 150 else "see judging words"))
    else:
        print("RULE: no trades -> NOT_ENOUGH_DATA")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "list": do_list()
        elif cmd == "match": do_match()
        elif cmd == "fetch": do_fetch(int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9)
        elif cmd == "score": do_score("--holdout" in sys.argv)
        else: print(__doc__)
    except h.Stop as e:
        print("STOP:", e)
