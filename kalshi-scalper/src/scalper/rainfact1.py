"""RAINFACT1: KXRAIN YES after the airport gauge has measured >= 0.01 inch (registration: workers/RAINFACT1_REGISTRATION.md).

Stages (each writes data/rainfact1/*.json; outcomes are only read in `score`):
  python3 -I src/scalper/rainfact1.py list      # settled KXRAIN markets before the cut (listing carries results; stored apart)
  python3 -I src/scalper/rainfact1.py obs       # IEM p01i per station
  python3 -I src/scalper/rainfact1.py triggers  # t_fact per market-day (no outcome used)
  python3 -I src/scalper/rainfact1.py candles   # candles for triggered days only
  python3 -I src/scalper/rainfact1.py score
"""
from __future__ import annotations
import csv, io, json, math, os, sys, time, urllib.request, urllib.error, urllib.parse, datetime as dt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

CUT = 1791043200            # 2026-10-03T16:00:00Z, frozen last third starts here
DIR = "data/rainfact1"
STATION = dict(ABQ="ABQ", ATL="ATL", AUS="AUS", BOS="BOS", CHI="ORD", CLL="CLL", CMH="CMH", DAL="DFW", DC="DCA",
               DEN="DEN", DTW="DTW", EWR="EWR", HOU="HOU", IND="IND", LAX="LAX", LEX="LEX", LV="LAS", MIA="MIA",
               MIN="MSP", MKE="MKE", NOLA="MSY", NYC="NYC", OKC="OKC", PHIL="PHL", PHX="PHX", PIT="PIT", PVD="PVD",
               SATX="SAT", SEA="SEA", SFO="SFO", SGF="SGF", STL="STL", TPA="TPA", TTN="TTN", WPB="PBI")
DELAY = 600                 # decision = t_fact + 10 min
ENTRY_AFTER = 60            # entry candle ends after decision + 60 s


def fee(p: float, c: int = 10) -> float:
    """Per contract, 7% x C x p x (1-p) rounded up to the cent at C=10."""
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100.0 / c


def city_of(ticker: str) -> str:
    return ticker.rsplit("-", 1)[-1]


def guard(rows):
    for r in rows:
        if int(r["close_ts"]) >= CUT:
            raise RuntimeError("frozen market in memory: " + r["ticker"])


def hourly_buckets(rows):
    """rows: [(valid_epoch, inches)] -> {utc_hour_epoch: max inches in that hour}."""
    b = {}
    for t, v in rows:
        h = t - t % 3600
        b[h] = max(b.get(h, 0.0), v)
    return b


def t_fact(rows, day_start, day_end):
    """First row valid time at which the market-day cumulative of hourly maxima reaches 0.01 inch, else None.
    Rows are (valid_epoch, inches). A bucket is counted when its first reporting row is in the day."""
    inday = [(t, v) for t, v in sorted(rows) if day_start <= t < day_end]
    best, cum, first_row = {}, 0.0, None
    seen_hours = {}
    for t, v in inday:
        h = t - t % 3600
        old = seen_hours.get(h, 0.0)
        if v > old:
            cum += v - old
            seen_hours[h] = v
            if cum >= 0.01 - 1e-9 and first_row is None:
                first_row = t
    return first_row


def entry_candle(cands, t0):
    """cands: [{end_ts, bid, ask}] sorted; first candle with end_ts > t0 + ENTRY_AFTER and a valid two-sided quote."""
    for c in cands:
        if c["end_ts"] > t0 + ENTRY_AFTER and c["bid"] is not None and c["ask"] is not None and 0 < c["bid"] and c["ask"] < 1:
            return c
    return None


def net(ask, won, mult=1.0, slip=0.0):
    p = min(0.999, ask + slip)
    return (1.0 if won else 0.0) - p - fee(p) * mult


def tail_prob(asks, wins):
    """P(at least `wins` wins) when trade i wins with probability asks[i] (null: price is fair)."""
    dp = [1.0]
    for p in asks:
        nd = [0.0] * (len(dp) + 1)
        for k, q in enumerate(dp):
            nd[k] += q * (1 - p)
            nd[k + 1] += q * p
        dp = nd
    return sum(dp[wins:])


