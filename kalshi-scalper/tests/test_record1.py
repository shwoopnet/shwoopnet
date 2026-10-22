import sys
sys.path.insert(0, "src")
from scalper import record1 as T

# a flat 100.0 index on three exchanges for 400 seconds, then trades
spot = [{"t_recv_ms": str(1_000_000 + i * 1000), "exchange": e, "asset": "BTC", "price": "100.0"} for i in range(400) for e in ("coinbase", "kraken", "bitstamp")]
for i, r in enumerate(spot):
    r["price"] = str(100.0 + (0.01 if (i // 3) % 2 else -0.01))        # tiny alternating wiggle so sigma > 0
idx = T.index_by_second(spot, "BTC")
assert len(idx) >= 390, len(idx)
close_ms = 1_000_000 + 399_000
poll = lambda t, bid, ask, bs=50.0, asz=50.0: {"t": t, "bid": bid, "ask": ask, "bid_size": bs, "ask_size": asz, "strike": 90.0}
# strike far below the index: P(YES) is ~1, an ask of 0.80 leaves a large edge -> buy YES; result yes
tr = T.trade_for([poll(close_ms - 60_000, 0.78, 0.80)], idx, close_ms, "yes", 90.0)
assert tr is not None and tr["side"] == "yes" and abs(tr["net"] - (0.2 - T.fee(0.8))) < 1e-9, tr
# the same with a thin ask (size 4 < 5): no trade
assert T.trade_for([poll(close_ms - 60_000, 0.78, 0.80, asz=4.0)], idx, close_ms, "yes", 90.0) is None
# an ask of 0.995 leaves no edge after the fee and margin: no trade
assert T.trade_for([poll(close_ms - 60_000, 0.99, 0.995)], idx, close_ms, "yes", 90.0) is None
# strike far above the index: P(YES) ~0, a bid of 0.20 means NO costs 0.80 -> buy NO; result no
tr = T.trade_for([poll(close_ms - 60_000, 0.20, 0.22)], idx, close_ms, "no", 110.0)
assert tr is not None and tr["side"] == "no" and abs(tr["price"] - 0.80) < 1e-9, tr
assert T.judge([])["verdict"] == "NOT_ENOUGH_DATA"
print("ok")
