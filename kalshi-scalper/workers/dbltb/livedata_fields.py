#!/usr/bin/env python3
"""LIVEDATA_PROBE_A: the FIELD reader. Zero tries. It opens the answers of the probe run and prints, for every field,
its path, its types and how often it occurs, and for time fields the first and last time. It NEVER prints a value: not
a temperature, a score, a status word, a name or an id. Written before the run exists (the Head of R&D, seq 6:
the answers are outcome data, and nothing else may open them).

  livedata_fields.py <probe run folder> <the committed job file>

It reads the files the manifest lists (never a folder walk). The run's own copy of the job must ask exactly what the
committed job file asks (ids, paths, parameters), or it refuses. Each stored answer is unpacked and its sha256 and its
length are checked against the manifest's (the runner records both for the UNPACKED body); a row with no sha256 is
refused. It refuses a HELDOUT_ path, a link and a path outside the run. A run that did not finish, or a request that
was refused or never sent, is REPORTED on its line and the other answers are still listed: for this probe "no answer"
is itself an answer (an old window that no longer exists).
Standard library only.
"""
import gzip
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from deskb_guard import refuse_all, refuse_heldout  # noqa: E402

TIME_KEY = re.compile(r"(^t$|^ts$|time|date|_ts$|_at$|timestamp|effective|expir|updated|created)", re.I)
SAFE_KEY = re.compile(r"[a-z][a-z_]{0,39}")      # a plain lowercase field name: letters and underscores only, no digit
TAG = " [field names only, no value]"


def inside(run, name):
    path = os.path.join(run, str(name))
    refuse_heldout(path)
    if not (os.path.realpath(path) + os.sep).startswith(os.path.realpath(run) + os.sep) or os.path.islink(path):
        sys.exit("REFUSED: %s is not a plain file of the run %s" % (path, run))
    return path


def as_time(v):
    """Seconds since 1970 if v looks like a time (an ISO string, or a number of seconds or milliseconds after 2001), else None."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        if 1e9 <= v < 1e11:
            return float(v)
        if 1e12 <= v < 1e14:
            return v / 1000.0
        return None
    if isinstance(v, str) and 10 <= len(v) <= 40 and v[:4].isdigit() and v[4:5] == "-":
        try:
            d = datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return None
        return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).timestamp()
    return None


def key_name(k, node):
    """A field name as printed. A key is printed only if it is a plain lowercase field name. Anything else (capitals,
    ANY digit, a dash, a dot: an id, a ticker, a station, a number) is printed as <key>, so no key can carry a number. So is every key of an
    object that has three or more keys whose values are all objects with one and the same set of keys: that is a map
    keyed by something, not a record."""
    if not SAFE_KEY.fullmatch(str(k)):
        return "<key>"
    vals = list(node.values())
    if len(vals) >= 3 and all(isinstance(v, dict) for v in vals) and len({tuple(sorted(v)) for v in vals}) == 1:
        return "<key>"
    return str(k)


def walk(node, path, out):
    """out[path] = {"n": occurrences, "types": {type: n}, "tmin": .., "tmax": .., "len": [min, max] for arrays}"""
    rec = out.setdefault(path, {"n": 0, "types": {}, "tmin": None, "tmax": None, "len": None})
    rec["n"] += 1
    kind = "null" if node is None else "bool" if isinstance(node, bool) else "number" if isinstance(node, (int, float)) else \
        "string" if isinstance(node, str) else "array" if isinstance(node, list) else "object"
    rec["types"][kind] = rec["types"].get(kind, 0) + 1
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, path + "." + key_name(k, node), out)
    elif isinstance(node, list):
        rec["len"] = [len(node), len(node)] if rec["len"] is None else [min(rec["len"][0], len(node)), max(rec["len"][1], len(node))]
        for v in node:
            walk(v, path + "[]", out)
    else:
        last = path.rsplit(".", 1)[-1].replace("[]", "")
        if TIME_KEY.search(last):
            t = as_time(node)
            if t is not None:
                rec["tmin"] = t if rec["tmin"] is None else min(rec["tmin"], t)
                rec["tmax"] = t if rec["tmax"] is None else max(rec["tmax"], t)


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    refuse_all()
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    run, job_path = sys.argv[1], sys.argv[2]
    refuse_heldout(run)
    refuse_heldout(job_path)
    man = json.load(open(inside(run, "manifest.json")))
    reqs = (man.get("job") or {}).get("requests")
    if not isinstance(reqs, list) or not reqs:
        sys.exit("REFUSED: the run's manifest does not carry its job")
    want = json.load(open(job_path))
    shape = lambda rs: [(r.get("id"), r.get("path"), json.dumps(r.get("params", {}), sort_keys=True), r.get("max_pages", 1)) for r in rs]
    if (man.get("job") or {}).get("job_id") != want.get("job_id") or shape(reqs) != shape(want.get("requests", [])):
        sys.exit("REFUSED: the run's job is not the committed job file (job id, request ids, paths or parameters differ)")
    print("job %s | %d requests, the same ids, paths and parameters as the committed job file%s" % (want.get("job_id"), len(reqs), TAG))
    rows = man.get("rows", [])
    asked = [r.get("id") for r in reqs]
    good = {r.get("id") for r in rows if r.get("status") == 200 and not r.get("truncated") and r.get("file")}
    print("LIVEDATA_PROBE_A field reader | requests asked %d | answered whole %d | run finished: %s%s" % (len(asked), len(good & set(asked)), "yes" if man.get("status") == "complete" else "NO", TAG))
    for rid in asked:
        mine = [r for r in rows if r.get("id") == rid]
        if not mine:
            print("%s: NOT SENT%s" % (rid, TAG))
            continue
        for r in sorted(mine, key=lambda r: int(r.get("page") or 1)):
            head = "%s page %s" % (rid, r.get("page") or 1)
            if r.get("status") != 200 or not r.get("file"):
                print("%s: HTTP %s, no answer stored%s" % (head, r.get("status"), TAG))
                continue
            try:
                raw = gzip.decompress(open(inside(run, r["file"]), "rb").read())
            except (OSError, EOFError):
                sys.exit("REFUSED: %s cannot be unpacked" % r["file"])
            if not r.get("sha256") or hashlib.sha256(raw).hexdigest() != r["sha256"] or r.get("bytes") != len(raw):
                sys.exit("REFUSED: %s does not match the sha256 and length the manifest records for its unpacked body" % r["file"])
            try:
                body = json.loads(raw.decode("utf-8"))
            except ValueError:
                print("%s: the answer is not JSON (%d bytes)%s" % (head, len(raw), TAG))
                continue
            out = {}
            walk(body, "$", out)
            print("%s: %d bytes, cut short by the runner: %s, %d distinct fields%s" % (head, len(raw), "yes" if r.get("truncated") else "no", len(out), TAG))
            for path in sorted(out):
                rec = out[path]
                types = ", ".join("%s x %d" % kv for kv in sorted(rec["types"].items()))
                extra = ""
                if rec["len"] is not None:
                    extra += " | array length %d to %d" % tuple(rec["len"])
                if rec["tmin"] is not None:
                    extra += " | times from %s to %s" % (iso(rec["tmin"]), iso(rec["tmax"]))
                print("  %s | %s%s" % (path, types, extra))
    print("nothing above is a value: no temperature, score or status word was printed; a key is shown only when it is a plain lowercase field name, and anything else is shown as <key>%s" % TAG)


if __name__ == "__main__":
    main()
