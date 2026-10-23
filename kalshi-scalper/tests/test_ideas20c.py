import sys
sys.path.insert(0, "src")
from scalper import ideas20 as I
from scalper import ideas20c as C

def cd(end, bid, ask):
    return {"end": end, "bid": bid, "ask": ask, "bid_h": bid, "bid_l": bid, "ask_h": ask, "ask_l": ask, "vol": 100.0, "oi": 1000.0, "last": ask}

close = 1_700_000_000
m = {"close": close, "res": "yes", "strike": 2.5, "c": [cd(close - 360 - 60 * k, 0.92, 0.93) for k in range(6, -1, -1)]}
names = [r[0] for r in C.all_rules({"A": m})]
assert len(names) == 38 and "ROUND" not in names and "ROUND500" not in names and "TIGHT" in names
rows = C.pooled({"KXXRP15M": {"A": m}, "KXGOLD15M": {"A": m}}, "TIGHT", "2099-01-01")
assert len(rows) == 2 and abs(rows[0]["net"]) < 1e-9 and rows[0]["raw"] > 0      # the only entry is its own baseline and {r["series"] for r in rows} == {"KXXRP15M", "KXGOLD15M"}
print("ok")
