"""SOCCER1: Kalshi soccer cheap side vs DraftKings (via ESPN core odds), de-vigged. Held to settlement.

Registration: workers/SOCCER1_REGISTRATION.md.  Cheap side only (ask 3c-30c): no favourite-side result is computed.
Frozen W3 (start from 2026-10-03T16:00Z) is never fetched or joined.  Cache outside the repo (SOCCER1_CACHE).
Usage: python -m scalper.soccer1 census|probe   (outcome-free steps); later steps are added after registration.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
import unicodedata
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CACHE = Path(os.environ.get("SOCCER1_CACHE", "/tmp/soccer1"))
W3_START = int(datetime(2026, 10, 3, 16, tzinfo=timezone.utc).timestamp())
LO_TS = int(datetime(2026, 8, 1, tzinfo=timezone.utc).timestamp())
LO, HI, RATIO, C, LEAD, MAXQ = 0.03, 0.30, 3.0, 10, 120, 0.10
UA = "research-bot SOCCER1 (kalshi research)"
# kalshi series prefix -> espn league slug
LEAGUES = {"EPL": "eng.1", "LALIGA": "esp.1", "SERIEA": "ita.1", "BUNDESLIGA": "ger.1", "LIGUE1": "fra.1",
           "UCL": "uefa.champions", "UEL": "uefa.europa", "UECL": "uefa.europa.conf", "MLS": "usa.1",
           "EFLCHAMPIONSHIP": "eng.2", "EREDIVISIE": "ned.1", "LIGAPORTUGAL": "por.1", "LIGAMX": "mex.1"}
FAMS = ("GAME", "TOTAL", "BTTS", "SPREAD")


def fee(p, c=C):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win, ask, mult=1.0):
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def implied(american):
    a = float(american)
    return 100 / (a + 100) if a > 0 else -a / (-a + 100)


def devig3(h, d, a):
    """Proportional de-vig of a three-way moneyline (American odds)."""
    ps = [implied(h), implied(d), implied(a)]
    s = sum(ps)
    return [p / s for p in ps]


def devig2(over, under):
    po, pu = implied(over), implied(under)
    return po / (po + pu)


def valid(q):
    return q is not None and 0 <= q[0] < q[1] <= 1 and q[1] - q[0] <= MAXQ


def look(cands, start):
    ts = [t for t, q in cands.items() if t <= start - LEAD and valid(q)]
    return cands[max(ts)] if ts else None


def cheap_side(q):
    bid, ask = q
    if LO <= ask <= HI:
        return "Y", ask
    if LO <= 1 - bid <= HI:
        return "N", 1 - bid
    return None


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf")


def http(url):
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(5):
        try:
            with urllib.request.urlopen(r, timeout=20) as f:
                return json.load(f)
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def census():
    """Listings and close times only: settled soccer markets closing before the frozen cut, by league and family. No results kept."""
    from . import api
    out = CACHE / "census.json"
    have = json.load(open(out)) if out.exists() else {}
    for pre in LEAGUES:
        for fam in FAMS:
            ser = f"KX{pre}{fam}"
            if ser in have:
                continue
            ev, n = {}, 0
            for m in api.settled_markets(ser, LO_TS, W3_START):
                n += 1
                ev.setdefault(m["event_ticker"], m.get("close_time"))
            have[ser] = dict(markets=n, events=ev)
            json.dump(have, open(out, "w"))
            print(ser, n, len(ev), flush=True)
            time.sleep(0.5)
    tot = defaultdict(int)
    for ser, v in have.items():
        pre = ser[2:].rsplit("GAME", 1)[0] if ser.endswith("GAME") else None
    for pre in LEAGUES:
        g = have.get(f"KX{pre}GAME", {})
        print(pre, "match events", len(g.get("events", {})), {f: have.get(f"KX{pre}{f}", {}).get("markets") for f in FAMS})


# ---------------------------------------------------------------- ESPN (core API, 1 request per second)

ESPN_DATES = "20260825-20261002"  # all before the frozen cut by date; Oct 3 is left out on purpose
CORE = "https://sports.core.api.espn.com/v2/sports/soccer/leagues"


def _norm(t):
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return " ".join(w for w in t.split() if w not in ("fc", "afc", "cf", "sc", "ac", "as", "ud", "cd", "club", "de", "the"))


def same_team(a, b):
    a, b = _norm(a), _norm(b)
    return bool(a and b and (a == b or a in b or b in a))


def espn():
    """Event ids, names, start times and DraftKings odds for matches before the frozen cut. Cached per event."""
    out = CACHE / "espn.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(l)["key"] for l in open(out)}
    f = open(out, "a")
    for pre, lg in LEAGUES.items():
        d = http(f"{CORE}/{lg}/events?dates={ESPN_DATES}&limit=300")
        time.sleep(1)
        ids = [x["$ref"].split("/events/")[1].split("?")[0] for x in (d or {}).get("items", [])]
        print(lg, len(ids), flush=True)
        for e in ids:
            key = f"{lg}|{e}"
            if key in done:
                continue
            ev = http(f"{CORE}/{lg}/events/{e}")
            time.sleep(1)
            if not ev:
                continue
            c = ev["competitions"][0]
            start = int(datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).timestamp())
            if start >= W3_START:  # frozen: nothing more is fetched
                continue
            o = http(f"{CORE}/{lg}/events/{e}/competitions/{e}/odds")
            time.sleep(1)
            it = [i for i in (o or {}).get("items", []) if i.get("provider", {}).get("name") == "DraftKings"]
            odds = None
            if it:
                i = it[0]
                try:
                    odds = dict(h=i["homeTeamOdds"]["moneyLine"], a=i["awayTeamOdds"]["moneyLine"], d=i["drawOdds"]["moneyLine"],
                                ou=i.get("overUnder"), ov=i.get("overOdds"), un=i.get("underOdds"))
                except (KeyError, TypeError):
                    odds = None
            names = ev["name"].split(" at ")
            f.write(json.dumps(dict(key=key, lg=lg, pre=pre, id=e, start=start, away=names[0] if len(names) == 2 else None,
                                    home=names[1] if len(names) == 2 else None, short=ev.get("shortName"), odds=odds)) + "\n")
            f.flush()
    f.close()


def markets():
    """Kalshi GAME and TOTAL settled market lists (structure and results; the result field is read only by score)."""
    from . import api
    out = CACHE / "markets.jsonl"
    f = open(out, "w")
    for pre in LEAGUES:
        for fam in ("GAME", "TOTAL"):
            ser = f"KX{pre}{fam}"
            n = 0
            for m in api.settled_markets(ser, LO_TS, W3_START):
                f.write(json.dumps(dict(pre=pre, fam=fam, ticker=m["ticker"], event=m["event_ticker"], sub=m.get("yes_sub_title"),
                                        k=m.get("floor_strike"), result=m.get("result"), close=m.get("close_time"))) + "\n")
                n += 1
            print(ser, n, flush=True)
            time.sleep(0.5)
    f.close()


def _event_date(ev):
    m = re.search(r"-(\d\d)([A-Z]{3})(\d\d)", ev)
    return datetime.strptime(m.group(1) + m.group(2) + m.group(3), "%y%b%d").replace(tzinfo=timezone.utc).date()


def join():
    """Kalshi match event -> ESPN event with odds. Returns list of dict(event, pre, start, odds, game markets, total markets)."""
    es = [json.loads(l) for l in open(CACHE / "espn.jsonl")]
    by = defaultdict(list)
    for r in es:
        if r["odds"] and r["home"]:
            by[r["pre"]].append(r)
    ev = defaultdict(lambda: dict(game=[], total=[]))
    for l in open(CACHE / "markets.jsonl"):
        m = json.loads(l)
        ev[(m["pre"], m["event"])]["game" if m["fam"] == "GAME" else "total"].append(m)
    out, unmatched = [], 0
    games = {k: v for k, v in ev.items() if k[1].startswith(f"KX{k[0]}GAME")}
    totals = defaultdict(list)
    for (pre, e), v in ev.items():
        if e.startswith(f"KX{pre}TOTAL"):
            totals[(pre, e.split("-", 1)[1])] = v["total"]
    for (pre, e), v in games.items():
        d = _event_date(e)
        teams = [m for m in v["game"] if m["sub"] != "Tie"]
        hit = None
        for r in by[pre]:
            rd = datetime.fromtimestamp(r["start"], timezone.utc).date()
            if abs((rd - d).days) > 1:
                continue
            if all(any(same_team(m["sub"], x) for x in (r["home"], r["away"])) for m in teams) and len(teams) == 2:
                hit = r
                break
        if not hit:
            unmatched += 1
            continue
        out.append(dict(event=e, pre=pre, start=hit["start"], home=hit["home"], away=hit["away"], odds=hit["odds"],
                        game=v["game"], total=totals.get((pre, e.split("-", 1)[1]), [])))
    print("kalshi match events", len(games), "joined", len(out), "unmatched", unmatched, flush=True)
    return out


def _book(r):
    """Per market ticker -> (side-of-YES book probability). G: home/draw/away; T: over at the book's own K.5 line."""
    o = r["odds"]
    qh, qd, qa = devig3(o["h"], o["d"], o["a"])
    q = {}
    for m in r["game"]:
        if m["sub"] == "Tie":
            q[m["ticker"]] = ("G", qd)
        elif same_team(m["sub"], r["home"]):
            q[m["ticker"]] = ("G", qh)
        elif same_team(m["sub"], r["away"]):
            q[m["ticker"]] = ("G", qa)
    ou = o.get("ou")
    if ou and o.get("ov") and o.get("un") and abs(ou - math.floor(ou) - 0.5) < 1e-9:
        for m in r["total"]:
            if m["k"] is not None and abs(float(m["k"]) - ou) < 1e-9:
                q[m["ticker"]] = ("T", devig2(o["ov"], o["un"]))
    return q


