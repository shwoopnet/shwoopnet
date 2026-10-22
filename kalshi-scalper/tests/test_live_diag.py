"""Plain assert tests for the live-account diagnosis (src/scalper/live_diag.py); run with: python tests/test_live_diag.py."""
import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import live_diag as D

assert abs(D.binom_tail(0, 10, 0.1) - 1.0) < 1e-12 and abs(D.binom_tail(10, 10, 0.5) - 0.5 ** 10) < 1e-15
assert abs(D.binom_tail(2, 3, 0.5) - 0.5) < 1e-12
csv_text = ("time,ticker,side,status,fillCount,avgFill,avgFee,entryLead,rise3\n"
            "2026-10-22T10:00:00Z,KXBTC15M-26OCT221000-00,yes,filled,2,0.94,0.004,10m,0.03\n"
            "2026-10-22T10:15:00Z,KXBTC15M-26OCT221015-15,no,filled,1,0.06,0.004,10m,0.30\n"       # NO order: YES-book fill 0.06 -> paid 0.94
            "2026-10-22T10:30:00Z,KXGOLD15M-26OCT221030-30,yes,filled,1,0.93,0.005,6m,\n"
            "2026-10-22T10:45:00Z,KXGOLD15M-26OCT221045-45,yes,rejected,0,,,6m,\n")
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "o.csv"
    p.write_text(csv_text)
    rows = D.load_orders(str(p))
    D.settle(rows, {"KXBTC15M-26OCT221000-00": "yes", "KXBTC15M-26OCT221015-15": "yes", "KXGOLD15M-26OCT221030-30": "no"})
assert abs(rows[1]["paid"] - 0.94) < 1e-9 and rows[0]["win"] is True and rows[1]["win"] is False and rows[2]["win"] is False
assert abs(rows[0]["pnl_c"] - 2 * (1 - 0.94 - 0.004)) < 1e-9, "a win pays 1 minus the price paid minus the fee, per contract, times the count"
assert abs(rows[1]["pnl_c"] - (-0.94 - 0.004)) < 1e-9, "a NO order whose result is yes loses what it paid plus the fee"
assert rows[3]["pnl_c"] is None and not rows[3]["filled"], "an unfilled order is not scored"
text = D.report(rows)
assert "BY SERIES" in text and "10 minute" in text and "rise 20c or more" in text
print("test_live_diag: ok")
