"""NHLALL1: unconditional cheap-side pool on KXNHLGOAL 1+ goal rungs, plus a ladder-sum filter. Research only.
Registration: workers/NHLALL1_REGISTRATION.md. Reuses nhlg1.py's pure helpers and its ESPN game table (game start times) and its
Kalshi listing (kmarket). Results are NOT copied into this module's database; they are read from nhlg1.sqlite at score time only.
  python -m scalper.nhlall1 census | build | candles MINUTES [STRIDE OFFSET] | score
"""
from __future__ import annotations
import json, sqlite3, sys, time, math, statistics as st
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from . import api
from .candlefield import quote_close
from .nhlg1 import (fee, net, cheap_side, valid, cluster_stats, profit_factor, event_teams, event_date, md5, sha, team_code,
                    DB as SRC_DB, C)

DB = Path("/home/user/.cache/nhlall1/nhlall1.sqlite")
ROOT = Path(__file__).resolve().parents[2]
LEAD, MAXPER, MIN_TRADES = 120, 2, 150
NHLG1_FETCHED_NOTE = "any event with at least one candle in nhlg1.sqlite cdone"

SCHEMA = """
CREATE TABLE IF NOT EXISTS gm(event TEXT PRIMARY KEY, gid TEXT, start_ts INTEGER, md5 TEXT, excluded INTEGER);
CREATE TABLE IF NOT EXISTS rung(ticker TEXT PRIMARY KEY, event TEXT, volume REAL);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS cdone(ticker TEXT PRIMARY KEY, n INTEGER);
"""


def conn():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=120)
    c.executescript(SCHEMA)
    return c


# ----------------------------------------------------------------------------- pure functions (tested)

def look_quote(candles, start_ts: int, lead: int = LEAD):
    """Last valid two sided candle ending at or before start - lead. candles: iterable of (end_ts, bid, ask)."""
    ok = [r for r in candles if r[0] <= start_ts - lead and valid(r[1], r[2])]
    if not ok:
        return None
    ok.sort()
    return ok[-1][1], ok[-1][2]


def pick_two(rows):
    """Two per game by sha1 of the ticker (no selection on price)."""
    return sorted(rows, key=lambda r: sha(r["ticker"]))[:MAXPER]


