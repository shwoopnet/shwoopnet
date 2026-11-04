"""NHLG1: KXNHLGOAL anytime goal scorer ladders, CHEAP side only (ask 3c to 30c), against a game-log Poisson goal rate.

Registration: workers/NHLG1_REGISTRATION.md. Data in data/nhlg1.sqlite (git-ignored); raw listing in /home/user/.cache/nhlg1/listing.json.
  python -m scalper.nhlg1 espn      # ESPN scoreboards and box scores (1 req/s), games before the frozen cut only
  python -m scalper.nhlg1 markets   # Kalshi listing with results (needed for the join) for pre-cut markets with volume
  python -m scalper.nhlg1 build     # match, split FIT/TEST, fit k and gamma on ESPN goals of FIT, model
  python -m scalper.nhlg1 candles MINUTES   # TEST games in md5 order, time boxed, resumable
  python -m scalper.nhlg1 score
The frozen games (from 2026-10-03T16:00Z) are never fetched: every query is bounded by CUT.
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
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import api
from .candlefield import quote_close

DB = Path(__file__).resolve().parents[2] / "data" / "nhlg1.sqlite"
LISTING = Path("/home/user/.cache/nhlg1/listing.json")
CUT_ISO = "2026-10-03T16:00:00Z"
CUT_TS = int(datetime(2026, 10, 3, 16, tzinfo=timezone.utc).timestamp())
LO, HI, RATIO, C, LEAD, MAXPER = 0.03, 0.30, 3.0, 10, 300, 2
UA = "shwoopnet-research-nhlg1/1.0 (personal research, 1 req/s)"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl"
KS_GRID, GAMMAS = (5, 10, 20, 40, 80, 160), (0.0, 0.5, 1.0)
MIN_PRIOR, LAST = 5, 20
TEAM_MAP = {"TB": "TBL", "NJ": "NJD", "SJ": "SJS", "LA": "LAK", "UTAH": "UTA", "WAS": "WSH"}


# ----------------------------------------------------------------------------- pure functions (tested)

def fee(p: float, c: int = C) -> float:
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win: bool, ask: float, mult: float = 1.0) -> float:
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def sha(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z ]", " ", s)
    return " ".join(w for w in s.split() if w not in ("jr", "sr", "ii", "iii", "iv"))


def team_code(c: str) -> str:
    return TEAM_MAP.get(c, c)


def pois_logpmf(x: int, mu: float) -> float:
    return x * math.log(mu) - mu - math.lgamma(x + 1)


def pois_ge(n: int, mu: float) -> float:
    """P(X >= n) for X ~ Poisson(mu)."""
    if n <= 0:
        return 1.0
    term = math.exp(-mu)
    cdf = term
    for j in range(1, n):
        term *= mu / j
        cdf += term
    return max(0.0, min(1.0, 1.0 - cdf))


def shrunk_rate(prior: list, m_lg: float, k: float):
    """Earlier goal counts, oldest first: the last up to 20 shrunk toward the league mean; None under 5 games."""
    last = prior[-LAST:]
    if len(last) < MIN_PRIOR:
        return None
    return max(0.005, (sum(last) + k * m_lg) / (len(last) + k))


def def_factor(opp_ga: list, lg_g: float, gamma: float) -> float:
    last = opp_ga[-LAST:]
    shr = (sum(last) + 10 * lg_g) / (len(last) + 10)
    return (shr / lg_g) ** gamma


def fit_params(rows, m_lg: float, lg_g: float):
    """rows: (prior goals, opp prior GA, actual goals). Best FIT Poisson log likelihood on the registered grid -> (ll, k, gamma, n)."""
    best = None
    for k in KS_GRID:
        for g in GAMMAS:
            ll, n = 0.0, 0
            for pr, oga, a in rows:
                r0 = shrunk_rate(pr, m_lg, k)
                if r0 is None:
                    continue
                ll += pois_logpmf(a, r0 * def_factor(oga, lg_g, g))
                n += 1
            if n and (best is None or ll > best[0]):
                best = (ll, k, g, n)
    return best


def event_date(event: str):
    m = re.match(r"^[A-Z0-9]+-(\d\d)([A-Z]{3})(\d\d)", event)
    if not m:
        return None
    mon = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"].index(m.group(2)) + 1
    return datetime(2000 + int(m.group(1)), mon, int(m.group(3)))


KNOWN = {"ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL", "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI",
         "NYR", "OTT", "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WPG", "WSH"}


def event_teams(event: str):
    """(away, home) ESPN codes from the event ticker tail (Kalshi writes TB, LA, NJ, SJ with two letters); None if it does not split."""
    m = re.match(r"^[A-Z0-9]+-\d\d[A-Z]{3}\d\d([A-Z]{4,6})$", event)
    if not m:
        return None
    t = m.group(1)
    for i in (3, 2, 4):
        x, y = t[:i], t[i:]
        if team_code(x) in KNOWN and team_code(y) in KNOWN:
            return team_code(x), team_code(y)
    return None


def player_team(ticker: str, teams):
    """The player's team: the ticker's player segment starts with that team's code (raw or mapped)."""
    parts = ticker.split("-")
    if len(parts) < 3:
        return None
    seg = parts[2]
    cands = []
    for t in teams or ():
        cands += [(t, t)] + [(k, t) for k, v in TEAM_MAP.items() if v == t]
    for raw, t in sorted(cands, key=lambda x: -len(x[0])):
        if seg.startswith(raw):
            return t
    return None


