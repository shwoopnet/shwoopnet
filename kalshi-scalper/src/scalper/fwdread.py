"""Shared guard rails for the forward-read commands (FWDTOOLS, 2026-11-03). Infrastructure only: nothing here scores anything or defines a rule.

Every forward command (makertail1_fwd, bookch1_fwd, usweep1_fwd, nowcast1_fwd, count1_fwd, count2_fwd, barrier1_fwd) goes through `run`, which

  1. prints the registered decision rule (verbatim lines copied from the registration) and the exact window it will read;
  2. refuses before the due date; `--force-info` prints information only (counts that need no outcome) and writes nothing;
  3. refuses a second real read: the durable record is a line `FWD-READ <ID> ...` in README.md (data/ is git-ignored and may be lost with the
     container), plus a started marker data/fwd_<ID>_read.txt written BEFORE the read, so a crashed read is also spent (runbook rule 1);
     the command PRINTS the README line to append and never appends it;
  4. applies only the registered rule, through the function the module passes in.

Flags: --force-info, --owner-asked (favourite-and-hold items only), --readme PATH and --marker-dir DIR (tests). There is deliberately no flag to
override the date, the second-read refusal or a blocker. Exit code 0 = ran (or printed information), 2 = refused.
"""
from __future__ import annotations

import math
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from .paths import DATA_DIR

ROOT = DATA_DIR.parent
README = ROOT / "README.md"
REPO = ROOT.parent
UTC = timezone.utc
MARK = "FWD-READ"


def utc(y, mo, d, h=0, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=UTC)


@dataclass
class Spec:
    id: str
    title: str
    rule: list           # verbatim lines from the registration (a test checks every one is a substring of the registration file)
    window: list         # plain description of the exact data the read touches
    due: Optional[datetime] = None
    due_note: str = ""
    owner_ruling: str = ""      # non-empty: print OWNER RULING NEEDED and refuse unless --owner-asked
    blocker: str = ""           # non-empty: a permanent refusal until a new registration exists (printed, quoted)
    sources: list = field(default_factory=list)   # registration files that hold the rule


def flags(argv):
    out = {"force_info": False, "owner_asked": False, "readme": README, "marker_dir": DATA_DIR, "rest": []}
    it = iter(argv)
    for a in it:
        if a == "--force-info":
            out["force_info"] = True
        elif a == "--owner-asked":
            out["owner_asked"] = True
        elif a == "--readme":
            out["readme"] = next(it)
        elif a == "--marker-dir":
            out["marker_dir"] = next(it)
        else:
            out["rest"].append(a)
    return out


def marker_path(spec, marker_dir):
    from pathlib import Path
    return Path(marker_dir) / f"fwd_{spec.id}_read.txt"


def already_read(spec, readme, marker_dir):
    """A reason string when a real read of this id is already logged (README line) or started (marker file), else None."""
    from pathlib import Path
    p = Path(readme)
    if p.exists():
        pat = re.compile(r"^\s*" + re.escape(MARK) + r"\s+" + re.escape(spec.id) + r"\b")
        for ln in p.read_text(errors="replace").splitlines():
            if pat.match(ln):
                return f"README already holds a read line: {ln[:120]}"
    m = marker_path(spec, marker_dir)
    if m.exists():
        return f"started marker {m} exists (a crashed read is spent; the coordinator decides)"
    return None


def readme_line(spec, now, body):
    return f"{MARK} {spec.id} {now.strftime('%Y-%m-%d')}: {body}"


def run(spec, argv, real, info, now=None, ready=None, out=print):
    """real() -> (lines, readme_body); info() -> lines (no outcome read, nothing written); ready(now) -> refusal text or None."""
    f = flags(argv)
    now = now or datetime.now(UTC)
    out(f"{spec.id}: {spec.title}")
    out("REGISTERED DECISION RULE (verbatim from " + ", ".join(spec.sources) + "):")
    for ln in spec.rule:
        out("  " + ln)
    out("EXACT WINDOW READ:")
    for ln in spec.window:
        out("  " + ln)
    out("DUE: " + (spec.due.strftime("%Y-%m-%d %H:%M UTC") if spec.due else "no calendar date") + (f" ({spec.due_note})" if spec.due_note else ""))
    if spec.owner_ruling:
        out("OWNER RULING NEEDED: " + spec.owner_ruling)
        if not f["owner_asked"]:
            out("REFUSED: run with --owner-asked only after the owner has ruled in writing. Nothing was read.")
            return 2
    if spec.blocker:
        out("REFUSED (blocker): " + spec.blocker)
        out("Nothing was read and nothing was written.")
        return 2
    if f["force_info"]:
        out("INFORMATION ONLY (--force-info): no outcome is scored, nothing is written, this is not a read.")
        for ln in info():
            out("  " + ln)
        return 0
    why = already_read(spec, f["readme"], f["marker_dir"])
    if why:
        out("REFUSED: a registered read is spent once it runs. " + why)
        return 2
    if spec.due is not None and now < spec.due:
        out(f"REFUSED: not due until {spec.due.strftime('%Y-%m-%d %H:%M UTC')} (now {now.strftime('%Y-%m-%d %H:%M UTC')}). Use --force-info for information only.")
        return 2
    if ready is not None:
        r = ready(now)
        if r:
            out("REFUSED: " + r)
            return 2
    from pathlib import Path
    mp = marker_path(spec, f["marker_dir"])
    Path(mp).parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(f"started {now.isoformat()}\n")        # before the read: a crash still spends it
    lines, body = real()
    for ln in lines:
        out(ln)
    out("APPEND THIS EXACT LINE TO kalshi-scalper/README.md (not appended automatically; data/ is git-ignored):")
    out(readme_line(spec, now, body))
    return 0


# ---------------------------------------------------------------- small shared statistics (no rule here)

def pf(v):
    w = sum(x for x in v if x > 0)
    l = -sum(x for x in v if x < 0)
    return w / l if l > 0 else (float("inf") if w > 0 else 0.0)


def fpf(x):
    return "inf" if x == float("inf") else f"{x:.2f}"


def clustered(obs):
    """(mean, z) for [(cluster key, value)], standard error clustered by the key (calibration.cluster_mean_z)."""
    from .calibration import cluster_mean_z
    m, _se, z = cluster_mean_z(obs)
    return m, z


def day_of(ts):
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%d")


def checkout_quote_data(prefixes, dest):
    """Materialise paths of origin/quote-data (daily/, wxens/, ref/, book/) into dest with git archive; returns dest. Public data, read only."""
    subprocess.run(["git", "-C", str(REPO), "fetch", "-q", "origin", "quote-data"], capture_output=True)
    p = subprocess.Popen(["git", "-C", str(REPO), "archive", "origin/quote-data", *prefixes], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", str(dest)], stdin=p.stdout, check=True)
    p.wait()
    return dest


def cli(spec_fn):
    """Module main: `python -m scalper.<name> forward [flags]`; anything else prints the module docstring."""
    def main(argv):
        if len(argv) > 1 and argv[1] in ("forward", "read"):
            return spec_fn(argv[2:])
        mod = sys.modules.get(spec_fn.__module__)
        print((mod.__doc__ if mod else "") or "usage: forward [--force-info]")
        return 0
    return main
