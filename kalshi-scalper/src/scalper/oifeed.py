"""OIFEED (OIFWD-AUDIT, 2026-10-30): one status line on the data feed behind the forward row REF_GEN6_OICORE, so a stalled
data/fresh.sqlite can never again look like a quiet rule. Research only: it reads candles and counts, never a window's result.

    PYTHONPATH=src python -m scalper.oifeed        (prints the line; `scalper.autoscore check` appends it to every pass's status)

Why: on 2026-10-30 the ledger showed OICORE at 0 windows for 11 hours because the AUTO loop died with a container restart and nothing
refreshed fresh.sqlite; the rule and its evaluator were fine (workers/OIFWD_AUDIT.md). Every error is caught: the line then says so.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .paths import DATA_DIR

CT = ZoneInfo("America/Chicago")
FRESH = DATA_DIR / "fresh.sqlite"
CAND = DATA_DIR.parent / "workers" / "candidates" / "REF_GEN6_OICORE.json"
SERIES, LOOK, BACK = "KXBTC15M", 180, 360
LO, HI, THRESH = 0.05, 0.50, 86299.56
FREEZE_DEFAULT = int(datetime(2026, 10, 30, 3, tzinfo=timezone.utc).timestamp())
STALE_H = 7.0     # the loop refreshes every 6 hours; one missed refresh is a stall


def freeze_ts() -> int:
    try:
        return int(datetime.fromisoformat(json.loads(CAND.read_text())["freeze_utc"].replace("Z", "+00:00")).timestamp())
    except Exception:
        return FREEZE_DEFAULT


def _ct(ts: int) -> str:
    return datetime.fromtimestamp(ts, CT).strftime("%Y-%m-%d %H:%M CT")


def counts(db_path=FRESH, freeze: int | None = None, now: float | None = None) -> dict:
    """Last KXBTC15M candle, settled windows closed since the freeze, those with a 5c to 50c side at 180 s, the largest doi seen.
    Reads only candles and the settled flag; never an outcome."""
    freeze = freeze_ts() if freeze is None else freeze
    now = time.time() if now is None else now
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        last = db.execute("select max(end_ts) from candle where series=?", (SERIES,)).fetchone()[0]
        wins = db.execute("select ticker, close_ts from market where series=? and close_ts>? and result in ('yes','no')", (SERIES, freeze)).fetchall()
        cand, mx, n_doi = 0, None, 0
        for tk, ct in wins:
            q = {e: (b, a, oi) for e, b, a, oi in db.execute(
                "select end_ts, bid_c, ask_c, oi from candle where ticker=? and end_ts in (?, ?)", (tk, ct - LOOK, ct - BACK))}
            s, p = q.get(ct - LOOK), q.get(ct - BACK)
            if s and s[0] is not None and s[1] is not None:
                asks = (s[1], round(1 - s[0], 4))
                cand += any(LO - 1e-9 <= a <= HI + 1e-9 for a in asks)
            if s and p and s[2] is not None and p[2] is not None:
                d = s[2] - p[2]; n_doi += 1
                mx = d if mx is None or d > mx else mx
    finally:
        db.close()
    age_h = (now - last) / 3600 if last else None
    return {"freeze": freeze, "last_candle": last, "age_h": age_h, "windows": len(wins), "candidates": cand, "max_doi": mx,
            "with_doi": n_doi, "stale": last is None or age_h > STALE_H}


def status_line(db_path=FRESH, freeze: int | None = None, now: float | None = None) -> str:
    try:
        c = counts(db_path, freeze, now)
        last = f"{_ct(c['last_candle'])} ({c['age_h']:.1f} h old)" if c["last_candle"] else "none"
        mx = f"{c['max_doi']:,.0f}" if c["max_doi"] is not None else "n/a"
        line = (f"OICORE feed: last {SERIES} candle {last}; since the freeze {_ct(c['freeze'])}: {c['windows']} settled windows, "
                f"{c['candidates']} with a 5c to 50c side at {LOOK} s, max doi {mx} (rule threshold {THRESH:,.0f})")
        if c["stale"]:
            line += f"; STALE: no new candle for over {STALE_H:.0f} h (is the AUTO loop running? fresh_update refreshes it)"
        return line
    except Exception as ex:          # the status line must never stop a pass
        return f"OICORE feed: status failed: {type(ex).__name__}: {str(ex)[:120]}"


if __name__ == "__main__":
    print(status_line(*(sys.argv[1:2] or [FRESH])))
