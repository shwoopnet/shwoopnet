"""IV1 (README, Pre-registration: IV1): option-style fair value for the Bitcoin and Ethereum 15 minute markets using Deribit's
implied volatility index (DVOL) as sigma. Research only: nothing here places an order. Verdict words: FALSIFIED,
NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

    python -m scalper.iv1 fetch     (Deribit perpetual 1 minute bars and DVOL into data/iv1.sqlite; resumable)
    python -m scalper.iv1 run       (the one read)
"""
from __future__ import annotations

import json
import math
import sqlite3
import statistics as st
import sys
import time
import urllib.request

from . import lstrats as L
from .calibration import cluster_mean_z
from .paths import DATA_DIR

DB = DATA_DIR / "iv1.sqlite"
SERIES = {"KXBTC15M": ("BTC-PERPETUAL", "BTC"), "KXETH15M": ("ETH-PERPETUAL", "ETH")}
LEFT_S = 360
TAU = 5.0 + 1.0 / 3.0            # five minutes before the last minute begins, plus the averaging minute
MARGIN = 0.02
MIN_N = 300
MIN_PER_YEAR = 525_600.0
BAR_S = 60                       # a bar stamped T closes at T + BAR_S


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def p_yes(spot: float, strike: float, sigma_annual_pct: float) -> float | None:
    """P(settlement average above the strike) with a per minute sigma from an annualised percent; None on bad inputs."""
    if not spot or not strike or spot <= 0 or strike <= 0 or not sigma_annual_pct or sigma_annual_pct <= 0:
        return None
    s = (sigma_annual_pct / 100.0) / math.sqrt(MIN_PER_YEAR)
    return phi(math.log(spot / strike) / (s * math.sqrt(TAU)))


def p_yes_realised(closes: list[float], strike: float) -> float | None:
    """Same model with sigma the sample standard deviation of the log returns of the 61 closes given (oldest first)."""
    if len(closes) != 61 or any(not c or c <= 0 for c in closes) or not strike or strike <= 0:
        return None
    r = [math.log(b / a) for a, b in zip(closes, closes[1:])]
    sd = st.stdev(r)
    if sd <= 0:
        return None
    return phi(math.log(closes[-1] / strike) / (sd * math.sqrt(TAU)))


def fee(p: float) -> float:
    return 0.07 * p * (1 - p)


def decide(p: float | None, bid: float, ask: float) -> tuple[str, float] | None:
    """Buy the side whose model edge net of its fee exceeds MARGIN; a one sided or crossed book trades nothing."""
    if p is None or not (0 < bid < ask < 1):
        return None
    ev_yes = p - ask - fee(ask)
    no_price = round(1 - bid, 4)
    ev_no = (1 - p) - no_price - fee(no_price)
    best = max((ev_yes, "yes", ask), (ev_no, "no", no_price))
    return (best[1], best[2]) if best[0] > MARGIN else None


def _get(url: str):
    for k in range(5):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 ** k)
    raise RuntimeError("fetch failed: " + url)


def fetch(days: int = 80) -> None:
    con = sqlite3.connect(DB)
    con.execute("create table if not exists bar(inst text, ts integer, close real, primary key(inst, ts))")
    con.execute("create table if not exists dvol(cur text, ts integer, close real, primary key(cur, ts))")
    end = int(time.time()) * 1000
    start0 = end - days * 86_400_000
    for inst, cur in SERIES.values():
        for table, key, name in (("bar", "inst", inst), ("dvol", "cur", cur)):
            have = con.execute(f"select max(ts) from {table} where {key}=?", (name,)).fetchone()[0]
            t = (have + 60_000) if have else start0
            while t < end:
                t2 = min(end, t + (4_000 if table == "bar" else 900) * 60_000)   # DVOL returns at most 1000 points a call
                if table == "bar":
                    u = f"https://www.deribit.com/api/v2/public/get_tradingview_chart_data?instrument_name={inst}&start_timestamp={t}&end_timestamp={t2}&resolution=1"
                    d = _get(u)["result"]
                    rows = list(zip(d["ticks"], d["close"]))
                else:
                    u = f"https://www.deribit.com/api/v2/public/get_volatility_index_data?currency={cur}&start_timestamp={t}&end_timestamp={t2}&resolution=60"
                    d = _get(u)["result"]["data"]
                    rows = [(x[0], x[4]) for x in d]
                con.executemany(f"insert or ignore into {table} values (?,?,?)", [(name, int(a), float(b)) for a, b in rows])
                con.commit()
                t = t2 + 60_000
            print(name, table, con.execute(f"select count(*) from {table} where {key}=?", (name,)).fetchone()[0], flush=True)


