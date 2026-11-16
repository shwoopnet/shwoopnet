#!/usr/bin/env python3
"""ENGINE1 HELD-OUT READ, INDEPENDENT SECOND BUILD (Forensics desk, Nov 16, 2026). Written from ENGINE1_HELDOUT_READ_PLAN_NOV16.md (version 3: windows, n floors, verdict, BH at 5% over m = 190 on the one-sided day clustered p of the 1c cash) and ENGINE1_RUN2_BARLIST_NOV16.json (sha256 16049fec...) ONLY. Desk A's held-out loader, scorer and print were not opened before this file was committed.
Two modes. (1) --dry <barlist> <archive_extract>: runs THIS code on the archive's own VALIDATE markets as if they were the held-out set and requires n, pf_1c, pf_2c to equal the listing (1e-9); nothing held out is opened. (2) --read <barlist> <archive_extract> <heldout_extract> <desk_a_print_file>: refuses unless the path of Desk A's committed print FILE can be opened and is not empty (the build computes and prints that file's sha256 itself; a typed hash is never accepted); prints counts, the SEARCH cut sha256, per rule verdict counts and BH survivors. Needs Auditor B's allow line for this reader before it is pointed at the held-out extract.
Floors (plan v3): n floor 74 for KXBTC15M KXETH15M KXXRP15M KXDOGE15M KXGOLD15M, 90 for the rest; holds = n >= floor and pf_1c >= 1.3 and pf_2c >= 1.0; below the floor 'no evidence'; BH over m = 190 on rules with a p (one sided, day clustered, UTC close date, 1c nets at 10 contracts; k < 2 days or sd 0 gives p = 1)."""
import sys, os, json, sqlite3, hashlib, collections, calendar, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_rank_b2 as P
import engb4xbtc_b2 as E
R6 = ("KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXGOLD15M")
def load(path, series=None):
    db = sqlite3.connect("file:%s?mode=ro" % path, uri=True); ms = {}
    for tk, ser, close, res in db.execute("select ticker, series, close_ts, result from market"):
        if series is None or ser in series: ms[tk] = P.Mkt(tk, ser, close, res, {})
    for tk, end, b, k, last, v, oi in db.execute("select ticker, end_ts, yes_bid, yes_ask, last, volume, oi from candle"):
        if tk in ms and end <= ms[tk].close: ms[tk].c[end] = (b, k, last, v, oi)
    return sorted(ms.values(), key=lambda m: (m.close, m.tk))
def search_cuts(arch, series, ls):
    cuts = {}; 
    for s in series:
        sm = [m for m in arch if m.ser == s and m.close < ls[s]]
        for B in sorted({r_b for r_b in range(120, 841, 60)}): cuts[(s, B)] = P.terciles(sm, s, B)
    return cuts
def score_rules(L, test_markets, cuts):
    by = collections.defaultdict(list)
    for m in test_markets: by[m.ser].append(m)
    out = []
    for r in L:
        rule = dict(r); rule["phase"] = "V"; rule["filter"] = tuple(r["filter"]) if r["filter"] else None
        res = {}
        for h in (0.01, 0.02):
            xs = []
            for m in by[r["series"]]:
                net, why = P.score(m, rule, h, cuts.get((r["series"], r["bucket"])))
                if net is not None: xs.append((m.close, net))
            res[h] = xs
        out.append((r, res))
    return out
def main(a):
    mode = a[0]; L = json.load(open(a[1]))["validate_bar_list"]; series = sorted({r["series"] for r in L})
    arch = load(a[2], series); ls = {s: calendar.timegm(tuple(int(x) for x in P.LAST_SEARCH[s].split("-")) + (0, 0, 0)) + 86400 for s in series}
    cuts = search_cuts(arch, series, ls)
    sha = hashlib.sha256(json.dumps(sorted((k[0], k[1], list(v) if v else None) for k, v in cuts.items())).encode()).hexdigest()
    if mode == "--dry":
        test = [m for m in arch if m.close >= ls[m.ser]]; sc = score_rules(L, test, cuts); bad = 0
        for r, res in sc:
            x1 = [x[1] for x in res[0.01]]; x2 = [x[1] for x in res[0.02]]
            ok = len(x1) == r["n"] and abs(E.pfv(x1) - r["pf_1c"]) < 1e-9 and abs(E.pfv(x2) - r["pf_2c"]) < 1e-9
            if not ok: bad += 1
        print("DRY on the archive VALIDATE half: rules", len(L), "reproduced", len(L) - bad, "mismatch", bad, "cuts sha256", sha); return
    if mode != "--read" or len(a) < 5: raise SystemExit("REFUSED: --read needs the path of Desk A's committed print FILE as the last argument")
    try: pb = open(a[4], "rb").read()
    except OSError: raise SystemExit("REFUSED: Desk A's print file cannot be opened")
    if not pb.strip(): raise SystemExit("REFUSED: Desk A's print file is empty")
    a = a[:4] + [hashlib.sha256(pb).hexdigest()]
    held = load(a[3], series); sc = score_rules(L, held, cuts); m_bh = 190; rows = []
    for r, res in sc:
        x1 = [x[1] for x in res[0.01]]; x2 = [x[1] for x in res[0.02]]; floor = 74 if r["series"] in R6 else 90; n = len(x1)
        z, p, k = E.pval(res[0.01]) if n else (None, 1.0, 0)
        pf1 = E.pfv(x1) if n else None; pf2 = E.pfv(x2) if n else None
        verdict = "no evidence" if n < floor else ("holds" if pf1 >= 1.3 and pf2 >= 1.0 else "does not hold")
        rows.append({"r": r, "n": n, "pf1": pf1, "pf2": pf2, "p": p, "days": k, "verdict": verdict})
    ps = [x["p"] for x in rows]; k, o = E.bh(ps, m_bh); surv = set(o[:k])
    print("label: unread by ENGINE1, seen by earlier development cards"); print("held-out markets", len(held), "cuts sha256", sha, "desk_a_print_sha256", a[4])
    print("verdicts", dict(collections.Counter(x["verdict"] for x in rows))); print("holds and BH survivor", sum(1 for i, x in enumerate(rows) if x["verdict"] == "holds" and i in surv), "BH survivors (any verdict)", k)
    for s in series: print(s, "rules", sum(1 for x in rows if x["r"]["series"] == s), "holds", sum(1 for x in rows if x["r"]["series"] == s and x["verdict"] == "holds"), "no evidence", sum(1 for x in rows if x["r"]["series"] == s and x["verdict"] == "no evidence"))
    out = os.environ.get("OUTLIST")
    if out: open(out, "w").write("\n".join("%d %s %d %d %s %s %s %.12f %.12f %d %.12e %s" % (i, x["r"]["series"], x["r"]["bucket"], x["r"]["band"], x["r"]["side"], x["r"]["filter"], x["r"]["exit"], x["pf1"] or 0, x["pf2"] or 0, x["n"], x["p"], x["verdict"]) for i, x in enumerate(rows)) + "\n")
if __name__ == "__main__": main(sys.argv[1:])
