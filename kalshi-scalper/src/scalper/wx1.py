"""WX1 (README, Pre-registration: WX1): daily high-temperature markets against a public forecast. Rules fixed in the README before this file ran on any market.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

History goes into its OWN database (`data/weather.sqlite`). Usage: python -m scalper.wx1 fetch   then   python -m scalper.wx1 run
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics as st
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from . import api, backfill
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalps import STRESS, fee

WX_DB = DATA_DIR / "weather.sqlite"
CITIES = {  # series -> (name, latitude, longitude): the registered seven
    "KXHIGHCHI": ("Chicago", 41.7860, -87.7524),
    "KXHIGHNY": ("New York", 40.7789, -73.9692),
    "KXHIGHMIA": ("Miami", 25.7959, -80.2870),
    "KXHIGHAUS": ("Austin", 30.1945, -97.6699),
    "KXHIGHDEN": ("Denver", 39.8466, -104.6562),
    "KXHIGHLAX": ("Los Angeles", 33.9382, -118.3866),
    "KXHIGHPHIL": ("Philadelphia", 39.8719, -75.2411),
}
DAYS = 69
DECISION_LEFT_S = 26 * 3600     # decision candle: ends 26 h before the close (22:00 local standard time the evening before)
ENTRY_LEFT_S = 25 * 3600        # entry candle: the NEXT hourly candle, strictly later
FIT_DAYS = 20                   # the last 20 resolved days at most ...
MIN_FIT = 10                    # ... and at least 10 usable ones
MIN_PRIOR = 20                  # a test day needs 20 prior resolved days
SIGMA_FLOOR = 1.5
EDGE = 0.03
BAND = (0.05, 0.95)
MIN_TRADES = 200
MIN_DAYS = 20
Z_BAR = 2.1
PLACEBO_REPS = 200
MDE_FLAG = 0.03
SENSITIVITY = (0.0, 0.02, 0.03, 0.05)


def ncdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bucket_range(stype: str, floor: float | None, cap: float | None) -> tuple[float, float] | None:
    """The continuous temperature range a bucket covers, with integer rounding: 'between 69 and 70' is [68.5, 70.5), 'less' with cap 69 is below 68.5, 'greater' with floor 76 is 76.5 and up."""
    if stype == "between" and floor is not None and cap is not None:
        return (floor - 0.5, cap + 0.5)
    if stype == "less" and cap is not None:
        return (-1e9, cap - 0.5)
    if stype == "greater" and floor is not None:
        return (floor + 0.5, 1e9)
    return None


def bucket_prob(mu: float, sigma: float, rng: tuple[float, float]) -> float:
    lo, hi = rng
    hi_c = 1.0 if hi >= 1e8 else ncdf((hi - mu) / sigma)
    lo_c = 0.0 if lo <= -1e8 else ncdf((lo - mu) / sigma)
    return max(0.0, min(1.0, hi_c - lo_c))


def observed(stype: str, floor: float | None, cap: float | None) -> float | None:
    """The temperature a resolved-YES bucket implies: its midpoint. A tail says too little and is dropped from the fit."""
    if stype == "between" and floor is not None and cap is not None:
        return (floor + cap) / 2.0
    return None


def calibrate(history: list[tuple[float, float]]) -> tuple[float, float] | None:
    """(bias, sigma) from (mu, observed) pairs: bias is the mean of observed minus mu; sigma is the standard deviation of that error, never below SIGMA_FLOOR. None if too few."""
    if len(history) < MIN_FIT:
        return None
    errs = [o - m for m, o in history]
    return st.mean(errs), max(st.pstdev(errs), SIGMA_FLOOR)


def climate_mu(forecast: dict[int, float], close_ts: int) -> float | None:
    """The maximum of the hourly previous-day-1 forecasts over the 24 hours ending at the close, or None when an hour is missing."""
    hrs = [forecast.get(t) for t in range(close_ts - 86400, close_ts, 3600)]
    return max(hrs) if all(h is not None for h in hrs) else None


def valid(bid: float | None, ask: float | None) -> bool:
    return bid is not None and ask is not None and bid >= 0.01 and ask <= 0.99 and ask >= bid


def pick_trade(p: float, bid: float, ask: float, edge: float = EDGE):
    """The side with the larger edge after the fee if it is at least `edge` and its price lies inside BAND, else None. Returns (side, price, edge)."""
    no_ask = round(1.0 - bid, 4)
    e_yes = p - ask - fee(ask)
    e_no = (1.0 - p) - no_ask - fee(no_ask)
    side, price, e = ("yes", ask, e_yes) if e_yes >= e_no else ("no", no_ask, e_no)
    if e >= edge - 1e-12 and BAND[0] - 1e-9 <= price <= BAND[1] + 1e-9:
        return side, price, e
    return None


def load() -> tuple[dict, dict]:
    """({series: {close_ts: [bucket dicts]}}, {series: {ts: temp_f}})."""
    db = sqlite3.connect(WX_DB)
    quotes: dict = defaultdict(dict)
    for t, end, bc, ac, v in db.execute("SELECT ticker, end_ts, bid_c, ask_c, volume FROM candle"):
        quotes[t][end] = (bc, ac, v)
    days: dict = {s: defaultdict(list) for s in CITIES}
    for t, s, close_ts, res, stype, fl, cp in db.execute("SELECT ticker, series, close_ts, result, strike_type, floor, cap FROM market"):
        if s in days:
            days[s][close_ts].append({"ticker": t, "result": res, "type": stype, "floor": fl, "cap": cp, "q": quotes.get(t, {})})
    fc: dict = {s: {} for s in CITIES}
    for city, ts, tf in db.execute("SELECT city, ts, temp_f FROM forecast"):
        if city in fc:
            fc[city][ts] = tf
    return days, fc


def simulate(days: dict, fc: dict, edge: float = EDGE) -> tuple[list[dict], list[dict]]:
    """(trades, brier rows). Walk forward: a day's fit uses only days whose close is at or before that day's DECISION time, so the previous day, which closes two hours after it, is never in."""
    trades, brier = [], []
    for series, by_close in days.items():
        closes = sorted(by_close)
        mus = {c: climate_mu(fc.get(series, {}), c) for c in closes}
        obs = {}
        for c in closes:
            win = [b for b in by_close[c] if b["result"] == "yes"]
            obs[c] = observed(win[0]["type"], win[0]["floor"], win[0]["cap"]) if len(win) == 1 else None
        resolved = [c for c in closes if any(b["result"] in ("yes", "no") for b in by_close[c])]
        for c in closes:
            decision_ts = c - DECISION_LEFT_S
            prior = [x for x in resolved if x <= decision_ts]
            if len(prior) < MIN_PRIOR or mus[c] is None:
                continue
            hist = [(mus[x], obs[x]) for x in prior[-FIT_DAYS:] if mus[x] is not None and obs[x] is not None]
            cal = calibrate(hist)
            if cal is None:
                continue
            bias, sigma = cal
            for b in by_close[c]:
                q = b["q"].get(c - ENTRY_LEFT_S)
                rng = bucket_range(b["type"], b["floor"], b["cap"])
                if q is None or rng is None or b["result"] not in ("yes", "no") or not valid(q[0], q[1]):
                    continue
                p = bucket_prob(mus[c] + bias, sigma, rng)
                yes = b["result"] == "yes"
                mid = (q[0] + q[1]) / 2.0
                brier.append({"series": series, "close_ts": c, "model": (p - (1.0 if yes else 0.0)) ** 2, "market": (mid - (1.0 if yes else 0.0)) ** 2})
                pk = pick_trade(p, q[0], q[1], edge)
                if pk is None:
                    continue
                side, price, e = pk
                won = yes if side == "yes" else (not yes)
                net = (1.0 if won else 0.0) - price - fee(price)
                stress = (1.0 if won else 0.0) - price - fee(price, STRESS)
                p_side_mid = mid if side == "yes" else 1.0 - mid
                trades.append({"series": series, "close_ts": c, "day": datetime.fromtimestamp(c, timezone.utc).strftime("%Y-%m-%d"), "side": side, "price": price,
                               "net": net, "stress": stress, "mid": p_side_mid})
    return sorted(trades, key=lambda t: t["close_ts"]), brier


def placebo_means(trades: list[dict], reps: int = PLACEBO_REPS, seed: int = 11) -> list[float]:
    """A fair market: the same entries, prices and fees, each outcome drawn as a Bernoulli at the entry's mid price."""
    rng = random.Random(seed)
    out = []
    for _ in range(reps):
        tot = 0.0
        for t in trades:
            tot += (1.0 if rng.random() < t["mid"] else 0.0) - t["price"] - fee(t["price"])
        out.append(tot / len(trades))
    return out


