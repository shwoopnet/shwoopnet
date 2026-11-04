"""SOCCERELO1: walk-forward Elo with a draw model from ESPN results vs Kalshi soccer cheap side (ask 3c-30c), held.

Registration: workers/SOCCERELO1_REGISTRATION.md.  Cheap side only: no favourite-side result is computed.  Frozen W3 (start from
2026-10-03T16:00Z) is never fetched or joined.  Caches outside the repo (SOCCERELO1_CACHE; Kalshi candles/markets reused from SOCCER1_CACHE).
Usage: python -m scalper.soccerelo1 hist|window|census|score    (hist = ESPN results before 2026-08-28; window = ESPN results 2026-08-28 to 2026-10-02)
"""
from __future__ import annotations

import json
import math
import os
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

from . import soccer1 as s1

CACHE = Path(os.environ.get("SOCCERELO1_CACHE", "/tmp/claude-0/soccerelo1"))
S1CACHE = Path(os.environ.get("SOCCER1_CACHE", "/tmp/claude-0/soccer1"))
UA = "research-bot SOCCERELO1 (kalshi research)"
CORE = s1.CORE
W3_START = s1.W3_START
WIN_START = int(datetime(2026, 8, 28, tzinfo=timezone.utc).timestamp())  # first Kalshi settled soccer market closes here
LO, HI, RATIO, C, LEAD = 0.03, 0.30, 3.0, 10, 120
# Kalshi prefix -> ESPN slug (Turkey has no Kalshi settled history; MLS, Championship, UEL are outside the registered universe)
LG = {"EPL": "eng.1", "LALIGA": "esp.1", "SERIEA": "ita.1", "BUNDESLIGA": "ger.1", "LIGUE1": "fra.1",
      "EREDIVISIE": "ned.1", "LIGAPORTUGAL": "por.1", "LIGAMX": "mex.1", "UCL": "uefa.champions"}
SLUG2PRE = {v: k for k, v in LG.items()}


# ------------------------------------------------------------------ the model (pure functions, synthetic-tested)

def p3(rh, ra, ha, nu, scale=400.0):
    """Davidson three-way probabilities (home, draw, away) from rating difference d = rh + ha - ra.
    Strengths: gh = 10^(d/2s), ga = 10^(-d/2s); P(home) = gh/(gh+ga+nu), P(away) = ga/(...), P(draw) = nu/(...)."""
    d = (rh + ha - ra) / (2 * scale)
    gh, ga = 10 ** d, 10 ** (-d)
    s = gh + ga + nu
    return gh / s, nu / s, ga / s


def update(rh, ra, res, ha, nu, k):
    """res in {'H','D','A'}. Elo step on the expected score ph + pd/2 with the draw worth half."""
    ph, pd, pa = p3(rh, ra, ha, nu)
    e = ph + pd / 2
    a = {"H": 1.0, "D": 0.5, "A": 0.0}[res]
    return rh + k * (a - e), ra - k * (a - e)


class Ratings:
    def __init__(self, ha, nu, k, start=1500.0, new=1450.0, shrink=0.75):
        self.r, self.ha, self.nu, self.k, self.start, self.new, self.shrink = {}, ha, nu, k, start, new, shrink
        self.seen = set()

    def get(self, team, lg):
        key = (lg, team)
        if key not in self.r:
            self.r[key] = self.start  # promoted or unseen teams start at the mean; rated only after 5 games (predict)
        return self.r[key]

    def offseason(self):
        for key in self.r:
            self.r[key] = self.start + self.shrink * (self.r[key] - self.start)

    def predict(self, home, away, lg):
        """None unless both teams already have a rating from at least 5 earlier games (rated)."""
        if self.n.get((lg, home), 0) < 5 or self.n.get((lg, away), 0) < 5:
            return None
        return p3(self.get(home, lg), self.get(away, lg), self.ha, self.nu)

    n: dict = None

    def step(self, home, away, lg, res):
        if self.n is None:
            self.n = defaultdict(int)
        a, b = self.get(home, lg), self.get(away, lg)
        self.r[(lg, home)], self.r[(lg, away)] = update(a, b, res, self.ha, self.nu, self.k)
        self.n[(lg, home)] += 1
        self.n[(lg, away)] += 1
        self.seen.add(lg)


