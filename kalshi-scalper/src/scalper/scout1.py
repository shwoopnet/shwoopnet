"""SCOUT1: census (listings and close times only; no candle, no result field read) and, once a rule is registered, the scorer.
Usage: python -m scalper.scout1 census OUT.json SERIES...   (counts markets/events/close dates settled before the frozen cut, per month, plus median volume)
The census never reads `result`, `settlement_value`, prices or any outcome."""
from __future__ import annotations
import collections, json, statistics as st, sys, time, urllib.parse, urllib.request

BASE = "https://api.elections.kalshi.com/trade-api/v2"
CUT = "2026-10-03T16:00:00Z"
UA = "shwoopnet-research-scout1/1.0 (listings census; polite)"
import os
MAX_PAGES = int(os.environ.get("SCOUT1_MAXP", "6"))


def get(path, **q):
    url = BASE + path + "?" + urllib.parse.urlencode(q)
    for a in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as e:
            time.sleep(min(60, 2 ** a * (3 if "429" in str(e) else 1)))
    return None


def census_series(s):
    mon = collections.Counter(); ev = collections.defaultdict(set); days = set(); vols = []
    tot = 0; capped = False; first = last = None
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cursor = None; pages = 0
        while True:
            q = dict(series_ticker=s, limit=1000, **extra)
            if cursor: q["cursor"] = cursor
            d = get(path, **q); time.sleep(0.5)
            if not d: break
            pages += 1
            for m in d.get("markets", []):
                ct = m.get("close_time") or ""
                tot += 1
                if ct and ct < CUT:
                    mon[ct[:7]] += 1; ev[ct[:7]].add(m.get("event_ticker")); days.add(ct[:10])
                    try: vols.append(float(m.get("volume_fp") or m.get("volume") or 0))
                    except Exception: pass
                    first = ct if first is None or ct < first else first
                    last = ct if last is None or ct > last else last
            cursor = d.get("cursor")
            if not cursor: break
            if pages >= MAX_PAGES: capped = True; break
    nm = sum(mon.values()); ne = sum(len(v) for v in ev.values())
    return dict(markets=nm, events=ne, close_days=len(days), first=first, last=last, capped=capped,
                median_volume=(st.median(vols) if vols else 0), by_month={k: [mon[k], len(ev[k])] for k in sorted(mon)})


def main():
    out, series = sys.argv[2], sys.argv[3:]
    res = {}
    for s in series:
        res[s] = census_series(s)
        r = res[s]
        print(s, r["markets"], r["events"], r["close_days"], r["first"], r["last"], "CAPPED" if r["capped"] else "", flush=True)
        json.dump(res, open(out, "w"), indent=1)


# ============================================================================================ MLBKS1 (registered in workers/SCOUT1_REGISTRATION.md)
# python -m scalper.scout1 espn | markets | build | candles | score    (data/scout1.sqlite, git-ignored)
# The frozen third (games starting at or after CUT) is never fetched: every query is bounded by CUT.
import hashlib, math, re, sqlite3, unicodedata
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import api
from .candlefield import quote_close

DB = Path(__file__).resolve().parents[2] / "data" / "scout1.sqlite"
CUT_TS = int(datetime(2026, 10, 3, 16, tzinfo=timezone.utc).timestamp())
LO, HI, RATIO, C, LEAD, MAXPER, SAMPLE = 0.03, 0.30, 3.0, 10, 300, 2, 40
ESPN_UA = "shwoopnet-research-scout1/1.0 (personal research, 1 req/s)"
SERIES = "KXMLBKS"
KS_GRID, RS_GRID, GAMMAS = (1, 2, 4, 8, 16), (1, 2, 4, 8, 16, 32, 64), (0.0, 0.5, 1.0)
ESPN = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb"


# ----------------------------------------------------------------------------- pure functions (tested)

def fee(p: float, c: int = C) -> float:
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win: bool, ask: float, mult: float = 1.0) -> float:
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def sha(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z ]", " ", s)
    return " ".join(w for w in s.split() if w not in ("jr", "sr", "ii", "iii", "iv"))


def nb_logpmf(x: int, mu: float, r: float) -> float:
    p = r / (r + mu)
    return math.lgamma(x + r) - math.lgamma(r) - math.lgamma(x + 1) + r * math.log(p) + x * math.log(1 - p)


def nb_sf(s: float, mu: float, r: float) -> float:
    """P(X > s), X negative binomial with mean mu and variance mu + mu^2 / r."""
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
    return max(0.0, min(1.0, 1.0 - cdf))


