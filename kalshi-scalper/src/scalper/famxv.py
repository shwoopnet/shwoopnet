"""FAMXV (workers/FAMXV_REGISTRATION.md): Kalshi NBA and NFL game-winner asks against Polymarket's price for the same team 60 minutes before the start.
Research only. Verdict words: FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade; no promote verb.
    python -m scalper.famxv fetch   (Polymarket event and 1 minute history per game into data/famxv/pm.json; resumable)
    python -m scalper.famxv run     (the one scored read; refused a second time)
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .econnew1 import fee, line, pnl, stats
from .paths import DATA_DIR

D = Path(os.environ["FAMXV_DIR"]) if os.environ.get("FAMXV_DIR") else DATA_DIR / "famxv"
RESULT = D / "famxv_result.txt"
SPORT = {"KXNBAGAME": "nba", "KXNFLGAME": "nfl"}
LOOK_S, QUOTE_FAR_S, QUOTE_NEAR_S, PM_MAX_AGE_S = 3600, 5400, 1800, 900
MAX_SPREAD = 0.10
TRIES = {"A": 0.04, "B": 0.08}
BAR_PF, BAR_Z, MIN_MEAN_C, MIN_TRADES = 1.5, 5.27, 2.0, 150
ET = ZoneInfo("America/New_York")
UA = {"User-Agent": "Mozilla/5.0"}


def get(url):
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read())
        except Exception:
            pass
    return None


def slug_candidates(sport, away, home, start_ts):
    """Slugs tried, in order: <sport>-<away>-<home>-<date> and the reversed order, date in UTC then US Eastern, then +-1 day."""
    t = datetime.fromtimestamp(start_ts, timezone.utc)
    days = []
    for d in (t.date(), t.astimezone(ET).date(), t.date() - timedelta(1), t.date() + timedelta(1)):
        if d not in days:
            days.append(d)
    out = []
    for d in days:
        out += [f"{sport}-{away.lower()}-{home.lower()}-{d}", f"{sport}-{home.lower()}-{away.lower()}-{d}"]
    return out


def team_token(market, aliases):
    """Index of the outcome whose name equals one of the team's aliases (nickname or city), else None."""
    outs = json.loads(market["outcomes"]) if isinstance(market["outcomes"], str) else market["outcomes"]
    low = [a.lower() for a in aliases]
    for i, o in enumerate(outs):
        if o.lower() in low:
            return i
    return None


def pm_at(hist, t, max_age=PM_MAX_AGE_S):
    """Last history point (t_i, p) with t_i <= t and t - t_i <= max_age, else None."""
    best = None
    for ti, p in hist:
        if ti <= t:
            best = (ti, p)
        else:
            break
    return best[1] if best and t - best[0] <= max_age else None


def valid_quote(bid, ask):
    return bid is not None and ask is not None and 0.02 <= bid < ask <= 0.98 and ask - bid <= MAX_SPREAD + 1e-9


def k_ask(candles, start_ts):
    """Last valid two-sided candle ending 90 to 30 minutes before the start: (ask, bid, end_ts) or None. candles sorted by end_ts: (end_ts, bid, ask)."""
    q = [c for c in candles if start_ts - QUOTE_FAR_S <= c[0] <= start_ts - QUOTE_NEAR_S and valid_quote(c[1], c[2])]
    return (q[-1][2], q[-1][1], q[-1][0]) if q else None


def pick(gaps, thr):
    """gaps: [(gap, team_key, ask, won)] -> the largest gap if it is at least thr, else None."""
    if not gaps:
        return None
    b = max(gaps, key=lambda g: (g[0], g[1]))
    return b if b[0] >= thr - 1e-12 else None


def games(db):
    out = []
    q = """select m.event, m.series, e.start_ts, e.home_id, e.away_id, e.teams, m.home_ticker, m.away_ticker
           from match m join egame e on e.id = m.egame and e.series = m.series where m.series in ('KXNBAGAME','KXNFLGAME')"""
    for ev, series, ts, hid, aid, teams, ht, at in db.execute(q):
        t = json.loads(teams)
        out.append(dict(event=ev, series=series, ts=ts, home=t[hid], away=t[aid], ht=ht, at=at))
    return out


