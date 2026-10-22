import sys
sys.path.insert(0, "src")
from scalper import stack1 as T

e = lambda s, t: {"series": s, "close_ts": t}
rows = [e("KXETH15M", 1), e("KXBTC15M", 1), e("KXGOLD15M", 1), e("KXDOGE15M", 2), e("KXXRP15M", 2)]
got = sorted((r["series"], r["close_ts"]) for r in T.first_per_window(rows))
assert got == [("KXBTC15M", 1), ("KXXRP15M", 2)], got        # gold is not a crypto order; Bitcoin beats Ethereum; XRP beats Dogecoin
print("ok")
