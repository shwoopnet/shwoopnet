#!/usr/bin/env python3
"""Counts the NC15 windows a new card may read (Forensics desk, Nov 14, 2026). Reads only the ticker_allowlist of the seven NC15_CANDLES job files (no answer file, no list run).
A ticker KX<NAME>15M-YYMMMDDHHMM-mm has its close time in US Eastern (HHMM); it is converted to UTC. CUTS are the binding fixed cuts of NC15_USABLE_WINDOWS_NOV14.md (UTC, window usable if close < cut).
usage: python3 -I nc15_usable_windows.py <folder with NC15_CANDLES_A1..B4.json>"""
import sys, json, glob, re, os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
ET = ZoneInfo("America/New_York"); MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
CUTS = {"KXSILVER15M": "2026-10-05T00:00", "KXCOPPER15M": "2026-10-05T00:00", "KXNATGAS15M": "2026-10-05T00:00", "KXWTI15M": "2026-10-03T16:00", "KXEURUSD15M": "2026-10-03T16:00",
        "KXGBPUSD15M": "2026-10-03T16:00", "KXUSDJPY15M": "2026-10-03T16:00", "KXAUDUSD15M": "2026-10-03T16:00", "KXUSDCAD15M": "2026-10-03T16:00", "KXHYPE15M": "2026-10-03T00:00", "KXBNB15M": "2026-10-03T00:00"}
tk = set()
for f in sorted(glob.glob(os.path.join(sys.argv[1], "NC15_CANDLES_*.json"))): tk |= set(json.load(open(f))["ticker_allowlist"])
by = {}; bad = []
for t in tk:
    m = re.match(r"^(KX[A-Z]+15M)-(\d{2})([A-Z]{3})(\d{2})(\d{2})(\d{2})-(\d{2})$", t)
    if not m: bad.append(t); continue
    s, yy, mo, dd, hh, mi, _ = m.groups(); by.setdefault(s, []).append(datetime(2000 + int(yy), MON[mo], int(dd), int(hh), int(mi), tzinfo=ET).astimezone(timezone.utc))
print("distinct tickers", len(tk), "| unparsed", len(bad))
for s in sorted(by):
    v = sorted(by[s]); cut = datetime.fromisoformat(CUTS[s]).replace(tzinfo=timezone.utc); u = [d for d in v if d < cut]; f = lambda d: d.strftime("%Y-%m-%dT%H:%MZ")
    print("%-12s listed %6d first %s last %s days %3d | usable %6d %s to %s days %3d" % (s, len(v), f(v[0]), f(v[-1]), len({d.date() for d in v}), len(u), f(u[0]) if u else "-", f(u[-1]) if u else "-", len({d.date() for d in u})))