def cheap_side(bid: float, ask: float):
    if LO <= ask <= HI:
        return "yes", ask
    if LO <= 1 - bid <= HI:
        return "no", 1 - bid
    return None


def valid(b, a) -> bool:
    return b is not None and a is not None and 0 <= b < a <= 1 and a - b <= 0.10


def pick_trades(rows: list, treated: bool) -> list:
    if treated:
        ok = [r for r in rows if r["p_side"] >= RATIO * r["ask"]]
        ok.sort(key=lambda r: (-r["p_side"] / r["ask"], sha(r["ticker"])))
    else:
        ok = sorted(rows, key=lambda r: sha(r["ticker"]))
    return ok[:MAXPER]


def cluster_stats(by: dict):
    xs = [v for L in by.values() for v in L]
    n = len(xs)
    if n < 2:
        return n, (xs[0] if xs else float("nan")), float("nan"), float("nan")
    m = sum(xs) / n
    s = sum(sum(v - m for v in L) ** 2 for L in by.values())
    se = math.sqrt(s) / n
    return n, m, se, (m / se if se > 0 else float("nan"))


def profit_factor(nets: list) -> float:
    g = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return g / l if l > 0 else float("inf")


def split_labels(n: int):
    """First two thirds FIT, then the last third halved T1 (older) / T2."""
    i_fit = (2 * n) // 3
    i_half = i_fit + (n - i_fit) // 2
    return ["FIT" if i < i_fit else ("T1" if i < i_half else "T2") for i in range(n)]


def parse_box(summ: dict):
    """-> list of dicts: aid, nm, team, goals, shots, toi (seconds). Skaters only (a block with a 'goals' key); goalies are left out."""
    out = []
    for tm in (summ.get("boxscore", {}) or {}).get("players", []) or []:
        team = (tm.get("team") or {}).get("abbreviation", "")
        for blk in tm.get("statistics", []) or []:
            keys = blk.get("keys") or []
            if "goals" not in keys:
                continue
            for a in blk.get("athletes", []) or []:
                ath, st = a.get("athlete") or {}, a.get("stats") or []
                try:
                    g = int(float(st[keys.index("goals")]))
                    sh = int(float(st[keys.index("shotsTotal")])) if "shotsTotal" in keys else 0
                    mm, ss = (st[keys.index("timeOnIce")] or "0:0").split(":")
                    toi = int(mm) * 60 + int(ss)
                except (ValueError, IndexError):
                    continue
                if toi <= 0:
                    continue
                out.append(dict(aid=str(ath.get("id")), nm=norm_name(ath.get("displayName", "")), team=team, goals=g, shots=sh, toi=toi))
    return out


# ----------------------------------------------------------------------------- storage and fetch

