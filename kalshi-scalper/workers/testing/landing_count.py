#!/usr/bin/env python3
"""landing_count.py: how many files and windows each recorder's data branch actually holds, against what its schedule should have produced (Testing Desk, Nov 12, 2026).
Reads ONLY branch file listings (git ls-tree) and the small coverage.csv.gz files of R6, NC15 and the hourly ladder (counts of windows and polls; the `result` column is never read).
Sends no request, opens no data file, writes nothing. Run from any clone: python3 -I landing_count.py [--repo PATH] [--days N] [--fetch]
  --fetch   run `git fetch origin <branches>` first (needs network); otherwise it reads whatever the clone already has under origin/.
Prints one table: recorder, branch/folder, per UTC day found vs expected for the last N days (default 3), and a verdict (OK >= 90 percent, GAPS 50 to 90, FAILING under 50).
EXPECTED figures (and where each comes from; Main: check them against the workflow crons):
  R6 book15r6   96 windows a day per crypto series (15 minute windows, 24 hours; market structure). Cron 5,35 and 20,50 each hour. Gold is weekday-only so it is not scored.
  NC15 nc15     96 windows a day for the 24 hour series (BNB, HYPE); the forex, metal and energy series trade fewer hours, so their ratio is shown but the verdict uses the 24 hour series. Cron as R6.
  hourly book/  24 hourly Bitcoin events a day (one per top of the hour). Cron 50 3,7,11,15,19,23 and 20 every hour.
  combo         48 runs a day (cron 11,41 each hour = 2 an hour).
  perps30       2 files per weekday (open and close), 0 at weekends; 29 starts a day on weekdays since the Nov 12 repack (cron lines in record-perps-fast.yml).
  perps hourly  48 samples a day (cron 7,37 each hour) counted from the distinct ts_utc values would need a file open; the listing gives 1 file per date, so this script reports FILES only and notes 48 starts as the schedule.
  kalshi1m / funding  1 file per UTC date Monday to Saturday (cron 0 2,3,4 * * 1-6 for kalshi1m); 0 or 1 on Sunday.
  ingame        about 6 run folders a day (a cycle runs up to the next 4 hour bound, record_ingame.py docstring; cron 7,37 and 22,52 each hour only restart it).
  politics polrec  96 runs a day (cron 7,22,37,52 each hour); each run polls about 31 minutes.
"""
import argparse, collections, csv, gzip, io, subprocess, sys, datetime as dt

def git(repo, *a):
    return subprocess.run(["git", "-C", repo] + list(a), capture_output=True)

def tree(repo, br):
    r = git(repo, "ls-tree", "-r", "--name-only", "origin/" + br)
    return r.stdout.decode().split("\n") if r.returncode == 0 else []

def rows(repo, br, path):
    r = git(repo, "show", "origin/%s:%s" % (br, path))
    return list(csv.DictReader(io.StringIO(gzip.decompress(r.stdout).decode()))) if r.returncode == 0 else []

START = {"R6": "2026-10-29", "hourly ladder": "2026-10-29", "NC15": "2026-11-11", "combo": "2026-11-12", "politics": "2026-11-11", "ingame": "2026-11-08", "perps30": "2026-11-06",
         "kalshi1m": "2026-11-06", "funding": "2026-11-06", "perps hourly (files only)": "2026-10-21"}      # first UTC day each recorder has data (from the branch history); the start day counts as a partial day


def verdict(f, e):
    if e == 0: return "n/a"
    q = f / e
    return "OK" if q >= 0.9 else ("GAPS" if q >= 0.5 else "FAILING")

