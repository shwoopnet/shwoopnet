#!/usr/bin/env python3
"""IGFADE1 and IGUNDER1 quick reads (History Miner, Nov 15, 2026). Cards INGAME_CARDS_NOV15.md (Amendment 1); hand case INGAME_HAND_CASE_NOV15.md.
Reads recorder rows (ingame/*/*/obs.csv.gz) before 2026-11-13T00:00Z and the IG_RESULTS listing pages. Upper bound, not fill-checked.

Usage (python3 -I, from outside the data folders):  python3 -I ingame1.py <ingame folder> <results folder> <out.json>"""
import csv, glob, gzip, io, json, math, os, sys, calendar
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

START, T12, CUT = 1794096000, 1794355200, 1794528000
GAP = 45.0
HS = (0.0, 0.01, 0.02)
CS = (1, 10)
MIN_N = 100
EPS = 1e-9
LEAGUE = {"KXNBA": "NBA", "KXNHL": "NHL", "KXNFL": "NFL"}


def fee(p, c):
    return math.ceil(round(100 * 0.07 * c * p * (1 - p), 9)) / 100


def net(e, h, res, side, c):
    ent = min(0.99, e + h); f = fee(ent, c) / c
    if res not in ("yes", "no"):
        return -f
    return (1.0 if res == side else 0.0) - ent - f


def pf(xs):
    g = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 else g / l


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def two_sided(b, a):
    return b is not None and a is not None and 0 < b < a < 1


def parse_rows(lines):
    """[(t_s, event, kind, ticker, bid, ask)] from obs.csv text lines; header rows skipped; rows at or after CUT dropped."""
    out = []
    for r in csv.reader(lines):
        if not r or r[0] == "t_recv_ms" or len(r) < 8:
            continue
        t = num(r[0])
        if t is None or t / 1000 >= CUT:
            continue
        out.append((t / 1000, r[2], r[3], r[4], num(r[6]), num(r[7])))
    return out


def game_of(event):
    return event.split("-", 1)[1] if "-" in event else None


def league_of(event):
    return LEAGUE.get(event[:5])


def fade(rows):
    """rows of one game, kind ml: earliest qualifying pair -> (ticker, side, ask, t) or None."""
    by = defaultdict(list)
    for t, _e, _k, tk, b, a in rows:
        by[tk].append((t, b, a))
    best = None
    for tk, rs in by.items():
        rs.sort()
        for (t1, b1, a1), (t2, b2, a2) in zip(rs, rs[1:]):
            if t2 - t1 > GAP or not two_sided(b1, a1) or not two_sided(b2, a2):
                continue
            d = (b2 + a2) / 2 - (b1 + a1) / 2
            if abs(d) < 0.10 - EPS:
                continue
            side, ask = ("no", round(1 - b2, 6)) if d > 0 else ("yes", a2)
            if 0.15 - EPS <= ask <= 0.60 + EPS and (best is None or t2 < best[3]):
                best = (tk, side, ask, t2)
    return best


def live_time(ml_rows):
    by = defaultdict(list)
    for t, _e, _k, tk, _b, _a in ml_rows:
        by[tk].append(t)
    c = [t2 for ts in by.values() for t1, t2 in zip(sorted(ts), sorted(ts)[1:]) if t2 - t1 <= GAP]
    return min(c) if c else None


def under(ml_rows, tot_rows):
    lt = live_time(ml_rows)
    if lt is None:
        return None
    cand = sorted((t, tk, b, a) for t, _e, _k, tk, b, a in tot_rows if t >= lt and two_sided(b, a))
    if not cand:
        return None
    t, tk, b, _a = cand[0]
    ask = round(1 - b, 6)
    return (tk, "no", ask, t) if 0.35 - EPS <= ask <= 0.65 + EPS else None


def load_results(folder):
    res = {}
    for f in sorted(glob.glob(os.path.join(folder, "*.json.gz"))):
        for m in json.load(gzip.open(f)).get("markets", []):
            cl = calendar.timegm(datetime.strptime(m["close_time"][:19], "%Y-%m-%dT%H:%M:%S").timetuple())
            if START <= cl < CUT:
                res[m["ticker"]] = (cl, m.get("result"))
    return res


def evaluate(games, res):
    """games: {game: {"league", "ml": rows, "total": rows}} -> per card list of trades."""
    out = {"IGFADE1": [], "IGUNDER1": []}
    for g in sorted(games):
        G = games[g]
        for card, en in (("IGFADE1", fade(G["ml"])), ("IGUNDER1", under(G["ml"], G["total"]))):
            if not en or en[0] not in res:
                continue
            cl, r = res[en[0]]
            out[card].append({"game": g, "league": G["league"], "ticker": en[0], "side": en[1], "e": en[2], "t": en[3], "close": cl,
                              "third": 1 if cl < T12 else 2, "res": r})
    return out


def summarise(trs):
    S = {"n": len(trs), "wins": sum(1 for x in trs if x["res"] == x["side"]), "voids": sum(1 for x in trs if x["res"] not in ("yes", "no"))}
    for c in CS:
        for h in HS:
            k = "c%d_h%d" % (c, round(h * 100))
            S[k] = {"pf": pf([net(x["e"], h, x["res"], x["side"], c) for x in trs]) if trs else None}
            for th in (1, 2):
                xs = [net(x["e"], h, x["res"], x["side"], c) for x in trs if x["third"] == th]
                S[k]["pf_third%d" % th] = pf(xs) if xs else None
            S[k]["n_third1"] = sum(1 for x in trs if x["third"] == 1)
    return S


def verdict(S):
    if S["n"] < MIN_N:
        return "no evidence at n = %d" % S["n"]
    p = S["c1_h2"]; ge = lambda v, b: v is not None and v >= b - 1e-12
    return "PASS" if ge(p["pf"], 1.3) and ge(p["pf_third1"], 1.0) and ge(p["pf_third2"], 1.0) else "fail"


def run(ingame, results):
    games = defaultdict(lambda: {"league": None, "ml": [], "total": []})
    nrows = 0
    for f in sorted(glob.glob(os.path.join(ingame, "*", "*", "obs.csv.gz"))):
        for row in parse_rows(io.TextIOWrapper(gzip.open(f), newline="")):
            g, lg = game_of(row[1]), league_of(row[1])
            if g is None or lg is None or row[2] not in ("ml", "total"):
                continue
            nrows += 1
            games[(lg, g)]["league"] = lg; games[(lg, g)][row[2]].append(row)
    res = load_results(results)
    tr = evaluate({"%s|%s" % k: v for k, v in games.items()}, res)
    out = {"label": "IGFADE1 and IGUNDER1 quick reads, thirds 1 and 2 only (closes Nov 8 to Nov 12); upper bound, not fill-checked",
           "tries": 2, "rows_read": nrows, "games": len(games), "markets_in_listing": len(res), "cards": {}}
    for card, trs in tr.items():
        S = summarise(trs); S["verdict"] = verdict(S)
        S["by_league"] = {lg: summarise([x for x in trs if x["league"] == lg]) for lg in ("NBA", "NHL", "NFL")}
        out["cards"][card] = S
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 3:
        print(__doc__); sys.exit(2)
    hm_guard.refuse_all(a)
    r = run(a[0], a[1])
    json.dump(r, open(a[2], "w"), indent=1, sort_keys=True)
    print(json.dumps({"tries": r["tries"], "rows_read": r["rows_read"], "games": r["games"]}))
