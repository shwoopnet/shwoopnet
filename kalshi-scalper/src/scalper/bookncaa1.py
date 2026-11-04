"""BOOKNCAA1: college basketball cheap side vs DraftKings de-vigged closing moneyline, held to settlement.

Registration: workers/BOOKNCAA1_REGISTRATION.md.  Cheap side only: no favourite-side result is computed.
Stages (each a CLI verb): games (census list), scoreboards, odds, candles, entries, results (only after entries are hashed), score.
Cache lives outside the repo (BOOKNCAA1_CACHE, default /tmp/bookncaa1).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CACHE = Path(os.environ.get("BOOKNCAA1_CACHE", "/tmp/bookncaa1"))
CUT = "2026-10-03T16:00:00Z"
LO, HI, RATIO, C, LEAD, MAXQ = 0.03, 0.30, 3.0, 10, 120, 0.45
UA = "research-bot BOOKNCAA1 (kalshi research)"
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
BUCKETS = [(0.03, 0.05), (0.05, 0.10), (0.10, 0.15), (0.15, 0.20), (0.20, 0.30001)]


def fee(p, c=C):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win, ask, mult=1.0):
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def implied(ml):
    ml = float(ml)
    return 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)


def devig(ml_home, ml_away):
    h, a = implied(ml_home), implied(ml_away)
    return h / (h + a), a / (h + a)


def valid(q):
    return q is not None and 0 <= q[0] < q[1] <= 1 and q[1] - q[0] <= 0.10


def look(candles, start):
    """candles: {end_ts: (bid, ask)}.  Last valid candle ending at or before start-LEAD."""
    ts = [t for t, q in candles.items() if t <= start - LEAD and valid(q)]
    return max(ts) if ts else None


def parse_event(ev):
    """'KXNCAAMBGAME-26JAN15GONZWSU' -> ('20260115', 'GONZWSU')."""
    m = re.match(r"(\d\d)([A-Z]{3})(\d\d)(.*)", ev.split("-", 1)[1])
    return f"20{m.group(1)}{MON[m.group(2)]:02d}{m.group(3)}", m.group(4)


def match_game(code, games):
    """games: list of dict(id,a,h).  Returns (game, away_code, home_code, how) or None.  Primary: exact concat.
    Fallback (unique per date): code starts with away abbrev or ends with home abbrev."""
    hit = [g for g in games if g["a"] + g["h"] == code]
    if len(hit) == 1:
        g = hit[0]
        return g, g["a"], g["h"], "exact"
    if hit:
        return None
    fb = [g for g in games if code.startswith(g["a"]) or code.endswith(g["h"])]
    if len(fb) != 1:
        return None
    g = fb[0]
    if code.startswith(g["a"]):
        return g, g["a"], code[len(g["a"]):], "fallback"
    return g, code[: len(code) - len(g["h"])], g["h"], "fallback"


def underdog(ml_home, ml_away):
    """('H'|'A', q_underdog) or None for a tie or a pick-em beyond MAXQ."""
    qh, qa = devig(ml_home, ml_away)
    if qh == qa:
        return None
    side, q = ("H", qh) if qh < qa else ("A", qa)
    return (side, q) if q <= MAXQ else None


def moneylines(path):
    try:
        d = json.load(open(path))
    except Exception:
        return None
    for it in d.get("items", []):
        try:
            return (float(it["homeTeamOdds"]["close"]["moneyLine"]["american"]),
                    float(it["awayTeamOdds"]["close"]["moneyLine"]["american"]))
        except Exception:
            continue
    return None


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf")


def zstat(xs):
    n = len(xs)
    if n < 3:
        return None
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    return m / math.sqrt(v / n) if v > 0 else None


def score(rows):
    """rows: dict(ask,q,win,st).  Returns report lines.  Cheap candidates only."""
    out = []
    n = len(rows)
    out.append(f"candidates (book underdog with a valid look and ask in [{LO},{HI}]): {n}")
    if not n:
        return out
    gaps = sorted(r["q"] - r["ask"] for r in rows)
    out.append(f"gap q-ask: median {gaps[n // 2] * 100:+.2f}c p90 {gaps[9 * n // 10] * 100:+.2f}c")
    xs = [net(r["win"], r["ask"]) for r in rows]
    out.append(f"control: n {n} win {sum(r['win'] for r in rows) / n:.3f} vs mean ask {sum(r['ask'] for r in rows) / n:.3f} vs mean q {sum(r['q'] for r in rows) / n:.3f}; mean net {sum(xs) / n * 100:+.2f}c PF {pf(xs):.2f}")
    for lo, hi in BUCKETS:
        b = [r for r in rows if lo <= r["ask"] < hi]
        if b:
            out.append(f"  ask {lo:.2f}-{min(hi, .30):.2f}: n {len(b)} win {sum(r['win'] for r in b) / len(b):.3f} vs ask {sum(r['ask'] for r in b) / len(b):.3f} vs q {sum(r['q'] for r in b) / len(b):.3f}; net {sum(net(r['win'], r['ask']) for r in b) / len(b) * 100:+.2f}c")
    tr = sorted([r for r in rows if r["q"] >= RATIO * r["ask"]], key=lambda r: r["st"])
    tx = [net(r["win"], r["ask"]) for r in tr]
    out.append(f"treated (q >= {RATIO:g} x ask): n {len(tr)}")
    if tr:
        h = len(tr) // 2
        out.append(f"  win {sum(r['win'] for r in tr) / len(tr):.3f} vs mean ask {sum(r['ask'] for r in tr) / len(tr):.3f}; mean net {sum(tx) / len(tx) * 100:+.2f}c; PF {pf(tx):.2f}; fees x1.2 {sum(net(r['win'], r['ask'], 1.2) for r in tr) / len(tr) * 100:+.2f}c; z {zstat(tx)}")
        out.append(f"  D1 mean {sum(tx[:h]) / max(1, h) * 100:+.2f}c (n {h}); D2 mean {sum(tx[h:]) / max(1, len(tx) - h) * 100:+.2f}c (n {len(tx) - h})")
        rest = [net(r["win"], r["ask"]) for r in rows if r["q"] < RATIO * r["ask"]]
        if rest:
            out.append(f"  treated minus untreated candidates {(sum(tx) / len(tx) - sum(rest) / len(rest)) * 100:+.2f}c")
    if len(tr) < 150:
        out.append(f"NOT_ENOUGH_DATA: {len(tr)} treated of 150 (one season in the file)")
    return out


# ---------------------------------------------------------------- fetching

def http(url):
    for i in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30))
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def md5key(e):
    return hashlib.md5(e.encode()).hexdigest()


def events():
    c = json.load(open("/tmp/bookncaa1_census.json"))
    return sorted({r[1] for r in c["KXNCAAMBGAME_hist"] if r[2] < CUT}, key=md5key)


def scoreboard(d):
    p = CACHE / "sb" / f"{d}.json"
    if p.exists():
        return json.load(open(p))
    j = http(f"https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={d}&groups=50&limit=400")
    time.sleep(1.0)
    if not j:
        return None
    ev = []
    for e in j.get("events", []):
        cp = e["competitions"][0]["competitors"]
        ev.append(dict(id=e["id"], date=e["date"],
                       a=[x["team"]["abbreviation"] for x in cp if x["homeAway"] == "away"][0],
                       h=[x["team"]["abbreviation"] for x in cp if x["homeAway"] == "home"][0]))
    json.dump(ev, open(p, "w"))
    return ev


def start_ts(iso):
    return int(datetime.strptime(iso, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc).timestamp())


def stage_odds(box):
    (CACHE / "odds").mkdir(parents=True, exist_ok=True)
    (CACHE / "sb").mkdir(parents=True, exist_ok=True)
    t0, games = time.time(), {}
    for e in events():
        if time.time() - t0 > box:
            break
        d, code = parse_event(e)
        ev = scoreboard(d)
        m = match_game(code, ev or [])
        if not m:
            games[e] = None
            continue
        g, ac, hc, how = m
        p = CACHE / "odds" / f"{g['id']}.json"
        if not p.exists():
            j = http(f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/{g['id']}/competitions/{g['id']}/odds")
            time.sleep(1.0)
            if j is not None:
                json.dump(j, open(p, "w"))
        games[e] = dict(gid=g["id"], st=start_ts(g["date"]), ac=ac, hc=hc, how=how)
        if len(games) % 50 == 0:
            json.dump(games, open(CACHE / "games.json", "w"))
    json.dump(games, open(CACHE / "games.json", "w"))
    if len(games) == len(events()):
        (CACHE / "odds_done").write_text("1")
    print("odds stage:", len(games), "events processed,", sum(1 for v in games.values() if v), "matched", flush=True)


def stage_candles(box, reverse=False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scalper import api
    (CACHE / "candles").mkdir(parents=True, exist_ok=True)
    t0, idle = time.time(), 0
    while time.time() - t0 < box:
        try:
            games = json.load(open(CACHE / "games.json"))
        except Exception:
            time.sleep(20); continue
        did = 0
        for e in (events()[::-1] if reverse else events()):
            g = games.get(e)
            if not g or time.time() - t0 > box:
                continue
            p = CACHE / "candles" / f"{e}.json"
            if p.exists():
                continue
            ml = moneylines(CACHE / "odds" / f"{g['gid']}.json")
            if ml is None:
                continue
            u = underdog(*ml)
            if u is None:
                p.write_text(json.dumps(dict(skip="not underdog <= MAXQ")))
                continue
            side, q = u
            code = g["hc"] if side == "H" else g["ac"]
            tk = f"{e}-{code}"
            try:
                d = api._get(f"/historical/markets/{tk}/candlesticks",
                             dict(start_ts=g["st"] - 4 * 3600, end_ts=g["st"] + 600, period_interval=1), retries=6)
                cs = {c["end_period_ts"]: [api.f((c.get("yes_bid") or {}).get("close")), api.f((c.get("yes_ask") or {}).get("close"))] for c in d.get("candlesticks", [])}
                p.write_text(json.dumps(dict(ticker=tk, side=side, q=q, st=g["st"], candles=cs)))
            except Exception as ex:
                p.write_text(json.dumps(dict(ticker=tk, side=side, q=q, st=g["st"], error=str(ex)[-80:])))
            did += 1
            time.sleep(0.5)
        if not did:
            idle += 1
            if idle > 3 and os.path.exists(CACHE / "odds_done"):
                break
            time.sleep(30)
    print("candles stage done", flush=True)


def stage_entries():
    rows, skipped = [], defaultdict(int)
    for e in events():
        p = CACHE / "candles" / f"{e}.json"
        if not p.exists():
            skipped["not fetched"] += 1; continue
        d = json.load(open(p))
        if "skip" in d: skipped["not underdog or pick-em"] += 1; continue
        if "error" in d: skipped["candle error"] += 1; continue
        ch = {int(t): tuple(v) if None not in v else None for t, v in d["candles"].items()}
        t = look({k: v for k, v in ch.items() if v}, d["st"])
        if t is None: skipped["no look"] += 1; continue
        ask = ch[t][1]
        if not (LO <= ask <= HI): skipped["ask outside band"] += 1; continue
        rows.append(dict(event=e, ticker=d["ticker"], ask=ask, q=d["q"], st=d["st"], lead=(d["st"] - t) / 60))
    json.dump(rows, open(CACHE / "entries.json", "w"), indent=0, sort_keys=True)
    h = hashlib.sha256(open(CACHE / "entries.json", "rb").read()).hexdigest()
    print(f"entries {len(rows)}; skipped {dict(skipped)}; entries.json sha256 {h}")


def stage_results():
    """Reads outcomes; ONLY after stage_entries wrote and hashed entries.json."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scalper import api
    want = {r["ticker"] for r in json.load(open(CACHE / "entries.json"))}
    res, cur = {}, None
    while True:
        q = dict(series_ticker="KXNCAAMBGAME", limit=1000)
        if cur: q["cursor"] = cur
        d = api._get("/historical/markets", q)
        for m in d.get("markets", []):
            if m["ticker"] in want: res[m["ticker"]] = m.get("result")
        cur = d.get("cursor")
        if not cur: break
        time.sleep(0.7)
    json.dump(res, open(CACHE / "results.json", "w"))
    print("results for", len(res), "of", len(want))


def stage_score():
    rows = json.load(open(CACHE / "entries.json"))
    res = json.load(open(CACHE / "results.json"))
    use = [dict(r, win=res[r["ticker"]] == "yes") for r in rows if res.get(r["ticker"]) in ("yes", "no")]
    out = [f"entries {len(rows)}, with result {len(use)}"] + score(use)
    print("\n".join(out))


if __name__ == "__main__":
    CACHE.mkdir(parents=True, exist_ok=True)
    v = sys.argv[1]
    {"odds": lambda: stage_odds(float(sys.argv[2])), "candles": lambda: stage_candles(float(sys.argv[2]), len(sys.argv) > 3 and sys.argv[3] == "reverse"),
     "entries": stage_entries, "results": stage_results, "score": stage_score}[v]()
