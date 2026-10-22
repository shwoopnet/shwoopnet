"""WX1 (README, Pre-registration: WX1): Kalshi daily-high temperature markets against the NBS blended forecast of the previous day. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.wx1 fetch    (downloads the forecasts, markets and prices into data/wx1.json; resumable)
       python -m scalper.wx1 run      (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import csv
import io
import json
import math
import statistics as st
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from . import api
from .backfill import iso_ts, parse_candle
from .calibration import cluster_mean_z
from .paths import DATA_DIR

# ---- fixed in the README before any fetch ----
CITIES = {"KXHIGHAUS": "KAUS", "KXHIGHCHI": "KMDW", "KXHIGHDEN": "KDEN", "KXHIGHLAX": "KLAX", "KXHIGHMIA": "KMIA", "KXHIGHNY": "KNYC", "KXHIGHPHIL": "KPHL"}
THRESH, THRESH_INFO, PRICE_HOUR_UTC = 0.07, 0.03, 20
MEAN_C, Z_BAR, FALSIFY_C, FALSIFY_Z, MIN_N, MIN_DAYS, MIN_CITIES, STRESS = 0.020, 3.0, 0.005, 1.0, 300, 20, 5, 1.2
DATA, RESULT = DATA_DIR / "wx1.json", DATA_DIR / "wx1_result.txt"
MONTHS = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def p_yes(kind: str, floor, cap, mean: float, sd: float) -> float:
    """P(the market resolves YES) for a whole degree maximum ~ Normal(mean, sd): greater than floor means max >= floor + 1; less than cap means max <= cap - 1; between is inclusive."""
    sd = max(sd, 1.0)
    if kind == "greater":
        return 1 - phi((floor + 0.5 - mean) / sd)
    if kind == "less":
        return phi((cap - 0.5 - mean) / sd)
    if kind == "between":
        return phi((cap + 0.5 - mean) / sd) - phi((floor - 0.5 - mean) / sd)
    raise ValueError(kind)


def fee(p: float) -> float:
    return 0.07 * p * (1 - p)


def decide(p: float, bid: float, ask: float, thresh: float):
    """('yes', price) / ('no', price) when the expected edge after the fee clears thresh, else None."""
    if p - ask - fee(ask) >= thresh:
        return "yes", ask
    pn = 1 - bid
    if (1 - p) - pn - fee(pn) >= thresh:
        return "no", pn
    return None


def net(side: str, price: float, result: str, mult: float = 1.0) -> float:
    f = fee(price) * mult
    return (1 - price - f) if side == result else -(price + f)


def target_date(ticker: str):
    t = ticker.split("-")[1]
    return datetime(2000 + int(t[:2]), MONTHS[t[2:5]], int(t[5:7]), tzinfo=timezone.utc)


def fetch() -> None:
    cache = json.loads(DATA.read_text()) if DATA.exists() else {"nbs": {}, "markets": {}}
    now = int(time.time())
    lo = now - 69 * 86400
    days = [datetime.fromtimestamp(lo, timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(days=i) for i in range(0, 71)]
    for station in CITIES.values():
        have = cache["nbs"].setdefault(station, {})
        for d in days:
            key = d.strftime("%Y-%m-%d")
            if key in have or d > datetime.now(timezone.utc):
                continue
            ts = d.strftime("%Y-%m-%dT%H:%MZ")
            try:
                txt = urllib.request.urlopen(f"https://mesonet.agron.iastate.edu/cgi-bin/request/mos.py?station={station}&model=NBS&sts={ts}&ets={ts}&format=csv", timeout=60).read().decode()
            except Exception as e:
                print(f"  {station} {key}: {str(e)[:60]}", flush=True)
                continue
            rows = {r["ftime"]: (r["txn"], r["xnd"]) for r in csv.DictReader(io.StringIO(txt)) if r.get("txn") and r.get("xnd")}
            have[key] = rows
            time.sleep(0.7)
        DATA.write_text(json.dumps(cache))
        print(f"{station}: forecasts for {len(have)} runs", flush=True)
    for series in CITIES:
        listed = [m for m in api.settled_markets(series, lo, now) if m.get("result") in ("yes", "no")]
        for m in listed:
            cache["markets"].setdefault(m["ticker"], {"series": series, "kind": m.get("strike_type"), "floor": m.get("floor_strike"), "cap": m.get("cap_strike"), "result": m["result"], "prices": None})
        print(f"{series}: {len(listed)} settled markets", flush=True)
    by_date = defaultdict(list)
    for tk, m in cache["markets"].items():
        if m["prices"] is None:
            by_date[target_date(tk)].append(tk)
    for D, tks in sorted(by_date.items()):
        t = int((D - timedelta(days=1)).replace(hour=PRICE_HOUR_UTC).timestamp())
        try:
            got = api._get("/markets/candlesticks", {"market_tickers": ",".join(tks), "start_ts": t - 7200, "end_ts": t + 3600, "period_interval": 60})
        except Exception as e:
            print(f"  prices {D.date()}: {str(e)[:60]}", flush=True)
            continue
        cm = {x.get("market_ticker"): x.get("candlesticks", []) for x in got.get("markets", [])}
        for tk in tks:
            cs = [parse_candle(c, tk, cache["markets"][tk]["series"]) for c in cm.get(tk, [])]
            cs = [(r[2], r[6], r[10]) for r in cs if r and r[6] is not None and r[10] is not None]
            if cs:
                k = min(cs, key=lambda x: abs(x[0] - t))
                cache["markets"][tk]["prices"] = [k[1], k[2], k[0] - t]
            else:
                cache["markets"][tk]["prices"] = []
        time.sleep(0.3)
    DATA.write_text(json.dumps(cache))
    print("done:", sum(1 for m in cache["markets"].values() if m["prices"]), "markets with a price", flush=True)


def build_trades(cache: dict, thresh: float) -> list[dict]:
    out = []
    for tk, m in cache["markets"].items():
        if not m.get("prices"):
            continue
        D = target_date(tk)
        run = (D - timedelta(days=1)).strftime("%Y-%m-%d")
        fc = cache["nbs"].get(CITIES[m["series"]], {}).get(run, {})
        key = (D + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
        if key not in fc:
            continue
        mean, sd = float(fc[key][0]), float(fc[key][1])
        p = p_yes(m["kind"], m["floor"], m["cap"], mean, sd)
        bid, ask = m["prices"][0], m["prices"][1]
        d = decide(p, bid, ask, thresh)
        out.append({"day": D.strftime("%Y-%m-%d"), "city": m["series"], "p": p, "result": m["result"], "bid": bid, "ask": ask, "trade": d,
                    "net": net(d[0], d[1], m["result"]) if d else None, "stress": net(d[0], d[1], m["result"], STRESS) if d else None})
    return out


def summarize(rows: list[dict]) -> dict:
    tr = [r for r in rows if r["trade"]]
    if len(tr) < 2:
        return {"n": len(tr)}
    m, _, z = cluster_mean_z([(r["day"], r["net"]) for r in tr])
    ordered = sorted(tr, key=lambda r: r["day"])
    h = len(ordered) // 2
    cities = defaultdict(list)
    for r in tr:
        cities[r["city"]].append(r["net"])
    return {"n": len(tr), "days": len({r["day"] for r in tr}), "mean": m, "z": z, "h1": st.mean(r["net"] for r in ordered[:h]), "h2": st.mean(r["net"] for r in ordered[h:]),
            "stress": st.mean(r["stress"] for r in tr), "cities_positive": sum(1 for v in cities.values() if st.mean(v) > 0), "by_city": {k: (len(v), st.mean(v)) for k, v in cities.items()}}


def main(argv: list[str]) -> None:
    if len(argv) >= 2 and argv[1] == "fetch":
        return fetch()
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    cache = json.loads(DATA.read_text())
    rows = build_trades(cache, THRESH)
    s = summarize(rows)
    if s["n"] < MIN_N or s.get("days", 0) < MIN_DAYS:
        verdict = "NOT_ENOUGH_DATA"
    elif s["mean"] >= MEAN_C and s["z"] >= Z_BAR and s["h1"] > 0 and s["h2"] > 0 and s["stress"] > 0 and s["cities_positive"] >= MIN_CITIES:
        verdict = "NOT_YET_FALSIFIED"
    elif s["mean"] < FALSIFY_C or s["z"] < FALSIFY_Z:
        verdict = "FALSIFIED"
    else:
        verdict = "NOT_ENOUGH_DATA"
    out = [f"WX1: verdict {verdict}", f"markets with forecast and price: {len(rows)}", json.dumps(s, default=str)]
    cal = defaultdict(list)
    for r in rows:
        cal[min(9, int(r["p"] * 10))].append(1.0 if r["result"] == "yes" else 0.0)
    out.append("info: calibration (decile of model p: n, observed yes rate): " + "; ".join(f"{k}: {len(v)}, {st.mean(v):.2f}" for k, v in sorted(cal.items())))
    out.append("info: same rule at 3c threshold: " + json.dumps(summarize(build_trades(cache, THRESH_INFO)), default=str))
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
