"""COMDAY1 (workers/COMDAY1_REGISTRATION.md): Kalshi DAILY commodity ladders (KXWTI, KXBRENTD, KXNATGASD, KXGOLDD, KXSILVERD, KXCOPPERD)
against an OKX perpetual outside price and a Student t (4 df) kernel; the CHEAP side only (ask 3c to 30c), held to settlement.
Research only: nothing here places an order. There is deliberately no favourite-side rule and no favourite-side output (owner rule).

Usage (cache lives OUTSIDE the repo, COMDAY1_CACHE):
  python -m scalper.comday1 markets   listings (hist + live) -> dev markets only; the frozen last third of the dates is dropped in memory and never written
  python -m scalper.comday1 okx       OKX 5 minute bars around every development close (and the previous day's close)
  python -m scalper.comday1 candles   Kalshi minute candles for the pre-filtered strikes, in md5 rank order, one thread
  python -m scalper.comday1 score     ONE scored run (W3 never loaded)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import api
from .calibration import cluster_mean_z
from .candlefield import quote_close

CACHE = Path(os.environ.get("COMDAY1_CACHE", "/tmp/comday1_cache"))
SERIES = {"KXWTI": "CL", "KXBRENTD": "BZ", "KXNATGASD": "NG", "KXGOLDD": "XAU", "KXSILVERD": "XAG", "KXCOPPERD": "XCU"}
FIRST_DATE = "2026-03-24"
LAST_DATE = "2026-11-02"
LOOKS = {"A": 360, "B": 60}
VOL_MIN = 240
MIN_RET = 36
NU_SCALE = math.sqrt(2.0)       # variance of t4 is 2
P_LO, P_HI = 0.03, 0.97
ASK_LO, ASK_HI = 0.03, 0.30
RATIO = 3.0
MAX_PER_DAY = 2
STALE_S = 3600
C = 10
STRESS = 1.2
NMAX = 150
HIST_CUT = "2026-09-04"
FETCH_CAP_S = 4 * 3600
PREV_GAP_DAYS = 5


# ------------------------------------------------------------------ model
def t4_cdf(t: float) -> float:
    x = t / math.sqrt(1.0 + t * t / 4.0)
    return 0.5 + 0.375 * x * (1.0 - x * x / 12.0)


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def p_yes(S: float, K: float, sig_min: float, H: float, kernel: str = "t4") -> float:
    """P(price at the close > K): ln(S_T/S) ~ t4 with variance sig_min^2 x H, zero drift."""
    sd = sig_min * math.sqrt(H)
    if sd <= 0 or S <= 0 or K <= 0:
        return float("nan")
    z = math.log(K / S) / sd
    if kernel == "t4":
        return 1.0 - t4_cdf(z * NU_SCALE)
    return 1.0 - phi(z)


def fee(p: float, mult: float = 1.0, c: int = C) -> float:
    return math.ceil(round(mult * 0.07 * c * p * (1 - p) * 100, 6)) / 100.0 / c


def net(won: bool, price: float, mult: float = 1.0) -> float:
    return (1.0 if won else 0.0) - price - fee(price, mult)


def date_of(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def iso_ts(s: str) -> int:
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def rank_key(series: str, date: str) -> str:
    return hashlib.md5(f"COMDAY1|{series}|{date}".encode()).hexdigest()


# ------------------------------------------------------------------ reference
def bar_close_ending(bars: dict, t: int):
    """Close of the 5 minute bar that ENDS at t (bars keyed by start second)."""
    return bars.get(t - 300)


def sigma_min(bars: dict, D: int):
    """RMS of 5 minute log returns over the VOL_MIN minutes ending at D (zero mean), per minute; None if fewer than MIN_RET returns."""
    rs = []
    for e in range(D - VOL_MIN * 60 + 300, D + 1, 300):
        a, b = bars.get(e - 600), bars.get(e - 300)
        if a and b and a > 0 and b > 0:
            rs.append(math.log(b / a))
    if len(rs) < MIN_RET:
        return None
    return math.sqrt(sum(r * r for r in rs) / len(rs)) / math.sqrt(5.0)


def ref_state(bars: dict, close: int, L: int, prev_exp, prev_close):
    """(S, sigma_min) at D = close - L minutes, or None. S = OKX close at D x (previous day's settlement value / OKX close at the previous close)."""
    D = close - L * 60
    R = bar_close_ending(bars, D)
    if not R or prev_exp is None or prev_close is None:
        return None
    pb = bar_close_ending(bars, prev_close)
    if not pb:
        return None
    sg = sigma_min(bars, D)
    if sg is None:
        return None
    return R * prev_exp / pb, sg


def quote_at(cs: list, D: int):
    """The two-sided quote in force at D + 60: the latest candle ending at or before D+60 and at most STALE_S old; (bid, ask) or None."""
    best = None
    for c in cs:
        e = c[0]
        if e is None or e > D + 60 or D + 60 - e > STALE_S:
            continue
        if best is None or e > best[0]:
            best = c
    if best is None:
        return None
    bid, ask = best[1], best[2]
    if bid is None or ask is None or not (0 < bid < ask < 1):
        return None
    return bid, ask


def sides_at(S: float, sg: float, H: float, K: float, q):
    """Cheap in-band sides of one strike: [(side, price, p_side, p_side_gauss)]; strikes with model P(YES) outside [P_LO, P_HI] give none."""
    pY = p_yes(S, K, sg, H)
    if not (P_LO <= pY <= P_HI):
        return []
    pG = p_yes(S, K, sg, H, "gauss")
    bid, ask = q
    out = []
    if ASK_LO <= ask <= ASK_HI:
        out.append(("yes", ask, pY, pG))
    b = 1.0 - bid
    if ASK_LO <= b <= ASK_HI:
        out.append(("no", b, 1.0 - pY, 1.0 - pG))
    return out


def treated_picks(sides: list):
    """sides: [(ticker, side, price, p, pG)] -> the registered picks: ratio >= 3, p <= 0.97, top MAX_PER_DAY by model edge."""
    c = [s for s in sides if s[3] >= RATIO * s[2] and s[3] <= P_HI]
    c.sort(key=lambda s: s[3] - s[2], reverse=True)
    return c[:MAX_PER_DAY]


# ------------------------------------------------------------------ fetch
def _json_curl(url: str):
    for attempt in range(5):
        r = subprocess.run(["curl", "-s", "-m", "25", url], capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
            if d.get("code") == "0":
                return d["data"]
        except Exception:
            pass
        time.sleep(1.5 + 2 * attempt)
    return None


def split_dates(dates: list[str]):
    d = sorted(set(dates))
    k = int(len(d) * 2 / 3)
    dev = d[:k]
    mid = len(dev) // 2
    return dev, dev[:mid], dev[mid:], d[k:]


def markets() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    allm = {}
    for s in SERIES:
        for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
            cur = None
            while True:
                p = {"series_ticker": s, "limit": 1000, **extra}
                if cur:
                    p["cursor"] = cur
                d = api._get(path, p)
                for m in d.get("markets", []):
                    if m.get("result") not in ("yes", "no"):
                        continue
                    dt = m["close_time"][:10]
                    if dt < "2026-03-18" or dt > LAST_DATE:
                        continue
                    allm[m["ticker"]] = (s, m)
                cur = d.get("cursor")
                if not cur or not d.get("markets"):
                    break
                time.sleep(0.5)
    dates = sorted({m["close_time"][:10] for s, m in allm.values() if FIRST_DATE <= m["close_time"][:10] <= LAST_DATE})
    dev, w1, w2, frozen = split_dates(dates)
    devset, frozenset_ = set(dev), set(frozen)
    # the frozen third is dropped here, in memory: nothing from it is written, including results and expiration values
    mk, res, exp = [], {}, {}
    for tk, (s, m) in allm.items():
        dt = m["close_time"][:10]
        if dt in frozenset_ or dt > (dev[-1] if dev else LAST_DATE):
            continue
        if dt in devset and m.get("expiration_value") not in (None, ""):
            exp[f"{s}|{dt}"] = float(m["expiration_value"])
        if dt not in devset:
            continue
        mk.append({"t": tk, "s": s, "d": dt, "close": iso_ts(m["close_time"]), "type": m.get("strike_type"), "K": m.get("floor_strike")})
        res[tk] = m["result"]
    (CACHE / "markets.json").write_text(json.dumps({"dev": dev, "w1": w1, "w2": w2, "markets": mk, "exp": exp}))
    (CACHE / "outcomes.json").write_text(json.dumps(res))
    print("dates", len(dates), "dev", len(dev), "w1", len(w1), "w2", len(w2), "frozen (not stored)", len(frozen), "dev markets", len(mk), flush=True)


def load_markets():
    return json.loads((CACHE / "markets.json").read_text())


def series_days(M):
    """{(series, date): {"close": ts, "mk": [market dicts]}} development only."""
    out = defaultdict(lambda: {"close": None, "mk": []})
    for m in M["markets"]:
        k = (m["s"], m["d"])
        out[k]["close"] = m["close"]
        out[k]["mk"].append(m)
    return out


def prev_day(sd, s, d):
    """The previous listed development date of the series within PREV_GAP_DAYS, else None (the series' first development day has none and is skipped)."""
    dates = sorted(k[1] for k in sd if k[0] == s)
    i = dates.index(d)
    if i == 0:
        return None
    pd = dates[i - 1]
    if (datetime.fromisoformat(d) - datetime.fromisoformat(pd)).days > PREV_GAP_DAYS:
        return None
    return pd


def okx() -> None:
    M = load_markets()
    sd = series_days(M)
    out = CACHE / "okx.json"
    have = json.loads(out.read_text()) if out.exists() else {}
    n = 0
    for (s, d), v in sorted(sd.items()):
        key = f"{s}|{d}"
        if key in have:
            continue
        inst = SERIES[s] + "-USDT-SWAP"
        bars = {}
        after = v["close"] * 1000
        for _ in range(2):
            data = _json_curl(f"https://www.okx.com/api/v5/market/history-candles?instId={inst}&bar=5m&limit=100&after={after}")
            if not data:
                break
            for x in data:
                bars[int(x[0]) // 1000] = float(x[4])
            after = int(data[-1][0])
            time.sleep(0.15)
        have[key] = bars
        n += 1
        if n % 100 == 0:
            out.write_text(json.dumps(have))
            print(n, flush=True)
        time.sleep(0.15)
    out.write_text(json.dumps(have))
    print("okx done", len(have), "series-days", flush=True)


def day_states(M, sd, bars_all, s, d):
    """{'A': (S, sg) or None, 'B': ...} for one series-day, using only data before each look."""
    c = sd[(s, d)]["close"]
    bars = bars_all.get(f"{s}|{d}") or {}
    pd = prev_day(sd, s, d)
    pe = M["exp"].get(f"{s}|{pd}") if pd else None
    pbars = bars_all.get(f"{s}|{pd}") if pd else None
    out = {}
    for r, L in LOOKS.items():
        st = None
        if pe is not None and pbars:
            R = bar_close_ending(bars, c - L * 60)
            pb = bar_close_ending(pbars, sd[(s, pd)]["close"])
            sg = sigma_min(bars, c - L * 60)
            if R and pb and sg is not None:
                st = (R * pe / pb, sg)
        out[r] = st
    return out


def prefilter(S_sg: dict, markets_: list, c: int):
    """Strikes with model P(YES) in [P_LO, P_HI] at either look (OKX only)."""
    keep = []
    for m in markets_:
        if m["type"] != "greater" or m["K"] is None:
            continue
        ok = False
        for r, st in S_sg.items():
            if st is None:
                continue
            p = p_yes(st[0], float(m["K"]), st[1], LOOKS[r])
            if P_LO <= p <= P_HI:
                ok = True
        if ok:
            keep.append(m)
    return keep


def candles() -> None:
    M = load_markets()
    sd = series_days(M)
    bars_all = {k: {int(a): b for a, b in v.items()} for k, v in json.loads((CACHE / "okx.json").read_text()).items()}
    order = sorted(sd, key=lambda k: rank_key(*k))
    cpath = CACHE / "candles.jsonl"
    done = set()
    if cpath.exists():
        done = {(x["s"], x["d"]) for x in map(json.loads, cpath.read_text().splitlines())}
    cf = cpath.open("a")
    t0 = time.time()
    nreq = 0
    for (s, d) in order:
        if (s, d) in done:
            continue
        if time.time() - t0 > FETCH_CAP_S:
            print("fetch cap reached", flush=True)
            break
        c = sd[(s, d)]["close"]
        st = day_states(M, sd, bars_all, s, d)
        keep = prefilter(st, sd[(s, d)]["mk"], c) if st else []
        rec = {"s": s, "d": d, "close": c, "states": st, "cands": {}}
        for m in keep:
            lo, hi = c - 7 * 3600, c - 59 * 60
            path = (f"/historical/markets/{m['t']}/candlesticks" if m["d"] < HIST_CUT
                    else f"/series/{s}/markets/{m['t']}/candlesticks")
            try:
                dd = api._get(path, {"start_ts": lo, "end_ts": hi, "period_interval": 1})
            except Exception as e:
                print("  fail", m["t"], str(e)[:60], flush=True)
                continue
            rec["cands"][m["t"]] = [[x.get("end_period_ts"), quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask")), None] for x in dd.get("candlesticks", [])]
            nreq += 1
            time.sleep(0.4)
        rec["states"] = {r: (list(v) if v else None) for r, v in st.items()}
        cf.write(json.dumps(rec) + "\n")
        cf.flush()
        if len(done) % 10 == 0:
            print(s, d, len(keep), "strikes; requests", nreq, flush=True)
        done.add((s, d))
    cf.close()
    print("candles done", len(done), "of", len(order), flush=True)


# ------------------------------------------------------------------ score
def stats(rows: list):
    """rows: (cluster, price, won, p, date). -> dict of n, days, win, price, PF, mean, z, mean at fees x1.2, mean at +1c."""
    if not rows:
        return {"n": 0}
    nets = [(r[0], net(r[2], r[1])) for r in rows]
    w = [x for _, x in nets if x > 0]
    l = [-x for _, x in nets if x < 0]
    m, se, z = cluster_mean_z(nets)
    return {"n": len(rows), "days": len({r[4] for r in rows}), "win": sum(1 for r in rows if r[2]) / len(rows),
            "price": sum(r[1] for r in rows) / len(rows), "pf": (sum(w) / sum(l)) if l else float("inf"),
            "mean": m, "z": z,
            "mean12": sum(net(r[2], r[1], STRESS) for r in rows) / len(rows),
            "mean_slip": sum(net(r[2], min(r[1] + 0.01, 0.99)) for r in rows) / len(rows)}


def fmt(name: str, st: dict) -> str:
    if st["n"] == 0:
        return f"{name}: n 0"
    pf = "inf" if st["pf"] == float("inf") else f"{st['pf']:.2f}"
    return (f"{name}: n {st['n']} days {st['days']} win {st['win']*100:.1f}% price {st['price']:.3f} PF {pf} mean {st['mean']*100:+.2f}c "
            f"z {st['z']:+.2f} | x1.2 {st['mean12']*100:+.2f}c | +1c {st['mean_slip']*100:+.2f}c")


def build(prefix_len: int | None = None):
    M = load_markets()
    res = json.loads((CACHE / "outcomes.json").read_text())
    w1set, w2set = set(M["w1"]), set(M["w2"])
    recs = [json.loads(x) for x in (CACHE / "candles.jsonl").read_text().splitlines()]
    by = {(r["s"], r["d"]): r for r in recs}
    order = sorted({k for k in series_days(M)}, key=lambda k: rank_key(*k))
    # longest rank prefix completed for ALL six series: per series, its own ranked list; the prefix is in per-series rank positions
    per = {s: [k for k in order if k[0] == s] for s in SERIES}
    L = min(len(per[s]) for s in SERIES)
    k = 0
    while k < L and all(per[s][k] in by for s in SERIES):
        k += 1
    use = {x for s in SERIES for x in per[s][:k]} if prefix_len is None else {x for s in SERIES for x in per[s][:prefix_len]}
    return M, res, by, use, k, w1set, w2set


def score() -> None:
    M, res, by, use, k, w1set, w2set = build()
    out = [f"COMDAY1 run {datetime.now(timezone.utc).isoformat()} z bar 5.27 (N about 730,119); fee 7% x C x p x (1-p) rounded up, C={C}, taker at the quote in force at D+60",
           f"rank prefix completed for all six series: {k} series-days each ({len(use)} series-days); development only, W3 never loaded",
           f"days W1 {len(M['w1'])} W2 {len(M['w2'])}"]
    for rule, L in LOOKS.items():
        H = L
        treated, control, cal, nskip = [], [], [], defaultdict(int)
        per_series = defaultdict(list)
        for (s, d) in sorted(use):
            r = by.get((s, d))
            if not r:
                continue
            st = (r["states"] or {}).get(rule)
            if not st:
                nskip["no_state"] += 1
                continue
            S, sg = st
            D = r["close"] - L * 60
            cl = f"{s}|{d}"
            sides = []
            for tk, cs in r["cands"].items():
                K = next((m["K"] for m in M["markets"] if m["t"] == tk), None)
                if K is None:
                    continue
                q = quote_at(cs, D)
                if q is None:
                    nskip["no_quote"] += 1
                    continue
                for side, price, p, pG in sides_at(S, sg, H, float(K), q):
                    won = (res[tk] == "yes") == (side == "yes")
                    sides.append((tk, side, price, p, pG, won))
            for tk, side, price, p, pG, won in sides:
                control.append((cl, price, won, p, d))
                cal.append((price, p, pG, won, p / price))
            picks = treated_picks([(x[0], x[1], x[2], x[3], x[4]) for x in sides])
            for pk in picks:
                x = next(y for y in sides if y[0] == pk[0] and y[1] == pk[1])
                row = (cl, x[2], x[5], x[3], d)
                treated.append(row)
                per_series[s].append(row)
        w = lambda rows, ws: [x for x in rows if x[4] in ws]
        out.append(f"=== RULE {rule} (look {L} min before the close)  skipped: {dict(nskip)}")
        for nm, rows in (("TREATED", treated), ("CONTROL (all cheap strike-sides)", control)):
            out.append(fmt(f"{nm} W1", stats(w(rows, w1set))))
            out.append(fmt(f"{nm} W2", stats(w(rows, w2set))))
            out.append(fmt(f"{nm} W1+W2", stats(rows)))
        out.append("per series (treated, W1+W2; descriptive):")
        for s in SERIES:
            out.append("  " + fmt(s, stats(per_series[s])))
        out.append("calibration of every cheap strike-side (price 0.03 to 0.30), W1+W2 by ratio p/price (t4) :")
        for nm, lo, hi in (("ratio<1", 0, 1), ("1<=ratio<3", 1, 3), ("ratio>=3", 3, 1e9)):
            b = [x for x in cal if lo <= x[4] < hi]
            if b:
                out.append(f"  {nm}: n {len(b)} price {sum(x[0] for x in b)/len(b):.3f} win {sum(1 for x in b if x[3])/len(b):.3f} model t4 {sum(x[1] for x in b)/len(b):.3f} gauss {sum(x[2] for x in b)/len(b):.3f}")
        out.append("calibration by model p (t4):")
        for lo, hi in ((0.03, 0.09), (0.09, 0.2), (0.2, 0.4), (0.4, 0.98)):
            b = [x for x in cal if lo <= x[1] < hi]
            if b:
                out.append(f"  p {lo}-{hi}: n {len(b)} price {sum(x[0] for x in b)/len(b):.3f} win {sum(1 for x in b if x[3])/len(b):.3f} model t4 {sum(x[1] for x in b)/len(b):.3f} gauss {sum(x[2] for x in b)/len(b):.3f}")
        s1, s2, sp = stats(w(treated, w1set)), stats(w(treated, w2set)), stats(treated)
        c1, c2 = stats(w(control, w1set)), stats(w(control, w2set))
        ntr = sp["n"]
        ndates = len({x[4] for x in treated}) or 1
        dev_dates = len(set(M["w1"]) | set(M["w2"]))
        rate = ntr / max(dev_dates, 1)
        if ntr < NMAX:
            verdict = f"NOT_ENOUGH_DATA ({ntr} treated trades under {NMAX}; {rate:.3f} per development date pooled, days to go at that rate {((NMAX - ntr) / rate) if rate > 0 else float('inf'):.0f} dates of listing)"
        else:
            bad = []
            for nm, s_ in (("W1", s1), ("W2", s2)):
                if s_["n"] == 0 or not s_["mean"] > 0:
                    bad.append(f"{nm} mean not above 0")
                if s_["n"] and s_["pf"] < 1.5:
                    bad.append(f"{nm} PF {s_['pf']:.2f} under 1.5")
            if not sp["mean12"] > 0:
                bad.append("fees x1.2 mean not above 0")
            for nm, s_, c_ in (("W1", s1, c1), ("W2", s2, c2)):
                if s_["n"] and c_["n"] and not s_["mean"] > c_["mean"]:
                    bad.append(f"{nm} treated not above control")
            verdict = ("FALSIFIED: " + "; ".join(bad)) if bad else ("NOT_YET_FALSIFIED" if sp["z"] >= 5.27 else "LEAD_ONLY (all lines hold but z under 5.27)")
        out.append(f"RULE {rule} VERDICT: {verdict}")
    text = "\n".join(out)
    print(text)
    (CACHE / "result.txt").write_text(text)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    {"markets": markets, "okx": okx, "candles": candles, "score": score}[cmd]()


if __name__ == "__main__":
    main(sys.argv)
