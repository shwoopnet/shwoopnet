"""CALIB3 loader and table (Desk A, Nov 15 2026), built to CALIB3_CARD_NOV15.md (CLEAN as a registration) and CALIB3_HAND_CASE_NOV15.md (committed first, addendum at e7b8ada11). Offline; reads one SQLite extract (Forensics' CALIB3_extract, third 3 already cut) and sends nothing. A descriptive table, not a rule: no try is counted.
  CALIB3_READ=1 python3 -I calib3.py <CALIB3_extract.sqlite> <out.json>     DEFAULT-CLOSED. Reuses calib3_stats.bucket_stats unchanged."""
import sys, os, json, math, sqlite3, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import calib3_stats as C
LOOKS = (1800, 600, 120); T12 = 1790755200; T_END = 1791129600; MIN_N = 300; MIN_EV = 60
def event_of(ticker): return ticker.rsplit("-T", 1)[0]
def third_of(close):
    return 1 if close < T12 else (2 if close < T_END else None)          # None: third 3, must not be here
def run(db):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    mk = [(tk, int(cl), res) for tk, cl, res in c.execute("select ticker, close_ts, result from market where series='KXBTCD' order by close_ts")]
    if any(third_of(cl) is None or cl >= 1791504000 for _, cl, _ in mk): sys.exit("REFUSED: the extract holds a market from third 3 or after 2026-10-09 (the cut must be in the extract)")
    cand = collections.defaultdict(dict)
    for tk, e, b, a in c.execute("select ticker,end_ts,bid_c,ask_c from candle"): cand[tk][int(e)] = (b, a)
    rows = collections.defaultdict(list); miss = collections.Counter(); void = 0
    for tk, cl, res in mk:
        if res not in ("yes", "no"): void += 1; continue
        ev, th = event_of(tk), third_of(cl)
        for L in LOOKS:
            q = cand.get(tk, {}).get(cl - L)
            if q is None or q[0] is None or q[1] is None: miss[(L, "missing")] += 1; continue
            b, a = q
            if not (0 < b < a < 1): miss[(L, "not_two_sided")] += 1; continue
            for side, ask in (("yes", a), ("no", round(1 - b, 6))):
                rows[(L, side, C.bucket(ask), th)].append((ev, ask, res == side))
    out = {"label": "descriptive calibration table, not a rule; no try is counted; candle ask, not book; the C2 haircut is not applied (the 2c in the candidate test covers it)", "voids_excluded": void, "missing": {"%d_%s" % k: v for k, v in miss.items()}, "buckets_inspected": 1 * len(LOOKS) * C.NB * 2, "cells": {}}
    elig = cands = 0; chance = 0.0
    for L in LOOKS:
        for side in ("yes", "no"):
            for b in range(C.NB):
                cell = {}
                for th in (1, 2): cell["third%d" % th] = C.bucket_stats(rows.get((L, side, b, th), []))
                cell["thirds_1_2"] = C.bucket_stats(rows.get((L, side, b, 1), []) + rows.get((L, side, b, 2), []))
                s1, s2 = cell["third1"], cell["third2"]
                e = all(s["n"] >= MIN_N and s["events"] >= MIN_EV for s in (s1, s2))
                cell["eligible"] = e
                if e:
                    elig += 1; chance += (s1["p_pass_third"] or 0) * (s2["p_pass_third"] or 0)
                    cell["candidate"] = all(s["gap"] >= s["fee"] + 0.02 and s["event_z"] is not None and s["event_z"] >= 2 for s in (s1, s2))
                    cands += cell["candidate"]
                    cell["neighbours"] = {n: {"third1": C.bucket_stats(rows.get((L, side, b + d, 1), [])), "third2": C.bucket_stats(rows.get((L, side, b + d, 2), []))} for d, n in ((-1, "lower"), (1, "upper")) if 0 <= b + d < C.NB}
                out["cells"]["%d_%s_%d" % (L, side, b)] = cell
    out["eligible_buckets"], out["candidates"], out["expected_chance_candidates_null"] = elig, cands, chance
    out["null_note"] = "per-event null (card): understates the chance count; strikes inside an event are tied together"
    return out
if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2: sys.exit(__doc__)
    if os.environ.get("CALIB3_READ") != "1": sys.exit("REFUSED: CALIB3_READ=1 is not set (reading starts only on the Head's go after Auditor B's check)")
    json.dump(run(a[0]), open(a[1], "w"), indent=1, default=str); print("wrote", a[1])
