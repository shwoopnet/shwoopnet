#!/usr/bin/env python3
"""1e-9 compare of the NBATOTAL first build (engine/nbatotal.py, Desk C) against the Testing Desk's second build on THEIR invented fixture (Nov 16, 2026).
Usage: python3 -I compare_second_build.py <fixture.json.gz> <their_lines.txt> <engine dir>
The fixture is converted into the landed-file layout (a list run and a candle run); the first build runs unchanged with its metrics function wrapped to capture each cell."""
import gzip, json, math, os, re, sys, tempfile, time

fx, theirs, eng = sys.argv[1], sys.argv[2], sys.argv[3]
DAYS = float(sys.argv[4]) if len(sys.argv) > 4 else 16
sys.path.insert(0, eng)
import nbatotal as N

iso = lambda ts: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
d = json.load(gzip.open(fx, "rt"))
root = tempfile.mkdtemp()


def put(job, rows):
    p = os.path.join(root, "pull", job, "r1")
    os.makedirs(p)
    man = []
    for i, (row, body) in enumerate(rows, 1):
        with gzip.open(os.path.join(p, "%04d.json.gz" % i), "wt") as f:
            json.dump(body, f)
        man.append(dict(row, index=i, file="%04d.json.gz" % i))
    with open(os.path.join(p, "manifest.json"), "w") as f:
        json.dump({"status": "complete", "rows": man}, f)


import re as _re
TK = lambda t: _re.sub(r"-P(\d+)-T(\d+)$", r"-\2-P\1", t) if _re.search(r"-P\d+-T\d+$", t) else t.replace("-T", "-")   # their invented tickers carry a ladder and a T before the strike; the landed ones are EVENT-STRIKE
ms = [{"ticker": TK(r["ticker"]), "event_ticker": r["event"], "occurrence_datetime": iso(r["occ"]), "close_time": iso(r["close_time"]),
       "open_time": iso(r["open_time"]), "result": r["result"]} for r in d["rungs"]]
put("KXNBATOTAL_LISTS_A", [({"id": "dev_KXNBATOTAL", "page": 1}, {"markets": ms, "cursor": ""})])
mk = [{"market_ticker": TK(tk), "candlesticks": [{"end_period_ts": int(t), "yes_bid": {"close_dollars": repr(v[0])}, "yes_ask": {"close_dollars": repr(v[1])}, "volume_fp": repr(v[2])}
                                            for t, v in sorted(c.items(), key=lambda x: int(x[0]))]} for tk, c in d["candles"].items()]
put("NBATOTAL_CANDLES_P1", [({"path": "/markets/candlesticks"}, {"markets": mk})])

cap = []
orig = N.metrics


def wrapped(rows):
    m = orig(rows)
    m["_net_primary"] = sum(r[4] for r in rows)
    cap.append(m)
    return m


N.metrics = wrapped
out = N.run(root, 6290660, DAYS)
mine = {}
for m in cap:
    if "cell" not in m:
        continue
    D, band, side, ex, fl = m["cell"]
    fl2 = {"vol_rise": "vol_rising", "vol_notrise": "vol_not", "age_lt24": "age_young", "age_ge24": "age_old"}.get(fl, fl)
    z = m["z_game"]
    mo = m.get("marked_only")
    mine["D%dh|%s|band%.2f|%s|%s" % (D // 60, ex, band[0], side, fl2)] = {"n": m["n"], "games": m["games"], "days": m["trade_days"], "pf1": m["p"]["pf"], "h1": m["p"]["h1"], "h2": m["p"]["h2"],
        "pf2": m["c2"]["pf"], "net1": m["_net_primary"], "weekly5": m["net5"] / (DAYS / 7), "z": z, "p": N.p_one_sided(z), "marked_n": 0 if mo is None else mo["n"], "marked_pf": None if mo is None else mo["pf_primary"]}


def num(s):
    return None if s in ("None", "nan") else (float("inf") if s == "inf" else float(s))


pat = re.compile(r"^(D\d+h\|\w+\|band[\d.]+\|\w+\|\w+) \| n (\d+) games (\d+) days (\d+) \| pf1 (\S+) h1 (\S+) h2 (\S+) pf2 (\S+) \| net1 (\S+) weekly5 (\S+) \| z (\S+) p (\S+) \| marked_n (\d+) marked_pf (\S+) \| pass (\w+)$")
lines = open(theirs).read().split("\n")
header, counts_line = lines[0], lines[1]
lines = [lines[0]] + lines[3:]
header, diffs, empty_theirs, checked = lines[0], [], 0, 0
for l in lines[1:]:
    g = pat.match(l)
    assert g, l
    key = g.group(1)
    t = {"n": int(g.group(2)), "games": int(g.group(3)), "days": int(g.group(4)), "pf1": num(g.group(5)), "h1": num(g.group(6)), "h2": num(g.group(7)), "pf2": num(g.group(8)),
         "net1": num(g.group(9)), "weekly5": num(g.group(10)), "z": num(g.group(11)), "p": num(g.group(12)), "marked_n": int(g.group(13)), "marked_pf": num(g.group(14))}
    if t["n"] == 0:
        empty_theirs += 1
        if key in mine and mine[key]["n"] != 0:
            diffs.append((key, "n", t["n"], mine[key]["n"]))
        continue
    m = mine.get(key)
    if m is None:
        diffs.append((key, "cell missing in first build", t["n"], None))
        continue
    checked += 1
    for f, tv in t.items():
        mv = m[f]
        if isinstance(tv, int) or isinstance(mv, int):
            if tv != mv:
                diffs.append((key, f, tv, mv))
        elif tv is None or mv is None:
            if not (tv is None and mv is None) and not (tv in (None,) and mv is None):
                diffs.append((key, f, tv, mv))
        elif not math.isclose(tv, mv, rel_tol=1e-9, abs_tol=1e-9):
            diffs.append((key, f, tv, mv))
extra = sorted(k for k in mine if k not in {pat.match(l).group(1) for l in lines[1:]})
print("their header:", header)
print("their counts:", counts_line)
print("my counts:", sorted(out["counts"].items()))
print("first build: m_total %s bh_survivors %s" % (out["m_total"], out["bh_survivors"]))
print("cells compared (their n > 0):", checked, "their empty cells:", empty_theirs, "cells only in mine:", len(extra))
print("differences:", len(diffs))
for x in diffs[:60]:
    print(" ", x)
