"""EVENT830 (workers/EVENT830_REGISTRATION.md): forward-only test of the cheap side (ask 0.05 to 0.50, hard fill limit 0.50) of the 8 L1-free
15 minute series in the window that CLOSES at a US 8:30 ET data release. Research only: no order, no key, no promote.
Evaluator for the forward ledger (source "candles"): `scalper.event830:forward_eval`. The rule is EVENT1's (`event1.window_trade`), unchanged.
    PYTHONPATH=src python -m scalper.event830 report   (event trades, Eastern-clock control, event minus control, kill-rule status)
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from . import event1
from .fwdeval import NoData

UTC = timezone.utc
NY = ZoneInfo("America/New_York")
SERIES = set(event1.SERIES)
FREEZE = int(datetime(2026, 11, 3, 15, 0, tzinfo=UTC).timestamp())
FLOOR_N, STOP_N = 150, 40
PF_BAR, STOP_PF = 1.2, 1.0
US_HOLIDAYS = {"2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18", "2027-02-15"}


def _t(day, hh="13:30"):
    return int(datetime.strptime(f"{day} {hh}", "%Y-%m-%d %H:%M").replace(tzinfo=UTC).timestamp())


# Frozen list (08:30 ET = 13:30 UTC in standard time). Append only, from official schedules; see workers/EVENT830_CALENDAR.md.
RELEASES = {_t(d): k for d, k in [
    ("2026-11-05", "CLAIMS"), ("2026-11-06", "JOBS"), ("2026-11-10", "CPI"), ("2026-11-12", "CLAIMS"), ("2026-11-13", "PPI"),
    ("2026-11-17", "RETAIL"), ("2026-11-19", "CLAIMS"), ("2026-11-25", "GDP_PCE"),
    ("2026-12-03", "CLAIMS"), ("2026-12-04", "JOBS"), ("2026-12-10", "CPI_CLAIMS"), ("2026-12-15", "PPI"), ("2026-12-16", "RETAIL"),
    ("2026-12-17", "CLAIMS"), ("2026-12-23", "GDP_PCE"),
]}


def forward_eval(window, params=None):
    """The EVENT1 trade on a window that closes at a listed release; None for every other window. NoData when a candle the rule needs is
    missing (not evaluated, never scored as a no-trade)."""
    if window.get("series") not in SERIES or window["close_ts"] not in RELEASES:
        return None
    why, tr = event1.window_trade(window["candles"], window["close_ts"])
    if why == "gap":
        raise NoData("signal or fill candle missing or one-sided")
    if tr is None:
        return None
    return {"side": tr["side"], "entry": float(tr["fill"]), "exit": None, "t": int(window["close_ts"] - event1.FILL),
            "zero_volume": bool(tr["zv"]), "note": f"{RELEASES[window['close_ts']]} cheap side, fill {tr['fill']:.2f}"}


def is_control(ct):
    """Closes at 08:30 New York time on a weekday, no listed release, not a holiday."""
    et = datetime.fromtimestamp(ct, NY)
    return (et.hour, et.minute) == (8, 30) and et.weekday() < 5 and ct not in RELEASES and et.strftime("%Y-%m-%d") not in US_HOLIDAYS


def diff_vs_control(ev, ctl):
    """Mean of (event net - mean net of the same series' control trades), cents per contract; z day-clustered, control SE added. A series
    with under CTRL_MIN control trades is dropped. Returns (diff, z, n used, n dropped)."""
    from .calibration import cluster_mean_z
    import math
    by = {}
    for t in ctl:
        by.setdefault(t["series"], []).append(event1.net_c(t["tr"]["fill"], t["win"]))
    res, dropped = [], 0
    for t in ev:
        v = by.get(t["series"], [])
        if len(v) < event1.CTRL_MIN:
            dropped += 1
            continue
        res.append((t["day"], event1.net_c(t["tr"]["fill"], t["win"]) - sum(v) / len(v)))
    if len(res) < 2:
        return 0.0, 0.0, len(res), dropped
    mean, se, _ = cluster_mean_z(res)
    cse = cluster_mean_z([(t["day"], event1.net_c(t["tr"]["fill"], t["win"])) for t in ctl])[1] if len(ctl) > 1 else 0.0
    tot = math.sqrt(se * se + cse * cse)
    return mean, (mean / tot if tot > 0 and tot != float("inf") else 0.0), len(res), dropped


def status(st, diff, now_ct, first_ct):
    """The registered kill rules. st = event1.stats of settled event trades; diff = event minus control (cents)."""
    n = st.get("n", 0)
    if n >= STOP_N and st["pf"] < STOP_PF:
        return "STOPPED_EARLY (FALSIFIED): PF under 1.0 at 40 or more trades"
    if n < FLOOR_N:
        rate = n / max((now_ct - first_ct) / 86400 / 30, 1e-9) if n else 35.0
        return f"NOT_ENOUGH_DATA: {n} of {FLOOR_N} trades, about {(FLOOR_N - n) / max(rate, 1e-9):.1f} months to go at {rate:.0f} per month"
    if st["pf"] < PF_BAR or diff <= 0 or st["pf_x12"] <= 1.0:
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED (a count of this size cannot reach the z bar 5.27)"


def report():
    from .fwdledger import load_candles
    ev, ctl, nd = [], [], 0
    for w in load_candles(set(SERIES), FREEZE):
        if w["series"] not in SERIES or w["result"] not in ("yes", "no"):
            continue
        ct = w["close_ts"]
        if ct in RELEASES or is_control(ct):
            why, tr = event1.window_trade(w["candles"], ct)
            if why == "gap":
                nd += 1
            if tr is None:
                continue
            row = {"series": w["series"], "ct": ct, "tr": tr, "win": (w["result"] == "yes") == (tr["side"] == "yes"), "day": event1.day_of(ct)}
            (ev if ct in RELEASES else ctl).append(row)
    se, sc = event1.stats(ev), event1.stats(ctl)
    d, z, nu, ndrop = diff_vs_control(ev, ctl)
    now = int(datetime.now(UTC).timestamp())
    print("event ", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in se.items()})
    print("ctrl  ", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in sc.items()})
    print(f"event minus control {d:+.2f}c z {z:+.2f} (n used {nu}, dropped {ndrop}); gaps {nd}")
    print(status(se, d, now, FREEZE) if se.get("n") else f"NOT_ENOUGH_DATA: 0 of {FLOOR_N} trades, no settled release window after the freeze yet")


if __name__ == "__main__":
    {"report": report}[sys.argv[1]]()