SCHEMA = """
CREATE TABLE IF NOT EXISTS game(id TEXT PRIMARY KEY, start_ts INTEGER, home TEXT, away TEXT, hs INTEGER, as_ INTEGER);
CREATE TABLE IF NOT EXISTS gdone(id TEXT PRIMARY KEY, n INTEGER);
CREATE TABLE IF NOT EXISTS skater(gid TEXT, aid TEXT, nm TEXT, team TEXT, goals INTEGER, shots INTEGER, toi INTEGER, PRIMARY KEY(gid, aid));
CREATE TABLE IF NOT EXISTS kmarket(ticker TEXT PRIMARY KEY, event TEXT, name TEXT, strike REAL, close_time TEXT, volume REAL, result TEXT);
CREATE TABLE IF NOT EXISTS mgame(ticker TEXT PRIMARY KEY, gid TEXT, split TEXT, rate REAL, p_yes REAL);
CREATE TABLE IF NOT EXISTS fit(id INTEGER PRIMARY KEY, k REAL, gamma REAL, m_lg REAL, lg_g REAL, n INTEGER);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS cdone(ticker TEXT PRIMARY KEY, n INTEGER);
"""


def conn():
    DB.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB, timeout=60)
    c.executescript(SCHEMA)
    return c


def jget(url: str, tries: int = 6):
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


