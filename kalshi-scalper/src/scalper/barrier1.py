"""BARRIER1: one-touch (max / min this month) markets against a reflection-principle model, held to settlement.

Registered in workers/BARRIER1_REGISTRATION.md before any outcome. Research only: no order, no key, public data.
    python -m scalper.barrier1 fetch    (resumable; cache outside the repo)
    python -m scalper.barrier1 run
"""
from __future__ import annotations

import json
import math
import sys
import time
import urllib.request
from pathlib import Path

from . import api

CACHE = Path("/tmp/claude-0/b1/cache")
SERIES = {  # series -> OKX instrument
    "KXBTCMAXMON": "BTC-USDT", "KXBTCMINMON": "BTC-USDT", "KXETHMAXMON": "ETH-USDT", "KXETHMINMON": "ETH-USDT",
    "KXSOLMAXMON": "SOL-USDT", "KXSOLMINMON": "SOL-USDT", "KXXRPMAXMON": "XRP-USDT", "KXXRPMINMON": "XRP-USDT",
    "KXDOGEMAXMON": "DOGE-USDT", "KXDOGEMINMON": "DOGE-USDT", "KXBNBMAXMON": "BNB-USDT", "KXBNBMINMON": "BNB-USDT",
    "KXHYPEMAXMON": "HYPE-USDT", "KXHYPEMINMON": "HYPE-USDT",
}
LOOK_AFTER_OPEN_S = 48 * 3600
VOL_HOURS = 336
LIMIT = 0.30
LO = 0.03
RATIO = 2.0
FEE_RATE = 0.07


def ncdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2))


def touch_prob(S: float, K: float, sigma_ann: float, T_years: float) -> float | None:
    """Reflection principle, zero drift: P(touch) = min(1, 2 N(-|ln(K/S)| / (sigma sqrt T)))."""
    if S <= 0 or K <= 0 or sigma_ann <= 0 or T_years <= 0:
        return None
    d = abs(math.log(K / S)) / (sigma_ann * math.sqrt(T_years))
    return min(1.0, 2 * ncdf(-d))


def fee_per_contract(price: float, C: int = 10) -> float:
    return math.ceil(FEE_RATE * C * price * (1 - price) * 100 - 1e-9) / 100 / C


def realised_vol(closes: list[float]) -> float | None:
    r = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a > 0 and b > 0]
    if len(r) < VOL_HOURS - 20:
        return None
    r = r[-VOL_HOURS:]
    m = sum(r) / len(r)
    var = sum((x - m) ** 2 for x in r) / (len(r) - 1)
    return math.sqrt(var) * math.sqrt(8760)


def decide(rule: str, yes_ask: float | None, yes_bid: float | None, p: float | None):
    """Return the price paid and the side, or None. rule is 'cheap' (BUY YES) or 'rich' (BUY NO)."""
    if p is None:
        return None
    if rule == "cheap":
        if yes_ask is not None and LO <= yes_ask <= LIMIT and p >= RATIO * yes_ask:
            return ("yes", yes_ask)
    else:
        if yes_bid is not None:
            na = 1 - yes_bid
            if LO <= na <= LIMIT and (1 - p) >= RATIO * na:
                return ("no", na)
    return None


def net_per_contract(side: str, price: float, result: str) -> float:
    won = (result == side)
    return (1 - price if won else -price) - fee_per_contract(price)


def pf(xs: list[float]) -> float | None:
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else (None if g == 0 else float("inf"))


def okx_hourly(inst: str, lo_s: int, hi_s: int) -> dict:
    out, after = {}, hi_s * 1000 + 3600000
    while True:
        u = f"https://www.okx.com/api/v5/market/history-candles?instId={inst}&bar=1H&limit=100&after={after}"
        for i in range(8):
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "barrier1-research/1.0"}), timeout=30))
                break
            except Exception:
                time.sleep(1.5 * (i + 1))
        else:
            raise RuntimeError("OKX failed " + u)
        rows = d.get("data", [])
        if not rows:
            break
        for r in rows:
            out[int(r[0]) // 1000] = float(r[4])
        oldest = int(rows[-1][0])
        if oldest // 1000 <= lo_s:
            break
        after = oldest
        time.sleep(0.15)
    return out


def event_end(ev: str) -> int:
    """Scheduled end of a monthly touch event from its ticker (...-26OCT31 = 11:59 PM ET on 2026-10-31, UTC-4 in Aug to Oct).
    A market that was touched CLOSES EARLY at the touch (close_time of a YES market is the outcome), so close_time must never be the horizon."""
    import datetime as dt
    d = dt.datetime.strptime(ev.rsplit("-", 1)[1], "%y%b%d").replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp()) + 86400 + 4 * 3600


