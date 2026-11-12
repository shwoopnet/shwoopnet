"""MMMAP1 (workers/MMMAP1_REGISTRATION.md): realized-spread map of the recorded books.
Offline: reads recorder branches through git, no network, no outcome (the coverage `result` column is dropped at read).
Refuses to run until the registration is committed, clean and pushed. Run: python3 -I src/scalper/mmmap1.py"""
import csv, gzip, io, subprocess, sys, os, random, statistics, collections, datetime as dt

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REG = "kalshi-scalper/workers/MMMAP1_REGISTRATION.md"
PUSHED_REF = "origin/claude/epic-ptolemy-0amjd9"
HOURLY_CUTOFF_MS = int(dt.datetime(2026, 11, 7, 15, 0, 0, tzinfo=dt.timezone.utc).timestamp() * 1000)
HOURLY_MAX_DIR = "2026-11-07"
HORIZONS = (30, 60, 180)
SNAP_LAG_MS = 10_000          # a snapshot must be within 10 s before the trade (and of the markout target)
GAP_MAX_MS = 15_000
DROP_LAST_MS = 60_000
CELL_MIN = 30
Q_R60, Q_TRADES, Q_DATES, Q_TOUCH = 0.5, 500, 3, 2000
DRAWS, SEED = 2000, 20261112


def git(*a):
    return subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, check=True).stdout


def registration_ok():
    """True only when the registration is committed, unmodified and contained in the pushed branch."""
    try:
        sha = git("log", "-1", "--format=%H", "--", REG).decode().strip()
        if not sha: return False, "registration not committed"
        if git("status", "--porcelain", "--", REG).strip(): return False, "registration has uncommitted changes"
        git("merge-base", "--is-ancestor", sha, PUSHED_REF)
        return True, sha
    except Exception as e:
        return False, "registration not on %s (%s)" % (PUSHED_REF, type(e).__name__)


def fnum(x):
    try:
        v = float(x)
        return v if v == v else None
    except Exception:
        return None


def parse_ms(s):
    return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000)


def snap_from_row(t, r):
    """(t_ms, yes_bid, yes_bid_size, no_bid, no_bid_size) or None when a side is empty."""
    y, ys, n, ns = fnum(r.get("yes_bid_px_1")), fnum(r.get("yes_bid_sz_1")), fnum(r.get("no_bid_px_1")), fnum(r.get("no_bid_sz_1"))
    if y is None or n is None or y <= 0 or n <= 0: return None
    return (t, y, ys or 0.0, n, ns or 0.0)


def mid_of(s): return (s[1] + (1.0 - s[3])) / 2.0


def window_records(snaps, trades, close_ms, max_gap_ms=0):
    """snaps: sorted list of (t_ms, y, ysz, n, nsz) or None-for-unusable as (t_ms,) ; trades: (t_ms, x, count, side).
    Returns (records, qhalf_sum, qhalf_n, span_ms, dropped_window). Uses no outcome."""
    ts = [s[0] for s in snaps]
    if not ts: return [], 0.0, 0, 0, False
    gaps = max([b - a for a, b in zip(ts, ts[1:])] or [0])
    if max(gaps, max_gap_ms) > GAP_MAX_MS: return [], 0.0, 0, 0, True
    use = [s for s in snaps if len(s) == 5]
    ut = [s[0] for s in use]
    qs = [(1.0 - s[1] - s[3]) / 2.0 for s in use if s[0] <= close_ms - DROP_LAST_MS]
    import bisect
    recs = []
    for (t, x, cnt, side) in trades:
        if t > close_ms - DROP_LAST_MS or x is None or cnt is None: continue
        i = bisect.bisect_right(ut, t) - 1
        if i < 0 or t - ut[i] > SNAP_LAG_MS: continue
        s0 = use[i]; mid0 = mid_of(s0); sg = 1 if side == "yes" else -1
        e = sg * (x - mid0) * 100
        m = {}
        for h in HORIZONS:
            target = t + h * 1000
            j = bisect.bisect_left(ut, target)
            m[h] = sg * (mid_of(use[j]) - mid0) * 100 if j < len(use) and use[j][0] - target <= SNAP_LAG_MS else None
        touch = s0[4] if sg == 1 else s0[2]
        recs.append({"t": t, "close": close_ms, "e": e, "m": m, "r60": (e - m[60]) if m[60] is not None else None,
                     "cnt": cnt, "touch": touch, "touch_min": min(s0[2], s0[4]), "frac": abs(cnt - round(cnt)) > 1e-9})
    return recs, sum(qs), len(qs), (ts[-1] - ts[0]), False


