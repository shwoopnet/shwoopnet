"""NHLAST1: unconditional cheap-side pool on KXNHLAST (assists) and KXNHLPTS (points) 1+ and 2+ rungs, plus an under-round filter. Research only.
Registration: workers/NHLAST1_REGISTRATION.md. Listing in nhlast1_census.py; game start times from nhlg1.sqlite (ESPN); reuses nhlall1 helpers.
  python -m scalper.nhlast1 census OUT.json | candles SERIES MINUTES | score
"""
from __future__ import annotations
import json, sqlite3, sys, time, statistics as st
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from . import api
from .candlefield import quote_close
from .nhlg1 import cheap_side, event_teams, event_date, md5, team_code, DB as SRC_DB
from .nhlall1 import look_quote, pick_two, clustered, verdict, DB as ALL_DB, MIN_TRADES
from .nhlast1_census import DB as CDB

ROOT = Path(__file__).resolve().parents[2]
SERIES = ("KXNHLAST", "KXNHLPTS")
STRIKES = (0.5, 1.5)
MIN_LADDER = 5  # chosen from the listing counts (median 1+ rungs per game is 4 for assists, 6 for points), before any candle or result


def suffix(event: str) -> str:
    return event.split("-", 1)[1]


def game_key(event: str) -> str:
    """md5 of the game part of the event ticker, so the same game sits at the same place for both series."""
    return md5(suffix(event))


def order_games(events, deferred):
    """Strict md5 order, except games the goal samples already used go after all others (still in md5 order)."""
    return sorted(events, key=lambda e: (e in deferred, game_key(e)))


