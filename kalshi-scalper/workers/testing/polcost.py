#!/usr/bin/env python3
"""POLCOST: a politics cost snapshot (Testing Desk, Nov 12, 2026; Head's ruling 18:01Z, POL-i2 Amendment 4). Research only; ZERO TRIES: nothing is scored, an open market has no result.
Job: the OPEN markets list (status open, same /markets endpoint) of the same 79 daily, weekly or monthly Politics series as POL-i2, one request a series plus paging (79 requests, at most 237 pages).
Table (`table <polcost folder>`): from the open-market objects keep two-sided quotes (0 < bid < ask < 1) with a mid of 20c to 80c; per series and overall: markets quoted, median spread, median round trip (spread plus two taker fees of
0.07 x mid x (1 - mid), Forensics' definition), median size at the touch (the smaller of the bid and ask sizes). RULE (Amendment 4, fixed before the pull): overall median round trip above 5c = POL-i2 CLOSED on cost and its settled lists are never pulled;
at or under 5c = the settled lists go in a later run, placed by the Head. LIMIT: the snapshot is taken at about 00:00Z (7 PM Eastern), not at the 07:00 ET entry hour; a morning snapshot is a second request, asked for only if the evening one is within 1c of the line.
The quotes are list quotes (up to about 11 seconds old), good enough for a spread LEVEL, never for a seconds-level signal.
Commands: build-job <census series-list folder> | table <polcost folder> [--csv out.csv]
"""
import csv, gzip, json, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import poli2_count as p2
import tie3

COST_MAX = 0.05
REG = "kalshi-scalper/workers/testing/POLI2_COUNT_REGISTRATION.md"


def build_job(census_folder):
    ser = p2.politics_series(census_folder)
    reqs = [{"id": "open_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "open", "limit": 1000}, "max_pages": 3} for s in ser]
    eps = [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "limit", "cursor"]}]
    j = tie3.job("POLCOST", "Politics cost snapshot (POL-i2 Amendment 4): the OPEN markets of the 79 daily, weekly or monthly Politics series, quotes and sizes only; no result exists for an open market; nothing scored.", eps, reqs, ser, [])
    j["registration"] = REG
    j["max_requests"] = sum(r["max_pages"] for r in reqs) + 14        # the runner counts pages against the cap
    j["heldout"] = "none: open markets have no result; a measurement of cost, no rule scored, no try"
    return j


def num(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def rows_from(folder):
    man = json.load(open(os.path.join(folder, "manifest.json")))
    for row in man["rows"]:
        if row.get("status") == 200 and row.get("file") and not row.get("truncated"):
            body = json.load(gzip.open(os.path.join(folder, row["file"])))
            for m in body.get("markets", []) if isinstance(body, dict) else []:
                if isinstance(m, dict) and m.get("ticker"): yield m


def table(folder):
    per, seen, open_n = {}, set(), 0
    for m in rows_from(folder):
        if m["ticker"] in seen: continue
        seen.add(m["ticker"]); open_n += 1
        b, a = num(m.get("yes_bid_dollars")), num(m.get("yes_ask_dollars"))
        if b is None or a is None or not (0 < b < a < 1): continue
        mid = (a + b) / 2
        if not (0.20 <= mid <= 0.80): continue
        sz = [x for x in (num(m.get("yes_bid_size_fp")), num(m.get("yes_ask_size_fp"))) if x is not None]
        per.setdefault(m["ticker"].split("-")[0], []).append({"spread": a - b, "rt": (a - b) + 2 * 0.07 * mid * (1 - mid), "size": min(sz) if sz else None})
    out = {"open_markets_listed": open_n, "series_with_a_quoted_market": len(per), "per_series": {}}
    allr = [r for v in per.values() for r in v]
    for s, v in sorted(per.items()):
        sizes = [r["size"] for r in v if r["size"] is not None]
        out["per_series"][s] = {"markets_quoted": len(v), "median_spread": round(st.median(r["spread"] for r in v), 4), "median_round_trip": round(st.median(r["rt"] for r in v), 4), "median_size_at_touch": None if not sizes else round(st.median(sizes), 1)}
    if allr:
        med = st.median(r["rt"] for r in allr)
        out["overall"] = {"markets_quoted_20c_to_80c": len(allr), "series": len(per), "median_spread": round(st.median(r["spread"] for r in allr), 4), "median_round_trip": round(med, 4)}
        near = abs(med - COST_MAX) <= 0.01
        out["verdict"] = ("POL-i2 CLOSED on cost: the overall median round trip is %.1fc, above 5c; its settled lists are never pulled" % (100 * med)) if med > COST_MAX else \
                         ("at or under the 5c line (%.1fc): POL-i2's settled lists go in a later run, placed by the Head" % (100 * med))
        if near: out["verdict"] += "; WITHIN 1c OF THE LINE: a morning snapshot (the 07:00 ET entry hour) may be asked for"
    else:
        out["overall"] = None; out["verdict"] = "no two-sided quote priced 20c to 80c: cannot screen (a morning snapshot may be asked for)"
    out["limit"] = "taken at about 00:00Z (7 PM Eastern), not at the 07:00 ET entry hour; list quotes up to about 11 s old"
    out["tries_added"] = 0; out["rule_scored"] = False
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__)
    elif a[0] == "build-job": print(json.dumps(build_job(a[1]), indent=1))
    elif a[0] == "table":
        t = table(a[1]); print(json.dumps(t, indent=1))
        if "--csv" in a:
            with open(a[a.index("--csv") + 1], "w", newline="") as fh:
                w = csv.writer(fh); w.writerow(["series", "markets_quoted", "median_spread", "median_round_trip_20c_to_80c", "median_size_at_touch"])
                for s, r in t["per_series"].items(): w.writerow([s, r["markets_quoted"], r["median_spread"], r["median_round_trip"], r["median_size_at_touch"]])
