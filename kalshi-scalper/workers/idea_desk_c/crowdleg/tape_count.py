#!/usr/bin/env python3
"""CROWDLEG tape-sizing trial reader, version 2 (Idea Desk C, Nov 13, 2026). Research only. [research]

Counts, for ONE landed run folder of the kalshi-pull job CROWDLEG_TAPE_TRIAL (job file sha256 165d906a...,
canonical job hash 6bb0ddcf...), the answer pages, the trade rows and the rows whose ticker starts with
"KXMVE" (combos). Per row it touches ONLY the "ticker" key; per page only "trades" and "cursor". No price,
size, side, time or id is read, nothing is written, and the raw rows are never read for any other purpose.
Rows are counted per answer row WITHOUT de-duplication across pages (cursor paging can repeat a trade at a
page boundary); for a sizing trial that is accepted and said in the output.

Order of checks (Auditor B's findings F1 to F3 on version 1, Nov 13):
  1. Held-out guard (rule (h)): refuse a path with a HELDOUT_ part, and any run listed in HELDOUT_PULL_RUNS.md
     (the copy beside this file, equal to main's at the time of writing; its sha256 is printed). An unreadable
     list refuses everything.
  2. manifest.json: its embedded job must have the canonical hash below (sha256 of the job as JSON with sorted
     keys and no spaces), so only CROWDLEG_TAPE_TRIAL's single request is accepted.
  3. Pages come from the manifest's rows, in order, never from a directory listing. Each file must resolve
     inside the run folder (no link out), exist, and match its row's sha256 and bytes (of the decompressed
     answer). A missing, mismatched, link-out, cut ("truncated": true) or unparsable page is counted unreadable.
  4. Labels: status not "complete" -> "INCOMPLETE run, status X, a lower bound"; any unreadable page -> "a
     lower bound"; the last manifest page still carrying a cursor -> "truncated" (whatever the page count);
     the last page unreadable -> "end of tape unknown"; "complete tape" only if status is complete, every page
     read and the last page has no cursor.
Hand cases (committed with this file): complete, stopped, truncated, corrupt page, wrong job.
Usage: python3 -I tape_count.py <run folder>
"""
import gzip, hashlib, json, os, re, sys

CANONICAL_JOB_SHA256 = "6bb0ddcfe201828e70d388afb251afa0d8b09c35c147c41aafdb9c546826be09"
HERE = os.path.dirname(os.path.abspath(__file__))
LIST_FILE = os.path.join(HERE, "HELDOUT_PULL_RUNS.md")
ROW = re.compile(r"^\|\s*`([A-Za-z0-9_\-]+)/([A-Za-z0-9_\-]+)`\s*\|")

def listed_runs(list_file=LIST_FILE):
    try:
        raw = open(list_file, "rb").read(); lines = raw.decode("utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        raise SystemExit("REFUSED: %s cannot be read, so no run can be shown to be clean" % list_file)
    if not any(ln.startswith("| Run folder") for ln in lines):
        raise SystemExit("REFUSED: %s has no table header" % list_file)
    sys.stderr.write("guard: HELDOUT_PULL_RUNS list read, sha256 %s\n" % hashlib.sha256(raw).hexdigest())
    return {m.group(2) for m in map(ROW.match, lines) if m}

def guard(path, list_file=LIST_FILE):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)):
            raise SystemExit("REFUSED: %s lies in or resolves into a HELDOUT_ folder" % path)
    runs = listed_runs(list_file)
    for p in (os.path.abspath(path), os.path.realpath(path)):
        hit = runs.intersection(p.split(os.sep))
        if hit:
            raise SystemExit("REFUSED: %s is the landed run %s, listed in HELDOUT_PULL_RUNS.md" % (path, sorted(hit)[0]))

def job_hash(job):
    return hashlib.sha256(json.dumps(job, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def count(folder, list_file=LIST_FILE):
    guard(folder, list_file)
    root = os.path.realpath(folder)
    try:
        man = json.load(open(os.path.join(folder, "manifest.json")))
    except Exception:
        raise SystemExit("REFUSED: no readable manifest.json in %s" % folder)
    if job_hash(man.get("job")) != CANONICAL_JOB_SHA256:
        raise SystemExit("REFUSED: the manifest's job is not CROWDLEG_TAPE_TRIAL at canonical hash %s" % CANONICAL_JOB_SHA256[:8])
    status = man.get("status")
    rows_m = [r for r in (man.get("rows") or []) if isinstance(r, dict) and r.get("file")]
    rows = kx = 0
    unreadable = []
    last_cursor = "unknown"
    for i, r in enumerate(rows_m):
        name = r["file"]; why = None; ans = None
        p = os.path.realpath(os.path.join(folder, name))
        if os.path.dirname(p) != root or not re.match(r"^\d{4}\.json\.gz$", name): why = "outside the run folder"
        elif not os.path.isfile(p): why = "missing"
        elif r.get("truncated"): why = "cut at the answer cap"
        else:
            try:
                data = gzip.open(p, "rb").read()
                if hashlib.sha256(data).hexdigest() != r.get("sha256") or len(data) != r.get("bytes"):
                    why = "sha256 or bytes differ from the manifest"
                else:
                    ans = json.loads(data.decode("utf-8"))
                    if not isinstance(ans, dict): why = "not an object"; ans = None
            except Exception:
                why = "not readable JSON"
        if why:
            unreadable.append("%s: %s" % (name, why))
            if i == len(rows_m) - 1: last_cursor = "unknown"
            continue
        for t in ans.get("trades") or []:
            rows += 1
            tk = t.get("ticker") if isinstance(t, dict) else None
            if isinstance(tk, str) and tk.startswith("KXMVE"): kx += 1
        if i == len(rows_m) - 1:
            last_cursor = "open" if ans.get("cursor") else "empty"
    labels = []
    if status != "complete": labels.append("INCOMPLETE run, status %s, a lower bound" % status)
    if unreadable: labels.append("a lower bound: %d unreadable page(s)" % len(unreadable))
    if last_cursor == "open": labels.append("truncated: the last page still carries a cursor")
    if last_cursor == "unknown": labels.append("end of tape unknown: the last page is unreadable")
    complete_tape = status == "complete" and not unreadable and last_cursor == "empty"
    if complete_tape: labels.append("complete tape")
    return {"pages_in_manifest": len(rows_m), "rows": rows, "kxmve_rows": kx,
            "kxmve_share": round(kx / rows, 4) if rows else None, "unreadable": unreadable,
            "status": status, "labels": labels,
            "note": "rows are counted per answer row, not de-duplicated across pages"}

if __name__ == "__main__":
    print(json.dumps(count(sys.argv[1]), indent=1, sort_keys=True))
