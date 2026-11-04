"""NHLAST1 Amendment 3: frozen post-cut read of KXNHLAST 1+ rungs (assists), under-round filter E = 4.21 frozen. Research only.
  python -m scalper.nhlast1_frozen list | espn | census OUT | candles MINUTES | score
Own cache /home/user/.cache/nhlast1/frozen.sqlite (append-only: INSERT OR IGNORE only)."""
from __future__ import annotations
import json, re, sqlite3, sys, time, statistics as st
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from . import api
from .candlefield import quote_close
from .nhlg1 import cheap_side, event_teams, event_date, md5, team_code, jget, ESPN
from .nhlall1 import look_quote, pick_two, clustered, verdict, MIN_TRADES
from .nhlast1 import suffix, game_key, MIN_LADDER, E_FROZEN, fmt

DB = Path("/home/user/.cache/nhlast1/frozen.sqlite")
ROOT = Path(__file__).resolve().parents[2]
CUT = "2026-10-03T16:00:00Z"
END = "2026-11-03T00:00:00Z"


def conn():
    c = sqlite3.connect(DB, timeout=120)
    c.executescript("""CREATE TABLE IF NOT EXISTS km(ticker TEXT PRIMARY KEY, event TEXT, strike REAL, close_time TEXT, volume REAL, result TEXT);
CREATE TABLE IF NOT EXISTS espn(id TEXT PRIMARY KEY, start_ts INTEGER, home TEXT, away TEXT);
CREATE TABLE IF NOT EXISTS gm(event TEXT PRIMARY KEY, start_ts INTEGER);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, PRIMARY KEY(ticker,end_ts));
CREATE TABLE IF NOT EXISTS cdone(ticker TEXT PRIMARY KEY, n INTEGER);
CREATE TABLE IF NOT EXISTS gdone(day TEXT PRIMARY KEY);""")
    return c


def in_frozen(ct, ex):
    return CUT <= ct < END and ex >= CUT


def cmd_list():
    c = conn()
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cur, n = None, 0
        while True:
            q = dict(series_ticker="KXNHLAST", limit=1000, **extra)
            if cur:
                q["cursor"] = cur
            d = api._get(path, q)
            time.sleep(1.0)
            for m in d.get("markets", []):
                ct = m.get("close_time") or ""
                ex = m.get("expected_expiration_time") or ct
                if not in_frozen(ct, ex) or float(m.get("volume_fp") or 0) <= 0 or m.get("floor_strike") != 0.5:
                    continue
                c.execute("INSERT OR IGNORE INTO km VALUES(?,?,?,?,?,?)", (m["ticker"], m["event_ticker"], 0.5, ct, float(m["volume_fp"]), m.get("result")))
                n += 1
            cur = d.get("cursor")
            if not cur:
                break
        c.commit()
        print(path, "kept", n, flush=True)


