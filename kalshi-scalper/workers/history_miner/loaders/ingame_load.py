"""ingame_load.py: the engine loader for the sports-data ingame recorder (History Miner, Nov 16, 2026). Hand case INGAME_LOAD_HAND_CASE_NOV16.md.
Desk A's LOADER CONTRACT (Nov 16): allow line with this file's sha256 and every extract hash; directory wall, then the time column first, then the ticker wall, then results for kept rows only.
  python3 -I ingame_load.py <ingame folder (holds <date>/<HHMM>/obs.csv.gz)> <listing folder (the five gz pages)>   prints counts."""
import collections, csv, gzip, hashlib, io, json, os, sys, calendar, time
HERE = os.path.dirname(os.path.abspath(__file__))
START, CUT = 1794096000, 1794528000                 # 2026-11-08T00:00Z, 2026-11-13T00:00Z
DATES = ("2026-11-08", "2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12")
SERIES = ("KXNBATOTAL", "KXNFLTOTAL", "KXNHLGAME", "KXNHLTOTAL")
LISTING_SHA = {   # IG_RESULTS 2026-11-16T1306Z_43872534396 (3 pages), IG_RESULTS_NHL 2026-11-16T1339Z_43875945403 (2 pages); gz bytes
    "30bc6b5848f66e13f694b54a769a196e76542a6b8d82a84f2678eeeb7892046e", "e2f0c91c966d8de8df1342810ebde6e9048779a30c772852393903db61ebd56e",
    "cd2a17d6c11a2b35b3156a6c0e78a8e557cf746218fd9a18c197d7ed6b4e49b9", "0915bbb025d2b4c156605b4607b930093da55eacf5bc25952197eb0c00d2e469",
    "6c0c54ff567edea38e52b95f96022480bef806fd3efb0315db766eb3d08e4726"}
ALLOW_FILE = os.path.join(HERE, "..", "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by the History Miner's ingame loader"


def self_sha():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()


def refuse_unless_allowed():
    try:
        text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "ingame_load.py" in line and self_sha() in line and all(h in line for h in LISTING_SHA):
            return
    raise SystemExit("REFUSED: no allow line names ingame_load.py with this file's sha256 %s and the five listing hashes" % self_sha())


def series_of(ticker):
    return ticker.split("-", 1)[0]


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
    """rows: dicts; the t_recv_ms column FIRST, then the ticker wall, then the rest. -> [(ticker, end_ts, bid, ask, last, volume, oi=None, bid_size, ask_size, kind, event)]"""
    out = []
    for r in rows:
        t = num(r["t_recv_ms"])
        if t is None:
            cnt["row with no time (header or unreadable, dropped)"] += 1; continue
        t = int(t // 1000)
        if not START <= t < CUT:
            cnt["row outside the window (dropped)"] += 1; continue
        tk = r["ticker"]
        if series_of(tk) not in SERIES:
            cnt["row ticker outside the wall (dropped)"] += 1; continue
        out.append((tk, t, num(r["yes_bid"]), num(r["yes_ask"]), num(r["last_price"]), num(r["volume"]), None, num(r["bid_size"]), num(r["ask_size"]), r["kind"], r["event"]))
    return out


def listing_markets(markets, cnt):
    """close_time FIRST, then the ticker wall, then result for kept markets only. -> {ticker: (series, close_ts, result)}"""
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
        out[tk] = (series_of(tk), c, r if r in ("yes", "no") else "void")
    return out


def load(ingame, listing):
    refuse_unless_allowed()
    cnt = collections.Counter(); mk = {}
    for f in sorted(os.listdir(listing)):
        if not f.endswith(".json.gz"):
            continue
        raw = open(os.path.join(listing, f), "rb").read()
        if hashlib.sha256(raw).hexdigest() not in LISTING_SHA:
            raise SystemExit("REFUSED: listing file %s is not one of the five named" % f)
        mk.update(listing_markets(json.loads(gzip.decompress(raw)).get("markets", []), cnt))
    candles = collections.defaultdict(list)
    for d in DATES:
        dp = os.path.join(ingame, d)
        if not os.path.isdir(dp):
            cnt["missing date directory"] += 1; continue
        for run in sorted(os.listdir(dp)):
            f = os.path.join(dp, run, "obs.csv.gz")
            if not os.path.exists(f):
                continue
            for row in obs_rows(csv.DictReader(io.TextIOWrapper(gzip.open(f), encoding="utf-8", newline="")), cnt):
                tk = row[0]
                if tk not in mk:
                    cnt["candle of a ticker without a kept market (dropped)"] += 1; continue
                if row[1] > mk[tk][1]:
                    cnt["candle after close (dropped)"] += 1; continue
                candles[tk].append(row[1:])
    market = [(tk, s, c, r) for tk, (s, c, r) in sorted(mk.items())]
    candle = {tk: sorted(v) for tk, v in candles.items()}
    cnt["markets kept"] = len(market); cnt["candles kept"] = sum(len(v) for v in candle.values())
    return market, candle, dict(cnt)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    m, c, k = load(sys.argv[1], sys.argv[2])
    print(json.dumps({"counts": k, "loader_sha256": self_sha()}, indent=1, sort_keys=True))