def shrunk_mean(prior: list[float], m_lg: float, k: float):
    """Earlier starts, oldest first: the last up to 10 shrunk toward the league mean; None under 3 starts."""
    last = prior[-10:]
    if len(last) < 3:
        return None
    return max(0.05, (sum(last) + k * m_lg) / (len(last) + k))


def opp_factor(opp_k: list[float], lg_k: float, gamma: float) -> float:
    """Opponent batting strikeouts per game (last up to 20 games before the start), shrunk with weight 10, as a ratio to the league."""
    last = opp_k[-20:]
    shr = (sum(last) + 10 * lg_k) / (len(last) + 10)
    return (shr / lg_k) ** gamma


def fit_params(rows, m_lg: float, lg_k: float):
    """rows: (prior_starts, opp_prior_k, actual_k). Highest FIT log likelihood over the registered grid -> (ll, k, r, gamma, n)."""
    best = None
    for k in KS_GRID:
        for g in GAMMAS:
            mus = []
            for pr, ok, a in rows:
                mu0 = shrunk_mean(pr, m_lg, k)
                if mu0 is not None:
                    mus.append((mu0 * opp_factor(ok, lg_k, g), a))
            if not mus:
                continue
            for r in RS_GRID:
                ll = sum(nb_logpmf(a, mu, r) for mu, a in mus)
                if best is None or ll > best[0]:
                    best = (ll, k, r, g, len(mus))
    return best


def parse_box_mlb(summ: dict):
    """-> (pitchers, team_k). pitchers: dicts aid, nm, team, starter, k, ip; team_k: team abbreviation -> batting strikeouts."""
    pitchers, team_k = [], {}
    for tm in (summ.get("boxscore", {}) or {}).get("players", []) or []:
        team = (tm.get("team") or {}).get("abbreviation", "")
        for blk in tm.get("statistics", []) or []:
            labels = blk.get("labels") or []
            kind = (blk.get("type") or blk.get("name") or "").lower()
            if kind == "batting" and "K" in labels and blk.get("totals"):
                try:
                    team_k[team] = float(blk["totals"][labels.index("K")])
                except (ValueError, IndexError):
                    pass
            if kind == "pitching" and "K" in labels:
                for a in blk.get("athletes", []) or []:
                    ath = a.get("athlete") or {}
                    st = a.get("stats") or []
                    try:
                        k = float(st[labels.index("K")])
                        ip = float(st[labels.index("IP")]) if "IP" in labels else 0.0
                    except (ValueError, IndexError):
                        continue
                    pitchers.append(dict(aid=str(ath.get("id")), nm=norm_name(ath.get("displayName", "")), team=team,
                                         starter=1 if a.get("starter") else 0, k=k, ip=ip))
    return pitchers, team_k


def event_date(event: str):
    m = re.match(r"^[A-Z0-9]+-(\d\d)([A-Z]{3})(\d\d)", event)
    if not m:
        return None
    mon = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"].index(m.group(2)) + 1
    return datetime(2000 + int(m.group(1)), mon, int(m.group(3)))


def cheap_side(bid: float, ask: float):
    ya, na = ask, 1 - bid
    if LO <= ya <= HI:
        return "yes", ya
    if LO <= na <= HI:
        return "no", na
    return None


def valid(b, a) -> bool:
    return b is not None and a is not None and 0 <= b < a <= 1 and a - b <= 0.10


def pick_trades(rows: list[dict], treated: bool) -> list[dict]:
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


def profit_factor(nets: list[float]) -> float:
    g = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return g / l if l > 0 else float("inf")


def split_labels(n: int):
    """First two thirds FIT, then the last third halved T1 (older) / T2."""
    i_fit = (2 * n) // 3
    i_half = i_fit + (n - i_fit) // 2
    return ["FIT" if i < i_fit else ("T1" if i < i_half else "T2") for i in range(n)]


# ----------------------------------------------------------------------------- storage and fetch

