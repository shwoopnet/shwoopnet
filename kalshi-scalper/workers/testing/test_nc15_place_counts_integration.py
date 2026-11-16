"""Integration of the wrapper with Desk A's REAL core on INVENTED book files (no real NC15 file): runs only when the pinned core is present (env NC15_CORE = its path); otherwise prints SKIPPED."""
import csv, datetime, gzip, json, os, sys, tempfile, calendar
import nc15_place_counts as N
core = os.environ.get("NC15_CORE")
if not core or not os.path.exists(core): print("SKIPPED: set NC15_CORE to the pinned nc15_wheel_counts.py"); sys.exit(0)
root = tempfile.mkdtemp(); allow = os.path.join(root, "allow.md")
def ts(*a): return calendar.timegm(a)
HDR = ["t_recv_ms", "server_date_header", "series", "ticker", "close_time"] + ["%s_%s_%d" % (s, k, i) for s in ("yes_bid", "no_bid") for k in ("px", "sz") for i in range(1, 6)]
from email.utils import formatdate
def rows(series, tk, close, imb_yes=90, side_sz=10):
    L = close - 600; H = L - 3; out = []
    for dt in (0, 3):          # the signal poll (exchange time L - 2.5) and the next poll 3 s later
        r = {"t_recv_ms": int((H + dt + 0.1) * 1000), "server_date_header": formatdate(H + dt, usegmt=True), "series": series, "ticker": tk, "close_time": datetime.datetime.fromtimestamp(close, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        for c in HDR[5:]: r[c] = ""
        r["yes_bid_px_1"], r["yes_bid_sz_1"], r["no_bid_px_1"], r["no_bid_sz_1"] = 0.40, imb_yes, 0.55, side_sz
        out.append(r)
    return out
def write(day, hhmm, allrows):
    d = os.path.join(root, "nc15", day, hhmm); os.makedirs(d, exist_ok=True)
    with gzip.open(os.path.join(d, "book.csv.gz"), "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HDR); w.writeheader(); w.writerows(allrows)
before = ts(2026, 11, 13, 2, 30, 0, 0, 0)          # a signal at 02:50 exchange time for a close at 03:00 is before the 02:40 start? the close at 02:45 gives a signal at 02:34:57: before; the close at 03:00 gives a signal at 02:49:57: after
write("2026-11-13", "0200", rows("KXSILVER15M", "KXSILVER15M-A", ts(2026, 11, 13, 2, 45, 0, 0, 0)) + rows("KXSILVER15M", "KXSILVER15M-B", ts(2026, 11, 13, 3, 0, 0, 0, 0)) + rows("KXSILVER15M", "KXSILVER15M-C", ts(2026, 11, 13, 3, 15, 0, 0, 0), side_sz=5) + rows("KXWTI15M", "KXWTI15M-A", ts(2026, 11, 13, 3, 15, 0, 0, 0)))
import hashlib; csha = hashlib.sha256(open(core, "rb").read()).hexdigest()
assert csha == N.CORE_SHA, csha
open(allow, "w").write("- " + N.ALLOW_MARK + ": nc15_place_counts.py sha256 " + N.self_sha() + " core sha256 " + csha + "\n")
out = os.path.join(root, "o.json"); obj = N.run(root, out, "2026-11-16T17:00:00Z", core_file=core, core_sha=csha, func="count_places", allow_file=allow)
cnt = {r["id"]: r["fill_checked_signals"] for r in obj["places"]}
# SILVER: window A's signal is before the start (not counted), B is counted, C has too little depth (not fill-checked); WTI: one window, counted
assert cnt == {"WH-NC15-SILVER": 1, "WH-NC15-COPPER": 0, "WH-NC15-WTI": 1, "WH-NC15-HYPE": 0, "WH-NC15-BNB": 0, "WH-NC15-USDCAD": 0, "WH-NC15-NATGAS": 0}, cnt
print("nc15 place counts integration test passed")
