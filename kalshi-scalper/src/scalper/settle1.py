"""SETTLE1: reference-implied winner on the silver, platinum, palladium, WTI and natural gas 15 minute
series against OKX perpetuals. Registration: workers/SETTLE1_REGISTRATION.md (commit bddb529), written
before any OKX bar was compared with any Kalshi quote or outcome.  Research only, no orders.

  python -m scalper.settle1 fetch   OKX 1 minute klines into the cache (public, keyless)
  python -m scalper.settle1 run     score once; W3 (last third of dates) is never loaded into a print
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .calibration import cluster_mean_z

UTC = timezone.utc
DB = Path(__file__).resolve().parents[2] / "data" / "alts3.sqlite"
CACHE = Path(os.environ.get("SETTLE1_CACHE", "/tmp/settle1_cache"))
FAMILIES = {"KXSILVER15M": "XAG-USDT-SWAP", "KXPLATINUM15M": "XPT-USDT-SWAP", "KXPALLADIUM15M": "XPD-USDT-SWAP",
            "KXWTI15M": "CL-USDT-SWAP", "KXNATGAS15M": "NG-USDT-SWAP"}
LOOKS = (180, 120)            # seconds before the close
Z_MIN = 1.0
BAND = (0.05, 0.30)
MAX_SPREAD = 0.10
VOL_BARS, MIN_RET = 60, 40
C = 10
BAR_PF, BAR_Z, MIN_TRADES, MIN_DAYS = 1.5, 5.27, 150, 8


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def fee(p: float, mult: float = 1.0, c: int = C) -> float:
    """Per contract fee in dollars: 7% x C x p x (1-p), rounded up to the cent per order of C contracts."""
    return math.ceil(round(mult * 0.07 * c * p * (1 - p) * 100, 9)) / 100 / c


def signal(klines: dict, close: int, look_s: int):
    """(x, sigma, z) from the reference only: R(t) is the close of the 1 minute bar opening at t - 60.
    Returns None if a needed bar is missing, sigma is zero, or x is zero."""
    d = close - look_s
    r0, rd = klines.get(close - 900 - 60), klines.get(d - 60)
    if not r0 or not rd:
        return None
    px = [klines.get(d - 60 - 60 * i) for i in range(VOL_BARS + 1)]
    rets = [math.log(a / b) for a, b in zip(px, px[1:]) if a and b]
    if len(rets) < MIN_RET:
        return None
    sigma = math.sqrt(sum(r * r for r in rets) / len(rets))
    x = math.log(rd / r0)
    if sigma <= 0 or x == 0:
        return None
    m = look_s / 60
    return x, sigma, x / (sigma * math.sqrt(m))


def quote(cands: dict, t: int):
    """(bid, ask) from the Kalshi candle ending exactly at t, two sided and tight, else None."""
    c = cands.get(t)
    if not c:
        return None
    bid, ask = c
    if bid is None or ask is None or not (0 < bid < ask < 1) or ask - bid > MAX_SPREAD + 1e-9:
        return None
    return bid, ask


def decide(klines: dict, cands: dict, close: int, look_s: int):
    """Return dict(side, price, z, p, triggered) or None when there is no signal or quote. No outcome used."""
    s = signal(klines, close, look_s)
    if s is None:
        return None
    x, _, z = s
    q = quote(cands, close - look_s + 60)
    if q is None:
        return None
    bid, ask = q
    side = "yes" if x > 0 else "no"
    price = ask if side == "yes" else 1 - bid
    return {"side": side, "price": price, "z": z, "p": phi(abs(z)), "bid": bid, "ask": ask}


def pnl(side: str, price: float, res: str, mult: float = 1.0, slip: float = 0.0) -> float:
    """Cents per contract after the fee (res is 'yes' or 'no')."""
    pr = price + slip
    win = 1.0 if res == side else 0.0
    return (win - pr - fee(pr, mult)) * 100


def thirds(dates: list[str]) -> dict[str, str]:
    ds = sorted(set(dates))
    n = len(ds)
    return {d: ("W1" if i < n / 3 else "W2" if i < 2 * n / 3 else "W3") for i, d in enumerate(ds)}


def stats(rows, mult=1.0, slip=0.0):
    """rows: (date, side, price, res). n, win rate, mean price, PF, mean c, z (date clustered), days."""
    if not rows:
        return {"n": 0, "win": 0, "price": 0, "pf": 0, "mean": 0, "z": 0, "days": 0}
    pn = [(d, pnl(s, p, r, mult, slip)) for d, s, p, r in rows]
    g = sum(x for _, x in pn if x > 0)
    l = -sum(x for _, x in pn if x < 0)
    mean, _, z = cluster_mean_z(pn)
    return {"n": len(rows), "win": sum(1 for _, s, _, r in rows if s == r) / len(rows), "price": sum(p for _, _, p, _ in rows) / len(rows),
            "pf": (g / l if l > 0 else float("inf")), "mean": mean, "z": z, "days": len({d for d, *_ in rows})}


def line(tag, s):
    return f"{tag:34s} n={s['n']:4d} days={s['days']:3d} win={s['win']:.3f} price={s['price']:.3f} PF={s['pf']:.2f} mean={s['mean']:+.2f}c z={s['z']:+.2f}"


# ---------------------------------------------------------------- data
def okx_klines(inst: str, lo_s: int, hi_s: int) -> dict:
    out, after = {}, hi_s * 1000 + 60000
    while True:
        u = f"https://www.okx.com/api/v5/market/history-candles?instId={inst}&bar=1m&limit=100&after={after}"
        for i in range(8):
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "settle1-research/1.0"}), timeout=30))
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


def load_markets():
    c = sqlite3.connect(DB)
    mk = {}
    for tk, s, close, res in c.execute(f"select ticker, series, close_ts, result from market where series in ({','.join('?' * len(FAMILIES))})", tuple(FAMILIES)):
        if res in ("yes", "no"):
            mk[tk] = {"s": s, "close": close, "res": res}
    cands = defaultdict(dict)
    for tk, t, b, a in c.execute(f"select ticker, end_ts, bid_c, ask_c from candle where series in ({','.join('?' * len(FAMILIES))})", tuple(FAMILIES)):
        cands[tk][t] = (b, a)
    return mk, cands


def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    mk, _ = load_markets()
    for s, inst in FAMILIES.items():
        p = CACHE / f"klines_{inst}.json"
        if p.exists():
            continue
        cl = [m["close"] for m in mk.values() if m["s"] == s]
        k = okx_klines(inst, min(cl) - 900 - 4000, max(cl))
        p.write_text(json.dumps({str(a): b for a, b in k.items()}))
        print(inst, len(k), "klines", flush=True)


def date_of(close: int) -> str:
    return datetime.fromtimestamp(close, UTC).strftime("%Y-%m-%d")


def build(mk, cands, kl):
    """Every market-look with a signal and a quote. No outcome is read here."""
    rows = []
    for tk, m in mk.items():
        for L in LOOKS:
            d = decide(kl[m["s"]], cands.get(tk, {}), m["close"], L)
            if d:
                rows.append({"tk": tk, "s": m["s"], "L": L, "date": date_of(m["close"]), "res": m["res"], **d})
    return rows


def run() -> None:
    mk, cands = load_markets()
    kl = {s: {int(a): b for a, b in json.loads((CACHE / f"klines_{i}.json").read_text()).items()} for s, i in FAMILIES.items()}
    rows = build(mk, cands, kl)
    trig = [r for r in rows if abs(r["z"]) >= Z_MIN]
    out = []
    P = out.append
    P(f"market-looks with a signal and a quote: {len(rows)}; triggered |z|>={Z_MIN}: {len(trig)} ({len(trig)/max(1,len(rows)):.1%})")
    P("-- no outcome used below: share of triggered looks whose implied side is still cheap, per family and look")
    for s in FAMILIES:
        for L in LOOKS:
            t = [r for r in trig if r["s"] == s and r["L"] == L]
            a = [r for r in rows if r["s"] == s and r["L"] == L]
            if not t:
                P(f"{s} L={L}: market-looks {len(a)}, triggered 0"); continue
            P(f"{s} L={L}: market-looks {len(a)} triggered {len(t)} ({len(t)/len(a):.1%}); implied side price <=0.30: {sum(r['price']<=0.30 for r in t)} ({sum(r['price']<=0.30 for r in t)/len(t):.2%}), <=0.50: {sum(r['price']<=0.50 for r in t)/len(t):.2%}, mean price {sum(r['price'] for r in t)/len(t):.3f}, mean model p {sum(r['p'] for r in t)/len(t):.3f}")
    treated = [r for r in trig if BAND[0] <= r["price"] <= BAND[1]]
    ctrl = [r for r in rows if abs(r["z"]) < 0.25]
    # control rows: cheaper side in band
    cr = []
    for r in ctrl:
        y, n_ = r["ask"], 1 - r["bid"]
        side, price = ("yes", y) if y <= n_ else ("no", n_)
        if BAND[0] <= price <= BAND[1]:
            cr.append({**r, "side": side, "price": price})
    dates = [r["date"] for r in trig]          # registered: dates with a triggered, quotable look (no outcome)
    split = thirds(dates)
    P(f"triggered dates {len(set(dates))} thirds sizes " + str({w: sum(1 for d in set(dates) if split[d] == w) for w in ('W1', 'W2', 'W3')}))
    P("treated trades per window (counts only; W3 outcomes never loaded): " + str({w: sum(1 for r in treated if split[r['date']] == w) for w in ('W1', 'W2', 'W3')}))
    def sel(rs, ws):
        return [(r["date"], r["side"], r["price"], r["res"]) for r in rs if split.get(r["date"], "W3") in ws]
    P("== treated, outcomes (W1 and W2 only)")
    for w in ("W1", "W2"):
        P(line(f"pooled {w}", stats(sel(treated, (w,)))))
    P(line("pooled W1+W2", stats(sel(treated, ("W1", "W2")))))
    P(line("pooled W1+W2 fees x1.2", stats(sel(treated, ("W1", "W2")), mult=1.2)))
    P(line("pooled W1+W2 +1c slip", stats(sel(treated, ("W1", "W2")), slip=0.01)))
    for s in FAMILIES:
        for L in LOOKS:
            sub = [r for r in treated if r["s"] == s and r["L"] == L]
            P(line(f"{s} L={L} W1+W2", stats(sel(sub, ("W1", "W2")))))
    P(line("control |z|<0.25 cheap side W1+W2", stats([(r["date"], r["side"], r["price"], r["res"]) for r in cr if split.get(r["date"]) in ("W1", "W2")])))
    P("== calibration of the implied side, ALL triggered looks on W1+W2 dates (information)")
    sp2 = split
    for s in FAMILIES:
        t = [r for r in trig if r["s"] == s and sp2[r["date"]] in ("W1", "W2")]
        if t:
            P(f"{s}: n={len(t)} implied-side win {sum(r['side']==r['res'] for r in t)/len(t):.3f} mean Phi {sum(r['p'] for r in t)/len(t):.3f} mean price {sum(r['price'] for r in t)/len(t):.3f}")
    w12 = stats(sel(treated, ("W1", "W2")))
    wins = {w: stats(sel(treated, (w,))) for w in ("W1", "W2")}
    fam_days = {s: len({r['date'] for r in treated if r['s'] == s and split[r['date']] in ('W1', 'W2')}) for s in FAMILIES}
    P("days with a treated trade per family (W1+W2): " + str(fam_days))
    if w12["n"] < MIN_TRADES:
        v = f"NOT_ENOUGH_DATA (pooled W1+W2 treated trades {w12['n']} < {MIN_TRADES})"
    elif any(wins[w]["pf"] < BAR_PF for w in wins) or stats(sel(treated, ("W1", "W2")), mult=1.2)["mean"] <= 0:
        v = "FALSIFIED"
    elif w12["z"] < BAR_Z:
        v = "NOT_YET_FALSIFIED (z below the bar; W3 read and forward registration only)"
    else:
        v = "NOT_YET_FALSIFIED (bars met; W3 read and forward registration only)"
    P("VERDICT pooled: " + v)
    if w12["n"] >= 1 and any(wins[w]["pf"] < BAR_PF for w in wins):
        P("note: PF under 1.5 in at least one read window, so FALSIFIED on that line whatever the count says")
    P("OUTCOME-BLIND counts: market-looks " + str(len(rows)) + ", triggered " + str(len(trig)) + ", treated " + str(len(treated)))
    print("\n".join(out))
    Path(__file__).resolve().parents[2].joinpath("studies", "settle1_result_2026-11-03.txt").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
