#!/usr/bin/env python3
"""DEPTH1 Bitcoin OICORE-overlap candle job (Head's ruling Nov 13, 2026): WRITTEN NOW, NOT SENT. To be sent ONLY if a Bitcoin try clears DEPTH1's bar, and only on the Head's word, to assign the 'paper only' label afterwards.
Offline: sends nothing. One request per market, two candles needed (the ones ending close-360 s and close-180 s): start_ts = close-420 s, end_ts = close-180 s EXACTLY, so no result and no minute after the decision is reached
(CFRTI's held-out closes are untouched: nothing after close-180 s of any market is requested). KXBTC15M tickers only; 1-minute candles; GET /markets/candlesticks with market_tickers = ONE ticker.
  python3 -I build_depth1_btc_candles.py <tickers.csv: columns ticker,close_ts (epoch seconds), nothing else> <outdir>
The input file is made from the R6 coverage file's ticker and close_time columns ONLY (no result column is read); to keep the job small, list only the Bitcoin windows whose try fired a trade.
  python3 -I build_depth1_btc_candles.py selftest"""
import csv, json, os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "desk_a_verify"))
LEAD_END, LEAD_START = 180, 420
RE = re.compile(r"^KXBTC15M-[0-9A-Z]+-[0-9]+$")
def build(rows):
    reqs, seen = [], set()
    for tk, close in rows:
        assert RE.match(tk), "not a KXBTC15M ticker: " + tk
        if tk in seen: continue
        seen.add(tk)
        reqs.append(dict(id="b%04d" % len(reqs), path="/markets/candlesticks", params=dict(market_tickers=tk, start_ts=close - LEAD_START, end_ts=close - LEAD_END, period_interval=1)))
    for (tk, close), r in zip([x for x in rows if True][:0], reqs): pass
    return reqs
def job(rows):
    reqs = build(rows)
    return dict(job_id="DEPTH1_BTC_OI", owner="DESK_A", registration="kalshi-scalper/workers/DEPTH1_AMENDMENT_2_DESK_A.md",
        purpose="DEPTH1 Bitcoin OICORE overlap mark: two 1-minute candles per market (ending close-360 s and close-180 s), request ends at close-180 s. No result read, nothing after the decision.",
        heldout="none reached: every request ends at close-180 s of its own market", allowed_endpoints=[dict(name="markets_candlesticks", method="GET", path_pattern="/markets/candlesticks", params_allowed=["market_tickers", "start_ts", "end_ts", "period_interval"])],
        series_allowlist=["KXBTC15M"], ticker_allowlist=sorted({r["params"]["market_tickers"] for r in reqs}), max_requests=len(reqs), status="active", host="api.elections.kalshi.com", base_path="/trade-api/v2", pacing_seconds=1.0,
        stop_rules={"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out; three in a row end the run; no other address, no proxy, no retry around a refusal"}, requests=reqs)
def check(j, rows):
    close = dict(rows)
    for r in j["requests"]:
        tk = r["params"]["market_tickers"]; assert "," not in tk and r["params"]["end_ts"] == close[tk] - LEAD_END and r["params"]["start_ts"] == close[tk] - LEAD_START and r["params"]["period_interval"] == 1
        assert set(r["params"]) == {"market_tickers", "start_ts", "end_ts", "period_interval"}
    assert j["max_requests"] == len(j["requests"]) == len(j["ticker_allowlist"])
def main(path, outdir):
    import heldout_guard_v2 as heldout_guard; heldout_guard.refuse_heldout(path, "depth1 btc candle builder")
    with open(path, newline="") as f:
        rd = csv.DictReader(f); assert rd.fieldnames == ["ticker", "close_ts"], "input must have exactly the columns ticker,close_ts"
        rows = [(r["ticker"], int(r["close_ts"])) for r in rd]
    j = job(rows); check(j, rows); os.makedirs(outdir, exist_ok=True); json.dump(j, open(os.path.join(outdir, "DEPTH1_BTC_OI.json"), "w"), indent=1)
    print("%d requests, one per market, each ends at close-180 s" % len(j["requests"]))
def selftest():
    rows = [("KXBTC15M-26NOV051530-30", 1794000000), ("KXBTC15M-26NOV051545-45", 1794000900), ("KXBTC15M-26NOV051530-30", 1794000000)]
    j = job(rows); check(j, rows); assert len(j["requests"]) == 2 and j["requests"][0]["params"]["end_ts"] == 1794000000 - 180
    try: job([("KXETH15M-26NOV051530-30", 1)]); raise SystemExit("FAIL: non-BTC accepted")
    except AssertionError: pass
    print("selftest OK")
if __name__ == "__main__":
    selftest() if sys.argv[1:2] == ["selftest"] else main(*sys.argv[1:3])
