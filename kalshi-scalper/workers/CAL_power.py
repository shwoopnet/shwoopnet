"""CAL power check: COUNTS ONLY (no profit or loss is read or computed).
L1 entries (6 minute look, price 0.88 to 0.97) from scalper.tstop1.load(), whose
15 minute window closes within 30 minutes AFTER a calendar event (event < close <= event + 1800 s).
Usage (from kalshi-scalper/): PYTHONPATH=src python3 workers/CAL_power.py
"""
import csv, collections, datetime as dt
from scalper import tstop1

cal = list(csv.DictReader(open("studies/EVENT_CALENDAR_2026.csv")))
ev = collections.defaultdict(set)
for r in cal:
    if r["status"] == "unverified":
        continue
    if r["event"].startswith("MAINT_") and "trading or API scope" not in r["note"]:
        continue
    ts = int(dt.datetime.strptime(r["release_utc"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc).timestamp())
    ev[r["event"]].add(ts)
    if r["release_et"][11:16] == "08:30":
        ev["ANY_0830ET"].add(ts)

rows = [(r["series"], r["close_ts"]) for r in tstop1.load() if 0.88 - 1e-9 <= r["price"] <= 0.97 + 1e-9]
lo, hi = min(c for _, c in rows), max(c for _, c in rows)
print(f"entries in band: {len(rows)}; closes {dt.datetime.fromtimestamp(lo, dt.timezone.utc):%Y-%m-%d %H:%M}Z to {dt.datetime.fromtimestamp(hi, dt.timezone.utc):%Y-%m-%d %H:%M}Z")
LIVE5 = {"KXGOLD15M", "KXBTC15M", "KXETH15M", "KXDOGE15M", "KXXRP15M"}
print("| event type | events in data span | events with >=1 entry (days) | entries, all series | entries, live 5 | entry at or after release (all) | per series (all, top) |")
print("|---|---|---|---|---|---|---|")
out = {}
for k in sorted(ev):
    ts = sorted(t for t in ev[k] if lo - 1800 <= t <= hi)
    n = live = post = 0; days = set(); per = collections.Counter()
    for s, c in rows:
        hit = [t for t in ts if t < c <= t + 1800]
        if hit:
            n += 1; live += s in LIVE5; per[s] += 1
            days.add(dt.datetime.fromtimestamp(hit[0], dt.timezone.utc).date())
            post += (c - 360) >= hit[0]
    top = ", ".join(f"{s.replace('KX','').replace('15M','')} {v}" for s, v in per.most_common(6))
    out[k] = (n, len(days))
    print(f"| {k} | {len(ts)} | {len(days)} | {n} | {live} | {post} | {top} |")
print()
print("powered (>=300 entries on >=30 distinct event days):", [k for k, (n, d) in out.items() if n >= 300 and d >= 30] or "none")