def block_of(r): return (dt.datetime.fromtimestamp(r["t"] / 1000, dt.timezone.utc).hour // 4) * 4
def bucket_of(r):
    left = (r["close"] - r["t"]) / 60000.0
    return "15-10" if left >= 10 else ("10-5" if left >= 5 else "5-1")
def date_of(r): return dt.datetime.fromtimestamp(r["close"] / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def mean(x): return sum(x) / len(x) if x else None


def boot_r60(wins, rng):
    """wins: {window: [r60 values]}; 90% interval of the mean by resampling whole windows (ratio of sums)."""
    agg = [(sum(v), len(v)) for v in wins.values() if v]
    if len(agg) < 2: return None, None
    out = []
    for _ in range(DRAWS):
        s = n = 0
        for _k in range(len(agg)):
            a = agg[rng.randrange(len(agg))]; s += a[0]; n += a[1]
        out.append(s / n)
    out.sort()
    return out[int(0.05 * DRAWS)], out[int(0.95 * DRAWS) - 1]


def summarize(series_windows):
    """series_windows: list of dicts {key, recs, qsum, qn, span}. Returns the per-series stats dict."""
    recs = [r for w in series_windows for r in w["recs"]]
    r60 = [r for r in recs if r["r60"] is not None]
    wins = collections.defaultdict(list)
    for w in series_windows:
        wins[w["key"]] = [r["r60"] for r in w["recs"] if r["r60"] is not None]
    lo, hi = boot_r60(wins, random.Random(SEED))
    dates = sorted({date_of(r) for r in r60})
    cnts = sum(r["cnt"] for r in recs)
    span_h = sum(w["span"] for w in series_windows) / 3.6e6
    qn = sum(w["qn"] for w in series_windows)
    out = {"trades": len(recs), "n_r60": len(r60), "contracts": cnts, "dates": len(dates), "windows": len([w for w in series_windows if w["recs"]]),
           "qhalf": (sum(w["qsum"] for w in series_windows) / qn * 100) if qn else None,
           "e": mean([r["e"] for r in recs])}
    for h in HORIZONS: out["m%d" % h] = mean([r["m"][h] for r in recs if r["m"][h] is not None])
    out["r60"] = mean([r["r60"] for r in r60]); out["lo"], out["hi"] = lo, hi
    out["r60w"] = (sum(r["r60"] * r["cnt"] for r in r60) / sum(r["cnt"] for r in r60)) if r60 and sum(r["cnt"] for r in r60) else None
    out["touch"] = statistics.median([r["touch"] for r in recs]) if recs else None
    out["touch_min"] = statistics.median([r["touch_min"] for r in recs]) if recs else None
    out["cph"] = cnts / span_h if span_h else None
    out["fracshare"] = (sum(r["cnt"] for r in recs if r["frac"]) / cnts) if cnts else None
    why = []
    if out["r60"] is None or out["r60"] < Q_R60: why.append("r60")
    if out["lo"] is None or out["lo"] <= 0: why.append("interval")
    if len(r60) < Q_TRADES: why.append("trades")
    if len(dates) < Q_DATES: why.append("dates")
    if out["touch"] is None or out["touch"] >= Q_TOUCH: why.append("touch")
    out["qualifies"] = not why; out["why"] = why
    return out


def cells(recs, keyf, keys):
    res = {}
    for k in keys:
        sub = [r for r in recs if keyf(r) == k]
        r60 = [r["r60"] for r in sub if r["r60"] is not None]
        res[k] = (len(sub), None if len(sub) < CELL_MIN else {"e": mean([r["e"] for r in sub]), "m60": mean([r["m"][60] for r in sub if r["m"][60] is not None]), "r60": mean(r60)})
    return res


def f(x, d=2): return "  n/a" if x is None else ("%.*f" % (d, x))


def report(by_series, out=print):
    out("series | trades | n_r60 | contracts | dates | windows | qhalf c | e c | m30 | m60 | m180 | r60 c | r60 lo | r60 hi | r60 cw | touch | touch_min | contracts/h | frac share | qualifies")
    for s in sorted(by_series):
        st = summarize(by_series[s])
        out(" | ".join([s, str(st["trades"]), str(st["n_r60"]), "%.0f" % st["contracts"], str(st["dates"]), str(st["windows"]), f(st["qhalf"]), f(st["e"]), f(st["m30"]), f(st["m60"]), f(st["m180"]),
                        f(st["r60"]), f(st["lo"]), f(st["hi"]), f(st["r60w"]), f(st["touch"], 0), f(st["touch_min"], 0), f(st["cph"], 0), f(st["fracshare"]),
                        "yes" if st["qualifies"] else "no (" + ",".join(st["why"]) + ")"]))
    out("")
    for s in sorted(by_series):
        recs = [r for w in by_series[s] for r in w["recs"]]
        for title, keyf, keys in (("UTC 4h block", block_of, (0, 4, 8, 12, 16, 20)), ("minutes to close", bucket_of, ("15-10", "10-5", "5-1"))):
            c = cells(recs, keyf, keys)
            out("%s by %s: " % (s, title) + "; ".join("%s n=%d %s" % (k, c[k][0], "blank (thin)" if c[k][1] is None else "e %s m60 %s r60 %s" % (f(c[k][1]["e"]), f(c[k][1]["m60"]), f(c[k][1]["r60"]))) for k in keys))


# ---------- loading (git only) ----------
def lines(sha_path):
    try: return gzip.decompress(git("show", sha_path)).decode()
    except Exception: return None


def load_fifteen(ref, prefix):
    """book15r6 / nc15 style: book, trades, coverage per job directory. Returns {series: [window dicts]}."""
    paths = git("ls-tree", "-r", "--full-tree", "--name-only", ref).decode().split("\n")
    jobs = sorted({p.rsplit("/", 1)[0] for p in paths if p.startswith(prefix + "/") and p.endswith("book.csv.gz")})
    by = collections.defaultdict(dict)
    for j in jobs:
        bk, tr, cv = (lines("%s:%s/%s.csv.gz" % (ref, j, n)) for n in ("book", "trades", "coverage"))
        if bk is None or tr is None: continue
        gap = {}
        if cv:
            for r in csv.DictReader(io.StringIO(cv)):
                r.pop("result", None)                       # never read an outcome
                gap[r.get("ticker")] = fnum(r.get("max_gap_ms")) or 0
        snaps = collections.defaultdict(list); close = {}; ser = {}
        for r in csv.DictReader(io.StringIO(bk)):
            t = int(r["t_recv_ms"]); tk = r["ticker"]
            snaps[tk].append(snap_from_row(t, r) or (t,)); close[tk] = parse_ms(r["close_time"]); ser[tk] = r["series"]
        trd = collections.defaultdict(list)
        for r in csv.DictReader(io.StringIO(tr)):
            trd[r["ticker"]].append((parse_ms(r["created_time"]), fnum(r["yes_price_dollars"]), fnum(r["count_fp"]), r["taker_outcome_side"]))
        for tk, sn in snaps.items():
            sn.sort(key=lambda s: s[0]); trd[tk].sort()
            recs, qs, qn, span, dropped = window_records(sn, trd[tk], close[tk], gap.get(tk, 0))
            if dropped: continue
            by[ser[tk]][tk] = {"key": tk, "recs": recs, "qsum": qs, "qn": qn, "span": span}   # later job for the same ticker overwrites
    return {s: list(d.values()) for s, d in by.items()}


def load_hourly(ref="origin/quote-data"):
    paths = git("ls-tree", "-r", "--full-tree", "--name-only", ref).decode().split("\n")
    jobs = sorted({p.rsplit("/", 1)[0] for p in paths if p.startswith("book/") and p.endswith("book.csv.gz") and p.split("/")[1] <= HOURLY_MAX_DIR})
    snaps = collections.defaultdict(list); close = {}; trd = collections.defaultdict(dict)
    for j in jobs:
        bk, tr = lines("%s:%s/book.csv.gz" % (ref, j)), lines("%s:%s/trades.csv.gz" % (ref, j))
        if bk is None: continue
        for r in csv.DictReader(io.StringIO(bk)):
            c = parse_ms(r["close_time"])
            if c >= HOURLY_CUTOFF_MS: continue              # held-out events are dropped before anything is computed
            t = int(r["poll_ts_local_ms"]); tk = r["ticker"]; snaps[tk].append(snap_from_row(t, r) or (t,)); close[tk] = c
        for r in csv.DictReader(io.StringIO(tr or "poll_ts_local_ms,ticker,created_time,yes_price_dollars,count_fp,taker_outcome_side,trade_id\n")):
            if r["ticker"] in close:
                trd[r["ticker"]][r["trade_id"]] = (parse_ms(r["created_time"]), fnum(r["yes_price_dollars"]), fnum(r["count_fp"]), r["taker_outcome_side"])
    out = []
    for tk, sn in snaps.items():
        sn = sorted(set(sn), key=lambda s: s[0])
        recs, qs, qn, span, dropped = window_records(sn, sorted(trd[tk].values()), close[tk], 0)
        if not dropped: out.append({"key": tk, "recs": recs, "qsum": qs, "qn": qn, "span": span})
    return {"KXBTCD": out}


def main():
    ok, why = registration_ok()
    if not ok:
        print("REFUSED: " + why + ". Commit and push workers/MMMAP1_REGISTRATION.md first."); return 2
    for r in ("origin/quote-data", "origin/nc-data"):
        git("fetch", "-q", "origin", r.split("/")[1])
    by = {}
    by.update(load_hourly()); by.update(load_fifteen("origin/quote-data", "book15r6"))
    for s, w in load_fifteen("origin/nc-data", "nc15").items(): by[s] = w
    print("MMMAP1 registration %s; hourly ladder restricted to closes before 2026-11-07T15:00Z; no outcome read." % why[:8])
    report(by)
    return 0


if __name__ == "__main__":
    sys.exit(main())
