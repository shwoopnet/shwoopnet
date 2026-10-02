"""Run the recorder in the background on a Mac, start it at login, restart it
if it dies, and keep the machine from idle-sleeping while it runs.

Usage (from the kalshi-scalper/src folder):
    python3 -m scalper.service install
    python3 -m scalper.service status
    python3 -m scalper.service uninstall
    python3 -m scalper.service install --dry-run     # print the config, change nothing

It only reads Kalshi's public prices. It needs no account, key or password and
writes nothing outside this project's data/ folder and its own log files.
"""
from __future__ import annotations

import os
import plistlib
import subprocess
import sys
from pathlib import Path

LABEL = "com.shwoop.kalshi-recorder"
PLIST = Path.home() / "Library" / "LaunchAgents" / (LABEL + ".plist")
SRC = Path(__file__).resolve().parents[1]
DATA = SRC.parent / "data"


def build_plist() -> dict:
    return {
        "Label": LABEL,
        # caffeinate -i stops IDLE sleep while the recorder runs. It cannot stop
        # a closed lid or a manual sleep; status.py reports those as gaps.
        "ProgramArguments": ["/usr/bin/caffeinate", "-i", sys.executable, "-m", "scalper.recorder", "2"],
        "WorkingDirectory": str(SRC),
        "EnvironmentVariables": {"PYTHONPATH": str(SRC)},
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 10,
        "StandardOutPath": str(DATA / "recorder.log"),
        "StandardErrorPath": str(DATA / "recorder.err.log"),
    }


def _launchctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["launchctl", *args], capture_output=True, text=True)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    dry = "--dry-run" in sys.argv
    domain = f"gui/{os.getuid()}"
    if cmd == "install":
        pl = build_plist()
        if dry:
            print(plistlib.dumps(pl).decode())
            return
        if sys.platform != "darwin":
            sys.exit("This installer is for macOS. On other systems run: python3 -m scalper.recorder 2")
        DATA.mkdir(exist_ok=True)
        PLIST.parent.mkdir(parents=True, exist_ok=True)
        PLIST.write_bytes(plistlib.dumps(pl))
        _launchctl("bootout", f"{domain}/{LABEL}")  # replace any older copy
        r = _launchctl("bootstrap", domain, str(PLIST))
        print("installed and started" if r.returncode == 0 else f"failed: {r.stderr.strip()}")
    elif cmd == "uninstall":
        _launchctl("bootout", f"{domain}/{LABEL}")
        PLIST.unlink(missing_ok=True)
        print("stopped and removed (saved data in data/ is kept)")
    elif cmd == "status":
        r = _launchctl("print", f"{domain}/{LABEL}")
        print("running" if r.returncode == 0 and "state = running" in r.stdout else "not running")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
