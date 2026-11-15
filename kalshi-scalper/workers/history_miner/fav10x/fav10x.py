#!/usr/bin/env python3
"""FAV10-X build 1 (History Miner, Nov 15, 2026). Spec and hand case FAV10X_HAND_CASE_NOV15.md.
XRPFAV10's rule frozen (exits3.fav_entry) on the 18 other 15 minute series of underdog2x, thirds 1 to 3, Oct 3 and SOL cuts.
Upper bound, not fill-checked.

Usage (python3 -I, from outside the data folder):  python3 -I fav10x.py <data folder> <out.json>"""
import json, os, sqlite3, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "underdog2x"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "exits3"))
sys.path.insert(0, os.path.dirname(HERE))
import underdog2x as U  # noqa: E402
import exits3 as X  # noqa: E402
import hm_guard  # noqa: E402

SERIES = sorted(s for s in U.THIRDS if s != "KXXRP15M")
HS = (0.0, 0.01, 0.02)
CS = (1, 10)
MIN_N = 100
GOLD = "KXGOLD15M"


def load(folder):
    """underdog2x.load without the third-3 drop: {ticker: [series, close, result]}, candles at or before close."""
    mk, src, dropped = {}, {}, defaultdict(int)
    for s in U.SOURCES:
        con = sqlite3.connect("file:%s?mode=ro" % os.path.join(folder, s + ".sqlite"), uri=True)
        for t, ser, cl in con.execute("select ticker, series, close_ts from market where series like '%15M'"):
            if t in src:
                dropped["dup_later_source"] += 1; continue
            src[t] = s
            if cl >= U.CUT or ser not in SERIES or cl >= U.SERIES_CUT.get(ser, U.CUT):
                dropped["on_or_after_cut_or_not_listed"] += 1; continue
            mk[t] = [ser, cl, None]
    cd = defaultdict(dict)
    for s in U.SOURCES:
        con = sqlite3.connect("file:%s?mode=ro" % os.path.join(folder, s + ".sqlite"), uri=True)
        keep = [t for t in mk if src[t] == s]
        for i in range(0, len(keep), 500):
            chunk = keep[i:i + 500]; ph = ",".join("?" * len(chunk))
            for t, res in con.execute("select ticker, result from market where ticker in (%s)" % ph, chunk):
                mk[t][2] = res
            for t, e, b, a in con.execute("select ticker, end_ts, bid_c, ask_c from candle where ticker in (%s)" % ph, chunk):
                if e <= mk[t][1]:
                    cd[t][e] = (b, a)
    return mk, cd, dict(dropped)


def entry(cands, close):
    r = X.fav_entry("XRPFAV10", cands, close)
    return r


def stats(xs):
    n = len(xs); h = n // 2
    return {"pf": X.pf(xs) if n else None, "pf_half1": X.pf(xs[:h]) if h else None, "pf_half2": X.pf(xs[h:]) if n - h else None,
            "mean_c": 100 * sum(xs) / n if n else None}


def verdict(series, n, s1):
    """s1: {h: stats} at c = 1."""
    if n < MIN_N:
        return "no evidence at n = %d" % n
    ge = lambda v, b: v is not None and v >= b - 1e-12
    if series in U.NC15:
        s = s1[0.02]
        ok = ge(s["pf"], 1.3) and ge(s["pf_half1"], 1.0) and ge(s["pf_half2"], 1.0)
    else:
        s = s1[0.01]
        ok = ge(s["pf"], 1.3) and ge(s["pf_half1"], 1.0) and ge(s["pf_half2"], 1.0) and ge(s1[0.02]["pf"], 1.0)
    return "PASS" if ok else "fail"


def run(folder):
    mk, cd, dropped = load(folder)
    tr = defaultdict(list); cnt = defaultdict(lambda: defaultdict(int))
    for t in sorted(mk, key=lambda x: (mk[x][1], x)):
        ser, close, res = mk[t]
        cnt[ser]["markets"] += 1
        en = entry(cd.get(t, {}), close)
        if en is None:
            continue
        if en == "not two-sided":
            cnt[ser]["not_two_sided"] += 1; continue
        tr[ser].append((close, t, en, res))
    out = {"label": "FAV10-X build 1: XRPFAV10 frozen on 18 series, thirds 1 to 3, Oct 3 cut; upper bound, not fill-checked",
           "tries": len(SERIES), "dropped_before_read": dropped, "markets_read": len(mk), "series": {}}
    for ser in SERIES:
        rows = tr[ser]; n = len(rows)
        R = {"n": n, "wins": sum(1 for _c, _t, en, r in rows if r == en["side"]), "voids": sum(1 for *_x, r in rows if r not in ("yes", "no")),
             "counts": dict(cnt[ser]), "nc15": ser in U.NC15, "primary_h": 0.02 if ser in U.NC15 else 0.01}
        s1 = {}
        for c in CS:
            for h in HS:
                st = stats([X.net(en["e"], h, None, r, en["side"], c) for _c, _t, en, r in rows])
                R["c%d_h%d" % (c, round(h * 100))] = st
                if c == 1:
                    s1[h] = st
        R["verdict"] = verdict(ser, n, s1)
        if ser == GOLD:
            R["gold_flag"] = "a pass here is a version of L1, not a new strategy"
        out["series"][ser] = R
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2:
        print(__doc__); sys.exit(2)
    hm_guard.refuse_all(a)
    res = run(a[0])
    json.dump(res, open(a[1], "w"), indent=1, sort_keys=True)
    print(json.dumps({"tries": res["tries"], "markets_read": res["markets_read"]}))
