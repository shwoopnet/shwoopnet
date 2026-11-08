"""NFLCOMBO1 (workers/NFLCOMBO1_PROTOCOL.md, registered 8b210dc + Amendment 1 d141b20, before any candle).
  python3 -I src/scalper/nflcombo1.py list      KXNFLGAME, KXNFLPASSYDS, KXNFLRSHYDS, KXNFLRECYDS, KXNFLANYTD into data/nflcombo1.sqlite (results stored, no statistic)
  python3 -I src/scalper/nflcombo1.py choose    fixed leg choice from tickers and listings only (never a price); census counts
  python3 -I src/scalper/nflcombo1.py fetch [--max N]   hourly candles [close-12h, close] for the chosen legs (resumable)
  python3 -I src/scalper/nflcombo1.py score     fixed-structure scorer, DEVELOPMENT games only (first 2/3 by date); --holdout reads the last third ONCE (prints a warning)
Legs per team in a game, all YES: moneyline; QB = the team's QB with most listed passing-yards markets, his lowest strike; R = the team's rusher with the highest top strike, his lowest strike;
W = same for receiving yards; T = the team's most-listed player (strikes across the three yard series), his anytime-TD market. Decision instant: the last hourly candle ending at or before
(QB leg close_time - 4 h) for R and W, (moneyline close_time - 4 h) for T; every leg uses the same instant.
"""
from __future__ import annotations
import math, os, random, sqlite3, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hist15 as h  # noqa: E402

DB = os.path.join(h.ROOT, "data", "nflcombo1.sqlite")
SERIES = ("KXNFLGAME", "KXNFLPASSYDS", "KXNFLRSHYDS", "KXNFLRECYDS", "KXNFLANYTD")


def connect():
    db = sqlite3.connect(DB)
    db.executescript("""
CREATE TABLE IF NOT EXISTS km(ticker TEXT PRIMARY KEY, series TEXT, game TEXT, subj TEXT, strike REAL, close_ts INT, result TEXT);
CREATE TABLE IF NOT EXISTS leg(ticker TEXT PRIMARY KEY, game TEXT, team TEXT, role TEXT);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INT, bid_c REAL, ask_c REAL, PRIMARY KEY(ticker,end_ts));
CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INT);
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);""")
    return db


def do_list():
    db = connect()
    for ser in SERIES:
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
                c = h.ts(m.get("close_time"))
                if c and m.get("result") in ("yes", "no"):
                    parts = m["ticker"].split("-")
                    db.execute("INSERT OR IGNORE INTO km VALUES(?,?,?,?,?,?,?)", (m["ticker"], ser, parts[1], parts[2] if len(parts) > 2 else "", m.get("floor_strike"), c, m["result"]))
            db.commit()
            cur = d.get("cursor")
            if not cur or not d.get("markets"):
                break
        db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", ("list_" + ser, "1")); db.commit()
        print(ser, db.execute("SELECT count(*) FROM km WHERE series=?", (ser,)).fetchone()[0], "settled markets", flush=True)


def team_of(subj, teams):
    best = None
    for t in teams:
        if subj.startswith(t) and (best is None or len(t) > len(best)):
            best = t
    return best


