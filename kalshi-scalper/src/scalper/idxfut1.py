"""IDXFUT1 (workers/IDXFUT1_REGISTRATION.md): Kalshi S&P 500 / Nasdaq 100 4 pm "above K" ladders against an OKX equity-index
perp (SPY, QQQ) and its 60 minute realised vol; cheap asks only. Research only: nothing here places an order.

Usage: python -m scalper.idxfut1 fetch     (OKX 1 minute bars around each close into data/idxfut1_okx/)
       python -m scalper.idxfut1 run       (W1 and W2 only; W3 is never loaded)
       python -m scalper.idxfut1 holdout   (W3 too, once, only if the registered gate passed)
"""
from __future__ import annotations

import json
import math
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from .calibration import cluster_mean_z
from .fees import taker_fee

DATA = Path("data")
ODIR = DATA / "idxfut1_okx"
DB = DATA / "inx1.sqlite"
YDIR = DATA / "inx1_yahoo"
SERIES = {"KXINXU": ("SPY-USDT-SWAP", "GSPC"), "KXNASDAQ100U": ("QQQ-USDT-SWAP", "NDX")}
LOOKS = (30, 10)
VOL_MIN = 60
MIN_RET = 40
ASK_LO, ASK_HI = 0.03, 0.30
RATIO = 3.0
SCALE_LEAD = 75 * 60
STRESS = 1.2
C = 10
NMAX = 150
ZBAR = 5.27


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def day_of(c: int) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(c))


