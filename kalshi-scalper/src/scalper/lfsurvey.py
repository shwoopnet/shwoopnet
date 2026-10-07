"""Survey for strategy #1 (favorite-longshot bias). DESCRIPTIVE ONLY.

Counts how many settled markets each recurring series has and how much each
traded. It never reads a result or a price-to-outcome relationship: series are
to be chosen on cost and liquidity alone, so nothing here may look at returns.
"""
import json, statistics, sys, time
from . import api

RECURRING = {"fifteen_min", "hourly", "daily", "weekly", "monthly"}
MAX_PAGES = 3


def candidates(series):
    return [s for s in series
            if not s["ticker"].startswith("KXMVE")
            and s.get("frequency") in RECURRING
            and s.get("fee_multiplier", 1) > 0]


def survey_one(ticker):
    vols, n, cur = [], 0, None
    for _ in range(MAX_PAGES):
        p = {"series_ticker": ticker, "status": "settled", "limit": 1000}
        if cur:
            p["cursor"] = cur
        r = api._get("/markets", p)
        for m in r.get("markets", []):
            n += 1
            vols.append(api.f(m.get("volume_fp")) or 0.0)
        cur = r.get("cursor")
        if not cur:
            break
    vols.sort()
    return {"ticker": ticker, "settled": n, "capped": bool(cur),
            "median_vol": statistics.median(vols) if vols else 0,
            "n_vol_100": sum(v >= 100 for v in vols),
            "total_vol": sum(vols)}


def main(series_path, out_path):
    series = candidates(json.load(open(series_path)))
    out = []
    for i, s in enumerate(series):
        try:
            row = survey_one(s["ticker"])
        except Exception as e:
            row = {"ticker": s["ticker"], "error": str(e)}
        row.update(frequency=s["frequency"], category=s["category"],
                   fee_type=s["fee_type"], fee_multiplier=s["fee_multiplier"])
        out.append(row)
        if i % 25 == 0:
            json.dump(out, open(out_path, "w"))
            print(i, len(series), file=sys.stderr, flush=True)
        time.sleep(0.12)
    json.dump(out, open(out_path, "w"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
