"""MORTGAGE1 (workers/MORTGAGE1_REGISTRATION.md): Kalshi weekly 30 year mortgage rate (KX30YMORTW) against a PMMS nowcast from the daily 10 year yield.
Research only; verdict words FALSIFIED / NOT_YET_FALSIFIED / NOT_ENOUGH_DATA / NOT_RUNNABLE. Nothing here means trade; no promote verb.
    python -m scalper.mortgage1 fetch   (FRED MORTGAGE30US and DGS10, Kalshi listing and hourly candles into data/mortgage1/; resumable)
    python -m scalper.mortgage1 run     (the one scored read; refused a second time)
Historical candles name fields close, live ones close_dollars: econnew1.pick reads both.
"""
from __future__ import annotations

import csv
import json
import math
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone

import numpy as np

from . import api
from .calibration import cluster_mean_z
from .econnew1 import fee, line, pick, pnl, stats
from .paths import DATA_DIR

D = DATA_DIR / "mortgage1"
RESULT = DATA_DIR / "mortgage1_result.txt"
SERIES = "KX30YMORTW"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
UTC = timezone.utc
EDGE, MAX_SPREAD, MAX_AGE_S, LOOK_HOUR = 0.08, 0.10, 6 * 3600, 12
MIN_FIT_WEEKS, FIT_START = 150, date(2010, 1, 7)
BAR_PF, MIN_TRADES = 1.5, 150


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def load_fred(name):
    out = {}
    for r in list(csv.reader(open(D / f"{name}.csv")))[1:]:
        try:
            out[date.fromisoformat(r[0])] = float(r[1])
        except (ValueError, IndexError):
            pass
    return out


def last_on_or_before(series, d, back=7):
    for i in range(back + 1):
        v = series.get(d - timedelta(days=i))
        if v is not None:
            return v
    return None


def week_x(pmms, y10, d):
    """For the PMMS date d: (previous PMMS, change in the 10y between the Wednesdays before the previous and this release). Only data dated before d."""
    prev = [x for x in pmms if x < d]
    if not prev:
        return None
    p0 = max(prev)
    y1 = last_on_or_before(y10, d - timedelta(days=1))
    y0 = last_on_or_before(y10, p0 - timedelta(days=1))
    if y1 is None or y0 is None:
        return None
    return pmms[p0], y1 - y0


def fit(pmms, y10, before):
    """OLS of the weekly PMMS change on the weekly 10y change using PMMS weeks strictly before the date `before`. Returns (a, b, sd) or None."""
    xs, ys = [], []
    for d in sorted(pmms):
        if d < FIT_START or d >= before:
            continue
        w = week_x(pmms, y10, d)
        if w:
            xs.append(w[1]); ys.append(pmms[d] - w[0])
    if len(xs) < MIN_FIT_WEEKS:
        return None
    X = np.column_stack([np.ones(len(xs)), xs])
    beta, *_ = np.linalg.lstsq(X, np.array(ys), rcond=None)
    res = np.array(ys) - X @ beta
    return float(beta[0]), float(beta[1]), float(res.std(ddof=2))


def fair_above(k, centre, sd):
    """P(two decimal print > k): the print is above k if it is at least k + 0.01."""
    return 1 - ncdf((k + 0.005 - centre) / sd)


def decide(fair, bid, ask, edge=EDGE, max_spread=MAX_SPREAD, side_only_cheap=False):
    """(side, price) or None. YES at the ask when fair - ask >= edge, NO at 1 - bid when bid - fair >= edge. Needs a valid two sided quote within the spread cut."""
    if not (bid is not None and ask is not None and 0 < bid < ask < 1) or ask - bid > max_spread + 1e-12:
        return None
    out = None
    if fair - ask >= edge - 1e-12:
        out = ("yes", ask)
    elif bid - fair >= edge - 1e-12:
        out = ("no", 1 - bid)
    if out and side_only_cheap and out[1] >= 0.5:
        return None
    return out


def split3(events):
    n = len(events); a, b = n // 3, 2 * (n // 3)
    return {e: ("w1" if i < a else "w2" if i < b else "w3") for i, e in enumerate(events)}


def get_text(u):
    for i in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read().decode()
        except Exception as e:
            print("get", e); time.sleep(10 * (i + 1))
    raise RuntimeError("unreachable " + u)


def fetch():
    D.mkdir(exist_ok=True)
    for n in ("MORTGAGE30US", "DGS10"):
        if not (D / f"{n}.csv").exists():
            (D / f"{n}.csv").write_text(get_text(FRED + n))
    if not (D / "markets.json").exists():
        out = {}
        for path, key in (("/historical/markets", "hist"), ("/markets", "live")):
            cur = None
            while True:
                p = {"series_ticker": SERIES, "limit": 1000}
                if key == "live":
                    p["status"] = "settled"
                if cur:
                    p["cursor"] = cur
                d = api._get(path, p)
                for m in d.get("markets", []):
                    if m.get("result") in ("yes", "no"):
                        out[m["ticker"]] = {"t": m["ticker"], "ev": m["event_ticker"], "res": m["result"], "close": m["close_time"],
                                            "strike": m.get("floor_strike"), "type": m.get("strike_type"), "val": m.get("expiration_value"), "src": key}
                cur = d.get("cursor")
                if not cur or not d.get("markets"):
                    break
        (D / "markets.json").write_text(json.dumps(out))
    mk = json.loads((D / "markets.json").read_text())
    cf = D / "candles.json"
    have = json.loads(cf.read_text()) if cf.exists() else {}
    for tk, m in mk.items():
        if tk in have:
            continue
        close = int(datetime.fromisoformat(m["close"].replace("Z", "+00:00")).timestamp())
        path = f"/historical/markets/{tk}/candlesticks" if m["src"] == "hist" else f"/series/{SERIES}/markets/{tk}/candlesticks"
        d = api._get(path, {"start_ts": close - 4 * 86400, "end_ts": close, "period_interval": 60})
        have[tk] = [(c["end_period_ts"], pick(c.get("yes_bid")), pick(c.get("yes_ask"))) for c in d.get("candlesticks", [])]
        cf.write_text(json.dumps(have))
    print("fetched", len(mk), "markets", flush=True)


