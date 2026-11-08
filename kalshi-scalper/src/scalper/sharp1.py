"""SHARP1 ingest and scoring: Kalshi soccer match markets (/historical) against football-data.co.uk consensus closing odds.
Protocol: workers/SHARP1_PROTOCOL.md (registered before any Kalshi price or result was joined to a bookmaker line).
  python3 -I src/scalper/sharp1.py list       Kalshi market listing (5 leagues) into data/sharp1.sqlite (result stored, no statistic)
  python3 -I src/scalper/sharp1.py match      join games to events, choose candidate outcomes from the BOOKMAKER line only, print counts
  python3 -I src/scalper/sharp1.py fetch      1 minute candles [kickoff-35 min, kickoff-4 min] for the chosen markets (resumable)
  python3 -I src/scalper/sharp1.py score [--holdout]   the registered rule on development (or the held-out, once)
"""
from __future__ import annotations
import csv, difflib, glob, math, os, re, sqlite3, sys, time, unicodedata
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hist15 as h  # noqa: E402

ROOT = h.ROOT
DB = os.path.join(ROOT, "data", "sharp1.sqlite")
FD = os.path.join(ROOT, "data", "fd")
SERIES = {"E0": "KXEPLGAME", "SP1": "KXLALIGAGAME", "D1": "KXBUNDESLIGAGAME", "I1": "KXSERIEAGAME", "F1": "KXLIGUE1GAME"}
LO_D, HI_D = date(2025, 8, 1), date(2026, 9, 7)
HOLD_DATE = date(2026, 3, 7)
QMAX, EDGE = 0.32, 0.04
ALIAS = {"man united": "manchester united", "man city": "manchester city", "nottm forest": "nottingham forest", "wolves": "wolverhampton",
         "spurs": "tottenham", "ath madrid": "atletico madrid", "ath bilbao": "athletic club", "sociedad": "real sociedad", "betis": "real betis",
         "espanol": "espanyol", "vallecano": "rayo vallecano", "celta": "celta vigo", "leverkusen": "bayer leverkusen", "mgladbach": "monchengladbach",
         "ein frankfurt": "eintracht frankfurt", "fc koln": "koln", "paris sg": "paris saint germain", "st etienne": "saint etienne",
         "inter": "internazionale", "dortmund": "borussia dortmund", "hertha": "hertha berlin", "stuttgart": "vfb stuttgart", "union berlin": "1 fc union berlin",
         "ein frankfurt": "frankfurt", "eintracht frankfurt": "frankfurt", "werder bremen": "bremen", "mgladbach": "m gladbach", "monchengladbach": "m gladbach",
         "schalke 04": "schalke", "leeds": "leeds united", "hull": "hull city", "ipswich": "ipswich town", "paris sg": "psg", "paris saint germain": "psg",
         "rennes": "stade rennais", "brest": "stade brest", "strasbourg": "strasbourg alsace", "parma": "parma calcio", "verona": "hellas verona",
         "ath bilbao": "bilbao", "athletic club": "bilbao", "ath madrid": "atletico", "atletico madrid": "atletico", "la coruna": "deportivo de la coruna",
         "man united": "man utd", "manchester united": "man utd", "nottm forest": "nottingham forest", "fc koln": "koln", "cologne": "koln"}


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]", "", s.replace("'", "").replace("-", " ")).strip()
    s = re.sub(r"\b(fc|cf|afc|sc|ac|as|us|ss|rc|ud|cd|sv|fsv|tsg|vfl|vfb|rb|1)\b", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return ALIAS.get(s, s)


def connect():
    db = sqlite3.connect(DB)
    db.executescript("""
CREATE TABLE IF NOT EXISTS km(ticker TEXT PRIMARY KEY, series TEXT, event TEXT, sub TEXT, open_ts INT, close_ts INT, result TEXT);
CREATE TABLE IF NOT EXISTS cand(ticker TEXT PRIMARY KEY, league TEXT, kickoff INT, q REAL, side TEXT, game TEXT);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INT, bid_c REAL, ask_c REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INT);
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
""")
    return db


def do_list():
    db = connect()
    for lg, ser in SERIES.items():
        if db.execute("SELECT v FROM meta WHERE k=?", ("list_" + ser,)).fetchone():
            continue
        cur = None
        while True:
            p = {"series_ticker": ser, "limit": 1000}
            if cur:
                p["cursor"] = cur
            d = h.get("/historical/markets", p)
            if d is None:
                continue
            for m in d.get("markets", []):
                c, o = h.ts(m.get("close_time")), h.ts(m.get("open_time"))
                if c and m.get("result") in ("yes", "no"):
                    db.execute("INSERT OR IGNORE INTO km VALUES(?,?,?,?,?,?,?)", (m["ticker"], ser, m.get("event_ticker"), m.get("yes_sub_title"), o, c, m["result"]))
            db.commit()
            cur = d.get("cursor")
            if not cur or not d.get("markets"):
                break
        db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", ("list_" + ser, "1")); db.commit()
        print(ser, db.execute("SELECT count(*) FROM km WHERE series=?", (ser,)).fetchone()[0], "markets", flush=True)


def load_games():
    out = []
    for f in sorted(glob.glob(os.path.join(FD, "*.csv"))):
        lg = os.path.basename(f).split("_")[0]
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            if not r.get("Date") or not r.get("AvgCH") or not r.get("AvgCD") or not r.get("AvgCA"):
                continue
            d = datetime.strptime(r["Date"], "%d/%m/%Y").date()
            if not (LO_D <= d <= HI_D):
                continue
            hh, mm = (r.get("Time") or "15:00").split(":")
            ko = datetime(d.year, d.month, d.day, int(hh), int(mm), tzinfo=ZoneInfo("Europe/London")).astimezone(timezone.utc)
            o = [1.0 / float(r["AvgC" + k]) for k in "HDA"]; s = sum(o)
            out.append(dict(league=lg, date=d, ko=int(ko.timestamp()), home=r["HomeTeam"], away=r["AwayTeam"], q=dict(zip("HDA", [x / s for x in o])), ftr=r["FTR"]))
    return out


def do_match():
    db = connect()
    games = load_games()
    ev = {}
    for tk, ser, e, sub, o, c, res in db.execute("SELECT * FROM km"):
        ev.setdefault((ser, e), []).append((tk, sub))
    byser = {}
    for (ser, e), mk in ev.items():
        teams = [(norm(s), tk) for tk, s in mk if s and s.lower() != "tie"]
        tie = [tk for tk, s in mk if s and s.lower() == "tie"]
        m = re.match(r".*-(\d\d)([A-Z]{3})(\d\d)", e or "")
        if not m or len(teams) != 2 or not tie:
            continue
        d = datetime.strptime(m.group(1) + m.group(2) + m.group(3), "%y%b%d").date()
        byser.setdefault(ser, []).append((d, teams, tie[0], e))
    db.execute("DELETE FROM cand")
    stat = {}
    for g in games:
        ser = SERIES[g["league"]]
        cands = [x for x in byser.get(ser, []) if abs((x[0] - g["date"]).days) <= 1]
        hn, an = norm(g["home"]), norm(g["away"])
        best = None
        for d, teams, tie, e in cands:
            def sc(a, b): return difflib.SequenceMatcher(None, a, b).ratio()
            for (t1, k1), (t2, k2) in (teams, teams[::-1]):
                s = min(sc(hn, t1), sc(an, t2))
                if s >= 0.72 and (best is None or s > best[0]):
                    best = (s, k1, k2, tie, e)
        st = stat.setdefault(g["league"], [0, 0])
        st[0] += 1
        if best is None:
            continue
        st[1] += 1
        _, kh, ka, kt, e = best
        for side, tk in (("H", kh), ("D", kt), ("A", ka)):
            if g["q"][side] <= QMAX:
                db.execute("INSERT OR REPLACE INTO cand VALUES(?,?,?,?,?,?)", (tk, g["league"], g["ko"], g["q"][side], side, "%s|%s|%s" % (g["date"], g["home"], g["away"])))
    db.commit()
    print("games / matched by league:", stat)
    print("candidate markets (bookmaker q <= %.2f):" % QMAX, db.execute("SELECT count(*) FROM cand").fetchone()[0])


def do_fetch(mx):
    db = connect()
    todo = db.execute("SELECT c.ticker, c.kickoff FROM cand c WHERE c.ticker NOT IN (SELECT ticker FROM done) ORDER BY c.kickoff DESC").fetchall()
    print(len(todo), "candidate markets still to fetch", flush=True)
    t0 = time.time(); n = 0
    for tk, ko in todo[:mx]:
        d = h.get(f"/historical/markets/{tk}/candlesticks", {"start_ts": ko - 35 * 60, "end_ts": ko - 4 * 60, "period_interval": 1})
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


def fee_per_contract(p, c=10, mult=1.0):
    return math.ceil(mult * 0.07 * c * p * (1 - p) * 100 - 1e-9) / c


def score(hold=False):
    db = connect()
    rows = db.execute("""SELECT c.ticker, c.league, c.kickoff, c.q, c.game, k.result FROM cand c JOIN km k ON k.ticker=c.ticker""").fetchall()
    trades = []; nq = 0; nn = 0
    for tk, lg, ko, q, game, res in rows:
        gd = datetime.strptime(game.split("|")[0], "%Y-%m-%d").date()
        if (gd >= HOLD_DATE) != hold:
            continue
        cs = db.execute("SELECT end_ts, bid_c, ask_c FROM candle WHERE ticker=? AND end_ts<=? ORDER BY end_ts DESC", (tk, ko - 300)).fetchall()
        q_ = [c for c in cs if c[1] is not None and c[2] is not None and c[2] >= c[1] and c[2] - c[1] <= 0.10]
        nn += 1
        if not q_:
            continue
        nq += 1
        _, b, a = q_[0]
        if not (0.03 <= a <= 0.30):
            continue
        trades.append(dict(tk=tk, lg=lg, game=game, ko=ko, q=q, ask=a, mid=(a + b) / 2, won=1.0 if res == "yes" else 0.0))
    return trades, nn, nq


def pf(v):
    g = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return g / l if l > 0 else float("inf")


def stats(tr, edge=EDGE, c=10, mult=1.0):
    sel = [t for t in tr if t["q"] - t["ask"] - fee_per_contract(t["ask"], c, mult) / 100 >= edge]
    net = [((t["won"] - t["ask"]) * 100 - fee_per_contract(t["ask"], c, mult)) for t in sel]
    return sel, net


def do_score(hold):
    tr, nn, nq = score(hold)
    print("candidate markets %d, with a valid quote 5 min before kickoff %d, ask 3c-30c %d" % (nn, nq, len(tr)))
    for label, kw in (("PRIMARY edge 4c C=10", dict()), ("stress x1.2", dict(mult=1.2)), ("C=1 fee", dict(c=1)), ("edge 2c", dict(edge=0.02)), ("edge 6c", dict(edge=0.06))):
        sel, net = stats(tr, **kw)
        if not sel:
            print(label, "no trades"); continue
        games = {}
        for t, x in zip(sel, net):
            games.setdefault(t["game"], []).append(x)
        gm = [sum(v) / len(v) for v in games.values()]
        m = sum(gm) / len(gm); sd = (sum((x - m) ** 2 for x in gm) / max(1, len(gm) - 1)) ** 0.5
        z = m / (sd / len(gm) ** 0.5) if sd > 0 else float("nan")
        dates = sorted({t["game"].split("|")[0] for t in sel})
        thirds = [dates[: len(dates) // 3], dates[len(dates) // 3: 2 * len(dates) // 3], dates[2 * len(dates) // 3:]]
        pfs = []
        for part in thirds:
            ps = set(part)
            pfs.append(round(pf([x for t, x in zip(sel, net) if t["game"].split("|")[0] in ps]), 3) if ps else None)
        print("%-22s n %4d games %4d mean %+.2fc PF %.3f thirds %s game-z %.2f win %.3f vs ask %.3f vs q %.3f" % (
            label, len(sel), len(games), sum(net) / len(net), pf(net), pfs, z, sum(t["won"] for t in sel) / len(sel), sum(t["ask"] for t in sel) / len(sel), sum(t["q"] for t in sel) / len(sel)))
    # information: Brier of q and of Kalshi mid on all quoted candidates
    if tr:
        bq = sum((t["q"] - t["won"]) ** 2 for t in tr) / len(tr); bm = sum((t["mid"] - t["won"]) ** 2 for t in tr) / len(tr)
        print("Brier on %d quoted candidates: bookmaker q %.4f, Kalshi mid %.4f" % (len(tr), bq, bm))


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
