"""BUYDIP1 (README, Pre-registration: BUYDIP1): "buy at key levels" against plain monthly buying, for SCHD, SPY and QQQ. Rules fixed in the README before any rule was run.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means invest.

Public Yahoo daily adjusted closes (total return) are cached in `data/prices_<SYMBOL>.json`. Usage: python -m scalper.buydip1 fetch   then, ONCE:   python -m scalper.buydip1 run
"""
from __future__ import annotations

import json
import statistics as st
import sys
import urllib.request
from datetime import date, datetime, timezone

from .paths import DATA_DIR

SYMBOLS = ("SCHD", "SPY", "QQQ")
INFO_SYMBOL = "JEPQ"
RULES = ("DIP10", "MA200")
CONTRIBUTION = 500.0
MONTHS = 60
INFO_MONTHS = 36
DIP = 0.10
HIGH_DAYS = 252
MA_DAYS = 200
MAX_WAIT_MONTHS = 6
MIN_STARTS = 24
MIN_SHARE = 0.60
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{s}?period1=1000000000&period2={t}&interval=1d&events=div"


def _path(sym: str):
    return DATA_DIR / f"prices_{sym}.json"


def fetch() -> None:
    import time
    DATA_DIR.mkdir(exist_ok=True)
    for s in SYMBOLS + (INFO_SYMBOL,):
        req = urllib.request.Request(URL.format(s=s, t=int(time.time())), headers={"User-Agent": "Mozilla/5.0 research"})
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)["chart"]["result"][0]
        rows = [(datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d"), a) for t, a in zip(d["timestamp"], d["indicators"]["adjclose"][0]["adjclose"]) if a]
        _path(s).write_text(json.dumps(rows))
        print(f"{s}: {len(rows)} daily closes {rows[0][0]} to {rows[-1][0]}", flush=True)


def load(sym: str) -> list[tuple[date, float]]:
    return [(date.fromisoformat(d), float(p)) for d, p in json.loads(_path(sym).read_text())]


def month_starts(prices: list[tuple[date, float]]) -> list[int]:
    """Index of the first trading day of every calendar month in the data."""
    out, seen = [], None
    for i, (d, _) in enumerate(prices):
        if (d.year, d.month) != seen:
            out.append(i)
            seen = (d.year, d.month)
    return out


def signal(rule: str, px: list[float], i: int) -> bool:
    """True when the rule says buy at close i, using closes up to and including i only."""
    if rule == "DCA":
        return True
    if rule == "DIP10":
        return i >= HIGH_DAYS - 1 and px[i] <= (1.0 - DIP) * max(px[i - HIGH_DAYS + 1:i + 1])
    if rule == "MA200":
        return i >= MA_DAYS - 1 and px[i] < sum(px[i - MA_DAYS + 1:i + 1]) / MA_DAYS
    raise ValueError(rule)


def simulate(prices: list[tuple[date, float]], start: int, months: int, rule: str, cash_rate: float = 0.0) -> dict:
    """End value of `months` monthly contributions beginning at month-start index `start` (an index into month_starts). The end is the last trading day before month `start + months` begins,
    or the last day of data when that month would begin after it. Returns {"end": value, "cash_days": days with cash waiting, "days": days simulated}."""
    ms = month_starts(prices)
    px = [p for _, p in prices]
    first = ms[start]
    stop = ms[start + months] - 1 if start + months < len(ms) else len(prices) - 1
    arrivals = {ms[start + k]: start + k for k in range(months) if start + k < len(ms)}
    month_of = {}
    for k, i in enumerate(ms):
        month_of[i] = k
    cur_month = start
    cash, waiting, units, cash_days = 0.0, [], 0.0, 0
    for i in range(first, stop + 1):
        if i in month_of:
            cur_month = month_of[i]
        cash *= (1.0 + cash_rate) ** (1.0 / 252.0)
        if i in arrivals:
            cash += CONTRIBUTION
            waiting.append(arrivals[i])
        if waiting and (signal(rule, px, i) or cur_month - waiting[0] >= MAX_WAIT_MONTHS):
            units += cash / px[i]
            cash, waiting = 0.0, []
        if cash > 0:
            cash_days += 1
    return {"end": units * px[stop] + cash, "cash_days": cash_days, "days": stop - first + 1}


def ratios(prices: list[tuple[date, float]], rule: str, months: int, cash_rate: float = 0.0) -> list[dict]:
    """One row per start month with `months` full months of data: R = rule end value / DCA end value."""
    ms = month_starts(prices)
    out = []
    for s in range(0, len(ms) - months):
        r = simulate(prices, s, months, rule, cash_rate)
        d = simulate(prices, s, months, "DCA", cash_rate)
        out.append({"start": s, "R": r["end"] / d["end"], "cash_share": r["cash_days"] / r["days"]})
    return out


def verdict(rows: list[dict]) -> tuple[str, dict]:
    if len(rows) < MIN_STARTS:
        return "NOT_ENOUGH_DATA", {"starts": len(rows)}
    rs = [r["R"] for r in rows]
    half = len(rs) // 2
    med, m1, m2 = st.median(rs), st.median(rs[:half]), st.median(rs[half:])
    share = sum(1 for r in rs if r > 1.0) / len(rs)
    ok = med > 1.0 and share >= MIN_SHARE and m1 > 1.0 and m2 > 1.0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"starts": len(rs), "median": med, "share": share, "h1": m1, "h2": m2, "worst": min(rs), "best": max(rs),
                                                           "cash_share": st.mean(r["cash_share"] for r in rows), "audit": med > 1.0}


def run() -> None:
    print("Signal counts first (start months with a full window):")
    data = {s: load(s) for s in SYMBOLS + (INFO_SYMBOL,)}
    for s in SYMBOLS:
        print(f"  {s}: {len(month_starts(data[s]))} months of data, {len(ratios(data[s], 'DCA', MONTHS))} windows of {MONTHS} months")
    print()
    for s in SYMBOLS:
        for rule in RULES:
            v, d = verdict(ratios(data[s], rule, MONTHS))
            if "median" in d:
                print(f"{s} {rule}: {d['starts']} start months, median R {d['median']:.3f}, R above 1 in {d['share']:.0%}, halves {d['h1']:.3f} / {d['h2']:.3f}, worst {d['worst']:.3f}, best {d['best']:.3f}, "
                      f"cash held on {d['cash_share']:.0%} of days -> {v}" + ("  AUDIT TRIGGER: median above 1" if d["audit"] else ""))
                alt = ratios(data[s], rule, MONTHS, cash_rate=0.04)
                print(f"    information, cash at 4% a year: median R {st.median(r['R'] for r in alt):.3f}, R above 1 in {sum(1 for r in alt if r['R'] > 1) / len(alt):.0%}")
            else:
                print(f"{s} {rule}: {d['starts']} start months -> {v}")
    print(f"\nInformation only (not tries): {INFO_SYMBOL}, {INFO_MONTHS} month windows")
    for rule in RULES:
        rows = ratios(data[INFO_SYMBOL], rule, INFO_MONTHS)
        if rows:
            rs = [r["R"] for r in rows]
            print(f"  {INFO_SYMBOL} {rule}: {len(rs)} start months, median R {st.median(rs):.3f}, R above 1 in {sum(1 for r in rs if r > 1) / len(rs):.0%}, worst {min(rs):.3f}, best {max(rs):.3f}")


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
