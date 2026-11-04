"""WXOTHER1 (workers/WXOTHER1_REGISTRATION.md): remaining weather and climate families (not daily highs, lows or daily rain), cheap side only.
Research only; nothing here places an order. Cheap side (ask 3c to 30c) only: no favourite-side result is computed or printed anywhere.
    python -m scalper.wxother1 census CACHE   listings and close times only (no price, no candle, no result), before the frozen cut 2026-10-03T16:00Z
Verdict words: FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE, NOT_YET_FALSIFIED."""
from __future__ import annotations

import json
import math
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CUT = datetime(2026, 10, 3, 16, tzinfo=timezone.utc)
CUTS = CUT.strftime("%Y-%m-%dT%H:%M:%SZ")
MIN_TRADES, MIN_EVENTS, MIN_VOLUME = 150, 150, 20.0
# already covered by WX1, WX2, WX3, WXNEW1, WXENS1, WXLOW1, WXLOCK1, RAINCAL, FAMWX: daily highs, daily lows, daily rain
COVERED = re.compile(r"^(KX)?(HIGH(?!NYD)|LOW|CITIESWEATHER|DVHIGH|PHILHIGH|HOUHIGH|DENHIGH|RAIND?(?![A-Z]*M$)|RAIN$)")
NOT_WEATHER = re.compile(r"(OPEN|CLOSE)$|^(KX)?(EMERGENCY|ECLIPSE|EARTHQUAKE|ERUPT|VEI|KILAUEA|SPURR|TSUNAMI|EVSHARE|EUCLIMATE|INDIACLIMATE|USCLIMATE|FEMA|WARMING|WASDESTAT|ELNINO|RONI|DROUGHT|ERCOTX)")


EXTRA = ["KXSEAICE", "SEAICE", "KXGSTORM", "GSTORM", "KXXFLARE"]   # category World or space weather, found by title search of the full series list


def family(t: str) -> str:
    """Family label by ticker; unlisted -> other."""
    u = t[2:] if t.startswith("KX") else t
    for pat, name in ((r"^AVGTK|^AVGTATL|^HEATAPHX|^WEEKHT", "weekly temperature"), (r"SNOW", "snowfall"), (r"^RAIN.*M$|^RAINNYCW|^RAINWKND", "rain totals (month/week)"),
                      (r"^TEMP[A-Z]*H(S)?$|^HIGHNYD", "hourly directional temperature"), (r"^AVGTEMP|^TEMPMON|^TEMP$|^GTEMP|^HMONTH|^HOTYEAR", "monthly/annual temperature rank"),
                      (r"LOWT$|^MINNYC|^MONTHLOW|^MSNLOWT|^SJCLOWT|^YEARLOW|^HOLIDAYT", "monthly/annual extreme temperature"), (r"^HUR|^TROPSTORM|^NAMEDSTORM|^FIRSTHURRICANE|^NEXT", "hurricanes and storms"),
                      (r"^TORNADO", "tornadoes"), (r"^AQI", "air quality"), (r"^AVGTATL", "weekly temperature"), (r"^(G)?STORM$|^GSTORM|^XFLARE", "space weather"), (r"^SEAICE", "sea ice"), (r"^HDD|^CO2", "degree days / CO2"), (r"ARCTIC|ARTICICE", "sea ice"), (r"^MICHTEMP|^MEAD|^CORIVER", "water temperature / level")):
        if re.search(pat, u):
            return name
    return "other"


def candidates(series: list[dict]) -> list[str]:
    out = []
    for s in series:
        t = s["ticker"]
        if COVERED.search(t) or NOT_WEATHER.search(t):
            continue
        out.append(t)
    out += EXTRA
    return sorted(set(out))


def listing(series: str) -> list:
    from . import api
    out = {}
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cur = None
        while True:
            p = {"series_ticker": series, "limit": 1000, "max_close_ts": int(CUT.timestamp()), **extra, **({"cursor": cur} if cur else {})}
            d = api._get(path, p)
            for m in d.get("markets", []):
                if m.get("result") in ("yes", "no") and (m.get("close_time") or "") < CUTS:
                    out[m["ticker"]] = (m["event_ticker"], m["close_time"], float(m.get("volume_fp") or 0), m["ticker"])
            cur = d.get("cursor")
            if not cur or not d.get("markets"):
                break
    return list(out.values())


def cap(rows, min_volume: float = MIN_VOLUME, per_event: int = 2) -> dict:
    """Upper bound on treated trades from the listing alone: per event at most per_event markets that traded min_volume or more."""
    ev = defaultdict(list)
    for e, c, v, _ in rows:
        ev[e].append((c, v))
    n_ev = len(ev)
    ub = sum(min(per_event, sum(1 for _, v in x if v >= min_volume)) for x in ev.values())
    first = sorted(min(c for c, _ in x) for x in ev.values())
    return {"events": n_ev, "markets": len(rows), "traded_events": sum(1 for x in ev.values() if any(v >= min_volume for _, v in x)), "upper_bound": ub,
            "first": first[0] if first else None, "last": first[-1] if first else None}


def verdict(expected_treated: float, events: int) -> str:
    return "RUNNABLE" if expected_treated >= MIN_TRADES and events >= MIN_EVENTS else "NOT_RUNNABLE"