def event_date(ev):
    s = ev.split("-")[-1]
    return datetime.strptime(s, "%y%b%d").date()


def quote_at(cs, look):
    q = [c for c in cs if c[0] <= look and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1 and look - c[0] <= MAX_AGE_S]
    return (q[-1][1], q[-1][2]) if q else None


def brier(pairs):
    return sum((p - o) ** 2 for p, o in pairs) / len(pairs) if pairs else float("nan")


def run():
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    pmms, y10 = load_fred("MORTGAGE30US"), load_fred("DGS10")
    mk = json.loads((D / "markets.json").read_text()); cd = json.loads((D / "candles.json").read_text())
    evs = sorted({m["ev"] for m in mk.values()}, key=event_date)
    win = split3(evs)
    out = [f"MORTGAGE1 single run, {len(evs)} settled weekly events, {len(mk)} markets"]
    trades = {"A": [], "B": []}; trades_x = {"A": []}; bm, bk, bp = [], [], []
    skipped = []
    for ev in evs:
        d = event_date(ev)
        w = week_x(pmms, y10, d); f = fit(pmms, y10, d)
        if not w or not f:
            skipped.append(ev); continue
        a, b, sd = f
        centre = w[0] + a + b * w[1]; centre0 = w[0] + a
        look = int(datetime(d.year, d.month, d.day, LOOK_HOUR, tzinfo=UTC).timestamp())
        for m in (x for x in mk.values() if x["ev"] == ev and x["type"] == "greater" and x["strike"] is not None):
            q = quote_at(cd.get(m["t"], []), look)
            if not q:
                continue
            bid, ask = q
            if ask - bid > MAX_SPREAD + 1e-12:
                continue
            k = float(m["strike"]); fair = fair_above(k, centre, sd); res = 1.0 if m["res"] == "yes" else 0.0
            bm.append((fair, res)); bk.append(((bid + ask) / 2, res)); bp.append((fair_above(k, centre0, sd), res))
            for tag, cheap in (("A", False), ("B", True)):
                dec = decide(fair, bid, ask, side_only_cheap=cheap)
                if dec:
                    trades[tag].append((ev, dec[0], dec[1], m["res"]))
    out.append(f"events skipped (no fit or data): {len(skipped)}")
    out.append(f"Brier at the look over {len(bm)} quoted strikes: nowcast {brier(bm):.4f}, persistence {brier(bp):.4f}, market mid {brier(bk):.4f}")
    for tag in ("A", "B"):
        tr = trades[tag]
        out.append(f"TRY {tag}: {len(tr)} trades")
        for wn in ("w1", "w2", "w3"):
            rows = [(e, pnl(s, p, r)) for e, s, p, r in tr if win[e] == wn]
            out.append(line(f"  {wn} (fees x1)", stats(rows)))
        allr = [(e, pnl(s, p, r)) for e, s, p, r in tr]
        allx = [(e, pnl(s, p, r, 1.2)) for e, s, p, r in tr]
        out.append(line("  pooled x1", stats(allr))); out.append(line("  pooled x1.2", stats(allx)))
    tr = trades["A"]
    pf = {wn: stats([(e, pnl(s, p, r)) for e, s, p, r in tr if win[e] == wn]) for wn in ("w1", "w2", "w3")}
    n = len(tr); brier_ok = brier(bm) < brier(bk)
    if n < MIN_TRADES:
        v = "NOT_ENOUGH_DATA"
    elif any(pf[w]["n"] >= 5 and pf[w]["pf"] < BAR_PF for w in pf) or not brier_ok:
        v = "FALSIFIED"
    else:
        v = "NOT_YET_FALSIFIED"
    pf_low = any(pf[w]["n"] >= 5 and pf[w]["pf"] < BAR_PF for w in pf)
    out.append(f"VERDICT {v} (try A: n {n} against the {MIN_TRADES} minimum; nowcast Brier better than market: {brier_ok}; a window with 5+ trades under PF {BAR_PF}: {pf_low}); cost fee at C = 10; N about 728,700, z bar 5.27")
    RESULT.write_text("\n".join(out) + "\n"); print("\n".join(out))


def main(argv):
    if len(argv) < 2 or argv[1] not in ("fetch", "run"):
        print(__doc__); return
    fetch() if argv[1] == "fetch" else run()


if __name__ == "__main__":
    main(sys.argv)
