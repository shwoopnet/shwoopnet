"""Prints every record of nc15_wheel_replay.py (imported unchanged, hash b44c1d8f...) for a diff with a second build. python3 -I nc15_wheel_replay_records.py <made-up fixture dir with MADE_UP_DATA> [now ISO]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import nc15_wheel_replay as N
root = sys.argv[1]; assert os.path.exists(os.path.join(root, "MADE_UP_DATA")), "made-up fixtures only"
now = N._iso(sys.argv[2]) if len(sys.argv) > 2 else None
recs, reasons = N.replay(root, now=now)
for r in sorted(recs, key=lambda r: (r["ticker"])):
    print("%s status=%s side=%s ask=%.4f limit=%.4f imb5=%+.4f price=%s fee=%s cash=%s result=%s" % (r["ticker"], r["status"], r["side"], r["ask"], r["limit"], r["imb5"], "%.6f" % r["price"] if "price" in r else "-", "%.2f" % r["fee"] if "fee" in r else "-", "%.4f" % r["cash"] if "cash" in r else "-", r.get("result", "-")))
print("no signal by reason:", dict(sorted(reasons.items())))
print("\n".join(N.report(recs, reasons)))
