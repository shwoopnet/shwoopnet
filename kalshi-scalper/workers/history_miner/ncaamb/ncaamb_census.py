#!/usr/bin/env python3
"""ncaamb_census.py: COUNTS ONLY for the NCAA men's basketball open-markets listing (History Miner, Nov 16, 2026). Job NCAAMB_CENSUS.
This reader NEVER reads a price, size, volume, open interest, result or any field but the five listed in ALLOWED: the landed open-market bodies carry bid, ask and last,
and every market is wrapped so that touching any other key raises (the test poisons the price columns). It counts markets, events (games) and games a day from tickers, event tickers and close and schedule times.
  python3 -I ncaamb_census.py <run folder (the landed pull folder with 0001.json.gz ...)>"""
import collections, calendar, gzip, json, os, sys, time
ALLOWED = ("ticker", "event_ticker", "close_time", "occurrence_datetime", "expected_expiration_time")
SERIES = ("KXNCAAMBGAME", "KXNCAAMBSPREAD", "KXNCAAMBTOTAL")


class Guarded(dict):
    def __getitem__(s, k):
        if k not in ALLOWED:
            raise AssertionError("touched field %r: counts only" % k)
        return super().__getitem__(k)
    def get(s, k, d=None):
        if k not in ALLOWED:
            raise AssertionError("touched field %r: counts only" % k)
        return super().get(k, d)


def iso(s):
    try:
        return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return None


def census(markets):
    """markets: list of dicts (wrapped in Guarded here). -> counts per series: markets, events, games a day by UTC close day, and by schedule day."""
    ms = collections.defaultdict(int); ev = collections.defaultdict(set); by_day = collections.defaultdict(lambda: collections.defaultdict(set)); sched = collections.defaultdict(lambda: collections.defaultdict(set))
    for raw in markets:
        m = Guarded(raw)
        tk = m["ticker"]; ser = tk.split("-", 1)[0]
        if ser not in SERIES:
            continue
        ms[ser] += 1; e = m["event_ticker"]; ev[ser].add(e)
        c = iso(m["close_time"]) if isinstance(m["close_time"], str) else None
        if c is not None:
            by_day[ser][time.strftime("%Y-%m-%d", time.gmtime(c))].add(e)
        o = m.get("occurrence_datetime")
        if isinstance(o, str) and iso(o) is not None:
            sched[ser][time.strftime("%Y-%m-%d", time.gmtime(iso(o)))].add(e)
    out = {}
    for ser in SERIES:
        days = {d: len(v) for d, v in sorted(by_day[ser].items())}
        out[ser] = {"markets": ms[ser], "events": len(ev[ser]), "events_by_close_day_utc": days,
                    "mean_events_per_close_day": (sum(days.values()) / len(days)) if days else None,
                    "events_by_schedule_day_utc": {d: len(v) for d, v in sorted(sched[ser].items())},
                    "markets_per_event": (ms[ser] / len(ev[ser])) if ev[ser] else None}
    return out


def load(folder):
    ms = []
    for f in sorted(os.listdir(folder)):
        if f.endswith(".json.gz"):
            d = json.loads(gzip.decompress(open(os.path.join(folder, f), "rb").read()))
            ms.extend(d.get("markets", []))
    return ms


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(json.dumps(census(load(sys.argv[1])), indent=1, sort_keys=True))