def e_fit(games):
    """Expected number of listed 1+ rungs that settle yes per game, from the FIT games (first two thirds in order) only."""
    fit = games[: (2 * len(games)) // 3]
    return sum(g["scorers"] for g in fit) / len(fit) if fit else float("nan")


def under_round(lsum, e):
    return lsum < e


def conn():
    return sqlite3.connect(CDB, timeout=120)


def cschema(c):
    c.executescript("""CREATE TABLE IF NOT EXISTS gm(event TEXT PRIMARY KEY, series TEXT, start_ts INTEGER, deferred INTEGER);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS cdone(ticker TEXT PRIMARY KEY, n INTEGER);""")


def used_goal_events():
    """KXNHLGOAL suffixes any goal sample touched: NHLG1's 25 events (nhlg1 cdone) and NHLALL1's fetched games (nhlall1 cdone)."""
    out = set()
    for dbp, tab in ((SRC_DB, "kmarket"), (ALL_DB, "rung")):
        s = sqlite3.connect(dbp, timeout=120)
        for (ev,) in s.execute(f"SELECT DISTINCT t.event FROM {tab} t JOIN cdone d ON d.ticker=t.ticker"):
            out.add(suffix(ev))
    return out


def build():
    s = sqlite3.connect(SRC_DB, timeout=120)
    c = conn()
    cschema(c)
    et = timezone(timedelta(hours=-5))
    games, pair = {}, defaultdict(list)
    for gid, stt, h, a in s.execute("SELECT id,start_ts,home,away FROM game"):
        games[gid] = dict(st=stt)
        pair[frozenset((team_code(h), team_code(a)))].append(gid)
    used = used_goal_events()
    rows = list(c.execute("SELECT DISTINCT event, series FROM kmarket WHERE strike IN (0.5,1.5)"))
    un = set()
    for ev, ser in rows:
        tm, d = event_teams(ev), event_date(ev)
        best = None
        for gid in pair.get(frozenset(tm), []) if tm else []:
            gd = datetime.fromtimestamp(games[gid]["st"], tz=timezone.utc).astimezone(et).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
            diff = abs((gd - d).days) if d else 9
            if diff <= 1 and (best is None or diff < best[0]):
                best = (diff, gid)
        if best is None:
            un.add(ev)
            continue
        c.execute("INSERT OR REPLACE INTO gm VALUES(?,?,?,?)", (ev, ser, games[best[1]]["st"], 1 if suffix(ev) in used else 0))
    c.commit()
    return len(rows), len(un)


def census(out):
    tot, un = build()
    c = conn()
    res = dict(unmatched_events=un, series={})
    for ser in SERIES:
        q = "FROM kmarket k JOIN gm g ON g.event=k.event WHERE k.series=? AND k.strike IN (0.5,1.5) AND k.volume>0"
        ng = c.execute("SELECT COUNT(*) FROM gm WHERE series=?", (ser,)).fetchone()[0]
        nd = c.execute("SELECT COUNT(*) FROM gm WHERE series=? AND deferred=1", (ser,)).fetchone()[0]
        per = [r[0] for r in c.execute("SELECT COUNT(*) " + q + " GROUP BY k.event", (ser,))]
        per1 = [r[0] for r in c.execute("SELECT COUNT(*) " + q + " AND k.strike=0.5 GROUP BY k.event", (ser,))]
        elig = c.execute("SELECT COUNT(*) FROM (SELECT k.event FROM kmarket k JOIN gm g ON g.event=k.event WHERE k.series=? AND k.strike=0.5 AND k.volume>0 GROUP BY k.event HAVING COUNT(*)>=?)", (ser, MIN_LADDER)).fetchone()[0]
        elig_fresh = c.execute("SELECT COUNT(*) FROM (SELECT k.event FROM kmarket k JOIN gm g ON g.event=k.event WHERE g.deferred=0 AND k.series=? AND k.strike=0.5 AND k.volume>0 GROUP BY k.event HAVING COUNT(*)>=?)", (ser, MIN_LADDER)).fetchone()[0]
        res["series"][ser] = dict(eligible_games_5plus_rungs=elig, eligible_fresh_games=elig_fresh, matched_games=ng, deferred_goal_overlap_games=nd, fresh_games=ng - nd, rungs_1plus_2plus=sum(per),
                                  rungs_per_game_median=st.median(per), rungs_1plus_per_game_median=st.median(per1))
    json.dump(res, open(out, "w"), indent=1)
    print(res)


def fetch(series, minutes):
    c = conn()
    cschema(c)
    t_end = time.time() + 60 * minutes
    starts = {r[0]: r[1] for r in c.execute("SELECT event,start_ts FROM gm WHERE series=?", (series,))}
    deferred = {r[0] for r in c.execute("SELECT event FROM gm WHERE series=? AND deferred=1", (series,))}
    byg = defaultdict(list)
    n1 = {r[0]: r[1] for r in c.execute("SELECT event,COUNT(*) FROM kmarket WHERE series=? AND strike=0.5 AND volume>0 GROUP BY event", (series,))}
    for tk, ev in c.execute("SELECT ticker,event FROM kmarket WHERE series=? AND strike IN (0.5,1.5) AND volume>0", (series,)):
        if ev in starts and n1.get(ev, 0) >= MIN_LADDER:
            byg[ev].append(tk)
    total, games = 0, 0
    for ev in order_games(list(byg), deferred):
        if total >= MIN_TRADES:
            print("stopping rule: candidate trades", total, "games", games, flush=True)
            return
        if time.time() > t_end:
            print("time box reached: candidate trades", total, "games", games, flush=True)
            return
        for tk in byg[ev]:
            if c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone():
                continue
            cs = None
            for a in range(8):
                try:
                    cs = api._get(f"/historical/markets/{tk}/candlesticks", {"start_ts": starts[ev] - 3600, "end_ts": starts[ev], "period_interval": 1}, retries=1).get("candlesticks", [])
                    break
                except Exception as e:  # noqa: BLE001
                    if "404" in str(e) and a >= 1:
                        break
                    time.sleep(2 + 4 * a)
            time.sleep(0.6)
            if cs is None:
                break  # one market failed after its retries: game dropped, no more requests on its rungs
            for x in cs:
                c.execute("INSERT OR IGNORE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
            c.execute("INSERT OR IGNORE INTO cdone VALUES(?,?)", (tk, len(cs)))
            c.commit()
        if all(c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone() for tk in byg[ev]):
            games += 1
            nl = ch = 0
            for tk in byg[ev]:
                q = look_quote(c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=?", (tk,)).fetchall(), starts[ev])
                if q is None:
                    continue
                if tk.endswith("-1"):
                    nl += 1
                ch += cheap_side(*q) is not None
            total += min(2, ch) if nl >= MIN_LADDER else 0
            print(series, "game", games, ev, "candidate trades", total, flush=True)
        else:
            print("dropped after retries:", ev, flush=True)
    print("order exhausted", total, games, flush=True)


def fmt(d):
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()}


def entries(series):
    c = conn()
    done = {r[0] for r in c.execute("SELECT ticker FROM cdone")}
    starts = {r[0]: (r[1], r[2]) for r in c.execute("SELECT event,start_ts,deferred FROM gm WHERE series=?", (series,))}
    byg = defaultdict(list)
    n1 = {r[0]: r[1] for r in c.execute("SELECT event,COUNT(*) FROM kmarket WHERE series=? AND strike=0.5 AND volume>0 GROUP BY event", (series,))}
    for tk, ev, k, res in c.execute("SELECT ticker,event,strike,result FROM kmarket WHERE series=? AND strike IN (0.5,1.5) AND volume>0", (series,)):
        if ev in starts and n1.get(ev, 0) >= MIN_LADDER:
            byg[ev].append((tk, k, res))
    games = []
    for ev in order_games(list(byg), {e for e, v in starts.items() if v[1]}):
        rows = byg[ev]
        if any(t not in done for t, _, _ in rows):
            continue
        stt = starts[ev][0]
        ladder, cheap = [], []
        for tk, k, res in rows:
            q = look_quote(c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=?", (tk,)).fetchall(), stt)
            if q is None or res not in ("yes", "no"):
                continue
            bid, ask = q
            if k == 0.5:
                ladder.append((ask, res == "yes"))
            sd = cheap_side(bid, ask)
            if sd:
                cheap.append(dict(ticker=tk, game=ev, date=ev.split("-")[1][:7], side=sd[0], ask=sd[1], win=(res == "yes") == (sd[0] == "yes"), start=stt))
        if len(ladder) < MIN_LADDER:
            continue
        games.append(dict(event=ev, start=stt, lsum=sum(a for a, _ in ladder), scorers=sum(1 for _, y in ladder if y), nl=len(ladder), cheap=cheap,
                          overlap=bool(starts[ev][1])))
    return games


def score():
    out = {}
    for ser in SERIES:
        G = entries(ser)
        if not G:
            continue
        E = e_fit(G)
        med = st.median([g["start"] for g in G])
        for g in G:
            g["ur"] = under_round(g["lsum"], E)
            for t in g["cheap"]:
                t["half"] = "H1" if g["start"] < med else "H2"
                t["ur"] = g["ur"]
        pool = [t for g in G for t in pick_two(g["cheap"])]
        allc = [t for g in G for t in g["cheap"]]
        d = dict(games=len(G), overlap_games=sum(g["overlap"] for g in G), E_fit=E, mean_sum_ask=sum(g["lsum"] for g in G) / len(G),
                 mean_scorers=sum(g["scorers"] for g in G) / len(G), under_round_games=sum(g["ur"] for g in G), cheap_entries=len(allc),
                 side_counts={s: sum(1 for t in allc if t["side"] == s) for s in ("yes", "no")})
        for name, T in (("pool_cap2", pool), ("under_round_cap2", [t for t in pool if t["ur"]]), ("over_round_cap2", [t for t in pool if not t["ur"]])):
            b = dict(game=clustered(T, "game"), date=clustered(T, "date"), x12=clustered(T, "game", 1.2))
            for h in ("H1", "H2"):
                b[h] = clustered([t for t in T if t["half"] == h], "game")
            b["verdict"] = verdict(b["game"]["n"], [b["H1"]["mean_c"], b["H2"]["mean_c"]], b["game"]["lo95_c"], b["game"]["pf"])
            d[name] = b
        d["uncapped_information"] = clustered(allc, "game")
        d["by_strike_cap2_information"] = {k: clustered([t for t in pool if t["ticker"].endswith("-" + k)], "game") for k in ("1", "2")}
        out[ser] = d
    json.dump(out, open(ROOT / "workers" / "NHLAST1_RESULT.json", "w"), indent=1, default=str)
    for s, d in out.items():
        print("==", s, {k: v for k, v in d.items() if not isinstance(v, dict)})
        for k, v in d.items():
            if isinstance(v, dict) and "game" in v:
                print(k, {a: (fmt(b) if isinstance(b, dict) else b) for a, b in v.items()})
        print("uncapped", fmt(d["uncapped_information"]), {k: fmt(v) for k, v in d["by_strike_cap2_information"].items()})


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "census":
        census(sys.argv[2])
    elif cmd == "candles":
        fetch(sys.argv[2], float(sys.argv[3]))
    elif cmd == "score":
        score()
