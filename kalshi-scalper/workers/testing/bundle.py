#!/usr/bin/env python3
"""TESTING_LISTS_BUNDLE: one kalshi-pull job holding the Testing Desk's five small jobs, and the splitter that turns the landed run folder back into five answer sets (Testing Desk, Nov 12, 2026).
Why: the runner allows 12 real runs a UTC day and fourteen jobs wait, so runs are scarcer than requests. Research only; the builder reads the five committed job files and writes one file, the splitter reads a landed run folder.
Sub-jobs, in the Head's scoring order (and request order, so that a 200 MB cut falls on the LAST sub-job):  t3 TIE3_LISTS | wx WXDAYEND_A | pc POLCOST   (SOCDERIV_LISTS is a separate job; POL-i2's settled lists are not pulled)
Every request id is the sub-job prefix + '_' + its original id, so a manifest row says which sub-job it belongs to. NOTE ON CANDLES: WXDAYEND_A carries its own 18 one-market candle windows (the registered finishing count of card 74, already approved);
the bundle holds no other candle request; nothing closing on or after any held-out constant (TIE3 2026-11-13T00:00Z; POLCOST lists open markets only) is requested (each sub-job keeps its own bound, copied unchanged).
Commands:  build > TESTING_LISTS_BUNDLE.json  |  split <landed bundle run folder> <out dir>   (writes <out>/<sub-job>/ with manifest.json + the answer files, original ids, and prints the check report)
"""
import gzip, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = os.path.join(HERE, "..", "kalshi_pull_jobs")
ORDER = [("t3", "TIE3_LISTS"), ("wx", "WXDAYEND_A"), ("pc", "POLCOST")]       # SOCDERIV_LISTS is its own job again (Head, 17:44Z); POL-i2's settled lists are replaced by the open-markets cost snapshot POLCOST (Head, 18:01Z, POL-i2 Amendment 4)
BUNDLE_ID = "TESTING_LISTS_BUNDLE"
SLACK = 14                       # 429 retries count against the cap


def load(name): return json.load(open(os.path.join(JOBS, name + ".json")))


def build():
    subs = [(p, load(n)) for p, n in ORDER]
    reqs, eps, series, tickers = [], {}, set(), set()
    for p, j in subs:
        for r in j["requests"]:
            r2 = dict(r); r2["id"] = "%s_%s" % (p, r["id"]); reqs.append(r2)
        for e in j["allowed_endpoints"]:                         # same path pattern: union of the allowed params
            cur = eps.setdefault(e["path_pattern"], {"name": e["name"], "method": "GET", "path_pattern": e["path_pattern"], "params_allowed": []})
            for x in e["params_allowed"]:
                if x not in cur["params_allowed"]: cur["params_allowed"].append(x)
        series |= set(j.get("series_allowlist", [])); tickers |= set(j.get("ticker_allowlist", []))
    pages = sum(r.get("max_pages", 1) for r in reqs)
    names = {}
    for e in eps.values():                                       # endpoint names must stay unique
        names[e["name"]] = names.get(e["name"], 0) + 1
        if names[e["name"]] > 1: e["name"] += "_%d" % names[e["name"]]
    base = subs[0][1]
    job = {"job_id": BUNDLE_ID, "owner": "MAIN", "registration": "kalshi-scalper/workers/testing/TESTING_LISTS_BUNDLE.md",
           "purpose": "Testing Desk bundle of three small jobs (TIE3 lists, WXDAYEND_A, POLCOST open-markets cost snapshot) so they cost one run; each request id is prefixed t3_, wx_, pc_. UNRATE_LISTS was dropped (Head, 18:03Z: UNRATEROUND retired unread).",
           "heldout": "none read; nothing closing on or after 2026-11-13T00:00Z (TIE3); POLCOST lists open markets, which have no result is requested; measurements and counts only, no rule scored, no try",
           "allowed_endpoints": list(eps.values()), "series_allowlist": sorted(series), "ticker_allowlist": sorted(tickers), "max_requests": pages + SLACK,
           "notes": "%d requests, %d pages at most (the runner counts pages against the cap); worst-case size is far above the 200 MB run cap if every page were full (see TESTING_LISTS_BUNDLE.md); sub-jobs are ordered so a size stop falls on the last one" % (len(reqs), pages),
           "status": "active", "host": base["host"], "base_path": base["base_path"], "pacing_seconds": 1.0, "stop_rules": base["stop_rules"], "requests": reqs}
    return job


def split(folder, out):
    """Turn one landed bundle run folder into five answer sets in the layout the readers expect. Returns a report per sub-job; one sub-job's failure never blocks reading the others."""
    man = json.load(open(os.path.join(folder, "manifest.json")))
    expected = {p: [r["id"][len(p) + 1:] for r in man["job"]["requests"] if r["id"].startswith(p + "_")] for p, _ in ORDER}
    known = {r["id"] for r in man["job"]["requests"]}
    report = {"bundle_status": man.get("status"), "requests_sent": man.get("requests_sent"), "bytes_stored": man.get("bytes_stored"), "sub_jobs": {}, "mixed_or_unknown_rows": []}
    by_prefix = {p: [] for p, _ in ORDER}
    for row in man["rows"]:
        if row["id"] not in known:
            report["mixed_or_unknown_rows"].append(row["id"]); continue
        by_prefix[row["id"].split("_", 1)[0]].append(row)
    seen_ids = set()
    for p, name in ORDER:
        sub = [r for r in man["job"]["requests"] if r["id"].startswith(p + "_")]
        d = os.path.join(out, name); os.makedirs(d, exist_ok=True)
        rows, ok, failed = [], set(), {}
        for row in by_prefix[p]:
            r2 = dict(row); r2["id"] = row["id"][len(p) + 1:]; rows.append(r2)
            if row.get("status") == 200 and row.get("file"):
                ok.add(r2["id"])
                shutil.copyfile(os.path.join(folder, row["file"]), os.path.join(d, row["file"]))
            elif row.get("status") == 404: ok.add(r2["id"])          # a 404 is an answer
            else: failed[r2["id"]] = row.get("status")
        subjob = {k: v for k, v in man["job"].items() if k not in ("requests", "job_id")}
        subjob["job_id"] = name; subjob["requests"] = [dict(r, id=r["id"][len(p) + 1:]) for r in sub]; subjob["allowed_endpoints"] = man["job"]["allowed_endpoints"]
        json.dump({"job": subjob, "rows": rows, "status": man.get("status"), "requests_sent": len(rows), "script": man.get("script")}, open(os.path.join(d, "manifest.json"), "w"))
        missing = [i for i in expected[p] if i not in ok and i not in failed]
        dup = len(expected[p]) != len(set(expected[p]))
        report["sub_jobs"][name] = {"expected_requests": len(expected[p]), "answered": len(ok & set(expected[p])), "failed": failed, "missing_ids": missing, "duplicate_expected_ids": dup,
                                    "state": "COMPLETE" if not missing and not failed else ("PARTIAL" if ok else "NOT RUN")}
    return report


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "build": print(json.dumps(build(), indent=1))
    elif a and a[0] == "split" and len(a) == 3: print(json.dumps(split(a[1], a[2]), indent=1))
    else: print(__doc__)
