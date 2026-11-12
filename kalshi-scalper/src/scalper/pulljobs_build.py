"""Writes workers/pulljobs/*.json (PULLJOBS1). Offline: reads data/ment1.sqlite, makes no network call.
Run: python3 -I src/scalper/pulljobs_build.py   (MENTPERSIST1 needs the md5 pool order from mentpersist1.build())."""
import os, sys, json, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "workers", "pulljobs"); os.makedirs(OUT, exist_ok=True)
HOST = "api.elections.kalshi.com"; BASE = "/trade-api/v2"
STOP = {"pause_seconds_on_429": 300, "stop_after_consecutive_429": 2, "stop_after_consecutive_other_failures": 3,
        "note": "a 429 pauses 5 minutes and the same request is tried once more; a second 429 in a row stops the run with the cursor saved; no retry loop"}
PRIV = ["public GET on api.elections.kalshi.com only", "no account, portfolio, order, fill, position or key endpoint (the runner refuses them)",
        "no Authorization header, no key, no cookie", "no POST", "response bodies go to scratch outside the repository and are never committed; only the status read log is committed"]

def write(name, d):
    json.dump(d, open(os.path.join(OUT, name + ".json"), "w"), indent=1); print(name, len(d.get("requests", [])), "requests")

def common(job_id, status, card, protocol, commit, **kw):
    d = dict(job_id=job_id, status=status, card=card, protocol_file=protocol, protocol_commit=commit, host=HOST, base_path=BASE,
             stop_rules=STOP, privacy_rules=PRIV, resume_cursor_file="workers/pulljobs/%s_CURSOR.json" % job_id,
             readlog_file="workers/pulljobs/%s_READLOG.json" % job_id, output_dir="/tmp/pulljobs/%s" % job_id)
    d.update(kw); return d

# ---- MENTPERSIST1 -------------------------------------------------------------------------------
import mentpersist1 as m
info, _ = m.build(); db = sqlite3.connect(m.DB)
done = set(r[0] for r in db.execute("select ticker from done"))
pool = [t for t in sorted([t for t, d in info.items() if not d["chosen"]], key=m.md5) if t not in done][:1600]
def mp_req(t):
    d = info[t]; c = d["c"]
    path = "/historical/markets/%s/candlesticks" % t if d["src"] == "hist" else "/series/%s/markets/%s/candlesticks" % (d["series"], t)
    return {"id": t, "path": path, "params": {"start_ts": c - 30 * 3600, "end_ts": c, "period_interval": 60}}
EP_MP = [{"name": "historical_market_candlesticks", "method": "GET", "path_pattern": r"/historical/markets/(?P<ticker>[A-Za-z0-9_.-]+)/candlesticks", "params_allowed": ["start_ts", "end_ts", "period_interval"]},
         {"name": "series_market_candlesticks", "method": "GET", "path_pattern": r"/series/(?P<series>[A-Za-z0-9_.-]+)/markets/(?P<ticker>[A-Za-z0-9_.-]+)/candlesticks", "params_allowed": ["start_ts", "end_ts", "period_interval"]}]
KEEP_MP = ["candlesticks[].end_period_ts", "candlesticks[].yes_bid.close(_dollars)", "candlesticks[].yes_ask.close(_dollars)"]
NOT_MP = ["does not decide MENTPERSIST1 by itself: the rules, gates, committed cut and held-out read-once marker stay in the protocol and mentpersist1.py",
          "reads no outcome of a target market; no outcome is scored by the runner", "does not touch the 500 held markets (already in data/ment1.sqlite)"]
def mp_job(job_id, lo, hi, expected, purpose, extra):
    reqs = [mp_req(t) for t in pool[lo:hi]]
    return common(job_id, "active", "MENTPERSIST1 (card 84, mention persistence)", "workers/MENTPERSIST1_PROTOCOL.md", "f73b7f4c",
        purpose=purpose, allowed_endpoints=EP_MP, ticker_allowlist=[r["id"] for r in reqs], series_allowlist=sorted({info[r["id"]]["series"] for r in reqs}),
        pacing_seconds=15, max_requests=len(reqs), expected_requests=expected, priority=extra.pop("priority"),
        requests=reqs, fields_to_keep=KEEP_MP, will_not_decide=NOT_MP,
        ingest="python3 -I src/scalper/pulljobs_ingest.py %s  (loads the scratch files into data/ment1.sqlite candle and done, exactly as mentpersist1 fetch does)" % job_id,
        order_note="requests are the first %d of the ascending-md5 new-market pool after the %d already in `done` (plan order of mentpersist1.py)" % (len(pool), len(done)), **extra)
write("MENTPERSIST1_A_300", mp_job("MENTPERSIST1_A_300", 0, 300, 300,
    "Reduced pull: the first 300 candle reads of the MENTPERSIST1 pool. About 52 R1 and 22 R2 trades by the held-500 rate (R1 0.175, R2 0.073 per read), so about 100 R1 and 42 R2 development trades in all: enough for the registered KILL test (PF under 1.0 on 60 or more trades), NOT enough for the held-out gate (about 17 held-out R1 trades, 30 needed).",
    dict(priority=2, depends_on=None, checkpoints=[100, 200], dev_only="Do NOT run commit-cut after this job alone: the protocol's cut is committed only when the pull is complete or at its read cap")))
