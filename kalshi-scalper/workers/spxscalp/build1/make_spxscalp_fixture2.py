#!/usr/bin/env python3
"""MADE-UP SPXSCALP fixture 2 (not Databento, not Kalshi), per EXPECTED_SPXSCALP_fixture2.md. argv[1] = output directory."""
import csv, json, os, sys
from datetime import datetime, timezone
d = sys.argv[1]; os.makedirs(d + "/cand", exist_ok=True); os.makedirs(d + "/lists", exist_ok=True)
def T(h, mi): return int(datetime(2026, 11, 6, h, mi, 0, tzinfo=timezone.utc).timestamp())
def iso(t, ns=True): return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S" + (".000000000Z" if ns else "Z"))
W = {  # name: (close, ES by m, candles by m: bid or (bid, ask), result)
 "A": (T(15, 0), {0: 7000, 1: 7002, 2: 7005}, {2: (.20, .22), 3: .30, 4: .40, 5: .47, 6: .50, 10: (.45, .47)}, "yes"),
 "B": (T(15, 15), {0: 7000, 1: 6990}, {1: (.80, .82), 10: (.83, .85)}, "yes"),
 "C": (T(15, 30), {0: 7000, 1: 7000, 2: 7005, 3: 7005}, {2: (.26, .28), 3: (.22, .24), 4: .35, 5: .52, 6: .60, 7: .70, 8: .82}, "yes"),
 "D": (T(15, 45), {0: 7000, 1: 7006}, {1: (.21, .23), 2: .30, 9: .30, 10: (.30, .30), 11: (.28, .31)}, "no"),
 "E": (T(16, 0), {0: 7000, 2: 7006}, {2: (.20, .22), 3: .60, 4: .85}, "yes"),
}
rows = []; mk = []; ls = []
for n, (c, es, cd, res) in W.items():
    O = c - 900
    for m, p in es.items(): rows.append((O + 60 * m - 60, p))
    cs = []
    for m, v in cd.items():
        b, a = v if isinstance(v, tuple) else (v, round(v + .02, 2))
        cs.append({"end_period_ts": O + 60 * m, "yes_bid": {"close_dollars": "%.2f" % b}, "yes_ask": {"close_dollars": "%.2f" % a}})
    mk.append({"market_ticker": "KXINX15M-W" + n, "candlesticks": cs}); ls.append({"ticker": "KXINX15M-W" + n, "close_time": iso(c, False), "result": res})
rows.sort()
with open(d + "/es.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow("ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume".split(","))
    for t, p in rows: w.writerow([iso(t), 33, 1, 7, p, p, p, p, 1])
json.dump({"markets": mk}, open(d + "/cand/c1.json", "w")); json.dump({"markets": ls}, open(d + "/lists/l1.json", "w"))
