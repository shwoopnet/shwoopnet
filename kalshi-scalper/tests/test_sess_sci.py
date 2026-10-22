"""Plain assert tests for SESS1 and SCI1 (src/scalper/sess_sci.py); run with: python tests/test_sess_sci.py."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import sess_sci as S
from scalper.scalps import fee

assert (S.SCALE_TIMES, S.SESS_Z, S.SESS_MIN_CLOSED, S.SCI_Z, S.SCI_DIFF_Z, S.SCI_MIN_N, S.MIN_DAYS) == ((720, 600, 480), 2.4, 300, 2.8, 2.0, 1000, 10), "the registered numbers"
ts = lambda y, mo, d, h, mi=0: int(datetime(y, mo, d, h, mi, tzinfo=timezone.utc).timestamp())
assert S.closed(ts(2026, 10, 24, 12)), "Saturday"
assert S.closed(ts(2026, 10, 23, 21, 30)) and not S.closed(ts(2026, 10, 23, 20, 59)), "Friday from 21:00 UTC"
assert S.closed(ts(2026, 10, 25, 21, 59)) and not S.closed(ts(2026, 10, 25, 22, 0)), "Sunday until 22:00 UTC"
assert S.closed(ts(2026, 10, 21, 21, 30)) and not S.closed(ts(2026, 10, 21, 22, 0)), "daily break 21:00 to 22:00 UTC"
close = 100_000
c = [(close - 720, 0.89, 0.90, 0, 0), (close - 600, 0.92, 0.93, 0, 0), (close - 480, 0.70, 0.71, 0, 0)]   # third buy: price fell out of band, not bought
net, k = S.scale_in(c, close, "yes")
assert k == 2 and abs(net - ((1 - 0.90 - fee(0.90)) + (1 - 0.93 - fee(0.93))) / 2) < 1e-12, "per contract, only the thirds bought"
flip = [(close - 720, 0.89, 0.90, 0, 0), (close - 600, 0.05, 0.06, 0, 0)]    # second time favourite is NO: different side, not bought
net2, k2 = S.scale_in(flip, close, "no")
assert k2 == 1 and abs(net2 - (-0.90 - fee(0.90))) < 1e-12
assert S.scale_in([(close - 360, 0.93, 0.94, 0, 0)], close, "yes") is None, "no qualifying time among 12/10/8 minutes"
print("test_sess_sci: ok")
