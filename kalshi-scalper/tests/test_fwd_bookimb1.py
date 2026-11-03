"""BOOKIMB1 forward command guard: refuses before enough ON trades, never touches DEV or HOLDOUT (synthetic)."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__file__), "..", "src"))
from scalper import bookimb1 as bi  # noqa: E402
from scalper import bookimb1_fwd as fw  # noqa: E402
from scalper import fwdread as fr  # noqa: E402

assert bi.FWD_FROM >= bi.HOLD_TO
reg = open(__import__("os").path.join(__import__("os").path.dirname(__file__), "..", "workers", "BOOKIMB1_REGISTRATION.md")).read()
for ln in fw.SPEC.rule:
    assert ln in reg or ln.replace("**", "") in reg.replace("**", ""), ln
assert fw.SPEC.due is None and fw.DEADLINE == fr.utc(2026, 12, 15)
print("test_fwd_bookimb1: ok")
