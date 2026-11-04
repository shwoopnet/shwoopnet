"""NHLALL1 Amendment 3: ONE frozen read of the post-cut KXNHLGOAL events. Registration: workers/NHLALL1_AMENDMENT3.md.
  python -m scalper.nhlfrozen espn | candles HOURS | score        (cache /home/user/.cache/nhlall1/frozen.sqlite, append only)"""
from __future__ import annotations
import json, sqlite3, sys, time, statistics as st, urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from . import api
from .candlefield import quote_close, candle_volume
from .nhlg1 import cheap_side, valid, event_teams, event_date, md5, team_code, ESPN
from .nhlall1 import look_quote, pick_two, tercile_of, clustered, verdict, fmt, MAXPER

DB = Path("/home/user/.cache/nhlall1/frozen.sqlite")
ROOT = Path(__file__).resolve().parents[2]
EVENTS = ROOT / "workers" / "NHLALL1_FROZEN_EVENTS.json"
OUT = ROOT / "workers" / "NHLALL1_RESULT3.json"
CUTS, ROUND_THR = (2.75, 3.66), 3.6085
UA = "shwoopnet-research-nhlall1/1.0 (personal research, 1 req/s)"
SCHEMA = """
CREATE TABLE IF NOT EXISTS game(event TEXT PRIMARY KEY, start_ts INTEGER, espn TEXT);
CREATE TABLE IF NOT EXISTS day(d TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS espn(id TEXT PRIMARY KEY, start_ts INTEGER, home TEXT, away TEXT);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, vol REAL, oi REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS cdone(ticker TEXT PRIMARY KEY, n INTEGER);
CREATE TABLE IF NOT EXISTS gdone(event TEXT PRIMARY KEY, how TEXT);
"""


def conn():
    c = sqlite3.connect(DB, timeout=120)
    c.executescript(SCHEMA)
    return c


def jget(url, tries=6):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=25) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{url}: {last}")


