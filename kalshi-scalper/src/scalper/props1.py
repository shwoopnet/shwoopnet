"""PROPS1: Kalshi player-prop ladders, CHEAP side only (ask 3c to 30c), against a game-log negative binomial.

Registration: workers/PROPS1_REGISTRATION.md (sha256 48a5e1cc...). Data in data/props1.sqlite (git-ignored).
  python -m scalper.props1 espn      # ESPN scoreboards + box scores (1 req/s), games before the frozen cut only
  python -m scalper.props1 markets   # Kalshi market listings (no candles) for the in-scope series, before the cut
  python -m scalper.props1 build     # match markets to games, split FIT/TEST, fit k and r on FIT stats, model, sample
  python -m scalper.props1 candles   # candles for the TEST sample (resumable)
  python -m scalper.props1 score     # the registered statistics
The frozen third (games from 2026-10-03T16:00Z) is never fetched: every query is bounded by CUT.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import api
from .candlefield import quote_close

DB = Path(__file__).resolve().parents[2] / "data" / "props1.sqlite"
CUT = datetime(2026, 10, 3, 16, tzinfo=timezone.utc)
CUT_TS = int(CUT.timestamp())
CUT_ISO = "2026-10-03T16:00:00Z"
LO, HI, RATIO, C, LEAD = 0.03, 0.30, 3.0, 10, 300
MAXPER, SAMPLE = 2, 40
UA = "shwoopnet-research-props1/1.0 (personal research, 1 req/s)"
KS = (1, 2, 4, 8, 16)
RS = (1, 2, 4, 8, 16, 32, 64)

# league -> (espn path, series -> stat, scoreboard date ranges)
LEAGUES = {
    "NBA": ("basketball/nba", {"KXNBAPTS": "pts", "KXNBAREB": "reb", "KXNBAAST": "ast", "KXNBA3PT": "tpm"},
            [("20251021", "20260630")]),
    "WNBA": ("basketball/wnba", {"KXWNBAPTS": "pts", "KXWNBAREB": "reb", "KXWNBAAST": "ast", "KXWNBA3PT": "tpm"},
             [("20250501", "20251031"), ("20260501", "20261002")]),
    "NFL": ("football/nfl", {"KXNFLRECYDS": "recyds", "KXNFLRSHYDS": "rshyds", "KXNFLPASSYDS": "passyds", "KXNFLREC": "rec"},
            [("20250904", "20260215"), ("20260901", "20261002")]),
}
SERIES_LEAGUE = {s: (lg, st) for lg, (_, ser, _) in LEAGUES.items() for s, st in ser.items()}


# ----------------------------------------------------------------------------- pure functions (tested)

def fee(p: float, c: int = C) -> float:
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win: bool, ask: float, mult: float = 1.0) -> float:
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z ]", " ", s)
    parts = [w for w in s.split() if w not in ("jr", "sr", "ii", "iii", "iv")]
    return " ".join(parts)


def nb_logpmf(x: int, mu: float, r: float) -> float:
    p = r / (r + mu)
    return (math.lgamma(x + r) - math.lgamma(r) - math.lgamma(x + 1) + r * math.log(p) + x * math.log(1 - p))


def nb_sf(s: float, mu: float, r: float) -> float:
    """P(X > s) for a negative binomial with mean mu and variance mu + mu^2/r."""
    n = math.floor(s)
    if n < 0:
        return 1.0
    p = r / (r + mu)
    q = 1 - p
    pm = p ** r
    cdf = pm
    for x in range(1, n + 1):
        pm *= q * (x - 1 + r) / x
        cdf += pm
        if pm < 1e-18 and x > mu:
            break
    return max(0.0, min(1.0, 1.0 - cdf))


def shrunk_mean(prior: list[float], m_lg: float, k: float) -> float | None:
    """prior: earlier values oldest first. Last up to 10, shrunk toward the league mean."""
    last = prior[-10:]
    if len(last) < 3:
        return None
    return max(0.05, (sum(last) + k * m_lg) / (len(last) + k))


def fit_kr(rows: list[tuple[list[float], int]], m_lg: float):
    """rows: (prior values, actual). Highest log likelihood over the registered grid."""
    best = None
    for k in KS:
        mus = []
        for pr, a in rows:
            mu = shrunk_mean(pr, m_lg, k)
            if mu is not None:
                mus.append((mu, a))
        if not mus:
            continue
        for r in RS:
            ll = sum(nb_logpmf(a, mu, r) for mu, a in mus)
            if best is None or ll > best[0]:
                best = (ll, k, r, len(mus))
    return best


def sha(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()


def choose_sample(tickers: list[str], n: int = SAMPLE) -> list[str]:
    return sorted(tickers, key=sha)[:n]


def cheap_side(bid: float, ask: float):
    """Return ('yes'|'no', side ask) for the side whose ask is in [LO, HI], else None."""
    ya, na = ask, 1 - bid
    if LO <= ya <= HI:
        return "yes", ya
    if LO <= na <= HI:
        return "no", na
    return None


def valid(b, a) -> bool:
    return b is not None and a is not None and 0 <= b < a <= 1 and a - b <= 0.10


def pick_trades(rows: list[dict], treated: bool) -> list[dict]:
    """rows: cheap-side candidates of ONE game, each with ticker, p_side, ask, win. Treated needs p_side >= 3 x ask;
    both treated and control keep at most MAXPER by (highest p/ask for treated, sha1 for control)."""
    if treated:
        ok = [r for r in rows if r["p_side"] >= RATIO * r["ask"]]
        ok.sort(key=lambda r: (-r["p_side"] / r["ask"], sha(r["ticker"])))
    else:
        ok = sorted(rows, key=lambda r: sha(r["ticker"]))
    return ok[:MAXPER]


def cluster_stats(vals_by_cluster: dict[str, list[float]]):
    """Mean over trades with a cluster-robust standard error; returns (n, mean, se, z)."""
    xs = [v for L in vals_by_cluster.values() for v in L]
    n = len(xs)
    if n < 2:
        return n, (xs[0] if xs else float("nan")), float("nan"), float("nan")
    m = sum(xs) / n
    s = sum(sum(v - m for v in L) ** 2 for L in vals_by_cluster.values())
    se = math.sqrt(s) / n
    return n, m, se, (m / se if se > 0 else float("nan"))


def profit_factor(nets: list[float]) -> float:
    g = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return g / l if l > 0 else float("inf")


# ----------------------------------------------------------------------------- storage

SCHEMA = """
CREATE TABLE IF NOT EXISTS game(id TEXT, league TEXT, start_ts INTEGER, home TEXT, away TEXT, PRIMARY KEY(id, league));
CREATE TABLE IF NOT EXISTS gdone(id TEXT, league TEXT, n INTEGER, PRIMARY KEY(id, league));
CREATE TABLE IF NOT EXISTS pstat(gid TEXT, league TEXT, aid TEXT, nm TEXT, team TEXT, played INTEGER,
  pts REAL, reb REAL, ast REAL, tpm REAL, rec REAL, recyds REAL, rshyds REAL, passyds REAL, PRIMARY KEY(gid, league, aid));
