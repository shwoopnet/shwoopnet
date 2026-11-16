"""Splits the candle requests of ENGINE1_HELD_CANDLES_A1/B1 whose minutes x tickers exceed 9,000 (the endpoint limit is 10,000) into two requests of the SAME tickers, in the generator's order. Ticker close times come from the ticker's own Eastern date and time (verified against every unsplit request: its start and end must equal its computed earliest close minus 1260 and latest close). Ids: the first half keeps the id, the second is the id plus "b". Nothing else is edited; max_requests and the allowlist are unchanged except max_requests = requests + 12. Reads no data.
  python3 -I engine1_heldout_split_jobs.py <jobs dir>"""
import sys, os, json, re, calendar
from zoneinfo import ZoneInfo
from datetime import datetime
LIMIT, LEAD = 9000, 1260
MON = {m: i for i, m in enumerate(["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"], 1)}
def close_of(t):
    m = re.match(r"^KX[A-Z0-9]+-(\d\d)([A-Z]{3})(\d\d)(\d\d)(\d\d)(E[SD]T)?-", t)
    y, mo, d, h, mi = 2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3)), int(m.group(4)), int(m.group(5))
    return int(datetime(y, mo, d, h, mi, tzinfo=ZoneInfo("America/New_York"), fold=1 if m.group(6) == "EST" else 0).timestamp())
def main(dirp):
    out = {}
    for name in ("ENGINE1_HELD_CANDLES_A1", "ENGINE1_HELD_CANDLES_B1"):
        p = os.path.join(dirp, name + ".json"); j = json.load(open(p)); new = []; split = []
        for r in j["requests"]:
            ts = r["params"]["market_tickers"].split(","); cl = [close_of(t) for t in ts]
            assert r["params"]["start_ts"] == min(cl) - LEAD and r["params"]["end_ts"] == max(cl), (r["id"], "close mismatch")
            mins = (r["params"]["end_ts"] - r["params"]["start_ts"]) / 60
            if mins * len(ts) <= LIMIT: new.append(r); continue
            k = len(ts) // 2; a, b = ts[:k], ts[k:]; ca, cb = cl[:k], cl[k:]
            for sfx, tt, cc in (("", a, ca), ("b", b, cb)):
                q = {"id": r["id"] + sfx, "path": r["path"], "params": {"market_tickers": ",".join(tt), "start_ts": min(cc) - LEAD, "end_ts": max(cc), "period_interval": 1}}
                assert ((q["params"]["end_ts"] - q["params"]["start_ts"]) / 60) * len(tt) <= LIMIT, q["id"]
                new.append(q)
            split.append(r["id"])
        j["requests"] = new; j["max_requests"] = len(new) + 12
        j["notes"] += " Nov 16 fix (Main run 118, HTTP 400): requests over 9,000 minutes x tickers split into two with the same tickers in the same order, ids %s keep their id for the first half and get b for the second; nothing else edited." % ",".join(split)
        json.dump(j, open(p, "w"), indent=1); out[name] = (len(new), split)
    print(out)
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