def cmd_espn():
    """Scoreboard only (start times), Oct 3 to Nov 3 2026. No box scores, no scores read."""
    c = conn()
    d0, d1 = datetime(2026, 10, 3), datetime(2026, 11, 3)
    while d0 <= d1:
        k = f"{d0:%Y%m%d}"
        if not c.execute("SELECT 1 FROM gdone WHERE day=?", (k,)).fetchone():
            sb = jget(f"{ESPN}/scoreboard?dates={k}&limit=100")
            time.sleep(1.0)
            for ev in sb.get("events", []):
                ts = int(datetime.strptime(ev["date"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc).timestamp())
                comp = (ev.get("competitions") or [{}])[0].get("competitors", [])
                h = next((x for x in comp if x.get("homeAway") == "home"), None)
                a = next((x for x in comp if x.get("homeAway") == "away"), None)
                if h and a:
                    c.execute("INSERT OR IGNORE INTO espn VALUES(?,?,?,?)", (ev["id"], ts, h["team"]["abbreviation"], a["team"]["abbreviation"]))
            c.execute("INSERT OR IGNORE INTO gdone VALUES(?)", (k,))
            c.commit()
        d0 += timedelta(days=1)
    print("espn games", c.execute("SELECT COUNT(*) FROM espn").fetchone()[0])


def build():
    c = conn()
    et = timezone(timedelta(hours=-5))
    pair = defaultdict(list)
    for gid, ts, h, a in c.execute("SELECT id,start_ts,home,away FROM espn"):
        pair[frozenset((team_code(h), team_code(a)))].append((gid, ts))
    n1 = {r[0]: r[1] for r in c.execute("SELECT event,COUNT(*) FROM km GROUP BY event")}
    un = 0
    for ev, n in n1.items():
        if n < MIN_LADDER:
            continue
        tm, d = event_teams(ev), event_date(ev)
        best = None
        for gid, ts in pair.get(frozenset(tm), []) if tm else []:
            gd = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(et).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
            diff = abs((gd - d).days) if d else 9
            if diff <= 1 and (best is None or diff < best[0]):
                best = (diff, ts)
        if best is None:
            un += 1
        else:
            c.execute("INSERT OR IGNORE INTO gm VALUES(?,?)", (ev, best[1]))
    c.commit()
    return un


def census(out):
    un = build()
    c = conn()
    allev = {r[0]: r[1] for r in c.execute("SELECT event,COUNT(*) FROM km GROUP BY event")}
    res = dict(events_listed=len(allev), events_5plus=sum(1 for v in allev.values() if v >= MIN_LADDER), unmatched_5plus=un,
               matched_5plus=c.execute("SELECT COUNT(*) FROM gm").fetchone()[0], rungs_5plus_events=sum(v for v in allev.values() if v >= MIN_LADDER))
    json.dump(res, open(out, "w"), indent=1)
    print(res)


def cmd_candles(minutes):
    c = conn()
    t_end = time.time() + 60 * minutes
    starts = {r[0]: r[1] for r in c.execute("SELECT event,start_ts FROM gm")}
    byg = defaultdict(list)
    for tk, ev in c.execute("SELECT ticker,event FROM km"):
        if ev in starts:
            byg[ev].append(tk)
    games = 0
    for ev in sorted(byg, key=game_key):
        if time.time() > t_end:
            print("time box reached; games", games, flush=True)
            return
        for tk in byg[ev]:
            if c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone():
                continue
            cs, last = None, ""
            for a in range(8):
                try:
                    path = f"/historical/markets/{tk}/candlesticks" if a % 2 == 0 or "404" not in last else f"/series/KXNHLAST/markets/{tk}/candlesticks"
                    cs = api._get(path, {"start_ts": starts[ev] - 3600, "end_ts": starts[ev], "period_interval": 1}, retries=1).get("candlesticks", [])
                    break
                except Exception as e:  # noqa: BLE001
                    last = str(e)
                    time.sleep(2 + 4 * a)
            time.sleep(0.6)
            if cs is None:
                print("fail", tk, last[:80], flush=True)
                break
            for x in cs:
                c.execute("INSERT OR IGNORE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
            c.execute("INSERT OR IGNORE INTO cdone VALUES(?,?)", (tk, len(cs)))
            c.commit()
        games += 1
        if games % 5 == 0:
            print("game", games, "/", len(byg), flush=True)
    print("order done; games", games, flush=True)


def score():
    c = conn()
    done = {r[0] for r in c.execute("SELECT ticker FROM cdone")}
    starts = {r[0]: r[1] for r in c.execute("SELECT event,start_ts FROM gm")}
    byg = defaultdict(list)
    for tk, ev, res in c.execute("SELECT ticker,event,result FROM km"):
        if ev in starts:
            byg[ev].append((tk, res))
    G, drop = [], defaultdict(int)
    for ev in sorted(byg, key=game_key):
        rows = byg[ev]
        if any(t not in done for t, _ in rows):
            drop["not fully fetched"] += 1
            continue
        stt = starts[ev]
        ladder, cheap = [], []
        for tk, res in rows:
            q = look_quote(c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=?", (tk,)).fetchall(), stt)
            if q is None or res not in ("yes", "no"):
                continue
            bid, ask = q
            ladder.append(ask)
            sd = cheap_side(bid, ask)
            if sd:
                cheap.append(dict(ticker=tk, game=ev, date=ev.split("-")[1][:7], side=sd[0], ask=sd[1], win=(res == "yes") == (sd[0] == "yes"), start=stt))
        if len(ladder) < MIN_LADDER:
            drop["fewer than 5 valid quotes or settled results"] += 1
            continue
        G.append(dict(event=ev, start=stt, lsum=sum(ladder), nl=len(ladder), cheap=cheap, ur=sum(ladder) < E_FROZEN))
    med = st.median([g["start"] for g in G]) if G else 0
    out = dict(games_usable=len(G), dropped=dict(drop), under_round_games=sum(g["ur"] for g in G), mean_sum_ask=(sum(g["lsum"] for g in G) / len(G) if G else None))
    pool = [t for g in G for t in pick_two(g["cheap"])]
    ur = {g["event"] for g in G if g["ur"]}
    for g in G:
        for t in g["cheap"]:
            t["half"] = "H1" if g["start"] < med else "H2"
    for nm, T in (("filter_arm", [t for t in pool if t["game"] in ur]), ("pooled_arm", pool), ("over_round", [t for t in pool if t["game"] not in ur])):
        b = dict(game=clustered(T, "game"), date=clustered(T, "date"), x12=clustered(T, "game", 1.2))
        for h in ("H1", "H2"):
            b[h] = clustered([t for t in T if t["half"] == h], "game")
        b["verdict"] = verdict(b["game"]["n"], [b["H1"]["mean_c"], b["H2"]["mean_c"]], b["game"]["lo95_c"], b["game"]["pf"])
        out[nm] = b
    json.dump(out, open(ROOT / "workers" / "NHLAST1_RESULT3.json", "w"), indent=1, default=str)
    print({k: v for k, v in out.items() if not isinstance(v, dict) or "game" not in v}, drop)
    for k in ("filter_arm", "pooled_arm", "over_round"):
        print(k, {a: (fmt(b) if isinstance(b, dict) else b) for a, b in out[k].items()})


if __name__ == "__main__":
    {"list": cmd_list, "espn": cmd_espn, "census": lambda: census(sys.argv[2]), "candles": lambda: cmd_candles(float(sys.argv[2])), "score": score}[sys.argv[1]]()
