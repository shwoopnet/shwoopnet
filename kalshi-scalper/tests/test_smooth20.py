import sys
from datetime import datetime, timezone
sys.path.insert(0, "src")
from scalper import smooth20 as T

def cd(end, bid, ask):
    return {"end": end, "bid": bid, "ask": ask, "bid_h": bid, "bid_l": bid, "ask_h": ask, "ask_l": ask, "vol": 1.0, "oi": 1.0, "last": ask}
close = int(datetime(2026, 10, 5, 13, 30, tzinfo=timezone.utc).timestamp())
R = dict(T.rules())
assert len(R) == 20
band = (0.88, 0.97)
smooth = {"close": close, "res": "yes", "strike": 1.0, "c": [cd(close - 900 + 60 * k, 0.50 + 0.04 * k, 0.51 + 0.04 * k) for k in range(0, 8)] + [cd(close - 360, 0.91, 0.92)]}
c, e = T.I.at(smooth, 360)
assert R["NO_DOWN_MINUTE"](smooth, c, e, band) is not None and R["LAST4_UP"](smooth, c, e, band) is not None and R["R2_GE_90"](smooth, c, e, band) is not None
choppy = {**smooth, "c": [cd(close - 900 + 60 * k, 0.50 + 0.04 * k - (0.06 if k % 2 else 0), 0.51 + 0.04 * k - (0.06 if k % 2 else 0)) for k in range(0, 8)] + [cd(close - 360, 0.91, 0.92)]}
c2, e2 = T.I.at(choppy, 360)
assert R["NO_DOWN_MINUTE"](choppy, c2, e2, band) is None and R["MAXPULL_LE_020"](choppy, c2, e2, band) is None
assert T.r2([0.5, 0.4, 0.3, 0.2]) is None                # falling path
print("ok")
