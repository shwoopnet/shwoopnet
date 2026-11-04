"""OUT1 census: LISTINGS, injury reports and snap counts only. No candle, no result, no price is read.
Counts NFL games before the frozen cut with a top-2 skill player Out/Doubtful and the listed beneficiary rungs.
"""
from __future__ import annotations
import csv, json, re, sqlite3, sys, unicodedata
from collections import defaultdict
from pathlib import Path

CACHE = Path("/root/out1cache")
DB = Path(__file__).resolve().parents[2] / "data" / "props1.sqlite"
CUT_TS = 1790956800 - 1790956800 + int(__import__("datetime").datetime(2026, 10, 3, 16, tzinfo=__import__("datetime").timezone.utc).timestamp())
SKILL = ("WR", "TE", "RB", "FB")
OUT = ("Out", "Doubtful")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z ]", " ", s)
    return " ".join(w for w in s.split() if w not in ("jr", "sr", "ii", "iii", "iv"))


def load_snaps():
    """-> team -> sorted list of (season, week, game_id) and per (game_id, team) {name: (pos, snaps)}"""
    tg = defaultdict(dict)
    for y in (2024, 2025, 2026):
        for r in csv.DictReader(open(CACHE / f"snap_counts_{y}.csv")):
            if r["game_type"] not in ("REG", "POST"):
                continue
            key = (r["game_id"], r["team"])
            tg[key][norm(r["player"])] = (r["position"], int(float(r["offense_snaps"] or 0)), r["game_id"])
    order = defaultdict(list)
    for (gid, team) in tg:
        s, w = int(gid[:4]), int(gid[5:7])
        order[team].append((s, w, gid))
    for t in order:
        order[t].sort()
    return tg, order


def load_inj():
    inj = defaultdict(dict)  # (season, week, team) -> {name: status}
    for y in (2024, 2025, 2026):
        for r in csv.DictReader(open(CACHE / f"injuries_{y}.csv")):
            if r["report_status"]:
                inj[(int(r["season"]), int(r["week"]), r["team"])][norm(r["full_name"])] = r["report_status"]
    return inj


def top2(tg, order, team, season, week):
    seq = order.get(team, [])
    prior = [g for g in seq if (g[0], g[1]) < (season, week)][-4:]
    if len(prior) < 3:
        return None
    tot = defaultdict(int)
    for _s, _w, gid in prior:
        for nm, (pos, sn, _g) in tg[(gid, team)].items():
            if pos in SKILL:
                tot[nm] += sn
    r = sorted(tot.items(), key=lambda kv: (-kv[1], kv[0]))[:2]
    return [(n, v) for n, v in r]


def main():
    games_csv = {r["espn"]: r for r in csv.DictReader(open(CACHE / "games.csv")) if r["espn"]}
    tg, order = load_snaps()
    inj = load_inj()
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    games = c.execute("SELECT id,start_ts,home,away FROM game WHERE league='NFL' AND start_ts<? ORDER BY start_ts", (CUT_TS,)).fetchall()
    # listed beneficiaries per game: (gid) -> {espn team: set(names)}; listing only (kmarket name/series/strike; mgame ticker->gid)
    ben = defaultdict(lambda: defaultdict(set)); nmk = defaultdict(int)
    for tk, gid, aid, series in c.execute("SELECT m.ticker,m.gid,m.aid,k.series FROM mgame m JOIN kmarket k ON k.ticker=m.ticker WHERE m.league='NFL' AND k.series IN ('KXNFLRECYDS','KXNFLREC','KXNFLRSHYDS')"):
        t = c.execute("SELECT team,nm FROM pstat WHERE gid=? AND league='NFL' AND aid=?", (gid, aid)).fetchone()
        if t:
            ben[gid][t[0]].add((t[1], series)); nmk[(gid, t[0], t[1], series)] += 1
    res = dict(n_games=len(games), covered=0, trig_games=0, trig_teamgames=0, rows=[])
    for gid, st, home, away in games:
        g = games_csv.get(gid)
        if not g or g["game_type"] not in ("REG", "POST"):
            continue
        season, week = int(g["season"]), int(g["week"])
        if not ben.get(gid):
            continue
        res["covered"] += 1
        hit = False
        for side, espn_abbr in (("home_team", home), ("away_team", away)):
            nv = g[side]
            t2 = top2(tg, order, nv, season, week)
            ij = inj.get((season, week, nv))
            if t2 is None or ij is None:
                continue
            outp = [(n, v, ij[n]) for n, v in t2 if ij.get(n) in OUT]
            if not outp:
                continue
            hit = True
            res["trig_teamgames"] += 1
            tgt_series = {"RB": ("KXNFLRSHYDS",), }  # beneficiaries: all listed receiving/rushing names of the team except the Out players
            names = {(n, s) for (n, s) in ben[gid].get(espn_abbr, set()) if norm(n) not in {o[0] for o in outp}}
            # ESPN pstat team abbreviations may differ from nflverse; ben is keyed by ESPN team
            nrung = sum(nmk[(gid, espn_abbr, n, s)] for n, s in names)
            res["rows"].append(dict(gid=gid, start=st, season=season, week=week, team=nv, out=[o[0] + ":" + o[2] for o in outp],
                                    n_ben=len({n for n, _ in names}), n_rungs=nrung))
        res["trig_games"] += int(hit)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}))
    import statistics
    rows = res["rows"]
    if rows:
        print("beneficiaries per trig team-game median", statistics.median(r["n_ben"] for r in rows), "rungs total", sum(r["n_rungs"] for r in rows))
    json.dump(res, open(Path(__file__).resolve().parents[2] / "workers" / "OUT1_CENSUS.json", "w"), indent=1)


if __name__ == "__main__":
    main()
