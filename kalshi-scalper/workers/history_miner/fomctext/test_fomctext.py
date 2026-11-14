"""Invented fixtures for fomctext.py (no Kalshi data). Run: python3 -I test_fomctext.py"""
import csv, gzip, hashlib, json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fomctext as F

def job(jid, reqs):
    return {"job_id": jid, "requests": [{"id": i, "path": p, "params": {}} for i, p in reqs]}

def run(jb, answers, name=None, status="complete", tamper=None):
    """answers: {request id: [body page 1, body page 2, ...]} in job order. Writes a kalshi-pull style run folder whose manifest embeds jb."""
    d = tempfile.mkdtemp() if name is None else os.path.join(tempfile.mkdtemp(), name)
    os.makedirs(d, exist_ok=True); rows = []; n = 0
    for r in jb["requests"]:
        for pg, body in enumerate(answers.get(r["id"], []), 1):
            n += 1; raw = json.dumps(body).encode(); fn = "%04d.json.gz" % n
            gzip.open(os.path.join(d, fn), "wb").write(raw)
            rows.append({"index": n, "id": r["id"], "path": r["path"], "page": pg, "status": 200, "bytes": len(raw), "file": fn, "sha256": hashlib.sha256(raw).hexdigest(), "truncated": False})
    if tamper: tamper(rows)
    json.dump({"job": jb, "status": status, "rows": rows}, open(os.path.join(d, "manifest.json"), "w")); return d

def table(rows, header=None):
    """Clarification 7: a five-column row gains type = statement-type (every earlier fixture's rows are statement-type); a six-column row carries its own type."""
    p = os.path.join(tempfile.mkdtemp(), "t.csv")
    with open(p, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header or ["decision_date", "event_ticker", "market_ticker", "strike_word", "statement_word", "type"])
        w.writerows([list(r) + ["statement-type"] if len(r) == 5 and header is None else r for r in rows])
    return p

