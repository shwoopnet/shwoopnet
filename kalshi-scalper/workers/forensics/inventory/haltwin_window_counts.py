#!/usr/bin/env python3
"""HALTWIN (Desk C) fact 2, counts only (Forensics desk, Nov 14, 2026): per series, the number of listed windows lying WHOLLY inside 17:00 to 18:00 US Eastern on a Monday to Thursday, in the usable range
(first listed close to the series' binding cut of NC15_USABLE_WINDOWS_NOV14.md). A 15 minute window is (close minus 15 min, close]; wholly inside means open >= 17:00 and close <= 18:00 Eastern (closes at 17:15, 17:30, 17:45, 18:00),
on the same Eastern date, Monday to Thursday by that Eastern date. Reads only the ticker_allowlist of the seven NC15_CANDLES job files; no answer file.
usage: python3 -I haltwin_window_counts.py <folder with NC15_CANDLES_*.json>"""
import sys, json, glob, re, os, collections
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
ET = ZoneInfo("America/New_York"); MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
CUTS = {"KXSILVER15M": "2026-10-05T00:00", "KXCOPPER15M": "2026-10-05T00:00", "KXNATGAS15M": "2026-10-05T00:00", "KXWTI15M": "2026-10-03T16:00"}
tk = set()
for f in sorted(glob.glob(os.path.join(sys.argv[1], "NC15_CANDLES_*.json"))): tk |= set(json.load(open(f))["ticker_allowlist"])
by = collections.defaultdict(list)
for t in tk:
    m = re.match(r"^(KX[A-Z]+15M)-(\d{2})([A-Z]{3})(\d{2})(\d{2})(\d{2})-(\d{2})$", t)
    if not m or m.group(1) not in CUTS: continue
    s, yy, mo, dd, hh, mi, _ = m.groups(); by[s].append(datetime(2000 + int(yy), MON[mo], int(dd), int(hh), int(mi), tzinfo=ET))
for s in sorted(CUTS):
    cut = datetime.fromisoformat(CUTS[s]).replace(tzinfo=timezone.utc); v = sorted(by[s]); usable = [d for d in v if d.astimezone(timezone.utc) < cut]
    hit = []
    for d in usable:
        o = d - timedelta(minutes=15)
        if o.date() == d.date() and d.weekday() <= 3 and (o.hour, o.minute) >= (17, 0) and (d.hour, d.minute) <= (18, 0) and (d.hour, d.minute) > (17, 0): hit.append(d)
    print("%-12s usable windows %5d | wholly inside 17:00 to 18:00 ET Mon to Thu: %4d windows on %3d dates (first %s last %s)" % (s, len(usable), len(hit), len({d.date() for d in hit}), hit[0].strftime("%Y-%m-%d") if hit else "-", hit[-1].strftime("%Y-%m-%d") if hit else "-"))
