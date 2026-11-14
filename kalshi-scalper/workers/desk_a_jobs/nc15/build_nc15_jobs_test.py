"""build_nc15_jobs hand-case test on INVENTED coverage rows. python3 -I build_nc15_jobs_test.py"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import build_nc15_jobs as B
# chunking: contiguous, no gap or overlap, starts at LIST_START, ends at END, every chunk at most 10 days
ch = B.chunks(); assert ch[0][0] == B.LIST_START and ch[-1][1] == B.END
for (a, b), (c, d) in zip(ch, ch[1:]): assert c == b + 1 and a <= b
assert all(b - a + 1 <= B.CHUNK_S for a, b in ch) and len(ch) == 17, len(ch)
j = B.lists_job(); assert len(j["requests"]) == 11 * 17 == j["max_requests"] and len({r["id"] for r in j["requests"]}) == len(j["requests"])
assert all(r["params"]["status"] == "settled" and r["params"]["limit"] == 1000 and r["max_pages"] == 3 and r["params"]["series_ticker"] in B.SERIES for r in j["requests"])
assert j["pacing_seconds"] == 5.0 and j["owner"] == "DESK_A" and j["ticker_allowlist"] == [] and max(r["params"]["max_close_ts"] for r in j["requests"]) == B.END
# the probe: invented coverage; hour A has 3 + 4 + 4 + 4 tickers, hour B has 11 each (the winner); an incomplete hour is skipped
base0 = B.ts("2026-11-12T14:00:00Z")           # :00 of an hour; the quartet starts at :15
rows = {}
def put(c, n, tag):
    for k in range(n): rows["KXSILVER15M-%s%d-%d" % (tag, c, k)] = (c, B.SERIES[k % 11])
for k, n in enumerate((3, 4, 4, 4)): put(base0 + 900 * (k + 1), n, "A")
hb = base0 + 3600
for k in range(4): put(hb + 900 * (k + 1), 11, "B")
put(hb + 7200 + 900, 5, "C")                  # an hour with only one close: incomplete
quartet, bycl = B.pick_hour(rows); assert quartet == [hb + 900, hb + 1800, hb + 2700, hb + 3600], quartet
pj = B.probe_job(rows); r1, r2 = pj["requests"]
assert len(pj["requests"]) == 2 == pj["max_requests"] and len(r1["params"]["market_tickers"].split(",")) == 44 == len(pj["ticker_allowlist"])
assert r1["params"]["start_ts"] == quartet[0] - 900 and r1["params"]["end_ts"] == quartet[-1] and r2["params"]["end_ts"] == quartet[0] and r2["params"]["start_ts"] == quartet[0] - 900
assert set(r2["params"]["market_tickers"].split(",")) == set(bycl[quartet[0]]) and len(bycl[quartet[0]]) == 11 and r1["params"]["period_interval"] == r2["params"]["period_interval"] == 1
assert all(t in pj["ticker_allowlist"] for t in r1["params"]["market_tickers"].split(","))
print("BUILD_NC15_JOBS TEST OK (chunks, 187 list requests, probe hour choice, 44 tickers batched and 11 plain)")
