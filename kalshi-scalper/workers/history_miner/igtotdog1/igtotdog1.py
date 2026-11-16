#!/usr/bin/env python3
"""IGTOTDOG1 quick read (History Miner, Nov 16, 2026). Card IGTOTDOG1_CARD_NOV16.md. Reuses ingame1 (frozen) for parsing, live time, net and results.
Usage (python3 -I, from outside the data folders):  python3 -I igtotdog1.py <ingame folder> <results folder> [<results folder> ...] <out.json>"""
import glob, gzip, io, json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "ingame1"))
sys.path.insert(0, os.path.dirname(HERE))
import ingame1 as I  # noqa: E402
import hm_guard  # noqa: E402

LO, HI = 0.08, 0.20


def entry(ml_rows, tot_rows):
    lt = I.live_time(ml_rows)
    if lt is None:
        return None
    for t, _e, _k, tk, b, a in sorted(tot_rows, key=lambda r: (r[0], r[3])):
        if t < lt or not I.two_sided(b, a):
            continue
        if LO - I.EPS <= a <= HI + I.EPS:
            return (tk, "yes", a, t)
        n = round(1 - b, 6)
        if LO - I.EPS <= n <= HI + I.EPS:
            return (tk, "no", n, t)
    return None


def run(ingame, result_dirs):
    games = defaultdict(lambda: {"league": None, "ml": [], "total": []})
    for f in sorted(glob.glob(os.path.join(ingame, "*", "*", "obs.csv.gz"))):
        for row in I.parse_rows(io.TextIOWrapper(gzip.open(f), newline="")):
            g, lg = I.game_of(row[1]), I.league_of(row[1])
            if g is None or lg is None or row[2] not in ("ml", "total"):
                continue
            games[(lg, g)]["league"] = lg; games[(lg, g)][row[2]].append(row)
    res = {}
    for d in result_dirs:
        res.update(I.load_results(d))
    trs = []
    for k in sorted(games):
        G = games[k]; en = entry(G["ml"], G["total"])
        if not en or en[0] not in res:
            continue
        cl, r = res[en[0]]
        trs.append({"game": "%s|%s" % k, "league": G["league"], "ticker": en[0], "side": en[1], "e": en[2], "t": en[3], "close": cl,
                    "third": 1 if cl < I.T12 else 2, "res": r})
    S = I.summarise(trs); S["verdict"] = I.verdict(S)
    S["by_league"] = {lg: I.summarise([x for x in trs if x["league"] == lg]) for lg in ("NBA", "NHL", "NFL")}
    return {"label": "IGTOTDOG1 quick read, thirds 1 and 2 only; upper bound, not fill-checked; live = first hot poll (may precede tip-off)",
            "tries": 1, "games": len(games), "card": S}


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__); sys.exit(2)
    hm_guard.refuse_all(a)
    r = run(a[0], a[1:-1])
    json.dump(r, open(a[-1], "w"), indent=1, sort_keys=True)
    print(json.dumps({"tries": r["tries"], "games": r["games"]}))
