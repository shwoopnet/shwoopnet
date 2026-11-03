"""NOWCAST1 (workers/NOWCAST1_REGISTRATION.md): macro release ladders against a public nowcast, cheap side with a 3x ratio rule. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
    python -m scalper.nowcast1 fetch    (GDP markets, FRED GDPNOW via curl, GDP hourly candles; resumable; CPI/core/PCE reuse data/cpi1 and data/econnew2)
    python -m scalper.nowcast1 prep     (release-series list, windows and the holdout cutoff from dates only; reads no price)
    python -m scalper.nowcast1 run      (the one scored read of development H1 and H2; the frozen holdout is never computed; refused a second time)
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import numpy as np

from . import api, cpi1, econnew2
from .calibration import cluster_mean_z
from .econnew1 import pick
from .paths import DATA_DIR

D = DATA_DIR / "nowcast1"
RESULT = DATA_DIR / "nowcast1_result.txt"
UTC = timezone.utc
LO, HI, RATIO, MAX_SPREAD, LEAD_S, MAX_AGE_S, SD_FLOOR, GDP_SD, C = 0.03, 0.30, 3.0, 0.10, 86400, 6 * 3600, 0.04, 1.2, 10
GDP_START = datetime(2023, 4, 1, tzinfo=UTC)
MAX_SETTLE_DELAY_S = 7 * 86400
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPNOW"


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def fee_order(p, mult=1.0, c=C):
    """7% x C x p x (1-p) rounded UP to the cent per order (mult scales it for the x1.2 view)."""
    return math.ceil(round(mult * 0.07 * c * p * (1 - p) * 100, 9)) / 100


def p_above(nc, sd, strike):
    """P(printed value >= strike + 0.05), the reference printed to one decimal."""
    return 1 - phi((strike + 0.05 - nc) / max(sd, SD_FLOOR))


def choose(strikes, ratio=RATIO, spread=MAX_SPREAD):
    """strikes: [(ticker, bid, ask, p_yes)]. One trade per release-series: (ticker, side, price, ratio) or None. Hard limit HI, never filled higher."""
    best = None
    for tk, bid, ask, p in strikes:
        if spread is not None and ask - bid > spread + 1e-9:
            continue
        for side, price, pw in (("yes", ask, p), ("no", 1 - bid, 1 - p)):
            if LO <= price <= HI + 1e-9 and pw >= ratio * price:
                key = (pw / price, -price)
                if best is None or key > best[0]:
                    best = (key, (tk, side, price, pw / price))
    return best[1] if best else None


def settle(side, price, yes, mult=1.0):
    win = yes if side == "yes" else (not yes)
    return ((1.0 if win else 0.0) - price) - fee_order(price, mult) / C


# ---------------------------------------------------------------- fetch
def fetch():
    D.mkdir(exist_ok=True)
    if not (D / "gdpnow.csv").exists():
        out = subprocess.run(["curl", "-sS", "--http1.1", "-m", "60", FRED], capture_output=True, text=True, check=True).stdout
        (D / "gdpnow.csv").write_text(out)
    if not (D / "gdp_markets.json").exists():
        out = {}
        for s in ("KXGDP", "GDP"):
            for path, key in (("/historical/markets", "hist"), ("/markets", "live")):
                cur = None
                while True:
                    p = {"series_ticker": s, "limit": 1000}
                    if key == "live":
                        p["status"] = "settled"
                    if cur:
                        p["cursor"] = cur
                    d = api._get(path, p)
                    for m in d.get("markets", []):
                        if m.get("result") in ("yes", "no"):
                            out[m["ticker"]] = {"t": m["ticker"], "ev": m["event_ticker"], "res": m["result"], "close": m["close_time"], "strike": m.get("floor_strike"),
                                                "type": m.get("strike_type"), "val": m.get("expiration_value"), "settle": m.get("settlement_ts"), "exp": m.get("expiration_time"), "src": key, "series": s}
                    cur = d.get("cursor")
                    if not cur or not d.get("markets"):
                        break
        (D / "gdp_markets.json").write_text(json.dumps(out))
    print("fetched", flush=True)


def gdp_candles():
    mk = gdp_universe()
    cp = D / "gdp_candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    for i, (tk, m) in enumerate(mk.items()):
        if tk in have:
            continue
        close = int(ts(m["close"]).timestamp())
        try:
            path = f"/historical/markets/{tk}/candlesticks" if m["src"] == "hist" else f"/series/{m['series']}/markets/{tk}/candlesticks"
            d = api._get(path, {"start_ts": close - 4 * 86400, "end_ts": close - 20 * 3600, "period_interval": 60})
            have[tk] = [(c["end_period_ts"], pick(c.get("yes_bid")), pick(c.get("yes_ask")), api.f(c.get("volume_fp") if c.get("volume_fp") is not None else c.get("volume")), pick(c.get("price"))) for c in d.get("candlesticks", [])]
        except Exception as e:
            print("skip", tk, e); continue
        if i % 25 == 0:
            cp.write_text(json.dumps(have)); print(i, len(mk), flush=True)
        time.sleep(0.4)
    cp.write_text(json.dumps(have)); print("done", len(have), flush=True)


# ---------------------------------------------------------------- universes
def gdpnow():
    rows = list(csv.reader(io.StringIO((D / "gdpnow.csv").read_text())))[1:]
    return {r[0]: float(r[1]) for r in rows if len(r) > 1 and r[1] not in ("", ".")}


def gdp_quarter(close):
    """First day of the reference quarter from the release month (Jan/Feb -> prior Q4, Mar-May -> Q1, Jun-Aug -> Q2, Sep-Dec -> Q3)."""
    m, y = close.month, close.year
    if m <= 2:
        return f"{y - 1}-10-01"
    return f"{y}-{'01' if m <= 5 else '04' if m <= 8 else '07'}-01"


def gdp_universe():
    p = D / "gdp_markets.json"
    mk = json.loads(p.read_text())
    now = gdpnow()
    out = {}
    for t, x in mk.items():
        if x["type"] != "greater" or x["strike"] is None:
            continue
        close = ts(x["close"])
        if close < GDP_START:
            continue
        st = x.get("settle") or x.get("exp")
        if st and (ts(st) - close).total_seconds() > MAX_SETTLE_DELAY_S:
            continue  # amendment 1: a delayed release makes the 24 hour look precede the final nowcast by weeks
        q = gdp_quarter(close)
        if q not in now:
            continue
        out[t] = dict(x, kind="gdp", rs=x["ev"], nc=now[q])
    return out


def cpi_family():
    """{release-series key: dict(close, strikes=[(ticker, strike, res, candles, ncfun)])} for head, core (cpi1) and PCE (econnew2)."""
    rel = {}
    for kind in cpi1.SERIES:
        tbl = cpi1.nowcast_table(kind)
        months = sorted(tbl, key=lambda r: (int(r.split("-")[0]), int(r.split("-")[1])))
        errs = [((int(r.split("-")[0]), int(r.split("-")[1])), tbl[r]["actual"] - tbl[r]["nc"][-1][1]) for r in months if tbl[r]["actual"] is not None and tbl[r]["nc"]]
        ms = json.loads((cpi1.D / f"markets_{kind}.json").read_text())
        cd = json.loads((cpi1.D / f"candles_{kind}.json").read_text())
        for tk, m in ms.items():
            if m["type"] != "greater" or m["strike"] is None:
                continue
            ev = m["ev"].split("-")[-1]
            yy, mon = 2000 + int(ev[:2]), cpi1.MONTHS.get(ev[2:5])
            if mon is None or f"{yy}-{mon}" not in tbl:
                continue
            prior = [e for r, e in errs if r < (yy, mon)]
            if len(prior) < cpi1.MIN_ERR_MONTHS:
                continue
            key = (kind, m["ev"])
            r = rel.setdefault(key, {"close": ts(m["close"]), "kind": kind, "tbl": tbl[f"{yy}-{mon}"], "sd": float(np.std(prior, ddof=1)), "strikes": []})
            r["strikes"].append((tk, m["strike"], m["res"], cd.get(tk, [])))
    # core PCE, as econnew2
    mk = json.loads((econnew2.D / "markets.json").read_text())
    ptbl = econnew2.nowcast_table(); perr = econnew2.pce_errors(ptbl)
    pc = json.loads((econnew2.D / "candles.json").read_text())
    for tk, x in econnew2.pce_markets(mk).items():
        rm = econnew2.ref_month(x["ev"])
        prior = [e for r, e in perr if r < rm]
        key = ("pce", x["ev"])
        r = rel.setdefault(key, {"close": ts(x["close"]), "kind": "pce", "tbl": ptbl[x["ref"]], "sd": float(np.std(prior, ddof=1)), "strikes": []})
        r["strikes"].append((tk, x["strike"], x["res"], pc.get(tk, [])))
    return rel


def vintage_value(tbl, close, pdate):
    return econnew2.vintage({"x": tbl}, "x", close, pdate)


def quote_of(close, cs):
    dec = int(close.timestamp()) - LEAD_S
    q = [c for c in cs if c[0] <= dec and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1 and dec - c[0] <= MAX_AGE_S]
    return (q[-1][1], q[-1][2], q[-1][0]) if q else None


def release_series():
    """All eligible release-series, dates only plus (later) quotes: [dict(key, kind, close, strikes=[(tk, strike, res, p_fn_args...)])]."""
    out = []
    for key, r in cpi_family().items():
        out.append({"key": key, "kind": r["kind"], "close": r["close"], "r": r})
    g = gdp_universe()
    byev = {}
    for t, x in g.items():
        byev.setdefault(x["ev"], []).append(x)
    for ev, xs in byev.items():
        out.append({"key": ("gdp", ev), "kind": "gdp", "close": ts(xs[0]["close"]), "r": {"xs": xs}})
    out.sort(key=lambda r: (r["close"], str(r["key"])))
    return out


def windows(rs):
    n = len(rs); dev = (2 * n) // 3; h1 = dev // 2
    return {"dev_n": dev, "h1_n": h1, "hold_n": n - dev, "cut_dev": rs[dev]["close"].date().isoformat() if dev < n else None,
            "cut_h": rs[h1]["close"].date().isoformat()}


def prep():
    rs = release_series(); w = windows(rs)
    by = {}
    for r in rs:
        by[r["kind"]] = by.get(r["kind"], 0) + 1
    (D / "windows.json").write_text(json.dumps(dict(w, by_kind=by, n=len(rs))))
    print("eligible release-series", len(rs), by, w)


# ---------------------------------------------------------------- trades
def trades_for(rs, w, ratio=RATIO, spread=MAX_SPREAD, mult=1.0, kinds=None):
    gc = json.loads((D / "gdp_candles.json").read_text()) if (D / "gdp_candles.json").exists() else {}
    out = []
    for i, r in enumerate(rs):
        if i >= w["dev_n"]:
            break  # frozen holdout: never touched
        if kinds and r["kind"] not in kinds:
            continue
        strikes = []
        if r["kind"] == "gdp":
            for x in r["r"]["xs"]:
                q = quote_of(r["close"], gc.get(x["t"], []))
                if q:
                    strikes.append((x["t"], q[0], q[1], p_above(x["nc"], GDP_SD, x["strike"]), x["res"]))
        else:
            rr = r["r"]
            for tk, strike, res, cs in rr["strikes"]:
                q = quote_of(r["close"], cs)
                if not q:
                    continue
                pdate = datetime.fromtimestamp(q[2], UTC).date()
                v = vintage_value(rr["tbl"], r["close"], pdate)
                if v is None:
                    continue
                strikes.append((tk, q[0], q[1], p_above(v, rr["sd"], strike), res))
        pick_ = choose([(a, b, c, d) for a, b, c, d, _ in strikes], ratio, spread)
        if pick_:
            tk, side, price, rat = pick_
            res = next(s[4] for s in strikes if s[0] == tk)
            out.append({"i": i, "key": r["key"], "kind": r["kind"], "date": r["close"].date().isoformat(), "tk": tk, "side": side, "price": price, "ratio": rat,
                        "win": (res == "yes") == (side == "yes"), "net": settle(side, price, res == "yes", mult), "half": 1 if i < w["h1_n"] else 2})
    return out


def pf(xs):
    wn = sum(x for x in xs if x > 0); ls = -sum(x for x in xs if x < 0)
    return wn / ls if ls else float("inf")


def line(label, tr):
    if not tr:
        return f"{label}: no trades"
    nets = [t["net"] for t in tr]; m, _, z = cluster_mean_z([(t["date"], t["net"]) for t in tr])
    return (f"{label}: {len(tr)} trades on {len({t['date'] for t in tr})} dates, win {100 * np.mean([t['win'] for t in tr]):.1f}% vs mean price {100 * np.mean([t['price'] for t in tr]):.1f}c, "
            f"PF {pf(nets):.2f}, mean {100 * m:+.2f}c, date-clustered z {z:+.2f}")


def main(argv):
    if len(argv) < 2 or argv[1] not in ("fetch", "candles", "prep", "run"):
        print(__doc__); return
    D.mkdir(exist_ok=True)
    if argv[1] == "fetch":
        fetch(); return
    if argv[1] == "candles":
        gdp_candles(); return
    if argv[1] == "prep":
        prep(); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    rs = release_series(); w = windows(rs)
    L = [f"windows {w} (holdout of {w['hold_n']} release-series never computed)"]
    tr = trades_for(rs, w); tr12 = trades_for(rs, w, mult=1.2)
    h1 = [t for t in tr if t["half"] == 1]; h2 = [t for t in tr if t["half"] == 2]
    L += [line("DEV pooled", tr), line("H1", h1), line("H2", h2), "fees x1.2 PF " + (f"{pf([t['net'] for t in tr12]):.2f}" if tr12 else "n/a")]
    for k in ("head", "core", "pce", "gdp"):
        L.append(line("  info " + k, [t for t in tr if t["kind"] == k]))
    for rat in (2.0, 5.0):
        L.append(line(f"  info ratio {rat}", trades_for(rs, w, ratio=rat)))
    L.append(line("  info no spread cap", trades_for(rs, w, spread=None)))
    nets = [t["net"] for t in tr]
    verdict = "NOT_ENOUGH_DATA"
    if tr:
        m1 = np.mean([t["net"] for t in h1]) if h1 else None; m2 = np.mean([t["net"] for t in h2]) if h2 else None
        if m1 is None or m2 is None or m1 <= 0 or m2 <= 0 or pf(nets) < 1.5:
            verdict = "FALSIFIED"
    if len(tr) < 100 and verdict != "FALSIFIED":
        verdict = "NOT_ENOUGH_DATA"
    L.insert(0, f"NOWCAST1 {verdict} (n {len(tr)} development trades; NOT_ENOUGH_DATA floor 100 development / 150 total)")
    RESULT.write_text("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv)
