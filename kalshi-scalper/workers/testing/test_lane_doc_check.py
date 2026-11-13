"""Test for lane_doc_check.py on INVENTED text. Run: python3 -B -W ignore test_lane_doc_check.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lane_doc_check as d
full = "\n".join("**%s**   (x)\n`%s`" % ("pad", ph) for _, ph in d.PHRASES)          # markdown marks and extra whitespace are normalised away
assert all(ok for _, _, ok in d.check_text(full))
missing = "\n".join(ph for name, ph in d.PHRASES if name != "bar")
res = {name: ok for name, _, ok in d.check_text(missing)}
assert res["bar"] is False and sum(1 for v in res.values() if not v) == 1
assert d.norm("a  **b**\n`c`") == "a b c"
# a one-character change in a rule is caught: 1.3 -> 1.4, 60 -> 61
changed = full.replace("1.3 or better on the block", "1.4 or better on the block").replace("A block is 60 fillable", "A block is 61 fillable")
bad = {name for name, _, ok in d.check_text(changed) if not ok}
assert bad == {"bar", "block size and days"}, bad
# the record builder runs on the real repo ref without tests and reports the doc hash line
rec, ok = d.build_record("origin/main", tests=False)
assert "sha256 of the doc:" in rec and "## File hashes tested" in rec and isinstance(ok, bool)
print("test_lane_doc_check: all checks passed")
