"""GAS2 (workers/GAS2_REGISTRATION.md): cheap-side AAA gas strikes against a pooled persistence model. Research only; nothing here places an order.
Usage: python -m scalper.gas2 fetch CACHE_DIR   list markets (frozen-date rows dropped before saving), then the look candle of development markets
       python -m scalper.gas2 score CACHE_DIR   the registered read; refused a second time (delete the result file to override for a crash fix only)
       python -m scalper.gas2 book CACHE_DIR    information: live order book depth at the ask for the nearest open ladder
Verdict words: FALSIFIED, NOT_ENOUGH_DATA, NOT_YET_FALSIFIED.
"""
from __future__ import annotations

import json
import math
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from . import api
from .backfill import iso_ts, parse_candle
from .calibration import cluster_mean_z

ET = ZoneInfo("America/New_York")
SERIES_FILE = Path(__file__).resolve().parents[2] / "workers" / "GAS2_SERIES.json"
RESULT_NAME = "gas2_result.txt"
# ---- fixed in the registration ----
LOOK_S = 8 * 3600
LO, HI, HARD, RATIO, MAX_PER_DAY = 0.03, 0.30, 0.30, 3.0, 2
MIN_HIST_DATES, MIN_RESID, SIGMA_FLOOR, MIN_N, PF_BAR, STRESS, C = 14, 200, 0.0010, 150, 1.5, 1.2, 10
MIN_SERIES_DATES, BRACKET_MAX = 40, 0.003


def fee(p: float, stress: float = 1.0) -> float:
    """7% x C x p x (1-p) rounded up to the cent for C contracts, per contract."""
    raw = 0.07 * C * p * (1 - p) * stress
    return math.ceil(round(raw * 100, 9)) / 100 / C


def net_of(side: str, price: float, result: str, stress: float = 1.0) -> float:
    return (1.0 if side == result else 0.0) - price - fee(price, stress)


def profit_factor(nets: list[float]) -> float:
    w = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return w / l if l > 0 else (math.inf if w > 0 else 0.0)


def et_date(close_iso: str) -> date:
    return datetime.fromisoformat(close_iso.replace("Z", "+00:00")).astimezone(ET).date()


def event_value(markets: list[dict]) -> float | None:
    """The settled AAA value of one event: expiration_value of its markets, else the bracket midpoint from the ladder."""
    vals = []
    for m in markets:
        try:
            v = float(m.get("expiration_value"))
            vals.append(v)
        except (TypeError, ValueError):
            pass
    if vals:
        return st.median(vals)
    yes = [float(m["floor_strike"]) for m in markets if m.get("result") == "yes" and m.get("floor_strike") is not None]
    no = [float(m["floor_strike"]) for m in markets if m.get("result") == "no" and m.get("floor_strike") is not None]
    if not yes or not no:
        return None
    lo, hi = max(yes), min(no)
    if hi < lo or hi - lo > BRACKET_MAX:
        return None
    return (lo + hi) / 2


def fit_predict_samples(vals: dict[str, dict[date, float]], t: date, series: str):
    """Pooled OLS d_u = a + b d_{u-1} + dow dummies fitted on dates u < t; returns (point prediction of V_t, V_{t-1}, array of
    pooled-residual draws scaled by the series' sd) or None when the history is short."""
    X, Y, rows = [], [], []
    for s, vs in vals.items():
        for u in vs:
            if u >= t:
                continue
            p1, p2 = u - timedelta(days=1), u - timedelta(days=2)
            if p1 in vs and p2 in vs:
                d, dl = vs[u] - vs[p1], vs[p1] - vs[p2]
                wd = (u + timedelta(days=1)).weekday()
                X.append([1.0, dl] + [1.0 if wd == k else 0.0 for k in range(1, 7)])
                Y.append(d)
                rows.append((s, u))
    if len({u for _, u in rows}) < MIN_HIST_DATES:
        return None
    X, Y = np.array(X), np.array(Y)
    beta = np.linalg.lstsq(X, Y, rcond=None)[0]
    res = Y - X @ beta
    by = defaultdict(list)
    for (s, _), r in zip(rows, res):
        by[s].append(r)
    sd = {s: max(float(np.std(v)), SIGMA_FLOOR) for s, v in by.items()}
    if series not in sd:
        return None
    e = np.array([r / sd[s] for (s, _), r in zip(rows, res)])
    if len(e) < MIN_RESID:
        return None
    vs = vals[series]
    p1, p2 = t - timedelta(days=1), t - timedelta(days=2)
    if p1 not in vs or p2 not in vs:
        return None
    wd = (t + timedelta(days=1)).weekday()
    x = np.array([1.0, vs[p1] - vs[p2]] + [1.0 if wd == k else 0.0 for k in range(1, 7)])
    mu = vs[p1] + float(x @ beta)
    return mu, vs[p1], mu + sd[series] * e


