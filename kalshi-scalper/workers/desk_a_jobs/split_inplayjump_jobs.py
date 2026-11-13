#!/usr/bin/env python3
"""INPLAYJUMP development candle pull, split per family (Head's decision Nov 13, 2026). Offline: sends nothing.
Re-groups the requests of build_inplayjump_candles.py (clock and tennis_plain) by family, sizes every file from the pilot's MEASURED bytes per ticker-minute for that series (INPLAYJUMP_PILOTVAL run 43338597423, manifest `bytes` of each 1-minute request), and packs requests in their original order into files of at most ~120 MB expected raw.
  python3 -I split_inplayjump_jobs.py <INPLAYJUMP_SERIES.json> <lists run folder> <pilotval run folder> <clock job json> <tennis job json ...> <outdir> <scorekit dir>
Rule (h) check, stated in each file and asserted here: every ticker is a development match of its family (close inside the family's development window from the series file, from the lists), no Tie contract, and every request window ends at or before its batch's last close."""
import json, os, sys, collections
FAMILY_FILES = [("INPLAYJUMP_C_ESOCCER", ["KXESOCCERGAME"]), ("INPLAYJUMP_C_TTEBB", ["KXLIGAPROMATCH", "KXEBASKETBALLGAME"]), ("INPLAYJUMP_T_ITF", ["KXITFMATCH", "KXITFWMATCH"]), ("INPLAYJUMP_T_CH", ["KXATPCHALLENGERMATCH", "KXWTACHALLENGERMATCH"])]
MAX_RAW = 120e6
def rates(pilot):
    m = json.load(open(os.path.join(pilot, "manifest.json"))); acc = collections.defaultdict(lambda: [0, 0])
    for r in m["rows"]:
        p = r["params"]
        if str(p.get("period_interval")) != "1" or r.get("status") != 200: continue
        t = p["market_tickers"].split(","); a = acc[t[0].split("-")[0]]; a[0] += len(t) * ((p["end_ts"] - p["start_ts"]) // 60); a[1] += r["bytes"]
    return {k: v[1] / v[0] for k, v in acc.items()}, {k: v for k, v in acc.items()}
def main(series_path, lists, pilot, jobs, outdir, scorekit_dir):
    sys.path.insert(0, scorekit_dir); import scorekit
    S = json.load(open(series_path)); mk = scorekit.markets([lists]); rate, raw = rates(pilot)
    dev = {}
    for f in S["families_ranked_by_events"]:
        b = (scorekit.iso(f["development"]["closes_from"]), scorekit.iso(f["development"]["closes_before"]))
        for s in f["series"]: dev[s] = b
    reqs = []
    for jf in jobs: reqs += json.load(open(jf))["requests"]
    base = json.load(open(jobs[0]))
    os.makedirs(outdir, exist_ok=True); summary = []
    for jid, series in FAMILY_FILES:
        mine = [r for r in reqs if r["params"]["market_tickers"].split(",")[0].split("-")[0] in series]
        parts, cur, curmb = [], [], 0.0
        for r in mine:
            p = r["params"]; tks = p["market_tickers"].split(",")
            for t in tks:
                s = t.split("-")[0]; assert s in series and not t.endswith("-TIE"), t
                c = mk[t]["close"]; assert c and dev[s][0] <= c < dev[s][1], ("outside development window", t)
                assert p["end_ts"] <= max(mk[x]["close"] for x in tks), ("window ends after the batch's last close", t)
            mb = len(tks) * ((p["end_ts"] - p["start_ts"]) // 60) * max(rate[s] for s in {t.split("-")[0] for t in tks}) / 1e6
            if cur and curmb + mb > MAX_RAW / 1e6: parts.append((cur, curmb)); cur, curmb = [], 0.0
            cur.append(r); curmb += mb
        if cur: parts.append((cur, curmb))
        for i, (rs, mb) in enumerate(parts, 1):
            name = jid + (str(i) if len(parts) > 1 else "")
            meas = ", ".join("%s %.0f B per ticker-minute" % (s.replace("KX", "").replace("MATCH", "").replace("GAME", ""), rate[s]) for s in series)
            tk = sorted({t for r in rs for t in r["params"]["market_tickers"].split(",")})
            j = dict(base, job_id=name, purpose="INPLAYJUMP dev candles 1 min, part %d of %d, %d requests, about %.0f MB raw expected (cap 120). Measured in pilot run 43338597423: %s. No result read." % (i, len(parts), len(rs), mb, meas),
                     heldout="rule (h) checked: every ticker is a development match of its family (close inside the family's development window from the series file, from the lists; no Tie contract) and no request ends after its batch's last close; the held-out window is never requested",
                     series_allowlist=sorted(series), ticker_allowlist=tk, max_requests=len(rs), requests=[dict(r, id="r%04d" % k) for k, r in enumerate(rs)])
            json.dump(j, open(os.path.join(outdir, name + ".json"), "w"), indent=1); summary.append((name, len(rs), mb))
    for n, c, mb in summary: print("%-24s %4d requests  expected %.0f MB raw" % (n, c, mb))
if __name__ == "__main__": main(*sys.argv[1:6] if False else (sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:-2], sys.argv[-2], sys.argv[-1]))