def cndl(t, ts, bid, ask):
    return {"market_ticker": t, "candlesticks": [{"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % bid}, "yes_ask": {"close_dollars": "%.4f" % ask}}]}

def refused(fn, word):
    try:
        fn(); raise AssertionError("not refused: " + word)
    except SystemExit as e:
        assert word in str(e), (word, str(e))

ev_of = {d: "KXFEDMENTION-%s%s%s" % (d[2:4], ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"][int(d[5:7]) - 1], d[8:10]) for d in F.DEV_DATES}
LJ = job("FOMCTEXT_LISTS", [("hist", "/historical/markets"), ("live", "/markets")])
CJ = job("FOMCTEXT_CANDLES", [("c1", "/markets/candlesticks")])

# --- 0. basics
assert F.date_of_event("KXFEDMENTION-25JAN29") == "2025-01-29"
assert F.et_epoch("2025-01-29", 14, 5) == 1738177500 and F.et_epoch("2025-06-18", 14, 5) == 1750269900
assert F.held_out("2026-06-17") and not F.held_out("2026-04-29")

# --- FIXTURE 1: survives. 6 meetings x 3 statement-word strikes settled yes at a 0.80 ask; one placebo strike that would qualify; a held-out and a non-decision event in the lists.
mk, cd, tb = [], [], []
for d in F.DEV_DATES[:6]:
    ev = ev_of[d]
    for k in range(3):
        t = "%s-W%d" % (ev, k); mk.append({"ticker": t, "event_ticker": ev, "result": "yes"}); tb.append([d, ev, t, "w%d" % k, "yes"])
        cd.append(cndl(t, F.et_epoch(d, 14, 5), 0.78, 0.80))
    t = ev + "-NOTSW"; mk.append({"ticker": t, "event_ticker": ev, "result": "yes"}); tb.append([d, ev, t, "x", "no"])
cd.append(cndl(ev_of[F.DEV_DATES[0]] + "-NOTSW", F.et_epoch(F.DEV_DATES[0], 14, 5), 0.78, 0.80))
mk.append({"ticker": "KXFEDMENTION-26JUN17-W0", "event_ticker": "KXFEDMENTION-26JUN17", "result": "yes"})
mk.append({"ticker": "KXFEDMENTION-25AUG22-W0", "event_ticker": "KXFEDMENTION-25AUG22", "result": "yes"})
mk.append({"ticker": "KXPOWELLMENTION-25JAN29-W0", "event_ticker": "KXPOWELLMENTION-25JAN29", "result": "yes"})   # a development event the table does not name
L = run(LJ, {"hist": [{"markets": mk[:10], "cursor": "abc"}, {"markets": mk[10:], "cursor": ""}], "live": [{"markets": [], "cursor": ""}]})
C = run(CJ, {"c1": [{"markets": cd}]}); T = table(tb)
r = F.count(T, [L], [C], LJ, CJ)
assert r["qualifying"] == 18 and len(r["qualifying_meetings"]) == 6 and r["verdict"].startswith("survives"), r
assert r["placebo_non_statement_words"]["qualifying"] == 1 and r["placebo_non_statement_words"]["strikes"] == 6, r
assert r["no_market_dates"] == list(F.DEV_DATES[6:]), r
assert r["list_rows_dropped_unread"]["held_out"] == 1 and r["list_rows_dropped_unread"]["not_a_development_decision_date"] == 1, r
assert r["development_events_in_lists_not_named_by_the_table"] == {"count": 1, "events": ["KXPOWELLMENTION-25JAN29"]}, r   # Auditor B defect 2

# --- FIXTURE 2 (BOUNDARY): 0.87 counts, 0.88 does not; a NO settlement never counts; exactly half two-sided does not close (c); one fewer does.
mk2, cd2, tb2 = [], [], []
d = F.DEV_DATES[0]; ev = ev_of[d]; ts = F.et_epoch(d, 14, 5)
for t, res, bid, ask in (("A87", "yes", 0.85, 0.87), ("A88", "yes", 0.86, 0.88), ("NOSETTLE", "no", 0.20, 0.22), ("ONESIDED", "yes", 0.00, 0.50)):
    tk = ev + "-" + t; mk2.append({"ticker": tk, "event_ticker": ev, "result": res}); tb2.append([d, ev, tk, t, "yes"]); cd2.append(cndl(tk, ts, bid, ask))
for t in ("NOCANDLE1", "NOCANDLE2"):
    tk = ev + "-" + t; mk2.append({"ticker": tk, "event_ticker": ev, "result": "yes"}); tb2.append([d, ev, tk, t, "yes"])
L2 = run(LJ, {"hist": [{"markets": mk2, "cursor": ""}], "live": [{"markets": []}]})
r2 = F.count(table(tb2), [L2], [run(CJ, {"c1": [{"markets": cd2}]})], LJ, CJ)
assert r2["qualifying"] == 1 and r2["two_sided_at_1405"] == 3 and r2["statement_word_strikes"] == 6 and "(c)" not in r2["verdict"], r2
assert r2["excluded"]["no_candle_at_1405"] == 2, r2
r2b = F.count(table(tb2), [L2], [run(CJ, {"c1": [{"markets": [c for c in cd2 if not c["market_ticker"].endswith("A88")]}]})], LJ, CJ)
assert "(c)" in r2b["verdict"], r2b
r3 = F.count(table([x for x in tb if x[0] in F.DEV_DATES[:4]]), [run(LJ, {"hist": [{"markets": [m for m in mk if F.date_of_event(m["event_ticker"]) in F.DEV_DATES[:4]]}], "live": [{"markets": []}]})], [C], LJ, CJ)
assert "(a)" in r3["verdict"] and "(b)" in r3["verdict"], r3

# --- FIXTURE 3: refusals.
for nm in ("HELDOUT_x", "heldout_x", "HeldOut_x"):
    refused(lambda: F.count(T, [run(LJ, {"hist": [{"markets": mk}], "live": [{"markets": []}]}, name=nm)], [C], LJ, CJ), "held-out")
refused(lambda: F.load_table(table([["2026-06-17", "KXFEDMENTION-26JUN17", "KXFEDMENTION-26JUN17-W0", "w", "yes"]])), "held-out")
refused(lambda: F.count(table(tb[:-1]), [L], [C], LJ, CJ), "disagree")
refused(lambda: F.load_table(table(tb + [tb[0][:4] + ["no"]])), "twice")                                                   # defect 1
def esc(rows): rows[0]["file"] = "../HELDOUT_t/x.json.gz"
refused(lambda: F.count(T, [run(LJ, {"hist": [{"markets": mk}], "live": [{"markets": []}]}, tamper=esc)], [C], LJ, CJ), "held-out")   # defect 3
def esc2(rows): rows[0]["file"] = "../other/x.json.gz"
refused(lambda: F.count(T, [run(LJ, {"hist": [{"markets": mk}], "live": [{"markets": []}]}, tamper=esc2)], [C], LJ, CJ), "outside")
refused(lambda: F.count(T, [L], [run(CJ, {"c1": [{"markets": cd}]}, status="stopped_429")], LJ, CJ), "not complete")        # defect 4
refused(lambda: F.count(T, [run(LJ, {"hist": [{"markets": mk}]})], [C], LJ, CJ), "no whole answer")                        # a request never answered
refused(lambda: F.count(T, [run(LJ, {"hist": [{"markets": mk, "cursor": "more"}], "live": [{"markets": []}]})], [C], LJ, CJ), "cursor left")
def bad_sha(rows): rows[0]["sha256"] = "0" * 64
refused(lambda: F.count(T, [L], [run(CJ, {"c1": [{"markets": cd}]}, tamper=bad_sha)], LJ, CJ), "sha256")
refused(lambda: F.count(T, [L], [C], LJ, job("OTHER", [("c1", "/markets/candlesticks")])), "committed job")
def r429(rows): rows.insert(0, {"index": 0, "id": "c1", "path": "/markets/candlesticks", "page": 1, "status": 429, "bytes": 0})
assert F.count(T, [L], [run(CJ, {"c1": [{"markets": cd}]}, tamper=r429)], LJ, CJ)["qualifying"] == 18                    # a 429 then a good retry is whole
refused(lambda: F.count(T, [L], [run(CJ, {"c1": [{"markets": [{"market_ticker": cd[0]["market_ticker"], "candlesticks": [{"end_period_ts": F.et_epoch(F.DEV_DATES[0], 14, 5), "yes_bid": {"close": 78}, "yes_ask": {"close": 80}}]}]}]})], LJ, CJ), "plain 'close'")   # gate 6
# --- defect 5: build-candles writes a whole job that passes the pull runner's own check_job
jb, drop = F.build_candles(T, [L], LJ)
assert jb["max_requests"] == len(jb["requests"]) and all(q["path"].startswith("/historical/markets/") for q in jb["requests"]) and len(jb["requests"]) == len(tb), jb["max_requests"]
# --- Amendment 2: a 404 only on a per-market historical candle request; the words command prints no price, volume or result
def r404_list(rows): rows.insert(0, {"index": 0, "id": "live", "path": "/markets", "page": 1, "status": 404, "bytes": 0})
LJ404 = job("FOMCTEXT_LISTS", [("hist", "/historical/markets"), ("live", "/markets")])
refused(lambda: F.count(T, [run(LJ404, {"hist": [{"markets": mk}]}, tamper=r404_list)], [C], LJ404, CJ), "404")
HJ = job("FOMCTEXT_CANDLES", [("h_X", "/historical/markets/X/candlesticks"), ("c1", "/markets/candlesticks")])
def r404_hist(rows): rows.insert(0, {"index": 0, "id": "h_X", "path": "/historical/markets/X/candlesticks", "page": 1, "status": 404, "bytes": 0})
rh = F.count(T, [L], [run(HJ, {"c1": [{"markets": cd}]}, tamper=r404_hist)], LJ, HJ)
assert rh["candle_requests_answered_404"] == 1 and rh["qualifying"] == 18, rh
mkw = [dict(m, title="Will the Chair say W?", yes_sub_title="W", last_price_dollars="0.5", volume_fp="10", yes_ask_dollars="0.6") for m in mk]
W = F.words([run(LJ, {"hist": [{"markets": mkw}], "live": [{"markets": []}]})], LJ)
assert W and all(set(x) <= {"market_ticker", "event_ticker", "decision_date"} | set(F.WORD_FIELDS) for x in W), W[0]
assert not any("result" in x or "price" in json.dumps(x) or "volume" in json.dumps(x) for x in W), W[0]
assert all(not F.held_out(x["decision_date"]) and x["decision_date"] in F.DEV_DATES for x in W) and len(W) == 25, len(W)
# --- Amendment 3: month-only event tickers
assert set(F.MONTH_ONLY.values()) == set(F.DEV_DATES) and len(F.MONTH_ONLY) == 11
assert F.date_of_event("KXFEDMENTION-26MAR") == "2026-03-18" and F.date_of_event("KXFEDMENTION-25JAN") == "2025-01-29"
assert F.date_of_event("KXFEDMENTION-26JUN") is None and F.date_of_event("KXFEDMENTION-25AUG") is None and F.date_of_event("KXFEDMENTION-26JUL") is None
assert F.date_of_event("KXFEDMENTION-26MAR18") == "2026-03-18" and F.date_of_event("KXPOWELLMENTION-25JAN29") == "2025-01-29"
mm = [{"ticker": "KXFEDMENTION-26MAR-INFL", "event_ticker": "KXFEDMENTION-26MAR", "result": "yes"},       # mapped month: kept
      {"ticker": "KXFEDMENTION-25AUG-INFL", "event_ticker": "KXFEDMENTION-25AUG", "result": "yes"},       # unmapped month: dropped as held out
      {"ticker": "KXFEDMENTION-26JUN-INFL", "event_ticker": "KXFEDMENTION-26JUN", "result": "yes"}]       # held-out month: dropped as held out
keep, drop = F.load_lists([run(LJ, {"hist": [{"markets": mm}], "live": [{"markets": []}]})], LJ)
assert list(keep) == ["KXFEDMENTION-26MAR-INFL"] and keep["KXFEDMENTION-26MAR-INFL"]["date"] == "2026-03-18" and drop["held_out"] == 2, (keep, drop)
tm = table([["2026-03-18", "KXFEDMENTION-26MAR", "KXFEDMENTION-26MAR-INFL", "inflation", "yes"]])
rm = F.count(tm, [run(LJ, {"hist": [{"markets": mm}], "live": [{"markets": []}]})], [run(CJ, {"c1": [{"markets": [cndl("KXFEDMENTION-26MAR-INFL", F.et_epoch("2026-03-18", 14, 5), 0.60, 0.62)]}]})], LJ, CJ)
assert rm["qualifying"] == 1 and rm["statement_word_strikes"] == 1, rm
print("ok", r["qualifying"], r2["qualifying"], len(jb["requests"]))

# --- Nov 14: the events command (dated line 0a030458): ticker, series, title and date only, before 2026-06-17
EJ = job("FOMCTEXT_EVENTS", [("events_KXFEDMENTION", "/events")])
evs = [{"event_ticker": "KXFEDMENTION-25JAN29", "title": "A", "strike_date": "2025-01-29T19:00:00Z", "category": "x"},
       {"event_ticker": "KXPOWELLMENTION-26MAR", "title": "B"},
       {"event_ticker": "KXFEDMENTION-26JUN17", "title": "HELD"},
       {"event_ticker": "KXJPOWMENTION-XYZ", "title": "C", "strike_date": "2026-04-29T18:00:00Z"},
       {"event_ticker": "KXWARSHMENTION-ABC", "title": "D"},
       {"event_ticker": "KXOTHER-25JAN29", "title": "E"}]
ER, ED = F.events([run(EJ, {"events_KXFEDMENTION": [{"events": evs, "cursor": ""}]})], EJ)
assert [(r["event_ticker"], r["date"], r["date_source"]) for r in ER] == [("KXFEDMENTION-25JAN29", "2025-01-29", "ticker"), ("KXPOWELLMENTION-26MAR", "2026-03-18", "ticker"),
                                                                         ("KXJPOWMENTION-XYZ", "2026-04-29", "strike_date")], ER
assert all(set(r) == {"event_ticker", "series_ticker", "title", "date", "date_source"} for r in ER), ER
assert "HELD" not in json.dumps(ER) and ED == {"held_out": 1, "no_date": 1, "not_fed_series": 1}, ED
refused(lambda: F.events([run(EJ, {"events_KXFEDMENTION": [{"events": evs, "cursor": ""}]})], job("OTHER", [("events_KXFEDMENTION", "/events")])), "committed job")
print("events command: ok")

# --- Nov 14 addendum: a landed run listed in HELDOUT_PULL_RUNS.md is refused by every command (hm_guard), not only HELDOUT_ names
listed = run(EJ, {"events_KXFEDMENTION": [{"events": evs, "cursor": ""}]}, name="2026-11-14T0054Z_43537213544")
refused(lambda: F.events([listed], EJ), "landed run")
refused(lambda: F.words([run(LJ, {"hist": [{"markets": []}], "live": [{"markets": []}]}, name="2026-11-14T0054Z_43537213544")], LJ), "landed run")
print("listed runs refused: ok")

# --- Nov 14, Clarification 7: the type column. 3 statement-type yes, 4 statement-type no, 2 NOT STATEMENT-TYPE at one meeting
d7 = F.DEV_DATES[0]; ev7 = ev_of[d7]; mk7, cd7, tb7 = [], [], []
for k, (sw, ty) in enumerate([("yes", "statement-type")] * 3 + [("no", "statement-type")] * 4 + [("no", "NOT STATEMENT-TYPE")] * 2):
    t7 = "%s-Z%d" % (ev7, k); mk7.append({"ticker": t7, "event_ticker": ev7, "result": "yes"}); tb7.append([d7, ev7, t7, "z%d" % k, sw, ty])
    cd7.append(cndl(t7, F.et_epoch(d7, 14, 5), 0.78, 0.80))
L7 = run(LJ, {"hist": [{"markets": mk7}], "live": [{"markets": []}]}); C7 = run(CJ, {"c1": [{"markets": cd7}]})
r7 = F.count(table(tb7), [L7], [C7], LJ, CJ)
assert r7["statement_word_strikes"] == 3 and r7["placebo_non_statement_words"]["strikes"] == 4 and r7["strikes_in_table"] == 9, r7
assert r7["not_statement_type"] == {"n": 2, "line": "not statement-type, n = 2"}, r7["not_statement_type"]
refused(lambda: F.count(table(tb7), [run(LJ, {"hist": [{"markets": mk7[:-1]}], "live": [{"markets": []}]})], [C7], LJ, CJ), "disagree")   # a NOT row is still in the universe check
refused(lambda: F.load_table(table([r[:5] for r in tb7], header=["decision_date", "event_ticker", "market_ticker", "strike_word", "statement_word"])), "no type column")
refused(lambda: F.load_table(table(tb7[:1] + [tb7[1][:5] + ["statement"]])), "type must be")
print("type column: ok")

# --- Nov 14, Amendment 4: a plain close is read only as a d.dddd dollar string
assert F.px({"close": "0.5600"}) == 0.56 and F.px({"close_dollars": "0.5600"}) == 0.56
for bad in ("56", 56, 0.56, "0.560"):
    refused(lambda: F.px({"close": bad}), "plain 'close'")
print("amendment 4: ok")
