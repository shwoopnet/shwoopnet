"""Plain assert tests for COMBOPRICE1 (src/scalper/combo_price.py); run with: python3 -I tests/test_combo_price.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import combo_price as C

P = [0.6, 0.7, 0.8, 0.5, 0.9, 0.55]
# At rho 0 the copula is the independence product, and at rho 1 it is the minimum.
assert abs(C.copula_joint(P, 0) - C.independence_product(P)) < 1e-12
assert abs(C.copula_joint(P, 1) - min(P)) < 1e-12
# Independence check by quadrature: tiny rho stays close to the product.
assert abs(C.copula_joint(P, 1e-6) - C.independence_product(P)) < 1e-4
# Positive correlation raises the joint win chance, monotonically, and stays inside the Frechet bounds.
lo, hi = C.frechet_bounds(P)
js = [C.copula_joint(P, r) for r in (0, 0.1, 0.3, 0.5, 0.7, 0.95)]
assert all(a < b for a, b in zip(js, js[1:])) and lo <= js[0] and js[-1] <= hi
# Near rho 1 the quadrature approaches the minimum.
assert abs(C.copula_joint(P, 0.999) - min(P)) < 0.03
# Known two-leg value: p=0.5 each, joint = 1/4 + asin(rho)/(2 pi).
import math
assert abs(C.copula_joint([0.5, 0.5], 0.5) - (0.25 + math.asin(0.5) / (2 * math.pi))) < 1e-6
# Frechet: three legs at 0.5 have lower bound 0 and upper 0.5; high legs have a positive lower bound.
assert C.frechet_bounds([0.5] * 3) == (0.0, 0.5)
assert abs(C.frechet_bounds([0.9, 0.9, 0.9])[0] - 0.7) < 1e-12
# Win chance falls with legs: 30 legs at 0.7 under independence is under 0.0001.
assert C.independence_product([0.7] * 30) < 1e-4 < C.independence_product([0.7] * 10)
# Fee: ceil to the cent of 0.07 p(1-p): at 0.5 it is 0.0175 -> 0.02; unrounded 0.0175.
assert C.taker_fee(0.5) == 0.02 and abs(C.taker_fee(0.5, False) - 0.0175) < 1e-12
# Edge: win chance equal to ask plus fee is zero edge; a fair 30c price with 40% win chance is positive.
assert abs(C.edge_per_dollar(0.30 + C.taker_fee(0.30), 0.30)) < 1e-12
assert C.edge_per_dollar(0.40, 0.30) > 0.1 and C.edge_per_dollar(0.25, 0.30) < 0
assert abs(C.return_per_dollar_year(0.10, 2.0) - 0.05) < 1e-12
# Break-even rho: an ask that equals the independence product plus fee is beaten by any positive rho.
ask = 0.20
assert C.breakeven_rho([0.5, 0.5], 0.25) is not None
assert C.breakeven_rho([0.5, 0.5], 0.60) is None
# Bad inputs are refused.
for bad in ([], [0.0, 0.5], [1.0]):
    try:
        C.independence_product(bad); raise SystemExit("accepted " + repr(bad))
    except ValueError:
        pass
txt = C.format_popup_spec([("KXA-1", "YES", 0.6), ("KXB-2", "NO", 0.7)], 0.30, "YES", "2027-11-02", 1.0, 0.3, "same Senate race")
assert "HELD UNTIL SETTLEMENT" in txt and "Frechet" in txt and "KXB-2 NO" in txt and "BREAK-EVEN" in txt
print("combo_price: all tests passed")
