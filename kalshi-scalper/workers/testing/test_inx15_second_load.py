import gzip, json, os, sqlite3, tempfile, inx15_second_load as L
base = tempfile.mkdtemp()
def put(run, bodies, status=200, complete=True, extra_rows=()):
    folder = os.path.join(base, *run.split("/")); os.makedirs(folder, exist_ok=True); rows = []
    for i, b in enumerate(bodies):
        fn = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(folder, fn), "wt").write(json.dumps(b)); rows.append({"id": "r%d" % i, "status": status, "file": fn})
    json.dump({"status": "complete" if complete else "running", "rows": rows + list(extra_rows)}, open(os.path.join(folder, "manifest.json"), "w"))
assert L.CUT == 1796083200; cut = 1796083200; iso = lambda t: __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(t))
c0 = 1794000000
mk = lambda tk, t, **kw: dict({"ticker": tk, "close_time": iso(t)}, **kw)
lists = {"markets": [mk("KXINX15M-A", c0, result="yes"), mk("KXINX15M-B", c0 + 900, result="no"), mk("KXINX15M-LATE", cut, result="yes"), mk("KXINX15M-LAST", cut - 1, result="no"), mk("KXNDQ15M-X", c0, result="yes"),
                     mk("KXINX15M-NORES", c0 + 1800), mk("KXNDQ15M-Y", cut + 5, result="yes"), {"ticker": "KXINX15M-NOCLOSE"}, mk("KXINX15M-VOID", c0 + 2700, result="void")]}
put(L.LISTS[0], [lists])
cn = lambda e, b, a, **kw: dict({"end_period_ts": e, "yes_bid": {"close_dollars": b}, "yes_ask": {"close_dollars": a}}, **kw)
candA = {"markets": [{"market_ticker": "KXINX15M-A", "candlesticks": [cn(c0 - 600, "0.40", "0.42", volume_fp="12.5", open_interest_fp="100"), cn(c0 - 540, "0.41", "0.43", volume=7, open_interest=101), cn(c0 + 60, "0.5", "0.6"), cn(c0 + 1, "0.5", "0.6"), cn(c0, "0.44", "0.46", volume_fp="2", open_interest_fp="9"), {"end_period_ts": c0 - 480}, cn(c0 - 600, "0.40", "0.42", volume_fp="12.5", open_interest_fp="100"), cn(c0 - 420, "0.3", "0.4", volume_fp="", open_interest_fp="", volume=3, open_interest=None)]},
                      {"market_ticker": "KXINX15M-LATE", "candlesticks": [cn(1, "BAD", "BAD")]}, {"market_ticker": "KXINX15M-B", "candlesticks": [cn(c0 + 900 - 300, "0.7", "0.72", volume_fp="1", open_interest_fp="5")]}]}
patch = {"markets": [{"market_ticker": "KXINX15M-A", "candlesticks": [cn(c0 - 600, "0.99", "0.98")]}]}
put(L.CANDLES[0], [candA]); put(L.CANDLES[1], [patch])
allow = os.path.join(base, "allow.md"); line = lambda sha, runs: "- " + L.ALLOW_MARK + ": inx15_second_load.py sha256 " + sha + " runs " + " ".join(runs)
# refusals
open(allow, "w").write("nothing\n")
try: L.load(base, allow); raise AssertionError("must refuse")
except SystemExit as e: assert "no allow-list line" in str(e)
open(allow, "w").write(line("0" * 64, L.LISTS + L.CANDLES) + "\n")
try: L.load(base, allow); raise AssertionError("must refuse")
except SystemExit as e: assert "no allow-list line" in str(e)
open(allow, "w").write(line(L.self_sha(), L.LISTS) + "\n")
try: L.load(base, allow); raise AssertionError("must refuse")
except SystemExit as e: assert "does not name run" in str(e)
try: L.load(base, os.path.join(base, "none.md")); raise AssertionError("must refuse")
except SystemExit as e: assert "cannot be read" in str(e)
open(allow, "w").write(line(L.self_sha(), L.LISTS + L.CANDLES) + "\n")
wins, c = L.load(base, allow)
# the cut first: LATE (== cut) dropped and counted; LAST (cut - 1) kept; other series dropped; unreadable rows counted; a result-less or void window dropped
assert c["dropped by the cut"] == 2 and c["other series (dropped)"] == 1 and c["unreadable ticker or close"] == 1 and c["no result (dropped)"] == 2 and c["candle market not kept (not parsed)"] == 1, c
assert [w["ticker"] for w in wins] == ["KXINX15M-A", "KXINX15M-B", "KXINX15M-LAST"] and wins[0]["result"] == "yes" and wins[2]["candles"] == []
a = wins[0]["candles"]          # (end, bid, ask, volume, oi): fp first, plain fallback, empty fp falls back, a candle after the close dropped, a candle with no prices unreadable, a duplicate that differs counted first kept
assert a == [(c0 - 600, 0.40, 0.42, 12.5, 100.0), (c0 - 540, 0.41, 0.43, 7.0, 101.0), (c0 - 420, 0.3, 0.4, 3.0, None), (c0, 0.44, 0.46, 2.0, 9.0)], a          # the candle ending exactly at the close is kept
assert c["candle after close (dropped)"] == 2 and c["candle unreadable"] == 1 and c["duplicate candle differs (first kept)"] == 1, c
# sqlite: the OIREL-X extract's schema
out = os.path.join(base, "o.sqlite"); L.to_sqlite(wins, out); db = sqlite3.connect(out)
assert db.execute("select ticker, series, open_ts, close_ts, result from market order by close_ts").fetchall()[0] == ("KXINX15M-A", "KXINX15M", c0 - 900, c0, "yes") and db.execute("select count(*) from candle").fetchone()[0] == 5
# manifest checks: an incomplete run, a non-200 row
for kw in ({"complete": False}, {"status": 500}):
    put(L.CANDLES[1], [patch], **kw)
    try: L.load(base, allow); raise AssertionError("must refuse")
    except SystemExit as e: assert "REFUSED" in str(e)
put(L.CANDLES[1], [patch], status=200, extra_rows=[{"id": "x", "status": 429}])          # a request that only ever got a 429 was never answered 200: refuse
try: L.load(base, allow); raise AssertionError("must refuse")
except SystemExit as e: assert "was not answered 200" in str(e)
put(L.CANDLES[1], [patch], status=200, extra_rows=[{"id": "r0", "status": 429}]); assert L.load(base, allow)[1]["dropped by the cut"] == 2          # a 429 retried into a 200 is fine
put(L.CANDLES[1], [patch], status=200, extra_rows=[{"id": "r0", "status": 500}])          # a 500 beside the 200 of the same request: refuse
try: L.load(base, allow); raise AssertionError("must refuse")
except SystemExit as e: assert "was not answered 200" in str(e)
print("inx15 second loader tests passed")
