"""AUTO: registered forward reads that run themselves. Research only; adds no hypothesis and changes no registration.
Usage: python -m scalper.autoscore check   (one pass: refresh public data when due, check each read's readiness WITHOUT scoring,
                                            run a ready read's registered scorer once, log to workers/AUTO_LOG.md)

Each read is run by its OWN registered command, as a subprocess, exactly once: a read counts as done when its result file exists.
Readiness is a count only (closes, losses in a block, windows); nothing here computes a PF, a net or a mean before a read is due.
  LOCK2      ready at 25 closes per asset (`scalper.lock2 count`), runs `scalper.lock2 run` (writes data/lock2_result.txt)
  MKTTIME1-F ready at 15 losses in gold's 20-24 CT block (`scalper.mkttime1f count`), runs `scalper.mkttime1f read`
  MM1        ready at 300 recorded gold 15 minute windows on origin/quote-data; no scorer exists, so it logs "MM1 ready, scorer needed" once
  RECORD1    the daily scheduled task reads it; this only logs the count line of `scalper.record1 look`, once a day
  CONF2 C    ready at 30 kept window C closes (from 2026-10-27), runs `scalper.conf2 holdout` (output saved to data/conf2_C_result.txt),
             and only if data/conf2_A_done exists (the lead writes it after reading window A)
AUTO_LOG.md gets a line for every read that runs, for MM1 becoming ready, and one status line a day (the first check after midnight Central).
Hourly counts go to stdout (the loop's log, data/autoscore_loop.log).
Data refresh, at most every 6 hours, one Kalshi stream at a time: `scalper.fresh_update` (data/fresh.sqlite) and
`scalper.conf2 fetch 1793059200 <now>` (data/conf2_lad.sqlite; skipped while another conf2 fetch is running on the same file).
"""
from __future__ import annotations

import ast
import csv
import gzip
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .paths import DATA_DIR

CT = ZoneInfo("America/Chicago")
ROOT = DATA_DIR.parent                       # kalshi-scalper/
LOG = ROOT / "workers" / "AUTO_LOG.md"
STATE = DATA_DIR / "autoscore_state.json"
MM1_CACHE = DATA_DIR / "autoscore_mm1_cache.json"
REFRESH_S = 6 * 3600
CONF2_C_START, CONF2_MIN_KEPT = 1793059200, 30
MM1_NEEDED, LOCK2_NEEDED = 300, 25
RESULTS = {"LOCK2": DATA_DIR / "lock2_result.txt", "MKTTIME1-F": DATA_DIR / "mkttime1f_result.txt",
           "CONF2C": DATA_DIR / "conf2_C_result.txt", "RECORD1": DATA_DIR / "record1_result.txt"}
CONF2_A_DONE = DATA_DIR / "conf2_A_done"


def now_ct() -> str:
    return datetime.now(CT).strftime("%Y-%m-%d %H:%M CT")


def state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def save(s: dict) -> None:
    STATE.write_text(json.dumps(s, indent=1))


def log(rid: str, line: str) -> None:
    if not LOG.exists():
        LOG.write_text("# AUTO_LOG: forward reads run by `scalper.autoscore` (newest last; time in US Central)\n\n")
    with LOG.open("a") as f:
        f.write(f"- {now_ct()} | {rid} | {line}\n")


def py(*args: str, timeout: int = 7200) -> tuple[int, str]:
    env = dict(os.environ, PYTHONPATH="src")
    try:
        p = subprocess.run([sys.executable, "-m", *args], cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + ("\n" + p.stderr.strip().splitlines()[-1] if p.returncode and p.stderr.strip() else "")).strip()
    except subprocess.TimeoutExpired:
        return 124, "timed out"


def last_line(text: str, needle: str = "") -> str:
    ls = [l for l in text.splitlines() if l.strip() and (needle in l)]
    return ls[-1].strip() if ls else (text.strip().splitlines() or [""])[-1]


def refresh(s: dict) -> list[str]:
    out = []
    if time.time() - s.get("fresh_at", 0) >= REFRESH_S:
        rc, o = py("scalper.fresh_update")
        out.append(f"fresh_update rc={rc}: {last_line(o, 'done')[:160]}")
        if rc == 0:
            s["fresh_at"] = time.time()
    if time.time() - s.get("conf2_at", 0) >= REFRESH_S:
        busy = subprocess.run(["pgrep", "-f", "scalper.conf2 fetch"], capture_output=True, text=True).stdout.strip()
        if busy:
            out.append("conf2 fetch skipped: another conf2 fetch is writing data/conf2_lad.sqlite")
        else:
            rc, o = py("scalper.conf2", "fetch", str(CONF2_C_START), str(int(time.time())))
            out.append(f"conf2 fetch C rc={rc}: {last_line(o, 'done')[:160]}")
            if rc == 0:
                s["conf2_at"] = time.time()
    save(s)
    return out


# ---- readiness counts (no scoring) ----

def lock2_count() -> tuple[bool, str]:
    rc, o = py("scalper.lock2", "count", timeout=1800)
    line = last_line(o, "LOCK2")
    try:
        per = ast.literal_eval(line.split(":", 1)[1].split("(")[0].strip())   # the dict lock2 prints
        ready = all(per.get(a, 0) >= LOCK2_NEEDED for a in ("BTC", "ETH"))
    except Exception:
        ready = False
    return ready, line


def mkttime_count() -> tuple[bool, str]:
    from .mkttime1f import LOSSES_NEEDED, count
    n, line = count(quiet=True)
    return n >= LOSSES_NEEDED, line


