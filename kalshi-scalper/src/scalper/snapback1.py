"""SNAPBACK1: fade a liquidation-style 1 hour move on Kalshi perpetuals BTC and ETH (research only, discovery, registered 2026-11-03).

Rule and grid are in workers/SNAPBACK1_REGISTRATION.md and README.md; nothing here may change after the first outcome.
    python -m scalper.snapback1 fetch      download 1 minute candles to CACHE (outside the repo)
    python -m scalper.snapback1 run        development window only (first two thirds); the frozen third is never touched
    python -m scalper.snapback1 frozen     refuses unless a cell survived development (see run output file)
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

CACHE = "/tmp/claude-0/cache"
HOST = "https://external-api.kalshi.com/trade-api/v2"
MARKETS = ["KXBTCPERP", "KXETHPERP"]
FEE_SIDE_BP = 12.0
FUND_BP = 1.0            # assumed, against the position, per funding time crossed (00, 08, 16 UTC)
FUND_PERIOD = 8 * 3600
STOP_ATR = 0.5
TIME_STOP_MIN = 360
COOLDOWN_MIN = 360
GRID = [(k, x, t) for k in (2, 3) for x in (0.02, 0.05) for t in (2, 3)]
Z_BAR = 5.27
PF_BAR = 1.5
MIN_N = 40


def fetch(markets=MARKETS):
    import urllib.request
    os.makedirs(CACHE, exist_ok=True)
    end = 1793730000
    start = 1780498800 - 3600
    for tk in markets:
        out = os.path.join(CACHE, tk + "_1m.jsonl")
        seen = set()
        if os.path.exists(out):
            seen = {json.loads(l)["end_period_ts"] for l in open(out)}
        f = open(out, "a")
        s = start
        while s < end:
            e = min(s + 4900 * 60, end)
            url = "%s/margin/markets/%s/candlesticks?period_interval=1&start_ts=%d&end_ts=%d" % (HOST, tk, s, e)
            for i in range(8):
                try:
                    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "shwoopnet-research"}), timeout=40))
                    break
                except Exception:
                    time.sleep(3 * (i + 1))
            else:
                raise SystemExit("fetch failed " + url)
            for c in d.get("candlesticks", []):
                if c["end_period_ts"] not in seen:
                    seen.add(c["end_period_ts"])
                    f.write(json.dumps(c) + "\n")
            s = e
            time.sleep(0.8)


def grid_from_candles(candles):
    """candles: dicts as the API returns. Returns (t0, o, h, l, c, oi): per-minute lists on a regular grid, minute i starts at t0 + 60 i.
    A minute with no trade price carries the previous close (open=high=low=close); a missing minute is the same; OI carries forward."""
    cs = sorted(candles, key=lambda c: c["end_period_ts"])
    first = cs[0]["end_period_ts"] - 60
    last = cs[-1]["end_period_ts"] - 60
    n = (last - first) // 60 + 1
    o = [None] * n; h = [None] * n; l = [None] * n; c = [None] * n; oi = [None] * n
    for k in cs:
        i = (k["end_period_ts"] - 60 - first) // 60
        p = k["price"]
        if p.get("open") is not None and p.get("close") is not None:
            o[i], h[i], l[i], c[i] = float(p["open"]), float(p["high"]), float(p["low"]), float(p["close"])
        if k.get("open_interest") is not None:
            oi[i] = float(k["open_interest"])
    prev_c = None
    prev_oi = None
    for i in range(n):
        if c[i] is None:
            if prev_c is None:
                continue
            o[i] = h[i] = l[i] = c[i] = prev_c
        prev_c = c[i]
        if oi[i] is None:
            oi[i] = prev_oi
        prev_oi = oi[i] if oi[i] is not None else prev_oi
    # drop leading minutes with no price
    s = 0
    while s < n and c[s] is None:
        s += 1
    return first + 60 * s, o[s:], h[s:], l[s:], c[s:], [v if v is not None else 0.0 for v in oi[s:]]


def hour_atrs(t0, h, l, c):
    """ATR(1h) known at each clock hour boundary: mean true range of the 24 completed hour bars before it.
    Returns dict {hour_start_ts: atr}."""
    n = len(c)
    bars = {}
    for i in range(n):
        ts = t0 + 60 * i
        hs = ts - ts % 3600
        b = bars.get(hs)
        if b is None:
            bars[hs] = [None, h[i], l[i], c[i]]   # prev close filled below
        else:
            b[1] = max(b[1], h[i]); b[2] = min(b[2], l[i]); b[3] = c[i]
    keys = sorted(bars)
    tr = {}
    prev = None
    for k in keys:
        b = bars[k]
        if prev is not None and k - prev[0] == 3600:
            pc = prev[1]
            tr[k] = max(b[1] - b[2], abs(b[1] - pc), abs(b[2] - pc))
        prev = (k, b[3])
    atr = {}
    for k in keys:
        window = [tr.get(k - 3600 * j) for j in range(1, 25)]
        if all(v is not None for v in window):
            atr[k] = sum(window) / 24.0
    return atr


def find_trades(t0, o, h, l, c, oi, k, x, tgt, last_entry_ts=None, first_entry_ts=None):
    """Sequential scan for one cell. Entry only if the whole trade (6 hours) lies before last_entry_ts + 6h, i.e. entry <= last_entry_ts."""
    atr = hour_atrs(t0, h, l, c)
    n = len(c)
    trades = []
    free_idx = 0
    for i in range(60, n - 1):
        ts_end = t0 + 60 * (i + 1)           # close time of minute i
        if i < free_idx:
            continue
        ets = t0 + 60 * (i + 1)              # entry minute start = next minute
        if last_entry_ts is not None and ets > last_entry_ts:
            break
        if first_entry_ts is not None and ets < first_entry_ts:
            continue
        hs = (t0 + 60 * i) - (t0 + 60 * i) % 3600
        a = atr.get(hs)
        if a is None or a <= 0:
            continue
        mv = c[i] - c[i - 60]
        if abs(mv) <= k * a:
            continue
        if oi[i - 60] <= 0 or oi[i] / oi[i - 60] - 1.0 >= -x:
            continue
        side = -1 if mv > 0 else 1           # against the move
        e = i + 1
        entry = o[e]
        stop = entry - side * STOP_ATR * a
        target = entry + side * tgt * a
        exit_px = None
        reason = "time"
        j_last = min(e + TIME_STOP_MIN - 1, n - 1)
        for j in range(e, j_last + 1):
            hit_stop = (l[j] <= stop) if side > 0 else (h[j] >= stop)
            hit_tgt = (h[j] >= target) if side > 0 else (l[j] <= target)
            if hit_stop:
                exit_px, reason = stop, "stop"; break
            if hit_tgt:
                exit_px, reason = target, "target"; break
        if exit_px is None:
            j = j_last
            exit_px = c[j]
        exit_ts = t0 + 60 * (j + 1)
        nf = exit_ts // FUND_PERIOD - ets // FUND_PERIOD   # funding times in (entry, exit]
        gross = side * (exit_px / entry - 1.0) * 1e4
        net = gross - 2 * FEE_SIDE_BP - nf * FUND_BP
        trades.append({"entry_ts": ets, "exit_ts": exit_ts, "side": side, "entry": entry, "exit": exit_px, "reason": reason,
                       "atr": a, "net_bp": net, "gross_bp": gross, "move_atr": (exit_px - entry) * side / a})
        free_idx = max(j + 1, e + COOLDOWN_MIN)
    return trades


def stats(trades, days=None):
    n = len(trades)
    if n == 0:
        return {"n": 0}
    r = [t["net_bp"] for t in trades]
    w = [v for v in r if v > 0]
    ls = [-v for v in r if v <= 0]
    mean = sum(r) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in r) / (n - 1)) if n > 1 else float("nan")
    pf = (sum(w) / sum(ls)) if ls and sum(ls) > 0 else float("inf")
    out = {"n": n, "win": len(w) / n, "payoff": ((sum(w) / len(w)) / (sum(ls) / len(ls))) if w and ls else float("nan"),
           "pf": pf, "exp_bp": mean, "z": (mean / (sd / math.sqrt(n))) if n > 1 and sd > 0 else float("nan"),
           "worst_bp": min(r), "worst_usd_per_100": min(r) / 100.0, "worst_atr": min(t["move_atr"] for t in trades)}
    if days:
        out["per_month"] = n / days * 30.4
    return out


def verdict(half1, half2, whole):
    """Registered development verdict for one cell."""
    if whole["n"] < MIN_N:
        return "NOT_ENOUGH_DATA"
    for s in (half1, half2, whole):
        if s["n"] == 0 or not s["exp_bp"] > 0:
            return "FALSIFIED"
    for s in (half1, half2, whole):
        if not s["pf"] >= PF_BAR:
            return "FALSIFIED"
    if not whole["z"] >= Z_BAR:
        return "FALSIFIED"
    return "SURVIVES_DEVELOPMENT"


def load(tk):
    return grid_from_candles([json.loads(l) for l in open(os.path.join(CACHE, tk + "_1m.jsonl"))])


def run(path):
    if os.path.exists(path):
        raise SystemExit("result exists; a second run needs the file deleted on purpose")
    from scalper.streaks import empirical_streaks
    data = {tk: load(tk) for tk in MARKETS}
    T0 = min(d[0] for d in data.values())
    T1 = max(d[0] + 60 * len(d[4]) for d in data.values())
    cut_half = T0 + (T1 - T0) // 3
    cut_dev = T0 + 2 * (T1 - T0) // 3
    last_entry = cut_dev - TIME_STOP_MIN * 60          # whole trade ends before the frozen third
    days = (cut_dev - T0) / 86400.0
    lines = ["SNAPBACK1 development read (frozen third untouched). T0 %d half cut %d dev cut %d; dev days %.1f" % (T0, cut_half, cut_dev, days)]
    res = {}
    for (k, x, tg) in GRID:
        allt = []
        per = {}
        for tk in MARKETS:
            t0, o, h, l, c, oi = data[tk]
            tr = find_trades(t0, o, h, l, c, oi, k, x, tg, last_entry_ts=last_entry)
            for t in tr:
                t["mkt"] = tk
            per[tk] = len(tr)
            allt += tr
        allt.sort(key=lambda t: t["entry_ts"])
        h1 = [t for t in allt if t["entry_ts"] < cut_half]
        h2 = [t for t in allt if t["entry_ts"] >= cut_half]
        s1, s2, sw = stats(h1), stats(h2), stats(allt, days)
        v = verdict(s1, s2, sw) if s1["n"] and s2["n"] else ("NOT_ENOUGH_DATA" if sw["n"] < MIN_N else "FALSIFIED")
        st = empirical_streaks([t["net_bp"] > 0 for t in allt]) if allt else None
        res[(k, x, tg)] = v
        lines.append("k=%d x=%d%% T=%d | n %d (BTC %d ETH %d) halves %d/%d | %s | %s | streaks %s" % (
            k, round(x * 100), tg, len(allt), per["KXBTCPERP"], per["KXETHPERP"], len(h1), len(h2), v, json.dumps(sw, default=str), st))
        lines.append("    half1 %s" % json.dumps(s1, default=str))
        lines.append("    half2 %s" % json.dumps(s2, default=str))
    survivors = [g for g, v in res.items() if v == "SURVIVES_DEVELOPMENT"]
    lines.append("survivors: %s" % survivors)
    open(path, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
    elif cmd == "run":
        run(os.path.join(os.path.dirname(__file__), "..", "..", "data", "snapback1_result.txt"))
    else:
        raise SystemExit("frozen read is not implemented unless a cell survives development")
