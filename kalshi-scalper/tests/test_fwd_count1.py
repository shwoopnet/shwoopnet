"""COUNT1 forward command: blocked until a new registration; never reads."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from _fwdutil import args, assert_rule_verbatim, marker  # noqa: E402

from scalper import count1_fwd as fw  # noqa: E402
from scalper import fwdread as fr  # noqa: E402


def test_rule_is_verbatim():
    assert_rule_verbatim(fw.SPEC)


def test_refuses_always_and_quotes_the_blocker(tmp_path, capsys):
    for extra in ((), ("--force-info",)):
        assert fw.forward(args(tmp_path, *extra), now=fr.utc(2030, 1, 1)) == 2      # no date lifts it
        out = capsys.readouterr().out
        assert "SOURCE_MISMATCH 65.4% (17 of 26)" in out and "new registration" in out and "Nothing was read" in out
    assert not marker(tmp_path, fw.SPEC).exists()


def test_blocker_quote_is_in_the_result_file():
    text = (fr.ROOT / "workers/COUNT1_RESULT.md").read_text()
    assert "Before any forward read the source gap must be fixed" in text and "65.4%" in text
