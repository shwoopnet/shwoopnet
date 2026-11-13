#!/usr/bin/env python3
"""Builds the made-up run folder for HAND_CASE.md (NOT Kalshi data). usage: python3 -I make_fixture.py <out dir> [dec|incomplete]"""
import sys, os, json, gzip
out = sys.argv[1]; mode = sys.argv[2] if len(sys.argv) > 2 else ""
os.makedirs(out, exist_ok=True)
def c(ts, bid, ask):
    d = {"end_period_ts": ts, "volume_fp": "99.00", "open_interest_fp": "1.00", "price": {"close_dollars": "0.9900"}}
    if bid is not None: d["yes_bid"] = {"close_dollars": bid}
    d["yes_ask"] = {"close_dollars": ask}
    return d
A = "KXINX15M-26NOV051300-00"; B = "KXINX15M-26NOV051315-15"; C = "KXINX15M-26NOV051330-30"; O = "KXINX15M-26NOV051345-45"
a = [("0.4900", "0.5100"), ("0.5000", "0.5100"), ("0.7000", "0.7300"), ("0.7100", "0.7500"), ("0.0000", "0.0500"), ("0.9500", "1.0000"), ("0.2000", "0.2200"),
     (None, "0.4000"), ("0.4000", "0.4000"), ("0.6900", "0.7200"), ("0.3000", "0.3300"), ("0.8000", "0.8100"), ("0.5000", "0.5050")]
body1 = {"markets": [{"market_ticker": A, "candlesticks": [c(1000 + 60 * i, b, k) for i, (b, k) in enumerate(a)]}, {"market_ticker": B, "candlesticks": []},
                     {"market_ticker": C, "candlesticks": [c(100, "0.4500", "0.4700"), c(160, "0.4500", "0.4800")]}, {"market_ticker": O, "candlesticks": [c(5, "0.1000", "0.1100")]}]}
body2 = {"markets": [{"market_ticker": C, "candlesticks": [c(100, "0.4500", "0.4700"), c(160, "0.4500", "0.4900")]}]}
tick = A + "," + B + "," + C + (",KXINX15M-26DEC011000-00" if mode == "dec" else "")
rows = []
for i, b in enumerate((body1, body2)):
    f = "%04d.json.gz" % i; gzip.open(os.path.join(out, f), "wt").write(json.dumps(b))
    rows.append({"id": "r%d" % i, "params": {"market_tickers": tick}, "status": 200, "file": f, "bytes": 1, "truncated": False})
json.dump({"job": {"job_id": "MADE_UP_FIXTURE"}, "status": "incomplete" if mode == "incomplete" else "complete", "requests_sent": 2, "rows": rows}, open(os.path.join(out, "manifest.json"), "w"))
