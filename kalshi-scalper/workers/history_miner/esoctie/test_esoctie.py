"""Synthetic tests of esoctie.py (no Kalshi data). Run: python3 -I test_esoctie.py"""
import gzip, json, os, random, sys, tempfile, time, calendar
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import esoctie as E

def folder(bodies):
    d = tempfile.mkdtemp(); rows = []
    for i, b in enumerate(bodies, 1):
        fn = "%04d.json.gz" % i; gzip.open(os.path.join(d, fn), "wt").write(json.dumps(b)); rows.append({"id": "r%d" % i, "status": 200, "file": fn})
    json.dump({"rows": rows}, open(os.path.join(d, "manifest.json"), "w")); return d

def key(ts):  # ET key from UTC epoch (November: daylight time ended Nov 1 2026 -> EST for Nov dates, EDT for Sep/Oct)
    t = time.gmtime(ts); off = E.us_eastern_offset(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min)
    l = time.gmtime(ts - off)
    return "%02d%s%02d%02d%02d" % (l.tm_year % 100, ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"][l.tm_mon-1], l.tm_mday, l.tm_hour, l.tm_min)

def iso(ts): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))

# 1. start_of: the census example 26NOV091943 -> 2026-11-10T00:43Z (EST after Nov 1)
assert E.start_of("KXESOCCERGAME-26NOV091943HURRROON") == calendar.timegm((2026, 11, 10, 0, 43, 0))
assert E.start_of("KXESOCCERGAME-26OCT101943AB") == calendar.timegm((2026, 10, 10, 23, 43, 0))  # EDT
# 2. fee rounding
assert E.fee_up(0.25) == 0.02 and E.fee_up(0.10) == 0.01

random.seed(1)
mk, cdl = [], []
S0 = calendar.timegm((2026, 9, 13, 12, 0, 0))
truth = []
for i in range(1400):
    S = S0 + i * 600
    ev = "KXESOCCERGAME-%sP%04d" % (key(S), i)
    tie = random.random() < 0.25
    close = S + 720
    for suf, res in (("TIE", "yes" if tie else "no"), ("AAA", "no"), ("BBB", "no")):
        mk.append({"ticker": "%s-%s" % (ev, suf), "event_ticker": ev, "close_time": iso(close), "open_time": iso(S - 3600), "result": res})
    ask = 0.12 if i % 20 == 0 else 0.27  # every 20th event the Tie is cheap
    cdl.append({"market_ticker": ev + "-TIE", "candlesticks": [{"end_period_ts": S - 60, "yes_bid": {"close_dollars": "%.2f" % (ask - 0.02)}, "yes_ask": {"close_dollars": "%.2f" % ask}}]})
    for suf, m in (("AAA", 0.5), ("BBB", 0.3)):
        cdl.append({"market_ticker": ev + "-" + suf, "candlesticks": [{"end_period_ts": S - 60, "yes_bid": {"close_dollars": "%.2f" % (m - .01)}, "yes_ask": {"close_dollars": "%.2f" % (m + .01)}}]})
# a held-out event must be refused
Sh = calendar.timegm((2026, 10, 25, 12, 0, 0)); evh = "KXESOCCERGAME-%sHOLD" % key(Sh)
for suf in ("TIE", "AAA", "BBB"):
    mk.append({"ticker": "%s-%s" % (evh, suf), "event_ticker": evh, "close_time": iso(Sh + 720), "open_time": iso(Sh - 3600), "result": "yes"})
L = folder([{"markets": mk}]); C = folder([{"markets": cdl}])
rep, rows = E.measure([L], [C])
assert rep["dropped"]["held-out (refused)"] == 1, rep["dropped"]
assert rep["filled"] == 1400 and rep["base_building"] >= 300, rep
# 3. walk-forward: base uses only events closed before S
for r in rows:
    if r["b"] is not None:
        assert r["n_base"] <= sum(1 for x in rows if x["close"] < r["S"])
assert rep["rule_may_be_scored"], rep["kill"]
res = E.score([L], [C])
n = res["rule"]["n"]
assert 40 <= n <= 60, n
# 4. results of non-bet events never change the bet list's prices: flip a result of an event after the last bet's S? (base changes are allowed by design); prices stay
# 5. the guard ignores close time: an event with a wild close but a good open is kept
assert E.events({"KXESOCCERGAME-26OCT101943AB-%s" % s: {"ticker": "KXESOCCERGAME-26OCT101943AB-%s" % s, "event": "KXESOCCERGAME-26OCT101943AB", "series": "KXESOCCERGAME", "close": calendar.timegm((2026,10,12,0,0,0)), "open": calendar.timegm((2026,10,10,23,0,0)), "result": "no"} for s in ("TIE","AAA","BBB")})[0]
print("ok", rep["filled_eligible"], n, res["rule"]["registered_verdict"])
