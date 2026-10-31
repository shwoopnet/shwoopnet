"""AUTO: registered forward reads that run themselves. Research only; adds no hypothesis and changes no registration.
Usage: python -m scalper.autoscore check   (one pass: refresh public data when due, check each read's readiness WITHOUT scoring,
                                            run a ready read's registered scorer once, log to workers/AUTO_LOG.md)

Each read is run by its OWN registered command, as a subprocess, exactly once: a read counts as done when its result file exists.
Readiness is a count only (closes, losses in a block, windows); nothing here computes a PF, a net or a mean before a read is due.
  LOCK2      ready at 25 closes per asset (`scalper.lock2 count`), runs `scalper.lock2 run` (writes data/lock2_result.txt)
  MKTTIME1-F ready at 15 losses in gold's 20-24 CT block (`scalper.mkttime1f count`), runs `scalper.mkttime1f read`
  MM1        ready at 300 recorded gold 15 minute windows on origin/quote-data; runs `scalper.mm1 run` (refuses below 300 usable windows; writes data/mm1_result.txt)
  QUOTE2B    from 2026-11-12, runs `scalper.quote2b run` (refuses below 300 usable closes; writes data/quote2b_result.txt)
  MAKER5     from 2026-11-06, runs `scalper.r6tests run maker5` (refuses below 300 usable R6 windows or, Amendment 1, below 300 posted windows for BOTH cards; writes data/maker5_result.txt)
  L1Q1       from 2026-11-06, runs `scalper.r6tests run l1q1` (same refusals; writes data/l1q1_result.txt)
  GF1, GF2   readiness `scalper.gf12 count` (R6 book files only: windows and L1 signals, no coverage or result); from 2026-11-14 02:00 UTC
             (the read date plus 2 hours for the recorder's last push) and at 300 signals, or from 2026-11-15 00:00 UTC whatever
             the count (the data can no longer grow; the run then reports NOT_ENOUGH_DATA), runs `scalper.gf12 run gf1` / `run gf2`
             (each refuses before 2026-11-14 00:00 UTC or a second time; writes data/gf1_result.txt / data/gf2_result.txt)
  DEPTH1     readiness from R6 file names only (`scalper.depth1 readiness`); from 2026-11-14 02:00 UTC runs `scalper.depth1 read` once
             (refuses before 00:00 UTC and a second time; below 300 windows per market writes NOT_ENOUGH_DATA; data/depth1_result.txt)
  STAB       once a week, on the first pass on or after Monday 01:00 US Central (week marked in data/stab_last_week by the run itself), runs
             `scalper.stab week` (a stability check of L1 as live trades it; writes workers/STABILITY.md; no read, no verdict)
  FWDLEDGER  every pass, runs `scalper.fwdledger run` (candidates in workers/candidates/*.json, writes workers/FORWARD_LEDGER.md);
             it only reports forward results after each candidate's freeze, never promotes; its failure stops nothing else
  SERIES     once a week, `scalper.seriescensus` (public /series: fifteen_min series count, those with a settled market, NEW SERIES line); no outcome
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
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
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
    # MKTTIME1-F interim (owner, 2026-10-29): information read at 100 block entries; its line goes to AUTO_LOG for V2 to forward
    interim_out = DATA_DIR / "mkttime1f_interim.txt"
    if interim_out.exists():
        status.append("MKTTIME1-F interim done")
    else:
        from .mkttime1f import INTERIM_ENTRIES, interim_count
        ready, line = guarded("MKTTIME1-F interim", lambda: (lambda n, l: (n >= INTERIM_ENTRIES, l))(*interim_count())); status.append(line)
        if ready:
            rc, o = py("scalper.mkttime1f", "interim")
            log("MKTTIME1-F interim", last_line(interim_out.read_text(), "INTERIM") if interim_out.exists() else f"interim rc={rc}: {last_line(o)[:200]}")
    # MM1
    # scorer from the MM1S amendment; `mm1 run` itself refuses below 300 usable windows, so a refusal just waits for the next pass
    mm1_out = DATA_DIR / "mm1_result.txt"
    if mm1_out.exists():
        status.append("MM1 done")
    else:
        ready, line = guarded("MM1", mm1_count); status.append(line)
        if ready:
            rc, o = py("scalper.mm1", "run")
            if mm1_out.exists():
                log("MM1", last_line(mm1_out.read_text(), "VERDICT"))
            elif not s.get("mm1_refused_logged"):
                log("MM1", f"run refused or failed rc={rc}: {last_line(o)[:200]}"); s["mm1_refused_logged"] = True
    # QUOTE2B (Q2B worker); `quote2b run` refuses before 2026-11-12 and below 300 usable closes, so a refusal just waits
    q2b_out = DATA_DIR / "quote2b_result.txt"
    if q2b_out.exists():
        status.append("QUOTE2B done")
    else:
        rc, o = py("scalper.quote2b", "count", timeout=900)
        status.append("QUOTE2B readiness: " + last_line(o)[:160])
        if datetime.now(timezone.utc) >= datetime(2026, 11, 12, tzinfo=timezone.utc):
            rc, o = py("scalper.quote2b", "run")
            if q2b_out.exists():
                log("QUOTE2B", last_line(q2b_out.read_text(), "VERDICT"))
            elif not s.get("q2b_refused_logged"):
                log("QUOTE2B", f"run refused or failed rc={rc}: {last_line(o)[:200]}"); s["q2b_refused_logged"] = True
    # MAKER5 and L1Q1 (R6T worker, recorder R6); `r6tests run <id>` refuses before 2026-11-06 and below 300 usable windows, so a refusal just waits
    r6_due = datetime.now(timezone.utc) >= datetime(2026, 11, 6, tzinfo=timezone.utc)
    r6_outs = {"MAKER5": DATA_DIR / "maker5_result.txt", "L1Q1": DATA_DIR / "l1q1_result.txt"}
    if all(o.exists() for o in r6_outs.values()):
        status.append("MAKER5 done ; L1Q1 done")
    else:
        rc, o = py("scalper.r6tests", "count", timeout=900)
        status.append("R6T readiness: " + last_line(o, "R6 count")[:300])
        for rid, out in r6_outs.items():
            if out.exists():
                status.append(f"{rid} done")
            elif r6_due:
                rc, o = py("scalper.r6tests", "run", rid.lower())
                if out.exists():
                    log(rid, last_line(out.read_text(), "VERDICT"))
                elif not s.get(f"{rid.lower()}_refused_logged"):
                    log(rid, f"run refused or failed rc={rc}: {last_line(o)[:200]}"); s[f"{rid.lower()}_refused_logged"] = True
    # GF1 and GF2 (GF12 worker, recorder R6); `gf12 run <id>` refuses before 2026-11-14 00:00 UTC and a second time, and below
    # 300 scored windows it writes NOT_ENOUGH_DATA, so it is fired only once the data is complete (workers/GF12_NOTES.md)
    gf_outs = {"GF1": DATA_DIR / "gf1_result.txt", "GF2": DATA_DIR / "gf2_result.txt"}
    if all(o.exists() for o in gf_outs.values()):
        status.append("GF1 done ; GF2 done")
    else:
        rc, o = py("scalper.gf12", "count", timeout=1800)
        line = last_line(o, "GF12 count")
        status.append("GF12 readiness: " + line[:300])
        m = re.search(r"L1 signals (\d+)", line)
        n_sig = int(m.group(1)) if rc == 0 and m else 0
        now_utc = datetime.now(timezone.utc)
        gf_due = (now_utc >= datetime(2026, 11, 14, 2, tzinfo=timezone.utc) and n_sig >= 300) \
            or now_utc >= datetime(2026, 11, 15, tzinfo=timezone.utc)
        for rid, out in gf_outs.items():
            if out.exists():
                status.append(f"{rid} done")
            elif gf_due:
                rc, o = py("scalper.gf12", "run", rid.lower())
                if out.exists():
                    log(rid, last_line(out.read_text(), "VERDICT"))
                elif not s.get(f"{rid.lower()}_refused_logged"):
                    log(rid, f"run refused or failed rc={rc}: {last_line(o)[:200]}"); s[f"{rid.lower()}_refused_logged"] = True
    # DEPTH1 (order-book depth, recorder R6; workers/DEPTH1_REGISTRATION.md): readiness from file NAMES only every pass; `depth1 read` runs once,
    # from 2026-11-14 02:00 UTC (the read refuses before 00:00 UTC by itself; two hours let the recorder's last job push) or 2026-11-15 whatever the count
    d1_out = DATA_DIR / "depth1_result.txt"
    try:
        if d1_out.exists():
            status.append("DEPTH1 done")
        else:
            rc, o = py("scalper.depth1", "readiness", timeout=300)
            status.append((last_line(o, "DEPTH1 readiness") if rc == 0 else f"DEPTH1 readiness failed rc={rc}: {last_line(o)[:160]}")[:400])
            if datetime.now(timezone.utc) >= datetime(2026, 11, 14, 2, tzinfo=timezone.utc):
                rc, o = py("scalper.depth1", "read", timeout=3600)
                if d1_out.exists():
                    log("DEPTH1", last_line(d1_out.read_text(), "VERDICT"))
                elif not s.get("depth1_refused_logged"):
                    log("DEPTH1", f"run refused or failed rc={rc}: {last_line(o)[:200]}"); s["depth1_refused_logged"] = True
    except Exception as ex:
        status.append(f"DEPTH1 readiness error: {type(ex).__name__}: {str(ex)[:120]}")
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
    # STAB (weekly stability check, no read): due when data/stab_last_week is not this week's Monday 01:00 CT boundary
    from .stab import MARK as STAB_MARK, week_key
    wk = week_key(datetime.now(timezone.utc))
    if (STAB_MARK.read_text().strip() if STAB_MARK.exists() else "") != wk:
        rc, o = py("scalper.stab", "week")
        log("STAB", f"week {wk} rc={rc}: {last_line(o, 'STAB done')[:400]}")
    status.append(f"STAB last week {STAB_MARK.read_text().strip() if STAB_MARK.exists() else 'never'}")
    # FWDLEDGER (forward ledger of candidates, report only): every pass, as its own process so a candidate's crash cannot reach this one
    rc, o = py("scalper.fwdledger", "run", timeout=1800)
    status.append((last_line(o, "FWDLEDGER") if rc == 0 else f"FWDLEDGER failed rc={rc}: {last_line(o)[:160]}")[:400])
    # OIFEED (OIFWD-AUDIT, 2026-10-30): the feed behind REF_GEN6_OICORE, every pass, so a stalled fresh.sqlite never reads as a quiet rule;
    # a STALE line also goes to AUTO_LOG, at most once per 6 hours. Counts only (candles, windows, max doi), never an outcome.
    try:
        from .oifeed import status_line
        feed = status_line()
        status.append(feed)
        if "STALE" in feed and time.time() - s.get("oifeed_stale_logged", 0) >= 6 * 3600:
            log("OIFEED", feed[:400]); s["oifeed_stale_logged"] = time.time()
    except Exception as ex:
        status.append(f"OICORE feed: status failed: {type(ex).__name__}")
    # RECFEED (FWD-AUDIT, 2026-10-30): last push of each GitHub Actions recorder (commit times on the data branches, no row read), every pass;
    # a STALE line also goes to AUTO_LOG, at most once per 6 hours, so a dropped schedule never reads as a slow rule.
    try:
        from .recfeed import status_line as rec_status
        rec = rec_status()
        status.append(rec)
        if "STALE" in rec and time.time() - s.get("recfeed_stale_logged", 0) >= 6 * 3600:
            log("RECFEED", rec[:400]); s["recfeed_stale_logged"] = time.time()
    except Exception as ex:
        status.append(f"RECORDERS: status failed: {type(ex).__name__}")
    # SERIESCENSUS (NEWH17, 2026-10-30): once every 7 days, count Kalshi's fifteen_min series and those with a settled market (public /series, no outcome);
    # a series going from none to some starts the line with NEW SERIES. State in this same file; every error is caught inside.
    try:
        from .seriescensus import census as series_census
        sc = series_census(s)
        if sc:
            log("SERIES", sc[:400]); status.append(sc[:200])
    except Exception as ex:
        status.append(f"SERIES CENSUS: failed {type(ex).__name__}")
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