def verdict(trades: list[dict], placebo: list[float]) -> tuple[str, dict]:
    n = len(trades)
    days = sorted({t["day"] for t in trades})
    if n < MIN_TRADES or len(days) < MIN_DAYS:
        return "NOT_ENOUGH_DATA", {"n": n, "days": len(days)}
    mean, se, z = cluster_mean_z([(t["day"], t["net"]) for t in trades])
    half = days[len(days) // 2]
    h1 = [t["net"] for t in trades if t["day"] < half]
    h2 = [t["net"] for t in trades if t["day"] >= half]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    stress = sum(t["stress"] for t in trades) / n
    p95 = sorted(placebo)[int(0.95 * (len(placebo) - 1))] if placebo else float("inf")
    ok = mean > 0 and z >= Z_BAR and m1 > 0 and m2 > 0 and stress > 0 and mean > p95
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": n, "days": len(days), "mean": mean, "z": z, "h1": m1, "h2": m2, "stress": stress, "p95": p95, "mde": Z_BAR * se}


# ---------------------------------------------------------------- download
def _iso_utc(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def fetch_forecast(lat: float, lon: float, start: str, end: str) -> dict[int, float]:
    out: dict[int, float] = {}
    d0 = datetime.fromisoformat(start)
    d1 = datetime.fromisoformat(end)
    while d0 <= d1:
        d_end = min(d0 + timedelta(days=29), d1)
        q = urllib.parse.urlencode({"latitude": lat, "longitude": lon, "hourly": "temperature_2m_previous_day1", "start_date": d0.date().isoformat(),
                                    "end_date": d_end.date().isoformat(), "timezone": "GMT", "temperature_unit": "fahrenheit"})
        for attempt in range(6):          # the proxy drops a TLS handshake now and then: wait and try again, never skip a month
            try:
                with urllib.request.urlopen("https://previous-runs-api.open-meteo.com/v1/forecast?" + q, timeout=45) as r:
                    h = json.load(r)["hourly"]
                break
            except Exception:
                if attempt == 5:
                    raise
                time.sleep(5 * (attempt + 1))
        for t, v in zip(h["time"], h["temperature_2m_previous_day1"]):
            if v is not None:
                out[_iso_utc(t)] = float(v)
        d0 = d_end + timedelta(days=1)
        time.sleep(0.5)
    return out


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(WX_DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS market(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike_type TEXT, floor REAL, cap REAL);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid_c REAL, ask_c REAL, volume REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS forecast(city TEXT, ts INTEGER, temp_f REAL, PRIMARY KEY(city, ts));""")
    have = {r[0] for r in db.execute("SELECT ticker FROM market")}
    now = int(time.time())
    start = (datetime.fromtimestamp(now, timezone.utc) - timedelta(days=DAYS + 2)).strftime("%Y-%m-%d")
    end = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d")
    for series, (name, lat, lon) in CITIES.items():
        fc = fetch_forecast(lat, lon, start, end)
        db.executemany("INSERT OR REPLACE INTO forecast VALUES(?,?,?)", [(series, t, v) for t, v in fc.items()])
        listed = [m for m in api.settled_markets(series, now - DAYS * 86400, now) if m.get("result") in ("yes", "no")]
        by_day: dict = defaultdict(list)
        for m in listed:
            by_day[m["close_time"]].append(m)
        stored = 0
        for close_iso in sorted(by_day):
            ms = [m for m in by_day[close_iso] if m["ticker"] not in have]
            if not ms:
                continue
            close_ts = backfill.iso_ts(close_iso)
            open_ts = min(backfill.iso_ts(m.get("open_time")) or close_ts for m in ms)
            got = api._get("/markets/candlesticks", {"market_tickers": ",".join(m["ticker"] for m in ms), "start_ts": open_ts, "end_ts": close_ts, "period_interval": 60})
            by_t = {x.get("market_ticker"): x.get("candlesticks", []) for x in got.get("markets", [])}
            for m in ms:
                rows = [r for r in (backfill.parse_candle(c, m["ticker"], series) for c in by_t.get(m["ticker"], [])) if r]
                db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?)", [(r[0], r[2], r[6], r[10], r[12]) for r in rows])
                db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?,?)", (m["ticker"], series, backfill.iso_ts(m.get("open_time")), close_ts, m["result"],
                                                                                  m.get("strike_type"), m.get("floor_strike"), m.get("cap_strike")))
                have.add(m["ticker"])
                stored += 1
            db.commit()
            time.sleep(0.4)
        print(f"{series} ({name}): {len(listed)} settled markets, {stored} new, {len(fc)} forecast hours", flush=True)
    print("done", flush=True)


def run() -> None:
    days, fc = load()
    trades, brier = simulate(days, fc)
    n_days = len({t["day"] for t in trades})
    print(f"{sum(len(v) for d in days.values() for v in d.values())} market-days loaded; {len(trades)} trades on {n_days} days; {len(brier)} priced buckets scored. Signal counts first.\n")
    pl = placebo_means(trades) if trades else []
    v, s = verdict(trades, pl)
    f = lambda x: f"{x * 100:+.2f}c"
    if "mean" in s:
        print(f"WX1: n={s['n']} on {s['days']} days, net {f(s['mean'])} per contract, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, fees x{STRESS} {f(s['stress'])}, "
              f"placebo 95th percentile {f(s['p95'])} -> {v}")
        note = "  (FALSIFIED here means NOT SHOWN at this sample size: the minimum detectable edge is above 3c)" if v == "FALSIFIED" and s["mde"] > MDE_FLAG else ""
        print(f"    minimum detectable edge {f(s['mde'])}{note}")
    else:
        print(f"WX1: n={s['n']} on {s['days']} days -> {v}")
    print("\nPer city (information):")
    for series, (name, _, _) in CITIES.items():
        mine = [t for t in trades if t["series"] == series]
        bm = [b for b in brier if b["series"] == series]
        if not bm:
            print(f"  {name:<13} no scored buckets")
            continue
        net = f"{st.mean(t['net'] for t in mine) * 100:+.2f}c" if mine else "n/a"
        print(f"  {name:<13} trades {len(mine):>3} net {net:>8}   Brier model {st.mean(b['model'] for b in bm):.4f} vs market {st.mean(b['market'] for b in bm):.4f} over {len(bm)} buckets")
    if brier:
        print(f"  all           Brier model {st.mean(b['model'] for b in brier):.4f} vs market {st.mean(b['market'] for b in brier):.4f}  (lower is better)")
    print("\nThreshold sensitivity (information only, not tries):")
    for e in SENSITIVITY:
        tr, _ = simulate(days, fc, e)
        print(f"  edge >= {e:.2f}: {len(tr):>4} trades, net {f(st.mean(t['net'] for t in tr)) if tr else 'n/a'}")
    sides = defaultdict(int)
    for t in trades:
        sides[t["side"]] += 1
    print("\nTrades by side:", dict(sides))


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