def _get(url, retries=8, timeout=40):
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return r.read().decode()
        except urllib.error.HTTPError as e:
            last = e
            time.sleep(min(60, 5 * (i + 1)) if e.code == 429 else 2 * (i + 1))
        except Exception as e:  # noqa
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(str(last))


def cmd_list():
    from scalper import api
    os.makedirs(DIR, exist_ok=True)
    out = []
    for m in api.settled_markets("KXRAIN", 0, CUT - 1):
        ct = m.get("close_time")
        cts = int(dt.datetime.fromisoformat(ct.replace("Z", "+00:00")).timestamp())
        if cts >= CUT:
            continue
        out.append(dict(ticker=m["ticker"], close_ts=cts, result=m.get("result"), city=city_of(m["ticker"])))
    guard(out)
    json.dump(out, open(f"{DIR}/markets.json", "w"))
    print("markets", len(out), "min close", min(r["close_ts"] for r in out), "max", max(r["close_ts"] for r in out))


def cmd_obs():
    mk = json.load(open(f"{DIR}/markets.json"))
    lo = min(r["close_ts"] for r in mk) - 86400 - 3600
    hi = max(r["close_ts"] for r in mk) + 3600
    d0, d1 = dt.datetime.fromtimestamp(lo, dt.timezone.utc), dt.datetime.fromtimestamp(hi, dt.timezone.utc)
    obs = {}
    for city, st in STATION.items():
        q = [("station", st), ("data", "p01i"), ("year1", d0.year), ("month1", d0.month), ("day1", d0.day),
             ("year2", d1.year), ("month2", d1.month), ("day2", d1.day), ("tz", "UTC"), ("format", "onlycomma"),
             ("latlon", "no"), ("elev", "no"), ("missing", "M"), ("trace", "T"), ("direct", "no"),
             ("report_type", "3"), ("report_type", "4")]
        txt = _get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?" + urllib.parse.urlencode(q))
        rows, nonnull = [], 0
        for r in csv.DictReader(io.StringIO(txt)):
            v = r.get("p01i")
            if v in (None, "", "M"):
                continue
            nonnull += 1
            v = 0.0 if v == "T" else float(v)
            t = int(dt.datetime.strptime(r["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp())
            rows.append((t, v))
        obs[city] = rows
        print(city, st, "rows", len(rows), "nonnull", nonnull, flush=True)
        time.sleep(1)
    json.dump(obs, open(f"{DIR}/obs.json", "w"))


def cmd_triggers():
    mk = json.load(open(f"{DIR}/markets.json"))
    obs = json.load(open(f"{DIR}/obs.json"))
    dropped = [c for c, r in obs.items() if len(r) == 0]
    trig = []
    for m in mk:       # NOTE: no outcome field is touched here
        rows = obs.get(m["city"]) or []
        if not rows:
            continue
        ds, de = m["close_ts"] - 86400, m["close_ts"]
        tf = t_fact(rows, ds, de)
        if tf is not None:
            trig.append(dict(ticker=m["ticker"], city=m["city"], close_ts=m["close_ts"], t_fact=tf))
    guard(trig)
    json.dump(dict(dropped=dropped, trig=trig, n_days=len({m["close_ts"] for m in mk}), n_markets=len(mk)),
              open(f"{DIR}/triggers.json", "w"))
    print("dropped cities", dropped, "triggers", len(trig), "of markets", len(mk))


def cmd_candles():
    from scalper import api
    T = json.load(open(f"{DIR}/triggers.json"))["trig"]
    path = f"{DIR}/candles.json"
    got = json.load(open(path)) if os.path.exists(path) else {}
    for i, t in enumerate(T):
        if t["ticker"] in got:
            continue
        try:
            cs = api.candlesticks("KXRAIN", t["ticker"], t["t_fact"] - 300, min(t["close_ts"], t["t_fact"] + 7800))
            got[t["ticker"]] = [dict(end_ts=c["end_period_ts"],
                                     bid=api.f((c.get("yes_bid") or {}).get("close_dollars", (c.get("yes_bid") or {}).get("close"))),
                                     ask=api.f((c.get("yes_ask") or {}).get("close_dollars", (c.get("yes_ask") or {}).get("close"))),
                                     vol=api.f(c.get("volume_fp", c.get("volume")))) for c in cs]
        except Exception as e:  # noqa
            got[t["ticker"]] = None
            print("fail", t["ticker"], e, flush=True)
        if i % 10 == 0:
            json.dump(got, open(path, "w"))
            print(i, len(T), flush=True)
        time.sleep(4)
    json.dump(got, open(path, "w"))


def cmd_score():
    mk = {m["ticker"]: m for m in json.load(open(f"{DIR}/markets.json"))}
    T = json.load(open(f"{DIR}/triggers.json"))
    cands = json.load(open(f"{DIR}/candles.json"))
    dates = sorted({m["close_ts"] // 86400 for m in mk.values()})
    half = dates[len(dates) // 2]
    rows = []
    stat = dict(triggers=len(T["trig"]), no_quote=0, not_fetched=0, priced=0)
    for t in T["trig"]:
        cs = cands.get(t["ticker"])
        if cs is None:
            stat["not_fetched"] += 1
            continue
        cs = sorted(cs, key=lambda c: c["end_ts"])
        e = entry_candle(cs, t["t_fact"] + DELAY)
        res = mk[t["ticker"]]["result"]
        if e is None:
            stat["no_quote"] += 1
            continue
        ask = e["ask"]
        rows.append(dict(t, ask=ask, bid=e["bid"], won=(res == "yes"), half=("D1" if t["close_ts"] // 86400 < half else "D2"),
                         group=("A" if ask <= 0.30 else "B" if ask <= 0.95 else "C"), end_ts=e["end_ts"]))
    stat["priced"] = sum(1 for r in rows if r["group"] == "C")
    trig_all_yes = None
    out = dict(stat=stat, n_dates=len(dates), half_cut_day=half)
    for name, sel in (("A+B", lambda r: r["group"] in "AB"), ("A", lambda r: r["group"] == "A"), ("B", lambda r: r["group"] == "B")):
        for hv in ("ALL", "D1", "D2"):
            rr = [r for r in rows if sel(r) and (hv == "ALL" or r["half"] == hv)]
            n = len(rr)
            if not n:
                out[f"{name}/{hv}"] = dict(n=0)
                continue
            w = sum(r["won"] for r in rr)
            nets = [net(r["ask"], r["won"]) for r in rr]
            out[f"{name}/{hv}"] = dict(n=n, wins=w, win=round(w / n, 4), mean_ask=round(sum(r["ask"] for r in rr) / n, 4),
                                       mean_net_c=round(100 * sum(nets) / n, 3),
                                       net_x12_c=round(100 * sum(net(r["ask"], r["won"], 1.2) for r in rr) / n, 3),
                                       net_slip1_c=round(100 * sum(net(r["ask"], r["won"], 1.2, 0.01) for r in rr) / n, 3),
                                       days=len({r["close_ts"] // 86400 for r in rr}),
                                       tail_p=tail_prob([r["ask"] for r in rr], w))
    out["trigger_resolved_no"] = [dict(ticker=r["ticker"], ask=r["ask"], group=r["group"]) for r in rows if not r["won"]]
    out["all_triggered_n"] = len(rows)
    out["all_triggered_yes"] = sum(r["won"] for r in rows)
    asks = sorted(r["ask"] for r in rows)
    out["ask_quantiles"] = {q: asks[min(len(asks) - 1, int(q * len(asks)))] for q in (0.05, 0.1, 0.25, 0.5, 0.75)} if asks else {}
    json.dump(out, open(f"{DIR}/score.json", "w"), indent=1)
    json.dump(rows, open(f"{DIR}/rows.json", "w"))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    globals()["cmd_" + sys.argv[1]]()
