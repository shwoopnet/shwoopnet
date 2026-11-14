"""build_nc15_jobs hand-case test on INVENTED coverage rows. python3 -I build_nc15_jobs_test.py"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import build_nc15_jobs as B
# chunking: contiguous, no gap or overlap, starts at LIST_START, ends at END, every chunk at most 10 days
ch = B.chunks(); assert ch[0][0] == B.LIST_START and ch[-1][1] == B.END
for (a, b), (c, d) in zip(ch, ch[1:]): assert c == b + 1 and a <= b
assert all(b - a + 1 <= B.CHUNK_S for a, b in ch) and len(ch) == 17, len(ch)
jl = B.lists_jobs(); assert [x["job_id"] for x in jl] == ["NC15_LISTS_A", "NC15_LISTS_B"]       # split by series group: the runner stops a run at 40 minutes (about 480 requests at 5 s), so no file may page past 470 (the Head, Nov 14)
reqs_all = [r for x in jl for r in x["requests"]]
assert len(reqs_all) == 11 * 17 and len({r["id"] for r in reqs_all}) == len(reqs_all)
assert sorted({r["params"]["series_ticker"] for r in reqs_all}) == sorted(B.SERIES) and {r["params"]["series_ticker"] for r in jl[0]["requests"]}.isdisjoint({r["params"]["series_ticker"] for r in jl[1]["requests"]})
for x in jl:
    pages = sum(r["max_pages"] for r in x["requests"]); assert pages + 14 == x["max_requests"] <= 470, (pages, x["max_requests"])      # the runner counts PAGES and retries against the cap: page budget plus 14, and at most 470
    assert x["pacing_seconds"] == 5.0 and x["owner"] == "DESK_A" and x["ticker_allowlist"] == [] and set(x["series_allowlist"]) == {r["params"]["series_ticker"] for r in x["requests"]}      # the allowlist is the file's own series group (Auditor B)
assert sum(sum(r["max_pages"] for r in x["requests"]) for x in jl) == 561
assert all(r["params"]["status"] == "settled" and r["params"]["limit"] == 1000 and r["max_pages"] == 3 and r["params"]["series_ticker"] in B.SERIES for r in reqs_all) and max(r["params"]["max_close_ts"] for r in reqs_all) == B.END
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
pg = sum(r.get("max_pages", 1) for r in pj["requests"]); assert len(pj["requests"]) == 2 and pg == 2 and pg + 6 == pj["max_requests"] <= 1200, (pg, pj["max_requests"])      # the runner counts every request SENT against the cap, a 429 retry or a retried non-200 included (kalshi_pull.py: sent += 1, then "sent >= cap"): pages + 6 leaves room for retries and len(r1["params"]["market_tickers"].split(",")) == 44 == len(pj["ticker_allowlist"])
assert r1["params"]["start_ts"] == quartet[0] - 900 and r1["params"]["end_ts"] == quartet[-1] and r2["params"]["end_ts"] == quartet[0] and r2["params"]["start_ts"] == quartet[0] - 900
assert set(r2["params"]["market_tickers"].split(",")) == set(bycl[quartet[0]]) and len(bycl[quartet[0]]) == 11 and r1["params"]["period_interval"] == r2["params"]["period_interval"] == 1
assert all(t in pj["ticker_allowlist"] for t in r1["params"]["market_tickers"].split(","))
print("BUILD_NC15_JOBS TEST OK (chunks, 187 list requests, probe hour choice, 44 tickers batched and 11 plain)")
