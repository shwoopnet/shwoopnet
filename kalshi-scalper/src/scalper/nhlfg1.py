"""NHLFG1: cheap-side pool on NHL first-goal-scorer (KXNHLFIRSTGOAL) and 2+ goal (KXNHLGOAL strike 1.5) rungs. Research only.
Registration: workers/NHLFG1_REGISTRATION.md. Listing fields copied here never include result or price. Game id = the event ticker suffix
after the series (e.g. 26JUN14CARVGK); games are taken in strict md5 order of that id. Games before the frozen cut 2026-10-03T16:00Z only.
  python -m scalper.nhlfg1 build | census OUT.json | candles MINUTES | score | results
"""
from __future__ import annotations
import json, sqlite3, sys, time, statistics as st
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from . import api
from .candlefield import quote_close
from .nhlg1 import net, cheap_side, valid, cluster_stats, profit_factor, event_teams, event_date, md5, sha, team_code, DB as SRC_DB
from .nhlall1 import look_quote, pick_two, terciles, tercile_of, verdict, MIN_TRADES

CUT = "2026-10-03T16:00:00Z"
CACHE = Path("/home/user/.cache/nhlfg1")
DB = CACHE / "nhlfg1.sqlite"
ROOT = Path(__file__).resolve().parents[2]
SERIES = {"FG": "KXNHLFIRSTGOAL", "G2": "KXNHLGOAL"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS gm(gid TEXT PRIMARY KEY, espn TEXT, start_ts INTEGER, md5 TEXT);
CREATE TABLE IF NOT EXISTS rung(ticker TEXT PRIMARY KEY, kind TEXT, gid TEXT, volume REAL);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS cdone(ticker TEXT PRIMARY KEY, n INTEGER);
CREATE TABLE IF NOT EXISTS res(ticker TEXT PRIMARY KEY, result TEXT);
"""


def conn():
    CACHE.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=120)
    c.executescript(SCHEMA)
    return c


def gid_of(event: str) -> str:
    return event.split("-", 1)[1]


def clustered(trades, key, mult=1.0):
    by = defaultdict(list)
    for t in trades:
        by[t[key]].append(net(t["win"], t["ask"], mult))
    n, m, se, z = cluster_stats(by)
    nets = [x for L in by.values() for x in L]
    return dict(n=n, clusters=len(by), mean_c=100 * m, se_c=100 * se, z=z, lo95_c=100 * (m - 1.96 * se) if se == se else float("nan"),
                pf=profit_factor(nets), win=(sum(1 for t in trades if t["win"]) / n if n else float("nan")),
                price=(sum(t["ask"] for t in trades) / n if n else float("nan")))


def build():
    s = sqlite3.connect(SRC_DB, timeout=120)
    c = conn()
    et = timezone(timedelta(hours=-5))
    games, pair = {}, defaultdict(list)
    for gid, stt, h, a in s.execute("SELECT id,start_ts,home,away FROM game"):
        games[gid] = dict(st=stt, h=team_code(h), a=team_code(a))
        pair[frozenset((team_code(h), team_code(a)))].append(gid)
    rows = []
    for k, S in SERIES.items():
        f = CACHE / f"list_{S}.json" if k == "FG" else Path("/home/user/.cache/nhlg1/listing.json")
        for r in json.load(open(f)):
            if (r["close_time"] or "") >= CUT or not float(r["volume_fp"] or 0) > 0:
                continue
            if k == "G2" and r["floor_strike"] != 1.5:
                continue
            rows.append((r["ticker"], k, r["event_ticker"], float(r["volume_fp"])))
    ev_game, unmatched = {}, set()
    for tk, k, ev, vol in rows:
        if ev not in ev_game and ev not in unmatched:
            tm, d = event_teams(ev), event_date(ev)
            best = None
            for g in pair.get(frozenset(tm), []) if tm else []:
                gd = datetime.fromtimestamp(games[g]["st"], tz=timezone.utc).astimezone(et).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
                diff = abs((gd - d).days) if d else 9
                if diff <= 1 and (best is None or diff < best[0]):
                    best = (diff, g)
            (unmatched.add(ev) if best is None else ev_game.__setitem__(ev, best[1]))
        if ev in ev_game:
            g = gid_of(ev)
            c.execute("INSERT OR IGNORE INTO rung VALUES(?,?,?,?)", (tk, k, g, vol))
            c.execute("INSERT OR REPLACE INTO gm VALUES(?,?,?,?)", (g, ev_game[ev], games[ev_game[ev]]["st"], md5(g)))
    c.commit()
    return len(unmatched)


def census(out):
    un = build()
    c = conn()
    res = dict(unmatched_events=un, games_matched=c.execute("SELECT COUNT(*) FROM gm").fetchone()[0])
    for k in SERIES:
        per = [r[0] for r in c.execute("SELECT COUNT(*) FROM rung WHERE kind=? GROUP BY gid", (k,))]
        res[k] = dict(games=len(per), rungs=sum(per), rungs_per_game_median=st.median(per), mean=sum(per) / len(per))
    nhlall = Path("/home/user/.cache/nhlall1/nhlall1.sqlite")
    if nhlall.exists():
        a = sqlite3.connect(nhlall)
        used = {r[0][10:] for r in a.execute("SELECT DISTINCT r.event FROM rung r JOIN cdone d ON d.ticker=r.ticker")}
        allg = {r[0] for r in c.execute("SELECT gid FROM gm")}
        res["games_already_fetched_by_NHLALL1"] = len(used & allg)
    json.dump(res, open(out, "w"), indent=1)
    print(res)


def get_candles(tk, stt):
    for a in range(8):
        try:
            return api._get(f"/historical/markets/{tk}/candlesticks", {"start_ts": stt - 3600, "end_ts": stt, "period_interval": 1}, retries=1).get("candlesticks", [])
        except Exception as e:  # noqa: BLE001
            if "404" in str(e) and a >= 1:
                return None
            time.sleep(2 + 4 * a)
    return None


def candidate_trades(c, kind, gid, stt):
    """Quotes only: min(2, cheap rungs) if at least 8 valid FG quotes (3 for G2), else 0."""
    nl = ch = 0
    for (tk,) in c.execute("SELECT ticker FROM rung WHERE kind=? AND gid=?", (kind, gid)).fetchall():
        q = look_quote(c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=?", (tk,)).fetchall(), stt)
        if q is None:
            continue
        nl += 1
        ch += cheap_side(*q) is not None
    return min(2, ch) if nl >= (8 if kind == "FG" else 3) else 0


def cmd_candles(minutes_fg, minutes_g2):
    """ONE process. Phase 1: FG rungs, strict md5 order of game id, stop at 150 candidate trades or minutes_fg. Phase 2: G2 rungs of the
    same games in the same order, stop at 150 candidate trades or minutes_g2. Each market up to 8 attempts; a game is dropped only if one still fails."""
    c = conn()
    starts = {r[0]: r[1] for r in c.execute("SELECT gid,start_ts FROM gm")}
    for kind, mins in (("FG", minutes_fg), ("G2", minutes_g2)):
        t_end = time.time() + 60 * mins
        byg = defaultdict(list)
        for tk, g in c.execute("SELECT ticker,gid FROM rung WHERE kind=?", (kind,)):
            byg[g].append(tk)
        order = sorted(byg, key=md5)
        total = games = 0
        for g in order:
            if total >= MIN_TRADES:
                print(kind, "stopping rule: candidate trades", total, "games", games, flush=True)
                break
            if time.time() > t_end:
                print(kind, "time box reached: candidate trades", total, "games", games, flush=True)
                break
            for tk in byg[g]:
                if c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone():
                    continue
                cs = get_candles(tk, starts[g])
                time.sleep(0.6)
                if cs is None:
                    break
                for x in cs:
                    c.execute("INSERT OR IGNORE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
                c.execute("INSERT OR IGNORE INTO cdone VALUES(?,?)", (tk, len(cs)))
                c.commit()
            if all(c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone() for tk in byg[g]):
                games += 1
                total += candidate_trades(c, kind, g, starts[g])
                print(kind, "game", games, g, "candidate trades", total, flush=True)
            else:
                print(kind, "dropped after retries:", g, flush=True)
        else:
            print(kind, "order exhausted", total, games, flush=True)


def cmd_results():
    """Score-time only: results of the fetched markets. FG from a fresh settled listing (result only), G2 from nhlg1.sqlite."""
    c = conn()
    need = {r[0] for r in c.execute("SELECT ticker FROM cdone")}
    s = sqlite3.connect(SRC_DB, timeout=120)
    for tk, r in s.execute("SELECT ticker,result FROM kmarket"):
        if tk in need and r in ("yes", "no"):
            c.execute("INSERT OR REPLACE INTO res VALUES(?,?)", (tk, r))
    games = {r[0] for r in c.execute("SELECT gid FROM rung WHERE ticker IN (SELECT ticker FROM cdone) AND kind='FG'")}
    for pth, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cur = None
        while True:
            q = dict(series_ticker="KXNHLFIRSTGOAL", limit=1000, **extra)
            if cur:
                q["cursor"] = cur
            d = api._get(pth, q)
            time.sleep(1)
            for m in d.get("markets", []):
                if m["ticker"] in need and m.get("result") in ("yes", "no"):
                    c.execute("INSERT OR REPLACE INTO res VALUES(?,?)", (m["ticker"], m["result"]))
            cur = d.get("cursor")
            if not cur:
                break
    c.commit()
    print("results", c.execute("SELECT COUNT(*) FROM res").fetchone()[0], "needed", len(need))


def entries(c, kind):
    res = {tk: r for tk, r in c.execute("SELECT ticker,result FROM res")}
    done = {r[0] for r in c.execute("SELECT ticker FROM cdone")}
    games = []
    for g, stt, m5 in c.execute("SELECT gid,start_ts,md5 FROM gm ORDER BY md5"):
        tks = [r[0] for r in c.execute("SELECT ticker FROM rung WHERE kind=? AND gid=?", (kind, g))]
        if not tks or any(t not in done for t in tks):
            continue
        ladder, cheap = [], []
        for tk in tks:
            q = look_quote(c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=?", (tk,)).fetchall(), stt)
            if q is None or res.get(tk) not in ("yes", "no"):
                continue
            bid, ask = q
            ladder.append((ask, res[tk] == "yes"))
            sd = cheap_side(bid, ask)
            if sd:
                side, a = sd
                cheap.append(dict(ticker=tk, game=g, date=g[:7], side=side, ask=a, win=(res[tk] == "yes") == (side == "yes"), start=stt))
        if len(ladder) < (8 if kind == "FG" else 3):
            continue
        games.append(dict(event=g, start=stt, lsum=sum(a for a, _ in ladder), scorers=sum(1 for _, y in ladder if y), nl=len(ladder), cheap=cheap))
    return games


def fmt(d):
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()}


def score_kind(c, kind, nall):
    G = entries(c, kind)
    if not G:
        return dict(games=0)
    third = G[: max(1, len(G) // 3)]
    cuts = terciles([g["lsum"] for g in third])
    med = st.median([g["start"] for g in G])
    for g in G:
        g["tc"] = tercile_of(g["lsum"], cuts)
        for t in g["cheap"]:
            t["half"], t["tc"], t["nhlall"] = ("H1" if g["start"] < med else "H2"), g["tc"], g["event"] in nall
    pool = [t for g in G for t in pick_two(g["cheap"])]
    allc = [t for g in G for t in g["cheap"]]
    out = dict(games=len(G), cheap_entries=len(allc), cuts=cuts, first_third_games=len(third), side_counts={s: sum(1 for t in allc if t["side"] == s) for s in ("yes", "no")})
    for nm, T in (("pool_cap2", pool), ("low_tercile_cap2", [t for t in pool if t["tc"] == 0])):
        d = dict(game=clustered(T, "game"), date=clustered(T, "date"), x12=clustered(T, "game", 1.2))
        for h in ("H1", "H2"):
            d[h] = clustered([t for t in T if t["half"] == h], "game")
        d["verdict"] = verdict(d["game"]["n"], [d["H1"]["mean_c"], d["H2"]["mean_c"]], d["game"]["lo95_c"], d["game"]["pf"])
        out[nm] = d
    out["by_tercile_cap2"] = {i: clustered([t for t in pool if t["tc"] == i], "game") for i in range(3)}
    out["tercile_games"] = {i: sum(1 for g in G if g["tc"] == i) for i in range(3)}
    out["pool_not_in_NHLALL1_games"] = clustered([t for t in pool if not t["nhlall"]], "game")
    out["pool_in_NHLALL1_games"] = clustered([t for t in pool if t["nhlall"]], "game")
    out["uncapped_information"] = clustered(allc, "game")
    out["by_ask_information"] = {nm: clustered([t for t in allc if lo <= t["ask"] < hi], "game") for lo, hi, nm in ((0.03, 0.08, "3-8c"), (0.08, 0.15, "8-15c"), (0.15, 0.30001, "15-30c"))}
    out["ladder"] = dict(mean_sum_ask=sum(g["lsum"] for g in G) / len(G), mean_realised_yes=sum(g["scorers"] for g in G) / len(G), mean_rungs=sum(g["nl"] for g in G) / len(G))
    return out


def score():
    c = conn()
    nall = set()
    p = Path("/home/user/.cache/nhlall1/nhlall1.sqlite")
    if p.exists():
        a = sqlite3.connect(p)
        nall = {r[0][10:] for r in a.execute("SELECT DISTINCT r.event FROM rung r JOIN cdone d ON d.ticker=r.ticker")}
    out = {k: score_kind(c, k, nall) for k in SERIES}
    json.dump(out, open(ROOT / "workers" / "NHLFG1_RESULT.json", "w"), indent=1, default=str)
    for k, v in out.items():
        print("==", k)
        for a, b in v.items():
            print(a, ({x: (fmt(y) if isinstance(y, dict) else y) for x, y in b.items()} if isinstance(b, dict) and a not in ("cuts",) and any(isinstance(y, dict) for y in b.values()) else (fmt(b) if isinstance(b, dict) else b)))


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"build": lambda: print(build()), "census": lambda: census(sys.argv[2]), "results": cmd_results, "score": score,
     "candles": lambda: cmd_candles(float(sys.argv[2]), float(sys.argv[3]))}[cmd]()
