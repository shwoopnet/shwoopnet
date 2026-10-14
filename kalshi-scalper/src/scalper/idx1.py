"""IDX1 (README, "Equities and options: ... four registered index-level tests"): overnight drift, turn of the month and the pre-holiday session on SPY and QQQ.
Rules fixed in the README before any was run. Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Public Yahoo daily open and adjusted close are cached in `data/ohlc_<SYMBOL>.json`. Usage: python -m scalper.idx1 fetch   then, ONCE:   python -m scalper.idx1 run
"""
from __future__ import annotations

import json
import statistics as st
import sys
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from .calibration import cluster_mean_z
from .paths import DATA_DIR

SYMBOLS = ("SPY", "QQQ")
SPLIT = date(2012, 1, 1)            # holdout = on or after
COST = 0.0002
STRESS_COST = 0.0004
Z_BAR = 2.4
MIN_ACTIVE = 150
TRADING_DAYS = 252
TRIES = (("A_overnight", "SPY"), ("A_overnight", "QQQ"), ("B_turn_of_month", "SPY"), ("C_pre_holiday", "SPY"))
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{s}?period1=725846400&period2={t}&interval=1d"


def _path(sym: str):
    return DATA_DIR / f"ohlc_{sym}.json"


def fetch() -> None:
    import time
    DATA_DIR.mkdir(exist_ok=True)
    for s in SYMBOLS + ("^VIX",):
        req = urllib.request.Request(URL.format(s=s.replace("^", "%5E"), t=int(time.time())), headers={"User-Agent": "Mozilla/5.0 research"})
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)["chart"]["result"][0]
        q = d["indicators"]["quote"][0]
        adj = d["indicators"].get("adjclose", [{}])[0].get("adjclose", q["close"])
        rows = [(datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d"), o, c, a) for t, o, c, a in zip(d["timestamp"], q["open"], q["close"], adj) if o and c and a]
        _path(s.replace("^", "")).write_text(json.dumps(rows))
        print(f"{s}: {len(rows)} days {rows[0][0]} to {rows[-1][0]}", flush=True)


def load(sym: str) -> list[dict]:
    """Rows with the dividend adjusted open (`ao`), adjusted close (`ac`), and the close to close return `r` and overnight return `o` (None on the first day)."""
    raw = json.loads(_path(sym).read_text())
    out = []
    for d, o, c, a in raw:
        out.append({"date": date.fromisoformat(d), "ao": o * a / c, "ac": a, "r": None, "o": None})
    for i in range(1, len(out)):
        out[i]["r"] = out[i]["ac"] / out[i - 1]["ac"] - 1.0
        out[i]["o"] = out[i]["ao"] / out[i - 1]["ac"] - 1.0
    return out[1:]


def _weekdays_between(a: date, b: date) -> int:
    """Weekdays strictly between two dates."""
    n, d = 0, a + timedelta(days=1)
    while d < b:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def strategy_returns(rows: list[dict], rule: str, cost: float) -> list[float]:
    """The strategy's net return for each row, zero when it is flat. A: the overnight return minus `cost` every day. B: the close to close returns of the first 3 sessions of each calendar
    month (bought at the prior close), with `cost` deducted on the third. C: the return of each pre-holiday session (a session followed, after a weekday with no trading, by the next one)
    with `cost` deducted on it."""
    n = len(rows)
    s = [0.0] * n
    if rule == "A_overnight":
        return [x["o"] - cost for x in rows]
    if rule == "B_turn_of_month":
        seen: dict = defaultdict(int)
        for i, x in enumerate(rows):
            key = (x["date"].year, x["date"].month)
            seen[key] += 1
            if seen[key] <= 3:
                s[i] = x["r"] - (cost if seen[key] == 3 else 0.0)
        return s
    if rule == "C_pre_holiday":
        for i in range(n - 1):
            if _weekdays_between(rows[i]["date"], rows[i + 1]["date"]) >= 1:
                s[i] = rows[i]["r"] - cost
        return s
    raise ValueError(rule)


def active_periods(rows: list[dict], rule: str) -> int:
    s = strategy_returns(rows, rule, 0.0)
    if rule == "A_overnight":
        return len(rows)
    if rule == "B_turn_of_month":
        return len({(x["date"].year, x["date"].month) for x, v in zip(rows, s) if v != 0.0})
    return sum(1 for i in range(len(rows) - 1) if _weekdays_between(rows[i]["date"], rows[i + 1]["date"]) >= 1)


def alpha(rows: list[dict], rule: str, cost: float, beta: float | None = None) -> dict:
    """Annualised alpha of the rule over `rows`: mean(s) - beta * mean(r), beta from the regression of s on r over `rows` unless given, with a month clustered z."""
    s = strategy_returns(rows, rule, cost)
    r = [x["r"] for x in rows]
    mr, ms = sum(r) / len(r), sum(s) / len(s)
    var = sum((x - mr) ** 2 for x in r)
    b = (sum((x - mr) * (y - ms) for x, y in zip(r, s)) / var) if beta is None else beta
    a = [y - b * x for x, y in zip(r, s)]
    months = [f"{x['date'].year}-{x['date'].month:02d}" for x in rows]
    mean, se, z = cluster_mean_z(list(zip(months, a)))
    return {"alpha_year": mean * TRADING_DAYS, "z": z, "beta": b, "mean_s_year": ms * TRADING_DAYS}


def verdict(rows: list[dict], rule: str) -> tuple[str, dict]:
    disc = [x for x in rows if x["date"] < SPLIT]
    hold = [x for x in rows if x["date"] >= SPLIT]
    if not hold or active_periods(hold, rule) < MIN_ACTIVE:
        return "NOT_ENOUGH_DATA", {"active": active_periods(hold, rule) if hold else 0}
    a_h = alpha(hold, rule, COST)
    a_d = alpha(disc, rule, COST) if disc else {"alpha_year": 0.0, "z": 0.0}
    a_s = alpha(hold, rule, STRESS_COST)
    mid = hold[len(hold) // 2]["date"]
    h1 = [x for x in hold if x["date"] < mid]
    h2 = [x for x in hold if x["date"] >= mid]
    b = a_h["beta"]
    r1, r2 = alpha(h1, rule, COST, beta=b)["alpha_year"], alpha(h2, rule, COST, beta=b)["alpha_year"]
    ok = a_h["alpha_year"] > 0 and a_h["z"] >= Z_BAR and r1 > 0 and r2 > 0 and a_s["alpha_year"] > 0 and a_d["alpha_year"] > 0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"holdout": a_h, "discovery": a_d, "stress": a_s, "h1": r1, "h2": r2, "active": active_periods(hold, rule), "audit": a_h["z"] >= Z_BAR}


def vrp_information() -> None:
    """Information only: the VIX against the volatility SPY then realised over the next 30 calendar days (about 21 sessions), from public daily data."""
    spy = {x["date"]: x for x in load("SPY")}
    vix = {date.fromisoformat(d): c for d, o, c, a in json.loads(_path("VIX").read_text())}
    dates = sorted(spy)
    gaps = []
    for i in range(0, len(dates) - 22, 21):
        d = dates[i]
        if d not in vix:
            continue
        rets = [spy[x]["r"] for x in dates[i + 1:i + 22]]
        rv = (sum(x * x for x in rets) / len(rets)) ** 0.5 * (TRADING_DAYS ** 0.5) * 100.0
        gaps.append((d, vix[d] - rv))
    g = [x for _, x in gaps]
    print(f"VRP information: {len(g)} non-overlapping 21 session windows from {gaps[0][0]} to {gaps[-1][0]}: mean VIX minus realised {st.mean(g):+.2f} vol points, "
          f"positive in {sum(1 for x in g if x > 0) / len(g):.0%}, median {st.median(g):+.2f}, worst {min(g):+.1f} (a month where the market moved far more than it was priced to), 5th percentile {sorted(g)[len(g) // 20]:+.1f}")


def run() -> None:
    data = {s: load(s) for s in SYMBOLS}
    print("Signal counts first: " + ", ".join(f"{s} {len(data[s])} days from {data[s][0]['date']}" for s in SYMBOLS))
    f = lambda x: f"{x * 100:+.2f}%"
    for rule, sym in TRIES:
        v, d = verdict(data[sym], rule)
        if "holdout" in d:
            h = d["holdout"]
            print(f"\n{rule} on {sym}: holdout active {d['active']}, net alpha {f(h['alpha_year'])} a year (beta {h['beta']:.2f}, month clustered z {h['z']:+.2f}), halves {f(d['h1'])} / {f(d['h2'])}, "
                  f"stress cost {f(d['stress']['alpha_year'])}, discovery {f(d['discovery']['alpha_year'])} (z {d['discovery']['z']:+.2f}) -> {v}" + ("  AUDIT TRIGGER" if d["audit"] else ""))
            print(f"    information: net return a year while exposed-or-flat {f(h['mean_s_year'])}; buy and hold {sym} {f(st.mean(x['r'] for x in data[sym] if x['date'] >= SPLIT) * TRADING_DAYS)} a year over the holdout")
        else:
            print(f"\n{rule} on {sym}: active {d['active']} -> {v}")
    print()
    vrp_information()


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
