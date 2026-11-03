"""XETH1 (workers/XETH1_REGISTRATION.md): Bitcoin's 10 minute move as the trigger for the CHEAP side of the hourly Ethereum ladder KXETHD.
Research only; places nothing; there is no promote verb. OWNER RULE: cheap side only, this module has no favourite-side function.
    python -m scalper.xeth1 fetch   (resumable; OKX klines, KXETHD listing for development closes, candles for the selected events -> $XETH1_CACHE)
    python -m scalper.xeth1 run     (the one scored read; refuses a second time)
The last third of the dates by close time is dropped before any listing or candle is fetched.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import api, backfill
from .calibration import cluster_mean_z

UTC = timezone.utc
HERE = Path(__file__).resolve().parents[2]
CACHE = Path(os.environ.get("XETH1_CACHE", "/tmp/xeth1_cache"))
RESULT = HERE / "workers" / "XETH1_RESULT.json"
LEAD = 1500                 # look: 25 minutes before the close
BACK = 600                  # the 10 minute return
SD_MIN = 1000               # valid trailing 10 minute returns needed
TRIG_K, ETH_K = 2.0, 1.0    # BTC beyond 2 sd, ETH under 1 sd the same way
NEAR = 6                    # strikes considered per event, on the move side
LO, HI = 0.03, 0.30         # tail band at the look; hard fill limit HI
TAKE = 2
C = 10
CONTROL_MOD = 4
MIN_N, BAR_PF, BAR_Z, MIN_MEAN = 150, 1.5, 5.27, 2.0
LOOKBACK_DAYS = 62
BATCH = 8


def fee(p: float, c: int = C, mult: float = 1.0) -> float:
    """Dollars for an order of c contracts: 7% x c x p x (1-p), rounded up to the cent (scaled by mult for the x1.2 stress)."""
    return math.ceil(round(mult * 0.07 * c * p * (1 - p) * 100, 9)) / 100.0


def end_of(kl: dict, t: int):
    """Close of the 1 minute kline that ENDS at t (it opens at t - 60). kl: {open_ts: close}."""
    return kl.get(t - 60)


def ret10(kl: dict, look: int):
    a, b = end_of(kl, look), end_of(kl, look - BACK)
    if a is None or b is None or a <= 0 or b <= 0:
        return None
    return math.log(a / b)


def sd10(kl: dict, look: int):
    """RMS of the 10 minute log returns ending every minute over the 1,440 minutes ending at the look; None under SD_MIN valid ones."""
    r = []
    for k in range(1440):
        t = look - 60 * k
        a, b = end_of(kl, t), end_of(kl, t - BACK)
        if a and b and a > 0 and b > 0:
            r.append(math.log(a / b))
    if len(r) < SD_MIN:
        return None
    s = math.sqrt(sum(x * x for x in r) / len(r))
    return s if s > 0 else None


def classify(btc: dict, eth: dict, look: int):
    """(group, side, S). group: 'TRIG' (BTC beyond 2 sd, ETH under 1 sd the same way), 'F' (BTC beyond 2 sd, ETH followed), 'NONE'
    (no BTC trigger; side is the sign of the BTC move, None if it is 0), None when a number is missing."""
    rb, re_ = ret10(btc, look), ret10(eth, look)
    sb, se = sd10(btc, look), sd10(eth, look)
    S = end_of(eth, look)
    if None in (rb, re_, sb, se, S):
        return None
    side = "up" if rb > 0 else "down" if rb < 0 else None
    if rb > TRIG_K * sb:
        return ("TRIG" if re_ < ETH_K * se else "F", "up", S)
    if rb < -TRIG_K * sb:
        return ("TRIG" if re_ > -ETH_K * se else "F", "down", S)
    return ("NONE", side, S)


def in_control(event_ticker: str) -> bool:
    return int(hashlib.md5(event_ticker.encode()).hexdigest(), 16) % CONTROL_MOD == 0


def near_strikes(markets: list, S: float, side: str, n: int = NEAR) -> list:
    """markets: [(ticker, strike, ...)]. The n strikes nearest the spot on the move side (above for up, below for down)."""
    if side == "up":
        c = sorted((m for m in markets if m[1] > S), key=lambda m: (m[1] - S, m[0]))
    else:
        c = sorted((m for m in markets if m[1] < S), key=lambda m: (S - m[1], m[0]))
    return c[:n]


def cheap_price(side: str, bid, ask):
    """Price of the cheap side: up buys YES at the ask, down buys NO at 1 - bid. None without a valid two sided quote."""
    if bid is None or ask is None or not (0 < bid < ask < 1):
        return None
    return ask if side == "up" else 1 - bid


def choose(quotes: dict, side: str) -> list:
    """quotes: {ticker: (bid, ask)} at the look candle. Tickers whose cheap-side price is in LO..HI, the TAKE highest-priced."""
    ok = []
    for tk, (b, a) in quotes.items():
        p = cheap_price(side, b, a)
        if p is not None and LO - 1e-9 <= p <= HI + 1e-9:
            ok.append((p, tk))
    ok.sort(key=lambda x: (-x[0], x[1]))
    return [tk for _, tk in ok[:TAKE]]


def fill(side: str, bid, ask):
    """Price paid at the candle one minute after the look; None if no quote, above the hard limit or under 1c."""
    p = cheap_price(side, bid, ask)
    if p is None or p > HI + 1e-9 or p < 0.01:
        return None
    return p


def trade(side: str, price: float, result: str) -> dict:
    won = (result == "yes") == (side == "up")
    g = (C if won else 0.0) - C * price
    return {"won": won, "price": price, "pnl10": g - fee(price), "pnl10x": g - fee(price, mult=1.2)}


def stats(rows: list) -> dict:
    """rows: dicts with pnl10, pnl10x, won, price, day."""
    n = len(rows)
    if n == 0:
        return {"n": 0, "pf": 0.0, "pfx": 0.0, "mean": 0.0, "z": 0.0, "win": 0.0, "price": 0.0, "days": 0}
    def pf(key):
        w = sum(r[key] for r in rows if r[key] > 0)
        l = -sum(r[key] for r in rows if r[key] < 0)
        return w / l if l > 0 else float("inf")
    mean, _, z = cluster_mean_z([(r["day"], r["pnl10"] / C * 100) for r in rows])
    return {"n": n, "pf": pf("pnl10"), "pfx": pf("pnl10x"), "mean": mean, "z": z, "win": sum(1 for r in rows if r["won"]) / n,
            "price": sum(r["price"] for r in rows) / n, "days": len({r["day"] for r in rows})}


def verdict(trig: dict, ctrl: dict, ndays: int):
    """trig/ctrl: {'H1','H2','ALL'} -> stats. Returns (word, reasons). NOT_ENOUGH_DATA first (pooled trigger trades under MIN_N)."""
    why = []
    n = trig["ALL"]["n"]
    if n < MIN_N:
        rate = n / ndays if ndays else 0.0
        togo = (MIN_N - n) / rate if rate > 0 else float("inf")
        return "NOT_ENOUGH_DATA", [f"{n} trigger trades of {MIN_N}; {rate:.3f} a day, about {togo:.0f} more days at that rate"]
    for h in ("H1", "H2"):
        if trig[h]["pf"] < BAR_PF:
            why.append(f"{h} PF {trig[h]['pf']:.2f} < {BAR_PF}")
        if trig[h]["pfx"] < 1.0 or trig[h]["mean"] <= 0:
            why.append(f"{h} not positive at fees x1.2")
        if trig[h]["mean"] - ctrl[h]["mean"] <= 0:
            why.append(f"{h} trigger minus control {trig[h]['mean'] - ctrl[h]['mean']:+.2f}c not positive")
    return ("FALSIFIED" if why else "NOT_YET_FALSIFIED"), why


def day_of(ts: int) -> str:
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%d")


def thirds(dates: list) -> dict:
    ds = sorted(set(dates))
    n = len(ds)
    a, b = n // 3, 2 * n // 3
    return {d: ("W1" if i < a else "W2" if i < b else "W3") for i, d in enumerate(ds)}


def dev_halves(dev_dates: list) -> dict:
    ds = sorted(set(dev_dates))
    h = len(ds) // 2
    return {d: ("H1" if i < h else "H2") for i, d in enumerate(ds)}


# ------------------------------------------------------------------ fetch

def okx_klines(inst: str, lo_s: int, hi_s: int) -> dict:
    out, after = {}, hi_s * 1000 + 60000
    while True:
        u = f"https://www.okx.com/api/v5/market/history-candles?instId={inst}&bar=1m&limit=100&after={after}"
        for i in range(8):
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "xeth1-research/1.0"}), timeout=30))
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


def _load(p: Path, default):
    return json.loads(p.read_text()) if p.exists() else default


def closes_dev(now: int) -> list:
    """Hourly closes of the last LOOKBACK_DAYS days that are development dates (the last third of the dates is dropped here)."""
    hi = now // 3600 * 3600 - 3600
    lo = hi - LOOKBACK_DAYS * 86400
    cts = list(range(lo, hi + 1, 3600))
    w = thirds([day_of(c) for c in cts])
    return [c for c in cts if w[day_of(c)] != "W3"]


def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    cfg = CACHE / "config.json"
    if not cfg.exists():
        cfg.write_text(json.dumps({"now": now}))
    now = json.loads(cfg.read_text())["now"]
    cts = closes_dev(now)
    lo, hi = min(cts) - LEAD - 90000, max(cts)
    for inst, name in (("BTC-USDT", "btc"), ("ETH-USDT", "eth")):
        p = CACHE / f"{name}.json"
        if not p.exists():
            kl = okx_klines(inst, lo, hi)
            p.write_text(json.dumps(kl))
            print(name, len(kl), "klines", flush=True)
    btc = {int(k): v for k, v in json.loads((CACHE / "btc.json").read_text()).items()}
    eth = {int(k): v for k, v in json.loads((CACHE / "eth.json").read_text()).items()}
    cls = {}
    for ct in cts:
        c = classify(btc, eth, ct - LEAD)
        if c:
            cls[ct] = c
    (CACHE / "classes.json").write_text(json.dumps({str(k): v for k, v in cls.items()}))
    print("classified", len(cls), "of", len(cts), {g: sum(1 for v in cls.values() if v[0] == g) for g in ("TRIG", "F", "NONE")}, flush=True)
    # listings: one per development close
    lp = CACHE / "listings.jsonl"
    done = {json.loads(l)["ct"] for l in lp.read_text().splitlines()} if lp.exists() else set()
    with lp.open("a") as fh:
        for i, ct in enumerate(cts):
            if ct in done or ct not in cls:
                continue
            ms = list(api.settled_markets("KXETHD", ct - 1, ct))
            rows = [[m["ticker"], m.get("event_ticker"), m.get("floor_strike"), m.get("result")] for m in ms
                    if backfill.iso_ts(m.get("close_time")) == ct]
            fh.write(json.dumps({"ct": ct, "m": rows}) + "\n"); fh.flush()
            if i % 50 == 0:
                print(f"listing {i}/{len(cts)}", flush=True)
            time.sleep(0.25)
    # candles for the selected strikes
    cp = CACHE / "candles.jsonl"
    have = {json.loads(l)["tk"] for l in cp.read_text().splitlines()} if cp.exists() else set()
    want = []
    for line in lp.read_text().splitlines():
        d = json.loads(line)
        ct = d["ct"]
        g, side, S = cls[ct]
        if side is None:
            continue
        by = defaultdict(list)
        for tk, ev, k, res in d["m"]:
            if k is not None:
                by[ev].append((tk, float(k)))
        for ev, ms in by.items():
            if g == "NONE" and not in_control(ev):
                continue
            for tk, _ in near_strikes(ms, S, side):
                if tk not in have:
                    want.append((tk, ct))
    print("candle requests", (len(want) + BATCH - 1) // BATCH, flush=True)
    with cp.open("a") as fh:
        for i in range(0, len(want), BATCH):
            ch = want[i:i + BATCH]
            ct = ch[0][1]
            for ct_ in sorted({c for _, c in ch}):
                sub = [tk for tk, c in ch if c == ct_]
                got = api.batch_candlesticks(sub, ct_ - LEAD - 240, ct_ - LEAD + 120)
                for tk in sub:
                    rows = [r for r in (backfill.parse_candle(x, tk, "KXETHD") for x in got.get(tk, [])) if r]
                    fh.write(json.dumps({"tk": tk, "c": [[r[2], r[6], r[10]] for r in rows]}) + "\n")
                time.sleep(0.4)
            fh.flush()
            if (i // BATCH) % 25 == 0:
                print(f"candles {i}/{len(want)}", flush=True)
    print("fetch done", flush=True)


# ------------------------------------------------------------------ run

def run() -> None:
    if RESULT.exists():
        print("XETH1 already scored once; refused. See", RESULT)
        return
    now = json.loads((CACHE / "config.json").read_text())["now"]
    cts = closes_dev(now)
    cls = {int(k): v for k, v in json.loads((CACHE / "classes.json").read_text()).items()}
    cand = {}
    for l in (CACHE / "candles.jsonl").read_text().splitlines():
        d = json.loads(l)
        cand[d["tk"]] = {c[0]: (c[1], c[2]) for c in d["c"]}
    halves = dev_halves([day_of(c) for c in cts])
    ndays = len(set(day_of(c) for c in cts))
    rows = {"TRIG": [], "F": [], "NONE": []}
    seen = {"TRIG": set(), "F": set(), "NONE": set()}
    for l in (CACHE / "listings.jsonl").read_text().splitlines():
        d = json.loads(l)
        ct = d["ct"]
        if ct not in cls:
            continue
        g, side, S = cls[ct]
        if side is None:
            continue
        by = defaultdict(list)
        res = {}
        for tk, ev, k, r in d["m"]:
            if k is not None:
                by[ev].append((tk, float(k)))
            res[tk] = r
        for ev, ms in by.items():
            if g == "NONE" and not in_control(ev):
                continue
            seen[g].add(ev)
            near = near_strikes(ms, S, side)
            q = {}
            for tk, _ in near:
                c = cand.get(tk, {}).get(ct - LEAD)
                if c:
                    q[tk] = c
            for tk in choose(q, side):
                f = cand.get(tk, {}).get(ct - LEAD + 60)
                p = fill(side, *f) if f else None
                if p is None or res.get(tk) not in ("yes", "no"):
                    continue
                t = trade(side, p, res[tk])
                t.update(day=day_of(ct), half=halves[day_of(ct)], ct=ct, ticker=tk, side=side)
                rows[g].append(t)
    out = {}
    for g in rows:
        out[g] = {h: stats([r for r in rows[g] if h == "ALL" or r["half"] == h]) for h in ("H1", "H2", "ALL")}
    word, why = verdict(out["TRIG"], out["NONE"], ndays)
    out["verdict"], out["reasons"] = word, why
    out["events"] = {g: len(seen[g]) for g in seen}
    out["class_counts"] = {g: sum(1 for v in cls.values() if v[0] == g) for g in ("TRIG", "F", "NONE")}
    out["ndays"], out["ncloses"] = ndays, len(cts)
    RESULT.write_text(json.dumps(out, indent=1, default=str))
    def line(tag, s):
        return f"{tag}: n {s['n']} days {s['days']} win {s['win']:.3f} paid {s['price']:.3f} PF {s['pf']:.2f} PFx1.2 {s['pfx']:.2f} mean {s['mean']:+.2f}c z {s['z']:+.2f}"
    for g in ("TRIG", "NONE", "F"):
        for h in ("H1", "H2", "ALL"):
            print(g, line(h, out[g][h]))
    print("events", out["events"], "classes", out["class_counts"], "ndays", ndays)
    print(word, why)


def main(argv):
    if len(argv) > 1 and argv[1] == "fetch":
        fetch()
    elif len(argv) > 1 and argv[1] == "run":
        run()
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
