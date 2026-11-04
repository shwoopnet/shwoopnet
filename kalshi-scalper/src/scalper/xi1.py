"""XI1: official starting XI vs Kalshi soccer anytime-goalscorer (1+) cheap YES rungs. Held to settlement.

Registration: workers/XI1_REGISTRATION.md (sha256 2022df46...). Cheap side only (YES ask 3c-30c). Research only.
Cache outside the repo (XI1_CACHE). Steps: espn | join | fit | candles | results | score.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import time
import unicodedata
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .candlefield import quote_close

CACHE = Path(os.environ.get("XI1_CACHE", "/home/user/.cache/xi1"))
UA = "research-bot XI1 (kalshi research)"
CORE = "https://sports.core.api.espn.com/v2/sports/soccer/leagues"
LO, HI, C, LEAD, MAXQ, MAXPER, RATIO, K = 0.03, 0.30, 10, 1800, 0.10, 2, 3.0, 3.0
LEAGUES = {"KXEPLGOAL": "eng.1", "KXLALIGAGOAL": "esp.1", "KXUCLGOAL": "uefa.champions"}
EARLY = 35 * 60  # a market opened later than kickoff - 35 min cannot have a candle ending 30 min before


# ----------------------------------------------------------------------------- pure functions (tested)
def fee(p, c=C):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win, ask, mult=1.0):
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf")


def sha(s):
    return hashlib.sha1(s.encode()).hexdigest()


def md5(s):
    return hashlib.md5(str(s).encode()).hexdigest()


def valid(bid, ask):
    return bid is not None and ask is not None and 0 <= bid < ask <= 1 and ask - bid <= MAXQ


def look_ask(candles, kick):
    """Last valid candle ending at least LEAD s before kickoff. candles: (end_ts, bid, ask). Returns ask or None."""
    ok = sorted(r for r in candles if r[0] <= kick - LEAD and valid(r[1], r[2]))
    return ok[-1][2] if ok else None


def cheap(ask):
    return ask is not None and LO <= ask <= HI


def norm(t):
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", t)


def surname_key(title):
    """'Patrick Dorgu: 1+ goals' -> 'dorgu'."""
    name = title.split(":")[0].strip()
    return norm(name.split()[-1]) if name.split() else ""


def ticker_jersey(tk):
    m = re.search(r"-[A-Z]{3}[A-Z]+?(\d+)-\d+$", tk)
    return m.group(1) if m else None


def pos_group(name):
    n = (name or "").lower()
    if "goalkeeper" in n:
        return "G"
    if "midfielder" in n:
        return "M"
    if "defender" in n or "back" in n:
        return "D"
    if "forward" in n or "striker" in n or "winger" in n or "wing" in n:
        return "A"
    return "?"


def minutes_played(starter, sub_in_clock, sub_out_clock):
    """Minutes from roster clocks (seconds) if present; else 90 starter / 25 sub."""
    if starter:
        return min(90.0, sub_out_clock / 60.0) if sub_out_clock else 90.0
    if sub_in_clock is None and sub_out_clock is None:
        return 25.0
    return max(0.0, 90.0 - sub_in_clock / 60.0) if sub_in_clock else 25.0


def shrunk_rate(g, m, r_pos):
    return (g + K * r_pos) / (m / 90.0 + K)


def p_goal(rate, e_min):
    return 1 - math.exp(-rate * e_min / 90.0)


def pick_two_by_hash(rows):
    return sorted(rows, key=lambda r: sha(r["ticker"]))[:MAXPER]


def pick_two_by_ratio(rows):
    return sorted(rows, key=lambda r: -r["p"] / r["ask"])[:MAXPER]


def cluster_stats(trades, mult=1.0):
    """trades: dicts with ask, win, match, date. Returns n, mean, se_match, z (larger of match and date cluster), pf."""
    if not trades:
        return dict(n=0)
    xs = [net(t["win"], t["ask"], mult) for t in trades]
    n = len(xs)
    mu = sum(xs) / n
    out = dict(n=n, mean=mu, pf=pf(xs), win=sum(1 for t in trades if t["win"]) / n, ask=sum(t["ask"] for t in trades) / n)
    se = 0.0
    for key in ("match", "date"):
        g = defaultdict(float)
        for t, x in zip(trades, xs):
            g[t[key]] += x - mu
        s = math.sqrt(sum(v * v for v in g.values())) / n
        out["se_" + key] = s
        se = max(se, s)
    out["se"] = se
    out["z"] = mu / se if se > 0 else 0.0
    out["lo95"] = mu - 1.96 * out["se_match"]
    return out


def halves(trades):
    ds = sorted(t["kick"] for t in trades)
    if not ds:
        return [], []
    med = ds[len(ds) // 2]
    return [t for t in trades if t["kick"] < med], [t for t in trades if t["kick"] >= med]


def verdict(n, matches, h1, h2, pf_, lo95, beats_control=True):
    if n < 150 or matches < 60:
        return "NOT_ENOUGH_DATA"
    if pf_ < 1.5 or h1 <= 0 or h2 <= 0 or not beats_control:
        return "FALSIFIED"
    return "LEAD" if lo95 > 0 else "FALSIFIED"


# ----------------------------------------------------------------------------- io
def http(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40) as f:
                return json.load(f)
        except Exception:
            time.sleep(1.5 * (i + 1))
    return None


def db():
    CACHE.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(CACHE / "xi1.sqlite", timeout=120)
    c.executescript("""
