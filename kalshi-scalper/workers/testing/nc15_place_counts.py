#!/usr/bin/env python3
"""NC15 place counts file (Testing Desk, Nov 16, 2026): a JSON writer around Desk A's counting core nc15_wheel_counts.py (frozen v4 sheet). Counts only; reads no result column (the core reads book columns only).
Hand case: NC15_PLACE_COUNTS_HAND_CASE.md (committed first). Test: test_nc15_place_counts.py (invented counters and a stub core).
  python3 -I nc15_place_counts.py <folder holding nc15/> <out.json> <as_of YYYY-MM-DDTHH:MM:SSZ>
REFUSES unless the allow-list file has a line with the mark below naming this file's sha256 and the core's sha256, and unless the core's own sha256 is the pinned one."""
import calendar, hashlib, importlib.util, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PLACES = (("WH-NC15-SILVER", "KXSILVER15M"), ("WH-NC15-COPPER", "KXCOPPER15M"), ("WH-NC15-WTI", "KXWTI15M"), ("WH-NC15-HYPE", "KXHYPE15M"), ("WH-NC15-BNB", "KXBNB15M"), ("WH-NC15-USDCAD", "KXUSDCAD15M"), ("WH-NC15-NATGAS", "KXNATGAS15M"))
START_UTC, TARGET = "2026-11-13T02:40:00Z", 60
START_TS = calendar.timegm(time.strptime(START_UTC, "%Y-%m-%dT%H:%M:%SZ"))
CORE_FILE = os.path.join(HERE, "..", "desk_a_held", "nc15_wheel_counts.py")
CORE_SHA = "23f5932d7f3f2abd7e42a71ffacdf4accc31e6878312f8cccd41cee8a7f8f44c"          # Desk A's nc15_wheel_counts.py with count_places(root, start_ts=None) -> (st, closes), claude/idea-desk-a 1ac684a3c
CORE_FUNC = "count_places"
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the Testing Desk's NC15 place-count job"
ASOF_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def sha_of(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()
def self_sha(): return sha_of(os.path.abspath(__file__))


def refuse_unless_allowed(core_sha, allow_file=None):
    try: text = open(allow_file or ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow-list file cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    if not line or "nc15_place_counts.py" not in line[0] or self_sha() not in line[0] or core_sha not in line[0]: raise SystemExit("REFUSED: no allow-list line naming nc15_place_counts.py with sha256 %s and the core with sha256 %s" % (self_sha(), core_sha))


def load_core(core_file=None, core_sha=None, func=None):
    path, want = core_file or CORE_FILE, core_sha or CORE_SHA
    try: got = sha_of(path)
    except OSError: raise SystemExit("REFUSED: the counting core cannot be read")
    if got != want: raise SystemExit("REFUSED: the counting core sha256 %s is not the pinned %s" % (got, want))
    spec = importlib.util.spec_from_file_location("nc15_core", path); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    fn = getattr(mod, func or CORE_FUNC, None)
    if fn is None: raise SystemExit("REFUSED: the core has no %s" % (func or CORE_FUNC))
    return fn


PARKED = ("WH-NC15-SILVER", "WH-NC15-USDCAD")          # Head ruling Nov 16: parked under the rate rule; kept in the file


def build(counts, as_of):
    if not ASOF_RE.fullmatch(as_of or ""): raise SystemExit("REFUSED: as_of must be YYYY-MM-DDTHH:MM:SSZ")
    rows = []
    for pid, series in PLACES:
        if series not in counts: raise SystemExit("REFUSED: the core's answer has no %s" % series)
        n = counts[series].get("fill-checked", 0)          # the core's Counters hold only the keys that were incremented: an absent "fill-checked" is a true 0
        if not (type(n) is int and n >= 0): raise SystemExit("REFUSED: %s fill-checked is not a non-negative integer" % series)
        rows.append({"id": pid, "fill_checked_signals": n, "status": "parked" if pid in PARKED else "active", "target": TARGET, "start_utc": START_UTC, "as_of_utc": as_of})
    return {"places": rows}


def write(obj, out):
    tmp = out + ".tmp"
    with open(tmp, "w") as fh: json.dump(obj, fh, indent=1); fh.write("\n")
    os.replace(tmp, out)


def run(root, out, as_of, core_file=None, core_sha=None, func=None, allow_file=None):
    sha = core_sha or CORE_SHA; refuse_unless_allowed(sha, allow_file)
    counts, _closes = load_core(core_file, sha, func)(root, START_TS)          # (st, closes): only st, the per-series counters, is used
    obj = build(counts, as_of); write(obj, out); return obj


if __name__ == "__main__":
    if len(sys.argv) != 4: sys.exit(__doc__)
    run(sys.argv[1], sys.argv[2], sys.argv[3])
