#!/usr/bin/env python3
"""OICORE-NC15 thresholds, build 2 (History Miner, Nov 14, 2026), from the Head's texts of 06:24Z, 06:34Z and 06:38Z and Desk A's frozen definitions v5
(claude/idea-desk-a 0dd16134), sections 1, 3 and 7. Desk B's code is not read (rule 16b). Hand case: OICNC15T2_HAND_CASE_NOV14.md.

Usage (run from outside the data folders, with python3 -I):
  python3 -I oicnc15t2.py <out.json> --run <candles folder> --job <its job file> [--run ... --job ...]  (the four OICAND candle runs, each with its job)

Thresholds only: reads ticker, end_period_ts, open_interest_fp and open_interest of KXHYPE15M and KXBNB15M candles. No price, volume, quote or result.
The OICAND lists run is never opened."""
import calendar, gzip, hashlib, json, math, os, re, sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402  (reused unchanged: listed_runs() reads and prints the list line)

ALLOWED_SERIES = ("KXHYPE15M", "KXBNB15M")                      # the Head, 06:34Z: any other series stops the reader
ALLOWED_RUNS = frozenset((                                       # the Head, 06:38Z: one constant, no flag; the lists run is left out (hand case, flagged)
    "2026-11-14T0253Z_43548715053",                              # OICAND_CANDLES_1
    "2026-11-14T0501Z_43559459347",                              # OICAND_CANDLES_1_REST
    "2026-11-14T0413Z_43555574326",                              # OICAND_CANDLES_2
    "2026-11-14T0541Z_43562765461",                              # OICAND_CANDLES_2_REST
))
BASE_JOBS = ("OICAND_CANDLES_1", "OICAND_CANDLES_2")              # every id of these two is answered exactly once across the runs
T_DAY = "2026-11-13"                                              # T is printed for this US Central day (hand case, flagged)
WINDOW_DAYS, PCT = 20, 0.9
MIN_T = 5
EVENT830_CUTS = tuple(calendar.timegm((2026, 11, d, 13, 30, 0)) for d in (5, 6, 10, 12))
CUT_SLACK = 300
END_TO_CLOSE = 120                                                # a request's end_ts is close - 120 s (the job's purpose: 7 to 2 minutes before each close)
STATUSES = ("complete", "stopped_time")
MON = {m: i for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}
TICK = re.compile(r"^([A-Z0-9]+)-(\d{2})([A-Z]{3})(\d{2})(\d{2})(\d{2})-[A-Z0-9]+$")


class Stop(Exception):
    pass


# ---- guard (reader-specific; hm_guard.py unchanged)
def guard_path(path, list_file=None):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)):
            raise SystemExit("REFUSED: %s lies in or resolves into a HELDOUT_ folder (standing rule (h))" % path)
    runs = hm_guard.listed_runs(list_file) - ALLOWED_RUNS
    for p in (os.path.abspath(path), os.path.realpath(path)):
        hit = runs.intersection(p.split(os.sep))
        if hit:
            raise SystemExit("REFUSED: %s is, or lies inside, the landed run %s, listed as held-out and not allowed for this reader" % (path, sorted(hit)[0]))


def guard_all(args, list_file=None):
    guard_path(os.getcwd(), list_file)
    for a in args:
        guard_path(a, list_file)


# ---- clocks
def nth_sunday(y, mo, n):
    d = 1 + (6 - calendar.weekday(y, mo, 1)) % 7
    return d + 7 * (n - 1)


def us_dst(y, mo, d, h):
    """US daylight saving in local wall time: from the 2nd Sunday of March 02:00 to the 1st Sunday of November 02:00."""
    start = (3, nth_sunday(y, 3, 2), 2)
    end = (11, nth_sunday(y, 11, 1), 2)
    return start <= (mo, d, h) < end


def eastern_epoch(y, mo, d, hh, mm):
    off = 4 if us_dst(y, mo, d, hh) else 5
    return calendar.timegm((y, mo, d, hh, mm, 0)) + off * 3600


