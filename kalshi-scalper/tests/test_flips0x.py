import sys
from datetime import datetime, timezone
sys.path.insert(0, "src")
from scalper import flips0x as T

assert T.judge([])["verdict"] == "NOT_ENOUGH_DATA"
def cd(end, bid, ask):
    return {"end": end, "bid": bid, "ask": ask, "bid_h": bid, "bid_l": bid, "ask_h": ask, "ask_l": ask, "vol": 1.0, "oi": 1.0, "last": ask}
close = int(datetime(2026, 10, 5, 13, 30, tzinfo=timezone.utc).timestamp())
smooth = [cd(close - 900 + 60 * k, 0.50 + 0.04 * k, 0.51 + 0.04 * k) for k in range(0, 8)] + [cd(close - 360, 0.91, 0.92)]    # a climb with no flip, then the 6 minute candle
mk = {"A": {"close": close, "res": "yes", "strike": 1.0, "c": smooth}}
rows = T.series_rows("KXXRP15M", mk)
assert len(rows) == 1 and abs(rows[0]["net"]) < 1e-9 and rows[0]["raw"] > 0        # the only entry is its own baseline
assert T.forward(now=0.0).startswith("Refusing the registered read")
print("ok")
