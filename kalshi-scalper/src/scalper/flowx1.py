"""FLOWX1: taker flow on the cheap side of non-15-minute, non-Bitcoin markets (public tape; research only, no orders).
    python3 -I -m scalper.flowx1 census OUT.sqlite      (market list and volumes only; the result field is never stored)
Registration: workers/FLOWX1_REGISTRATION.md. Cheap side only (ask 3c to 30c).
"""
from __future__ import annotations
import json, sqlite3, sys, time, datetime
import urllib.request, urllib.parse, urllib.error
from . import api

BASE = "https://api.elections.kalshi.com/trade-api/v2"   # api.BASES[0] (external-api) was refused 2026-11-06 while this host answered


def get(path, params=None, tries=6):
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429:
                time.sleep(4.0 * (i + 1))
            else:
                time.sleep(2.0)
        except Exception as e:  # noqa
            last = e
            time.sleep(3.0)
    raise RuntimeError("GET %s failed: %s" % (path, last))

CUT = int(datetime.datetime(2026, 10, 3, 16, tzinfo=datetime.timezone.utc).timestamp())   # frozen last third starts here: never fetched
START = int(datetime.datetime(2026, 9, 6, tzinfo=datetime.timezone.utc).timestamp())   # live /markets and /markets/trades tier only (the historical endpoints were rate limited 2026-11-06)
CATS = ("Financials", "Crypto", "Commodities")
FREQS = ("hourly", "daily", "weekly")
EXCLUDE_WORDS = ("TEST",)


def universe(series_list):
    """Series chosen from the public series catalogue only (category, frequency, title). No price or outcome."""
    out = []
    for s in series_list:
        t, title = s["ticker"], (s.get("title") or "")
        if s.get("category") not in CATS or s.get("frequency") not in FREQS:
            continue
        if "15M" in t or any(w in t for w in EXCLUDE_WORDS):
            continue
        if "Bitcoin" in title or t.startswith("KXBTC") or t in ("BTC", "BTCD", "BTCD-B"):   # BTC hourly is FLOWHR1's lane
            continue
        out.append(t)
    return sorted(set(out))


def census(out):
    ser = get("/series", {})["series"]
    U = universe(ser)
    db = sqlite3.connect(out)
    db.execute("create table if not exists mk(ticker text primary key, series text, event text, open_ts integer, close_ts integer, volume real, src text)")
    db.execute("create table if not exists sdone(series text primary key, n integer)")
    done = {r[0] for r in db.execute("select series from sdone")}
    print("universe", len(U), "done", len(done), flush=True)
    for k, s in enumerate(U):
        if s in done:
            continue
        rows = []
        for path, extra in (("/markets", {"status": "settled", "min_close_ts": START, "max_close_ts": CUT - 1}),):
            cur = None
            while True:
                p = {"series_ticker": s, "limit": 1000, **extra}
                if cur:
                    p["cursor"] = cur
                try:
                    d = get(path, p)
                except Exception as e:  # noqa
                    print("fail", path, s, e, flush=True)
                    break
                for m in d.get("markets", []):
                    ct = int(datetime.datetime.fromisoformat(m["close_time"].replace("Z", "+00:00")).timestamp())
                    if not (START <= ct < CUT) or m.get("result") not in ("yes", "no"):
                        continue
                    ot = int(datetime.datetime.fromisoformat(m["open_time"].replace("Z", "+00:00")).timestamp())
                    rows.append((m["ticker"], s, m.get("event_ticker"), ot, ct, float(m.get("volume_fp") or m.get("volume") or 0), path))
                cur = d.get("cursor")
                time.sleep(1.2)
                if not cur or not d.get("markets"):
                    break
        db.executemany("insert or ignore into mk values(?,?,?,?,?,?,?)", rows)
        db.execute("insert or replace into sdone values(?,?)", (s, len(rows)))
        db.commit()
        print(k, len(U), s, len(rows), flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "census":
        census(sys.argv[2])