def central_day(ts):
    """The US Central calendar day of a UTC epoch second."""
    u = datetime.fromtimestamp(ts, timezone.utc)
    for off in (5, 6):                       # try CDT then CST; the right one gives a local time whose DST state matches
        loc = datetime.fromtimestamp(ts - off * 3600, timezone.utc)
        if us_dst(loc.year, loc.month, loc.day, loc.hour) == (off == 5):
            return loc.strftime("%Y-%m-%d")
    return datetime.fromtimestamp(ts - 6 * 3600, timezone.utc).strftime("%Y-%m-%d")   # the repeated hour in November: standard time


def ticker_close(t):
    m = TICK.match(t)
    if not m:
        raise Stop("unreadable ticker %s" % t)
    _s, yy, mon, dd, hh, mi = m.groups()
    if mon not in MON:
        raise Stop("unreadable month in %s" % t)
    return eastern_epoch(2000 + int(yy), MON[mon], int(dd), int(hh), int(mi))


# ---- runs
def load_run(folder, job):
    mf = os.path.join(folder, "manifest.json")
    m = json.load(open(mf))
    if m.get("job") != job:
        raise Stop("the run's job is not the committed job: %s" % folder)
    if m.get("status") not in STATUSES:
        raise Stop("run status %r is not complete or stopped_time: %s" % (m.get("status"), folder))
    reqs = {r["id"]: r for r in job["requests"]}
    out = {}
    root = os.path.realpath(folder)
    for row in m.get("rows", []):
        if row.get("status") != 200:
            continue
        if row.get("truncated"):
            raise Stop("truncated row %s" % row.get("id"))
        if row.get("id") not in reqs:
            raise Stop("row for an id not in the job: %s" % row.get("id"))
        if row.get("page", 1) != 1:
            raise Stop("a candle request with more than one page: %s" % row["id"])
        p = os.path.realpath(os.path.join(folder, row["file"]))
        if os.path.dirname(p) != root:
            raise Stop("file outside run: %s" % row["file"])
        raw = gzip.open(p, "rb").read()
        if hashlib.sha256(raw).hexdigest() != row.get("sha256") or len(raw) != row.get("bytes"):
            raise Stop("sha or length mismatch %s" % row["file"])
        if row["id"] in out:
            raise Stop("id answered twice in one run: %s" % row["id"])
        out[row["id"]] = (reqs[row["id"]], json.loads(raw))
    return out


def merge(runs_and_jobs):
    base = {}
    for _folder, job in runs_and_jobs:
        if job["job_id"] in BASE_JOBS:
            for r in job["requests"]:
                base[r["id"]] = r
    if not base:
        raise Stop("neither base job given")
    got = {}
    for folder, job in runs_and_jobs:
        for rid, (req, body) in load_run(folder, job).items():
            if rid in got:
                raise Stop("request id answered in two runs: %s" % rid)
            if rid not in base or base[rid] != req:
                raise Stop("request %s differs from the base job's request of the same id" % rid)
            got[rid] = (req, body)
    missing = sorted(set(base) - set(got))
    if missing:
        raise Stop("request ids answered in no run: %s" % ",".join(missing[:5]))
    return {k: got[k] for k in sorted(got)}


def oi_value(c):
    """F1: open_interest_fp first (a string), else open_interest; null, blank, non-finite or bool is unreadable (None)."""
    v = c["open_interest_fp"] if "open_interest_fp" in c else c.get("open_interest")
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, str):
        if not v.strip():
            return None
        try:
            v = float(v)
        except ValueError:
            return None
    if not isinstance(v, (int, float)) or not math.isfinite(v):
        return None
    return float(v)


