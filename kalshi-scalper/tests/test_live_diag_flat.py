import sys
sys.path.insert(0, "src")
from scalper import live_diag as T

o = lambda tk, rng, rise, pnl=0.05: {"ticker": tk, "rng5": rng, "rise3": rise, "pnl_c": pnl}
assert T.is_flat(o("KXETH15M-X-1", 0.15, 0.05)) is True and T.is_flat(o("KXETH15M-X-1", 0.16, 0.0)) is False
assert T.is_flat({"rng5": None, "rise3": 0.0}) is None and T.is_flat({"rng5": 0.1, "rise3": None}) is None
rows = [o("KXETH15M-W1-1", 0.1, 0.0), o("KXETH15M-W2-1", 0.5, 0.0), o("KXBTC15M-W3-1", 0.1, 0.3)]
txt = T.flat_section(rows, [])
assert "ETH" in txt and "(50%)" in txt and "BTC" in txt and "(0%)" in txt, txt
assert T.flat_section([{"ticker": "KXETH15M-W1-1", "rng5": None, "rise3": None}], []) == ""
print("ok")
