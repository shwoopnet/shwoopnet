"""Writes the canonical per-signal CSV (ticker,series,signal_t,status,result,win,cash) from the frozen scorer nc15_wheel_replay.py (imported unchanged) for wheel_block_reader.py. Made-up folders only.
  python3 -I nc15_wheel_records_csv.py <fixture dir with MADE_UP_DATA> <now ISO> <out.csv>"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import nc15_wheel_replay as N
root, now, out = sys.argv[1], N._iso(sys.argv[2]), sys.argv[3]
assert os.path.exists(os.path.join(root, "MADE_UP_DATA")), "made-up fixtures only"
recs, reasons = N.replay(root, now=now)
with open(out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["ticker", "series", "signal_t", "limit", "side", "status", "result", "win", "cash"])
    for r in sorted(recs, key=lambda r: (r["signal_t"], r["ticker"])): w.writerow([r["ticker"], r["series"], "%.6f" % r["signal_t"], "%.4f" % r["limit"], r["side"], r["status"], r.get("result", ""), r.get("win", ""), ("%.6f" % r["cash"]) if "cash" in r else ""])
print("wrote", out, len(recs), "records")