write("MENTPERSIST1_B_1300", mp_job("MENTPERSIST1_B_1300", 300, 1600, 1300,
    "Remainder to the protocol cap of 1,600. The registered stop rule ends it earlier: the first 200 read block in which a rule has 130 trades by the rule (R1 expected near 470 total reads, about 520 reads for 30 held-out R1 trades; R2 is not expected to get there under 1,600). Review at each checkpoint with `python3 -I src/scalper/mentpersist1.py plan` counts.",
    dict(priority=3, depends_on="MENTPERSIST1_A_300", checkpoints=[200, 400, 600, 800, 1000, 1200],
         stop_review="at each checkpoint run the block count (counts()) and stop for good when R1 or R2 has total >= 130 trades")))

# ---- COMBO1 open book probe -------------------------------------------------------------------
cs = ["KXMVENBASINGLEGAME", "KXMVENFLSINGLEGAME", "KXMVESPORTSMULTIGAMEEXTENDED"]
reqs = [{"id": "open_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "open", "limit": 100}} for s in cs]
write("COMBO1_OPENBOOK", common("COMBO1_OPENBOOK", "active", "COMBO1 (reopen test only)", "workers/COMBO1_PROTOCOL.md", "f3756e56",
    purpose="REPLACES the 17+ page historical NBA walk and the 300 to 500 candle reads. One page (100) of OPEN combos for each of three collections, to answer the only question the zero-ask finding left: does any open combo show a real two-sided quote (ask between 0.01 and 0.99, bid above 0, ask minus bid at most 0.10) now? NBA is in season, so open NBA combos should exist; the earlier read of the other two found only 37 stale open combos. Zero quoted combos in 3 pages closes COMBO1 for good.",
    allowed_endpoints=[{"name": "open_markets_by_series", "method": "GET", "path_pattern": r"/markets", "params_allowed": ["series_ticker", "status", "limit"]}],
    ticker_allowlist=[], series_allowlist=cs, pacing_seconds=15, max_requests=3, expected_requests=3, priority=1, depends_on=None, checkpoints=[],
    requests=reqs, fields_to_keep=["markets[].ticker", "markets[].event_ticker", "markets[].status", "markets[].yes_bid_dollars", "markets[].yes_ask_dollars", "markets[].no_bid_dollars", "markets[].no_ask_dollars", "markets[].volume_fp", "markets[].close_time", "markets[].open_time", "len(markets[].mve_selected_legs)", "cursor present or not (not followed)"],
    will_not_decide=["does not price or score any combo (R1, R2, R3 stay unrun)", "does not follow a cursor", "a quoted combo only means the ask/bid test should be re-run with a recorder; it is not an edge"]))

# ---- inactive / retired -------------------------------------------------------------------------
write("CLINICAL2_REMAINDER", common("CLINICAL2_REMAINDER", "retired", "CLINICAL2", "workers/CLINICAL2_PROTOCOL.md", "72024226",
    purpose="RETIRE. The card closed under its registered kill rule (Nov 11): at most 17 distinct settled events in the nine fixed series against a gate of 100, median 1 new settled event a month, 83 months to 100. Candle reads (Amendment 1) cannot change that because the gate counts EVENTS, and an event with no quote only lowers the count. The 65 further health series would have to supply 83 more settled events inside a 90 day hold to matter; the listing alone is 130 reads (2 per series) for a family where 75 of 126 settled markets took over 90 days to close. Not written as a runnable plan.",
    allowed_endpoints=[], ticker_allowlist=[], series_allowlist=[], pacing_seconds=15, max_requests=0, expected_requests=0, priority=None, depends_on=None, checkpoints=[], requests=[],
    reopen_condition="a registered RETURN: a new source or series family, or 100 events reached. Then the plan would be: 130 listing reads for the 65 series (GET /markets and /historical/markets per series) and up to 126 candle reads for the nine fixed series; write the job file from that new registration.",
    fields_to_keep=[], will_not_decide=["nothing: retired"]))
write("POLCOMBO1B_REOPEN", common("POLCOMBO1B_REOPEN", "inactive", "POLCOMBO1B", "workers/POLCOMBO1B_PROTOCOL.md", "0cd23715",
    purpose="INACTIVE (retired Nov 11 by its KILL rule: two sampled runs found no politics-leg combo with a live two-sided quote; 74 of 75 showed 0.00/0.00). Reopen only on the protocol's REOPEN CONDITION: a politics-leg combo with a live two-sided quote, or 100 settled politics combos. The plan is the census resume from POLCOMBO1B_RESUME.json: the largest collection KXMVESPORTSMULTIGAMEEXTENDED-R at page 29 (28 pages read, cursor in the resume file, not copied here), then the two cross-category collections from page 1, at most 60 pages each and 150 pages in total (about 122 reads left).",
    allowed_endpoints=[{"name": "open_markets_by_collection", "method": "GET", "path_pattern": r"/markets", "params_allowed": ["mve_collection_ticker", "status", "limit", "cursor"]}],
    ticker_allowlist=[], series_allowlist=[], collection_allowlist=["KXMVESPORTSMULTIGAMEEXTENDED-R", "KXMVECROSSCATEGORY-SHARD1-R", "KXMVECROSSCATEGORY-R"],
    pacing_seconds=15, max_requests=0, expected_requests=122, priority=None, depends_on=None, checkpoints=[], requests=[],
    note="max_requests 0 and no requests on purpose: a cursor-following walk needs a paging feature the runner does not have. To reopen, add it (a dated amendment) and fill the plan; the runner refuses an inactive job.",
    fields_to_keep=["markets[].ticker", "mve_selected_legs", "yes_bid_dollars", "yes_ask_dollars", "close_time", "volume_fp"],
    will_not_decide=["no combo pricing, no edge, no popup: a census only"]))
