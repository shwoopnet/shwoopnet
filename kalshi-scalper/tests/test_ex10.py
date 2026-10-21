"""Plain assert tests for EX10 (src/scalper/ex10.py); run with: python tests/test_ex10.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import ex10 as X
from scalper.scalps import fee

assert (X.LINES, X.LIVE_LINE, X.ENTRY_S, X.SLIP, X.SLIP_ALT, X.Z_BAR, X.MIN_HOLDOUT) == ((0.10, 0.15, 0.20, 0.25, 0.30, 0.35), 0.25, 600, 0.02, 0.05, 2.4, 500), "the registered numbers"
close = 10_000
entry = {"side": "yes", "price": 0.93, "net": 0.05}
dip = [(close - 600, 0.92, 0.93, 0.92, 0.93), (close - 540, 0.70, 0.71, 0, 0), (close - 480, 0.22, 0.23, 0, 0), (close - 420, 0.97, 0.98, 0, 0)]
n, ex = X.exit_net(entry, dip, close, 0.25, 0.02)
got = 0.22 - 0.02
assert ex and abs(n - (got - fee(got) - 0.93 - fee(0.93))) < 1e-12, "sold at the bid minus slippage, with fees"
n2, ex2 = X.exit_net(entry, dip, close, 0.20, 0.02)
assert not ex2 and n2 == 0.05, "a lower line does not fire on a 22c dip; the position is held"
# NO side: the YES ask is 0.80 -> the NO bid is 0.20
no = {"side": "no", "price": 0.93, "net": -0.93}
n3, ex3 = X.exit_net(no, [(close - 540, 0.78, 0.80, 0, 0)], close, 0.25, 0.0)
assert ex3
# the entry candle itself never triggers
assert X.exit_net(entry, [(close - 600, 0.10, 0.11, 0, 0)], close, 0.25, 0.0) == (0.05, False)
print("test_ex10: ok")