def do_choose():
    db = connect()
    db.execute("DELETE FROM leg")
    games = {}
    for tk, ser, game, subj, strike, cl, res in db.execute("SELECT * FROM km"):
        games.setdefault(game, {}).setdefault(ser, []).append((tk, subj, strike, cl))
    census = dict(games=0, ml=0, R=0, W=0, T=0)
    for game, d in games.items():
        ml = d.get("KXNFLGAME")
        if not ml or "KXNFLPASSYDS" not in d:
            continue
        teams = {m[1]: m[0] for m in ml}
        census["games"] += 1
        for team, mltk in teams.items():
            qbs = {}
            for tk, subj, strike, cl in d["KXNFLPASSYDS"]:
                if team_of(subj, teams) == team:
                    qbs.setdefault(subj, []).append((strike, tk))
            if not qbs:
                continue
            qb = max(qbs, key=lambda s: len(qbs[s]))
            qbleg = min(qbs[qb])[1]
            db.execute("INSERT OR REPLACE INTO leg VALUES(?,?,?,?)", (mltk, game, team, "ML"))
            db.execute("INSERT OR REPLACE INTO leg VALUES(?,?,?,?)", (qbleg, game, team, "QB"))
            census["ml"] += 1
            for role, ser in (("R", "KXNFLRSHYDS"), ("W", "KXNFLRECYDS")):
                pl = {}
                for tk, subj, strike, cl in d.get(ser, []):
                    if team_of(subj, teams) == team:
                        pl.setdefault(subj, []).append((strike, tk))
                if pl:
                    best = max(pl, key=lambda s: max(x[0] or 0 for x in pl[s]))
                    db.execute("INSERT OR REPLACE INTO leg VALUES(?,?,?,?)", (min(pl[best])[1], game, team, role))
                    census[role] += 1
            cnt = {}
            for ser in ("KXNFLPASSYDS", "KXNFLRSHYDS", "KXNFLRECYDS"):
                for tk, subj, strike, cl in d.get(ser, []):
                    if team_of(subj, teams) == team:
                        cnt[subj] = cnt.get(subj, 0) + 1
            if cnt:
                star = max(cnt, key=cnt.get)
                for tk, subj, strike, cl in d.get("KXNFLANYTD", []):
                    if subj == star:
                        db.execute("INSERT OR REPLACE INTO leg VALUES(?,?,?,?)", (tk, game, team, "TD")); census["T"] += 1
    db.commit()
    print("census (team-combos with each variant's legs found):", census, "| leg markets chosen:", db.execute("SELECT count(*) FROM leg").fetchone()[0])


def do_fetch(mx):
    db = connect()
    todo = db.execute("""SELECT l.ticker, k.close_ts FROM leg l JOIN km k ON k.ticker=l.ticker WHERE l.ticker NOT IN (SELECT ticker FROM done) ORDER BY k.close_ts DESC""").fetchall()
    print(len(todo), "leg markets still to fetch", flush=True)
    t0 = time.time(); n = 0
    for tk, c in todo[:mx]:
        d = h.get(f"/historical/markets/{tk}/candlesticks", {"start_ts": c - 12 * 3600, "end_ts": c, "period_interval": 60})
        if d is None:
            continue
        rows = []
        for x in d.get("candlesticks", []):
            b, a = (x.get("yes_bid") or {}).get("close"), (x.get("yes_ask") or {}).get("close")
            if x.get("end_period_ts") is not None:
                rows.append((tk, int(x["end_period_ts"]), h.fl(b), h.fl(a)))
        db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", rows)
        db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (tk, len(rows))); db.commit(); n += 1
        if n % 100 == 0:
            print(n, "fetched", int(time.time() - t0), "s", flush=True)
    print("fetched", n, "this run")


def fee(p, c=10, mult=1.0):
    return math.ceil(mult * 0.07 * c * p * (1 - p) * 100 - 1e-9) / c


def pf(v):
    g = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return g / l if l > 0 else float("inf")


def quote(db, tk, T):
    r = db.execute("SELECT end_ts, bid_c, ask_c FROM candle WHERE ticker=? AND end_ts<=? ORDER BY end_ts DESC", (tk, T)).fetchall()
    for e, b, a in r:
        if b is not None and a is not None and a >= b and a - b <= 0.10 and 0.01 <= a < 0.999:
            return b, a
    return None


def combos(db, variant, mult=1.0):
    role = {"R": "R", "W": "W", "T": "TD"}[variant]
    out = []
    rows = db.execute("SELECT game, team FROM leg WHERE role='ML'").fetchall()
    for game, team in rows:
        legs = {r[0]: r[1] for r in db.execute("SELECT role, ticker FROM leg WHERE game=? AND team=?", (game, team))}
        need = ["ML", role] if variant == "T" else ["ML", "QB", role]
        if any(n not in legs for n in need):
            continue
        ks = {n: db.execute("SELECT close_ts, result FROM km WHERE ticker=?", (legs[n],)).fetchone() for n in need}
        ref = ks["QB"][0] if variant != "T" else ks["ML"][0]
        T = (ref - 4 * 3600) // 3600 * 3600
        net = []; ok = True; wins = []
        for n in need:
            q = quote(db, legs[n], T)
            if q is None or ks[n][1] not in ("yes", "no"):
                ok = False; break
            a = q[1]; won = 1.0 if ks[n][1] == "yes" else 0.0
            net.append((won - a) * 100 - fee(a, 10, mult)); wins.append(won)
        if ok:
            out.append(dict(game=game, team=team, T=T, net=sum(net), cost=None, wins=wins, ref=ref))
    return out


