"""COUNT1 forward command: BLOCKED until a new registration exists. Research only.

    python -m scalper.count1_fwd forward        (prints the blocker and refuses; --force-info changes nothing)

COUNT1 (Truth Social post-count brackets against CNN's archive) ended NOT_ENOUGH_DATA with SOURCE_MISMATCH: only 17 of 26 periods (65.4%) had the archive total inside
the winning bracket, under the registered 70%. workers/COUNT1_RESULT.md: "Before any forward read the source gap must be fixed (count Roll Call's rule more closely ...)
which would be a new registration." Until that registration is pushed there is nothing to read, so this command reads nothing and writes nothing. When the new
registration exists, replace SPEC.blocker and implement the read here; do not run count1.py against a forward period meanwhile.
"""
from __future__ import annotations

import sys

from . import fwdread as fr

SPEC = fr.Spec(
    id="COUNT1F",
    title="forward read of the Truth Social post-count brackets (KXTRUTHSOCIALD daily from 2026-11-04, KXTRUTHSOCIAL weekly from the week of 2026-11-08)",
    sources=["workers/COUNT1_REGISTRATION.md", "workers/COUNT1_RESULT.md"],
    rule=[
        "a trade needs fill ask in [0.03, 0.30] (hard limit 0.30). Signal: p_model >= 3 x fill ask.",
        "If under 70%, tag SOURCE_MISMATCH and the verdict is NOT_ENOUGH_DATA whatever the P&L.",
    ],
    window=["none: no forward read is permitted until the source gap has a new registration"],
    blocker=("SOURCE_MISMATCH 65.4% (17 of 26) is under the registered 70%. COUNT1_RESULT.md: \"Before any forward read the source gap must be fixed (count Roll Call's rule more "
             "closely, e.g. test whether replies explain the 35% mismatch) which would be a new registration.\" Register that first, then build the read."),
)


def forward(argv, now=None):
    return fr.run(SPEC, argv, lambda: ([], ""), lambda: [], now=now)


main = fr.cli(forward)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
