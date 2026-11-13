"""OIVER-SPREAD scorer hand case on INVENTED candles (hand-computed). python3 -I oiver_spread_test.py"""
import sys, os, gzip, json, tempfile, calendar, time, io, contextlib, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import oiver_spread as O
def iso(t): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
def folder(d, name, body):
    p = os.path.join(d, name); os.makedirs(p); raw = json.dumps(body).encode()
    with gzip.open(p + "/0001.json.gz", "wb") as f: f.write(raw)
    json.dump({"status": "complete", "rows": [{"index": 1, "id": "r1", "page": 1, "status": 200, "bytes": len(raw), "file": "0001.json.gz", "sha256": hashlib.sha256(raw).hexdigest(), "truncated": False, "body_kind": "object"}]}, open(p + "/manifest.json", "w")); return p
base = calendar.timegm(time.strptime("2026-11-10", "%Y-%m-%d")) + 15 * 3600
mk, cd = [], []
def C(end, bid, ask, oi): return {"end_period_ts": end, "yes_bid": {"close": bid}, "yes_ask": {"close": ask}, "open_interest_fp": str(oi)}
def win(name, k, rise, dec, fill, result="yes", skip_prev=False):
    c = base + 900 * k; tk = "KXBTC15M-" + name; mk.append({"ticker": tk, "close_time": iso(c), "result": result})
    cs = [C(c - 180, dec[0], dec[1], 1000000 + rise), C(c - 120, fill[0], fill[1], 1000000 + rise)]
    if not skip_prev: cs.append(C(c - 360, 0.5, 0.5, 1000000))
    cd.append({"market_ticker": tk, "candlesticks": cs})
win("W1", 1, 100000, (0.08, 0.10), (0.08, 0.10), "yes")      # YES 0.10, spread 0.02, wins: 20 contracts, fee ceil(0.07 x 20 x 0.10 x 0.90 x 100) = 13c, per contract 0.0065: cash 1 - 0.10 - 0.0065 = 0.8935; version passes
win("W2", 2, 100000, (0.20, 0.26), (0.20, 0.26), "no")       # YES 0.26, spread 0.06, loses: fee 27c / 20 = 0.0135: cash -0.26 - 0.0135 = -0.2735; parent only
win("W3", 3, 100000, (0.70, 0.73), (0.68, 0.72), "yes")      # NO 0.30 (YES ask 0.73, bid 0.70), spread exactly 0.03; filled at the ask SEEN (no slip, no next-candle fill check, the later candle is ignored); NO loses: fee 30c / 20 = 0.015: cash -0.30 - 0.015 = -0.315; version passes
win("W4", 4, 50000, (0.08, 0.10), (0.08, 0.10), "yes")       # rise below 86,300: not fired
win("W5", 5, 100000, (0.03, 0.05), (0.03, 0.05), "yes")      # YES 0.05: outside the 0.08 floor
win("W6", 6, 100000, (0.44, 0.47), (0.45, 0.48), "yes")      # YES 0.47, spread exactly 0.03 (version passes), filled at 0.47, wins: fee 35c / 20 = 0.0175: cash 1 - 0.47 - 0.0175 = 0.5125
win("W7", 7, 100000, (0.08, 0.10), (0.08, 0.10), "yes", skip_prev=True)    # the close-360 candle missing
win("W8", 8, 100000, (0.30, 0.35), (0.30, 0.35), "no")       # YES 0.35, spread 0.05, loses: fee 32c / 20 = 0.016: cash -0.35 - 0.016 = -0.366; parent only
win("W9", 9, 100000, (0.08, 0.10), (0.08, 0.10), "void")     # a void result: dropped before scoring
win("W10", 10, 100000, (0.50, 0.50), (0.50, 0.50), "yes")    # locked book: skipped
d = tempfile.mkdtemp(); lists = folder(d, "l", {"markets": mk}); cands = folder(d, "c", {"markets": cd})
windows, bad = O.load_windows(lists); assert bad == 1 and len(windows) == 9, (bad, len(windows))
C_ = O.load_candles(cands); trades, why = {}, {}
for tk, w in windows.items():
    t, r = O.decide(w, C_.get(tk, {})); why[tk.split("-")[1]] = r
    if t: trades[tk[len("KXBTC15M-"):]] = t
