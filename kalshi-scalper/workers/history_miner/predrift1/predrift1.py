#!/usr/bin/env python3
"""PREDRIFT1 quick read (History Miner, Nov 16, 2026). Card PREDRIFT1_CARD_NOV16.md. Reuses ingame1 (frozen) for parsing, net, summary and the bar.
Usage (python3 -I, from outside the data folders):  python3 -I predrift1.py <ingame folder> <results folder> <out.json>"""
import calendar, glob, gzip, io, json, os, sys
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "ingame1"))
sys.path.insert(0, os.path.dirname(HERE))
import ingame1 as I  # noqa: E402
import hm_guard  # noqa: E402

WIN = 600
MIN_D = 0.04
LO, HI = 0.20, 0.80
ts = lambda s: calendar.timegm(datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").timetuple())


def quote_at(rows, mark):
    """rows: sorted [(t, bid, ask)]; last row in (mark - WIN, mark], two-sided, else None."""
    q = None
    for t, b, a in rows:
        if t > mark:
            break
        if t > mark - WIN:
            q = (b, a)
    return q if q and I.two_sided(*q) else None


def entry(rows, tip):
    q6, q1 = quote_at(rows, tip - 6 * 3600), quote_at(rows, tip - 3600)
    if not q6 or not q1:
        return None
    d = (q1[0] + q1[1]) / 2 - (q6[0] + q6[1]) / 2
    if abs(d) < MIN_D - I.EPS:
        return None
    side, ask = ("yes", q1[1]) if d > 0 else ("no", round(1 - q1[0], 6))
    return (side, ask, d) if LO - I.EPS <= ask <= HI + I.EPS else None


def load_listing(folder):
    out = {}
    for f in sorted(glob.glob(os.path.join(folder, "*.json.gz"))):
        for m in json.load(gzip.open(f)).get("markets", []):
            cl = ts(m["close_time"])
            if I.START <= cl < I.CUT and m.get("occurrence_datetime"):
                out[m["ticker"]] = (cl, m.get("result"), ts(m["occurrence_datetime"]) - 3 * 3600)
    return out


def pick(G, kind, league):
    if kind == "total":
        return G
    if league != "NHL":
        return {}
    first = min(G) if G else None
    return {first: G[first]} if first else {}


def run(ingame, results):
    per = defaultdict(lambda: defaultdict(list))        # (league, game, kind) -> ticker -> rows
    for f in sorted(glob.glob(os.path.join(ingame, "*", "*", "obs.csv.gz"))):
        for t, ev, kind, tk, b, a in I.parse_rows(io.TextIOWrapper(gzip.open(f), newline="")):
            lg, g = I.league_of(ev), I.game_of(ev)
            if lg and g and kind in ("ml", "total"):
                per[(lg, g, kind)][tk].append((t, b, a))
    L = load_listing(results)
    trs = []
    for (lg, g, kind) in sorted(per):
        for tk, rows in sorted(pick(per[(lg, g, kind)], kind, lg).items()):
            if tk not in L:
                continue
            cl, res, tip = L[tk]
            en = entry(sorted(rows), tip)
            if not en:
                continue
            trs.append({"league": lg, "kind": kind, "ticker": tk, "side": en[0], "e": en[1], "d": en[2], "close": cl,
                        "third": 1 if cl < I.T12 else 2, "res": res})
            break                                        # one entry per game per kind
    S = I.summarise(trs); S["verdict"] = I.verdict(S)
    S["by_league_kind"] = {"%s_%s" % (lg, k): I.summarise([x for x in trs if x["league"] == lg and x["kind"] == k])
                           for lg in ("NBA", "NFL", "NHL") for k in ("total", "ml")}
    S["yes_share"] = sum(1 for x in trs if x["side"] == "yes") / len(trs) if trs else None
    return {"label": "PREDRIFT1 quick read, thirds 1 and 2 only; tip = occurrence_datetime - 3 h; upper bound, not fill-checked",
            "tries": 1, "card": S}


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 3:
        print(__doc__); sys.exit(2)
    hm_guard.refuse_all(a)
    r = run(a[0], a[1])
    json.dump(r, open(a[2], "w"), indent=1, sort_keys=True)
    print(json.dumps({"tries": r["tries"], "n": r["card"]["n"]}))
