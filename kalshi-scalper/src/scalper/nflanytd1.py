"""NFLANYTD1: NFL anytime-touchdown ladder (KXNFLANYTD), CHEAP side only, unconditional pool plus a ladder-sum filter. Research only.
Registration: workers/NFLANYTD1_REGISTRATION.md.
  python -m scalper.nflanytd1 build | espn | candles MINUTES [STRIDE OFFSET] | score
Listing is cached in /home/user/.cache/nflanytd1/listing.json (listings only: no `result`). The result is read from Kalshi once, at score time.
"""
from __future__ import annotations
import json, re, sqlite3, sys, time, hashlib, math, urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from . import api
from .candlefield import quote_close
from .nhlg1 import net, valid, cluster_stats, profit_factor, md5, sha, C

CACHE = Path("/home/user/.cache/nflanytd1")
DB = CACHE / "nflanytd1.sqlite"
ROOT = Path(__file__).resolve().parents[2]
PROPS = ROOT / "data" / "props1.sqlite"
CUT = "2026-10-03T16:00:00Z"
LO, HI, LEAD, MAXPER, MIN_TRADES, WINDOW = 0.03, 0.30, 120, 2, 150, 6 * 3600
UA = "shwoopnet-research-nflanytd1/1.0 (personal research, 1 req/s)"
ET = ZoneInfo("America/New_York")
KALSHI_TO_ESPN = {"JAC": "JAX", "LA": "LAR", "WAS": "WSH"}
CODES = "ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAC KC LA LAC LV MIA MIN NE NO NYG NYJ PHI PIT SEA SF TB TEN WAS".split()
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
EV = re.compile(r"^KXNFLANYTD-(\d\d)([A-Z]{3})(\d\d)([A-Z]+)$")
SCHEMA = """
CREATE TABLE IF NOT EXISTS gm(event TEXT PRIMARY KEY, start_ts INTEGER, espn_id TEXT, md5 TEXT);
CREATE TABLE IF NOT EXISTS rung(ticker TEXT PRIMARY KEY, event TEXT, volume REAL);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS cdone(ticker TEXT PRIMARY KEY, n INTEGER);
CREATE TABLE IF NOT EXISTS tdbox(espn_id TEXT PRIMARY KEY, scorers INTEGER);
"""


def conn():
    CACHE.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=120)
    c.executescript(SCHEMA)
    return c


# ----------------------------------------------------------------------------- pure functions (tested)

def split_event(event: str):
    """(date, (team_a, team_b)) from KXNFLANYTD-YYMONDDAABB; teams as ESPN abbreviations; None if unparsable or ambiguous."""
    m = EV.match(event)
    if not m or m.group(2) not in MON:
        return None
    try:
        d = datetime(2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3))).date()
    except ValueError:
        return None
    s = m.group(4)
    opts = [(s[:i], s[i:]) for i in range(2, len(s) - 1) if s[:i] in CODES and s[i:] in CODES]
    if len(opts) != 1:
        return None
    a, b = opts[0]
    return d, (KALSHI_TO_ESPN.get(a, a), KALSHI_TO_ESPN.get(b, b))


def match_game(event: str, games):
    """games: iterable of (id, start_ts, home, away). Match by Eastern date (+-1 day) and team set; None unless exactly one."""
    sp = split_event(event)
    if not sp:
        return None
    d, teams = sp
    hits = []
    for gid, ts, h, a in games:
        if {h, a} != set(teams):
            continue
        gd = datetime.fromtimestamp(ts, timezone.utc).astimezone(ET).date()
        if abs((gd - d).days) <= 1:
            hits.append((abs((gd - d).days), gid, ts))
    hits.sort()
    if not hits or (len(hits) > 1 and hits[0][0] == hits[1][0]):
        return None
    return hits[0][1], hits[0][2]


def look_quote(candles, start_ts: int, lead: int = LEAD):
    ok = [r for r in candles if r[0] <= start_ts - lead and valid(r[1], r[2])]
    if not ok:
        return None
    ok.sort()
    return ok[-1][1], ok[-1][2]


def is_cheap(ask) -> bool:
    return ask is not None and LO <= ask <= HI


def pick_two(rows):
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