def cmd_espn():
    c = conn()
    d0, d1 = datetime(2025, 10, 1), datetime(2026, 10, 2)
    done_days = {r[0] for r in c.execute("SELECT id FROM gdone WHERE id LIKE 'day:%'")}
    while d0 <= d1:
        key = f"day:{d0:%Y%m%d}"
        if key not in done_days:
            sb = jget(f"{ESPN}/scoreboard?dates={d0:%Y%m%d}&limit=100")
            time.sleep(1.0)
            for ev in sb.get("events", []):
                typ = (ev.get("season") or {}).get("type")
                st = ((ev.get("status") or {}).get("type") or {}).get("name", "")
                ts = int(datetime.strptime(ev["date"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc).timestamp())
                if typ not in (2, 3) or st != "STATUS_FINAL" or ts >= CUT_TS:
                    continue
                comp = (ev.get("competitions") or [{}])[0].get("competitors", [])
                h = next((x for x in comp if x.get("homeAway") == "home"), None)
                a = next((x for x in comp if x.get("homeAway") == "away"), None)
                if not h or not a:
                    continue
                c.execute("INSERT OR IGNORE INTO game VALUES(?,?,?,?,?,?)",
                          (ev["id"], ts, h["team"]["abbreviation"], a["team"]["abbreviation"], int(float(h.get("score") or 0)), int(float(a.get("score") or 0))))
            c.execute("INSERT OR REPLACE INTO gdone VALUES(?,?)", (key, 0))
            c.commit()
        d0 += timedelta(days=1)
    todo = [r[0] for r in c.execute("SELECT id FROM game WHERE id NOT IN (SELECT id FROM gdone) ORDER BY start_ts")]
    print("box scores to fetch", len(todo), flush=True)
    for i, gid in enumerate(todo):
        try:
            s = jget(f"{ESPN}/summary?event={gid}")
        except Exception as ex:  # noqa: BLE001
            print("fail", gid, ex, flush=True)
            continue
        rows = parse_box(s)
        for p in rows:
            c.execute("INSERT OR REPLACE INTO skater VALUES(?,?,?,?,?,?,?)", (gid, p["aid"], p["nm"], p["team"], p["goals"], p["shots"], p["toi"]))
        c.execute("INSERT OR REPLACE INTO gdone VALUES(?,?)", (gid, len(rows)))
        if i % 25 == 0:
            c.commit()
            print("box", i, "/", len(todo), flush=True)
        time.sleep(1.0)
    c.commit()
    print("espn done: games", c.execute("SELECT COUNT(*) FROM game").fetchone()[0], "with box", c.execute("SELECT COUNT(*) FROM gdone WHERE id NOT LIKE 'day:%'").fetchone()[0], flush=True)


def cmd_markets():
    """Re-list the series (cursor) and keep result for pre-cut markets with volume > 0. Results are read once, for the join."""
    c = conn()
    if c.execute("SELECT COUNT(*) FROM kmarket").fetchone()[0] > 0:
        print("kmarket already filled", flush=True)
        return
    kept = dropped = 0
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cursor = None
        while True:
            q = dict(series_ticker="KXNHLGOAL", limit=1000, **extra)
            if cursor:
                q["cursor"] = cursor
            d = api._get(path, q)
            time.sleep(1.0)
            for m in d.get("markets", []):
                ct = m.get("close_time") or ""
                ex = m.get("expected_expiration_time") or ct
                vol = float(m.get("volume_fp") or 0)
                if ct >= CUT_ISO or ex >= CUT_ISO or m.get("floor_strike") is None or vol <= 0:
                    continue
                if m.get("result") not in ("yes", "no"):
                    dropped += 1
                    continue
                name = (m.get("yes_sub_title") or "").split(":")[0]
                c.execute("INSERT OR IGNORE INTO kmarket VALUES(?,?,?,?,?,?,?)",
                          (m["ticker"], m["event_ticker"], norm_name(name), m["floor_strike"], ct, vol, m["result"]))
                kept += 1
            cursor = d.get("cursor")
            if not cursor:
                break
        c.commit()
        print(path, "kept", kept, "dropped (result not yes/no)", dropped, flush=True)


def cmd_build():
    c = conn()
    et = timezone(timedelta(hours=-5))
    games = {}
    pair = defaultdict(list)
    for gid, st, h, a, hs, as_ in c.execute("SELECT id,start_ts,home,away,hs,as_ FROM game"):
        games[gid] = dict(st=st, h=team_code(h), a=team_code(a), hs=hs, as_=as_)
        pair[frozenset((team_code(h), team_code(a)))].append(gid)
    box = defaultdict(dict)  # gid -> nm -> (team, goals)
    for gid, nm, team, g in c.execute("SELECT gid,nm,team,goals FROM skater"):
        box[gid][nm] = (team_code(team), g)
    # per-player history (appearances) and per-team history (goals allowed), time ordered
    phist = defaultdict(list)
    for gid, B in box.items():
        for nm, (_, g) in B.items():
            phist[nm].append((games[gid]["st"], g))
    for L in phist.values():
        L.sort()
    thist = defaultdict(list)
    for gid, g in games.items():
        thist[g["h"]].append((g["st"], g["hs"], g["as_"]))
        thist[g["a"]].append((g["st"], g["as_"], g["hs"]))
    for L in thist.values():
        L.sort()
    # match markets to games
    c.execute("DELETE FROM mgame")
    total = unmatched_game = unmatched_player = 0
    mk = []
    for tk, event, nm, strike, ct, vol, res in list(c.execute("SELECT ticker,event,name,strike,close_time,volume,result FROM kmarket")):
        total += 1
        tm, d = event_teams(event), event_date(event)
        best = None
        for gid in pair.get(frozenset(tm), []) if tm else []:
            gd = datetime.fromtimestamp(games[gid]["st"], tz=timezone.utc).astimezone(et).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
            diff = abs((gd - d).days) if d else 9
            if diff <= 1 and (best is None or diff < best[0]):
                best = (diff, gid)
        if best is None:
            unmatched_game += 1
            continue
        if nm not in phist:
            unmatched_player += 1
            continue
        mk.append((tk, best[1], nm, strike, player_team(tk, tm)))
    print("markets", total, "no game", unmatched_game, "no player history", unmatched_player, "kept", len(mk), flush=True)
    gs = sorted({(games[g]["st"], g) for _, g, _, _, _ in mk})
    labels = split_labels(len(gs))
    lab = {g: sp for (st, g), sp in zip(gs, labels)}
    split_ts = next((st for (st, g), sp in zip(gs, labels) if sp != "FIT"), gs[-1][0])
    print("matched games", len(gs), "FIT", labels.count("FIT"), "T1", labels.count("T1"), "T2", labels.count("T2"), flush=True)
    fit_goals = [g for L in phist.values() for st, g in L if st < split_ts]
    m_lg = sum(fit_goals) / len(fit_goals)
    fgs = [gf for L in thist.values() for st, gf, ga in L if st < split_ts]
    lg_g = sum(fgs) / len(fgs)
    rows = []
    for gid, B in box.items():
        st = games[gid]["st"]
        if st >= split_ts:
            continue
        for nm, (team, g) in B.items():
            prior = [v for s, v in phist[nm] if s < st]
            if len(prior) < MIN_PRIOR:
                continue
            opp = games[gid]["a"] if team == games[gid]["h"] else games[gid]["h"]
            oga = [ga for s, gf, ga in thist[opp] if s < st]  # goals the opponent has ALLOWED in earlier games
            rows.append((prior, oga, g))
    best = fit_params(rows, m_lg, lg_g)
    _, kk, gg, nn = best
    c.execute("INSERT OR REPLACE INTO fit VALUES(1,?,?,?,?,?)", (kk, gg, m_lg, lg_g, nn))
    print("fit k", kk, "gamma", gg, "m_lg", round(m_lg, 4), "lg_g", round(lg_g, 3), "skater games", nn, flush=True)
    made = 0
    for tk, gid, nm, strike, team in mk:
        sp = lab[gid]
        if sp == "FIT":
            c.execute("INSERT INTO mgame VALUES(?,?,?,NULL,NULL)", (tk, gid, sp))
            continue
        st = games[gid]["st"]
        prior = [v for s, v in phist[nm] if s < st]
        r0 = shrunk_rate(prior, m_lg, kk)
        if r0 is None or team not in (games[gid]["h"], games[gid]["a"]):
            continue
        opp = games[gid]["a"] if team == games[gid]["h"] else games[gid]["h"]
        oga = [ga for s, gf, ga in thist[opp] if s < st]
        rate = r0 * def_factor(oga, lg_g, gg)
        c.execute("INSERT INTO mgame VALUES(?,?,?,?,?)", (tk, gid, sp, rate, pois_ge(int(math.floor(strike)) + 1, rate)))
        made += 1
    c.commit()
    print("TEST markets with a model", made, "TEST games", len({g for _, g, *_ in mk if lab[g] != 'FIT'}), flush=True)


def cmd_candles(minutes: float):
    c = conn()
    t_end = time.time() + 60 * minutes
    starts = {r[0]: r[1] for r in c.execute("SELECT id,start_ts FROM game")}
    byg = defaultdict(list)
    for tk, gid in c.execute("SELECT ticker,gid FROM mgame WHERE split IN ('T1','T2') AND p_yes IS NOT NULL"):
        byg[gid].append(tk)
    ev = {r[0]: r[1] for r in c.execute("SELECT ticker,event FROM kmarket")}
    order = sorted(byg, key=lambda g: md5(ev[byg[g][0]]))
    print("TEST games", len(order), "markets", sum(len(v) for v in byg.values()), flush=True)
    done_games = 0
    for gi, gid in enumerate(order):
        if time.time() > t_end:
            print("time box reached at game", gi, flush=True)
            break
        st = starts[gid]
        for tk in byg[gid]:
            if c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone():
                continue
            cs = None
            for _ in range(3):
                try:
                    d = api._get(f"/historical/markets/{tk}/candlesticks", {"start_ts": st - 3600, "end_ts": st, "period_interval": 1}, retries=4)
                    cs = d.get("candlesticks", [])
                    break
                except Exception:  # noqa: BLE001
                    try:
                        cs = api.candlesticks("KXNHLGOAL", tk, st - 3600, st)
                        break
                    except Exception:  # noqa: BLE001
                        time.sleep(5)
            if cs is None:
                continue
            for x in cs:
                c.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
            c.execute("INSERT OR REPLACE INTO cdone VALUES(?,?)", (tk, len(cs)))
            time.sleep(0.4)
        c.commit()
        done_games += 1
        if gi % 10 == 0:
            print("game", gi, "/", len(order), flush=True)
    c.commit()
    print("candles pass done; games started", done_games, flush=True)


def load_entries(c):
    out, brier, ladders = [], [], defaultdict(list)
    q = """SELECT m.ticker,m.gid,m.split,m.p_yes,k.result,k.strike,g.start_ts FROM mgame m JOIN kmarket k ON k.ticker=m.ticker JOIN game g ON g.id=m.gid
           WHERE m.split IN ('T1','T2') AND m.p_yes IS NOT NULL"""
    rows = list(c.execute(q))
    done = {r[0] for r in c.execute("SELECT ticker FROM cdone")}
    tot, ok_g = defaultdict(int), defaultdict(int)
    for tk, gid, *_ in rows:
        tot[gid] += 1
        ok_g[gid] += tk in done
    full = {g for g in tot if tot[g] == ok_g[g]}
    for tk, gid, sp, py, res, strike, st in rows:
        if gid not in full:
            continue
        look = st - LEAD
        cs = [r for r in c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=? AND end_ts<=? ORDER BY end_ts", (tk, look)) if valid(r[1], r[2])]
        if not cs:
            continue
        _, bid, ask = cs[-1]
        y = 1.0 if res == "yes" else 0.0
        if strike == 0.5:
            ladders[gid].append((ask, py, y))
        side = cheap_side(bid, ask)
        if side is None:
            continue
        s, a = side
        ps = py if s == "yes" else 1 - py
        o = 1.0 if (y == 1.0) == (s == "yes") else 0.0
        brier.append(((ps - o) ** 2, (a - o) ** 2))
        out.append(dict(ticker=tk, game=gid, split=sp, side=s, ask=a, p_side=ps, win=(res == "yes") == (s == "yes"), strike=strike))
    return out, brier, ladders, full


def summarise(trades, mult=1.0):
    by = defaultdict(list)
    for t in trades:
        by[t["game"]].append(net(t["win"], t["ask"], mult))
    n, m, se, z = cluster_stats(by)
    nets = [x for L in by.values() for x in L]
    return dict(n=n, games=len(by), mean_c=100 * m, se_c=100 * se, z=z, pf=profit_factor(nets),
                win=(sum(1 for t in trades if t["win"]) / n if n else float("nan")), price=(sum(t["ask"] for t in trades) / n if n else float("nan")))


def cmd_score():
    c = conn()
    ents, brier, ladders, full = load_entries(c)
    bygame = defaultdict(list)
    for e in ents:
        bygame[e["game"]].append(e)
    treated, control, allcheap = [], [], []
    for g, L in bygame.items():
        treated += pick_trades(L, True)
        control += pick_trades(L, False)
        allcheap += L
    res = {"games_with_full_candles": len(full), "cheap_entries": len(ents), "games_with_cheap": len(bygame),
           "cheap_brier_model": sum(b[0] for b in brier) / max(1, len(brier)), "cheap_brier_ask": sum(b[1] for b in brier) / max(1, len(brier)),
           "mean_gap_pside_minus_ask": sum(e["p_side"] - e["ask"] for e in ents) / max(1, len(ents)),
           "treatable_ratio_ge3": sum(1 for e in ents if e["p_side"] >= RATIO * e["ask"])}
    for nm, T in (("treated", treated), ("control_cap2", control), ("all_cheap", allcheap)):
        res[nm] = summarise(T)
        res[nm + "_x1.2"] = summarise(T, 1.2)
        for h in ("T1", "T2"):
            res[nm + "_" + h] = summarise([t for t in T if t["split"] == h])
    # overround of the 1+ ladder: sum of YES asks vs sum of model probabilities vs scorers (prices and counts, descriptive)
    ov = [(sum(a for a, p, y in L), sum(p for a, p, y in L), sum(y for a, p, y in L), len(L)) for L in ladders.values() if len(L) >= 8]
    if ov:
        res["ladder_games"] = len(ov)
        res["ladder_mean_sum_ask"] = sum(o[0] for o in ov) / len(ov)
        res["ladder_mean_sum_model"] = sum(o[1] for o in ov) / len(ov)
        res["ladder_mean_scorers"] = sum(o[2] for o in ov) / len(ov)
        res["ladder_mean_players"] = sum(o[3] for o in ov) / len(ov)
    json.dump(res, open(Path(__file__).resolve().parents[2] / "workers" / "NHLG1_RESULT.json", "w"), indent=1)
    for k, v in res.items():
        print(k, v if not isinstance(v, dict) else {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items()})


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"espn": cmd_espn, "markets": cmd_markets, "build": cmd_build, "score": cmd_score}.get(cmd, lambda: cmd_candles(float(sys.argv[2])))()