def fetch() -> None:
    ODIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    closes = sorted({c for (c,) in db.execute("SELECT DISTINCT close_ts FROM market WHERE series='KXINXU'")})
    for series, (inst, _) in SERIES.items():
        out = ODIR / f"{inst}.json"
        have = json.load(open(out)) if out.exists() else {}
        for c in closes:
            if str(c) in have:
                continue
            url = f"https://www.okx.com/api/v5/market/history-candles?instId={inst}&bar=1m&limit=100&after={(c + 60) * 1000}"
            for attempt in range(4):
                r = subprocess.run(["curl", "-s", "-m", "20", url], capture_output=True, text=True)
                try:
                    d = json.loads(r.stdout)
                    if d.get("code") == "0":
                        have[str(c)] = {int(x[0]) // 1000: float(x[4]) for x in d["data"]}
                        break
                except Exception:
                    pass
                time.sleep(2 + 3 * attempt)
            time.sleep(0.4)
        json.dump(have, open(out, "w"))
        print(inst, len(have), "closes", flush=True)


def yahoo_bars(sym: str) -> dict[int, float]:
    d = json.load(open(YDIR / f"{sym}_5m.json"))["chart"]["result"][0]
    return {int(t): c for t, c in zip(d["timestamp"], d["indicators"]["quote"][0]["close"]) if c is not None}


def ref_state(bars: dict[int, float], ybars: dict[int, float], close: int, L: int):
    """(S, sigma) at D = close - L min, or None. bars: {bar start ts: close}. OKX bar starting D-60 ends at D."""
    D = close - L * 60
    R = bars.get(D - 60)
    t0 = close - SCALE_LEAD
    r0, y0 = bars.get(t0 - 60), ybars.get(t0 - 300)
    if R is None or r0 is None or y0 is None:
        return None
    rets, prev = [], None
    for i in range(VOL_MIN + 1):
        v = bars.get(D - 60 - 60 * (VOL_MIN - i))
        if v is not None and prev is not None and v > 0 and prev > 0:
            rets.append(math.log(v / prev))
        prev = v if v is not None else prev
    if len(rets) < MIN_RET:
        return None
    sig = math.sqrt(sum(x * x for x in rets) / len(rets))
    if sig <= 0:
        return None
    return R * (y0 / r0), sig


def cands_at(S, sig, L, quotes):
    """quotes: [(ticker, strike, result, bid, ask)] -> all strike-sides with ask 0.03..0.30 as dicts incl. model p."""
    out = []
    for t, k, res, b, a in quotes:
        if b is None or a is None or not (b > 0 and a < 1):
            continue
        p = phi(math.log(S / k) / (sig * math.sqrt(L)))
        if ASK_LO <= a <= ASK_HI:
            out.append(dict(ticker=t, side="yes", price=a, won=res == "yes", mp=p))
        nb = round(1 - b, 4)
        if ASK_LO <= nb <= ASK_HI:
            out.append(dict(ticker=t, side="no", price=nb, won=res == "no", mp=1 - p))
    return out


def pick_treated(cs):
    ok = [c for c in cs if c["mp"] >= RATIO * c["price"]]
    return max(ok, key=lambda c: c["mp"] - c["price"]) if ok else None


def pick_control(cs):
    return min(cs, key=lambda c: abs(c["price"] - 0.10)) if cs else None


def pnl(tr, mult=1.0, slip=0.0) -> float:
    price = tr["price"] + slip
    fee = taker_fee(price, C, mult)
    return (C * (1 - price) if tr["won"] else -C * price) - fee


def score(rows, mult=1.0, slip=0.0):
    nets = [pnl(r, mult, slip) for r in rows]
    w = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    pf = (w / l) if l > 0 else (float("inf") if w > 0 else 0.0)
    return dict(n=len(rows), days=len({r["day"] for r in rows}), net=sum(nets), pf=pf,
                mean=(sum(nets) / len(nets) if nets else 0.0), win=(sum(r["won"] for r in rows) / len(rows) if rows else 0.0),
                price=(sum(r["price"] for r in rows) / len(rows) if rows else 0.0))


def build(days_ok):
    """days_ok: set of days that may be loaded. Returns treated rows, control rows, calibration rows."""
    db = sqlite3.connect(DB)
    mk = defaultdict(list)
    for t, s, c, r, k in db.execute("SELECT ticker, series, close_ts, result, strike FROM market"):
        if day_of(c) in days_ok:
            mk[(s, c)].append((t, r, k))
    cd = defaultdict(dict)
    for t, e, b, a in db.execute("SELECT ticker, end_ts, bid_c, ask_c FROM candle"):
        cd[t][e] = (b, a)
    tre, con, cal, st = [], [], [], defaultdict(int)
    for series, (inst, ysym) in SERIES.items():
        okx = json.load(open(ODIR / f"{inst}.json"))
        yb = yahoo_bars(ysym)
        for (s, c), ms in sorted(mk.items()):
            if s != series:
                continue
            bars = {int(k): v for k, v in okx.get(str(c), {}).items()}
            for L in LOOKS:
                var = f"{series}-{L}"
                stt = ref_state(bars, yb, c, L)
                if stt is None:
                    st[(var, "no reference")] += 1
                    continue
                S, sig = stt
                D = c - L * 60
                qs = []
                for t, r, k in ms:
                    q = cd[t].get(D + 60)
                    if q:
                        qs.append((t, k, r, q[0], q[1]))
                cs = cands_at(S, sig, L, qs)
                st[(var, "event-looks")] += 1
                for x in cs:
                    cal.append(dict(var=var, day=day_of(c), ratio=x["mp"] / x["price"], **{k: x[k] for k in ("price", "won", "mp")}))
                tr, co = pick_treated(cs), pick_control(cs)
                if tr:
                    tre.append(dict(var=var, day=day_of(c), **tr))
                if co:
                    con.append(dict(var=var, day=day_of(c), **co))
    return tre, con, cal, st


def all_days():
    db = sqlite3.connect(DB)
    return sorted({day_of(c) for (c,) in db.execute("SELECT DISTINCT close_ts FROM market WHERE series='KXINXU'")})


def split(days):
    n = len(days)
    a, b = days[n // 3 - 1], days[2 * n // 3 - 1]
    return (lambda d: "W1" if d <= a else ("W2" if d <= b else "W3")), a, b


def line(tag, rows):
    s, sx, sl = score(rows), score(rows, STRESS), score(rows, 1.0, 0.01)
    return (f"{tag}: n {s['n']} days {s['days']} win {s['win']:.1%} price {s['price']:.3f} PF {s['pf']:.2f} mean {s['mean']*100:+.2f}c "
            f"| fees x1.2 mean {sx['mean']*100:+.2f}c | +1c slip mean {sl['mean']*100:+.2f}c")


def report(wins) -> None:
    days = all_days()
    win, a, b = split(days)
    use = {d for d in days if win(d) in wins}
    tre, con, cal, st = build(use)
    print(f"IDXFUT1 run {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} N=728763 z bar {ZBAR} C={C} windows {sorted(wins)}; days {len(days)} cuts W1<={a} W2<={b}")
    for k, v in sorted(st.items(), key=str):
        print("  stat", k, v)
    for var in sorted({r["var"] for r in tre + con}):
        for w in sorted(wins):
            print(line(f"TREATED {var} {w}", [r for r in tre if r["var"] == var and win(r["day"]) == w]))
            print(line(f"CONTROL {var} {w}", [r for r in con if r["var"] == var and win(r["day"]) == w]))
    for w in sorted(wins):
        print(line(f"TREATED POOLED {w}", [r for r in tre if win(r["day"]) == w]))
        print(line(f"CONTROL POOLED {w}", [r for r in con if win(r["day"]) == w]))
    print("calibration (every strike-side with ask 0.03..0.30), pooled windows:")
    for lo, hi, nm in ((0, 1, "ratio<1"), (1, 3, "1<=ratio<3"), (3, 1e9, "ratio>=3")):
        rs = [x for x in cal if lo <= x["ratio"] < hi]
        if rs:
            print(f"  {nm}: n {len(rs)} price {sum(x['price'] for x in rs)/len(rs):.3f} win {sum(x['won'] for x in rs)/len(rs):.3f} model {sum(x['mp'] for x in rs)/len(rs):.3f}")
    pooled = [r for r in tre if win(r["day"]) in ("W1", "W2")]
    m, se, z = cluster_mean_z([(r["day"], pnl(r)) for r in pooled])
    print(f"pooled treated W1+W2: n {len(pooled)}, mean {m*100:+.2f}c, day-clustered z {z:+.2f} (bar {ZBAR})")
    verdict(tre, con, win)


def verdict(tre, con, win) -> None:
    pooled = [r for r in tre if win(r["day"]) in ("W1", "W2")]
    if len(pooled) < NMAX:
        print(f"VERDICT: NOT_ENOUGH_DATA | pooled treated {len(pooled)} under {NMAX}")
    pf = {w: score([r for r in tre if win(r["day"]) == w])["pf"] for w in ("W1", "W2")}
    xm = score(pooled, STRESS)["mean"]
    ctrl_ok = all(score([r for r in tre if win(r["day"]) == w])["mean"] > score([r for r in con if win(r["day"]) == w])["mean"] for w in ("W1", "W2"))
    fals = pf["W1"] < 1.5 or pf["W2"] < 1.5 or xm <= 0 or not ctrl_ok
    print(f"gate: PF W1 {pf['W1']:.2f} W2 {pf['W2']:.2f}, fees x1.2 mean {xm*100:+.2f}c, treated above control both: {ctrl_ok} -> "
          f"{'FALSIFIED (any one failing)' if fals else 'passes W1/W2 gate (needs z bar for NOT_YET_FALSIFIED)'}")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "fetch":
        fetch()
    elif cmd == "run":
        report({"W1", "W2"})
    elif cmd == "holdout":
        report({"W1", "W2", "W3"})


if __name__ == "__main__":
    main()