CREATE TABLE IF NOT EXISTS kmarket(ticker TEXT PRIMARY KEY, series TEXT, event TEXT, name TEXT, strike REAL, close_time TEXT, exp_time TEXT, result TEXT, src TEXT);
CREATE TABLE IF NOT EXISTS kdone(series TEXT, src TEXT, PRIMARY KEY(series, src));
CREATE TABLE IF NOT EXISTS mgame(ticker TEXT PRIMARY KEY, gid TEXT, league TEXT, stat TEXT, aid TEXT, split TEXT, mu REAL, p_yes REAL, sampled INTEGER);
CREATE TABLE IF NOT EXISTS fit(league TEXT, stat TEXT, k REAL, r REAL, m_lg REAL, n INTEGER, PRIMARY KEY(league, stat));
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS cdone(ticker TEXT PRIMARY KEY, n INTEGER);
"""


def conn():
    DB.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB, timeout=60)
    c.executescript(SCHEMA)
    return c


def jget(url: str, tries: int = 5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{url}: {last}")


# ----------------------------------------------------------------------------- ESPN

def parse_box(league: str, summ: dict) -> list[dict]:
    """One dict per player: aid, nm, team, played and the stats registered."""
    out: dict[str, dict] = {}
    for tm in (summ.get("boxscore", {}) or {}).get("players", []) or []:
        team = (tm.get("team") or {}).get("abbreviation", "")
        for blk in tm.get("statistics", []) or []:
            labels = blk.get("labels") or []
            kind = (blk.get("name") or "").lower()
            for a in blk.get("athletes", []) or []:
                ath = a.get("athlete") or {}
                aid = str(ath.get("id"))
                d = out.setdefault(aid, dict(aid=aid, nm=norm_name(ath.get("displayName", "")), team=team, played=0,
                                             pts=0.0, reb=0.0, ast=0.0, tpm=0.0, rec=0.0, recyds=0.0, rshyds=0.0, passyds=0.0))
                st = a.get("stats") or []
                row = dict(zip(labels, st))
                if league in ("NBA", "WNBA"):
                    try:
                        mins = float(row.get("MIN", 0) or 0)
                    except ValueError:
                        mins = 0.0
                    d["played"] = 1 if (mins > 0 and not a.get("didNotPlay")) else 0
                    for key, lab in (("pts", "PTS"), ("reb", "REB"), ("ast", "AST")):
                        try:
                            d[key] = float(row.get(lab, 0) or 0)
                        except ValueError:
                            pass
                    t = str(row.get("3PT", "0-0")).split("-")[0]
                    d["tpm"] = float(t) if t.isdigit() else 0.0
                else:  # NFL: appears in any category = counted as having played
                    d["played"] = 1

                    def num(lab):
                        try:
                            return float(row.get(lab, 0) or 0)
                        except ValueError:
                            return 0.0
                    if kind == "receiving":
                        d["rec"], d["recyds"] = num("REC"), num("YDS")
                    elif kind == "rushing":
                        d["rshyds"] = num("YDS")
                    elif kind == "passing":
                        d["passyds"] = num("YDS")
    return list(out.values())


def cmd_espn():
    c = conn()
    for league, (path, _ser, ranges) in LEAGUES.items():
        base = f"https://site.api.espn.com/apis/site/v2/sports/{path}"
        for a, b in ranges:
            d0 = datetime.strptime(a, "%Y%m%d")
            d1 = datetime.strptime(b, "%Y%m%d")
            while d0 <= d1:
                e = d0
                sb = jget(f"{base}/scoreboard?dates={d0:%Y%m%d}&limit=500")
                time.sleep(1.0)
                for ev in sb.get("events", []):
                    typ = ((ev.get("season") or {}).get("type"))
                    st = ((ev.get("status") or {}).get("type") or {}).get("name", "")
                    ts = int(datetime.strptime(ev["date"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc).timestamp())
                    if typ not in (2, 3) or st != "STATUS_FINAL" or ts >= CUT_TS:
                        continue
                    comp = (ev.get("competitions") or [{}])[0].get("competitors", [])
                    h = next((x["team"]["abbreviation"] for x in comp if x.get("homeAway") == "home"), "")
                    aw = next((x["team"]["abbreviation"] for x in comp if x.get("homeAway") == "away"), "")
                    c.execute("INSERT OR IGNORE INTO game VALUES(?,?,?,?,?)", (ev["id"], league, ts, h, aw))
                c.commit()
                d0 = e + timedelta(days=1)
        todo = [r[0] for r in c.execute("SELECT id FROM game WHERE league=? AND id NOT IN (SELECT id FROM gdone WHERE league=?) ORDER BY start_ts", (league, league))]
        print(league, "box scores to fetch", len(todo), flush=True)
        for i, gid in enumerate(todo):
            try:
                s = jget(f"{base}/summary?event={gid}")
            except Exception as ex:  # noqa: BLE001
                print("fail", gid, ex, flush=True)
                continue
            rows = parse_box(league, s)
            for r in rows:
                c.execute("INSERT OR REPLACE INTO pstat VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (gid, league, r["aid"], r["nm"], r["team"], r["played"], r["pts"], r["reb"], r["ast"], r["tpm"],
                           r["rec"], r["recyds"], r["rshyds"], r["passyds"]))
            c.execute("INSERT OR REPLACE INTO gdone VALUES(?,?,?)", (gid, league, len(rows)))
            if i % 25 == 0:
                c.commit()
                print(league, i, "/", len(todo), flush=True)
            time.sleep(1.0)
        c.commit()
    print("espn done", flush=True)


# ----------------------------------------------------------------------------- Kalshi listings

def cmd_markets():
    c = conn()
    for series in SERIES_LEAGUE:
        for src, path, extra in (("hist", "/historical/markets", {}), ("live", "/markets", {"status": "settled"})):
            if c.execute("SELECT 1 FROM kdone WHERE series=? AND src=?", (series, src)).fetchone():
                continue
            cursor, n = None, 0
            while True:
                q = dict(series_ticker=series, limit=1000, **extra)
                if cursor:
                    q["cursor"] = cursor
                d = api._get(path, q)
                time.sleep(0.6)
                for m in d.get("markets", []):
                    ct = m.get("close_time") or ""
                    ex = m.get("expected_expiration_time") or ct
                    if ct >= CUT_ISO or ex >= CUT_ISO or m.get("result") not in ("yes", "no"):
                        continue
                    name = (m.get("yes_sub_title") or "").split(":")[0]
                    c.execute("INSERT OR IGNORE INTO kmarket VALUES(?,?,?,?,?,?,?,?,?)",
                              (m["ticker"], series, m["event_ticker"], norm_name(name), m.get("floor_strike"), ct, ex, m["result"], src))
                    n += 1
                cursor = d.get("cursor")
                if not cursor:
                    break
            c.execute("INSERT OR REPLACE INTO kdone VALUES(?,?)", (series, src))
            c.commit()
            print(series, src, n, flush=True)


# ----------------------------------------------------------------------------- build

def event_date(event: str):
    m = re.match(r"^[A-Z0-9]+-(\d\d)([A-Z]{3})(\d\d)", event)
    if not m:
        return None
    mon = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"].index(m.group(2)) + 1
    return datetime(2000 + int(m.group(1)), mon, int(m.group(3)))


def cmd_build():
    c = conn()
    et = timezone(timedelta(hours=-5))  # tickers carry the US game date; +-1 day tolerance below
    # players by (league, name) -> list of (gid, start, aid)
    byname = defaultdict(list)
    for gid, lg, st, nm, aid in c.execute("SELECT p.gid,p.league,g.start_ts,p.nm,p.aid FROM pstat p JOIN game g ON g.id=p.gid AND g.league=p.league WHERE p.played=1"):
        byname[(lg, nm)].append((gid, st, aid))
    # 1. match markets -> ESPN game by date and player name
    c.execute("DELETE FROM mgame")
    unmatched = defaultdict(int)
    total = defaultdict(int)
    rows = list(c.execute("SELECT ticker,series,event,name,close_time FROM kmarket"))
    for tk, series, event, name, ct in rows:
        lg, stat = SERIES_LEAGUE[series]
        total[lg] += 1
        d = event_date(event)
        best = None
        for gid, st, aid in byname.get((lg, name), []):
            gd = datetime.fromtimestamp(st, tz=timezone.utc).astimezone(et).replace(tzinfo=None)
            diff = abs((gd.replace(hour=0, minute=0, second=0, microsecond=0) - d).days) if d else 9
            if diff <= 1 and (best is None or diff < best[0]):
                best = (diff, gid, aid)
        if best is None:
            unmatched[lg] += 1
            continue
        c.execute("INSERT INTO mgame(ticker,gid,league,stat,aid) VALUES(?,?,?,?,?)", (tk, best[1], lg, stat, best[2]))
    c.commit()
    for lg in LEAGUES:
        print(lg, "markets", total[lg], "unmatched", unmatched[lg], f"match rate {1 - unmatched[lg] / max(1, total[lg]):.3f}", flush=True)
    # 2. split per league by matched-game start time
    split_ts = {}
    for lg in LEAGUES:
        ts = sorted(r[0] for r in c.execute("SELECT DISTINCT g.start_ts FROM mgame m JOIN game g ON g.id=m.gid AND g.league=m.league WHERE m.league=?", (lg,)))
        gids = [r[0] for r in c.execute("SELECT DISTINCT g.id,g.start_ts FROM mgame m JOIN game g ON g.id=m.gid AND g.league=m.league WHERE m.league=? ORDER BY g.start_ts", (lg,))]
        if not gids:
            continue
        starts = sorted(r[0] for r in c.execute("SELECT DISTINCT g.id,g.start_ts FROM mgame m JOIN game g ON g.id=m.gid AND g.league=m.league WHERE m.league=?", (lg,)))
        gs = [(r[1], r[0]) for r in c.execute("SELECT DISTINCT g.id,g.start_ts FROM mgame m JOIN game g ON g.id=m.gid AND g.league=m.league WHERE m.league=?", (lg,))]
        gs.sort()
        n = len(gs)
        i_fit, i_half = (2 * n) // 3, (2 * n) // 3 + (n - (2 * n) // 3) // 2
        split_ts[lg] = gs[i_fit][0] if i_fit < n else gs[-1][0]
        for i, (st, gid) in enumerate(gs):
            sp = "FIT" if i < i_fit else ("T1" if i < i_half else "T2")
            c.execute("UPDATE mgame SET split=? WHERE gid=? AND league=?", (sp, gid, lg))
        print(lg, "matched games", n, "FIT", i_fit, "T1", i_half - i_fit, "T2", n - i_half, flush=True)
    c.commit()
    # 3. player histories and fit (FIT ESPN stats only: games starting before the first TEST game)
    stats_cols = {"pts": 6, "reb": 7, "ast": 8, "tpm": 9, "rec": 10, "recyds": 11, "rshyds": 12, "passyds": 13}
    hist = defaultdict(list)  # (league, aid) -> [(start, {stat: val})]
    for r in c.execute("SELECT p.league,p.aid,g.start_ts,p.pts,p.reb,p.ast,p.tpm,p.rec,p.recyds,p.rshyds,p.passyds FROM pstat p JOIN game g ON g.id=p.gid AND g.league=p.league WHERE p.played=1 ORDER BY g.start_ts"):
        hist[(r[0], r[1])].append((r[2], dict(zip(("pts", "reb", "ast", "tpm", "rec", "recyds", "rshyds", "passyds"), r[3:]))))
    fits = {}
    for lg, (_, ser, _) in LEAGUES.items():
        if lg not in split_ts:
            continue
        for stat in set(ser.values()):
            allv, rows_fit = [], []
            for (l2, aid), L in hist.items():
                if l2 != lg:
                    continue
                prior = []
                for st, d in L:
                    if st >= split_ts[lg]:
                        break
                    v = max(0.0, d[stat])  # negative yards counted as 0 (NB needs counts)
                    allv.append(v)
                    if len(prior) >= 3:
                        rows_fit.append((list(prior), max(0, int(round(v)))))
                    prior.append(v)
            m_lg = sum(allv) / len(allv) if allv else 1.0
            best = fit_kr(rows_fit, m_lg)
            if best:
                fits[(lg, stat)] = (best[1], best[2], m_lg)
                c.execute("INSERT OR REPLACE INTO fit VALUES(?,?,?,?,?,?)", (lg, stat, best[1], best[2], m_lg, best[3]))
                print("fit", lg, stat, "k", best[1], "r", best[2], "m_lg", round(m_lg, 3), "n", best[3], flush=True)
    c.commit()
    # 4. model for TEST markets, then the sha1 sample of SAMPLE per game
    games = defaultdict(list)
    for tk, gid, lg, stat, aid in list(c.execute("SELECT ticker,gid,league,stat,aid FROM mgame WHERE split IN ('T1','T2')")):
        k = c.execute("SELECT strike FROM kmarket WHERE ticker=?", (tk,)).fetchone()
        st_row = c.execute("SELECT start_ts FROM game WHERE id=? AND league=?", (gid, lg)).fetchone()
        if (lg, stat) not in fits or k is None or k[0] is None:
            continue
        kk, rr, mlg = fits[(lg, stat)]
        prior = [max(0.0, d[stat]) for st, d in hist[(lg, aid)] if st < st_row[0]]
        mu = shrunk_mean(prior, mlg, kk)
        if mu is None:
            continue
        py = nb_sf(k[0], mu, rr)
        c.execute("UPDATE mgame SET mu=?, p_yes=? WHERE ticker=?", (mu, py, tk))
        games[(gid, lg)].append(tk)
    for (gid, lg), tks in games.items():
        for tk in choose_sample(tks):
            c.execute("UPDATE mgame SET sampled=1 WHERE ticker=?", (tk,))
    c.commit()
    print("TEST games", len(games), "sampled markets", c.execute("SELECT COUNT(*) FROM mgame WHERE sampled=1").fetchone()[0], flush=True)


# ----------------------------------------------------------------------------- candles

def cmd_candles():
    c = conn()
    todo = [r for r in c.execute("""SELECT m.ticker,k.series,k.close_time,g.start_ts,k.src FROM mgame m JOIN kmarket k ON k.ticker=m.ticker
        JOIN game g ON g.id=m.gid AND g.league=m.league WHERE m.sampled=1 AND m.ticker NOT IN (SELECT ticker FROM cdone)""")]
    todo.sort(key=lambda r: (sha(str(r[3])[:0] + r[0].rsplit('-', 1)[0]), r[0]))  # by sha1(game-player prefix): stopping early stays unbiased
    print("candles to fetch", len(todo), flush=True)
    live = [r for r in todo if r[4] == "live"]
    hist_ = [r for r in todo if r[4] != "live"]
    done = 0
    for tk, series, ct, st, _ in hist_:
        a, b = st - 7200, st
        try:
            d = api._get(f"/historical/markets/{tk}/candlesticks", {"start_ts": a, "end_ts": b, "period_interval": 1})
            cs = d.get("candlesticks", [])
        except Exception:  # noqa: BLE001
            cs = None
        if cs is not None:
            for x in cs:
                c.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
            c.execute("INSERT OR REPLACE INTO cdone VALUES(?,?)", (tk, len(cs)))
        done += 1
        if done % 100 == 0:
            c.commit()
            print("hist", done, "/", len(hist_), flush=True)
        time.sleep(0.4)
    c.commit()
    for i in range(0, len(live), 8):
        batch = live[i:i + 8]
        st = max(b[3] for b in batch)
        a, b = min(x[3] for x in batch) - 7200, st
        try:
            res = api.batch_candlesticks([x[0] for x in batch], a, b)
        except Exception:  # noqa: BLE001
            res = None
        if res is not None:
            for tk in [x[0] for x in batch]:
                cs = res.get(tk, [])
                for x in cs:
                    c.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
                c.execute("INSERT OR REPLACE INTO cdone VALUES(?,?)", (tk, len(cs)))
        if (i // 8) % 20 == 0:
            c.commit()
            print("live", i, "/", len(live), flush=True)
        time.sleep(0.7)
    c.commit()
    print("candles done", flush=True)


# ----------------------------------------------------------------------------- score

def load_entries(c):
    """Cheap-side candidates of the sampled TEST markets: dicts with game, split, league, stat, side, ask, p_side, win."""
    out = []
    q = """SELECT m.ticker,m.gid,m.league,m.stat,m.split,m.p_yes,k.result,k.strike,g.start_ts FROM mgame m
           JOIN kmarket k ON k.ticker=m.ticker JOIN game g ON g.id=m.gid AND g.league=m.league
           WHERE m.sampled=1 AND m.p_yes IS NOT NULL"""
    for tk, gid, lg, stat, sp, py, res, strike, st in list(c.execute(q)):
        look = st - LEAD
        cs = [r for r in c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=? AND end_ts<=? ORDER BY end_ts", (tk, look))]
        cs = [r for r in cs if valid(r[1], r[2])]
        if not cs:
            continue
        _, bid, ask = cs[-1]
        side = cheap_side(bid, ask)
        if side is None:
            continue
        s, a = side
        out.append(dict(ticker=tk, game=f"{lg}:{gid}", league=lg, stat=stat, split=sp, side=s, ask=a, start=st,
                        p_side=py if s == "yes" else 1 - py, win=(res == "yes") == (s == "yes")))
    return out


def summarise(trades, mult=1.0):
    by = defaultdict(list)
    for t in trades:
        by[t["game"]].append(net(t["win"], t["ask"], mult))
    n, m, se, z = cluster_stats(by)
    nets = [x for L in by.values() for x in L]
    wins = sum(1 for t in trades if t["win"])
    return dict(n=n, games=len(by), mean_c=100 * m, se_c=100 * se, z=z, pf=profit_factor(nets),
                win=wins / n if n else float("nan"), price=(sum(t["ask"] for t in trades) / n if n else float("nan")))


def cmd_score():
    c = conn()
    ents = load_entries(c)
    bygame = defaultdict(list)
    for e in ents:
        bygame[e["game"]].append(e)
    treated, control, allcheap = [], [], []
    for g, L in bygame.items():
        treated += pick_trades(L, True)
        control += pick_trades(L, False)
        allcheap += L
    res = {"entries_cheap": len(ents), "games": len(bygame)}
    for nm, T in (("treated", treated), ("control_cap2", control), ("all_cheap", allcheap)):
        res[nm] = summarise(T)
        res[nm + "_x1.2"] = summarise(T, 1.2)
        for h in ("T1", "T2"):
            res[nm + "_" + h] = summarise([t for t in T if t["split"] == h])
        for lg in LEAGUES:
            res[nm + "_" + lg] = summarise([t for t in T if t["league"] == lg])
    json.dump(res, open(Path(__file__).resolve().parents[2] / "workers" / "PROPS1_RESULT.json", "w"), indent=1)
    for k, v in res.items():
        print(k, v if not isinstance(v, dict) else {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items()})


if __name__ == "__main__":
    {"espn": cmd_espn, "markets": cmd_markets, "build": cmd_build, "candles": cmd_candles, "score": cmd_score}[sys.argv[1]]()
