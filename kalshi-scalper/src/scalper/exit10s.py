"""X8 (README, Pre-registration: X8): an exit at 70c on the recorder's 10 second books, read on FRESH data only. Research only: nothing here places an order.

Input: one or more CSV files from the page's "Download book snapshots" (gz or plain), columns t (ms), series, ticker, yesBid, yesAsk, noBid, noAsk, ...
Usage: python -m scalper.exit10s FILE [FILE ...]      (one read, after the registered start; snapshots before CUTOFF_MS are ignored)
"""
from __future__ import annotations

import csv
import gzip
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .calibration import cluster_mean_z
from .scalps import MIN_N, STRESS, Z_BAR

CUTOFF_MS = int(datetime(2026, 10, 10, 12, 57, tzinfo=timezone.utc).timestamp() * 1000)   # the first fresh snapshot: everything before it was read exploratorily
THRESHOLD = 0.70
BAND = (0.88, 0.97)
WINDOW_MS = (330_000, 400_000)
TARGET_MS = 365_000
MIN_DAYS = 5
_ET = ZoneInfo("America/New_York")


def fee(p: float, mult: float = 1.0) -> float:
    return mult * 0.07 * p * (1 - p)


def close_ms(ticker: str) -> int:
    """KXBTC15M-26OCT092245-45: the close, written in Eastern time (EDT or EST)."""
    s = ticker.split("-")[1]
    mon = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}[s[2:5]]
    d = datetime(2000 + int(s[:2]), mon, int(s[5:7]), int(s[7:9]), int(s[9:11]), tzinfo=_ET)
    return int(d.timestamp() * 1000)


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load(paths: list[str]) -> dict[str, list[tuple]]:
    """{ticker: [(t, series, yesBid, yesAsk, noBid, noAsk)]}, merged across files, de-duplicated on (t, ticker), snapshots before CUTOFF_MS dropped."""
    seen, by = set(), defaultdict(list)
    for p in paths:
        op = gzip.open if str(p).endswith(".gz") else open
        with op(p, "rt") as f:
            for r in csv.DictReader(f):
                t = int(r["t"])
                if t < CUTOFF_MS or (t, r["ticker"]) in seen:
                    continue
                seen.add((t, r["ticker"]))
                by[r["ticker"]].append((t, r["series"], _num(r["yesBid"]), _num(r["yesAsk"]), _num(r["noBid"]), _num(r["noAsk"])))
    for v in by.values():
        v.sort()
    return by


def entries(by: dict[str, list[tuple]]) -> list[dict]:
    """L1's entries on the snapshots, each with its settlement and both arms (hold, exit at THRESHOLD)."""
    out = []
    for tk, snaps in by.items():
        cm = close_ms(tk)
        cand = [s for s in snaps if WINDOW_MS[0] <= cm - s[0] <= WINDOW_MS[1]]
        if not cand:
            continue
        e = min(cand, key=lambda s: abs((cm - s[0]) - TARGET_MS))
        t0, series, yb, ya, nb, na = e
        if ya is not None and BAND[0] - 1e-9 <= ya <= BAND[1] + 1e-9:
            side, price = "yes", ya
        elif na is not None and BAND[0] - 1e-9 <= na <= BAND[1] + 1e-9:
            side, price = "no", na
        else:
            continue
        path = [(s[0], s[2] if side == "yes" else s[4]) for s in snaps if t0 < s[0] <= cm + 20_000]     # strictly LATER than the entry snapshot
        path = [(t, b) for t, b in path if b is not None]
        if len(path) < 3:
            continue
        last = path[-1][1]
        res = "win" if last >= 0.90 else ("loss" if last <= 0.10 else "unclear")
        if res == "unclear":
            continue
        hit = next(((t, b) for t, b in path if b <= THRESHOLD), None)
        won = res == "win"
        hold = (1.0 if won else 0.0) - price - fee(price)
        hold_s = (1.0 if won else 0.0) - price - fee(price, STRESS)
        if hit:
            ex = hit[1] - price - fee(price) - fee(hit[1])
            ex_s = hit[1] - price - fee(price, STRESS) - fee(hit[1], STRESS)
        else:
            ex, ex_s = hold, hold_s
        day = datetime.fromtimestamp(cm / 1000, timezone.utc).strftime("%Y-%m-%d")
        out.append({"ticker": tk, "series": series, "side": side, "price": price, "t0": t0, "close_ts": cm // 1000, "day": day, "res": res,
                    "stopped": hit is not None, "hold": hold, "exit": ex, "diff": ex - hold, "diff_stress": ex_s - hold_s})
    return sorted(out, key=lambda e: e["close_ts"])


def verdict(es: list[dict]) -> tuple[str, dict]:
    if not es:
        return "NOT_ENOUGH_DATA", {"n": 0}
    mean, se, z = cluster_mean_z([(e["day"], e["diff"]) for e in es])
    days = sorted({e["day"] for e in es})
    mid = (es[0]["close_ts"] + es[-1]["close_ts"]) / 2
    h1 = [e["diff"] for e in es if e["close_ts"] < mid]
    h2 = [e["diff"] for e in es if e["close_ts"] >= mid]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    stress = sum(e["diff_stress"] for e in es) / len(es)
    stats = {"n": len(es), "days": len(days), "mean": mean, "z": z, "h1": m1, "h2": m2, "stress": stress}
    if len(es) < MIN_N or len(days) < MIN_DAYS:
        return "NOT_ENOUGH_DATA", stats
    ok = mean > 0 and z >= Z_BAR and m1 > 0 and m2 > 0 and stress > 0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), stats


def _day_series(es: list[dict], key: str) -> tuple[float, float]:
    byday = defaultdict(float)
    for e in es:
        byday[e["day"]] += e[key]
    worst_day = min(byday.values()) if byday else 0.0
    cum = peak = dd = 0.0
    for e in es:
        cum += e[key]
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return worst_day, dd


def run(paths: list[str]) -> None:
    by = load(paths)
    es = entries(by)
    print(f"{sum(len(v) for v in by.values())} fresh snapshots on {len(by)} markets; signal count first: {len(es)} entries (the registered minimum is 300 on 5 days)")
    if not es:
        print("VERDICT: NOT_ENOUGH_DATA")
        return
    v, s = verdict(es)
    f = lambda x: f"{x * 100:+.2f}c"
    losses = [e for e in es if e["res"] == "loss"]; wins = [e for e in es if e["res"] == "win"]
    print(f"X8 exit at {THRESHOLD:.2f}: n={s['n']} on {s['days']} days; exit minus hold per entry {f(s['mean'])}, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, fees x{STRESS} {f(s['stress'])}")
    print(f"  losses stopped {sum(e['stopped'] for e in losses)} of {len(losses)}; winners stopped {sum(e['stopped'] for e in wins)} of {len(wins)}")
    for label, key in (("hold", "hold"), ("exit", "exit")):
        wd, dd = _day_series(es, key)
        print(f"  {label}: mean {f(sum(e[key] for e in es) / len(es))}, worst entry {f(min(e[key] for e in es))}, worst day {wd * 100:+.0f}c, deepest drawdown {dd * 100:.0f}c (one contract per entry)")
    print(f"VERDICT: {v}")


if __name__ == "__main__":
    run(sys.argv[1:])
