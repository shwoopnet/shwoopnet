"""LAG15 (workers/LAG15_REGISTRATION.md): RECORD1's spot-lag hypothesis replicated from history on never-named 15 minute Kalshi
series (HYPE, BNB, Zcash, NEAR). Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE, OVERLAPS_L1.
Nothing here means trade; there is no promote verb.
    python -m scalper.lag15 fetch   (resumable; settled markets, Kalshi 1 minute candles, OKX 1 minute klines into $LAG15_CACHE)
    python -m scalper.lag15 run     (the one scored read; refused a second time)
Metals and FX are NOT_RUNNABLE (no keyless minute history beyond 7 days reachable) and are not fetched.
"""
from __future__ import annotations

import calendar
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import api
from .calibration import cluster_mean_z

UTC = timezone.utc
CACHE = Path(os.environ.get("LAG15_CACHE", "/tmp/lag15_cache"))
RESULT = CACHE / "lag15_result.txt"
ASSETS = {"KXHYPE15M": "HYPE-USDT", "KXBNB15M": "BNB-USDT", "KXZEC15M": "ZEC-USDT", "KXNEAR15M": "NEAR-USDT"}
LOOK_S = 60                  # seconds before the close
EDGE_A, EDGE_B = 0.03, 0.06  # Try A (verdict) and Try B (stricter)
MIN_ENTRY, BAND = 0.20, (0.88, 0.97)
OVERLAP_SHARE = 0.50
MAX_SPREAD, QUOTE_AGE_S, VOL_WINDOW_S, MIN_VOL = 0.10, 120, 300, 10.0
C = 10
BAR_PF, BAR_Z, MIN_MEAN_C, MIN_TRADES = 1.5, 5.27, 2.0, 150
NRUN = 728714


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def fee_exact(p: float) -> float:
    return 0.07 * p * (1 - p)


def fee(p: float, mult: float = 1.0, c: int = C) -> float:
    """Per contract fee in dollars: 7% x C x p x (1-p), rounded up to the cent per order of C contracts."""
    return math.ceil(round(mult * 0.07 * c * p * (1 - p) * 100, 9)) / 100 / c


def pick(o):
    o = o or {}
    return api.f(o.get("close_dollars") if o.get("close_dollars") is not None else o.get("close"))


def sigma_per_s(closes: list[float | None]) -> float | None:
    """closes: six consecutive 1 minute closes ending at the look. RMS of the five log returns / sqrt(60). None if a close is missing."""
    if len(closes) != 6 or any(c is None or c <= 0 for c in closes):
        return None
    r = [math.log(closes[i + 1] / closes[i]) for i in range(5)]
    s = math.sqrt(sum(x * x for x in r) / 5) / math.sqrt(60)
    return s if s > 0 else None


def p_yes(S: float, K: float, sigma: float) -> float:
    """P(60 s average of the index >= K) seen from 60 s before the close: normal, variance of the average sigma^2 * 20 (RECORD1, s = 60)."""
    return phi((S - K) / (S * sigma * math.sqrt(20)))


def quote_at(candles: list, look: int):
    """candles: (end_ts, bid, ask, vol). Latest two sided quote ending at or before the look, not older than QUOTE_AGE_S."""
    best = None
    for c in candles:
        if c[0] <= look and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1 and look - c[0] <= QUOTE_AGE_S:
            if best is None or c[0] > best[0]:
                best = c
    return best


def volume_ok(candles: list, look: int) -> bool:
    return sum((c[3] or 0.0) for c in candles if look - VOL_WINDOW_S < c[0] <= look) >= MIN_VOL