def fetch():
    D.mkdir(parents=True, exist_ok=True)
    f = D / "pm.json"
    store = json.loads(f.read_text()) if f.exists() else {}
    db = sqlite3.connect(str(DATA_DIR / "espn1.sqlite"))
    gl = [g for g in games(db) if g["event"] not in store]

    def one(g):
        sport = SPORT[g["series"]]
        for slug in slug_candidates(sport, g["away"][0], g["home"][0], g["ts"]):
            js = get(f"https://gamma-api.polymarket.com/events?slug={slug}")
            if not js:
                continue
            ev = js[0]
            mk = next((m for m in ev["markets"] if m.get("sportsMarketType") == "moneyline"), None)
            if not mk:
                continue
            toks = json.loads(mk["clobTokenIds"])
            res = {"slug": slug, "teams": {}}
            for key, al in (("home", g["home"]), ("away", g["away"])):
                i = team_token(mk, al)
                if i is None:
                    res["teams"][key] = None; continue
                h = get(f"https://clob.polymarket.com/prices-history?market={toks[i]}&startTs={g['ts'] - 4 * 3600}&endTs={g['ts']}&fidelity=1")
                res["teams"][key] = [[x["t"], x["p"]] for x in (h or {}).get("history", [])]
            return res
        return None

    with ThreadPoolExecutor(6) as ex:
        for g, r in zip(gl, ex.map(one, gl)):
            store[g["event"]] = r
    f.write_text(json.dumps(store))
    fetch_kalshi_pre(games(db))
    print("games", len(store), "with a Polymarket event", sum(1 for v in store.values() if v))


def fetch_kalshi_pre(gl):
    """Amendment 1: Kalshi 1 minute candles from 100 to 10 minutes before the start for both team markets of every game, into kpre.json."""
    from . import api, backfill
    f = D / "kpre.json"
    store = json.loads(f.read_text()) if f.exists() else {}
    for g in gl:
        tks = [t for t in (g["ht"], g["at"]) if t not in store]
        if not tks:
            continue
        try:
            got = api.batch_candlesticks(tks, g["ts"] - 6000, g["ts"] - 600)
        except RuntimeError as e:
            print("skip", g["event"], e); continue
        for tk in tks:
            rows = []
            for c in got.get(tk, []):
                end = c.get("end_period_ts")
                if end is not None:
                    rows.append([int(end), backfill._d(c.get("yes_bid"), "close_dollars"), backfill._d(c.get("yes_ask"), "close_dollars")])
            store[tk] = sorted(rows)
    f.write_text(json.dumps(store))
    print("Kalshi pre-game candles for", len(store), "markets")


def brier(rows):
    return sum((p - y) ** 2 for p, y in rows) / len(rows) if rows else float("nan")