def count_td_scorers(summ: dict) -> int:
    """Distinct players with at least one rushing or receiving TD in an ESPN summary."""
    seen = set()
    for tm in (summ.get("boxscore", {}) or {}).get("players", []) or []:
        for blk in tm.get("statistics", []) or []:
            kind = (blk.get("name") or "").lower()
            if kind not in ("rushing", "receiving"):
                continue
            labels = blk.get("labels") or []
            if "TD" not in labels:
                continue
            i = labels.index("TD")
            for a in blk.get("athletes", []) or []:
                try:
                    if float((a.get("stats") or [])[i]) >= 1:
                        seen.add((a.get("athlete") or {}).get("id"))
                except (IndexError, ValueError, TypeError):
                    pass
    return len(seen)


# ----------------------------------------------------------------------------- build / espn / candles

def listing():
    return json.load(open(CACHE / "listing.json"))


def build():
    c = conn()
    g = list(sqlite3.connect(f"file:{PROPS}?mode=ro", uri=True).execute("SELECT id,start_ts,home,away FROM game WHERE league='NFL'"))
    tot = ok = 0
    seen = {}
    for r in listing():
        if (r["close_time"] or "9") >= CUT or r["ticker"].endswith("-NOTD"):
            continue
        vol = float(r["volume_fp"] or 0)
        if vol <= 0:
            continue
        ev = r["event_ticker"]
        if ev not in seen:
            seen[ev] = match_game(ev, g)
            tot += 1
            ok += seen[ev] is not None
        if seen[ev] is None:
            continue
        gid, ts = seen[ev]
        c.execute("INSERT OR IGNORE INTO gm VALUES(?,?,?,?)", (ev, ts, gid, md5(ev)))
        c.execute("INSERT OR IGNORE INTO rung VALUES(?,?,?)", (r["ticker"], ev, vol))
    c.commit()
    print("events", tot, "matched", ok, flush=True)
    return tot, ok