def decide(close: int, strike: float, candles: list, klines: dict, edge: float):
    """Everything here uses data at or before the look (close - 60 s). klines: {open_ts_s: close_price}.
    Returns dict(eligible, p, mid, side, price) or None when not eligible. side is None when eligible but no edge or a banned price."""
    look = close - LOOK_S
    closes = [klines.get(look - 60 - 60 * (5 - i)) for i in range(6)]  # the kline opening at look-60-60k ends at look-60k; the last one ends AT the look
    sig = sigma_per_s(closes)
    q = quote_at(candles, look)
    if sig is None or q is None or not volume_ok(candles, look) or q[2] - q[1] > MAX_SPREAD + 1e-9:
        return None
    S = closes[-1]
    p = p_yes(S, strike, sig)
    bid, ask = q[1], q[2]
    out = {"eligible": True, "p": p, "mid": (bid + ask) / 2, "side": None, "price": None, "banned": False}
    if p - ask - fee_exact(ask) >= edge:
        side, price = "yes", ask
    elif (1 - p) - (1 - bid) - fee_exact(1 - bid) >= edge:
        side, price = "no", 1 - bid
    else:
        return out
    if price < MIN_ENTRY:
        out["banned"] = True
        return out
    out["side"], out["price"] = side, price
    return out


def pnl(side: str, price: float, res: str, mult: float = 1.0) -> float:
    win = (res == "yes") == (side == "yes")
    return ((1.0 if win else 0.0) - price - fee(price, mult)) * 100


def in_band(price: float) -> bool:
    return BAND[0] <= price <= BAND[1]


def overlap_share(prices: list[float]) -> float:
    return sum(1 for x in prices if in_band(x)) / len(prices) if prices else 0.0


def thirds(dates: list[str]) -> dict[str, str]:
    ds = sorted(set(dates))
    n = len(ds)
    a, b = n // 3, 2 * n // 3
    return {d: ("W1" if i < a else "W2" if i < b else "W3") for i, d in enumerate(ds)}


def stats(rows):
    """rows: [(cluster, pnl_cents)]"""
    if not rows:
        return dict(n=0, ev=0, pf=0.0, mean=0.0, z=0.0)
    w = sum(x for _, x in rows if x > 0)
    l = -sum(x for _, x in rows if x < 0)
    mean, se, z = cluster_mean_z(rows)
    return dict(n=len(rows), ev=len({e for e, _ in rows}), pf=(w / l if l > 0 else float("inf")), mean=mean, z=z)


def line(tag, s):
    return f"{tag}: n {s['n']} days {s['ev']} PF {s['pf']:.2f} mean {s['mean']:+.2f}c z {s['z']:+.2f}"


def verdict(S: dict, S12: dict, brier_model: float | None, brier_mkt: float | None, w3_read: bool, pooled: dict):
    """S: {'W1','W2'[,'W3']} stats at fee x1; S12 the same at fees x1.2; pooled stats. Returns (word, reasons)."""
    why = []
    if brier_model is not None and brier_mkt is not None and brier_model >= brier_mkt:
        why.append("Brier model no better than the market mid")
    ntr = pooled["n"]
    if ntr < MIN_TRADES:
        return ("FALSIFIED" if why else "NOT_ENOUGH_DATA"), why + [f"trades {ntr} under {MIN_TRADES}"]
    for w in (("W1", "W2", "W3") if w3_read else ("W1", "W2")):
        if S[w]["pf"] < BAR_PF:
            why.append(f"{w} PF {S[w]['pf']:.2f} under {BAR_PF}")
        if S12[w]["mean"] <= 0:
            why.append(f"{w} not positive at fees x1.2")
    if pooled["mean"] < MIN_MEAN_C:
        why.append(f"pooled mean {pooled['mean']:+.2f}c under {MIN_MEAN_C}")
    if pooled["z"] < BAR_Z:
        why.append(f"pooled z {pooled['z']:+.2f} under {BAR_Z}")
    return ("FALSIFIED" if why else "NOT_YET_FALSIFIED"), why


# ---------------------------------------------------------------- fetch
def ts(s: str) -> int:
    return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))