def run():
    store = json.loads((D / "pm.json").read_text())
    db = sqlite3.connect(str(DATA_DIR / "espn1.sqlite"))
    out = [f"FAMXV run {datetime.now(timezone.utc).isoformat()} N=728734 z bar {BAR_Z} cost 7% x C x p x (1-p) rounded up, C 10, taker at the ask"]
    gl = games(db)
    kpre = json.loads((D / "kpre.json").read_text())
    drops = defaultdict(int)
    rows = []
    for g in gl:
        pm = store.get(g["event"])
        if not pm:
            drops["no Polymarket event"] += 1; continue
        look = g["ts"] - LOOK_S
        legs = []
        for key, tk in (("home", g["ht"]), ("away", g["at"])):
            h = pm["teams"].get(key)
            if not h:
                break
            cs = kpre.get(tk, [])
            ka = k_ask(cs, g["ts"])
            p = pm_at(h, look)
            res = db.execute("select result from kmarket where ticker=?", (tk,)).fetchone()
            if ka is None or p is None or not res or res[0] not in ("yes", "no"):
                break
            legs.append((key, ka[0], ka[1], p, res[0] == "yes"))
        else:
            rows.append(dict(event=g["event"], series=g["series"], ts=g["ts"], legs=legs))
            continue
        drops["no Kalshi quote, Polymarket point or result"] += 1
    rows.sort(key=lambda r: r["ts"])
    n = len(rows)
    out.append(f"games on file {len(gl)}, eligible {n}; drops " + ", ".join(f"{k} {v}" for k, v in sorted(drops.items())))
    cut = [rows[n // 3]["ts"], rows[2 * n // 3]["ts"]] if n >= 3 else [0, 0]
    win = lambda r: "W1" if r["ts"] < cut[0] else ("W2" if r["ts"] < cut[1] else "W3")
    gaps_all = [abs(l[3] - l[1]) for r in rows for l in r["legs"]]
    gaps_all.sort()
    if gaps_all:
        out.append(f"gap |P_pm - Kalshi ask| over {len(gaps_all)} legs: median {gaps_all[len(gaps_all) // 2] * 100:.1f}c, p90 {gaps_all[int(len(gaps_all) * .9)] * 100:.1f}c")
    bp, bk, bb = [], [], []
    for r in rows:
        if win(r) == "W3":
            continue
        for key, ask, bid, p, y in r["legs"]:
            mid = (ask + bid) / 2
            yy = 1.0 if y else 0.0
            bp.append((p, yy)); bk.append((mid, yy)); bb.append(((p + mid) / 2, yy))
    out.append(f"Brier W1+W2 ({len(bk)} team legs): Polymarket {brier(bp):.4f} Kalshi mid {brier(bk):.4f} blend {brier(bb):.4f}")
    for tag, thr in TRIES.items():
        trades = {"W1": [], "W2": [], "W3": []}
        for r in rows:
            gp = [(p - ask, key, ask, y) for key, ask, bid, p, y in r["legs"]]
            c = pick(gp, thr)
            if c:
                res = "yes" if c[3] else "no"
                trades[win(r)].append((r["event"], pnl("yes", c[2], res), pnl("yes", c[2], res, 1.2), c[0]))
        s1, s2 = [stats([(e, x) for e, x, _, _ in trades[w]]) for w in ("W1", "W2")]
        sp = stats([(e, x) for w in ("W1", "W2") for e, x, _, _ in trades[w]])
        sx = stats([(e, x) for w in ("W1", "W2") for e, _, x, _ in trades[w]])
        out += [f"{tag} gap >= {thr}: " + line("W1", s1), "   " + line("W2", s2), "   " + line("pooled W1+W2", sp), f"   fees x1.2 pooled PF {sx['pf']:.2f} mean {sx['mean']:+.2f}c"]
        ok = s1["n"] and s2["n"] and s1["pf"] >= BAR_PF and s2["pf"] >= BAR_PF
        why = []
        if not (brier(bb) <= brier(bk)): why.append("blend Brier worse than Kalshi's")
        if sp["n"] < MIN_TRADES: why.append(f"{sp['n']} trades under {MIN_TRADES}")
        if not ok: why.append("PF under 1.5 in a window")
        if sp["mean"] < MIN_MEAN_C: why.append("pooled mean under 2c")
        if sp["z"] < BAR_Z: why.append(f"pooled z {sp['z']:+.2f} under {BAR_Z}")
        if sx["pf"] < 1.0: why.append("not positive at fees x1.2")
        fals = s1["n"] >= 30 and s2["n"] >= 30 and not ok
        v = "PASS_TO_W3" if not why else ("FALSIFIED" if fals else "NOT_ENOUGH_DATA")
        out.append(f"VERDICT {tag}: {v}: " + "; ".join(why))
    out.append("W3 holdout NOT read (W1 and W2 did not both pass).")
    text = "\n".join(out)
    RESULT.write_text(text + "\n")
    print(text)


def main(argv):
    if len(argv) < 2 or argv[1] not in ("fetch", "run"):
        print(__doc__); return
    if argv[1] == "fetch":
        fetch(); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    run()


if __name__ == "__main__":
    main(sys.argv)
