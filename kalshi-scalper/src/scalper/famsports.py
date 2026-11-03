"""FAMSPORTS (workers/FAMSPORTS_REGISTRATION.md): NBA, NFL, NHL game totals against a points model built only from teams' earlier public final scores.
Research only. Verdict words: FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade; no promote verb.
    python -m scalper.famsports fetch   (ESPN scoreboard, one request per day, into data/famsports/scores.json; resumable)
    python -m scalper.famsports run     (the one scored read; refused a second time)
"""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import sys
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .calibration import cluster_mean_z
from .econnew1 import fee, line, pnl, stats
from .paths import DATA_DIR

D = Path(os.environ["FAMSPORTS_DIR"]) if os.environ.get("FAMSPORTS_DIR") else DATA_DIR / "famsports"
RESULT = D / "famsports_result.txt"
SPORTS = {"KXNBATOTAL": ("basketball/nba", 19.0), "KXNFLTOTAL": ("football/nfl", 14.0), "KXNHLTOTAL": ("hockey/nhl", 2.4)}
FIRST_DAY, LAST_DAY = date(2025, 9, 1), date(2026, 11, 2)
WIN_FAR_S, WIN_NEAR_S = 120 * 60, 10 * 60
MAX_SPREAD, MIN_PRIOR, LAST_N = 0.10, 5, 10
TRIES = {"A": 0.08, "B": 0.15}
BAR_PF, BAR_Z, MIN_MEAN_C, MIN_TRADES, N_RUN = 1.5, 5.27, 2.0, 150, 732
TK = re.compile(r"^(KX[A-Z]+TOTAL)-(\d{2}[A-Z]{3}\d{2})([A-Z0-9]+)-\d+$")
ALIAS = {"WAS": "WSH", "GSW": "GS", "NOP": "NO", "SAS": "SA", "NYK": "NY", "LA": "LAR", "TB": "TBL", "NJ": "NJD", "LV": "LV"}


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def p_over(pred, strike, sigma):
    return 1.0 - norm_cdf((strike - pred) / sigma)


def pred_total(fa, ga, fb, gb):
    """(F_A + G_B)/2 + (F_B + G_A)/2."""
    return (fa + gb) / 2.0 + (fb + ga) / 2.0


def trailing(hist, team, before_day):
    """(F, G) means over the team's last LAST_N completed games strictly before before_day, at least MIN_PRIOR, else None."""
    g = [x for x in hist.get(team, ()) if x[0] < before_day][-LAST_N:]
    if len(g) < MIN_PRIOR:
        return None
    return sum(x[1] for x in g) / len(g), sum(x[2] for x in g) / len(g)


def build_history(games):
    """games: [(day_iso, start_ts, away, home, away_score, home_score)] -> {team: [(day_iso, scored, allowed)] sorted}"""
    h = defaultdict(list)
    for day, _ts, a, hm, sa, sh in games:
        h[a].append((day, sa, sh)); h[hm].append((day, sh, sa))
    for t in h:
        h[t].sort()
    return h


def split_code(code, teams):
    """Split 'MIATOR' into (away, home) using the set of ESPN abbreviations (and a small alias table); None if ambiguous or not found."""
    out = []
    for i in range(2, len(code) - 1):
        a, b = code[:i], code[i:]
        a, b = ALIAS.get(a, a) if a not in teams else a, ALIAS.get(b, b) if b not in teams else b
        if a in teams and b in teams:
            out.append((a, b))
    return out[0] if len(out) == 1 else None


def valid_quote(bid, ask):
    return bid is not None and ask is not None and 0.01 <= bid < ask <= 0.99 and ask - bid <= MAX_SPREAD + 1e-9


def choose(options, thr):
    """options: [(edge, strike_ticker, side, price, outcome_yes)] -> best option if edge >= thr else None. Deterministic tie-break by ticker."""
    if not options:
        return None
    b = max(options, key=lambda o: (o[0], o[1]))
    return b if b[0] >= thr - 1e-12 else None


def brier(rows):
    return sum((p - y) ** 2 for p, y in rows) / len(rows) if rows else float("nan")


def fetch_day(sport, d):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/scoreboard?dates={d:%Y%m%d}"
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
                return json.loads(r.read())
        except Exception:
            pass
    return None


