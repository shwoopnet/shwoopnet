#!/usr/bin/env python3
"""ENGINE1 extract: ECONHIST lists in ONE schema (Forensics desk, Nov 16, 2026; Auditor B's draft allow line of 15:34Z). WRITTEN WITHOUT OPENING THE RUN; it runs once after the allow line is merged.
REFUSES unless HELDOUT_PULL_RUNS.md carries a line containing this file's name, its own sha256 and the run name (no flag, no env var). Opens no other run.
Order: (1) `ticker` and `close_time` ONLY of each market object; the series is the ticker's text before the first '-'; a series not in CUTS, or an unreadable close, is dropped and counted; a row with close_time at or after the series' cut (KXCPI and KXPCECORE: 1758844800 = 2025-09-26T00:00Z; the other eight have no cut before the endpoint's end) is dropped and counted BEFORE any other key is touched.
(2) for kept rows only: `event_ticker` and `result` (result not yes or no: kept with result NULL and counted, not dropped, because a settled economic market may have a scalar result; counted by series). No price or volume exists in the lists. Duplicate tickers keep the first and are counted.
Schema: market(ticker, series, close_ts, result, src, event_ticker) and an empty candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi) for loader compatibility. usage: python3 -I engine1_econhist.py <dir holding the pull run folders> <out dir>"""
import os, sys, json, gzip, hashlib, collections, calendar, time, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__))
CUTS = {"KXCPI": 1758844800, "KXPCECORE": 1758844800, "KXPAYROLLS": None, "KXJOBLESSCLAIMS": None, "KXCONTCLAIMS": None, "KXUE": None, "KXISMPMI": None, "KXUSISMSERV": None, "KXUSPPIYOY": None, "KXCPINDEX": None}
RUN = "ECONHIST_LISTS/2026-11-16T1522Z_43895509363"
ALLOW_FILE = os.path.join(HERE, "..", "..", "HELDOUT_PULL_RUNS.md")
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def refuse_unless_allowed(allow_file=ALLOW_FILE):
    try: text = open(allow_file, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    if not [l for l in text.splitlines() if "engine1_econhist.py" in l and self_sha() in l and RUN in l]:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md has no allow-list line naming engine1_econhist.py with this file's sha256 %s and run %s" % (self_sha(), RUN))
def run_bodies(base, run):
    folder = os.path.join(base, *run.split("/"))
    try: man = json.load(open(os.path.join(folder, "manifest.json")))
    except Exception as e: raise SystemExit("REFUSED: %s has no readable manifest.json (%s)" % (run, e))
    if man.get("status") != "complete" or not isinstance(man.get("rows"), list) or not man["rows"]: raise SystemExit("REFUSED: %s is not a complete run" % run)
    ids = collections.defaultdict(list)
    for r in man["rows"]: ids[r.get("id")].append(r)
    for rid, rs in ids.items():
        if not any(r.get("status") == 200 for r in rs) or any(r.get("status") not in (200, 429) for r in rs): raise SystemExit("REFUSED: request %r of %s was not answered 200" % (rid, run))
    for r in man["rows"]:
        if r.get("status") == 200 and "file" in r: yield json.load(gzip.open(os.path.join(folder, r["file"])))
def iso(s):
    try: return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception: return None
def build(base, out, allow_file=ALLOW_FILE):
    refuse_unless_allowed(allow_file); os.makedirs(out, exist_ok=True); c = collections.Counter(); kept = {}
    for b in run_bodies(base, RUN):
        for m in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
            tk, ct = m["ticker"], m["close_time"]
            s = tk.split("-")[0] if isinstance(tk, str) else None; cl = iso(ct) if isinstance(ct, str) else None
            if s not in CUTS or cl is None: c["unknown series or no close"] += 1; continue
            if CUTS[s] is not None and cl >= CUTS[s]: c["dropped by the cut " + s] += 1; continue
            if tk in kept: c["duplicate ticker (first kept)"] += 1; continue
            kept[tk] = [s, cl, m]
    dst = os.path.join(out, "ENGINE1_econhist_extract.sqlite")
    if os.path.exists(dst): os.remove(dst)
    o = sqlite3.connect(dst); o.execute("create table market(ticker, series, close_ts, result, src, event_ticker)"); o.execute("create table candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi)")
    for tk, (s, cl, m) in kept.items():
        r = m.get("result"); ev = m.get("event_ticker")
        if r not in ("yes", "no"): c["result not yes or no (kept, NULL) " + s] += 1; r = None
        o.execute("insert into market values(?,?,?,?,?,?)", (tk, s, cl, r, "econhist", ev if isinstance(ev, str) else None))
    o.commit(); o.execute("vacuum"); o.close(); sha = hashlib.sha256(open(dst, "rb").read()).hexdigest(); db = sqlite3.connect(dst)
    by = db.execute("select series,count(*),min(close_ts),max(close_ts),count(distinct event_ticker) from market group by series order by series").fetchall()
    L = {"extract": "ENGINE1 econhist", "run": RUN, "cuts": CUTS, "counts": dict(c), "markets_by_series": by, "markets": len(kept), "extract_sha256": sha, "extractor_sha256": self_sha()}
    json.dump(L, open(os.path.join(out, "ENGINE1_econhist_cutlog.json"), "w"), indent=1); return L
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    L = build(sys.argv[1], sys.argv[2]); print(json.dumps({k: L[k] for k in ("counts", "markets", "markets_by_series", "extract_sha256", "extractor_sha256")}, indent=1))