def run(repo, days, today):
    D = [(today - dt.timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]
    out = []
    def add(name, where, expected, found_by_day, note=""):
        for d in D:
            e = expected(d) if callable(expected) else expected
            f = found_by_day.get(d, 0)
            st = START.get(name, "0000-00-00")
            v = "not started" if d < st else ("partial day" if d == today.isoformat() or d == st else verdict(f, e))
            out.append((name, where, d, f, e, v, note))
    # R6: Bitcoin windows with polls by close-time date
    w = collections.defaultdict(set)
    for p in tree(repo, "quote-data"):
        if p.startswith("book15r6/") and p.endswith("coverage.csv.gz"):
            for r in rows(repo, "quote-data", p):
                if r.get("series") == "KXBTC15M" and r.get("ticker") and int(float(r.get("ok_polls") or 0)) > 0: w[r["close_time"][:10]].add(r["close_time"])
    add("R6", "quote-data book15r6 KXBTC15M windows with polls", 96, {k: len(v) for k, v in w.items()})
    # hourly ladder events
    h = collections.defaultdict(set)
    for p in tree(repo, "quote-data"):
        if p.startswith("book/") and p.endswith("coverage.csv.gz"):
            for r in rows(repo, "quote-data", p):
                if r.get("close_time") and int(float(r.get("ok_polls") or 0)) > 0: h[r["close_time"][:10]].add(r["close_time"])
    add("hourly ladder", "quote-data book/ events with polls", 24, {k: len(v) for k, v in h.items()})
    # NC15, 24 hour series only
    n = collections.defaultdict(set)
    for p in tree(repo, "nc-data"):
        if p.startswith("nc15/") and p.endswith("coverage.csv.gz"):
            for r in rows(repo, "nc-data", p):
                if r.get("series") in ("KXBNB15M", "KXHYPE15M") and r.get("ticker") and int(float(r.get("ok_polls") or 0)) > 0: n[(r["series"], r["close_time"][:10])].add(r["close_time"])
    for s in ("KXBNB15M", "KXHYPE15M"):
        add("NC15", "nc-data nc15 %s windows with polls" % s, 96, {d: len(v) for (ss, d), v in n.items() if ss == s})
    # file or run-folder counts per date
    def by_date(br, prefix, depth_sub=True, suffix=None):
        c = collections.defaultdict(set)
        for p in tree(repo, br):
            if p.startswith(prefix) and (suffix is None or p.endswith(suffix)):
                parts = p.split("/")
                c[parts[1]].add("/".join(parts[:3]))
        return {k: len(v) for k, v in c.items()}
    add("combo", "combo-data combo/ run folders", 48, by_date("combo-data", "combo/"))
    add("politics", "pol-data polrec/ run folders", 96, by_date("pol-data", "polrec/"))
    add("ingame", "sports-data ingame/ run folders", 6, by_date("sports-data", "ingame/"))
    wk = lambda d: 2 if dt.date.fromisoformat(d).weekday() < 5 else 0
    p30 = collections.defaultdict(int)
    for p in tree(repo, "perp-data"):
        if p.startswith("perps30/"): p30[p.split("/")[1]] += 1
    add("perps30", "perp-data perps30/ files (open+close)", wk, dict(p30))
    for nm, pre in (("kalshi1m", "kalshi1m/"), ("funding", "funding/"), ("perps hourly (files only)", "perps/perps-")):
        f = {}
        for p in tree(repo, "perp-data"):
            if p.startswith(pre): f[p.split("/")[1].replace("perps-", "").replace(".csv.gz", "").replace(".csv", "")] = 1
        add(nm, "perp-data " + pre, (lambda d: 0 if dt.date.fromisoformat(d).weekday() == 6 and nm != "perps hourly (files only)" else 1), f, "perps hourly: samples a day not counted here (schedule 48)" if nm.startswith("perps hourly") else "")
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("--days", type=int, default=3); ap.add_argument("--fetch", action="store_true"); ap.add_argument("--today")
    a = ap.parse_args()
    if a.fetch: git(a.repo, "fetch", "-q", "origin", "quote-data", "nc-data", "combo-data", "perp-data", "sports-data", "pol-data")
    today = dt.date.fromisoformat(a.today) if a.today else dt.datetime.now(dt.timezone.utc).date()
    print("%-26s %-52s %-10s %6s %8s  %s" % ("recorder", "what is counted", "UTC day", "found", "expected", "verdict"))
    for r in run(a.repo, a.days, today): print("%-26s %-52s %-10s %6d %8d  %s %s" % r)