def _git(*a: str) -> bytes:
    return subprocess.run(["git", *a], capture_output=True, check=True, cwd=ROOT).stdout


def mm1_count() -> tuple[bool, str]:
    """Distinct KXGOLD15M windows (tickers) in the recorder's quotes files. Files are cached by blob hash."""
    _git("fetch", "-q", "origin", "quote-data")
    try:
        cache = json.loads(MM1_CACHE.read_text())
    except Exception:
        cache = {}
    tickers = set()
    for ln in _git("ls-tree", "-r", "--full-tree", "origin/quote-data").decode().splitlines():
        meta, path = ln.split("\t", 1)
        if not (path.startswith("quotes/") and path.endswith("/quotes.csv.gz")):
            continue
        blob = meta.split()[2]
        if blob not in cache:
            raw = gzip.decompress(_git("cat-file", "blob", blob)).decode()
            cache[blob] = sorted({r["ticker"] for r in csv.DictReader(io.StringIO(raw)) if r.get("ticker", "").startswith("KXGOLD15M-")})
        tickers.update(cache[blob])
    MM1_CACHE.write_text(json.dumps(cache))
    return len(tickers) >= MM1_NEEDED, f"MM1 readiness: {len(tickers)} recorded gold 15 minute windows ({MM1_NEEDED} needed)"


def conf2_count() -> tuple[bool, str]:
    from . import conf2
    L, _ = conf2.ladder_at()
    kept, und, n = set(), 0, 0
    for e in conf2.entries():
        if e["close"] < CONF2_C_START:
            continue
        n += 1
        lad = L.get(e["close"])
        if not lad:
            und += 1
            continue
        k, b, a = min(lad, key=lambda x: abs(x[0] - e["strike"]))
        if (a if e["side"] == "yes" else 1 - b) >= 0.88:
            kept.add(e["close"])
    gate = "" if CONF2_A_DONE.exists() else "; waiting for data/conf2_A_done (the lead reads window A first)"
    return len(kept) >= CONF2_MIN_KEPT, f"CONF2 C readiness: {n} window C entries, {len(kept)} kept closes ({CONF2_MIN_KEPT} needed), {und} without ladder{gate}"


def record1_look() -> str:
    """The count line only (runs, coverage, qualifying trades and dates); the look's means and z are left out of the log on purpose."""
    rc, o = py("scalper.record1", "look", timeout=3600)
    if rc != 0:
        return f"record1 look failed rc={rc}: {last_line(o)[:200]}"
    head = last_line(o, "runs")
    try:
        j = ast.literal_eval(next(l for l in o.splitlines() if l.startswith("{")))
        head += f"; qualifying trades {j.get('n')} on {j.get('dates')} dates (read needs 300 on 10)"
    except Exception:
        pass
    return head[:400]


# ---- one pass ----

def check() -> None:
    s = state()
    print(f"== autoscore check {now_ct()}", flush=True)
    for l in refresh(s):
        print("  " + l, flush=True)
    status = []

    def guarded(name, fn):
        try:
            return fn()
        except Exception as ex:   # one read's failure never stops the others
            return False, f"{name} readiness failed: {type(ex).__name__}: {str(ex)[:160]}"

    # LOCK2
    if RESULTS["LOCK2"].exists():
        status.append("LOCK2 done")
    else:
        ready, line = guarded("LOCK2", lock2_count); status.append(line)
        if ready:
            rc, o = py("scalper.lock2", "run")
            log("LOCK2", last_line(RESULTS["LOCK2"].read_text(), "VERDICT") if RESULTS["LOCK2"].exists() else f"run rc={rc}: {last_line(o)[:200]}")
    # MKTTIME1-F
    if RESULTS["MKTTIME1-F"].exists():
        status.append("MKTTIME1-F done")
    else:
        ready, line = guarded("MKTTIME1-F", mkttime_count); status.append(line)
        if ready:
            rc, o = py("scalper.mkttime1f", "read")
            log("MKTTIME1-F", last_line(RESULTS["MKTTIME1-F"].read_text(), "VERDICT") if RESULTS["MKTTIME1-F"].exists() else f"read rc={rc}: {last_line(o)[:200]}")
    # MM1
    ready, line = guarded("MM1", mm1_count); status.append(line)
    if ready and not s.get("mm1_logged"):
        log("MM1", "MM1 ready, scorer needed (" + line + ")"); s["mm1_logged"] = True
    # CONF2 window C
    if RESULTS["CONF2C"].exists():
        status.append("CONF2 C done")
    else:
        ready, line = guarded("CONF2C", conf2_count); status.append(line)
        if ready and CONF2_A_DONE.exists():
            rc, o = py("scalper.conf2", "holdout")
            if rc == 0:
                RESULTS["CONF2C"].write_text(f"# conf2 holdout, run once by scalper.autoscore at {now_ct()}\n{o}\n")
            log("CONF2C", (last_line(o, "C forward holdout") if rc == 0 else f"holdout rc={rc}: {last_line(o)[:200]}")[:400])
    # RECORD1: count line once a day only
    today = datetime.now(CT).strftime("%Y-%m-%d")
    if s.get("daily") != today:
        r1 = "RECORD1 registered read done" if RESULTS["RECORD1"].exists() else record1_look()
        status.append(r1)
        log("RECORD1", r1)
        log("STATUS", " ; ".join(x for x in status if not x.startswith("RECORD1"))[:900])
        s["daily"] = today
    save(s)
    for l in status:
        print("  " + l, flush=True)


if __name__ == "__main__":
    {"check": check}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