def ts(s: str) -> int:
    import datetime as dt
    return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    mp = CACHE / "markets.json"
    markets = json.loads(mp.read_text()) if mp.exists() else {}
    import os
    only = os.environ.get("BARRIER1_ONLY")        # rate limit: read only the series named (all are registered; the rest stay unread)
    for s in SERIES:
        if s in markets or (only and s not in only.split(",")):
            continue
        r = api._get("/markets", {"series_ticker": s, "limit": 1000, "status": "settled"})
        markets[s] = r.get("markets", [])
        mp.write_text(json.dumps(markets)); print(s, len(markets[s]), flush=True)
        time.sleep(3)
    for inst in sorted({SERIES[s] for s in markets}):
        kp = CACHE / f"h_{inst}.json"
        if not kp.exists():
            k = okx_hourly(inst, ts("2026-06-01T00:00:00Z"), int(time.time()))
            kp.write_text(json.dumps({str(a): b for a, b in k.items()})); print(inst, len(k), flush=True)
    cp = CACHE / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    for s, ms in markets.items():
        byev: dict = {}
        for m in ms:
            if m.get("result") in ("yes", "no"):
                byev.setdefault(m["event_ticker"], []).append(m)
        for ev, mm in byev.items():
            if ev in have:
                continue
            lo = ts(mm[0]["open_time"]) + LOOK_AFTER_OPEN_S
            tks = [m["ticker"] for m in mm][:100]
            d = api._get("/markets/candlesticks", {"market_tickers": ",".join(tks), "start_ts": lo, "end_ts": lo + 3 * 3600, "period_interval": 60})
            have[ev] = {m.get("market_ticker"): m.get("candlesticks", []) for m in d.get("markets", [])}
            cp.write_text(json.dumps(have)); print(ev, len(tks), flush=True)
            time.sleep(3)


def first_quote(cs: list[dict]):
    for c in cs:
        a, b = c.get("yes_ask", {}), c.get("yes_bid", {})
        ak = a.get("close_dollars") or a.get("close"); bk = b.get("close_dollars") or b.get("close")
        try:
            av = float(ak) if ak not in (None, "") else None
            bv = float(bk) if bk not in (None, "") else None
        except ValueError:
            continue
        if av is not None or bv is not None:
            return c.get("end_period_ts"), av, bv
    return None


def build_rows():
    markets = {s: v for s, v in json.loads((CACHE / "markets.json").read_text()).items() if s in SERIES}
    have = json.loads((CACHE / "candles.json").read_text())
    kl = {inst: {int(a): b for a, b in json.loads((CACHE / f"h_{inst}.json").read_text()).items()} for inst in {SERIES[s] for s in markets}}
    rows, drop = [], {}
    for s, ms in markets.items():
        k = kl[SERIES[s]]
        for m in ms:
            if m.get("result") not in ("yes", "no"):
                continue
            st = m.get("strike_type")
            K = m.get("floor_strike") if st == "greater" else m.get("cap_strike") if st == "less" else None
            cs = (have.get(m["event_ticker"]) or {}).get(m["ticker"]) or []
            q = first_quote(cs)
            if K is None or not q:
                drop["no_strike_or_quote"] = drop.get("no_strike_or_quote", 0) + 1
                continue
            t_look, ask, bid = q
            hour = t_look // 3600 * 3600 - 3600
            S = k.get(hour)
            hist = [k[h] for h in range(hour - 3600 * (VOL_HOURS + 5), hour + 1, 3600) if h in k]
            sig = realised_vol(hist)
            if S is None or sig is None:
                drop["no_okx"] = drop.get("no_okx", 0) + 1
                continue
            if (st == "greater" and S >= K) or (st == "less" and S <= K):
                drop["already_crossed"] = drop.get("already_crossed", 0) + 1
                continue
            T = (event_end(m["event_ticker"]) - t_look) / (3600 * 8760)
            p = touch_prob(S, K, sig, T)
            rows.append({"t": m["ticker"], "s": s, "ev": m["event_ticker"], "close": event_end(m["event_ticker"]), "ask": ask, "bid": bid, "p": p, "res": m["result"], "S": S, "K": K, "sig": sig})
    return rows, drop


def run() -> None:
    rows, drop = build_rows()
    rows.sort(key=lambda r: r["close"])
    n = len(rows)
    evs = sorted({r["close"] for r in rows})
    cut = evs[int(len(evs) * 2 / 3)] if len(evs) >= 3 else None
    dev = [r for r in rows if cut is None or r["close"] < cut]
    hold = [r for r in rows if cut is not None and r["close"] >= cut]
    print("markets with model", n, "dropped", drop, "events", len(evs), "holdout_from", cut)
    for rule in ("cheap", "rich"):
        for name, part in (("dev", dev), ("hold", hold)):
            tr = []
            for r in part:
                d = decide(rule, r["ask"], r["bid"], r["p"])
                if d:
                    tr.append((r["close"], d[1], net_per_contract(d[0], d[1], r["res"]), r["res"] == d[0], r["p"]))
            tr.sort()
            h = len(tr) // 2
            xs = [x[2] for x in tr]
            print(rule, name, "n", len(tr), "events", len({x[0] for x in tr}), "win", round(sum(x[3] for x in tr) / len(tr), 3) if tr else None,
                  "price", round(sum(x[1] for x in tr) / len(tr), 3) if tr else None, "model", round(sum(x[4] for x in tr) / len(tr), 3) if tr else None,
                  "net", round(sum(xs) / len(xs), 4) if xs else None, "half1", round(sum(xs[:h]) / max(1, h), 4) if h else None,
                  "half2", round(sum(xs[h:]) / max(1, len(xs) - h), 4) if xs else None, "pf", pf(xs))
    # calibration of the model on all quoted markets (information only)
    for lo, hi in ((0, 0.1), (0.1, 0.3), (0.3, 0.6), (0.6, 1.01)):
        b = [r for r in rows if lo <= r["p"] < hi]
        if b:
            print("model p", lo, hi, "n", len(b), "yes", round(sum(r["res"] == "yes" for r in b) / len(b), 3), "meanp", round(sum(r["p"] for r in b) / len(b), 3),
                  "mean ask", round(sum((r["ask"] or 0) for r in b) / len(b), 3))


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
