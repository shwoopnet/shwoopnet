"""PUB1 (README, Pre-registration: GAS1, APP1 and CMD1): daily ladders on a published number or a spot price, one walk-forward model each.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

History goes into its OWN database (`data/pub1.sqlite`): settled markets with their published value, hourly bid and ask candles, and Yahoo's 5 minute spot bars for
the commodity series. The rules are in the README ("Pre-registration: GAS1, APP1 and CMD1") and were written before `run` existed. Each strategy is run ONCE: a result
file is written next to the data and a second run is refused unless it is deleted on purpose (a fix to a crash, never a chase for a pass).
Usage: python -m scalper.pub1 fetch   then   python -m scalper.pub1 run GAS1|APP1|CMD1
"""
from __future__ import annotations

import bisect
import json
import math
import sqlite3
import statistics as st
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

from . import api, backfill
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalps import STRESS, fee
from .wx1 import EDGE, ncdf, pick_trade, placebo_means, valid

PUB_DB = DATA_DIR / "pub1.sqlite"
DAYS = 69
GAS = "KXAAAGASD"
APPROVE = "KXTRUMPAPPROVE"
# series -> Yahoo symbol for the spot price the market settles near (a proxy, not the settlement source itself)
COMMODITIES = {"KXBRENTD": "BZ=F", "KXWTI": "CL=F", "KXGOLDD": "GC=F", "KXSILVERD": "SI=F", "KXNATGASD": "NG=F", "KXCOPPERD": "HG=F"}
SERIES = [GAS, APPROVE] + list(COMMODITIES)