def _series(con, table, key, name):
    return {ts // 1000: c for ts, c in con.execute(f"select ts, close from {table} where {key}=?", (name,))}


def observations(markets: list[tuple], bars: dict, dvol: dict) -> list[dict]:
    out = []
    for ticker, series, candles, close_ts, res in markets:
        if series not in SERIES or res not in ("yes", "no"):
            continue
        t = close_ts - LEFT_S
        c = next((x for x in candles if x[0] == t), None)
        if c is None or c[1] is None or c[2] is None:
            continue
        b = bars[series]
        # Deribit stamps a bar with its START; its close is known one minute later. The Kalshi candle ends at t, so the last
        # bar usable at t starts at t - 60 (the first read of IV1 used the bar starting at t and saw one minute of the future).
        open_t = close_ts - 900 - BAR_S
        K, S = b.get(open_t), b.get(t - BAR_S)
        win = [b.get(t - BAR_S - 60 * k) for k in range(60, -1, -1)]
        dv = dvol[series].get(t - BAR_S)
        if not K or not S or dv is None or any(x is None for x in win):
            continue
        out.append({"ticker": ticker, "series": series, "close_ts": close_ts, "day": L._day(close_ts), "bid": c[1], "ask": c[2],
                    "yes": res == "yes", "p_iv": p_yes(S, K, dv), "p_rv": p_yes_realised(win, K)})
    return sorted(out, key=lambda o: o["close_ts"])


def run_entries(obs: list[dict], key: str, mult: float = 1.0) -> list[dict]:
    out = []
    for o in obs:
        d = decide(o[key], o["bid"], o["ask"])
        if d is None:
            continue
        side, price = d
        out.append({**o, "side": side, "price": price, "net": L.net(side, price, o["yes"], mult)})
    return out


def judge(entries: list[dict]) -> tuple[str, dict]:
    if len(entries) < MIN_N:
        return "NOT_ENOUGH_DATA", {"n": len(entries)}
    m, _, z = cluster_mean_z([(e["day"], e["net"]) for e in entries])
    half = len(entries) // 2
    h1 = st.mean(e["net"] for e in entries[:half])
    h2 = st.mean(e["net"] for e in entries[half:])
    stress = st.mean(L.net(e["side"], e["price"], e["yes"], L.STRESS) for e in entries)
    ok = m > 0 and z >= 2.1 and h1 > 0 and h2 > 0 and stress > 0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": len(entries), "net_c": 100 * m, "z": z, "h1_c": 100 * h1, "h2_c": 100 * h2, "stress_c": 100 * stress}


def brier(obs: list[dict], f) -> float:
    v = [(f(o) - (1.0 if o["yes"] else 0.0)) ** 2 for o in obs if f(o) is not None]
    return sum(v) / len(v)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
        return
    if cmd != "run":
        print(__doc__)
        return
    from .fwd_reads import load_fresh
    from .hs1 import load
    mk = {m[0]: m for m in load() + load_fresh()}
    con = sqlite3.connect(DB)
    bars = {s: _series(con, "bar", "inst", i) for s, (i, _) in SERIES.items()}
    dvol = {s: _series(con, "dvol", "cur", c) for s, (_, c) in SERIES.items()}
    for s in SERIES:
        obs = observations([m for m in mk.values() if m[1] == s], bars, dvol)
        both = [o for o in obs if o["p_iv"] is not None and o["p_rv"] is not None]
        print(s, "observations", len(obs), "with both models", len(both))
        mid = lambda o: 0.5 * (o["bid"] + o["ask"])
        print("  Brier  p_iv %.4f  p_rv %.4f  market mid %.4f" % (brier(both, lambda o: o["p_iv"]), brier(both, lambda o: o["p_rv"]), brier(both, mid)))
        v, d = judge(run_entries(obs, "p_iv"))
        print("  IV1", v, {k: round(x, 2) for k, x in d.items()})
        v2, d2 = judge(run_entries(obs, "p_rv"))
        print("  information only, realised sigma:", v2, {k: round(x, 2) for k, x in d2.items()})


if __name__ == "__main__":
    main()
