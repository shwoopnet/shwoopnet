"""ESPN1: ESPN's public in-play win probability against Kalshi game-winner asks.

Registration: kalshi-scalper/workers/ESPN1_REGISTRATION.md (written and pushed before scoring).
Public, keyless data only. Data goes to data/espn1.sqlite (ignored by git).

  python -m scalper.espn1 fetch     # ESPN game lists, Kalshi markets, matching, ESPN rows, Kalshi candles
  python -m scalper.espn1 lag FILE  # the live lag sample -> D
  python -m scalper.espn1 score D AB|C
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import api, backfill

DB = Path(__file__).resolve().parents[2] / "data" / "espn1.sqlite"
ET = ZoneInfo("America/New_York")
LO = datetime(2026, 8, 30, tzinfo=timezone.utc)
HI = datetime(2026, 10, 29, tzinfo=timezone.utc)
LEAGUES = {  # kalshi series -> (espn path, extra scoreboard params)
    "KXNFLGAME": ("football/nfl", [""]),
    "KXNCAAFGAME": ("football/college-football", ["&groups=80", "&groups=81"]),
    "KXNBAGAME": ("basketball/nba", [""]),
    "KXMLBGAME": ("baseball/mlb", [""]),
}
PAUSE = 0.5

SCHEMA = """
CREATE TABLE IF NOT EXISTS egame(id TEXT, series TEXT, start_ts INTEGER, home_id TEXT, away_id TEXT, teams TEXT, PRIMARY KEY(id, series));
CREATE TABLE IF NOT EXISTS kmarket(ticker TEXT PRIMARY KEY, series TEXT, event TEXT, sub TEXT, close_ts INTEGER, result TEXT);
CREATE TABLE IF NOT EXISTS match(event TEXT PRIMARY KEY, series TEXT, egame TEXT, home_ticker TEXT, away_ticker TEXT);
CREATE TABLE IF NOT EXISTS erow(egame TEXT, seq INTEGER, play TEXT, wall_ts INTEGER, home_p REAL, tie_p REAL, PRIMARY KEY(egame, seq));
CREATE TABLE IF NOT EXISTS edone(egame TEXT PRIMARY KEY, n INTEGER);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, volume REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS kdone(event TEXT PRIMARY KEY, n INTEGER);
"""


def _json(url: str, tries: int = 5):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{url}: {last}")


def _ts(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return None


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower().replace("&", "and").replace("state", "st")).strip()


# ---------------------------------------------------------------- fetch

def fetch_espn_games(db):
    have = {r[0] for r in db.execute("SELECT DISTINCT series FROM egame")}
    for series, (path, extras) in LEAGUES.items():
        if series in have:
            continue
        d = LO - timedelta(days=2)
        n = 0
        while d <= HI:
            for ex in extras:
                sb = _json(f"https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard?dates={d:%Y%m%d}&limit=500{ex}")
                for e in sb.get("events", []):
                    comp = e["competitions"][0]
                    teams = {}
                    hid = aid = None
                    for c in comp["competitors"]:
                        t = c["team"]
                        teams[t["id"]] = [t.get("abbreviation", ""), t.get("location", ""), t.get("name", ""),
                                          t.get("displayName", ""), t.get("shortDisplayName", "")]
                        if c.get("homeAway") == "home":
                            hid = t["id"]
                        else:
                            aid = t["id"]
                    db.execute("INSERT OR REPLACE INTO egame VALUES(?,?,?,?,?,?)",
                               (e["id"], series, _ts(e["date"]), hid, aid, json.dumps(teams)))
                    n += 1
                time.sleep(0.2)
            d += timedelta(days=1)
        db.commit()
        print(f"{series}: {n} ESPN scoreboard rows", flush=True)


def fetch_kalshi_markets(db):
    if db.execute("SELECT COUNT(*) FROM kmarket").fetchone()[0]:
        return
    for series in LEAGUES:
        ms = list(api.settled_markets(series, int(LO.timestamp()), int(HI.timestamp())))
        for m in ms:
            if m.get("result") not in ("yes", "no"):
                continue
            db.execute("INSERT OR REPLACE INTO kmarket VALUES(?,?,?,?,?,?)",
                       (m["ticker"], series, m["event_ticker"], m.get("yes_sub_title") or "", backfill.iso_ts(m.get("close_time")), m["result"]))
        db.commit()
        print(f"{series}: {len(ms)} Kalshi markets", flush=True)


MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def _ticker_date(event: str):
    m = re.match(r"^[A-Z0-9]+-(\d\d)([A-Z]{3})(\d\d)(\d{4})?", event)
    if not m:
        return None, None
    return datetime(2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3))).date(), m.group(4)


def team_score(code: str, sub: str, t: list[str]) -> int:
    abbr, loc, name, disp, short = t
    s = 0
    if code and code.upper() == abbr.upper():
        s += 2
    ns = norm(sub)
    cands = {norm(loc), norm(disp), norm(short), norm(name)}
    if ns and ns in cands:
        s += 2
    elif ns and len(ns.split()) >= 2 and len(ns.split()[-1]) == 1 and ns[:-2] == norm(loc) and norm(name).startswith(ns[-1]):
        s += 2  # "Los Angeles L"
    elif ns and (norm(loc).startswith(ns) or ns.startswith(norm(loc))) and norm(loc):
        s += 1
    return s


def match_games(db):
    db.execute("DELETE FROM match")
    games = defaultdict(list)
    for gid, series, st, hid, aid, teams in db.execute("SELECT * FROM egame"):
        if st is None or hid is None or aid is None:
            continue
        games[(series, datetime.fromtimestamp(st, ET).date())].append((gid, st, hid, aid, json.loads(teams)))
    ev = defaultdict(list)
    for tk, series, event, sub, close, res in db.execute("SELECT * FROM kmarket"):
        ev[(series, event)].append((tk, sub))
    stats = defaultdict(lambda: [0, 0])
    for (series, event), mk in ev.items():
        stats[series][0] += 1
        if len(mk) != 2:
            continue
        day, hhmm = _ticker_date(event)
        if day is None:
            continue
        best = []
        for dd in (-1, 0, 1):
            for gid, st, hid, aid, teams in games.get((series, day + timedelta(days=dd)), []):
                (t1, s1), (t2, s2) = mk
                c1, c2 = t1.rsplit("-", 1)[1], t2.rsplit("-", 1)[1]
                a = team_score(c1, s1, teams[hid]) + team_score(c2, s2, teams[aid])
                b = team_score(c1, s1, teams[aid]) + team_score(c2, s2, teams[hid])
                ok_a = team_score(c1, s1, teams[hid]) > 0 and team_score(c2, s2, teams[aid]) > 0
                ok_b = team_score(c1, s1, teams[aid]) > 0 and team_score(c2, s2, teams[hid]) > 0
                if a > b and ok_a:
                    home, away, sc = t1, t2, a
                elif b > a and ok_b:
                    home, away, sc = t2, t1, b
                else:
                    continue
                pen = abs(dd) * 10
                if hhmm:
                    loc = datetime.fromtimestamp(st, ET)
                    pen += abs((loc.hour * 60 + loc.minute) - (int(hhmm[:2]) * 60 + int(hhmm[2:]))) / 60.0
                best.append((sc - pen, gid, home, away))
        if not best:
            continue
        best.sort(reverse=True)
        if len(best) > 1 and best[1][0] == best[0][0]:
            continue  # ambiguous
        _, gid, home, away = best[0]
        db.execute("INSERT OR REPLACE INTO match VALUES(?,?,?,?,?)", (event, series, gid, home, away))
        stats[series][1] += 1
    # one ESPN game may not serve two Kalshi events
    dup = [r[0] for r in db.execute("SELECT egame FROM match GROUP BY series, egame HAVING COUNT(*) > 1")]
    for g in dup:
        db.execute("DELETE FROM match WHERE egame = ?", (g,))
    db.commit()
    for s, (n, m) in stats.items():
        print(f"{s}: {n} Kalshi events, {m} matched", flush=True)
    print(f"dropped {len(dup)} ESPN games matched twice", flush=True)


def fetch_rows(db):
    done = {r[0] for r in db.execute("SELECT egame FROM edone")}
    todo = [(g, s) for g, s in db.execute("SELECT egame, series FROM match") if g not in done]
    print(f"ESPN summaries to fetch: {len(todo)}", flush=True)
    for i, (gid, series) in enumerate(todo):
        path = LEAGUES[series][0]
        try:
            s = _json(f"https://site.api.espn.com/apis/site/v2/sports/{path}/summary?event={gid}")
        except RuntimeError as e:
            print("skip", gid, e, flush=True)
            continue
        plays = list(s.get("plays") or [])
        for d in (s.get("drives") or {}).get("previous", []) or []:
            plays += d.get("plays", []) or []
        wc = {p["id"]: _ts(p.get("wallclock")) for p in plays if isinstance(p, dict) and "id" in p}
        n = 0
        for k, w in enumerate(s.get("winprobability", []) or []):
            t = wc.get(w.get("playId"))
            if t is None or w.get("homeWinPercentage") is None:
                continue
            db.execute("INSERT OR REPLACE INTO erow VALUES(?,?,?,?,?,?)", (gid, k, w["playId"], t, w["homeWinPercentage"], w.get("tiePercentage") or 0.0))
            n += 1
        db.execute("INSERT OR REPLACE INTO edone VALUES(?,?)", (gid, n))
        if i % 50 == 0:
            db.commit()
            print(f"  {i}/{len(todo)}", flush=True)
        time.sleep(0.25)
    db.commit()


def fetch_candles(db):
    done = {r[0] for r in db.execute("SELECT event FROM kdone")}
    rows = db.execute("""SELECT m.event, m.home_ticker, m.away_ticker, MIN(r.wall_ts), k.close_ts
                         FROM match m JOIN erow r ON r.egame = m.egame JOIN kmarket k ON k.ticker = m.home_ticker
                         GROUP BY m.event""").fetchall()
    todo = [r for r in rows if r[0] not in done]
    print(f"Kalshi events to fetch candles for: {len(todo)}", flush=True)
    for i, (event, h, a, first, close) in enumerate(todo):
        lo = first - 600
        hi = close
        if (hi - lo) / 60 * 2 > 9500:
            lo = hi - int(9500 / 2 * 60)
        try:
            got = api.batch_candlesticks([h, a], lo, hi)
        except RuntimeError as e:
            print("skip", event, e, flush=True)
            continue
        n = 0
        for tk in (h, a):
            for c in got.get(tk, []):
                end = c.get("end_period_ts")
                if end is None:
                    continue
                b = backfill._d(c.get("yes_bid"), "close_dollars")
                k = backfill._d(c.get("yes_ask"), "close_dollars")
                db.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?)", (tk, int(end), b, k, api.f(c.get("volume_fp"))))
                n += 1
        db.execute("INSERT OR REPLACE INTO kdone VALUES(?,?)", (event, n))
        if i % 25 == 0:
            db.commit()
            print(f"  {i}/{len(todo)}", flush=True)
        time.sleep(PAUSE)
    db.commit()


def fetch():
    DB.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    fetch_espn_games(db)
    fetch_kalshi_markets(db)
    match_games(db)
    fetch_rows(db)
    fetch_candles(db)


# ---------------------------------------------------------------- lag

def lag(path: str):
    rows = [json.loads(x) for x in open(path)]
    first = {}
    for r in rows:
        first[r["g"]] = min(first.get(r["g"], 1e18), r["seen"])
    lags = defaultdict(list)
    keep = []
    for r in rows:
        w = _ts(r["wall"])
        if w is None or w < first[r["g"]] or r["seen"] <= first[r["g"]] + 1:
            continue
        lags[r["lg"]].append(r["seen"] - w)
        keep.append(r)
    allv = sorted(v for vs in lags.values() for v in vs)

    def q(v, x):
        return v[min(len(v) - 1, int(x * len(v)))] if v else float("nan")
    print(f"lag sample: n {len(allv)} rows, games {len({r['g'] for r in keep})}")
    print(f"  all: median {q(allv, .5):.0f}s, p90 {q(allv, .9):.0f}s, p99 {q(allv, .99):.0f}s, max {allv[-1] if allv else float('nan'):.0f}s, min {allv[0] if allv else float('nan'):.0f}s")
    for lg, v in lags.items():
        v.sort()
        print(f"  {lg}: n {len(v)}, median {q(v, .5):.0f}s, p90 {q(v, .9):.0f}s, max {v[-1]:.0f}s")
    p90 = q(allv, .9)
    D = 60 if p90 <= 60 else int(math.ceil(p90 / 60.0)) * 60 + 60
    print(f"D = {D}s")
    # revisions: live first-seen value against the post-game stored value
    diff = tot = 0
    for g in {(r["lg"], r["g"]) for r in keep}:
        s = _json(f"https://site.api.espn.com/apis/site/v2/sports/{g[0]}/summary?event={g[1]}")
        stored = {w["playId"]: w["homeWinPercentage"] for w in s.get("winprobability", [])}
        for r in keep:
            if r["g"] == g[1] and r["play"] in stored:
                tot += 1
                diff += abs(stored[r["play"]] - r["p"]) > 0.01
        time.sleep(0.3)
    print(f"revisions: {diff} of {tot} rows differ by more than 0.01 between live and post-game")
    return D


# ---------------------------------------------------------------- score

VARIANTS = {
    "V1": ({"KXNFLGAME", "KXNCAAFGAME", "KXNBAGAME", "KXMLBGAME"}, 0.08),
    "V2": ({"KXNFLGAME", "KXNCAAFGAME", "KXNBAGAME", "KXMLBGAME"}, 0.15),
    "V3": ({"KXNFLGAME", "KXNCAAFGAME"}, 0.08),
    "V4": ({"KXNBAGAME", "KXMLBGAME"}, 0.08),
}


def fee_order(p: float, c: int) -> float:
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def load(db):
    res = {t: r for t, r in db.execute("SELECT ticker, result FROM kmarket")}
    cand = defaultdict(list)
    for tk, end, b, a, v in db.execute("SELECT ticker, end_ts, bid, ask, volume FROM candle ORDER BY ticker, end_ts"):
        cand[tk].append((end, b, a, v or 0.0))
    erows = defaultdict(list)
    for g, seq, wall, hp, tp in db.execute("SELECT egame, seq, wall_ts, home_p, tie_p FROM erow ORDER BY egame, wall_ts, seq"):
        erows[g].append((wall, hp, tp))
    games = []
    for event, series, g, h, a in db.execute("SELECT event, series, egame, home_ticker, away_ticker FROM match"):
        if not erows.get(g) or not (cand.get(h) or cand.get(a)):
            continue
        games.append(dict(event=event, series=series, g=g, h=h, a=a, day=datetime.fromtimestamp(erows[g][0][0], timezone.utc).date()))
    return res, cand, erows, games


def thirds(games):
    from collections import Counter
    cnt = Counter(x["day"] for x in games)
    n = len(games)
    cum = 0
    cuts = []
    for d in sorted(cnt):
        cum += cnt[d]
        if len(cuts) == 0 and cum >= n / 3:
            cuts.append(d)
        elif len(cuts) == 1 and cum >= 2 * n / 3:
            cuts.append(d)
    return cuts


def window_of(day, cuts):
    return "A" if day <= cuts[0] else ("B" if day <= cuts[1] else "C")


def entry_candle(cs, t, D, way):
    import bisect
    i = bisect.bisect_left(cs, (t + D, -1, -1, -1))
    while i < len(cs) and cs[i][0] <= t + D + 120:
        end, b, a, v = cs[i]
        if way == "A" or v > 0:
            return cs[i]
        i += 1
    return None


def valid(b, a):
    return b is not None and a is not None and b >= 0.01 and a <= 0.99 and a >= b and 0.03 <= a <= 0.97


def entry_for(game, cand, erows, D, way, thr):
    for wall, hp, tp in erows[game["g"]]:
        best = None
        for tk, p in ((game["h"], hp), (game["a"], 1 - hp - tp)):
            if p <= 0.005 or p >= 0.995:
                continue
            c = entry_candle(cand.get(tk, []), wall, D, way)
            if c is None or not valid(c[1], c[2]):
                continue
            gap = p - c[2]
            if gap >= thr and (best is None or gap > best[0]):
                best = (gap, tk, c[2], p, wall, c[0])
        if best:
            return best
    return None


def stats(nets):
    n = len(nets)
    if n == 0:
        return dict(n=0)
    m = sum(nets) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in nets) / (n - 1)) if n > 1 else float("nan")
    win = sum(x for x in nets if x > 0)
    loss = -sum(x for x in nets if x < 0)
    return dict(n=n, mean=m, z=m / (sd / math.sqrt(n)) if n > 1 and sd > 0 else float("nan"), pf=(win / loss if loss > 0 else float("inf")))


def score(D: int, which: str):
    db = sqlite3.connect(DB)
    res, cand, erows, games = load(db)
    cuts = thirds(games)
    from collections import Counter
    wc = Counter(window_of(x["day"], cuts) for x in games)
    print(f"games with ESPN rows and candles: {len(games)}; windows A <= {cuts[0]}, B <= {cuts[1]}, C after; games {dict(wc)}")
    print(f"by league: {dict(Counter(x['series'] for x in games))}")
    zero = sum(1 for cs in cand.values() for c in cs if c[3] == 0)
    allc = sum(len(cs) for cs in cand.values())
    print(f"candles {allc}, zero-volume {zero} ({zero / max(allc, 1):.1%})")
    wins = ["A", "B"] if which == "AB" else ["A", "B", "C"]
    out = {}
    for vname, (leagues, thr) in VARIANTS.items():
        for way in ("A", "B"):
            ents = defaultdict(list)
            for gm in games:
                if gm["series"] not in leagues:
                    continue
                w = window_of(gm["day"], cuts)
                if w not in wins:
                    continue
                e = entry_for(gm, cand, erows, D, way, thr)
                if e:
                    gap, tk, ask, p, wall, end = e
                    y = 1.0 if res[tk] == "yes" else 0.0
                    ents[w].append((ask, p, y, gm["series"]))
            for w in wins:
                es = ents[w]
                line = f"{vname} way{way} {w}: games {len(es)}"
                if es:
                    line += f", mean ask {sum(e[0] for e in es) / len(es):.3f}, mean ESPN p {sum(e[1] for e in es) / len(es):.3f}, win {sum(e[2] for e in es) / len(es):.3f}"
                for C in (1, 10):
                    for mult in (1.0, 1.2):
                        nets = [e[2] - e[0] - fee_order(e[0], C) * mult / C for e in es]
                        s = stats(nets)
                        if s["n"]:
                            line += f" | C{C} x{mult}: net {s['mean'] * 100:+.2f}c PF {s['pf']:.2f} z {s['z']:+.2f}"
                print(line)
                out[(vname, way, w)] = es
            pooled = [e for w in wins for e in ents[w]]
            nets = [e[2] - e[0] - fee_order(e[0], 1) for e in pooled]
            s = stats(nets)
            if s["n"]:
                print(f"{vname} way{way} pooled {''.join(wins)}: games {s['n']}, net {s['mean'] * 100:+.2f}c, PF {s['pf']:.2f}, z {s['z']:+.2f}")
            by = defaultdict(list)
            for e in pooled:
                by[e[3]].append(e[2] - e[0] - fee_order(e[0], 1))
            print("   by league (C1): " + ", ".join(f"{k} {len(v)} {sum(v) / len(v) * 100:+.2f}c" for k, v in by.items()))
    return out


def calib():
    """Information only: Brier of ESPN's probability vs Kalshi's mid (candle ending >= t+60, way A, valid quote)."""
    db = sqlite3.connect(DB)
    res, cand, erows, games = load(db)
    agg = defaultdict(lambda: [0, 0.0, 0.0])
    for gm in games:
        for wall, hp, tp in erows[gm["g"]]:
            tk, p = gm["h"], hp
            c = entry_candle(cand.get(tk, []), wall, 60, "A")
            if c is None or not valid(c[1], c[2]):
                continue
            y = 1.0 if res[tk] == "yes" else 0.0
            mid = (c[1] + c[2]) / 2
            a = agg[gm["series"]]
            a[0] += 1
            a[1] += (p - y) ** 2
            a[2] += (mid - y) ** 2
    for k, (n, be, bk) in agg.items():
        print(f"{k}: rows {n}, Brier ESPN {be / n:.4f}, Brier Kalshi mid {bk / n:.4f}")


if __name__ == "__main__":
    if sys.argv[1] == "lag":
        lag(sys.argv[2])
    elif sys.argv[1] == "score":
        score(int(sys.argv[2]), sys.argv[3])
    elif sys.argv[1] == "calib":
        calib()

    cmd = sys.argv[1]
    if cmd == "fetch":
        fetch()
    elif cmd == "match":
        db = sqlite3.connect(DB)
        match_games(db)