def jget(url, tries=5):
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
    todo = [r[0] for r in c.execute("SELECT DISTINCT espn_id FROM gm WHERE espn_id NOT IN (SELECT espn_id FROM tdbox)")]
    for i, gid in enumerate(todo):
        s = jget(f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={gid}")
        c.execute("INSERT OR REPLACE INTO tdbox VALUES(?,?)", (gid, count_td_scorers(s)))
        if i % 25 == 0:
            c.commit()
            print("espn", i, "/", len(todo), flush=True)
        time.sleep(1.0)
    c.commit()


def cmd_candles(minutes, stride=1, offset=0):
    c = conn()
    t_end = time.time() + 60 * minutes
    byg = defaultdict(list)
    for tk, ev in c.execute("SELECT ticker,event FROM rung"):
        byg[ev].append(tk)
    starts = {r[0]: r[1] for r in c.execute("SELECT event,start_ts FROM gm")}
    order = sorted(byg, key=md5)
    n_ok = n_fail = 0
    for pas in range(3):
        pending = [g for g in order if any(not c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone() for tk in byg[g])]
        print("pass", pas, "games left", len(pending), flush=True)
        if not pending:
            break
        for gi, ev in enumerate(pending):
            if gi % stride != offset:
                continue
            if time.time() > t_end:
                print("time box reached", flush=True)
                break
            st = starts[ev]
            for tk in byg[ev]:
                if c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone():
                    continue
                cs = None
                for a in range(4):
                    try:
                        cs = api._get(f"/historical/markets/{tk}/candlesticks", {"start_ts": st - WINDOW, "end_ts": st, "period_interval": 1}, retries=1).get("candlesticks", [])
                        break
                    except Exception:  # noqa: BLE001
                        time.sleep(2 + 3 * a)
                time.sleep(0.5)
                if cs is None:
                    n_fail += 1
                    continue
                n_ok += 1
                for x in cs:
                    c.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
                c.execute("INSERT OR REPLACE INTO cdone VALUES(?,?)", (tk, len(cs)))
                c.commit()
            if gi % 5 == 0:
                print("pass", pas, "game", gi, "/", len(pending), "ok", n_ok, "fail", n_fail, flush=True)
        if time.time() > t_end:
            break
    c.commit()
    print("candles done; ok", n_ok, "fail", n_fail, flush=True)


# ----------------------------------------------------------------------------- score (reads results once)

def fetch_results():
    """Kalshi settled results, read ONCE at score time."""
    res = {}
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cursor = None
        while True:
            q = dict(series_ticker="KXNFLANYTD", limit=1000, **extra)
            if cursor:
                q["cursor"] = cursor
            d = api._get(path, q)
            time.sleep(1.0)
            for m in d.get("markets", []):
                if m.get("result") in ("yes", "no"):
                    res[m["ticker"]] = m["result"]
            cursor = d.get("cursor")
            if not cursor:
                break
    return res


def build_games(c):
    """Complete games (every rung fetched): event -> dict(start, asks{ticker: ask}, S). Prices only, no results."""
    byg = defaultdict(list)
    for tk, ev in c.execute("SELECT ticker,event FROM rung"):
        byg[ev].append(tk)
    done = {r[0] for r in c.execute("SELECT ticker FROM cdone")}
    starts = {r[0]: r[1] for r in c.execute("SELECT event,start_ts FROM gm")}
    games = {}
    for ev, tks in byg.items():
        if not all(t in done for t in tks):
            continue
        asks = {}
        for tk in tks:
            q = look_quote(list(c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=?", (tk,))), starts[ev])
            if q:
                asks[tk] = q[1]
        games[ev] = dict(start=starts[ev], asks=asks, S=sum(asks.values()))
    return games


def score(out_json):
    c = conn()
    games = build_games(c)
    allstarts = sorted(r[0] for r in c.execute("SELECT start_ts FROM gm"))
    cut2 = allstarts[(2 * len(allstarts)) // 3]
    early = [r[0] for r in c.execute("SELECT t.scorers FROM gm g JOIN tdbox t ON t.espn_id=g.espn_id WHERE g.start_ts<?", (cut2,))]
    E = sum(early) / len(early)
    early_S = [g["S"] for g in games.values() if g["start"] < cut2 and g["asks"]]
    cuts = terciles(early_S) if len(early_S) >= 3 else (0, 0)
    res = fetch_results()
    trades = []
    for ev, g in games.items():
        rows = [dict(ticker=t, ask=a) for t, a in g["asks"].items() if is_cheap(a) and t in res]
        for r in pick_two(rows):
            trades.append(dict(game=ev, date=datetime.fromtimestamp(g["start"], timezone.utc).astimezone(ET).strftime("%Y-%m-%d"), start=g["start"],
                               ask=r["ask"], win=res[r["ticker"]] == "yes", S=g["S"], under=g["S"] < E, terc=tercile_of(g["S"], cuts)))
    out = dict(games_complete=len(games), games_with_cheap_trade=len({t["game"] for t in trades}), E_expected_scorers=E, early_games=len(early),
               mean_S=sum(g["S"] for g in games.values()) / max(1, len(games)), under_games=sum(1 for g in games.values() if g["S"] < E),
               cuts=list(cuts), cut2_ts=cut2,
               cheap_rungs_in_complete_games=sum(1 for g in games.values() for a in g["asks"].values() if is_cheap(a)))

    def block(ts):
        if not ts:
            return dict(n=0, verdict="NOT_ENOUGH_DATA")
        ms = sorted(t["start"] for t in ts)
        med = ms[len(ms) // 2]
        h = [[t for t in ts if t["start"] < med], [t for t in ts if t["start"] >= med]]
        b = clustered(ts, "game")
        b["date_cluster"] = clustered(ts, "date")
        b["mean_c_fee_x1.2"] = clustered(ts, "game", 1.2)["mean_c"]
        b["halves"] = [clustered(x, "game") if x else dict(n=0, mean_c=float("nan")) for x in h]
        b["buckets"] = {k: clustered([t for t in ts if lo <= t["ask"] < hi], "game")
                        for k, (lo, hi) in {"3-10": (0.03, 0.10), "10-20": (0.10, 0.20), "20-30": (0.20, 0.3001)}.items()
                        if any(lo <= t["ask"] < hi for t in ts)}
        hm = [x["mean_c"] for x in b["halves"]]
        b["verdict"] = verdict(b["n"], hm, b["lo95_c"], b["pf"])
        return b
    out["pooled"] = block(trades)
    out["filter_under_round"] = block([t for t in trades if t["under"]])
    out["terciles"] = {str(k): block([t for t in trades if t["terc"] == k]) for k in (0, 1, 2)}
    json.dump(out, open(out_json, "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build()
    elif cmd == "espn":
        cmd_espn()
    elif cmd == "score":
        score(sys.argv[2])
    elif cmd == "candles":
        cmd_candles(float(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 1, int(sys.argv[4]) if len(sys.argv) > 4 else 0)