def candles():
    from . import api, backfill
    from concurrent.futures import ThreadPoolExecutor
    rows = join()
    outp = CACHE / "candles.jsonl"
    done = set()
    if outp.exists():
        done = {json.loads(l)["key"] for l in open(outp)}
    jobs = []
    for r in rows:
        tks = sorted(_book(r))
        for i in range(0, len(tks), 8):
            key = f"{r['event']}|{i}"
            if key not in done:
                jobs.append((key, r["start"], tks[i:i + 8]))
    print("jobs", len(jobs), flush=True)
    fh = open(outp, "a")

    def run(job):
        key, st, tks = job
        got = api.batch_candlesticks(tks, st - 6 * 3600, st - 60)
        return key, got

    with ThreadPoolExecutor(2) as ex:
        for key, got in ex.map(run, jobs):
            fh.write(json.dumps(dict(key=key, c={t: [(c.get("end_period_ts"), backfill._d(c.get("yes_bid"), "close_dollars"),
                                                       backfill._d(c.get("yes_ask"), "close_dollars")) for c in cs] for t, cs in got.items()})) + "\n")
            fh.flush()
            time.sleep(0.4)
    fh.close()


def zstat(per):
    n = len(per)
    if n < 3:
        return None
    m = sum(per) / n
    v = sum((x - m) ** 2 for x in per) / (n - 1)
    return m / math.sqrt(v / n) if v > 0 else None


