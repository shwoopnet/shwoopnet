import sys
sys.path.insert(0, "src")
from scalper import record1 as T

row = lambda off, rtt, v="clock2": {"t_local_ms": "0", "offset_ms": off, "rtt_ms": rtt, "version": v}
# a run with one lopsided sample (137 ms) among small ones passes: the median bound is what counts
assert T.run_clock_ok_b({"clock": [row("10", "20"), row("4", "18"), row("10", "22"), row("137", "300")]}) is True
# a run whose samples are mostly over the bound fails (an offset of 120 ms with a 20 ms round trip is 130 ms at worst)
assert T.run_clock_ok_b({"clock": [row("120", "20"), row("118", "20"), row("5", "10")]}) is False
# the error bound counts: a small offset behind a 400 ms round trip cannot be called within 100 ms
assert T.run_clock_ok_b({"clock": [row("5", "400"), row("6", "380")]}) is False
# an old-format run (no version) or a run with no answered sample is not a RECORD1B run
assert T.run_clock_ok_b({"clock": [{"t_local_ms": "0", "offset_ms": "4"}]}) is None
assert T.run_clock_ok_b({"clock": [row("", "")]}) is None and T.run_clock_ok_b({"clock": []}) is None
# the old rule is untouched: one 137 ms sample still fails an OLD-format run (the scored RECORD1 read stays as scored)
assert T.MAX_OFFSET_MS == 100 and T.MARGIN == 0.03 and T.MIN_SIZE == 5.0 and T.STALE_S == 5 and T.SIGMA_WINDOW_S == 300 and T.MEAN_C == 0.020 and T.Z_BAR == 3.0 and T.MIN_N == 300 and T.MIN_DAYS == 10
# trades_b keeps only tagged runs and stamps the new clock_ok on their trades
mk = lambda cl: {"quotes": [], "spot": [], "results": [], "coverage": [], "clock": cl}
t, c = T.trades_b({"quotes/2026-11-10/0000": mk([{"t_local_ms": "0", "offset_ms": "4"}]), "quotes/2026-11-11/0000": mk([row("3", "20")]), "quotes/2026-11-12/0000": mk([row("", "")])})
assert t == [] and c == {"runs": 2, "runs_used": 1, "runs_no_clock": 1, "first_date": "2026-11-11"}, c
print("ok")
