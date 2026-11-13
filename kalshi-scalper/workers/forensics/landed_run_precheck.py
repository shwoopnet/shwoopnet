#!/usr/bin/env python3
"""Integrity pre-check of a landed kalshi-pull run (Forensics desk, Nov 13, 2026; the Head of R&D's order of 21:05Z, item 2). To speed Auditor B's structure check, not to replace it.
It reads ONLY the run's manifest.json and the file list: no answer file is opened, so no price, result or other value is read. It refuses a run listed in HELDOUT_PULL_RUNS.md
(listed_runs_guard) and any HELDOUT_ folder, and prints the guard's list hash with its result.
Prints, per run: status and requests_sent from the manifest against the number of rows; rows by HTTP status; rows marked truncated; rows with no file or a file that is not on disk; the count of
answer files in the folder that no manifest row names (and rows that name a file twice); pages per request id (how many rows share one id: the paging count); the sum of the rows' own `bytes` against the manifest's bytes_stored (the files on disk are compressed, so their size is printed but not compared). The runner's STATUS marker file is not a stray file.
Exit 0 only if the run is COMPLETE (status complete, every row 200, none truncated, every named file present, requests_sent equals the rows, no stray files).
usage: python3 -I landed_run_precheck.py <run folder> [<run folder> ...]"""
import sys, os, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from listed_runs_guard import refuse_listed, listed_source


def check(folder):
    for p in (os.path.abspath(folder), os.path.realpath(folder)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)): raise SystemExit("REFUSED: %s is in or resolves into a HELDOUT_ folder (standing rule (h))" % folder)
    refuse_listed(folder)
    man = json.load(open(os.path.join(folder, "manifest.json"))); rows = man.get("rows", []); job = man.get("job", {}) if isinstance(man.get("job"), dict) else {}
    by_status = collections.Counter(r.get("status") for r in rows); trunc = sum(1 for r in rows if r.get("truncated"))
    named = [r.get("file") for r in rows if r.get("file")]; nofile = sum(1 for r in rows if not r.get("file")); missing = [f for f in named if not os.path.isfile(os.path.join(folder, f))]
    dup = [f for f, n in collections.Counter(named).items() if n > 1]
    on_disk = sorted(f for f in os.listdir(folder) if f not in ("manifest.json", "STATUS"))   # STATUS is the pull runner's own marker file
    stray = [f for f in on_disk if f not in set(named)]
    pages = collections.Counter(r.get("id") for r in rows); multi = {i: n for i, n in pages.items() if n > 1}
    size = sum(os.path.getsize(os.path.join(folder, f)) for f in named if os.path.isfile(os.path.join(folder, f))); row_bytes = sum(int(r.get("bytes") or 0) for r in rows)
    complete = (man.get("status") == "complete" and set(by_status) <= {200} and trunc == 0 and not missing and not dup and not stray and nofile == 0 and man.get("requests_sent") == len(rows) and (man.get("bytes_stored") is None or int(man.get("bytes_stored")) == row_bytes))
    out = {"run": os.path.basename(os.path.normpath(folder)), "job_id": job.get("job_id"), "manifest_status": man.get("status"), "requests_sent": man.get("requests_sent"), "rows": len(rows), "rows_by_http_status": dict(by_status),
           "truncated_rows": trunc, "rows_without_a_file": nofile, "files_named_but_missing": len(missing), "files_named_twice": len(dup), "stray_files_not_in_the_manifest": len(stray),
           "request_ids": len(pages), "ids_with_more_than_one_page": len(multi), "max_pages_for_one_id": max(multi.values()) if multi else 1, "compressed_bytes_on_disk_named_files": size, "sum_of_row_bytes_in_manifest": row_bytes, "bytes_stored_in_manifest": man.get("bytes_stored"), "COMPLETE": complete}
    return out, complete


def main(argv):
    if not argv: print(__doc__); return 2
    ok = True
    for f in argv:
        try: out, c = check(f)
        except SystemExit as e: print(str(e)); return 1
        print(json.dumps(out)); ok = ok and c
    src, h = listed_source(); print("list guard: %s sha256 %s" % (os.path.relpath(src), h[:16])); return 0 if ok else 1


if __name__ == "__main__":
    import collections
    sys.exit(main(sys.argv[1:]))
