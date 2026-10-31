"""Gate tests for R6T Amendment 1 (posted-order gate) on SYNTHETIC rows only; no recorded R6 row is used.
Run with: python tests/test_r6_gate.py."""
import contextlib
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import r6tests as R
from scalper.quote2b import Poll

CLOSE = 1_800_000_000.0
OPEN = CLOSE - 900


def path(bid, ask, until=CLOSE):
    out, t = [], OPEN
    while t < until:
        out.append(Poll(t, [bid], [5.0], [round(1 - ask, 4)], [3.0]))
        t += 2
    return out


# MAKER5 posted: both bids, bid below ask, mid 0.20..0.80 at T-12 min
assert R.posted_flags(path(0.50, 0.52), CLOSE)[0]
assert not R.posted_flags(path(0.85, 0.87), CLOSE)[0]                       # mid out of band
assert not R.posted_flags(path(0.52, 0.50), CLOSE)[0]                       # crossed
assert not R.posted_flags([Poll(t, [0.5], [5], [], []) for t in range(int(OPEN), int(CLOSE), 2)], CLOSE)[0]   # no NO bid
assert not R.posted_flags([p for p in path(0.50, 0.52) if p.t > CLOSE - 600], CLOSE)[0]   # no poll near T-12 min
# L1Q1 signal: exactly one side with ask 0.88..0.97 at the 6 minute look
assert R.posted_flags(path(0.90, 0.92), CLOSE)[1]                           # YES side
assert R.posted_flags(path(0.07, 0.09), CLOSE)[1]                           # NO side: NO ask = 1 - 0.07 = 0.93
assert not R.posted_flags(path(0.50, 0.52), CLOSE)[1]                       # neither
assert not R.posted_flags(path(0.98, 0.99), CLOSE)[1]                       # above band
assert not R.posted_flags(path(0.90, 0.92, CLOSE - 400), CLOSE)[1]          # last poll older than 10 s before T-360
# price-only: the counter does not take trades, results or fills at all
import inspect
assert list(inspect.signature(R.posted_flags).parameters) == ["polls", "close"]
src = inspect.getsource(R.posted_by_window) + inspect.getsource(R.posted_flags)
assert "trades.csv.gz" not in src and "_trade" not in src and 'get("result")' not in src and '["result"]' not in src

# gate message
assert R.gate_message({"maker5": 300, "l1q1": 300}) is None
m = R.gate_message({"maker5": 299, "l1q1": 500})
assert "maker5 299 of 300" in m and "l1q1" not in m
m = R.gate_message({"maker5": 10, "l1q1": 20})
assert "maker5 10 of 300" in m and "l1q1 20 of 300" in m

# run: existing refusals hold; the gate refuses when a count is short and writes nothing
_real_counts = R.posted_counts
R.RESULTS = {"maker5": Path("/nonexistent/maker5_result.txt"), "l1q1": Path("/nonexistent/l1q1_result.txt")}
def runout(card, now):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        R.run(card, now=now)
    return buf.getvalue()
before = datetime(2026, 11, 5, 23, tzinfo=timezone.utc).timestamp()
after = datetime(2026, 11, 7, tzinfo=timezone.utc).timestamp()
assert "Refusing: the read date" in runout("maker5", before)
row = lambda c: {"ticker": "X", "series": "KXBTC15M", "polls": "450", "ok_polls": "440", "max_gap_ms": "4000", "tape_pages": "3",
                 "note": "", "first_recv_ms": str(int((c - 899) * 1000)), "last_recv_ms": str(int((c - 1) * 1000)), "result": "yes"}
R.windows = lambda: {(CLOSE + 900 * i, "KXBTC15M"): ("r", row(CLOSE + 900 * i)) for i in range(299)}
for card in ("maker5", "l1q1"):
    assert "Refusing: 299 usable windows" in runout(card, after)
# 300 usable windows but posted counts short -> gate refusal naming the count, no result file
R.windows = lambda: {(CLOSE + 900 * i, "KXBTC15M"): ("r", row(CLOSE + 900 * i)) for i in range(300)}
R.posted_counts = lambda ws=None: {"maker5": 120, "l1q1": 300}
for card in ("maker5", "l1q1"):
    out = runout(card, after)
    assert "posted-order gate not met" in out and "maker5 120 of 300" in out and "l1q1" not in out.split("short:")[1], out
    assert not R.RESULTS[card].exists()
# counts: summed from the per-window flags
R.posted_by_window = lambda ws=None: {(1, "a"): (True, False), (2, "a"): (True, True), (3, "b"): (False, True)}
assert _real_counts() == {"maker5": 2, "l1q1": 2}
print("R6T posted-order gate synthetic tests: all passed")