def run_elo(matches, ha, nu, k, upto=None):
    """matches: list of dict(start, lg, home, away, res) sorted by start. Yields (match, prediction before it)."""
    R = Ratings(ha, nu, k)
    R.n = defaultdict(int)
    out = []
    season_break = None
    for m in matches:
        yr = datetime.fromtimestamp(m["start"], timezone.utc)
        if season_break is not None and (m["start"] - season_break) > 45 * 86400:
            R.offseason()
        season_break = m["start"]
        out.append((m, R.predict(m["home"], m["away"], m["lg"])))
        R.step(m["home"], m["away"], m["lg"], m["res"])
    return out, R


def logloss(pairs):
    tot, n = 0.0, 0
    for m, p in pairs:
        if p is None:
            continue
        pr = {"H": p[0], "D": p[1], "A": p[2]}[m["res"]]
        tot += -math.log(max(pr, 1e-9))
        n += 1
    return tot / n if n else float("inf"), n


def fit(matches):
    """Grid fit of home advantage, draw parameter nu and K on the warm-up matches ONLY (log loss of the walk-forward prediction)."""
    best = None
    for ha in (40, 60, 80, 100):
        for nu in (0.6, 0.8, 1.0, 1.2):
            for k in (10, 20, 30):
                pairs, _ = run_elo(matches, ha, nu, k)
                ll, n = logloss(pairs[len(pairs) // 3:])  # score the last two thirds of the warm-up, first third is burn-in
                if best is None or ll < best[0]:
                    best = (ll, ha, nu, k, n)
    return best


# ------------------------------------------------------------------ ESPN results (core API, 1 request per second)

def http(url):
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(5):
        try:
            with urllib.request.urlopen(r, timeout=20) as f:
                return json.load(f)
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def months(a, b):
    d = a
    while d < b:
        e = min((d.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1), b)
        yield d, e
        d = e + timedelta(days=1)


def fetch_results(out, d0, d1):
    done = set()
    if out.exists():
        done = {json.loads(l)["key"] for l in open(out)}
    f = open(out, "a")
    for pre, lg in LG.items():
        for a, b in months(d0, d1):
            d = http(f"{CORE}/{lg}/events?dates={a:%Y%m%d}-{b:%Y%m%d}&limit=300")
            time.sleep(1)
            ids = [x["$ref"].split("/events/")[1].split("?")[0] for x in (d or {}).get("items", [])]
            for e in ids:
                key = f"{lg}|{e}"
                if key in done:
                    continue
                ev = http(f"{CORE}/{lg}/events/{e}")
                time.sleep(1)
                if not ev:
                    continue
                start = int(datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).timestamp())
                if start >= W3_START:  # frozen: nothing more is fetched
                    continue
                c = ev["competitions"][0]
                names = ev["name"].split(" at ")
                if len(names) != 2:
                    continue
                win = {x["homeAway"]: bool(x.get("winner")) for x in c["competitors"]}
                completed = None
                if not (win.get("home") or win.get("away")):
                    st = http(c["status"]["$ref"].replace("http://", "https://")) if c.get("status") else None
                    time.sleep(1)
                    completed = bool(st and st.get("type", {}).get("completed"))
                res = "H" if win.get("home") else "A" if win.get("away") else ("D" if completed else None)
                f.write(json.dumps(dict(key=key, lg=lg, id=e, start=start, home=names[1], away=names[0], res=res)) + "\n")
                f.flush()
            print(lg, f"{a:%Y-%m}", len(ids), flush=True)
    f.close()


def hist():
    fetch_results(CACHE / "hist.jsonl", datetime(2025, 8, 1).date(), datetime(2026, 8, 27).date())


def window():
    fetch_results(CACHE / "window.jsonl", datetime(2026, 8, 28).date(), datetime(2026, 10, 2).date())


def load_matches(*names):
    rows = []
    for n in names:
        p = CACHE / n
        if p.exists():
            rows += [json.loads(l) for l in open(p)]
    rows = [r for r in rows if r["res"] in ("H", "D", "A") and r["start"] < W3_START]
    rows.sort(key=lambda r: r["start"])
    return rows


# ------------------------------------------------------------------ Kalshi join (reuses SOCCER1's cached markets and candles)

def kalshi_events():
    ev = defaultdict(list)
    for l in open(S1CACHE / "markets.jsonl"):
        m = json.loads(l)
        if m["fam"] == "GAME" and m["pre"] in LG:
            ev[(m["pre"], m["event"])].append(m)
    return ev


def candles():
    cand = defaultdict(dict)
    for l in open(S1CACHE / "candles.jsonl"):
        for t, cs in json.loads(l)["c"].items():
            for ts, b, a in cs:
                if b is not None and a is not None:
                    cand[t][ts] = (b, a)
    return cand


def join_events(matches_by_lg):
    """Kalshi match event -> ESPN match (same league slug, within 1 day, both team names equal under s1.same_team). Uses no price or result."""
    out = []
    for (pre, e), v in kalshi_events().items():
        d = s1._event_date(e)
        teams = [m for m in v if m["sub"] != "Tie"]
        if len(teams) != 2:
            continue
        hit = None
        for r in matches_by_lg.get(LG[pre], []):
            rd = datetime.fromtimestamp(r["start"], timezone.utc).date()
            if abs((rd - d).days) > 1:
                continue
            if all(any(s1.same_team(m["sub"], x) for x in (r["home"], r["away"])) for m in teams):
                hit = r
                break
        if hit:
            out.append(dict(event=e, pre=pre, markets=v, espn=hit))
    return out


def outcome_probs(row, p):
    """Per Kalshi GAME ticker -> Elo probability of YES."""
    h, d, a = p
    q = {}
    for m in row["markets"]:
        if m["sub"] == "Tie":
            q[m["ticker"]] = d
        elif s1.same_team(m["sub"], row["espn"]["home"]):
            q[m["ticker"]] = h
        elif s1.same_team(m["sub"], row["espn"]["away"]):
            q[m["ticker"]] = a
    return q


def predictions(upto_window):
    """Fit on the warm-up season, then walk forward through the window. Returns joined rows with Elo probabilities (no Kalshi result used)."""
    warm = load_matches("hist.jsonl")
    ll, ha, nu, k, n = fit(warm)
    names = ("hist.jsonl", "window.jsonl") if upto_window else ("hist.jsonl",)
    allm = load_matches(*names)
    pairs, R = run_elo(allm, ha, nu, k)
    pred = {m["key"]: p for m, p in pairs}
    by = defaultdict(list)
    for m in allm:
        if m["start"] >= WIN_START:
            by[m["lg"]].append(m)
    rows = []
    for r in join_events(by):
        p = pred.get(r["espn"]["key"])
        if p is None:
            continue
        rows.append(dict(r, elo=outcome_probs(r, p)))
    return rows, dict(logloss=ll, ha=ha, nu=nu, k=k, n_fit=n, n_matches=len(allm))


def treated_rows(rows, cand, with_results=False, res=None):
    """Candidate cheap outcomes at the last valid candle at least LEAD seconds before kickoff; treated when Elo >= 3 x ask."""
    out = []
    for r in rows:
        st = r["espn"]["start"]
        for t, q in r["elo"].items():
            lk = s1.look(cand.get(t, {}), st)
            if lk is None:
                continue
            cs = s1.cheap_side(lk)
            if cs is None:
                continue
            side, ask = cs
            qs = q if side == "Y" else 1 - q
            x = dict(ev=r["event"], t=t, st=st, ask=ask, q=qs, side=side, treated=qs >= RATIO * ask)
            if with_results:
                rr = res.get(t)
                if rr not in ("yes", "no"):
                    continue
                x["win"] = (rr == "yes") == (side == "Y")
            out.append(x)
    return out


def census():
    """Outcome-free: ratings from pre-window results only (static), asks from SOCCER1's candles; counts matches rated and expected treated."""
    rows, info = predictions(False)
    cand = candles()
    allr = treated_rows(rows, cand)
    tr = [x for x in allr if x["treated"]]
    ev = {x["ev"] for x in tr}
    print(json.dumps(info))
    print(f"Kalshi GAME events with candles+rated: {len(rows)}; cheap outcomes {len(allr)}; treated (pre-window ratings) {len(tr)} in {len(ev)} matches")
    gaps = sorted(x["q"] - x["ask"] for x in allr)
    if gaps:
        n = len(gaps)
        print(f"gap q-ask median {gaps[n//2]*100:+.2f}c p10 {gaps[n//10]*100:+.2f}c p90 {gaps[9*n//10]*100:+.2f}c")


def score():
    rows, info = predictions(True)
    cand = candles()
    res = {}
    for l in open(S1CACHE / "markets.jsonl"):
        m = json.loads(l)
        res[m["ticker"]] = m["result"]
    allr = treated_rows(rows, cand, True, res)
    out = [json.dumps(info)]
    P = out.append
    n = len(allr)
    gaps = sorted(x["q"] - x["ask"] for x in allr)
    xs = [s1.net(x["win"], x["ask"]) for x in allr]
    P(f"matches rated+joined {len(rows)}; cheap outcomes (control) {n}")
    if n:
        P(f"gap elo-ask median {gaps[n//2]*100:+.2f}c p10 {gaps[n//10]*100:+.2f}c p90 {gaps[9*n//10]*100:+.2f}c")
        byev = defaultdict(float)
        for x, v in zip(allr, xs):
            byev[x["ev"]] += v
        P(f"control: win {sum(x['win'] for x in allr)/n:.3f} vs ask {sum(x['ask'] for x in allr)/n:.3f} vs elo {sum(x['q'] for x in allr)/n:.3f}; mean net {sum(xs)/n*100:+.2f}c; PF {s1.pf(xs):.2f}; z(match) {s1.zstat(list(byev.values()))}")
    by = defaultdict(list)
    for x in allr:
        if x["treated"]:
            by[x["ev"]].append(x)
    tr = []
    for e, l in by.items():
        tr += sorted(l, key=lambda x: -x["q"] / x["ask"])[:2]
    tr.sort(key=lambda x: x["st"])
    ys = [s1.net(x["win"], x["ask"]) for x in tr]
    P(f"treated (elo >= {RATIO:g} x ask): n {len(tr)} in {len(by)} matches")
    if tr:
        h = len(tr) // 2
        P(f"  win {sum(x['win'] for x in tr)/len(tr):.3f} vs ask {sum(x['ask'] for x in tr)/len(tr):.3f} vs elo {sum(x['q'] for x in tr)/len(tr):.3f}; mean net {sum(ys)/len(ys)*100:+.2f}c; PF {s1.pf(ys):.2f}; fees x1.2 {sum(s1.net(x['win'],x['ask'],1.2) for x in tr)/len(tr)*100:+.2f}c")
        P(f"  half1 {sum(ys[:h])/max(1,h)*100:+.2f}c (n {h}); half2 {sum(ys[h:])/max(1,len(ys)-h)*100:+.2f}c (n {len(ys)-h})")
    if len(tr) < 150:
        P(f"NOT_ENOUGH_DATA: {len(tr)} of 150")
    print("\n".join(out))
    (CACHE / "result.txt").write_text("\n".join(out))


if __name__ == "__main__":
    CACHE.mkdir(parents=True, exist_ok=True)
    import sys
    globals()[sys.argv[1]]()
