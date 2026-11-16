"""ingame_fwd_load.py: the forward engine loader for the sports-data ingame recorder (History Miner, Nov 16, 2026). Hand case IGFWD_HAND_CASE_NOV16.md.
Same walls as ingame_load.py 6ac835f4, forward window. Auditor B's note 4: the allow line is bound to this file's sha256 and the sha256 of the committed job IG_FWD_RESULTS.json;
a listing RUN is accepted only if its manifest checks out (STATUS complete, embedded job equals the committed job, every body's sha256 and byte count equal its manifest row,
every row 200 and not truncated, pages 1..k per request with no cursor on the last, folder files equal manifest files plus STATUS and manifest.json).
  python3 -I ingame_fwd_load.py <ingame folder> <folder holding one or more listing run folders>   prints counts."""
import collections, csv, gzip, hashlib, io, json, os, sys, calendar, time
HERE = os.path.dirname(os.path.abspath(__file__))
START, CUT = 1794873600, 1797292800                 # 2026-11-17T00:00Z, 2026-12-15T00:00Z
DATES = tuple(time.strftime("%Y-%m-%d", time.gmtime(START + 86400 * i)) for i in range((CUT - START) // 86400))
SERIES = ("KXNHLGAME", "KXNBATOTAL", "KXNFLTOTAL", "KXNHLTOTAL", "KXNBASPREAD", "KXNHLSPREAD")
ALLOW_FILE = os.path.join(HERE, "..", "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the History Miner's forward ingame loader"
JOB_FILE = os.path.join(HERE, "IG_FWD_RESULTS.json")
JOB_SHA256 = "d535923d29b05c7d186985a242ec895736da757fc600640c7eba926ba6931b17"


def self_sha():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


def refuse_unless_allowed():
    try:
        text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "ingame_fwd_load.py" in line and self_sha() in line and JOB_SHA256 in line:
            return
    raise SystemExit("REFUSED: no allow line names ingame_fwd_load.py with this file's sha256 %s and the job sha256 %s" % (self_sha(), JOB_SHA256))


def check_run(run):
    """-> list of (page name, markets) for a run folder, or SystemExit. The structure check Auditor B asked for (note 4)."""
    raw_job = open(JOB_FILE, "rb").read()
    if hashlib.sha256(raw_job).hexdigest() != JOB_SHA256:
        raise SystemExit("REFUSED: IG_FWD_RESULTS.json is not the committed job")
    if open(os.path.join(run, "STATUS"), encoding="utf-8").read().strip() != "complete":
        raise SystemExit("REFUSED: %s STATUS is not complete" % run)
    man = json.load(open(os.path.join(run, "manifest.json"), encoding="utf-8"))
    if json.dumps(man["job"], sort_keys=True) != json.dumps(json.loads(raw_job), sort_keys=True):
        raise SystemExit("REFUSED: %s embedded job differs from the committed job" % run)
    if sorted(os.listdir(run)) != sorted([r["file"] for r in man["rows"]] + ["STATUS", "manifest.json"]):
        raise SystemExit("REFUSED: %s files differ from the manifest" % run)
    pages = collections.defaultdict(list); out = []
    for r in man["rows"]:
        body = gzip.decompress(open(os.path.join(run, r["file"]), "rb").read())
        if r["status"] != 200 or r["truncated"] or hashlib.sha256(body).hexdigest() != r["sha256"] or len(body) != r["bytes"]:
            raise SystemExit("REFUSED: %s row %s fails the manifest check" % (run, r["file"]))
        d = json.loads(body)
        if not isinstance(d, dict) or "markets" not in d:
            raise SystemExit("REFUSED: %s body %s is not a listing page" % (run, r["file"]))
        pages[r["id"]].append((r["page"], bool(d.get("cursor")))); out.append(d["markets"])
    for rid, pg in pages.items():
        pg.sort()
        if [x[0] for x in pg] != list(range(1, len(pg) + 1)) or pg[-1][1]:
            raise SystemExit("REFUSED: %s request %s has missing pages or a cursor on its last page" % (run, rid))
    return out


def series_of(t):
    return t.split("-", 1)[0]


def iso(s):
    try:
        return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return None


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def obs_rows(rows, cnt):
    out = []
    for r in rows:
        t = num(r["t_recv_ms"])
        if t is None:
            cnt["row with no time (dropped)"] += 1; continue
        t = int(t // 1000)
        if not START <= t < CUT:
            cnt["row outside the window (dropped)"] += 1; continue
        tk = r["ticker"]
        if series_of(tk) not in SERIES:
            cnt["row ticker outside the wall (dropped)"] += 1; continue
        out.append((tk, t, num(r["yes_bid"]), num(r["yes_ask"]), r["kind"], r["event"]))
    return out


def listing_markets(markets, cnt):
    out = {}
    for m in markets:
        c = iso(m["close_time"]) if isinstance(m["close_time"], str) else None
        if c is None or not START <= c < CUT:
            cnt["market outside the window (dropped)"] += 1; continue
        tk = m["ticker"]
        if series_of(tk) not in SERIES:
            cnt["market ticker outside the wall (dropped)"] += 1; continue
        r = m["result"]
        if r not in ("yes", "no"):
            cnt["market result not yes or no, mapped to void: %s" % series_of(tk)] += 1
        out[tk] = (c, r if r in ("yes", "no") else "void", m.get("occurrence_datetime"))
    return out


def load(ingame, listing):
    refuse_unless_allowed()
    cnt = collections.Counter(); mk = {}
    runs = sorted(d for d in os.listdir(listing) if os.path.isdir(os.path.join(listing, d)))
    for d in runs:
        for markets in check_run(os.path.join(listing, d)):
            mk.update(listing_markets(markets, cnt))
    cnt["listing runs accepted"] = len(runs)
    ev = {}
    for d in DATES:
        dp = os.path.join(ingame, d)
        if not os.path.isdir(dp):
            cnt["missing date directory"] += 1; continue
        for run in sorted(os.listdir(dp)):
            f = os.path.join(dp, run, "obs.csv.gz")
            if not os.path.exists(f):
                continue
            for tk, t, b, a, kind, event in obs_rows(csv.DictReader(io.TextIOWrapper(gzip.open(f), encoding="utf-8", newline="")), cnt):
                if tk not in mk:
                    cnt["row of a ticker without a kept market (dropped)"] += 1; continue
                if t > mk[tk][0]:
                    cnt["row after close (dropped)"] += 1; continue
                lg = series_of(tk)[2:5]; key = (lg, event.split("-", 1)[-1], kind)
                E = ev.setdefault(key, {"key": "%s|%s|%s" % key, "league": lg, "kind": kind, "rows": collections.defaultdict(list), "result": {}, "close": {}, "occ": {}})
                E["rows"][tk].append((t, b, a)); E["close"][tk], E["result"][tk], E["occ"][tk] = mk[tk]
    events = []
    for k in sorted(ev):
        E = ev[k]; E["rows"] = {tk: sorted(v) for tk, v in E["rows"].items()}; events.append(E)
    cnt["events built"] = len(events)
    return events, dict(cnt)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    e, c = load(sys.argv[1], sys.argv[2])
    print(json.dumps({"counts": c, "loader_sha256": self_sha()}, indent=1, sort_keys=True))
