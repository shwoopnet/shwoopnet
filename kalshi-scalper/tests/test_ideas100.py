import sys
from datetime import datetime, timezone
sys.path.insert(0, "src")
from scalper import ideas100 as D
from scalper import ideas20 as I

def cd(end, bid, ask, vol=100.0, oi=1000.0):
    return {"end": end, "bid": bid, "ask": ask, "bid_h": bid, "bid_l": bid, "ask_h": ask, "ask_l": ask, "vol": vol, "oi": oi, "last": ask}

close = int(datetime(2026, 10, 5, 13, 30, tzinfo=timezone.utc).timestamp())         # a Monday, 13:30 UTC
m = {"close": close, "res": "yes", "strike": 100.0, "c": [cd(close - 900 + 60 * k, 0.60 + 0.02 * k, 0.61 + 0.02 * k) for k in range(0, 6)] + [cd(close - 540, 0.90, 0.91), cd(close - 480, 0.90, 0.91)]}
mk = {"KXBTC15M": {close: m}, "KXETH15M": {}}
ctx = D.Ctx(mk, "KXBTC15M")
ctx.cuts = {"drift": (0.05, 0.1, 0.2), "dd": (0.01, 0.02, 0.03), "rvol": (0.01, 0.02, 0.03), "oi_growth": (1.0, 1.1, 1.2), "oi_level": (900.0, 1000.0, 1100.0)}
R = dict(D.all_rules())
assert len(R) == 100
c, e = I.at(m, 540)
band = (0.80, 0.93)
assert R["HOURBLOCK_12_15"](ctx, m, c, e, band, 540) == ("yes", 0.91) and R["HOURBLOCK_15_18"](ctx, m, c, e, band, 540) is None
assert R["DOW_0"](ctx, m, c, e, band, 540) == ("yes", 0.91) and R["DOW_1"](ctx, m, c, e, band, 540) is None
assert R["SIDE_YES"](ctx, m, c, e, band, 540) is not None and R["SIDE_NO"](ctx, m, c, e, band, 540) is None
assert R["DRIFT_Q4"](ctx, m, c, e, band, 540) is not None and R["DRIFT_Q1"](ctx, m, c, e, band, 540) is None      # mid rose from 0.605 to 0.905, above the top cut
assert R["DD_Q1"](ctx, m, c, e, band, 540) is not None                       # at its peak now: drawdown 0, below the first cut
assert R["PRICE_Q3"](ctx, m, c, e, band, 540) is not None and R["PRICE_Q0"](ctx, m, c, e, band, 540) is None     # 0.91 is in the top quarter of 0.80-0.93
assert R["LAST3_UP"](ctx, m, c, e, band, 540) is not None
assert R["G_OTHER_SAME_FAVYES"](ctx, m, c, e, band, 540) is None            # the other coin has no market for the window
print("ok")