def fetch():
    D.mkdir(parents=True, exist_ok=True)
    f = D / "scores.json"
    store = json.loads(f.read_text()) if f.exists() else {}
    days = [FIRST_DAY + timedelta(n) for n in range((LAST_DAY - FIRST_DAY).days + 1)]
    for series, (sport, _s) in SPORTS.items():
        have = store.setdefault(series, {})
        todo = [d for d in days if d.isoformat() not in have]
        with ThreadPoolExecutor(8) as ex:
            for d, js in zip(todo, ex.map(lambda d: fetch_day(sport, d), todo)):
                if js is None:
                    continue
                rows = []
                for e in js.get("events", []):
                    try:
                        if e["status"]["type"]["name"] != "STATUS_FINAL":
                            continue
                        comp = e["competitions"][0]["competitors"]
                        h = next(c for c in comp if c["homeAway"] == "home"); a = next(c for c in comp if c["homeAway"] == "away")
                        ts = int(datetime.strptime(e["date"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc).timestamp())
                        rows.append([e["id"], ts, a["team"]["abbreviation"], h["team"]["abbreviation"], int(a["score"]), int(h["score"])])
                    except Exception:
                        continue
                have[d.isoformat()] = rows
        print(series, len(have), "days", sum(len(v) for v in have.values()), "final games")
        f.write_text(json.dumps(store))


def load_games(store, series):
    out = []
    for dayiso, rows in store[series].items():
        for _id, ts, a, h, sa, sh in rows:
            out.append((datetime.fromtimestamp(ts, timezone.utc).date().isoformat(), ts, a, h, sa, sh))
    return out


def run():
    store = json.loads((D / "scores.json").read_text())
    db = sqlite3.connect(str(DATA_DIR / "sports1.sqlite"))
    out = [f"FAMSPORTS run {datetime.now(timezone.utc).isoformat()} N={728000 + N_RUN} z bar {BAR_Z} cost 7% x C x p x (1-p) rounded up, C 10, taker at the ask"]
    games = {}  # (series, espn id) -> record, and per series history
    per_game = []  # eligible games
    drops = defaultdict(int)
    for series, (_sp, sigma) in SPORTS.items():
        gl = load_games(store, series)
        hist = build_history(gl)
        teams = set(hist)
        espn = {}
        for dayiso, rows in store[series].items():
            for _id, ts, a, h, sa, sh in rows:
                espn[(frozenset((a, h)), datetime.fromtimestamp(ts, timezone.utc).date())] = (ts, a, h)
        ev = defaultdict(list)
        for t, st, res, strike, cl in db.execute("select ticker,series,result,strike,close_ts from market where series=? and result in ('yes','no')", (series,)):
            m = TK.match(t)
            if m:
                ev[m.group(2) + m.group(3)].append((t, res, strike))
        for key, mk in ev.items():
            code = key[7:]
            try:
                kd = datetime.strptime(key[:7], "%y%b%d").date()
            except ValueError:
                drops["bad date"] += 1; continue
            ab = split_code(code, teams)
            if not ab:
                drops["team code"] += 1; continue
            hit = None
            for dd in (0, 1, -1):
                hit = espn.get((frozenset(ab), kd + timedelta(dd)))
                if hit and {hit[1], hit[2]} == set(ab):
                    break
                hit = None
            if not hit:
                drops["no espn game"] += 1; continue
            ts, ea, eh = hit
            day = datetime.fromtimestamp(ts, timezone.utc).date().isoformat()
            ta, tb = trailing(hist, ea, day), trailing(hist, eh, day)
            if not ta or not tb:
                drops["under 5 prior games"] += 1; continue
            pred = pred_total(ta[0], ta[1], tb[0], tb[1])
            opts = []
            for t, res, strike in mk:
                rows = db.execute("select end_ts,bid_c,ask_c from candle where ticker=? and end_ts between ? and ? order by end_ts", (t, ts - WIN_FAR_S, ts - WIN_NEAR_S)).fetchall()
                q = next(((b, a) for _e, b, a in rows if valid_quote(b, a)), None)
                if q:
                    opts.append((t, strike, q[0], q[1], res == "yes"))
            if not opts:
                drops["no valid quote"] += 1; continue
            per_game.append(dict(series=series, event=series + ":" + key, ts=ts, pred=pred, sigma=sigma, opts=opts))
    out.append("drops " + ", ".join(f"{k} {v}" for k, v in sorted(drops.items())))
    per_game.sort(key=lambda g: g["ts"])
    n = len(per_game)
    out.append(f"eligible games {n} " + ", ".join(f"{s} {sum(1 for g in per_game if g['series'] == s)}" for s in SPORTS))
    cut = [per_game[n // 3]["ts"] if n else 0, per_game[2 * n // 3]["ts"] if n else 0]
    win = lambda g: "W1" if g["ts"] < cut[0] else ("W2" if g["ts"] < cut[1] else "W3")
    # Brier on the strike nearest a 50c mid, one per game, windows W1 + W2 only (W3 stays unread unless both pass)
    br = {"model": [], "market": []}
    for g in per_game:
        if win(g) == "W3":
            continue
        t, k, b, a, y = min(g["opts"], key=lambda o: (abs((o[2] + o[3]) / 2 - 0.5), o[0]))
        br["model"].append((p_over(g["pred"], k, g["sigma"]), 1.0 if y else 0.0)); br["market"].append(((b + a) / 2, 1.0 if y else 0.0))
    bm, bk = brier(br["model"]), brier(br["market"])
    out.append(f"Brier W1+W2 (strike nearest 50c, {len(br['model'])} games): model {bm:.4f} market mid {bk:.4f}")
    verdicts = {}
    for tag, thr in TRIES.items():
        trades = {"W1": [], "W2": [], "W3": []}
        for g in per_game:
            options = []
            for t, k, b, a, y in g["opts"]:
                po = p_over(g["pred"], k, g["sigma"])
                options.append((po - a - fee(a), t, "yes", a, y))
                no_ask = 1.0 - b
                options.append(((1.0 - po) - no_ask - fee(no_ask), t, "no", no_ask, y))
            c = choose(options, thr)
            if c:
                trades[win(g)].append((g["event"], pnl(c[2], c[3], "yes" if c[4] else "no"), pnl(c[2], c[3], "yes" if c[4] else "no", 1.2)))
        s1, s2 = [stats([(e, x) for e, x, _ in trades[w]]) for w in ("W1", "W2")]
        sp = stats([(e, x) for w in ("W1", "W2") for e, x, _ in trades[w]])
        sx = stats([(e, x) for w in ("W1", "W2") for e, _, x in trades[w]])
        out += [f"{tag} thr {thr}: " + line("W1", s1), "   " + line("W2", s2), "   " + line("pooled W1+W2", sp), f"   fees x1.2 pooled PF {sx['pf']:.2f} mean {sx['mean']:+.2f}c"]
        by = defaultdict(list)
        for w in ("W1", "W2"):
            for e, x, _ in trades[w]:
                by[e.split(":")[0]].append((e, x))
        out.append("   per sport (information): " + "; ".join(f"{k} n {len(v)} mean {sum(x for _, x in v) / len(v):+.1f}c" for k, v in sorted(by.items())))
        ok = s1["n"] and s2["n"] and s1["pf"] >= BAR_PF and s2["pf"] >= BAR_PF
        why = []
        if not (bm < bk): why.append("model Brier not better than the market mid")
        if sp["n"] < MIN_TRADES: why.append(f"{sp['n']} trades under {MIN_TRADES}")
        if not ok: why.append("PF under 1.5 in a window")
        if sp["mean"] < MIN_MEAN_C: why.append("pooled mean under 2c")
        if sp["z"] < BAR_Z: why.append(f"pooled z {sp['z']:+.2f} under {BAR_Z}")
        if sx["pf"] < 1.0: why.append("not positive at fees x1.2")
        v = "PASS_TO_W3" if not why else ("NOT_ENOUGH_DATA" if (bm < bk and sp["n"] < MIN_TRADES) else "FALSIFIED")
        out.append(f"VERDICT {tag}: {v}: " + "; ".join(why))
        out.append(f"   trades per day over the read span: {sp['n'] / max(1, (per_game[2 * n // 3]['ts'] - per_game[0]['ts']) / 86400):.2f}" if n else "")
    if any("PASS_TO_W3" in l for l in out):
        out.append("W3 holdout would be read next as a separate registered step; not read here.")
    else:
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