def side_probs(draws: np.ndarray, strike: float) -> tuple[float, float]:
    """(P(V > K), P(V <= K)) from the empirical draws."""
    p = float((draws > strike).mean())
    return p, 1.0 - p


def pick(cands: list[dict]) -> list[dict]:
    """At most MAX_PER_DAY per series-day, highest probability/ask first."""
    out, seen = [], defaultdict(list)
    for c in sorted(cands, key=lambda c: -c["ratio"]):
        k = (c["series"], c["date"])
        if len(seen[k]) < MAX_PER_DAY:
            seen[k].append(c)
            out.append(c)
    return out


# ------------------------------------------------------------------ fetch
def fetch(cache: Path) -> None:
    cache.mkdir(parents=True, exist_ok=True)
    series = json.loads(SERIES_FILE.read_text())
    now = int(time.time())
    allm: dict[str, list[dict]] = {}
    for s in series:
        ms = []
        for m in api.settled_markets(s, now - 110 * 86400, now):
            if m.get("result") in ("yes", "no") and m.get("close_time"):
                ms.append({k: m.get(k) for k in ("ticker", "close_time", "open_time", "result", "expiration_value", "floor_strike", "strike_type", "volume")})
        allm[s] = ms
        print(s, len(ms), flush=True)
        time.sleep(1.0)
    dates_by_series = {s: {et_date(m["close_time"]) for m in ms} for s, ms in allm.items()}
    keep = [s for s in series if len(dates_by_series[s]) >= MIN_SERIES_DATES]
    alld = sorted({d for s in keep for d in dates_by_series[s]})
    cut = alld[int(len(alld) * 2 / 3) - 1]            # last development date; later dates are frozen
    dropped = 0
    dev = []
    for s in keep:
        for m in allm[s]:
            if et_date(m["close_time"]) > cut:
                dropped += 1
                continue
            m["series"], m["date"] = s, et_date(m["close_time"]).isoformat()
            dev.append(m)
    allm.clear()                                       # frozen rows leave memory without being written
    (cache / "markets.json").write_text(json.dumps({"series": keep, "cut": cut.isoformat(), "dates": len(alld), "markets": dev}))
    print(f"series kept {len(keep)} of {len(series)}; distinct dates {len(alld)}; development through {cut}; frozen rows dropped {dropped}; development markets {len(dev)}", flush=True)
    # look candles
    cf = cache / "look.json"
    look = json.loads(cf.read_text()) if cf.exists() else {}
    todo = sorted((m for m in dev if m["ticker"] not in look), key=lambda m: m["close_time"])
    step, i = 40, 0
    while i < len(todo):
        chunk = todo[i:i + step]
        lo_ts = min(iso_ts(m["close_time"]) for m in chunk) - LOOK_S - 3600
        hi_ts = max(iso_ts(m["close_time"]) for m in chunk) - LOOK_S
        if hi_ts - lo_ts > 3 * 86400:                  # candles are batched by time; keep a chunk's span short
            step = max(1, step // 2)
            continue
        try:
            got = api._get("/markets/candlesticks", {"market_tickers": ",".join(m["ticker"] for m in chunk), "start_ts": lo_ts, "end_ts": hi_ts, "period_interval": 60})
            cmap = {x.get("market_ticker"): x.get("candlesticks", []) for x in got.get("markets", [])}
        except Exception as e:
            if step > 1:
                step = max(1, step // 2)
                continue
            print("skip", chunk[0]["ticker"], e, flush=True)
            cmap = {}
        for m in chunk:
            tgt = iso_ts(m["close_time"]) - LOOK_S
            best = None
            for c in cmap.get(m["ticker"], []):
                r = parse_candle(c, m["ticker"], m["series"])
                if r and tgt - 3600 < r[2] <= tgt:
                    if best is None or r[2] > best[2]:
                        best = r
            look[m["ticker"]] = None if best is None else {"end": best[2], "bid": best[6], "ask": best[10], "vol": best[12]}
        i += len(chunk)
        cf.write_text(json.dumps(look))
        print(f"candles {i}/{len(todo)}", flush=True)
        time.sleep(0.8)
    cf.write_text(json.dumps(look))


# ------------------------------------------------------------------ score
def build(cache: Path):
    d = json.loads((cache / "markets.json").read_text())
    look = json.loads((cache / "look.json").read_text())
    byev = defaultdict(list)
    for m in d["markets"]:
        byev[(m["series"], m["date"])].append(m)
    vals: dict[str, dict[date, float]] = defaultdict(dict)
    for (s, dt), ms in byev.items():
        v = event_value(ms)
        if v is not None:
            vals[s][date.fromisoformat(dt)] = v
    return d, look, byev, vals


def valid(q) -> bool:
    return bool(q) and q["bid"] is not None and q["ask"] is not None and 0 < q["bid"] < q["ask"] < 1


def run(cache: Path) -> str:
    d, look, byev, vals = build(cache)
    rows, miss, nm = [], 0, 0
    brier_m = brier_k = nb = 0.0
    for (s, dt), ms in sorted(byev.items()):
        t = date.fromisoformat(dt)
        fp = fit_predict_samples(vals, t, s)
        if fp is None:
            continue
        mu, vprev, draws = fp
        cands = []
        for m in ms:
            q = look.get(m["ticker"])
            if not valid(q) or m.get("floor_strike") is None:
                miss += 1
                continue
            nm += 1
            k = float(m["floor_strike"])
            py, pn = side_probs(draws, k)
            mid = (q["bid"] + q["ask"]) / 2
            y = 1.0 if m["result"] == "yes" else 0.0
            brier_m += (mid - y) ** 2
            brier_k += (py - y) ** 2
            nb += 1
            for side, price, p in (("yes", q["ask"], py), ("no", 1 - q["bid"], pn)):
                if LO <= price <= HI and price <= HARD:
                    cands.append({"series": s, "date": dt, "side": side, "price": price, "p": p, "ratio": p / price, "result": m["result"], "vol": q["vol"] or 0.0,
                                  "net": net_of(side, price, m["result"]), "stress": net_of(side, price, m["result"], STRESS), "win": 1 if side == m["result"] else 0})
        rows.extend(cands)
    ctrl = rows
    model = pick([c for c in rows if c["ratio"] >= RATIO])
    scored = sorted({r["date"] for r in rows})
    half = set(scored[: (len(scored) + 1) // 2])

    def block(name: str, xs: list[dict]) -> str:
        if not xs:
            return f"{name}: n 0\n"
        nets = [x["net"] for x in xs]
        mean, se, z = cluster_mean_z([(x["date"], x["net"]) for x in xs])
        a = [x["net"] for x in xs if x["date"] in half]
        b = [x["net"] for x in xs if x["date"] not in half]
        out = (f"{name}: n {len(xs)}, days {len({x['date'] for x in xs})}, win {sum(x['win'] for x in xs)/len(xs):.3f} vs mean price {sum(x['price'] for x in xs)/len(xs):.3f}, "
               f"net {mean*100:+.2f}c, z {z:.2f}, PF {profit_factor(nets):.2f}, halves A {(sum(a)/len(a)*100 if a else float('nan')):+.2f}c (n {len(a)}) / B {(sum(b)/len(b)*100 if b else float('nan')):+.2f}c (n {len(b)}), "
               f"stress x1.2 {sum(x['stress'] for x in xs)/len(xs)*100:+.2f}c, vol>0 subset n {sum(1 for x in xs if x['vol']>0)} net {(sum(x['net'] for x in xs if x['vol']>0)/max(1,sum(1 for x in xs if x['vol']>0)))*100:+.2f}c\n")
        for lo, hi in ((0.03, 0.10), (0.10, 0.20), (0.20, 0.3001)):
            g = [x for x in xs if lo <= x["price"] < hi]
            if g:
                out += f"    ask {lo:.2f}-{min(hi,0.30):.2f}: n {len(g)}, win {sum(x['win'] for x in g)/len(g):.3f} vs price {sum(x['price'] for x in g)/len(g):.3f}, net {sum(x['net'] for x in g)/len(g)*100:+.2f}c\n"
        return out

    txt = f"GAS2 read. Series {len(vals)}, scored dates {len(scored)} ({scored[0] if scored else '-'} to {scored[-1] if scored else '-'}), markets with a valid look quote {nm}, missing or invalid {miss}\n"
    txt += f"Brier on scored markets: model {brier_k/max(nb,1):.4f} vs market mid {brier_m/max(nb,1):.4f}\n"
    txt += block("CONTROL (all cheap strikes in band)", ctrl) + block("MODEL (p >= 3 x ask, <= 2 per series-day)", model)
    for sd in ("yes", "no"):
        txt += block(f"  model side {sd}", [x for x in model if x["side"] == sd])
    per = defaultdict(int)
    for x in model:
        per[x["series"]] += 1
    txt += "model trades by series: " + ", ".join(f"{k} {v}" for k, v in sorted(per.items())) + "\n"
    n = len(model)
    if n < MIN_N:
        per_day = n / max(1, len(scored))
        togo = math.ceil((MIN_N - n) / per_day) if per_day > 0 else None
        verdict = f"NOT_ENOUGH_DATA (n {n} < {MIN_N}; {per_day:.2f} trades per scored date, about {togo} more dates needed)"
    else:
        a = [x["net"] for x in model if x["date"] in half]
        b = [x["net"] for x in model if x["date"] not in half]
        pf = profit_factor([x["net"] for x in model])
        if not (a and b and sum(a) > 0 and sum(b) > 0) or pf < PF_BAR:
            verdict = "FALSIFIED"
        else:
            verdict = "NOT_YET_FALSIFIED (a lead only; capped probe at most)"
    return txt + "VERDICT: " + verdict + "\n"


def score(cache: Path) -> None:
    out = cache / RESULT_NAME
    if out.exists():
        sys.exit(f"refused: {out} exists (one read)")
    txt = run(cache)
    out.write_text(txt)
    print(txt)


def book(cache: Path) -> None:
    series = json.loads(SERIES_FILE.read_text())
    out = []
    for s in series:
        try:
            ms = api._get("/markets", {"series_ticker": s, "status": "open", "limit": 200}).get("markets", [])
        except Exception as e:
            out.append((s, str(e)))
            continue
        for m in ms:
            ya, yb = api.f(m.get("yes_ask_dollars")), api.f(m.get("yes_bid_dollars"))
            if ya is None or yb is None or not (LO <= ya <= HI or LO <= 1 - yb <= HI):
                continue
            try:
                ob = api._get(f"/markets/{m['ticker']}/orderbook").get("orderbook_fp") or {}
            except Exception as e:
                out.append((m["ticker"], str(e)))
                continue
            out.append({"ticker": m["ticker"], "ask": ya, "bid": yb, "orderbook": {k: v[:3] for k, v in ob.items()}})
            time.sleep(0.5)
        time.sleep(0.8)
    (cache / "book_snapshot.json").write_text(json.dumps(out, default=str))
    print(len(out), "rows saved")


if __name__ == "__main__":
    cmd, path = sys.argv[1], Path(sys.argv[2])
    {"fetch": fetch, "score": score, "book": book}[cmd](path)
