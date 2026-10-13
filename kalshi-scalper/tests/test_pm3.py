"""Plain assert tests for PM3 (src/scalper/pm3.py); run with: python tests/test_pm3.py. Each states a consequence, not a mechanism."""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import fwd1
from scalper import pm1
from scalper import pm2
from scalper import pm3 as P
from scalper import vol1

# Registered: the forward Kalshi data as the source, its own Polymarket file, FWD1's start and read date, PM2's flag, VOL1's bar with 100 as the minimum.
assert P.SRC_DB.name == "fwd1.sqlite" and P.PM3_DB.name == "pm3.sqlite" and P.PM3_DB != pm2.PM2_DB != pm1.PM_DB and P.START_TS == fwd1.START_TS and P.EARLIEST_READ_TS == fwd1.EARLIEST_READ_TS
assert P.MIN_SKIPPED == 100 and pm2.DISAGREE == 0.05
# Only windows on or after the start count, whatever the source holds.
orig = pm1.windows
pm1.windows = lambda src: [{"close_ts": P.START_TS - 1}, {"close_ts": P.START_TS}, {"close_ts": P.START_TS + 900}]
try:
    assert [w["close_ts"] for w in P.windows()] == [P.START_TS, P.START_TS + 900]
finally:
    pm1.windows = orig
# fetch() sends the forward windows to PM3's own file, never PM1's or PM2's.
calls = []
o1, o2 = pm1.fetch_windows, pm1.windows
pm1.fetch_windows = lambda db, wins: calls.append((db, wins))
pm1.windows = lambda src: [{"close_ts": P.START_TS + 5}]
try:
    P.fetch()
finally:
    pm1.fetch_windows, pm1.windows = o1, o2
assert calls == [(P.PM3_DB, [{"close_ts": P.START_TS + 5}])]
# The single read is refused before the registered date.
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    P.run(now_ts=P.EARLIEST_READ_TS - 1)
assert "Too early" in buf.getvalue()
# The bar is VOL1's with the lower minimum: 120 skipped entries is enough here and not for VOL1's 150.
def rows(n_days, per_day, skip_net, kept_net, skip_share=0.3):
    return [{"series": "KXBTC15M" if i % 2 else "KXETH15M", "close_ts": d, "day": f"2026-11-{d + 1:02d}", "net": (skip_net(d) if i < int(per_day * skip_share) else kept_net(d)), "skip": i < int(per_day * skip_share)}
            for d in range(n_days) for i in range(per_day)]
r = rows(20, 20, lambda d: -0.2 if d % 2 else -0.05, lambda d: 0.03)
assert sum(1 for e in r if e["skip"]) == 120
assert vol1.verdict(r, [0.0] * 20, min_skipped=P.MIN_SKIPPED)[0] == "NOT_YET_FALSIFIED" and vol1.verdict(r, [0.0] * 20)[0] == "NOT_ENOUGH_DATA"
assert vol1.verdict(rows(20, 10, lambda d: -0.2, lambda d: 0.03), [0.0] * 20, min_skipped=P.MIN_SKIPPED)[0] == "NOT_ENOUGH_DATA"
code = "\n".join(l.split("#")[0] for l in Path(P.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("PM3 passed")