def score():
    """One run, all registered statistics. Cheap side only: no favourite-side figure is computed."""
    rows = join()
    cand = defaultdict(dict)
    for l in open(CACHE / "candles.jsonl"):
        for t, cs in json.loads(l)["c"].items():
            for ts, b, a in cs:
                if b is not None and a is not None:
                    cand[t][ts] = (b, a)
    res = {}
    for l in open(CACHE / "markets.jsonl"):
        m = json.loads(l)
        res[m["ticker"]] = m["result"]
    W1 = int(datetime(2026, 9, 13, 1, tzinfo=timezone.utc).timestamp())
    allr, nolook, noprice = [], 0, 0
    for r in rows:
        bk = _book(r)
        for t, (fam, q) in bk.items():
            lk = look(cand.get(t, {}), r["start"])
            if lk is None:
                nolook += 1
                continue
            cs = cheap_side(lk)
            if cs is None:
                continue
            side, ask = cs
            if res.get(t) not in ("yes", "no"):
                noprice += 1
                continue
            qs = q if side == "Y" else 1 - q
            win = (res[t] == "yes") == (side == "Y")
            allr.append(dict(fam=fam, ev=r["event"], t=t, st=r["start"], ask=ask, q=qs, win=win, w=1 if r["start"] < W1 else 2, pre=r["pre"]))
    out = []
    P = out.append
    P(f"matches joined {len(rows)}; markets with book price and no valid look {nolook}; unresolved {noprice}; cheap outcomes (control) {len(allr)}")
    for fam in ("G", "T", "all"):
        rr = [x for x in allr if fam == "all" or x["fam"] == fam]
        if not rr:
            P(f"{fam}: no cheap outcomes")
            continue
        gaps = sorted(x["q"] - x["ask"] for x in rr)
        n = len(gaps)
        P(f"{fam}: cheap n {n} ({len({x['ev'] for x in rr})} matches); gap q-ask median {gaps[n//2]*100:+.2f}c p90 {gaps[9*n//10]*100:+.2f}c")
        xs = [net(x["win"], x["ask"]) for x in rr]
        byev = defaultdict(float)
        for x, v in zip(rr, xs):
            byev[x["ev"]] += v
        P(f"  control: win {sum(x['win'] for x in rr)/n:.3f} vs ask {sum(x['ask'] for x in rr)/n:.3f} vs q {sum(x['q'] for x in rr)/n:.3f}; mean net {sum(xs)/n*100:+.2f}c; PF {pf(xs):.2f}; z(match) {zstat(list(byev.values()))}")
        for lo, hi in ((0.03, 0.10), (0.10, 0.20), (0.20, 0.30001)):
            b = [x for x in rr if lo <= x["ask"] < hi]
            if b:
                P(f"  ask {lo*100:.0f}-{hi*100:.0f}c n {len(b)}: win {sum(x['win'] for x in b)/len(b):.3f} vs ask {sum(x['ask'] for x in b)/len(b):.3f} vs q {sum(x['q'] for x in b)/len(b):.3f}")
    # treated: q >= 3 x ask, at most 2 per match (largest q/ask)
    by = defaultdict(list)
    for x in allr:
        if x["q"] >= RATIO * x["ask"]:
            by[x["ev"]].append(x)
    tr = []
    for e, l in by.items():
        tr += sorted(l, key=lambda x: -x["q"] / x["ask"])[:2]
    tr.sort(key=lambda x: x["st"])
    xs = [net(x["win"], x["ask"]) for x in tr]
    P(f"treated (q >= {RATIO:g} x ask): n {len(tr)} in {len(by)} matches (G {sum(x['fam']=='G' for x in tr)}, T {sum(x['fam']=='T' for x in tr)})")
    if tr:
        h = len(tr) // 2
        P(f"  win {sum(x['win'] for x in tr)/len(tr):.3f} vs ask {sum(x['ask'] for x in tr)/len(tr):.3f} vs q {sum(x['q'] for x in tr)/len(tr):.3f}; mean net {sum(xs)/len(xs)*100:+.2f}c; PF {pf(xs):.2f}; fees x1.2 {sum(net(x['win'],x['ask'],1.2) for x in tr)/len(tr)*100:+.2f}c")
        P(f"  half1 {sum(xs[:h])/max(1,h)*100:+.2f}c (n {h}); half2 {sum(xs[h:])/max(1,len(xs)-h)*100:+.2f}c (n {len(xs)-h})")
    if len(tr) < 150:
        rate = len(tr) / 1.3
        P(f"NOT_ENOUGH_DATA: {len(tr)} of 150; rate {rate:.1f}/month over the 1.3 month window; " + (f"about {(150-len(tr))/rate:.0f} more months" if rate > 0 else "no rate to extrapolate"))
    print("\n".join(out))
    open(CACHE / "result.txt", "w").write("\n".join(out))
    return out


if __name__ == "__main__":
    CACHE.mkdir(parents=True, exist_ok=True)
    import sys
    globals()[sys.argv[1]]()
