"""Plain assert tests for src/scalper/slowstat1.py; run with: python tests/test_slowstat1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import slowstat1 as S

rows = [(f"e{i}", f"2026-01-{i + 1:02d}T00:00:00Z", 30.0) for i in range(12)] + [("e11", "2026-01-12T00:00:00Z", 5.0)]
assert S.cap(rows) == {"events": 12, "scored_events": 4, "scored_markets": 4}      # last third = e8..e11, the thin market is dropped
assert S.cap(rows[:11])["scored_markets"] == 0                                    # 11 events: no sd, not scored
assert S.cap([]) == {"events": 0, "scored_events": 0, "scored_markets": 0}
assert S.verdict(149) == "NOT_RUNNABLE" and S.verdict(150) == "RUNNABLE"
print("ok")
