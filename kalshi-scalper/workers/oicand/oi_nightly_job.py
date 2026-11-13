#!/usr/bin/env python3
"""Nightly OI candle job for the 13 OICORE shadow places (Desk A's twelve at 29dd035e plus Ethereum), written by Desk B. Usage: oi_nightly_job.py <UTC day YYYY-MM-DD> <hours table json> <out job json>.
One batched candlesticks request per close of that UTC day (00:00Z to 23:45Z), period 1, start_ts = close - 420 s, end_ts = close - 120 s, open interest kept. Tickers are built from the close
time in Eastern (EST, UTC-5, valid 2026-11-02 to 2027-03-13; DST starts 2027-03-14) and a series is asked at a close only if the hours table (weekday of the close's UTC date, HH:MM) lists it, so no ticker that does not
exist is asked. EVENT830's 8 series skip the 13:30Z close on EVENT830's calendar dates. Forward days only: before 2026-11-14 it refuses. Reads no Kalshi data. Standard library only."""
import json, os, sys
from datetime import datetime, timedelta, timezone

SERIES = ["KXXRP15M", "KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M", "KXAUDUSD15M", "KXUSDCAD15M", "KXNATGAS15M", "KXETH15M"]
EV830 = {"KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M"}
REL = {"2026-11-05", "2026-11-06", "2026-11-10", "2026-11-12", "2026-11-13", "2026-11-17", "2026-11-19", "2026-11-25", "2026-12-03", "2026-12-04", "2026-12-10", "2026-12-15", "2026-12-16", "2026-12-17", "2026-12-23"}
FIRST_DAY, LAST_EST_DAY = "2026-11-14", "2027-03-13"
MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
U = timezone.utc

def ticker(series, close):
    et = close - timedelta(hours=5)
    return "%s-%02d%s%02d%02d%02d-%02d" % (series, et.year % 100, MON[et.month - 1], et.day, et.hour, et.minute, et.minute)

def build(day, hours):
    if day < FIRST_DAY or day > LAST_EST_DAY:
        sys.exit("REFUSED: day %s is outside %s to %s (forward days only; Eastern is taken as EST)" % (day, FIRST_DAY, LAST_EST_DAY))
    d0 = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=U)
    wd = str(d0.weekday())
    reqs, allow = [], set()
    for i in range(96):
        close = d0 + timedelta(minutes=15 * i)
        hm = close.strftime("%H:%M")
        ts = []
        for s in SERIES:
            if hm not in hours.get(s, {}).get(wd, []):
                continue
            if s in EV830 and hm == "13:30" and day in REL:
                continue
            ts.append(ticker(s, close))
        if ts:
            c = int(close.timestamp())
            reqs.append({"id": "c%04d" % (len(reqs) + 1), "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(sorted(ts)), "start_ts": c - 420, "end_ts": c - 120, "period_interval": 1}})
            allow.update(ts)
    return reqs, sorted(allow)

def main():
    day = sys.argv[1]
    hours = json.load(open(sys.argv[2]))
    reqs, allow = build(day, hours)
    tpl = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "OICAND_CANDLES_template.json")))
    tpl["job_id"] = "OICAND_NIGHTLY_" + day.replace("-", "")
    tpl["purpose"] = "Nightly one minute candles with open interest (7 to 2 minutes before each close) of the 13 OICORE shadow places' markets for the UTC day %s, one batched request per close, for each place's open interest threshold and signal." % day
    tpl["heldout"] = "Forward days only: no day before 2026-11-14 (after the places' registration commit 29dd035e of 2026-11-13T21:09Z and the Ethereum place of 21:19Z). EVENT830's release windows are skipped (its 8 series' 13:30Z closes on its calendar dates). No result or price is read by the builder. HELDOUT_FIRST for the places 2026-12-01T00:00Z."
    tpl["series_allowlist"] = sorted(SERIES)
    tpl["requests"], tpl["ticker_allowlist"], tpl["max_requests"] = reqs, allow, len(reqs)
    tpl["notes"] = "Built by workers/oicand/oi_nightly_job.py for the UTC day %s from the hours table made from the OICAND lists run; %d requests, %d tickers." % (day, len(reqs), len(allow))
    json.dump(tpl, open(sys.argv[3], "w"), indent=1)
    print("day %s | requests %d | tickers %d | job_id %s" % (day, len(reqs), len(allow), tpl["job_id"]))

if __name__ == "__main__":
    main()
