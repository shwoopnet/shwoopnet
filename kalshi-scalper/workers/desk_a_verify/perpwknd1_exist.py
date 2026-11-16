"""PERPWKND1 existence count (Desk A, Nov 16 2026), the card's first step: for every weekend (Friday F, Sunday F + 2, Monday F + 3) and every Equities or Indices perp, are the three candles (ending Friday 16:00 ET, Sunday 18:00 ET, Monday 10:00 ET) PRESENT and USABLE (0 < bid_close < ask_close < 1000; the extract's placeholder ask of about 9.2e14 is unusable)? Prints counts by weekend and class and the names that fail by reason. It prints NO price and NO return: it reads only presence and the bid < ask test; no mid, no gap, no outcome. REFUSES unless HELDOUT_PULL_RUNS.md carries a line with the mark PERPWKND1, "perpwknd1_exist.py" and this file's own sha256.
  python3 -I perpwknd1_exist.py <dir with kalshi1m/<date>[.only].csv.gz> <page max table tsv> <first Friday YYYY-MM-DD> <last Friday YYYY-MM-DD> <out.json>"""
import sys, os, json, gzip, csv, hashlib, datetime, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_perps as P
ALLOW_FILE = os.path.join(here, "..", "HELDOUT_PULL_RUNS.md")
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def refuse_unless_allowed():
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if "PERPWKND1" in line and "perpwknd1_exist.py" in line and self_sha() in line: return
    raise SystemExit("REFUSED: no allow-list line names perpwknd1_exist.py with this file's sha256 %s" % self_sha())
def et_epoch(d, hh):
    """epoch of the ET wall clock hh:00 on date d (a datetime.date), the DST offset read at that day's midday."""
    mid = int((datetime.datetime(d.year, d.month, d.day, 12) - datetime.datetime(1970, 1, 1)).total_seconds()) + 5 * 3600
    return P.et_day0(mid) + hh * 3600
def classes(tsv):
    rows = list(csv.reader(open(tsv, encoding="utf-8"), delimiter="\t")); h = [x.strip().lower() for x in rows[0]]; ti, ci = h.index("ticker"), h.index("class")
    return {r[ti]: r[ci] for r in rows[1:] if len(r) > ci}
def read_file(path):
    out = {}
    for pth in path:
        for r in csv.DictReader(gzip.open(pth, "rt")):
            try: out[(r["ticker"], int(r["end_period_ts"]))] = (float(r["bid_close"]), float(r["ask_close"]))
            except (ValueError, KeyError): pass
    return out
def day_candles(base, d, cache):
    k = d.isoformat()
    if k not in cache:
        pths = [os.path.join(base, "kalshi1m", k + sfx) for sfx in (".csv.gz", ".only.csv.gz") if os.path.exists(os.path.join(base, "kalshi1m", k + sfx))]
        cache[k] = read_file(pths)
    return cache[k]
def usable(c): return c is not None and 0 < c[0] < c[1] < 1000
def main(base, tsv, first, last, out, check_allow=True):
    if check_allow: refuse_unless_allowed()
    cls = {t: c for t, c in classes(tsv).items() if c in ("Equities", "Indices")}; cache = {}; rep = {"weekends": {}}
    f = datetime.date.fromisoformat(first); end = datetime.date.fromisoformat(last)
    while f <= end:
        if f.weekday() == 4:                                                              # Friday
            su, mo = f + datetime.timedelta(days=2), f + datetime.timedelta(days=3)
            tms = (et_epoch(f, 16), et_epoch(su, 18), et_epoch(mo, 10)); cs = [day_candles(base, d, cache) for d in (f, su, mo)]
            c = collections.Counter(); fail = collections.Counter(); names = {}
            for t, k in cls.items():
                c[k + ":listed"] += 1; ok = True
                for i in range(3):
                    cd = cs[i].get((t, tms[i]))
                    if cd is None: fail[(k, i, "missing")] += 1; ok = False
                    elif not usable(cd): fail[(k, i, "unusable")] += 1; ok = False
                if ok: c[k + ":usable all three"] += 1
            rep["weekends"][f.isoformat()] = {"counts": dict(c), "fail_by_leg_reason": {"%s:%s:%s" % (k, ("fri16", "sun18", "mon10")[i], r): v for (k, i, r), v in sorted(fail.items())}}
        f += datetime.timedelta(days=1)
    rep["total_usable_name_weekends"] = sum(v for w in rep["weekends"].values() for k, v in w["counts"].items() if k.endswith("usable all three"))
    rep["rule"] = "closed as NOT_ENOUGH_DATA if under 30 name-weekends are usable (card PERPWKND1)"; rep["reads"] = "presence and bid < ask only; no price, no return printed"
    json.dump(rep, open(out, "w"), indent=1); print("wrote", out, "usable name-weekends", rep["total_usable_name_weekends"], "sha", self_sha()[:8])
if __name__ == "__main__":
    if len(sys.argv) != 6: sys.exit(__doc__)
    main(*sys.argv[1:])