def cmd_espn():
    c = conn()
    d0, d1 = datetime(2026, 10, 3), datetime(2026, 11, 3)
    have = {r[0] for r in c.execute("SELECT d FROM day")}
    while d0 <= d1:
        k = f"{d0:%Y%m%d}"
        if k not in have:
            sb = jget(f"{ESPN}/scoreboard?dates={k}&limit=100")
            time.sleep(1.0)
            for ev in sb.get("events", []):
                ts = int(datetime.strptime(ev["date"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc).timestamp())
                comp = (ev.get("competitions") or [{}])[0].get("competitors", [])
                h = next((x for x in comp if x.get("homeAway") == "home"), None)
                a = next((x for x in comp if x.get("homeAway") == "away"), None)
                if h and a:
                    c.execute("INSERT OR IGNORE INTO espn VALUES(?,?,?,?)", (ev["id"], ts, team_code(h["team"]["abbreviation"]), team_code(a["team"]["abbreviation"])))
            c.execute("INSERT INTO day VALUES(?)", (k,))
            c.commit()
        d0 += timedelta(days=1)
    et = timezone(timedelta(hours=-5))
    pair = defaultdict(list)
    for gid, ts, h, a in c.execute("SELECT id,start_ts,home,away FROM espn"):
        pair[frozenset((h, a))].append((ts, gid))
    ok = un = 0
    for ev in json.load(open(EVENTS)):
        tm, d = event_teams(ev), event_date(ev)
        best = None
        for ts, gid in pair.get(frozenset(tm), []) if tm else []:
            gd = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(et).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
            diff = abs((gd - d).days) if d else 9
            if diff <= 1 and (best is None or diff < best[0]):
                best = (diff, ts, gid)
        if best:
            c.execute("INSERT OR IGNORE INTO game VALUES(?,?,?)", (ev, best[1], best[2]))
            ok += 1
        else:
            un += 1
    c.commit()
    print("espn games", c.execute("SELECT COUNT(*) FROM espn").fetchone()[0], "events matched", ok, "unmatched", un, flush=True)


def store(c, tk, cs):
    for x in cs:
        c.execute("INSERT OR IGNORE INTO candle VALUES(?,?,?,?,?,?)",
                  (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask")), candle_volume(x), api.f(x.get("open_interest_fp", x.get("open_interest")))))
    c.execute("INSERT OR IGNORE INTO cdone VALUES(?,?)", (tk, len(cs)))


def cmd_candles(hours):
    c = conn()
    t_end = time.time() + 3600 * hours
    tks = json.load(open(EVENTS))
    start = {r[0]: r[1] for r in c.execute("SELECT event,start_ts FROM game")}
    order = sorted(tks, key=md5)
    done = games = 0
    for ev in order:
        if time.time() > t_end:
            print("time box reached", flush=True)
            return
        if ev not in start or c.execute("SELECT 1 FROM gdone WHERE event=?", (ev,)).fetchone():
            continue
        s = start[ev]
        need = [t for t in tks[ev] if not c.execute("SELECT 1 FROM cdone WHERE ticker=?", (t,)).fetchone()]
        got = None
        for a in range(8):  # batch: one request for the game's rungs (at most 100 tickers)
            try:
                got = {}
                for i in range(0, len(need), 100):
                    got.update(api.batch_candlesticks(need[i:i + 100], s - 3600, s))
                    time.sleep(0.6)
                break
            except Exception:  # noqa: BLE001
                got = None
                time.sleep(2 + 4 * a)
        how = "batch"
        if got is None:  # one fallback: per-market series endpoint
            got, how = {}, "series"
            for t in need:
                cs = None
                for a in range(8):
                    try:
                        cs = api.candlesticks("KXNHLGOAL", t, s - 3600, s)
                        break
                    except Exception:  # noqa: BLE001
                        time.sleep(2 + 4 * a)
                time.sleep(0.6)
                if cs is None:
                    got = None
                    break
                got[t] = cs
        if got is None:
            c.execute("INSERT OR IGNORE INTO gdone VALUES(?,?)", (ev, "FAILED"))
            c.commit()
            print("dropped after retries", ev, flush=True)
            continue
        for t in need:
            store(c, t, got.get(t, []))
        c.execute("INSERT OR IGNORE INTO gdone VALUES(?,?)", (ev, how))
        c.commit()
        games += 1
        print("game", games, ev, how, "rungs", len(need), "with candles", sum(1 for t in need if got.get(t)), flush=True)
    print("all events done", games, flush=True)


def results():
    r = {}
    cursor = None
    while True:
        q = dict(series_ticker="KXNHLGOAL", status="settled", min_close_ts=int(datetime(2026, 10, 3, 16, tzinfo=timezone.utc).timestamp()), max_close_ts=int(datetime(2026, 11, 3, tzinfo=timezone.utc).timestamp()), limit=1000)
        if cursor:
            q["cursor"] = cursor
        d = api._get("/markets", q)
        time.sleep(1.0)
        for m in d.get("markets", []):
            if m.get("result") in ("yes", "no"):
                r[m["ticker"]] = m["result"]
        cursor = d.get("cursor")
        if not cursor:
            return r


def score():
    if OUT.exists():
        sys.exit("refusing a second read: " + str(OUT))
    c = conn()
    tks = json.load(open(EVENTS))
    res = results()
    start = {r[0]: r[1] for r in c.execute("SELECT event,start_ts FROM game")}
    drops = defaultdict(int)
    drops["events"] = len(tks)
    G = []
    for ev in sorted(tks, key=md5):
        if ev not in start:
            drops["no_espn_match"] += 1
            continue
        how = c.execute("SELECT how FROM gdone WHERE event=?", (ev,)).fetchone()
        if not how or how[0] == "FAILED":
            drops["fetch_failed_or_missing"] += 1
            continue
        ladder, cheap, nq = [], [], 0
        for tk in tks[ev]:
            cs = c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=?", (tk,)).fetchall()
            q = look_quote(cs, start[ev])
            if q is None:
                continue
            nq += 1
            if tk not in res:
                drops["rung_without_result"] += 1
                continue
            bid, ask = q
            ladder.append((ask, res[tk] == "yes"))
            sd = cheap_side(bid, ask)
            if sd and sd[0] == "yes":
                cheap.append(dict(ticker=tk, game=ev, date=ev[10:17], side="yes", ask=sd[1], win=res[tk] == "yes", start=start[ev]))
        if not any(c.execute("SELECT 1 FROM candle WHERE ticker=?", (tk,)).fetchone() for tk in tks[ev]):
            drops["no_candle_at_all"] += 1
        elif len(ladder) < 8:
            drops["under_8_valid_quotes"] += 1
        if len(ladder) < 8:
            continue
        G.append(dict(event=ev, start=start[ev], lsum=sum(a for a, _ in ladder), scorers=sum(1 for _, y in ladder if y), nl=len(ladder), cheap=cheap))
    out = dict(drops=dict(drops), usable_games=len(G))
    if G:
        med = st.median([g["start"] for g in G])
        for g in G:
            g["tc"] = tercile_of(g["lsum"], CUTS)
            for t in g["cheap"]:
                t["half"] = "H1" if g["start"] < med else "H2"
        pool = [t for g in G for t in pick_two(g["cheap"])]
        arms = {"A_pooled": pool, "B_lowest_tercile": [t for g in G for t in pick_two(g["cheap"]) if g["tc"] == 0],
                "C_nhlround1": [t for g in G if g["lsum"] <= ROUND_THR for t in pick_two(g["cheap"])]}
        for nm, T in arms.items():
            b = dict(game=clustered(T, "game"), date=clustered(T, "date"), x12=clustered(T, "game", 1.2))
            for h in ("H1", "H2"):
                b[h] = clustered([t for t in T if t["half"] == h], "game")
            b["verdict"] = verdict(b["game"]["n"], [b["H1"]["mean_c"], b["H2"]["mean_c"]], b["game"]["lo95_c"], b["game"]["pf"])
            b["games"] = len({t["game"] for t in T})
            out[nm] = b
        allc = [t for g in G for t in g["cheap"]]
        out["uncapped_all_cheap"] = clustered(allc, "game")
        out["by_ask_uncapped"] = {nm: clustered([t for t in allc if lo <= t["ask"] < hi], "game") for lo, hi, nm in ((0.03, 0.08, "3-8c"), (0.08, 0.15, "8-15c"), (0.15, 0.30001, "15-30c"))}
        out["by_tercile_capped"] = {i: clustered([t for t in pool if tercile_of(next(g["lsum"] for g in G if g["event"] == t["game"]), CUTS) == i], "game") for i in range(3)}
        out["ladder"] = dict(mean_sum_ask=sum(g["lsum"] for g in G) / len(G), mean_scorers=sum(g["scorers"] for g in G) / len(G),
                             games_sum_le_round=sum(1 for g in G if g["lsum"] <= ROUND_THR), tercile_games={i: sum(1 for g in G if g["tc"] == i) for i in range(3)})
    # field availability before puck drop (counts only)
    tot = vol = oi = 0
    for ev in tks:
        if ev not in start:
            continue
        for r in c.execute("SELECT c.vol,c.oi FROM candle c WHERE c.ticker IN (%s) AND c.end_ts<=?" % ",".join("?" * len(tks[ev])), (*tks[ev], start[ev] - 120)):
            tot += 1
            vol += r[0] is not None
            oi += r[1] is not None
    out["candle_fields_before_puck_drop"] = dict(candles=tot, with_volume=vol, with_open_interest=oi)
    json.dump(out, open(OUT, "w"), indent=1, default=str)
    for k, v in out.items():
        print(k, v if not isinstance(v, dict) else {a: (fmt(b) if isinstance(b, dict) else b) for a, b in v.items()})


if __name__ == "__main__":
    {"espn": cmd_espn, "candles": lambda: cmd_candles(float(sys.argv[2])), "score": score}[sys.argv[1]]()