def okx_klines(inst: str, lo_s: int, hi_s: int) -> dict:
    """{open_ts_s: close} for 1 minute klines opening in [lo_s, hi_s], paginating backwards with `after`."""
    out, after = {}, hi_s * 1000 + 60000
    while True:
        u = f"https://www.okx.com/api/v5/market/history-candles?instId={inst}&bar=1m&limit=100&after={after}"
        for i in range(8):
            try:
                d = json.load(urllib.request.urlopen(u, timeout=30))
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
        time.sleep(0.12)
    return out


def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    mp = CACHE / "markets.json"
    markets = json.loads(mp.read_text()) if mp.exists() else {}
    if not markets:
        for s in ASSETS:
            for m in api.settled_markets(s, 0, 2**31 - 1):
                if m.get("result") in ("yes", "no") and m.get("floor_strike") is not None:
                    markets[m["ticker"]] = {"s": s, "close": ts(m["close_time"]), "k": float(m["floor_strike"]), "res": m["result"], "vol": api.f(m.get("volume_fp") or m.get("volume"))}
        mp.write_text(json.dumps(markets)); print(len(markets), "markets", flush=True)
    cp = CACHE / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    by = defaultdict(list)
    for tk, m in markets.items():
        if tk not in have:
            by[m["close"]].append(tk)
    closes = sorted(by)
    groups = [closes[i:i + 4] for i in range(0, len(closes), 4)]   # four consecutive windows per request (rate limit)
    pause = 0.3
    for i, g in enumerate(groups):
        tks = [t for c in g for t in by[c]]
        lo, hi = g[0] - 420, g[-1] - LOOK_S
        for attempt in range(12):
            try:
                req = urllib.request.Request(api.BASES[1] + "/markets/candlesticks?" + urllib.parse.urlencode({"market_tickers": ",".join(tks), "start_ts": lo, "end_ts": hi, "period_interval": 1}))
                d = json.load(urllib.request.urlopen(req, timeout=30))
                got = {x.get("market_ticker") or x.get("ticker"): x for x in d.get("markets", [])}
                for tk in tks:
                    close = markets[tk]["close"]
                    cs = (got.get(tk) or {}).get("candlesticks", [])
                    have[tk] = [(c["end_period_ts"], pick(c.get("yes_bid")), pick(c.get("yes_ask")), api.f(c.get("volume_fp") or c.get("volume"))) for c in cs if close - 900 < c["end_period_ts"] <= close - LOOK_S]
                pause = max(0.25, pause * 0.9)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    pause = min(pause * 1.3, 1.5); time.sleep(1 + attempt)
                else:
                    time.sleep(1 + attempt)
            except Exception:
                time.sleep(1 + attempt)
        else:
            print("skip", g[0], flush=True)
        if i % 50 == 0:
            cp.write_text(json.dumps(have)); print("candles", i, len(groups), "pause", round(pause, 2), flush=True)
        time.sleep(pause)
    cp.write_text(json.dumps(have))
    lo = min(m["close"] for m in markets.values()) - 700
    hi = max(m["close"] for m in markets.values())
    for s, inst in ASSETS.items():
        kp = CACHE / f"klines_{inst}.json"
        if not kp.exists():
            k = okx_klines(inst, lo, hi)
            kp.write_text(json.dumps({str(a): b for a, b in k.items()})); print(inst, len(k), "klines", flush=True)
    print("done", flush=True)


# ---------------------------------------------------------------- run
def collect(markets, cands, klines, series, edge):
    """Rows for the given asset series: eligible dict per market plus the trade decision; no outcome is read."""
    rows = []
    for tk, m in markets.items():
        if m["s"] not in series:
            continue
        d = decide(m["close"], m["k"], [tuple(c) for c in cands.get(tk, [])], klines[m["s"]], edge)
        if d:
            rows.append((tk, m, d))
    return rows