CREATE TABLE IF NOT EXISTS fx(key TEXT PRIMARY KEY, lg TEXT, id TEXT, kick INTEGER, name TEXT);
CREATE TABLE IF NOT EXISTS ro(key TEXT, side TEXT, pid TEXT, jersey TEXT, starter INTEGER, pos TEXT, sin REAL, sout REAL, PRIMARY KEY(key,side,pid));
CREATE TABLE IF NOT EXISTS ath(pid TEXT PRIMARY KEY, name TEXT);
CREATE TABLE IF NOT EXISTS pos(pid TEXT PRIMARY KEY, name TEXT);
CREATE TABLE IF NOT EXISTS mk(ticker TEXT PRIMARY KEY, series TEXT, event TEXT, title TEXT, open_ts INTEGER, key TEXT, pid TEXT, starter INTEGER, grp TEXT);
CREATE TABLE IF NOT EXISTS goal(key TEXT, pid TEXT, n INTEGER, PRIMARY KEY(key,pid));
CREATE TABLE IF NOT EXISTS gdone(key TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, PRIMARY KEY(ticker,end_ts));
CREATE TABLE IF NOT EXISTS cdone(ticker TEXT PRIMARY KEY, n INTEGER);
CREATE TABLE IF NOT EXISTS res(ticker TEXT PRIMARY KEY, result TEXT);
""")
    return c


def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def cmd_espn():
    c = db()
    for lg in LEAGUES.values():
        d = http(f"{CORE}/{lg}/events?dates=20260828-20260921&limit=300")
        for x in d["items"]:
            e = x["$ref"].split("/events/")[1].split("?")[0]
            key = f"{lg}|{e}"
            if c.execute("SELECT 1 FROM fx WHERE key=?", (key,)).fetchone():
                continue
            comp = http(f"{CORE}/{lg}/events/{e}/competitions/{e}?lang=en")
            if not comp:
                continue
            kick = ts(comp["date"].replace("Z", ":00Z") if len(comp["date"]) == 17 else comp["date"])
            if kick >= ts("2026-10-03T16:00:00Z"):
                continue
            c.execute("INSERT OR REPLACE INTO fx VALUES(?,?,?,?,?)", (key, lg, e, kick, ""))
            for comp_c in comp["competitors"]:
                r = http(f"{CORE}/{lg}/events/{e}/competitions/{e}/competitors/{comp_c['id']}/roster")
                for en in (r or {}).get("entries", []):
                    pid = str(en["playerId"])
                    pr = en.get("position", {}).get("$ref", "")
                    posid = re.search(r"/positions/(\d+)", pr)
                    posid = posid.group(1) if posid else ""
                    sin = (en.get("subbedIn", {}).get("clock") or {}).get("value")
                    sout = (en.get("subbedOut", {}).get("clock") or {}).get("value")
                    c.execute("INSERT OR REPLACE INTO ro VALUES(?,?,?,?,?,?,?,?)", (key, comp_c["homeAway"], pid, str(en.get("jersey")), int(bool(en.get("starter"))), posid, sin, sout))
                    if posid and not c.execute("SELECT 1 FROM pos WHERE pid=?", (posid,)).fetchone():
                        pj = http(f"{CORE}/{lg}/positions/{posid}")
                        c.execute("INSERT OR REPLACE INTO pos VALUES(?,?)", (posid, (pj or {}).get("name", "")))
                    if not c.execute("SELECT 1 FROM ath WHERE pid=?", (pid,)).fetchone():
                        aj = http(f"{CORE}/{lg}/seasons/2026/athletes/{pid}")
                        if aj:
                            c.execute("INSERT OR REPLACE INTO ath VALUES(?,?)", (pid, aj.get("displayName") or aj.get("fullName") or ""))
            c.commit()
            print(key, flush=True)
    c.commit()


def cmd_join():
    """Kalshi market list (tickers, titles, open time only; NO result) joined to ESPN fixtures by surname + jersey."""
    from . import api
    c = db()
    lo, cut = ts("2026-08-01T00:00:00Z"), ts("2026-10-03T16:00:00Z")
    mk = defaultdict(list)
    for ser in LEAGUES:
        for m in api.settled_markets(ser, lo, cut):
            if m.get("floor_strike") != 0.5:
                continue
            mk[m["event_ticker"]].append((m["ticker"], ser, m["title"], ts(m["open_time"])))
    fxs = {r[0]: (r[1], r[2]) for r in c.execute("SELECT key,lg,kick FROM fx")}
    ro = defaultdict(list)
    for key, pid, jersey, st, pos in c.execute("SELECT key,pid,jersey,starter,pos FROM ro"):
        ro[key].append((pid, jersey, st, pos))
    names = {p: n for p, n in c.execute("SELECT pid,name FROM ath")}
    posname = {p: n for p, n in c.execute("SELECT pid,name FROM pos")}
    joined = dropped = 0
    for ev, rows in sorted(mk.items()):
        ser = rows[0][1]
        lg = LEAGUES[ser]
        d = datetime.strptime(re.search(r"-(\d\d[A-Z]{3}\d\d)", ev).group(1), "%y%b%d").replace(tzinfo=timezone.utc).timestamp() + 12 * 3600
        best = (0, None)
        for key, (flg, kick) in fxs.items():
            if flg != lg or abs(kick - d) > 36 * 3600:
                continue
            idx = {(norm(names.get(p, "").split()[-1] if names.get(p, "") else ""), j): (p, st, pos) for p, j, st, pos in ro[key]}
            hit = sum(1 for tk, _, title, _ in rows if (surname_key(title), ticker_jersey(tk)) in idx)
            if hit > best[0]:
                best = (hit, key)
        if best[0] < 12:
            dropped += 1
            continue
        key = best[1]
        idx = {(norm(names.get(p, "").split()[-1] if names.get(p, "") else ""), j): (p, st, pos) for p, j, st, pos in ro[key]}
        joined += 1
        for tk, ser, title, ots in rows:
            hit = idx.get((surname_key(title), ticker_jersey(tk)))
            if not hit:
                continue
            c.execute("INSERT OR REPLACE INTO mk VALUES(?,?,?,?,?,?,?,?,?)", (tk, ser, ev, title, ots, key, hit[0], hit[1], pos_group(posname.get(hit[2], ""))))
    c.commit()
    print("events joined", joined, "dropped", dropped, flush=True)


def fit_split(c):
    keys = [r[0] for r in c.execute("SELECT DISTINCT m.key FROM mk m JOIN fx f ON f.key=m.key ORDER BY f.kick, f.id")]
    k = (2 * len(keys)) // 3
    return keys[:k], keys[k:]


def cmd_fit():
    """ESPN scoring plays for the FIT matches only (own goals excluded)."""
    c = db()
    fit, _ = fit_split(c)
    for key in fit:
        if c.execute("SELECT 1 FROM gdone WHERE key=?", (key,)).fetchone():
            continue
        lg, e = key.split("|")
        base = f"{CORE}/{lg}/events/{e}/competitions/{e}/plays"
        page, n, ok = 1, 0, True
        while True:
            d = http(f"{base}?limit=1000&page={page}&lang=en")
            if not d:
                ok = False
                break
            for it in d["items"]:
                if it.get("scoringPlay") and not it.get("ownGoal") and "own" not in (it.get("type", {}).get("text", "").lower()):
                    for p in it.get("participants", [])[:1]:
                        pid = re.search(r"/athletes/(\d+)", p["athlete"]["$ref"]).group(1)
                        c.execute("INSERT INTO goal VALUES(?,?,1) ON CONFLICT(key,pid) DO UPDATE SET n=n+1", (key, pid))
            if page >= d.get("pageCount", 1):
                break
            page += 1
        if ok:
            c.execute("INSERT OR REPLACE INTO gdone VALUES(?)", (key,))
            c.commit()
        print("fit", key, ok, flush=True)


def cmd_candles(minutes):
    from . import api
    c = db()
    t_end = time.time() + 60 * minutes
    kick = {r[0]: r[1] for r in c.execute("SELECT key,kick FROM fx")}
    byk = defaultdict(list)
    for tk, key, ots in c.execute("SELECT ticker,key,open_ts FROM mk WHERE starter=1"):
        if ots <= kick[key] - EARLY:
            byk[key].append((tk, ots))
    order = sorted(byk, key=lambda k: md5(k.split("|")[1]))
    print("matches", len(order), "markets", sum(len(v) for v in byk.values()), flush=True)
    ok = fail = 0
    for pas in range(4):
        pending = [k for k in order if any(not c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone() for tk, _ in byk[k])]
        print("pass", pas, "incomplete", len(pending), flush=True)
        if not pending:
            break
        for k in pending:
            todo = [(tk, ots) for tk, ots in byk[k] if not c.execute("SELECT 1 FROM cdone WHERE ticker=?", (tk,)).fetchone()]
            if time.time() > t_end:
                print("time box reached", flush=True)
                c.commit()
                return
            # AMENDMENT (documented in the result): one live batch request per match (identical quotes to the single-market endpoints,
            # checked on one match) because the single-market endpoints ran at about 4 a minute under the shared limit.
            b = None
            for a in range(8):
                try:
                    b = api.batch_candlesticks([tk for tk, _ in todo], min(o for _, o in todo), kick[k] - LEAD)
                    break
                except Exception:  # noqa: BLE001
                    time.sleep(min(60, 5 + 8 * a))
            time.sleep(3)
            if b is None:
                fail += len(todo)
                continue
            for tk, ots in todo:
                cs = b.get(tk, [])
                ok += 1
                for x in cs:
                    c.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
                c.execute("INSERT OR REPLACE INTO cdone VALUES(?,?)", (tk, len(cs)))
            c.commit()
            print("pass", pas, k, "ok", ok, "fail", fail, flush=True)
    print("candles done; ok", ok, "fail", fail, flush=True)


def cmd_results():
    """Kalshi settled result per joined market (read once, after registration)."""
    from . import api
    c = db()
    lo, cut = ts("2026-08-01T00:00:00Z"), ts("2026-10-03T16:00:00Z")
    have = {r[0] for r in c.execute("SELECT ticker FROM mk")}
    for ser in LEAGUES:
        for m in api.settled_markets(ser, lo, cut):
            if m["ticker"] in have:
                c.execute("INSERT OR REPLACE INTO res VALUES(?,?)", (m["ticker"], m.get("result")))
    c.commit()
    print("results", c.execute("SELECT COUNT(*), SUM(result='yes') FROM res").fetchone(), flush=True)


def model_params(c, fit):
    """Per-player rate and per-group (r_pos, e_min) from FIT matches only."""
    posname = {p: n for p, n in c.execute("SELECT pid,name FROM pos")}
    goals = {(k, p): n for k, p, n in c.execute("SELECT key,pid,n FROM goal")}
    g, m = defaultdict(float), defaultdict(float)
    grp_g, grp_m, st_min = defaultdict(float), defaultdict(float), defaultdict(list)
    for key in fit:
        for pid, st, pos, sin, sout in c.execute("SELECT pid,starter,pos,sin,sout FROM ro WHERE key=?", (key,)):
            grp = pos_group(posname.get(pos, ""))
            if grp not in ("A", "M"):
                continue
            mins = minutes_played(bool(st), sin, sout)
            gg = goals.get((key, pid), 0)
            g[pid] += gg
            m[pid] += mins
            grp_g[grp] += gg
            grp_m[grp] += mins
            if st:
                st_min[grp].append(mins)
    r_pos = {k: grp_g[k] / (grp_m[k] / 90.0) for k in grp_m if grp_m[k] > 0}
    e_min = {k: sum(v) / len(v) for k, v in st_min.items() if v}
    return g, m, r_pos, e_min


def cmd_score():
    c = db()
    fit, test = fit_split(c)
    kick = {r[0]: r[1] for r in c.execute("SELECT key,kick FROM fx")}
    g, m, r_pos, e_min = model_params(c, fit)
    cdone = {r[0] for r in c.execute("SELECT ticker FROM cdone")}
    res = {r[0]: r[1] for r in c.execute("SELECT ticker,result FROM res")}
    cand = defaultdict(lambda: defaultdict(list))
    for ev_ in c.execute("SELECT ticker,candle.end_ts,bid,ask FROM candle JOIN mk USING(ticker)"):
        cand[ev_[0]][0].append((ev_[1], ev_[2], ev_[3]))
    byk = defaultdict(list)
    for tk, key, ots, grp, pid, ser, ev in c.execute("SELECT ticker,key,open_ts,grp,pid,series,event FROM mk WHERE starter=1"):
        if ots <= kick[key] - EARLY:
            byk[key].append(dict(ticker=tk, key=key, grp=grp, pid=pid, ser=ser, ev=ev))
    order = sorted(byk, key=lambda k: md5(k.split("|")[1]))
    prefix = []
    for k in order:
        if all(r["ticker"] in cdone for r in byk[k]):
            prefix.append(k)
        else:
            break
    out = dict(matches_joined=len(set(r[0] for r in c.execute("SELECT key FROM mk"))), fit_matches=len(fit), test_matches=len(test),
               matches_with_eligible_markets=len(order), prefix_matches=len(prefix), r_pos=r_pos, e_min=e_min)
    rows = []
    unavailable = 0
    for k in prefix:
        for r in byk[k]:
            ask = look_ask(cand[r["ticker"]][0], kick[k])
            if ask is None:
                unavailable += 1
                continue
            res_ = res.get(r["ticker"])
            if res_ not in ("yes", "no"):
                continue
            r.update(ask=ask, win=res_ == "yes", kick=kick[k], match=k, date=(kick[k] - 5 * 3600) // 86400)
            if r["grp"] in ("A", "M"):
                rate = shrunk_rate(g.get(r["pid"], 0.0), m.get(r["pid"], 0.0), r_pos.get(r["grp"], 0.0))
                r["p"] = p_goal(rate, e_min.get(r["grp"], 80.0))
            rows.append(r)
    out["unavailable_no_valid_look"] = unavailable
    cheapr = [r for r in rows if cheap(r["ask"])]
    out["rows_with_look"] = len(rows)
    out["cheap_rows"] = len(cheapr)
    pm = defaultdict(list)
    for r in cheapr:
        pm[r["match"]].append(r)
    U = [t for k, v in pm.items() for t in pick_two_by_hash(v)]
    tset = set(test)
    ctrl = [r for r in cheapr if r["key"] in tset and r["grp"] in ("A", "M")]
    tm = defaultdict(list)
    for r in ctrl:
        if r["p"] >= RATIO * r["ask"]:
            tm[r["match"]].append(r)
    M = [t for v in tm.values() for t in pick_two_by_ratio(v)]
    tr_all = [r for r in ctrl if r["p"] >= RATIO * r["ask"]]

    def block(name, T):
        h1, h2 = halves(T)
        st = cluster_stats(T)
        d = dict(stats=st, stats_x12=cluster_stats(T, 1.2), h1=cluster_stats(h1), h2=cluster_stats(h2), matches=len({t["match"] for t in T}))
        out[name] = d
        return d

    bu = block("U", U)
    block("M", M)
    block("M_uncapped", tr_all)
    block("control", ctrl)
    block("U_uncapped", cheapr)
    for lo_, hi_ in ((0.03, 0.10), (0.10, 0.20), (0.20, 0.301)):
        b = [r for r in cheapr if lo_ <= r["ask"] < hi_]
        out[f"bucket_{lo_}"] = dict(n=len(b), win=sum(r["win"] for r in b) / max(1, len(b)), ask=sum(r["ask"] for r in b) / max(1, len(b)))
    out["by_league"] = {s: cluster_stats([t for t in U if t["ser"] == s]) for s in LEAGUES}
    out["by_group"] = {gp: cluster_stats([r for r in cheapr if r["grp"] == gp]) for gp in "AMDG?"}
    gaps = sorted(r["p"] - r["ask"] for r in ctrl)
    if gaps:
        out["gap_model_minus_ask"] = dict(n=len(gaps), median=gaps[len(gaps) // 2], p90=gaps[int(0.9 * len(gaps))])
    lad = defaultdict(lambda: [0.0, 0, 0])
    for r in rows:
        x = lad[r["match"]]
        x[0] += r["ask"]
        x[1] += 1
        x[2] += int(r["win"])
    out["ladder"] = dict(matches=len(lad), mean_sum_asks=sum(x[0] for x in lad.values()) / max(1, len(lad)),
                         mean_scorers=sum(x[2] for x in lad.values()) / max(1, len(lad)), mean_rungs=sum(x[1] for x in lad.values()) / max(1, len(lad)))
    for nm in ("U", "M"):
        d = out[nm]
        st = d["stats"]
        if st["n"]:
            bc = nm == "U" or (out["control"]["stats"]["n"] > 0 and st["mean"] > out["control"]["stats"]["mean"])
            d["verdict"] = verdict(st["n"], d["matches"], d["h1"].get("mean", 0), d["h2"].get("mean", 0), st["pf"], st["lo95"], bc)
        else:
            d["verdict"] = "NOT_ENOUGH_DATA"
    json.dump(out, open(CACHE / "xi1_result.json", "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1]
    {"espn": cmd_espn, "join": cmd_join, "fit": cmd_fit, "results": cmd_results, "score": cmd_score}.get(cmd, lambda: cmd_candles(float(sys.argv[2])) if cmd == "candles" else None)()