def fetch_spot(symbol: str) -> list[tuple[int, float]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=60d"
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                res = json.load(r)["chart"]["result"][0]
            break
        except Exception:
            if attempt == 5:
                raise
            time.sleep(5 * (attempt + 1))
    closes = res["indicators"]["quote"][0]["close"]
    return [(int(t), float(c)) for t, c in zip(res["timestamp"], closes) if c is not None]


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(PUB_DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS market(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike_type TEXT, floor REAL, cap REAL, value TEXT, volume REAL);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid_c REAL, ask_c REAL, volume REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS spot(symbol TEXT, ts INTEGER, close REAL, PRIMARY KEY(symbol, ts));""")
    have = {r[0] for r in db.execute("SELECT ticker FROM market")}
    now = int(time.time())
    for series, sym in COMMODITIES.items():
        rows = fetch_spot(sym)
        db.executemany("INSERT OR REPLACE INTO spot VALUES(?,?,?)", [(sym, t, c) for t, c in rows])
        db.commit()
        print(f"spot {sym}: {len(rows)} bars", flush=True)
    for series in SERIES:
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
            open_ts = max(min(backfill.iso_ts(m.get("open_time")) or close_ts for m in ms), close_ts - 3 * 86400)
            for i in range(0, len(ms), 100):
                chunk = ms[i:i + 100]
                got = api._get("/markets/candlesticks", {"market_tickers": ",".join(m["ticker"] for m in chunk), "start_ts": open_ts, "end_ts": close_ts, "period_interval": 60})
                by_t = {x.get("market_ticker"): x.get("candlesticks", []) for x in got.get("markets", [])}
                for m in chunk:
                    rows = [r for r in (backfill.parse_candle(c, m["ticker"], series) for c in by_t.get(m["ticker"], [])) if r]
                    db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?)", [(r[0], r[2], r[6], r[10], r[12]) for r in rows])
                    db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?,?,?,?)", (m["ticker"], series, backfill.iso_ts(m.get("open_time")), close_ts, m["result"],
                                                                                         m.get("strike_type"), m.get("floor_strike"), m.get("cap_strike"),
                                                                                         m.get("expiration_value"), api.f(m.get("volume_fp"))))
                    have.add(m["ticker"])
                    stored += 1
            db.commit()
            time.sleep(0.3)
        print(f"{series}: {len(listed)} settled markets, {stored} new", flush=True)
    print("done", flush=True)


# ---------------------------------------------------------------- the registered rules
DAY_S = 86400
MIN_TRADES = 100
MIN_DAYS = 25
Z_BAR = 2.4                     # 2.1 with a step for three tries
MDE_FLAG = 0.03
SENSITIVITY = (0.0, 0.02, 0.03, 0.05)
SIGMA_FLOOR_GAS = 0.0010        # a tenth of a cent
SIGMA_FLOOR_APP = 0.15
VOL_BARS = 2000
BASIS_DAYS = 10
MIN_BASIS = 5
GAP_S = 900


def num(x) -> float | None:
    try:
        return float(str(x).replace("%", "").replace("$", "").replace(",", "")) if x not in (None, "") else None
    except ValueError:
        return None


def load():
    """(by_series {series: {close_ts: [market dicts]}}, spot {symbol: ([ts], [close])})."""
    db = sqlite3.connect(PUB_DB)
    quotes: dict = defaultdict(dict)
    for t, end, bc, ac, v in db.execute("SELECT ticker, end_ts, bid_c, ask_c, volume FROM candle"):
        quotes[t][end] = (bc, ac, v)
    by: dict = defaultdict(lambda: defaultdict(list))
    for t, s, close_ts, res, stype, fl, cp, val in db.execute("SELECT ticker, series, close_ts, result, strike_type, floor, cap, value FROM market"):
        by[s][close_ts].append({"ticker": t, "result": res, "type": stype, "floor": fl, "cap": cp, "value": num(val), "q": quotes.get(t, {})})
    spot: dict = {}
    for sym in {r[0] for r in db.execute("SELECT DISTINCT symbol FROM spot")}:
        rows = sorted(db.execute("SELECT ts, close FROM spot WHERE symbol=?", (sym,)))
        spot[sym] = ([r[0] for r in rows], [r[1] for r in rows])
    return by, spot


def day_value(markets: list[dict]) -> float | None:
    vals = {m["value"] for m in markets if m["value"] is not None}
    return vals.pop() if len(vals) == 1 else None


def consecutive_values(by_close: dict, c: int, need: int) -> list[float] | None:
    """The `need` most recent daily values before close c, oldest first, each event a day (plus or minus an hour) after the one before it and the last one a day
    before c; None if the run is broken or a value is missing. Every one of them closed a day or more before c, so all are published before the decision."""
    vals, cur = [], c
    closes = sorted(by_close)
    i = closes.index(c)
    while len(vals) < need:
        if i == 0:
            return None
        prev = closes[i - 1]
        if abs((cur - prev) - DAY_S) > 3600:
            return None
        v = day_value(by_close[prev])
        if v is None:
            return None
        vals.append(v)
        cur, i = prev, i - 1
    return vals[::-1]


def entry_end(c: int, entry_left: int) -> int:
    """The hourly candle that ends at or just before close - ENTRY_LEFT (closes sit at :59 or :00, candles end on the hour)."""
    return ((c - entry_left) // 3600) * 3600


def score(trades: list[dict], brier: list[dict], b: dict, c: int, series: str, p: float, side_q, edge: float) -> None:
    q = side_q
    yes = b["result"] == "yes"
    mid = (q[0] + q[1]) / 2.0
    brier.append({"series": series, "close_ts": c, "model": (p - (1.0 if yes else 0.0)) ** 2, "market": (mid - (1.0 if yes else 0.0)) ** 2})
    pk = pick_trade(p, q[0], q[1], edge)
    if pk is None:
        return
    side, price, e = pk
    won = yes if side == "yes" else (not yes)
    trades.append({"series": series, "close_ts": c, "day": datetime.fromtimestamp(c, timezone.utc).strftime("%Y-%m-%d"), "side": side, "price": price,
                   "net": (1.0 if won else 0.0) - price - fee(price), "stress": (1.0 if won else 0.0) - price - fee(price, STRESS),
                   "mid": mid if side == "yes" else 1.0 - mid})


def simulate_gas(by: dict, edge: float = EDGE):
    trades, brier = [], []
    by_close = by.get(GAS, {})
    for c in sorted(by_close):
        vals = consecutive_values(by_close, c, 21)
        if vals is None:
            continue
        dv = [vals[i] - vals[i - 1] for i in range(1, len(vals))]
        errs = [dv[i] - st.mean(dv[i - 3:i]) for i in range(3, len(dv))][-20:]
        if len(errs) < 10:
            continue
        sigma = max(st.pstdev(errs), SIGMA_FLOOR_GAS)
        mu = vals[-1] + st.mean(dv[-3:])
        ee = entry_end(c, 7 * 3600)
        assert ee > c - 8 * 3600
        for b in by_close[c]:
            q = b["q"].get(ee)
            if b["type"] != "greater" or b["floor"] is None or b["result"] not in ("yes", "no") or q is None or not valid(q[0], q[1]):
                continue
            p = 1.0 - ncdf((b["floor"] - mu) / sigma)
            score(trades, brier, b, c, GAS, p, q, edge)
    return sorted(trades, key=lambda t: t["close_ts"]), brier


def app_range(b: dict) -> tuple[float, float] | None:
    f, cp, t = b["floor"], b["cap"], b["type"]
    if t == "between" and f is not None and cp is not None and abs(f - cp) < 1e-9:
        return (f - 0.05, f + 0.05)
    if t == "less" and cp is not None:
        return (-1e9, cp - 0.05)
    if t == "greater" and f is not None:
        return (f + 0.05, 1e9)
    return None


def simulate_app(by: dict, edge: float = EDGE):
    trades, brier = [], []
    by_close = by.get(APPROVE, {})
    for c in sorted(by_close):
        vals = consecutive_values(by_close, c, 21)
        if vals is None:
            continue
        dv = [vals[i] - vals[i - 1] for i in range(1, len(vals))][-20:]
        sigma = max(st.pstdev(dv), SIGMA_FLOOR_APP)
        mu = vals[-1]
        ee = entry_end(c, 19 * 3600)
        assert ee > c - 20 * 3600
        for b in by_close[c]:
            q = b["q"].get(ee)
            rng = app_range(b)
            if rng is None or b["result"] not in ("yes", "no") or q is None or not valid(q[0], q[1]):
                continue
            lo, hi = rng
            p = (1.0 if hi >= 1e8 else ncdf((hi - mu) / sigma)) - (0.0 if lo <= -1e8 else ncdf((lo - mu) / sigma))
            score(trades, brier, b, c, APPROVE, max(0.0, min(1.0, p)), q, edge)
    return sorted(trades, key=lambda t: t["close_ts"]), brier


def spot_at(sp: tuple, t: int) -> tuple[int, float] | None:
    """The last 5 minute bar that ENDED at or before t: (its end, its close)."""
    ts, cl = sp
    i = bisect.bisect_right(ts, t - 300) - 1
    return (ts[i] + 300, cl[i]) if i >= 0 else None


def vol5(sp: tuple, t: int) -> float | None:
    ts, cl = sp
    j = bisect.bisect_right(ts, t - 300)          # exclusive end: bars that ended by t
    i = max(1, j - VOL_BARS)
    rets = [math.log(cl[k] / cl[k - 1]) for k in range(i, j) if ts[k] - ts[k - 1] <= GAP_S and cl[k] > 0 and cl[k - 1] > 0]
    return st.pstdev(rets) if len(rets) >= 200 else None


def simulate_cmd(by: dict, spot: dict, edge: float = EDGE):
    trades, brier = [], []
    for series, sym in COMMODITIES.items():
        by_close = by.get(series, {})
        sp = spot.get(sym)
        if not by_close or not sp:
            continue
        closes = sorted(by_close)
        for c in closes:
            dec = c - 3 * 3600
            ee = entry_end(c, 2 * 3600)
            assert ee > dec
            base = []
            for k in closes:
                if k <= dec:
                    v = day_value(by_close[k])
                    s_k = spot_at(sp, k)
                    if v is not None and s_k is not None and k - s_k[0] <= 1800:
                        base.append(v - s_k[1])
            base = base[-BASIS_DAYS:]
            now = spot_at(sp, dec)
            vol = vol5(sp, dec)
            if len(base) < MIN_BASIS or now is None or vol is None or vol <= 0 or dec - now[0] > 1800:
                continue
            centre = now[1] + st.median(base)
            n = max(1.0, (c - now[0]) / 300.0)
            sd = vol * math.sqrt(n)
            if centre <= 0:
                continue
            for b in by_close[c]:
                q = b["q"].get(ee)
                if b["type"] not in ("greater", "less") or b["result"] not in ("yes", "no") or q is None or not valid(q[0], q[1]):
                    continue
                k = b["floor"] if b["type"] == "greater" else b["cap"]
                if k is None or k <= 0:
                    continue
                z = math.log(k / centre) / sd
                p = 1.0 - ncdf(z) if b["type"] == "greater" else ncdf(z)
                score(trades, brier, b, c, series, p, q, edge)
    return sorted(trades, key=lambda t: t["close_ts"]), brier


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


def run(name: str) -> None:
    out = DATA_DIR / f"pub1_result_{name}.txt"
    if out.exists():
        sys.exit(f"{name} has been run once already ({out}). A second read is only for a crash fix, and the file is deleted on purpose first.")
    by, spot = load()
    sim = {"GAS1": lambda e: simulate_gas(by, e), "APP1": lambda e: simulate_app(by, e), "CMD1": lambda e: simulate_cmd(by, spot, e)}[name]
    trades, brier = sim(EDGE)
    lines = []
    f = lambda x: f"{x * 100:+.2f}c"
    pl = placebo_means(trades) if trades else []
    v, s = verdict(trades, pl)
    lines.append(f"{name}: {len(trades)} entries from {len(brier)} scored buckets on {len({t['day'] for t in trades})} days.")
    if "mean" in s:
        lines.append(f"{name}: n={s['n']} on {s['days']} days, net {f(s['mean'])} per contract, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, fees x{STRESS} {f(s['stress'])}, "
                     f"placebo 95th percentile {f(s['p95'])} -> {v}")
        note = "  (FALSIFIED here means NOT SHOWN at this sample size: the minimum detectable edge is above 3c)" if v == "FALSIFIED" and s["mde"] > MDE_FLAG else ""
        lines.append(f"    minimum detectable edge {f(s['mde'])}{note}")
    else:
        lines.append(f"{name}: n={s['n']} on {s['days']} days -> {v}")
    if brier:
        lines.append(f"Information: Brier model {st.mean(b['model'] for b in brier):.4f} vs market {st.mean(b['market'] for b in brier):.4f} over {len(brier)} buckets (lower is better)")
    sides = defaultdict(int)
    for t in trades:
        sides[t["side"]] += 1
    lines.append(f"Trades by side: {dict(sides)}")
    if name == "CMD1":
        lines.append("Per series (information):")
        for series in COMMODITIES:
            mine = [t for t in trades if t["series"] == series]
            bm = [b for b in brier if b["series"] == series]
            if bm:
                lines.append(f"  {series:<10} entries {len(mine):>4} net {f(st.mean(t['net'] for t in mine)) if mine else 'n/a':>8}   Brier model {st.mean(b['model'] for b in bm):.4f} vs market {st.mean(b['market'] for b in bm):.4f} over {len(bm)}")
    lines.append("Threshold sensitivity (information only, not tries):")
    for e in SENSITIVITY:
        tr, _ = sim(e)
        lines.append(f"  edge >= {e:.2f}: {len(tr):>4} entries, net {f(st.mean(t['net'] for t in tr)) if tr else 'n/a'}")
    text = "\n".join(lines)
    print(text)
    out.write_text(text + "\n")


if __name__ == "__main__":
    if sys.argv[1:2] == ["fetch"]:
        fetch()
    elif sys.argv[1:2] == ["run"] and sys.argv[2:3] and sys.argv[2] in ("GAS1", "APP1", "CMD1"):
        run(sys.argv[2])
    else:
        sys.exit("usage: python -m scalper.pub1 fetch | run GAS1|APP1|CMD1")