def main(argv):
    if argv and argv[0] == "fetch":
        return fetch()
    if RESULT.exists():
        print("refused: the one scored read has been run; see", RESULT); return
    markets = json.loads((CACHE / "markets.json").read_text())
    cands = json.loads((CACHE / "candles.json").read_text())
    klines = {s: {int(a): b for a, b in json.loads((CACHE / f"klines_{inst}.json").read_text()).items()} for s, inst in ASSETS.items()}
    out = [f"LAG15 run {datetime.now(UTC).isoformat()} N={NRUN} z bar {BAR_Z} cost: fee 7% x C x p x (1-p) rounded up, C={C}, taker at the ask"]
    out.append(f"markets {len(markets)}, with candles {sum(1 for t in markets if cands.get(t))}")
    # step 1: overlap test from entry PRICES only (no outcome is read)
    scored = []
    for s in ASSETS:
        r = collect(markets, cands, klines, {s}, EDGE_A)
        trades = [d["price"] for _, _, d in r if d["side"]]
        banned = sum(1 for _, _, d in r if d["banned"])
        sh = overlap_share(trades)
        tag = "OVERLAPS_L1 (not scored)" if trades and sh > OVERLAP_SHARE else "scored"
        out.append(f"{s}: eligible {len(r)}, qualifying {len(trades)}, banned under {MIN_ENTRY} {banned}, share priced {BAND[0]} to {BAND[1]} {sh*100:.0f}% -> {tag}")
        if tag == "scored":
            scored.append(s)
    if not scored:
        out.append("GROUP crypto-new: OVERLAPS_L1 (every asset); nothing scored.")
    else:
        out.append(f"scored assets: {', '.join(scored)}")
        for tag, edge in (("Try A edge 0.03 (verdict)", EDGE_A), ("Try B edge 0.06", EDGE_B)):
            rows = collect(markets, cands, klines, set(scored), edge)
            win = thirds([datetime.fromtimestamp(m["close"], UTC).strftime("%Y-%m-%d") for _, m, _ in rows])
            bm = sum((d["p"] - (m["res"] == "yes")) ** 2 for _, m, d in rows) / len(rows)
            bk = sum((d["mid"] - (m["res"] == "yes")) ** 2 for _, m, d in rows) / len(rows)
            out.append(f"{tag}: eligible markets {len(rows)} on {len(set(win))} dates; Brier model {bm:.4f} market mid {bk:.4f}")
            tr = {w: [] for w in ("W1", "W2", "W3")}
            tr12 = {w: [] for w in tr}
            for tk, m, d in rows:
                if not d["side"]:
                    continue
                day = datetime.fromtimestamp(m["close"], UTC).strftime("%Y-%m-%d")
                tr[win[day]].append((day, pnl(d["side"], d["price"], m["res"])))
                tr12[win[day]].append((day, pnl(d["side"], d["price"], m["res"], 1.2)))
            S = {w: stats(tr[w]) for w in tr}
            S12 = {w: stats(tr12[w]) for w in tr}
            for w in ("W1", "W2"):
                out.append(line(w, S[w]) + f" | fees x1.2 mean {S12[w]['mean']:+.2f}c")
            ok = S["W1"]["pf"] >= BAR_PF and S["W2"]["pf"] >= BAR_PF
            w3 = ok and bm < bk
            pooled_rows = tr["W1"] + tr["W2"] + (tr["W3"] if w3 else [])
            if w3:
                out.append(line("W3 (holdout, read because W1 and W2 passed)", S["W3"]))
            else:
                out.append("W3 holdout: not read (W1 and W2 did not both pass, or Brier failed)")
            P = stats(pooled_rows)
            word, why = verdict(S, S12, bm, bk, w3, P)
            out.append(line("pooled (windows read)", P))
            out.append(f"{tag}: {word}" + (" | " + "; ".join(why) if why else ""))
    txt = "\n".join(out)
    print(txt)
    CACHE.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(txt + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
