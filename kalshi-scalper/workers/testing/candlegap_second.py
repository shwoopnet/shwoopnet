"""CANDLEGAP second, independent build from DESIGN text only. Usage: python3 -I candlegap_second.py <wheelbook run folder> <pull folder>
Choices (see report): row time=t_recv_ms; window end=last poll t_recv_ms, inclusive (m+60<=end); window start=max(S,first_seen_ms) with m*1000>=start;
S=ticker clock YYMONDDHHMM as US Eastern (America/New_York); first book row time = first row's t_recv_ms, minute needs m*1000>=that;
changed = row with m*1000 <= t < (m+60)*1000; two-sided book = last row t <= (m+60)*1000; match book = last row t < (m+60)*1000;
split a = m+60 <= close_time, else b (straddlers go to b); no close row -> all a; close_time from answers/ markets[] (first seen)."""
import sys, os, csv, gzip, json, re, calendar, bisect, collections
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

run, pull = sys.argv[1], sys.argv[2]
rd = lambda n: list(csv.DictReader(gzip.open(os.path.join(run, n), "rt")))
cov = [r for r in rd("coverage.csv.gz") if r["ticker"].startswith("KXCS2GAME-")]
T = {r["ticker"]: r for r in cov}
polls = rd("polls.csv.gz")
end_ms = max(int(p["t_recv_ms"]) for p in polls)
MON = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}
def startS(t):
    m = re.match(r"KXCS2GAME-(\d\d)([A-Z]{3})(\d\d)(\d\d)(\d\d)", t)
    y, mo, d, hh, mi = int(m[1]) + 2000, MON[m[2]], int(m[3]), int(m[4]), int(m[5])
    return int(datetime(y, mo, d, hh, mi, tzinfo=ZoneInfo("America/New_York")).timestamp() * 1000)
def f(x):
    return float(x) if x not in ("", None) else None
rows = collections.defaultdict(list)   # ticker -> [(t, yes5 prices, no5, yes_sz, no_sz)]
for fn in ("book_fast.csv.gz", "book_slow.csv.gz"):
    for r in rd(fn):
        if r["ticker"] in T:
            y = tuple(f(r["yes_bid_px_%d" % i]) for i in range(1, 6)); n = tuple(f(r["no_bid_px_%d" % i]) for i in range(1, 6))
            ys = tuple(f(r["yes_bid_sz_%d" % i]) for i in range(1, 6)); ns = tuple(f(r["no_bid_sz_%d" % i]) for i in range(1, 6))
            rows[r["ticker"]].append((int(r["t_recv_ms"]), y, n, ys, ns))
for t in rows: rows[t].sort(key=lambda x: x[0])
close = {}
import glob
for fn in sorted(glob.glob(os.path.join(run, "answers", "*.json.gz"))):
    try: body = json.load(gzip.open(fn))
    except Exception: continue
    for m in (body.get("markets") or []) if isinstance(body, dict) else []:
        if m.get("ticker") in T and m.get("close_time") and m["ticker"] not in close:
            close[m["ticker"]] = k.iso(m["close_time"])
C = k.candles(pull)
cm = {t: {c["ts"]: c for c in v} for t, v in C.items()}

def best(a): return a[0]
def two_sided(r):
    yb, nb = r[1][0], r[2][0]
    return yb is not None and nb is not None and yb < 1 - nb - 1e-9
KEYS = ["1_present_changed", "2_present_unchanged", "3_missing_unchanged_twosided", "4_missing_unchanged_empty_or_onesided", "5_missing_changed"]
cnt = {s: {b: dict.fromkeys(KEYS, 0) for b in ("any5", "top")} for s in "ab"}
tot = {"a": 0, "b": 0}; match = dict(n_candle_bidask=0, bid=0, ask=0, both=0); straddle = 0; boundary_rows = 0
tickers_with_candles = sum(1 for t in T if cm.get(t))
for t in T:
    if not rows[t]: continue
    ts = [r[0] for r in rows[t]]
    S = startS(t); start = max(S, int(T[t]["first_seen_ms"])); first = ts[0]
    ct = close.get(t)
    boundary_rows += sum(1 for x in ts if x % 60000 == 0)
    mm = (max(start, first) + 59999) // 60000 * 60
    while (mm + 60) * 1000 <= end_ms:
        m = mm; mm += 60
        lo, hi = m * 1000, (m + 60) * 1000
        i0 = bisect.bisect_left(ts, lo); i1 = bisect.bisect_left(ts, hi)
        changed5 = i1 > i0
        prev = rows[t][i0 - 1] if i0 > 0 else None
        topch = False
        for j in range(i0, i1):
            p = rows[t][j - 1] if j > 0 else None
            if p is None or p[1][0] != rows[t][j][1][0] or p[2][0] != rows[t][j][2][0]: topch = True
        e = bisect.bisect_right(ts, hi) - 1
        ts_end = two_sided(rows[t][e]) if e >= 0 else False
        s = "a" if (ct is None or hi <= ct * 1000) else "b"
        if s == "b" and ct is not None and lo < ct * 1000: straddle += 1
        tot[s] += 1
        c = cm.get(t, {}).get(m + 60)
        for basis, ch in (("any5", changed5), ("top", topch)):
            if c is not None: key = KEYS[0] if ch else KEYS[1]
            elif ch: key = KEYS[4]
            else: key = KEYS[2] if ts_end else KEYS[3]
            cnt[s][basis][key] += 1
        if s == "a" and c is not None and c["bid"] is not None and c["ask"] is not None:
            e2 = i1 - 1 if i1 > 0 else -1
            r = rows[t][e2]
            match["n_candle_bidask"] += 1
            bmt = r[1][0] is not None and abs(c["bid"] - r[1][0]) <= 0.01 + 1e-9
            amt = r[2][0] is not None and abs(c["ask"] - (1 - r[2][0])) <= 0.01 + 1e-9
            match["bid"] += bmt; match["ask"] += amt; match["both"] += bmt and amt
out = {"tickers_with_candles": tickers_with_candles, "tickers_total": len(T), "tickers_with_close_row": len(close),
       "market_minutes": {"all": tot["a"] + tot["b"], "a_before_close": tot["a"], "b_after_close": tot["b"]},
       "counts_any5_a": cnt["a"]["any5"], "counts_any5_b": cnt["b"]["any5"], "counts_topofbook_a": cnt["a"]["top"],
       "counts_topofbook_b_extra": cnt["b"]["top"], "match_a": match, "extra": {"straddle_minutes_put_in_b": straddle, "book_rows_on_exact_minute_boundary": boundary_rows, "run_end_ms": end_ms}}
print(json.dumps(out, indent=1))
print("%-40s %8s %8s %8s" % ("count", "a_any5", "b_any5", "a_top"))
for key in KEYS: print("%-40s %8d %8d %8d" % (key, cnt["a"]["any5"][key], cnt["b"]["any5"][key], cnt["a"]["top"][key]))