SCHEMA = """
CREATE TABLE IF NOT EXISTS game(id TEXT PRIMARY KEY, start_ts INTEGER, home TEXT, away TEXT);
CREATE TABLE IF NOT EXISTS gdone(id TEXT PRIMARY KEY, n INTEGER);
CREATE TABLE IF NOT EXISTS pitch(gid TEXT, aid TEXT, nm TEXT, team TEXT, starter INTEGER, k REAL, ip REAL, PRIMARY KEY(gid, aid));
CREATE TABLE IF NOT EXISTS tbat(gid TEXT, team TEXT, k REAL, PRIMARY KEY(gid, team));
CREATE TABLE IF NOT EXISTS kmarket(ticker TEXT PRIMARY KEY, event TEXT, name TEXT, strike REAL, close_time TEXT, exp_time TEXT, result TEXT, src TEXT);
CREATE TABLE IF NOT EXISTS kdone(src TEXT PRIMARY KEY, n INTEGER, dropped INTEGER);
CREATE TABLE IF NOT EXISTS mgame(ticker TEXT PRIMARY KEY, gid TEXT, aid TEXT, split TEXT, mu REAL, p_yes REAL, sampled INTEGER);
CREATE TABLE IF NOT EXISTS fit(id INTEGER PRIMARY KEY, k REAL, r REAL, gamma REAL, m_lg REAL, lg_k REAL, n INTEGER);
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
            req = urllib.request.Request(url, headers={"User-Agent": ESPN_UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{url}: {last}")


def cmd_espn():
    c = conn()
    d0, d1 = datetime(2026, 3, 25), datetime(2026, 10, 2)
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
                h = next((x["team"]["abbreviation"] for x in comp if x.get("homeAway") == "home"), "")
                aw = next((x["team"]["abbreviation"] for x in comp if x.get("homeAway") == "away"), "")
                c.execute("INSERT OR IGNORE INTO game VALUES(?,?,?,?)", (ev["id"], ts, h, aw))
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
        pit, tk = parse_box_mlb(s)
        for p in pit:
            c.execute("INSERT OR REPLACE INTO pitch VALUES(?,?,?,?,?,?,?)", (gid, p["aid"], p["nm"], p["team"], p["starter"], p["k"], p["ip"]))
        for t, k in tk.items():
            c.execute("INSERT OR REPLACE INTO tbat VALUES(?,?,?)", (gid, t, k))
        c.execute("INSERT OR REPLACE INTO gdone VALUES(?,?)", (gid, len(pit)))
        if i % 25 == 0:
            c.commit()
            print("box", i, "/", len(todo), flush=True)
        time.sleep(1.0)
    c.commit()
    print("espn done: games", c.execute("SELECT COUNT(*) FROM game").fetchone()[0], "with box", c.execute("SELECT COUNT(*) FROM gdone WHERE id NOT LIKE 'day:%'").fetchone()[0], flush=True)


def cmd_markets():
    c = conn()
    cut_iso = "2026-10-03T16:00:00Z"
    for src, path, extra in (("hist", "/historical/markets", {}), ("live", "/markets", {"status": "settled"})):
        if c.execute("SELECT 1 FROM kdone WHERE src=?", (src,)).fetchone():
            continue
        cursor, n, dropped = None, 0, 0
        while True:
            q = dict(series_ticker=SERIES, limit=1000, **extra)
            if cursor:
                q["cursor"] = cursor
            d = api._get(path, q)
            time.sleep(0.6)
            for m in d.get("markets", []):
                ct = m.get("close_time") or ""
                ex = m.get("expected_expiration_time") or ct
                if ct >= cut_iso or ex >= cut_iso:
                    continue
                if m.get("result") not in ("yes", "no"):
                    dropped += 1
                    continue
                name = (m.get("yes_sub_title") or "").split(":")[0]
                c.execute("INSERT OR IGNORE INTO kmarket VALUES(?,?,?,?,?,?,?,?)",
                          (m["ticker"], m["event_ticker"], norm_name(name), m.get("floor_strike"), ct, ex, m["result"], src))
                n += 1
            cursor = d.get("cursor")
            if not cursor:
                break
        c.execute("INSERT OR REPLACE INTO kdone VALUES(?,?,?)", (src, n, dropped))
        c.commit()
        print(src, "markets kept", n, "dropped (result not yes/no)", dropped, flush=True)


def cmd_build():
    c = conn()
    et = timezone(timedelta(hours=-4))  # the ticker date is the US Eastern date; plus or minus one day tolerated below
    starts = {r[0]: r[1] for r in c.execute("SELECT id,start_ts FROM game")}
    byname = defaultdict(list)
    for gid, aid, nm in c.execute("SELECT gid,aid,nm FROM pitch"):
        if gid in starts:
            byname[nm].append((gid, starts[gid], aid))
    c.execute("DELETE FROM mgame")
    total = unmatched = 0
    for tk, event, name, ct in list(c.execute("SELECT ticker,event,name,close_time FROM kmarket")):
        total += 1
        d = event_date(event)
        best = None
        for gid, st, aid in byname.get(name, []):
            gd = datetime.fromtimestamp(st, tz=timezone.utc).astimezone(et).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
            diff = abs((gd - d).days) if d else 9
            if diff <= 1 and (best is None or diff < best[0]):
                best = (diff, gid, aid)
        if best is None:
            unmatched += 1
            continue
        c.execute("INSERT INTO mgame(ticker,gid,aid) VALUES(?,?,?)", (tk, best[1], best[2]))
    c.commit()
    print("markets", total, "unmatched", unmatched, f"match rate {1 - unmatched / max(1, total):.3f}", flush=True)
    gs = sorted({(starts[r[0]], r[0]) for r in c.execute("SELECT gid FROM mgame")})
    labels = split_labels(len(gs))
    for (st, gid), sp in zip(gs, labels):
        c.execute("UPDATE mgame SET split=? WHERE gid=?", (sp, gid))
    split_ts = next((st for (st, gid), sp in zip(gs, labels) if sp != "FIT"), gs[-1][0])
    print("matched games", len(gs), "FIT", labels.count("FIT"), "T1", labels.count("T1"), "T2", labels.count("T2"), flush=True)
    hist = defaultdict(list)  # aid -> [(start, k)] starts only
    for gid, aid, k in c.execute("SELECT gid,aid,k FROM pitch WHERE starter=1"):
        if gid in starts:
            hist[aid].append((starts[gid], k))
    for L in hist.values():
        L.sort()
    opp_of = {}
    for gid, home, away in c.execute("SELECT id,home,away FROM game"):
        opp_of[(gid, home)] = away
        opp_of[(gid, away)] = home
    tk_hist = defaultdict(list)  # team -> [(start, batting strikeouts)]
    for gid, team, k in c.execute("SELECT gid,team,k FROM tbat"):
        if gid in starts:
            tk_hist[team].append((starts[gid], k))
    for L in tk_hist.values():
        L.sort()
    team_of = {(gid, aid): team for gid, aid, team in c.execute("SELECT gid,aid,team FROM pitch")}
    fit_ks = [k for L in hist.values() for st, k in L if st < split_ts]
    m_lg = sum(fit_ks) / len(fit_ks)
    lgk_vals = [k for L in tk_hist.values() for st, k in L if st < split_ts]
    lg_k = sum(lgk_vals) / len(lgk_vals)
    rows = []
    for gid, aid, k in c.execute("SELECT gid,aid,k FROM pitch WHERE starter=1"):
        st = starts.get(gid)
        if st is None or st >= split_ts:
            continue
        prior = [v for s, v in hist[aid] if s < st]
        if len(prior) < 3:
            continue
        opp = opp_of.get((gid, team_of.get((gid, aid))))
        ok = [v for s, v in tk_hist.get(opp, []) if s < st]
        rows.append((prior, ok, int(round(k))))
    _, kk, rr, gg, nn = fit_params(rows, m_lg, lg_k)
    c.execute("INSERT OR REPLACE INTO fit VALUES(1,?,?,?,?,?,?)", (kk, rr, gg, m_lg, lg_k, nn))
    print("fit k", kk, "r", rr, "gamma", gg, "m_lg", round(m_lg, 3), "lg_k", round(lg_k, 3), "starts", nn, flush=True)
    games = defaultdict(list)
    for tk, gid, aid, sp in list(c.execute("SELECT ticker,gid,aid,split FROM mgame WHERE split IN ('T1','T2')")):
        strike = c.execute("SELECT strike FROM kmarket WHERE ticker=?", (tk,)).fetchone()[0]
        st = starts[gid]
        prior = [v for s, v in hist.get(aid, []) if s < st]
        mu0 = shrunk_mean(prior, m_lg, kk)
        if mu0 is None or strike is None:
            continue
        opp = opp_of.get((gid, team_of.get((gid, aid))))
        ok = [v for s, v in tk_hist.get(opp, []) if s < st]
        mu = mu0 * opp_factor(ok, lg_k, gg)
        c.execute("UPDATE mgame SET mu=?, p_yes=? WHERE ticker=?", (mu, nb_sf(strike, mu, rr), tk))
        games[gid].append(tk)
    for gid, tks in games.items():
        for tk in sorted(tks, key=sha)[:SAMPLE]:
            c.execute("UPDATE mgame SET sampled=1 WHERE ticker=?", (tk,))
    c.commit()
    print("TEST games with a model", len(games), "sampled markets", c.execute("SELECT COUNT(*) FROM mgame WHERE sampled=1").fetchone()[0], flush=True)


def cmd_candles():
    c = conn()
    todo = list(c.execute("""SELECT m.ticker,g.start_ts,k.src FROM mgame m JOIN kmarket k ON k.ticker=m.ticker JOIN game g ON g.id=m.gid
        WHERE m.sampled=1 AND m.ticker NOT IN (SELECT ticker FROM cdone) ORDER BY g.start_ts"""))
    print("candles to fetch", len(todo), flush=True)
    live = [r for r in todo if r[2] == "live"]
    hist_ = [r for r in todo if r[2] != "live"]
    # plumbing only: the batch endpoint also answers for the newer archived markets; those it leaves empty go one by one below
    newer = [r for r in hist_ if r[1] >= 1788000000]  # 2026-08-29: the batch endpoint answered from about 08-28 on (probe, plumbing only)
    for i in range(0, len(newer), 8):
        batch = newer[i:i + 8]
        try:
            res = api.batch_candlesticks([x[0] for x in batch], min(x[1] for x in batch) - 7200, max(x[1] for x in batch))
        except Exception:  # noqa: BLE001
            res = {}
        for tk, st, _ in batch:
            cs = res.get(tk) or []
            if cs:
                for x in cs:
                    c.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
                c.execute("INSERT OR REPLACE INTO cdone VALUES(?,?)", (tk, len(cs)))
        if (i // 8) % 20 == 0:
            c.commit()
            print("hist batch", i, "/", len(newer), flush=True)
        time.sleep(0.8)
    c.commit()
    hist_ = [r for r in hist_ if not c.execute("SELECT 1 FROM cdone WHERE ticker=?", (r[0],)).fetchone()]
    print("hist one by one", len(hist_), flush=True)
    for i, (tk, st, _) in enumerate(hist_):
        try:
            d = api._get(f"/historical/markets/{tk}/candlesticks", {"start_ts": st - 7200, "end_ts": st, "period_interval": 1})
            cs = d.get("candlesticks", [])
        except Exception:  # noqa: BLE001
            cs = None
        if cs is not None:
            for x in cs:
                c.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
            c.execute("INSERT OR REPLACE INTO cdone VALUES(?,?)", (tk, len(cs)))
        if i % 100 == 0:
            c.commit()
            print("hist", i, "/", len(hist_), flush=True)
        time.sleep(1.0)
    c.commit()
    for i in range(0, len(live), 8):
        batch = live[i:i + 8]
        a, b = min(x[1] for x in batch) - 7200, max(x[1] for x in batch)
        try:
            res = api.batch_candlesticks([x[0] for x in batch], a, b)
        except Exception:  # noqa: BLE001
            res = None
        if res is not None:
            for tk, st, _ in batch:
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


def load_entries(c):
    out, brier = [], []
    q = """SELECT m.ticker,m.gid,m.split,m.p_yes,k.result,g.start_ts FROM mgame m JOIN kmarket k ON k.ticker=m.ticker JOIN game g ON g.id=m.gid
           WHERE m.sampled=1 AND m.p_yes IS NOT NULL"""
    for tk, gid, sp, py, res, st in list(c.execute(q)):
        look = st - LEAD
        cs = [r for r in c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=? AND end_ts<=? ORDER BY end_ts", (tk, look)) if valid(r[1], r[2])]
        if not cs:
            continue
        _, bid, ask = cs[-1]
        y = 1.0 if res == "yes" else 0.0
        brier.append(((py - y) ** 2, (((bid + ask) / 2) - y) ** 2))
        side = cheap_side(bid, ask)
        if side is None:
            continue
        s, a = side
        out.append(dict(ticker=tk, game=gid, split=sp, side=s, ask=a, p_side=py if s == "yes" else 1 - py, win=(res == "yes") == (s == "yes")))
    return out, brier


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
    ents, brier = load_entries(c)
    bygame = defaultdict(list)
    for e in ents:
        bygame[e["game"]].append(e)
    treated, control, allcheap = [], [], []
    for g, L in bygame.items():
        treated += pick_trades(L, True)
        control += pick_trades(L, False)
        allcheap += L
    res = {"cheap_entries": len(ents), "games_with_cheap": len(bygame), "quoted_rungs": len(brier),
           "brier_model": sum(b[0] for b in brier) / max(1, len(brier)), "brier_mid": sum(b[1] for b in brier) / max(1, len(brier))}
    for nm, T in (("treated", treated), ("control_cap2", control), ("all_cheap", allcheap)):
        res[nm] = summarise(T)
        res[nm + "_x1.2"] = summarise(T, 1.2)
        for h in ("T1", "T2"):
            res[nm + "_" + h] = summarise([t for t in T if t["split"] == h])
    json.dump(res, open(Path(__file__).resolve().parents[2] / "workers" / "SCOUT1_RESULT.json", "w"), indent=1)
    for k, v in res.items():
        print(k, v if not isinstance(v, dict) else {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items()})


if __name__ == "__main__":
    {"census": main, "espn": cmd_espn, "markets": cmd_markets, "build": cmd_build, "candles": cmd_candles, "score": cmd_score}[sys.argv[1]]()