def terciles(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 3], s[(2 * n) // 3]


def tercile_of(x, cuts):
    return 0 if x < cuts[0] else (1 if x < cuts[1] else 2)


def clustered(trades, key, mult=1.0):
    by = defaultdict(list)
    for t in trades:
        by[t[key]].append(net(t["win"], t["ask"], mult))
    n, m, se, z = cluster_stats(by)
    nets = [x for L in by.values() for x in L]
    return dict(n=n, clusters=len(by), mean_c=100 * m, se_c=100 * se, z=z, lo95_c=100 * (m - 1.96 * se) if se == se else float("nan"),
                pf=profit_factor(nets), win=(sum(1 for t in trades if t["win"]) / n if n else float("nan")),
                price=(sum(t["ask"] for t in trades) / n if n else float("nan")))


def verdict(n, half_means, lo95, pf):
    if n < MIN_TRADES:
        return "NOT_ENOUGH_DATA"
    if all(h > 0 for h in half_means) and lo95 > 0 and pf >= 1.5:
        return "LEAD"
    return "FALSIFIED"


# ----------------------------------------------------------------------------- build / census

def build():
    s = sqlite3.connect(SRC_DB, timeout=120)
    c = conn()
    et = timezone(timedelta(hours=-5))
    games, pair = {}, defaultdict(list)
    for gid, stt, h, a in s.execute("SELECT id,start_ts,home,away FROM game"):
        games[gid] = dict(st=stt, h=team_code(h), a=team_code(a))
        pair[frozenset((team_code(h), team_code(a)))].append(gid)
    ev_fetched = set()
    ev_of = {}
    for tk, ev in s.execute("SELECT ticker,event FROM kmarket"):
        ev_of[tk] = ev
    for (tk,) in s.execute("SELECT ticker FROM cdone"):
        ev_fetched.add(ev_of[tk])
    ev_game, unmatched, rungs = {}, set(), 0
    for tk, ev, strike, vol in list(s.execute("SELECT ticker,event,strike,volume FROM kmarket")):  # result is NOT selected
        if strike != 0.5 or not vol or vol <= 0:
            continue
        if ev not in ev_game and ev not in unmatched:
            tm, d = event_teams(ev), event_date(ev)
            best = None
            for gid in pair.get(frozenset(tm), []) if tm else []:
                gd = datetime.fromtimestamp(games[gid]["st"], tz=timezone.utc).astimezone(et).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
                diff = abs((gd - d).days) if d else 9
                if diff <= 1 and (best is None or diff < best[0]):
                    best = (diff, gid)
            if best is None:
                unmatched.add(ev)
            else:
                ev_game[ev] = best[1]
        if ev in ev_game:
            c.execute("INSERT OR IGNORE INTO rung VALUES(?,?,?)", (tk, ev, vol))
            rungs += 1
    for ev, gid in ev_game.items():
        c.execute("INSERT OR REPLACE INTO gm VALUES(?,?,?,?,?)", (ev, gid, games[gid]["st"], md5(ev), 1 if ev in ev_fetched else 0))
    c.commit()
    return len(ev_game), len(unmatched), rungs, len(ev_fetched)


def census(out):
    g, un, rungs, exf = build()
    c = conn()
    tot = c.execute("SELECT COUNT(*) FROM gm").fetchone()[0]
    avail = c.execute("SELECT COUNT(*) FROM gm WHERE excluded=0").fetchone()[0]
    per = [r[0] for r in c.execute("SELECT COUNT(*) FROM rung r JOIN gm g ON g.event=r.event WHERE g.excluded=0 GROUP BY r.event")]
    ex_events = sorted(r[0] for r in c.execute("SELECT event FROM gm WHERE excluded=1"))
    res = dict(matched_games=tot, unmatched_events=un, one_plus_rungs_with_volume_matched=rungs, nhlg1_fetched_events_excluded=len(ex_events),
               available_games=avail, rungs_per_game_median=st.median(per), rungs_per_game_mean=sum(per) / len(per), rungs_available=sum(per),
               excluded_events=ex_events)
    json.dump(res, open(out, "w"), indent=1)
    print({k: v for k, v in res.items() if k != "excluded_events"})


# ----------------------------------------------------------------------------- candles

def cmd_candles(minutes, stride=1, offset=0):
    c = conn()
    t_end = time.time() + 60 * minutes
    byg = defaultdict(list)
    for tk, ev in c.execute("SELECT r.ticker,r.event FROM rung r JOIN gm g ON g.event=r.event WHERE g.excluded=0"):
        byg[ev].append(tk)
    starts = {r[0]: r[1] for r in c.execute("SELECT event,start_ts FROM gm")}
    order = sorted(byg, key=md5)
    print("games", len(order), "markets", sum(len(v) for v in byg.values()), flush=True)
    ok = fail = 0
    for pas in range(6):
        pending = [g for g in order if any(not c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone() for tk in byg[g])]
        # stop at the first incomplete md5 position boundary: games are taken strictly in md5 order
        print("pass", pas, "incomplete games", len(pending), flush=True)
        if not pending:
            break
        for gi, ev in enumerate(pending):
            if gi % stride != offset:
                continue
            if time.time() > t_end:
                print("time box reached", flush=True)
                c.commit()
                return
            stt = starts[ev]
            for tk in byg[ev]:
                if c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone():
                    continue
                cs = None
                for a in range(4):
                    try:
                        cs = api._get(f"/historical/markets/{tk}/candlesticks", {"start_ts": stt - 3600, "end_ts": stt, "period_interval": 1}, retries=1).get("candlesticks", [])
                        break
                    except Exception:  # noqa: BLE001
                        time.sleep(2 + 3 * a)
                time.sleep(0.5)
                if cs is None:
                    fail += 1
                    continue
                ok += 1
                for x in cs:
                    c.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
                c.execute("INSERT OR REPLACE INTO cdone VALUES(?,?)", (tk, len(cs)))
                c.commit()
            if gi % 5 == 0:
                print("pass", pas, "game", gi, "/", len(pending), "ok", ok, "fail", fail, flush=True)
    print("candles done; ok", ok, "fail", fail, flush=True)


# ----------------------------------------------------------------------------- score

def entries(c):
    """Per fully fetched game, in md5 order: ladder sum, scorers, cheap candidates. Results read from the nhlg1 db here only."""
    s = sqlite3.connect(SRC_DB, timeout=120)
    res = {tk: r for tk, r in s.execute("SELECT ticker,result FROM kmarket")}
    done = {r[0] for r in c.execute("SELECT ticker FROM cdone")}
    games = []
    for ev, stt, m5 in c.execute("SELECT event,start_ts,md5 FROM gm WHERE excluded=0 ORDER BY md5"):
        tks = [r[0] for r in c.execute("SELECT ticker FROM rung WHERE event=?", (ev,))]
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
                cheap.append(dict(ticker=tk, game=ev, date=ev[10:17], side=side, ask=a, win=(res[tk] == "yes") == (side == "yes"), start=stt))
        if len(ladder) < 8:
            continue
        games.append(dict(event=ev, start=stt, lsum=sum(a for a, _ in ladder), scorers=sum(1 for _, y in ladder if y), nl=len(ladder), cheap=cheap))
    return games


def fmt(d):
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()}