def thresholds(merged, series=ALLOWED_SERIES):
    for s in series:
        if s not in ALLOWED_SERIES:
            raise Stop("series %s is not allowed for this reader" % s)
    t_day_start = None
    y, mo, d = map(int, T_DAY.split("-"))
    for off in (5, 6):                                        # 00:00 US Central of T_DAY
        cand = calendar.timegm((y, mo, d, 0, 0, 0)) + off * 3600
        if central_day(cand) == T_DAY and central_day(cand - 1) != T_DAY:
            t_day_start = cand
    occ, skipped_other = {}, 0
    for rid, (req, body) in merged.items():
        close = int(req["params"]["end_ts"]) + END_TO_CLOSE
        for mk in body.get("markets", []):
            t = mk.get("market_ticker")
            s = t.split("-")[0] if isinstance(t, str) else None
            if s not in series:
                skipped_other += 1
                continue
            if ticker_close(t) != close:
                raise Stop("close of %s (%d) does not match its request's end_ts + 120 (%d)" % (t, ticker_close(t), close))
            occ.setdefault(t, []).append((rid, close, mk))
    out = {}
    for s in series:
        rec = {"windows_seen": 0, "dropped": {"event830_cut": 0, "missing_candle": 0, "no_open_interest": 0, "repeated_ticker": 0, "outside_20_days": 0}}
        rises_by_day = {}
        for t in sorted(x for x in occ if x.split("-")[0] == s):
            rows = occ[t]
            rec["windows_seen"] += len(rows)
            if len(rows) > 1:
                rec["dropped"]["repeated_ticker"] += len(rows)
                continue
            _rid, close, mk = rows[0]
            if any(abs(close - c) <= CUT_SLACK for c in EVENT830_CUTS):
                rec["dropped"]["event830_cut"] += 1
                continue
            if close >= t_day_start:
                raise Stop("a window closing on or after T's day start: %s" % t)
            byend = {}
            for c in mk.get("candlesticks", []):
                e = int(c["end_period_ts"])
                if e in byend:
                    raise Stop("two candles with one end for %s" % t)
                byend[e] = c
            a, b = byend.get(close - 180), byend.get(close - 360)
            if a is None or b is None:
                rec["dropped"]["missing_candle"] += 1
                continue
            va, vb = oi_value(a), oi_value(b)
            if va is None or vb is None:
                rec["dropped"]["no_open_interest"] += 1
                continue
            rises_by_day.setdefault(central_day(close), []).append(va - vb)
        days = sorted(d_ for d_ in rises_by_day if d_ < T_DAY)
        used = days[-WINDOW_DAYS:]
        rec["dropped"]["outside_20_days"] = sum(len(rises_by_day[d_]) for d_ in days[:-WINDOW_DAYS]) if len(days) > WINDOW_DAYS else 0
        rises = sorted(r for d_ in used for r in rises_by_day[d_])
        n = len(rises)
        rank = math.ceil(PCT * n - 1e-12) if n else 0
        T = rises[rank - 1] if n else None
        why = []
        if len(days) < WINDOW_DAYS: why.append("fewer than 20 trading days (%d)" % len(days))
        if T is None: why.append("no rise")
        elif T == 0: why.append("T is 0")
        elif T < MIN_T: why.append("T under 5 contracts")
        rec.update({"trading_days_available": len(days), "trading_days_used": len(used), "first_day_used": used[0] if used else None,
                    "last_day_used": used[-1] if used else None, "n": n, "rank": rank, "T": T, "seated": not why and T is not None, "not_seated_reason": why})
        out[s] = rec
    return {"T_day_us_central": T_DAY, "series": out, "other_series_candle_sets_skipped_unread": skipped_other,
            "label": "thresholds only: open interest fields of the allowed series; no price, volume, quote or result read; the OICAND lists run is not opened"}


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__); return 2
    out_path, rest = argv[0], argv[1:]
    runs, jobs = [], []
    i = 0
    while i < len(rest):
        if rest[i] == "--run": runs.append(rest[i + 1])
        elif rest[i] == "--job": jobs.append(rest[i + 1])
        else: raise SystemExit("unknown argument %s" % rest[i])
        i += 2
    guard_all([out_path] + runs + jobs)
    try:
        if len(runs) != len(jobs) or not runs:
            raise Stop("give one --job per --run")
        merged = merge([(r, json.load(open(j))) for r, j in zip(runs, jobs)])
        res = thresholds(merged)
    except Stop as e:
        res = {"stopped": str(e)}
    with open(out_path, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True); f.write("\n")
    print(json.dumps(res, sort_keys=True)[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