def report(label, cs):
    if not cs:
        print(label, "no combos"); return
    net = [c["net"] for c in cs]; games = {}
    for c in cs:
        games.setdefault(c["game"], []).append(c["net"])
    gm = [sum(v) / len(v) for v in games.values()]
    m = sum(gm) / len(gm); sd = (sum((x - m) ** 2 for x in gm) / max(1, len(gm) - 1)) ** 0.5
    z = m / (sd / len(gm) ** 0.5) if sd > 0 else float("nan")
    w = [x for x in net if x > 0]; l = [x for x in net if x <= 0]
    allwin = sum(1 for c in cs if all(x == 1.0 for x in c["wins"])) / len(cs)
    nonewin = sum(1 for c in cs if all(x == 0.0 for x in c["wins"])) / len(cs)
    print("%-26s combos %4d games %4d mean %+.2fc PF %.3f game-z %.2f | all-legs-win %.3f none %.3f | mean win %+.1fc mean loss %+.1fc worst %+.1fc loss/win %.2f" % (
        label, len(cs), len(games), sum(net) / len(net), pf(net), z, allwin, nonewin, sum(w) / len(w) if w else 0, sum(l) / len(l) if l else 0, min(net), (-sum(l) / len(l)) / (sum(w) / len(w)) if w and l else float("nan")))


def pairs(cs):
    by = {}
    for c in cs:
        by.setdefault(c["game"], []).append(c)
    out = []
    for g, lst in by.items():
        if len(lst) == 2:
            out.append(dict(game=g, net=lst[0]["net"] + lst[1]["net"], wins=lst[0]["wins"] + lst[1]["wins"], parts=lst))
    return out


def stacks(cs, ks=(2, 3, 5, 7), draws=10000, seed=7):
    rng = random.Random(seed); net = [c["net"] for c in cs]
    for k in ks:
        tot = [sum(rng.choice(net) for _ in range(k)) for _ in range(draws)]
        tot.sort()
        print("   %d-game stack: mean %+.1fc p5 %+.1fc p50 %+.1fc share>0 %.3f worst %+.1fc" % (k, sum(tot) / draws, tot[int(.05 * draws)], tot[draws // 2], sum(1 for x in tot if x > 0) / draws, tot[0]))


def do_score(hold):
    db = connect()
    games = sorted({r[0] for r in db.execute("SELECT game FROM leg")}, key=lambda g: db.execute("SELECT min(close_ts) FROM km WHERE game=?", (g,)).fetchone()[0])
    k = int(len(games) * 2 / 3)
    use = set(games[k:] if hold else games[:k])
    if hold:
        print("WARNING: reading the HELD-OUT last third; allowed once, only if a development line is NOT_YET_FALSIFIED")
    print("games with a leg:", len(games), "| development", k, "| using", len(use))
    for variant in ("R", "W", "T"):
        for mult, tag in ((1.0, ""), (1.2, " x1.2")):
            cs = [c for c in combos(db, variant, mult) if c["game"] in use]
            report("variant %s singles%s" % (variant, tag), cs)
            if mult == 1.0:
                ps = pairs(cs)
                if ps:
                    net = [p["net"] for p in ps]
                    aw = sum(1 for p in ps if all(x == 1.0 for x in p["parts"][0]["wins"])) / len(ps)
                    bw = sum(1 for p in ps if all(x == 1.0 for x in p["parts"][1]["wins"])) / len(ps)
                    neither = sum(1 for p in ps if not all(x == 1.0 for x in p["parts"][0]["wins"]) and not all(x == 1.0 for x in p["parts"][1]["wins"])) / len(ps)
                    print("   pair A+B: games %d mean %+.2fc PF %.3f | A all-legs-win %.3f B %.3f neither %.3f | worst %+.1fc" % (len(ps), sum(net) / len(net), pf(net), aw, bw, neither, min(net)))
                if cs:
                    stacks(cs)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "list": do_list()
        elif cmd == "choose": do_choose()
        elif cmd == "fetch": do_fetch(int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9)
        elif cmd == "score": do_score("--holdout" in sys.argv)
        else: print(__doc__)
    except h.Stop as e:
        print("STOP:", e)