def score():
    c = conn()
    G = entries(c)
    n_games = len(G)
    third = G[: max(1, n_games // 3)]  # first third in fetch (md5) order: the only source of tercile cuts
    cuts = terciles([g["lsum"] for g in third])
    med = st.median([g["start"] for g in G])
    for g in G:
        g["tc"] = tercile_of(g["lsum"], cuts)
        for t in g["cheap"]:
            t["half"] = "H1" if g["start"] < med else "H2"
            t["tc"] = g["tc"]
    pool = [t for g in G for t in pick_two(g["cheap"])]
    allc = [t for g in G for t in g["cheap"]]
    low = [t for t in pool if t["tc"] == 0]
    out = dict(games=n_games, cheap_entries=len(allc), tercile_cuts_from_first_third=cuts, first_third_games=len(third))

    def block(name, T):
        d = dict(game=clustered(T, "game"), date=clustered(T, "date"), x12=clustered(T, "game", 1.2))
        for h in ("H1", "H2"):
            d[h] = clustered([t for t in T if t["half"] == h], "game")
        d["verdict"] = verdict(d["game"]["n"], [d["H1"]["mean_c"], d["H2"]["mean_c"]], d["game"]["lo95_c"], d["game"]["pf"])
        out[name] = d
    block("pool_cap2", pool)
    block("low_tercile_cap2", low)
    out["all_cheap_uncapped_information"] = clustered(allc, "game")
    out["by_tercile_cap2"] = {i: clustered([t for t in pool if t["tc"] == i], "game") for i in range(3)}
    out["by_tercile_games"] = {i: sum(1 for g in G if g["tc"] == i) for i in range(3)}
    bk = {}
    for lo, hi, nm in ((0.03, 0.08, "3-8c"), (0.08, 0.15, "8-15c"), (0.15, 0.30001, "15-30c")):
        bk[nm] = clustered([t for t in allc if lo <= t["ask"] < hi], "game")
    out["by_ask_bucket_all_cheap_information"] = bk
    out["ladder"] = dict(mean_sum_ask=sum(g["lsum"] for g in G) / n_games, mean_scorers=sum(g["scorers"] for g in G) / n_games,
                         mean_rungs=sum(g["nl"] for g in G) / n_games)
    out["side_counts"] = {s: sum(1 for t in allc if t["side"] == s) for s in ("yes", "no")}
    json.dump(out, open(ROOT / "workers" / "NHLALL1_RESULT.json", "w"), indent=1, default=str)
    for k, v in out.items():
        print(k, v if not isinstance(v, dict) else {a: (fmt(b) if isinstance(b, dict) else b) for a, b in v.items()})


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "census":
        census(sys.argv[2])
    elif cmd == "build":
        print(build())
    elif cmd == "candles":
        cmd_candles(float(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 1, int(sys.argv[4]) if len(sys.argv) > 4 else 0)
    elif cmd == "score":
        score()


# ----------------------------------------------------------------------------- amendment 2 (continuation block)
OLD = ROOT / "workers" / "NHLALL1_FIRST61.json"
CUTS = (2.75, 3.66)
OLD_TRADES = 122


def next_block_order(c):
    old = set(json.load(open(OLD)))
    return [r[0] for r in c.execute("SELECT event FROM gm WHERE excluded=0 ORDER BY md5") if r[0] not in old]


def candidate_trades(c, ev, stt, tks):
    """Trade count of a fully fetched game from quotes only (no result is read): 0 if fewer than 8 valid ladder quotes, else min(2, cheap rungs)."""
    nl = ch = 0
    for tk in tks:
        q = look_quote(c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=?", (tk,)).fetchall(), stt)
        if q is None:
            continue
        nl += 1
        ch += cheap_side(*q) is not None
    return min(MAXPER, ch) if nl >= 8 else 0


def cmd_block2(minutes):
    """ONE process, strict md5 order over the unfetched pre-cut games; each market retried before the game is dropped; stops at 150 pooled trades."""
    c = conn()
    t_end = time.time() + 60 * minutes
    starts = {r[0]: r[1] for r in c.execute("SELECT event,start_ts FROM gm")}
    byg = defaultdict(list)
    for tk, ev in c.execute("SELECT ticker,event FROM rung"):
        byg[ev].append(tk)
    total, games = OLD_TRADES, 0
    for ev in next_block_order(c):
        if total >= MIN_TRADES:
            print("stopping rule reached: pooled trades", total, "new games", games, flush=True)
            return
        if time.time() > t_end:
            print("time box reached: pooled trades", total, "new games", games, flush=True)
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
                        break  # not on the historical endpoint: no point waiting, the game is dropped below
                    time.sleep(2 + 4 * a)
            time.sleep(0.6)
            if cs is None:
                break  # one market failed after its retries: the game is dropped, no more requests on its other rungs
            for x in cs:
                c.execute("INSERT OR IGNORE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
            c.execute("INSERT OR IGNORE INTO cdone VALUES(?,?)", (tk, len(cs)))
            c.commit()
        if all(c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone() for tk in byg[ev]):
            games += 1
            total += candidate_trades(c, ev, starts[ev], byg[ev])
            print("game", games, ev, "pooled trades", total, flush=True)
        else:
            print("dropped after retries:", ev, flush=True)
    print("order exhausted", total, games, flush=True)


def score2():
    c = conn()
    G = entries(c)
    old = set(json.load(open(OLD)))
    med = st.median([g["start"] for g in G])
    for g in G:
        g["tc"] = tercile_of(g["lsum"], CUTS)
        for t in g["cheap"]:
            t["half"] = "H1" if g["start"] < med else "H2"
            t["tc"] = g["tc"]
    out = {}
    sets = {"combined": G, "new_only": [g for g in G if g["event"] not in old]}
    for nm, S in sets.items():
        pool = [t for g in S for t in pick_two(g["cheap"])]
        low = [t for t in pool if t["tc"] == 0]
        d = dict(games=len(S))
        for rule, T in (("pooled", pool), ("low_tercile", low)):
            b = dict(game=clustered(T, "game"), date=clustered(T, "date"), x12=clustered(T, "game", 1.2))
            for h in ("H1", "H2"):
                b[h] = clustered([t for t in T if t["half"] == h], "game")
            b["verdict"] = verdict(b["game"]["n"], [b["H1"]["mean_c"], b["H2"]["mean_c"]], b["game"]["lo95_c"], b["game"]["pf"])
            d[rule] = b
        d["by_tercile"] = {i: clustered([t for t in pool if t["tc"] == i], "game") for i in range(3)}
        d["tercile_games"] = {i: sum(1 for g in S if g["tc"] == i) for i in range(3)}
        d["uncapped_all_cheap"] = clustered([t for g in S for t in g["cheap"]], "game")
        d["ladder"] = dict(mean_sum_ask=sum(g["lsum"] for g in S) / len(S), mean_scorers=sum(g["scorers"] for g in S) / len(S))
        out[nm] = d
    json.dump(out, open(ROOT / "workers" / "NHLALL1_RESULT2.json", "w"), indent=1, default=str)
    for k, v in out.items():
        print("==", k, v["games"])
        for r in ("pooled", "low_tercile"):
            print(r, {a: (fmt(b) if isinstance(b, dict) else b) for a, b in v[r].items()})
        print("by_tercile", {i: fmt(b) for i, b in v["by_tercile"].items()}, v["tercile_games"])
        print("uncapped", fmt(v["uncapped_all_cheap"]), v["ladder"])


if __name__ == "__main__" and sys.argv[1] in ("block2", "score2"):
    {"block2": lambda: cmd_block2(float(sys.argv[2])), "score2": score2}[sys.argv[1]]()
