"""RECFEED (FWD-AUDIT, 2026-10-30): one status line on the GitHub Actions recorders the dated forward reads depend on, so a
dropped schedule can never look like a slow rule. Research only: it reads commit times on the data branches, never a row.

    PYTHONPATH=src python -m scalper.recfeed        (prints the line; `scalper.autoscore check` appends it to every pass's status)

Why: the readiness lines (MM1, QUOTE2B, R6T, GF12) print counts, and a count that has stopped growing looks the same as one that
is growing slowly unless someone compares two passes. On 2026-10-30 R6 (record-15m-book, a 30 minute cron) recorded nothing from
08:02 to 12:43 UTC because GitHub fired no scheduled run; the counts said nothing. This line says how old each recorder's last push
is and marks STALE when that age is past what the schedule allows. Every error is caught: the line then says so.
"""
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .paths import DATA_DIR

CT = ZoneInfo("America/Chicago")
ROOT = DATA_DIR.parent
# name, remote ref, folder, hours allowed since the last push, end of the recorder (UTC) or None.
# quotes and book: 4 hour jobs that start late (gaps of 5.5 h seen); book15r6: 30 minute cron, 4 hour jobs (a 4.7 h gap seen);
# perps: an hourly cron that GitHub fires about 5 times a day (gaps of 7 h seen). Past its end a recorder is "ended", not stale.
RECORDERS = (
    ("quotes (MM1, RECORD1)", "origin/quote-data", "quotes", 8.0, None),
    ("book (QUOTE2B)", "origin/quote-data", "book", 8.0, None),
    ("book15r6 (R6: MAKER5, L1Q1, GF1, GF2)", "origin/quote-data", "book15r6", 8.0, "2026-11-13T23:59:00Z"),
    ("perps", "origin/perp-data", "perps", 12.0, None),
)


def _git(*a: str) -> bytes:
    return subprocess.run(["git", *a], capture_output=True, check=True, cwd=ROOT, timeout=300).stdout


def fetch() -> str:
    """Refresh the two data branches; a failed fetch is reported, and the local refs are read as they are."""
    try:
        _git("fetch", "-q", "origin", "quote-data", "perp-data")
        return ""
    except Exception as ex:
        return f"fetch failed ({type(ex).__name__}), ages are from the last fetch"


def last_push(ref: str, folder: str) -> int | None:
    """Unix time of the newest commit on `ref` that touched `folder`, or None when there is none."""
    out = _git("log", "-1", "--format=%ct", ref, "--", folder).decode().strip()
    return int(out) if out else None


def pushes() -> dict[str, int | None]:
    return {name: last_push(ref, folder) for name, ref, folder, _, _ in RECORDERS}


def describe(now: float, push: dict[str, int | None]) -> tuple[str, list[str]]:
    """The line's body and the names that are STALE. Pure: no git, no clock."""
    parts, stale = [], []
    for name, _, _, allow_h, end in RECORDERS:
        ts = push.get(name)
        end_ts = datetime.fromisoformat(end.replace("Z", "+00:00")).timestamp() if end else None
        if ts is None:
            parts.append(f"{name} never pushed")
            stale.append(name)
            continue
        age_h = (now - ts) / 3600
        when = datetime.fromtimestamp(ts, CT).strftime("%Y-%m-%d %H:%M CT")
        if end_ts is not None and now >= end_ts:
            parts.append(f"{name} last push {when}, ended {end[:10]}")
            continue
        parts.append(f"{name} last push {when} ({age_h:.1f} h)")
        if age_h > allow_h:
            stale.append(name)
    body = "; ".join(parts)
    if stale:
        body += "; STALE: " + ", ".join(stale) + " (no push within the allowed hours: is the GitHub Actions schedule firing?)"
    return body, stale


def status_line(now: float | None = None, push: dict[str, int | None] | None = None, do_fetch: bool = True) -> str:
    try:
        note = fetch() if (do_fetch and push is None) else ""
        body, _ = describe(time.time() if now is None else now, pushes() if push is None else push)
        return "RECORDERS: " + body + (f" [{note}]" if note else "")
    except Exception as ex:          # the status line must never stop a pass
        return f"RECORDERS: status failed: {type(ex).__name__}: {str(ex)[:120]}"


if __name__ == "__main__":
    print(status_line(do_fetch="--no-fetch" not in sys.argv[1:]))
