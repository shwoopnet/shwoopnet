"""Helpers shared by the test_fwd_*.py files (synthetic data only; no recorder data, no outcome of any real market)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import fwdread as fr  # noqa: E402


def registration_text(spec):
    return "\n".join((fr.ROOT / s).read_text() for s in spec.sources)


def assert_rule_verbatim(spec):
    text = registration_text(spec)
    for ln in spec.rule:
        assert ln in text, "rule line is not verbatim in the registration: " + ln[:80]


def args(tmp_path, *extra):
    """Flags that keep README and markers in the test's own folder."""
    return ["--readme", str(tmp_path / "README.md"), "--marker-dir", str(tmp_path), *extra]


def marker(tmp_path, spec):
    return fr.marker_path(spec, tmp_path)
