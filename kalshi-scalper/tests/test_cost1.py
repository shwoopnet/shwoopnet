import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper.cost1 import fee_cents, band_of, klass, fee_row

assert fee_cents(50, 1) == 2          # 1.75c rounds up to 2c
assert fee_cents(1, 1) == 1           # 0.0693c rounds up to a whole cent: 100 percent of price
assert fee_cents(1, 100) == 7         # 6.93c -> 7c
assert fee_cents(92, 1) == 1          # 0.51c -> 1c
assert fee_cents(50, 100) == 175
assert fee_cents(50, 10, 0.0175) == 5  # 0.4375c... 10 x 0.0175 x .25 = 4.375c -> 5c
assert band_of(97) == (85, 97) and band_of(98) == (97, 99) and band_of(0) is None
assert klass("KXBTC15M") == "crypto" and klass("KXGOLD15M") == "metals_energy" and klass("KXEURUSD15M") == "fx"
assert abs(fee_row(10, 10)[2] - 100 * fee_cents(10, 10) / 100) < 1e-9
print("cost1 tests ok")
