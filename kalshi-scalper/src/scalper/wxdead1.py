"""WXDEAD1 (workers/WXDEAD1_REGISTRATION.md): daily temperature brackets already decided by the observed running max or min.
Research only. Usage: python -m scalper.wxdead1 fetch ; python -m scalper.wxdead1 run (refused a second time)
"""
from __future__ import annotations

import calendar
import csv
import hashlib
import io
import json
import math
import sys
import time
import urllib.request
from collections import defaultdict

from . import api
from .paths import DATA_DIR

CACHE = DATA_DIR / "wxdead1_cache.json"
RESULT = DATA_DIR / "wxdead1_result.txt"
CUT = calendar.timegm((2026, 10, 3, 16, 0, 0))
HALF = calendar.timegm((2026, 9, 17, 0, 0, 0))
HIGH = {"KXHIGHNY": "NYC", "KXHIGHCHI": "MDW", "KXHIGHMIA": "MIA", "KXHIGHAUS": "AUS", "KXHIGHDEN": "DEN", "KXHIGHLAX": "LAX",
        "KXHIGHPHIL": "PHL", "KXHIGHTHOU": "HOU", "KXHIGHTDC": "DCA", "KXHIGHTSEA": "SEA", "KXHIGHTATL": "ATL"}
LOW = {"KXLOWTNYC": "NYC", "KXLOWTCHI": "MDW", "KXLOWTMIA": "MIA", "KXLOWTAUS": "AUS", "KXLOWTDEN": "DEN", "KXLOWTLAX": "LAX", "KXLOWTPHIL": "PHL"}
SERIES = {**{s: ("high", st) for s, st in HIGH.items()}, **{s: ("low", st) for s, st in LOW.items()}}
Z_BAR = 5.27
FETCH_MINUTES = 90


def ts(s: str) -> int:
    return calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))


def fmt(t):
    return time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(t))


def fetch_obs(station, lo, hi):
    rows = []
    t0 = lo
    while t0 < hi:
        t1 = min(t0 + 8 * 86400, hi)
        url = f"https://mesonet.agron.iastate.edu/cgi-bin/request/asos1min.py?station={station}&vars=tmpf&sts={fmt(t0)}&ets={fmt(t1)}&sample=1min&what=download&tz=UTC"
        txt = urllib.request.urlopen(url, timeout=120).read().decode()
        for r in csv.DictReader(io.StringIO(txt)):
            try:
                rows.append([ts(r["valid(UTC)"].replace(" ", "T") + ":00"), float(r["tmpf"])])
            except (ValueError, KeyError):
                pass
        t0 = t1
    return rows


def fetch() -> None:
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {"markets": {}, "obs": {}, "candles": {}, "fetched": []}
    if not cache["markets"]:
        for s in SERIES:
            ms = [m for m in api.settled_markets(s, 0, CUT) if ts(m["close_time"]) < CUT]
            cache["markets"][s] = [{k: m.get(k) for k in ("ticker", "event_ticker", "close_time", "floor_strike", "cap_strike", "strike_type", "result", "expiration_value")} for m in ms]
            print(s, len(ms), "markets", flush=True)
        CACHE.write_text(json.dumps(cache))
    for st in sorted({v[1] for v in SERIES.values()}):
        if st in cache["obs"]:
            continue
        allc = [ts(m["close_time"]) for s, ms in cache["markets"].items() if SERIES[s][1] == st for m in ms]
        cache["obs"][st] = fetch_obs(st, min(allc) - 86400 - 3600, max(allc) + 3600)
        print(st, len(cache["obs"][st]), "obs", flush=True)
        CACHE.write_text(json.dumps(cache))
    evs = {}
    for s, ms in cache["markets"].items():
        for m in ms:
            evs.setdefault(m["event_ticker"], []).append(m)
    order = sorted(evs, key=lambda e: hashlib.md5(e.encode()).hexdigest())
    done = set(cache["fetched"])
    deadline = time.time() + FETCH_MINUTES * 60
    for i, e in enumerate(order):
        if e in done:
            continue
        if time.time() > deadline:
            print("time box reached; fetched", len(cache["fetched"]), "of", len(order), flush=True)
            break
        c = ts(evs[e][0]["close_time"])
        try:
            d = api._get("/markets/candlesticks", {"market_tickers": ",".join(m["ticker"] for m in evs[e]), "start_ts": c - 129600, "end_ts": c, "period_interval": 60})
        except Exception as ex:  # noqa: BLE001
            print("skip", e, ex, flush=True)
            continue
        for m in d.get("markets", []):
            cache["candles"][m["market_ticker"]] = [[x["end_period_ts"], api.f((x.get("yes_bid") or {}).get("close_dollars")), api.f((x.get("yes_ask") or {}).get("close_dollars")), api.f(x.get("volume_fp"))] for x in m.get("candlesticks", [])]
        cache["fetched"].append(e)
        time.sleep(0.5)
        if len(cache["fetched"]) % 25 == 0:
            print("events", len(cache["fetched"]), "of", len(order), flush=True)
            CACHE.write_text(json.dumps(cache))
    CACHE.write_text(json.dumps(cache))


def fee(p, mult=1.0):
    return math.ceil(round(0.07 * 10 * p * (1 - p) * 100, 6) * mult - 1e-9) / 100 / 10 * 1.0 if False else math.ceil(0.07 * 10 * p * (1 - p) * mult * 100 - 1e-9) / 100 / 10