assert sorted(trades) == ["W1", "W2", "W3", "W6", "W8"], (sorted(trades), why)
assert abs(trades["W1"]["cash"] - 0.8935) < 1e-12 and abs(trades["W2"]["cash"] + 0.2735) < 1e-12 and abs(trades["W3"]["cash"] + 0.315) < 1e-12 and abs(trades["W6"]["cash"] - 0.5125) < 1e-12 and abs(trades["W8"]["cash"] + 0.366) < 1e-12
assert [trades[k]["spread_ok"] for k in ("W1", "W2", "W3", "W6", "W8")] == [True, False, True, True, False]
assert all(abs(trades[k]["p"] - v) < 1e-12 for k, v in (("W1", 0.10), ("W2", 0.26), ("W3", 0.30), ("W6", 0.47), ("W8", 0.35)))      # the price paid is the ask seen at the decision candle
assert why["W4"] == "not fired" and why["W5"] == "outside 0.08 to 0.50" and why["W7"] == "missing candle" and why["W10"] == "crossed or locked book", why
assert O.CONTRACTS == 20 and O.fee_up(0.10) == 0.13 and O.fee_up(0.26) == 0.27 and O.fee_up(0.47) == 0.35 and O.fee_up(0.30) == 0.30 and O.fee_up(0.35) == 0.32
buf = io.StringIO()
with contextlib.redirect_stdout(buf): O.main(lists, cands)
out = buf.getvalue()
assert "parent OICORE: n 5 | win 40.0% | cash PF 1.47 | mean +9.03c a contract" in out, out          # PF = (0.8935 + 0.5125) / (0.2735 + 0.315 + 0.366) = 1.4731; mean (1.406 - 0.9545) / 5 = 0.0903
assert "version SPREAD <= 3c: n 3 | win 66.7% | cash PF 4.46 | mean +36.37c a contract" in out, out      # W1, W3, W6: (0.8935 + 0.5125) / 0.315 = 4.4635; mean (1.406 - 0.315) / 3 = 0.3637
assert "share of parent signals removed by the spread condition: 40.0%" in out and "n >= 60 version signals: NO" in out and "no evidence at n = 3 version trades" in out and "windows dropped for a result that is not yes or no: 1" in out, out
# a window with NO fill candle at all still trades now (the fill is the ask seen at the decision candle)
c0 = base + 900 * 30; tk0 = "KXBTC15M-NF"; mk3 = [{"ticker": tk0, "close_time": iso(c0), "result": "yes"}]; cd3 = [{"market_ticker": tk0, "candlesticks": [C(c0 - 180, 0.08, 0.10, 1100000), C(c0 - 360, 0.5, 0.5, 1000000)]}]
d3 = tempfile.mkdtemp(); w3, _ = O.load_windows(folder(d3, "l", {"markets": mk3})); t3, r3 = O.decide(w3[tk0], O.load_candles(folder(d3, "c", {"markets": cd3}))[tk0]); assert r3 == "trade" and abs(t3["p"] - 0.10) < 1e-12
# halves by COUNT: the first half is FLOOR(n / 2) trades, in date order (the Head, 19:54Z): 5 trades split 2 and 3
tr5 = [dict(close=i * 86400, cash=0.1, win=True) for i in range(5)]; h1, h2 = O.halves(tr5); assert (len(h1), len(h2)) == (2, 3) and h1[-1]["close"] == 1 * 86400 and h2[0]["close"] == 2 * 86400
tr4 = [dict(close=i * 86400, cash=0.1, win=True) for i in range(4)]; h1, h2 = O.halves(tr4); assert (len(h1), len(h2)) == (2, 2)
tr1 = [dict(close=0, cash=0.1, win=True)]; h1, h2 = O.halves(tr1); assert (len(h1), len(h2)) == (0, 1)
# 86,300 is INCLUSIVE: a rise of exactly 86,300 fires, 86,299 does not
for rise, fired in ((86300, True), (86299, False)):
    c1 = base + 900 * 31; wx = dict(close=c1, yes=True); csx = {c1 - 180: dict(bid=0.08, ask=0.10, oi=1000000.0 + rise), c1 - 360: dict(bid=0.5, ask=0.5, oi=1000000.0)}
    assert (O.decide(wx, csx)[0] is not None) == fired, rise
# the held-out windows never load: a window closing on 2026-12-01 is excluded
mk2 = [{"ticker": "KXBTC15M-H", "close_time": "2026-12-01T15:00:00Z", "result": "yes"}]; l2 = folder(d, "l2", {"markets": mk2}); w2, _ = O.load_windows(l2); assert w2 == {}
# the source reads no field beyond the named ones
src = open(os.path.join(here, "oiver_spread.py")).read().split("import sys, os, gzip", 1)[1]
for bad in ("floor_strike", "volume", "yes_sub_title", "rules_primary"): assert bad not in src, bad
print("OIVER-SPREAD HAND CASE OK (parent and version rules, limit fill, floor, spread slack, missing candle, locked book, void dropped, fees, held-out windows never load)")
print(out.strip())
