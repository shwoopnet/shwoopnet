"""Tests of scorekit's exit and resting-order pricing (standing rule (i)). Synthetic."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
c = lambda ts, bid, low=None, ask=None: {"ts": ts, "bid": bid, "bid_low": low, "ask": ask}
# round trip cost: spread plus both fees (rounded up)
assert abs(k.round_trip_cost(0.40, 0.44) - (0.04 + k.fee_rounded(0.44) + k.fee_rounded(0.40))) < 1e-12 and k.round_trip_cost(0.40, 0.44) > 0.05
# taker exit sells at the BID of the exit minute (candle bid close), fails closed if absent
ser = [c(60, 0.50), c(120, 0.55), c(180, 0.52)]
assert k.exit_bid(ser, 120) == 0.55 and k.exit_bid(ser, 240) is None
assert abs(k.taker_exit_net(0.45, 0.55) - (0.10 - k.fee_rounded(0.45) - k.fee_rounded(0.55))) < 1e-12
# a book wins over the candle: first poll at or after the minute, best YES bid
polls = [{"t": 119, "yes_bids": [(0.60, 5)], "no_bids": []}, {"t": 121, "yes_bids": [(0.53, 2), (0.52, 9)], "no_bids": []}]
assert k.exit_bid(ser, 120, polls) == 0.53
# stop: fills at the first bid at or after the crossing, however far through, never at the level
s2 = [c(60, 0.50, 0.49), c(120, 0.44, 0.40), c(180, 0.30, 0.28)]
assert k.stop_exit(s2, 0, 0.45) == (120, 0.44)                    # close 0.44 <= stop 0.45: fills at the close, not at 0.45
s3 = [c(60, 0.50, 0.49), c(120, 0.47, 0.40), c(180, 0.30, 0.28)]
assert k.stop_exit(s3, 0, 0.45) == (120, 0.40)                    # crossed inside the minute, close recovered: the minute's LOW (conservative), never 0.45
s4 = [c(60, 0.50, 0.49), c(120, 0.30, 0.20)]                      # gap through: fills at 0.30, far below the level
assert k.stop_exit(s4, 0, 0.45) == (120, 0.30) and k.stop_exit([c(60, 0.5, 0.49)], 0, 0.45) is None
assert k.stop_exit(s2, 120, 0.45) == (180, 0.30)                  # from the minute after t_from only
pl = [{"t": 10, "yes_bids": [(0.50, 3)], "no_bids": []}, {"t": 20, "yes_bids": [(0.41, 3)], "no_bids": []}, {"t": 30, "yes_bids": [(0.20, 3)], "no_bids": []}]
assert k.stop_exit([], 0, 0.45, pl) == (20, 0.41)
# resting buy at 0.40, 3 contracts, 5 ahead at the price
tape = [{"ts": 10, "price": 0.40, "count": 4, "taker": "sell"}, {"ts": 20, "price": 0.40, "count": 4, "taker": "buy"}, {"ts": 30, "price": 0.40, "count": 2, "taker": None}, {"ts": 40, "price": 0.40, "count": 4, "taker": "sell"}]
o = k.resting_order("buy", 0.40, 3, 0, tape, size_ahead=5)
assert o["filled"] == 3 and o["fills"] == [(40, 3.0)], o         # 4 sold at the price: 4 of the 5 ahead; the buy print and the unknown-aggressor print do not count; the next sell clears 1 ahead then fills 3
assert k.resting_order("buy", 0.40, 3, 0, tape[:1], size_ahead=5)["filled"] == 0         # not enough traded ahead
th = [{"ts": 5, "price": 0.39, "count": 2, "taker": "sell"}, {"ts": 6, "price": 0.38, "count": 5, "taker": "sell"}]
o2 = k.resting_order("buy", 0.40, 3, 0, th, size_ahead=99); assert o2["filled"] == 3 and o2["fills"] == [(5, 2.0), (6, 1.0)]       # strictly through fills regardless of the queue
assert k.resting_order("buy", 0.40, 3, 7, th)["filled"] == 0 and k.resting_order("buy", 0.40, 3, 0, [{"ts": 1, "price": 0.40, "count": 9, "taker": "sell"}], 0)["filled"] == 3   # prints before t0 ignored; empty queue fills at the price
# resting sell mirrors it
os_ = k.resting_order("sell", 0.60, 2, 0, [{"ts": 1, "price": 0.61, "count": 1, "taker": "buy"}, {"ts": 2, "price": 0.60, "count": 5, "taker": "buy"}], size_ahead=2)
assert os_["fills"] == [(1, 1.0), (2, 1.0)] or os_["filled"] == 2, os_
rep = k.resting_report([o, k.resting_order("buy", 0.40, 3, 0, tape[:1], 5), o2]); assert rep == {"orders": 3, "filled_in_full": 2, "filled_in_part": 0, "not_filled": 1, "contracts_filled": 6.0, "contracts_unfilled": 3.0}, rep
print("exits and resting orders tests passed")