def status(kind, m, ext):
    """'dead', 'won' or None for a bracket given the running max (high) or min (low) ext, in integers."""
    st, F, C = m["strike_type"], m["floor_strike"], m["cap_strike"]
    if kind == "high":
        if st == "less":
            return "dead" if ext >= C else None
        if st == "between":
            return "dead" if ext >= C + 1 else None   # for "between a b" cap_strike is the top integer b
        if st == "greater":
            return "won" if ext >= F + 1 else None
    else:
        if st == "greater":
            return "dead" if ext <= F else None
        if st == "between":
            return "dead" if ext <= F - 1 else None   # floor_strike is the bottom integer a
        if st == "less":
            return "won" if ext <= C - 1 else None
    return None


def trades(cache, margin=0):
    out = []
    for s, ms in cache["markets"].items():
        kind, st = SERIES[s]
        obs = cache["obs"].get(st, [])
        if not obs:
            continue
        ot = [r[0] for r in obs]
        import bisect
        evs = defaultdict(list)
        for m in ms:
            if m["ticker"] in cache["candles"]:
                evs[m["event_ticker"]].append(m)
        for e, mk in evs.items():
            close = ts(mk[0]["close_time"])
            day0 = close - 86400
            seen = set()
            looks = sorted({x[0] for m in mk for x in cache["candles"][m["ticker"]] if 8 * 3600 <= x[0] - day0 <= 23 * 3600})
            for t in looks:
                cut = t - 900
                a, b = bisect.bisect_left(ot, day0), bisect.bisect_right(ot, cut)
                if b <= a:
                    continue
                vals = [obs[i][1] for i in range(a, b)]
                ext = round(max(vals)) if kind == "high" else round(min(vals))
                for m in mk:
                    if m["ticker"] in seen:
                        continue
                    stt = status(kind, m, ext + (margin if kind == "high" else -margin) * (1 if stt_is(m) else 1)) if False else status(kind, m, ext + margin if kind == "high" else ext - margin)
                    if stt is None:
                        continue
                    c = next((x for x in cache["candles"][m["ticker"]] if x[0] == t), None)
                    if not c:
                        continue
                    bid, ask, vol = c[1], c[2], c[3] or 0
                    yes = m["result"] == "yes"
                    if stt == "dead" and bid is not None and bid >= 0.03:
                        p = round(1 - bid, 4)
                        pay = 0 if yes else 1
                        out.append(dict(side="A", series=s, event=e, close=close, t=t, p=p, vol=vol, pay=pay, tk=m["ticker"]))
                        seen.add(m["ticker"])
                    elif stt == "won" and ask is not None and ask <= 0.97 and ask > 0:
                        pay = 1 if yes else 0
                        out.append(dict(side="B", series=s, event=e, close=close, t=t, p=ask, vol=vol, pay=pay, tk=m["ticker"]))
                        seen.add(m["ticker"])
    return out


def stats(tr, mult=1.0):
    if not tr:
        return None
    net = [100 * (x["pay"] - x["p"] - fee(x["p"], mult)) for x in tr]
    n = len(net)
    mean = sum(net) / n
    ev = defaultdict(float)
    for x, v in zip(tr, net):
        ev[x["event"]] += v
    k = len(ev)
    vals = list(ev.values())
    mu = sum(vals) / k
    var = sum((v - mu) ** 2 for v in vals) / max(k - 1, 1)
    z = (mu / math.sqrt(var / k)) if var > 0 else (float("inf") if mu > 0 else 0.0)
    gains = sum(v for v in net if v > 0)
    losses = -sum(v for v in net if v < 0)
    return dict(n=n, events=k, mean=round(mean, 3), pf=("inf" if losses == 0 else round(gains / losses, 2)), z=round(z, 2),
                viol=sum(1 for x in tr if x["pay"] == 0), win=round(sum(x["pay"] for x in tr) / n, 4))


def run() -> None:
    if RESULT.exists():
        print("refused: WXDEAD1 already run; see", RESULT)
        return
    cache = json.loads(CACHE.read_text())
    lines = []
    allt = trades(cache)
    fetched = len(cache["fetched"])
    totev = len({m["event_ticker"] for ms in cache["markets"].values() for m in ms})
    lines.append(f"events fetched {fetched} of {totev}; obs stations: " + ", ".join(f"{k}={len(v)}" for k, v in cache["obs"].items()))
    for side in "AB":
        tr = [x for x in allt if x["side"] == side]
        lines.append(f"TRY {side} pooled {stats(tr)}")
        lines.append(f"TRY {side} fees x1.2 {stats(tr, 1.2)}")
        lines.append(f"TRY {side} D1 {stats([x for x in tr if x['close'] < HALF])}")
        lines.append(f"TRY {side} D2 {stats([x for x in tr if x['close'] >= HALF])}")
        lines.append(f"TRY {side} volume>=10 (info) {stats([x for x in tr if x['vol'] >= 10])}")
        lines.append(f"TRY {side} high-day (info) {stats([x for x in tr if SERIES[x['series']][0] == 'high'])}")
        lines.append(f"TRY {side} low-day (info) {stats([x for x in tr if SERIES[x['series']][0] == 'low'])}")
        lines.append(f"TRY {side} margin 1 (info) {stats([x for x in trades(cache, 1) if x['side'] == side])}")
        byp = defaultdict(int)
        for x in tr:
            byp[round(x["p"], 2)] += 1
        lines.append(f"TRY {side} price histogram (p: n) " + str(sorted(byp.items())))
        lines.append(f"TRY {side} violators " + str([(x['tk'], x['p']) for x in tr if x['pay'] == 0][:20]))
    txt = "\n".join(lines)
    RESULT.write_text(txt)
    print(txt)


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
