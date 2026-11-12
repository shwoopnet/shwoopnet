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
# 6. NOTE 3: a result inside the 300 s settle gap cannot move a decision; one just outside it can
def mini(close_y, flip):
    mk2, cd2 = [], []
    S0b = calendar.timegm((2026, 9, 20, 12, 0, 0))
    for i in range(400):
        S = S0b + i * 1200
        ev = "KXESOCCERGAME-%sQ%04d" % (key(S), i)
        for suf, res in (("TIE", "yes" if i % 4 == 0 else "no"), ("AAA", "no"), ("BBB", "no")):
            mk2.append({"ticker": "%s-%s" % (ev, suf), "event_ticker": ev, "close_time": iso(S + 720), "open_time": iso(S - 3600), "result": res})
        for suf, (b, a) in (("TIE", (.25, .27)), ("AAA", (.49, .51)), ("BBB", (.29, .31))):
            cd2.append({"market_ticker": "%s-%s" % (ev, suf), "candlesticks": [{"end_period_ts": S - 60, "yes_bid": {"close_dollars": "%.2f" % b}, "yes_ask": {"close_dollars": "%.2f" % a}}]})
    SX = S0b + 400 * 1200; evx = "KXESOCCERGAME-%sXXXX" % key(SX)
    SY = ((close_y - 720) // 60) * 60; evy = "KXESOCCERGAME-%sYYYY" % key(SY)
    for e, S, cl, res in ((evx, SX, SX + 720, "no"), (evy, SY, close_y, ("yes" if flip else "no"))):
        for suf in ("TIE", "AAA", "BBB"):
            mk2.append({"ticker": "%s-%s" % (e, suf), "event_ticker": e, "close_time": iso(cl), "open_time": iso(S - 3600), "result": res if suf == "TIE" else "no"})
        for suf, (b, a) in (("TIE", (.25, .27)), ("AAA", (.49, .51)), ("BBB", (.29, .31))):
            cd2.append({"market_ticker": "%s-%s" % (e, suf), "candlesticks": [{"end_period_ts": S - 60, "yes_bid": {"close_dollars": "%.2f" % b}, "yes_ask": {"close_dollars": "%.2f" % a}}]})
    rows, _ = E.walk(E.events(sk_markets([folder([{"markets": mk2}])]))[0], sk_candles([folder([{"markets": cd2}])]))
    return [r for r in rows if r["event"] == evx][0]["b"], SX - 60
import scorekit as SK
sk_markets, sk_candles = SK.markets, SK.candles
SXd = calendar.timegm((2026, 9, 20, 12, 0, 0)) + 400 * 1200 - 60
for gap, must_equal in ((180, True), (299, True), (300, False), (400, False)):
    a, _ = mini(SXd - gap, False); b, _ = mini(SXd - gap, True)
    assert (a == b) == must_equal, (gap, a, b)
# 7. rule (h): a HELDOUT_ folder is refused
import shutil
H = os.path.join(tempfile.mkdtemp(), "HELDOUT_ESOC"); shutil.copytree(L, H)
try:
    E.measure([H], [C]); raise AssertionError("HELDOUT_ folder was read")
except SystemExit as e:
    assert "HELDOUT_" in str(e)
print("ok", rep["filled_eligible"], n, res["rule"]["registered_verdict"])