def census(cache: str) -> None:
    from . import api
    c = Path(cache); c.mkdir(parents=True, exist_ok=True)
    ss = json.load(open(c / "series.json")) if (c / "series.json").exists() else api._get("/series", {"category": "Climate and Weather"})["series"]
    json.dump(ss, open(c / "series.json", "w"))
    order = ["weekly temperature", "hourly directional temperature", "snowfall", "rain totals (month/week)", "monthly/annual extreme temperature",
             "monthly/annual temperature rank", "air quality", "tornadoes", "space weather", "sea ice", "water temperature / level", "degree days / CO2", "hurricanes and storms", "other"]
    # KX series first (the live tickers), then the older tickers without the prefix; the order is by family, a pure scheduling choice
    for t in sorted(candidates(ss), key=lambda t: (order.index(family(t)), not t.startswith("KX"), t)):
        f = c / f"list_{t}.json"
        for attempt in range(20):              # the shared Kalshi limit answers 429 for minutes at a time: wait and retry, never skip a series
            if f.exists():
                break
            try:
                json.dump(listing(t), open(f, "w"))
            except RuntimeError as e:
                print("retry", t, str(e)[:60], flush=True)
                time.sleep(90)
        print(t, family(t), len(json.load(open(f))), flush=True)


def report(cache: str) -> dict:
    c = Path(cache); fam = defaultdict(lambda: defaultdict(list)); res = {}
    for f in sorted(c.glob("list_*.json")):
        t = f.stem[5:]; rows = [tuple(r) for r in json.load(open(f))]
        if rows:
            fam[family(t)][t] = rows
    for name, d in sorted(fam.items()):
        allrows = [r for rows in d.values() for r in rows]
        k = cap(allrows)
        res[name] = {"series": {t: cap(r) for t, r in d.items()}, "pooled": k}
    return res


# ---- the rule, fixed in the registration (used by the forward read; not run on history unless the census says RUNNABLE) ----
LO, HI, HARD, RATIO, MAX_PER_EVENT, C, STRESS, PF_BAR = 0.03, 0.30, 0.30, 3.0, 2, 10, 1.2, 1.5


def fee(p: float, stress: float = 1.0) -> float:
    """7% x C x p x (1-p) rounded UP to the cent per order of C contracts, per contract."""
    return math.ceil(round(0.07 * C * p * (1 - p) * stress * 100, 9)) / 100 / C


def normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def prob_above(forecast: float, bias: float, sd: float, threshold: float) -> float:
    """P(observed > threshold) with observed = forecast + bias + N(0, sd). sd comes from the first two thirds of events only."""
    return 1 - normal_cdf((threshold - forecast - bias) / sd)


def fit_error(pairs: list) -> tuple:
    """pairs: (forecast, observed) of the FIRST TWO THIRDS of events by close time. Returns (bias, sd) with sd floored at 0.1."""
    e = [o - f for f, o in pairs]
    m = sum(e) / len(e)
    return m, max(0.1, math.sqrt(sum((x - m) ** 2 for x in e) / max(1, len(e) - 1)))


def pick(quotes: list, model_p: dict) -> list:
    """quotes: [(market, yes_ask, no_ask)]; model_p[market] = P(yes). Cheap side only: a side with ask in [LO, HI] and model probability >= RATIO x ask.
    At most MAX_PER_EVENT per event, the highest ratio first. Returns [(market, side, ask)]. No favourite side is ever considered."""
    out = []
    for m, ya, na in quotes:
        p = model_p.get(m)
        if p is None:
            continue
        for side, ask, q in (("yes", ya, p), ("no", na, 1 - p)):
            if ask is not None and LO <= ask <= min(HI, HARD) and q >= RATIO * ask:
                out.append((q / ask, m, side, ask))
    out.sort(reverse=True)
    return [(m, side, ask) for _, m, side, ask in out[:MAX_PER_EVENT]]


def net_of(side: str, price: float, result: str, stress: float = 1.0) -> float:
    return (1.0 if side == result else 0.0) - price - fee(price, stress)


def profit_factor(nets: list) -> float:
    w = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return w / l if l > 0 else (math.inf if w > 0 else 0.0)


def verdict_scored(nets_first: list, nets_second: list, months_to_go: float = 0.0) -> str:
    n = len(nets_first) + len(nets_second)
    if n < MIN_TRADES:
        return "NOT_ENOUGH_DATA"
    mean = lambda x: sum(x) / len(x) if x else 0.0
    if not (mean(nets_first) > 0 and mean(nets_second) > 0) or profit_factor(nets_first + nets_second) < PF_BAR:
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED"


if __name__ == "__main__":
    if sys.argv[1:2] == ["census"]:
        census(sys.argv[2])
    elif sys.argv[1:2] == ["report"]:
        r = report(sys.argv[2])
        for n, v in r.items():
            p = v["pooled"]; print(f"{n}: series {len(v['series'])} events {p['events']} traded_events {p['traded_events']} markets {p['markets']} UB {p['upper_bound']} {p['first'][:10] if p['first'] else ''}..{p['last'][:10] if p['last'] else ''}")
    else:
        print(__doc__)
