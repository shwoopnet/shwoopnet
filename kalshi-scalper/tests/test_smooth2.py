import sys
from datetime import datetime, timezone
sys.path.insert(0, "src")
from scalper import smooth2 as T

def cd(end, bid, ask, vol=100.0, oi=1000.0):
    return {"end": end, "bid": bid, "ask": ask, "bid_h": bid, "bid_l": bid, "ask_h": ask, "ask_l": ask, "vol": vol, "oi": oi, "last": ask}
close = int(datetime(2026, 10, 5, 13, 30, tzinfo=timezone.utc).timestamp())
cs = [cd(close - 900 + 60 * k, 0.50 + 0.04 * k, 0.51 + 0.04 * k, vol=100 + 10 * k, oi=1000 + 5 * k) for k in range(0, 8)] + [cd(close - 360, 0.91, 0.92, vol=400, oi=1100)]
m = {"close": close, "res": "yes", "strike": 1.0, "c": cs}
R = dict(T.rules())
assert len(R) == 20
c, e = T.I.at(m, 360)
band = (0.88, 0.97)
for name in ("BIDMONO", "ASKMONO", "CLEANSTART_SMOOTH", "VOL_RISING", "OI_MONO_UP", "SMOOTH_AND_OI", "SMOOTH_AND_VOLRISE", "LAST_STEP_BIG"):
    assert R[name](m, c, e, band) is not None, name
assert R["OFFSTART_SMOOTH"](m, c, e, band) is None and R["LAST_STEP_SMALL"](m, c, e, band) is None and R["VOL_FALLING"](m, c, e, band) is None
assert T.age([0.5, 0.6, 0.85, 0.9], 0.80) == 1 and T.age([0.5, 0.6], 0.80) is None
print("ok")
