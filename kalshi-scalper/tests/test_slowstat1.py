"""Plain assert tests for src/scalper/slowstat1.py; run with: python tests/test_slowstat1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import slowstat1 as S

assert S.cap([("a", 5), ("a", 30), ("b", 20), ("c", 19.9)]) == {"markets": 2, "events": 2}
assert S.cap([]) == {"markets": 0, "events": 0}
assert S.verdict(149) == "NOT_RUNNABLE" and S.verdict(150) == "RUNNABLE"
print("ok")
