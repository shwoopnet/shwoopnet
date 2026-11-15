#!/usr/bin/env python3
"""ECONCENSUS count table (Desk B, Nov 15, 2026). Usage: census_table.py <landed run folder> [--out DIR]
Reads a landed ECONCENSUS_LISTS run (manifest.json + answer files). Prints COUNTS per series: settled markets, close dates, events, markets with volume,
median volume, last price in 10c bands. NEVER reads a market's result. Expected figures: EXPECTED_census_table_nov15.md."""
import csv, gzip, json, math, os, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import deskb_guard as _dg
# The ONLY listed runs this reader may open. Empty until the run lands; then a reviewed edit names the one ECONCENSUS_LISTS run folder. No flag or environment variable extends it.
ALLOWED_RUNS = frozenset()
CUT = "2026-10-17T00:00:00Z"
FED_CUT = "2025-09-17T00:00:00Z"
FED = ("KXFED", "KXFEDDECISION")

def guard(paths):
    for path in [os.getcwd()] + list(paths):
        for p in (os.path.abspath(path), os.path.realpath(path)):
            parts = p.split(os.sep)
            if any(x.upper().startswith("HELDOUT_") for x in parts):
                raise SystemExit("REFUSED: %s lies in or resolves into a HELDOUT_ folder (standing rule (h))" % path)
            bad = _dg.listed_runs().intersection(parts) - ALLOWED_RUNS
            if bad:
                raise SystemExit("REFUSED: %s is, or lies inside, the landed run %s, listed as held-out material, which this reader may not read" % (path, sorted(bad)[0]))

def ts(s): return int(datetime.strptime(s.strip().rstrip("Z").split(".")[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp())

def rows_of(run):
    """[(request id, series or None, answer body)] of a landed run; only rows with status 200 and not truncated."""
    man = json.load(open(os.path.join(run, "manifest.json")))
    out = []
    for r in man.get("rows", []):
        if r.get("status") != 200 or r.get("truncated") or not r.get("file"): continue
        fp = os.path.join(run, os.path.basename(r["file"]))
        body = json.load((gzip.open if fp.endswith(".gz") else open)(fp, "rt"))
        out.append((r.get("id", ""), (r.get("params") or {}).get("series_ticker"), body))
    return out

def median(v):
    v = sorted(v); n = len(v)
    return None if not n else (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2)

def table(rows, outdir=None):
    cut, fcut = ts(CUT), ts(FED_CUT)
    agg = defaultdict(lambda: {"n": 0, "dropped": 0, "dates": set(), "events": set(), "vol": [], "bands": Counter()})
    series_list = []
    for rid, series, body in rows:
        if rid == "series_economics":
            for s in (body.get("series") or []):
                series_list.append((s.get("ticker", ""), s.get("frequency", ""), s.get("title", "")))
            continue
        if not series: continue
        a = agg[series]
        for m in body.get("markets") or []:
            try: t = ts(m["close_time"])                      # close_time FIRST: a market at or after the cut is dropped before any other field is read
            except (KeyError, ValueError, TypeError): continue
            if t >= (fcut if series in FED else cut): a["dropped"] += 1; continue
            a["n"] += 1; a["dates"].add(datetime.fromtimestamp(t, timezone.utc).date().isoformat()); a["events"].add(m.get("event_ticker", ""))
            try: v = float(m.get("volume_fp", m.get("volume")))
            except (TypeError, ValueError): v = None
            if v is not None: a["vol"].append(v)
            try: lp = float(m.get("last_price_dollars", m.get("last_price")))
            except (TypeError, ValueError): lp = None
            if lp is not None: a["bands"][min(9, max(0, int(math.floor(lp * 10 + 1e-9))))] += 1
    lines = []
    for s in sorted(agg):
        a = agg[s]; ds = sorted(a["dates"])
        mv = median(a["vol"])
        lines.append("%s: settled markets %d, after the cut dropped %d, close dates %d%s, events %d, markets with volume above 0 %d, median volume %s, last price bands: %s" % (
            s, a["n"], a["dropped"], len(ds), " (%s to %s)" % (ds[0], ds[-1]) if ds else "", len(a["events"]), sum(1 for x in a["vol"] if x > 0),
            "n/a" if mv is None else ("%g" % mv), ", ".join("[%.1f,%.1f%s %d" % (b / 10, (b + 1) / 10, "]" if b == 9 else ")", a["bands"][b]) for b in range(10) if a["bands"][b]) or "none"))
    if outdir and series_list:
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "series_economics.tsv"), "w", newline="") as f:
            w = csv.writer(f, delimiter="\t"); w.writerow(["ticker", "frequency", "title"]); w.writerows(sorted(series_list))
    return lines, len(series_list)

def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    run = a[0]; out = a[a.index("--out") + 1] if "--out" in a else None
    guard([run] + ([out] if out else []))
    lines, ns = table(rows_of(run), out)
    print("ECONCENSUS count table (counts only; no result read); series in the Economics list answer: %d" % ns)
    print("\n".join(lines))

if __name__ == "__main__": main()
