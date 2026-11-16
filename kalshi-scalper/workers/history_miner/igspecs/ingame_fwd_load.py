"""ingame_fwd_load.py: the forward engine loader for the sports-data ingame recorder (History Miner, Nov 16, 2026). Hand case IGFWD_HAND_CASE_NOV16.md.
Same walls as ingame_load.py 6ac835f4, forward window. Every listing gz file must be named by sha256 in the allow line.
  python3 -I ingame_fwd_load.py <ingame folder> <listing folder>   prints counts."""
import collections, csv, gzip, hashlib, io, json, os, sys, calendar, time
HERE = os.path.dirname(os.path.abspath(__file__))
START, CUT = 1794873600, 1797292800                 # 2026-11-17T00:00Z, 2026-12-15T00:00Z
DATES = tuple(time.strftime("%Y-%m-%d", time.gmtime(START + 86400 * i)) for i in range((CUT - START) // 86400))
SERIES = ("KXNHLGAME", "KXNBATOTAL", "KXNFLTOTAL", "KXNHLTOTAL", "KXNBASPREAD", "KXNFLSPREAD", "KXNHLSPREAD")
ALLOW_FILE = os.path.join(HERE, "..", "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the History Miner's forward ingame loader"


def self_sha():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


def refuse_unless_allowed(listing_hashes):
    try:
        text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "ingame_fwd_load.py" in line and self_sha() in line and all(h in line for h in listing_hashes):
            return
    raise SystemExit("REFUSED: no allow line names ingame_fwd_load.py with this file's sha256 %s and every listing file's sha256" % self_sha())


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
    files = sorted(f for f in os.listdir(listing) if f.endswith(".json.gz"))
    raws = {f: open(os.path.join(listing, f), "rb").read() for f in files}
    refuse_unless_allowed([hashlib.sha256(b).hexdigest() for b in raws.values()])
    cnt = collections.Counter(); mk = {}
    for f in files:
        mk.update(listing_markets(json.loads(gzip.decompress(raws[f])).get("markets", []), cnt))
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
