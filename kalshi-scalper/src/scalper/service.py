"""Run the recorder in the background on a Mac, start it at login, restart it
if it dies, and keep the machine from idle-sleeping while it runs.

Usage (from the kalshi-scalper/src folder), JOB is "recorder" (default) or "bot":
    python3 -m scalper.service install [JOB]
    python3 -m scalper.service status [JOB]
    python3 -m scalper.service uninstall [JOB]
    python3 -m scalper.service install bot --dry-run     # print the config, change nothing

It only reads Kalshi's public prices. It needs no account, key or password and
writes nothing outside this project's data/ folder and its own log files.
"""
from __future__ import annotations

import os
import plistlib
import subprocess
import sys
from pathlib import Path

# One installer, two jobs. The bot is paper only and starts with $100.
JOBS = {
    "recorder": ("com.shwoop.kalshi-recorder", ["scalper.recorder", "2"]),
    "bot": ("com.shwoop.kalshi-bot", ["scalper.bot", "--bankroll", "100"]),
}
LABEL = JOBS["recorder"][0]


def plist_path(target: str = "recorder") -> Path:
    return Path.home() / "Library" / "LaunchAgents" / (JOBS[target][0] + ".plist")


PLIST = plist_path("recorder")
SRC = Path(__file__).resolve().parents[1]
DATA = SRC.parent / "data"


def build_plist(target: str = "recorder") -> dict:
    label, args = JOBS[target]
    return {
        "Label": label,
        # -i stops idle sleep; -s stops system sleep while on AC power. Neither
        # stops a closed lid (without an external display) or a manual sleep;
        # status.py reports those as gaps.
        "ProgramArguments": ["/usr/bin/caffeinate", "-i", "-s", sys.executable, "-m", *args],
        "WorkingDirectory": str(SRC),
        "EnvironmentVariables": {"PYTHONPATH": str(SRC)},
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 10,
        "StandardOutPath": str(DATA / f"{target}.log"),
        "StandardErrorPath": str(DATA / f"{target}.err.log"),
    }


def _launchctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["launchctl", *args], capture_output=True, text=True)


def main() -> None:
    words = [a for a in sys.argv[1:] if not a.startswith("--")]
    cmd = words[0] if words else ""
    target = words[1] if len(words) > 1 else "recorder"
    if target not in JOBS:
        sys.exit(f"unknown job {target!r}: choose one of {', '.join(JOBS)}")
    label, plist = JOBS[target][0], plist_path(target)
    dry = "--dry-run" in sys.argv
    domain = f"gui/{os.getuid()}"
    if cmd == "install":
        pl = build_plist(target)
        if dry:
            print(plistlib.dumps(pl).decode())
            return
        if sys.platform != "darwin":
            sys.exit("This installer is for macOS. On other systems run: python3 -m scalper.recorder 2")
        DATA.mkdir(exist_ok=True)
        plist.parent.mkdir(parents=True, exist_ok=True)
        plist.write_bytes(plistlib.dumps(pl))
        _launchctl("bootout", f"{domain}/{label}")  # replace any older copy
        r = _launchctl("bootstrap", domain, str(plist))
        print("installed and started" if r.returncode == 0 else f"failed: {r.stderr.strip()}")
    elif cmd == "uninstall":
        _launchctl("bootout", f"{domain}/{label}")
        plist.unlink(missing_ok=True)
        print("stopped and removed (saved data in data/ is kept)")
    elif cmd == "status":
        r = _launchctl("print", f"{domain}/{label}")
        print("running" if r.returncode == 0 and "state = running" in r.stdout else "not running")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
