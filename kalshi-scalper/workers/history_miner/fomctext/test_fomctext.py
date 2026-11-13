"""Invented fixtures for fomctext.py (no Kalshi data). Run: python3 -I test_fomctext.py"""
import csv, gzip, json, os, shutil, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fomctext as F

def folder(bodies, paths=None, name=None):
    d = tempfile.mkdtemp() if name is None else os.path.join(tempfile.mkdtemp(), name)
    os.makedirs(d, exist_ok=True); rows = []
    for i, b in enumerate(bodies, 1):
        fn = "%04d.json.gz" % i; gzip.open(os.path.join(d, fn), "wt").write(json.dumps(b))
        rows.append({"id": "r%d" % i, "status": 200, "file": fn, "path": (paths or ["/markets"] * len(bodies))[i - 1]})
    json.dump({"rows": rows}, open(os.path.join(d, "manifest.json"), "w")); return d

def table(rows):
    p = os.path.join(tempfile.mkdtemp(), "t.csv")
    with open(p, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["decision_date", "event_ticker", "market_ticker", "strike_word", "statement_word"]); w.writerows(rows)
    return p

def cndl(t, ts, bid, ask):
    return {"market_ticker": t, "candlesticks": [{"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % bid}, "yes_ask": {"close_dollars": "%.4f" % ask}}]}

ev_of = {d: "KXFEDMENTION-%s%s%s" % (d[2:4], ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"][int(d[5:7]) - 1], d[8:10]) for d in F.DEV_DATES}

# --- 0. basics
assert F.date_of_event("KXFEDMENTION-25JAN29") == "2025-01-29"
assert F.et_epoch("2025-01-29", 14, 5) == 1738177500            # 19:05Z (EST)
assert F.et_epoch("2025-06-18", 14, 5) == 1750269900            # 18:05Z (EDT)
assert F.held_out("2026-06-17") and not F.held_out("2026-04-29")

# --- FIXTURE 1: survives. 6 meetings x 3 statement-word strikes that settled yes at 0.80 ask (18 qualifying), all two-sided.
mk, cd, tb = [], [], []
for d in F.DEV_DATES[:6]:
    ev = ev_of[d]
    for k in range(3):
        t = "%s-W%d" % (ev, k); mk.append({"ticker": t, "event_ticker": ev, "result": "yes"}); tb.append([d, ev, t, "w%d" % k, "yes"])
        cd.append(cndl(t, F.et_epoch(d, 14, 5), 0.78, 0.80))
    t = ev + "-NOTSW"; mk.append({"ticker": t, "event_ticker": ev, "result": "yes"}); tb.append([d, ev, t, "x", "no"])
# a held-out meeting in the lists: dropped unread
mk.append({"ticker": "KXFEDMENTION-26JUN17-W0", "event_ticker": "KXFEDMENTION-26JUN17", "result": "yes"})
mk.append({"ticker": "KXFEDMENTION-25AUG22-W0", "event_ticker": "KXFEDMENTION-25AUG22", "result": "yes"})
cd.append(cndl(ev_of[F.DEV_DATES[0]] + "-NOTSW", F.et_epoch(F.DEV_DATES[0], 14, 5), 0.78, 0.80))   # one placebo strike that would qualify
L = folder([{"markets": mk}]); C = folder([{"markets": cd}]); T = table(tb)
r = F.count(T, [L], [C])
assert r["qualifying"] == 18 and len(r["qualifying_meetings"]) == 6 and r["verdict"].startswith("survives"), r
assert r["placebo_non_statement_words"]["strikes"] == 6 and r["placebo_non_statement_words"]["qualifying"] == 1 and r["placebo_non_statement_words"]["two_sided_at_1405"] == 1, r   # placebo counted apart, never in the kill line
assert r["no_market_dates"] == list(F.DEV_DATES[6:]), r
assert r["list_rows_dropped_unread"]["held_out"] == 1 and r["list_rows_dropped_unread"]["not_a_development_decision_date"] == 1, r

# --- FIXTURE 2 (BOUNDARY): ask exactly 0.87 counts, 0.88 does not; a NO settlement never counts; two-sided exactly half is NOT "fewer than half".
mk2, cd2, tb2 = [], [], []
d = F.DEV_DATES[0]; ev = ev_of[d]; ts = F.et_epoch(d, 14, 5)
for t, res, bid, ask in (("A87", "yes", 0.85, 0.87), ("A88", "yes", 0.86, 0.88), ("NOSETTLE", "no", 0.20, 0.22), ("ONESIDED", "yes", 0.00, 0.50)):
    tk = ev + "-" + t; mk2.append({"ticker": tk, "event_ticker": ev, "result": res}); tb2.append([d, ev, tk, t, "yes"]); cd2.append(cndl(tk, ts, bid, ask))
for t in ("NOCANDLE1", "NOCANDLE2"):
    tk = ev + "-" + t; mk2.append({"ticker": tk, "event_ticker": ev, "result": "yes"}); tb2.append([d, ev, tk, t, "yes"])
r2 = F.count(table(tb2), [folder([{"markets": mk2}])], [folder([{"markets": cd2}])])
assert r2["qualifying"] == 1, r2                     # only A87
assert r2["two_sided_at_1405"] == 3 and r2["statement_word_strikes"] == 6, r2   # 3 of 6 = exactly half: (c) does not fire
assert not any(x.startswith("(c)") for x in r2["verdict"].split(": ", 1)[-1].split("; ")), r2
assert r2["excluded"]["no_candle_at_1405"] == 2, r2
# one fewer two-sided: (c) fires
cd2b = [c for c in cd2 if not c["market_ticker"].endswith("A88")]
r2b = F.count(table(tb2), [folder([{"markets": mk2}])], [folder([{"markets": cd2b}])])
assert "(c)" in r2b["verdict"], r2b

# --- FIXTURE 3: refusals. A HELDOUT folder (any case), a table naming a held-out date, a strike missing from the table, a non-200 row.
for nm in ("HELDOUT_x", "heldout_x", "HeldOut_x"):
    H = folder([{"markets": mk}], name=nm)
    try:
        F.count(T, [H], [C]); raise AssertionError("held-out folder read: " + nm)
    except SystemExit as e:
        assert "held-out" in str(e)
try:
    F.load_table(table([["2026-06-17", "KXFEDMENTION-26JUN17", "KXFEDMENTION-26JUN17-W0", "w", "yes"]])); raise AssertionError("held-out table row read")
except SystemExit as e:
    assert "held-out" in str(e)
try:
    F.count(table(tb[:-1]), [L], [C]); raise AssertionError("missing table strike accepted")
except SystemExit as e:
    assert "disagree" in str(e)
bad = folder([{"markets": mk}]); m = json.load(open(os.path.join(bad, "manifest.json"))); m["rows"][0]["status"] = 429; json.dump(m, open(os.path.join(bad, "manifest.json"), "w"))
try:
    F.count(T, [bad], [C]); raise AssertionError("429 row accepted")
except SystemExit as e:
    assert "not a whole 200" in str(e)
# fixture 1 under (a) and (b): drop to 4 meetings x 3 = 12
r3 = F.count(table([x for x in tb if x[0] in F.DEV_DATES[:4]]), [folder([{"markets": [m_ for m_ in mk if F.date_of_event(m_["event_ticker"]) in F.DEV_DATES[:4] or not F.date_of_event(m_["event_ticker"]) in F.DEV_DATES]}])], [C])
assert "(a)" in r3["verdict"] and "(b)" in r3["verdict"], r3
# candle job: historical rows go one per market, live rows batched
reqs, drop = F.build_candles(T, [folder([{"markets": mk[:8]}, {"markets": mk[8:]}], paths=["/historical/markets", "/markets"])])
assert sum(1 for q in reqs if q["path"].startswith("/historical/")) == 8 and all(q["params"]["period_interval"] == 1 for q in reqs), reqs[:2]
print("ok", r["qualifying"], r2["qualifying"], len(reqs))
