"""WXENS1 (README, Pre-registration: WXENS1; workers/WXENS1_REGISTRATION.md): ensemble spread tail brackets on the Kalshi daily-high temperature markets. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade; no order of any kind exists in this module.

Usage (DATA is the checked out `quote-data` branch directory that holds wxens/):
  python -m scalper.wxens1 snapshot [DATA] [--wide] [--results]   one manual snapshot, same as the hourly recorder (no network library beyond urllib, GET only)
  python -m scalper.wxens1 cities DATA                     freeze the 8 tested cities from the first 7 days of volume (refuses to overwrite)
  python -m scalper.wxens1 count DATA                      trade COUNTS only (no outcome is read for the count)
  python -m scalper.wxens1 run DATA                        the one registered read (refused before 300 trades or the stop date, and a second time)
"""
from __future__ import annotations

import csv
import glob
import gzip
import json
import math
import os
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from .calibration import cluster_mean_z

# ---- fixed in the registration before any recorded row ----
SD_F, MIN_RATIO, ASK_LO, ASK_HI, MAX_PER_DAY = 1.5, 3.0, 0.03, 0.30, 2
BIAS_DAYS, BIAS_MIN_DAYS, MIN_MODELS = 14, 5, 2
FEE_RATE, FEE_C, STRESS = 0.07, 10, 1.2
N_CITIES, CITY_DAYS = 8, 7
PRIMARY, PRIMARY_START_H, PRIMARY_END_H = "L1_10", 10, 12
MIN_TRADES, FULL_TRADES, STOP_DATE = 150, 300, "2027-02-28"
PF_BAR, Z_BAR = 1.5, 5.27


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def member_prob(kind: str, floor, cap, v: float, sd: float = SD_F) -> float:
    """Normal kernel of one (bias shifted) member, probability that the whole-degree maximum falls in the bracket. greater K: max >= K+1; less K: max <= K-1; between: inclusive."""
    if kind == "greater":
        return 1 - phi((floor + 0.5 - v) / sd)
    if kind == "less":
        return phi((cap - 0.5 - v) / sd)
    if kind == "between":
        return phi((cap + 0.5 - v) / sd) - phi((floor - 0.5 - v) / sd)
    raise ValueError(kind)


def bracket_prob(kind, floor, cap, by_model: dict, shift: float = 0.0):
    """Equal weight per model, equal weight per member in a model. None when fewer than MIN_MODELS models have members."""
    ms = [vals for vals in by_model.values() if vals]
    if len(ms) < MIN_MODELS:
        return None
    return sum(sum(member_prob(kind, floor, cap, v + shift) for v in vals) / len(vals) for vals in ms) / len(ms)


def pooled_mean(by_model: dict):
    ms = [sum(v) / len(v) for v in by_model.values() if v]
    return sum(ms) / len(ms) if len(ms) >= MIN_MODELS else None


def fee_order(price: float, c: int = FEE_C, mult: float = 1.0) -> float:
    """Kalshi fee for an order of c contracts, rounded UP to the cent."""
    return math.ceil(FEE_RATE * mult * c * price * (1 - price) * 100 - 1e-9) / 100


def net(price: float, won: bool, mult: float = 1.0) -> float:
    return (1.0 if won else 0.0) - price - fee_order(price, mult=mult) / FEE_C


def choose_trades(brackets: list[dict], max_per_day: int = MAX_PER_DAY) -> list[dict]:
    """brackets: dicts with ticker, ask, p. Cheap = ask in [0.03, 0.30]; a candidate has p >= 3 x ask; best p/ask first, ties to the lower ask then ticker."""
    cands = [b for b in brackets if b["p"] is not None and b["ask"] is not None and ASK_LO <= b["ask"] <= ASK_HI and b["p"] + 1e-9 >= MIN_RATIO * b["ask"]]
    cands.sort(key=lambda b: (-b["p"] / b["ask"], b["ask"], b["ticker"]))
    return cands[:max_per_day]


def control_trades(brackets: list[dict]) -> list[dict]:
    return [b for b in brackets if b["ask"] is not None and ASK_LO <= b["ask"] <= ASK_HI]


def profit_factor(nets: list[float]):
    w, l = sum(x for x in nets if x > 0), -sum(x for x in nets if x < 0)
    return (w / l) if l > 0 else (float("inf") if w > 0 else 0.0)


def split_halves(trades: list[dict]):
    """By settlement date; the earlier half is the first ceil(n/2) trades with whole days kept together."""
    ts = sorted(trades, key=lambda t: t["date"])
    n = len(ts)
    need = math.ceil(n / 2)
    cut = 0
    while cut < n and cut < need:
        d = ts[cut]["date"]
        while cut < n and ts[cut]["date"] == d:
            cut += 1
    return ts[:cut], ts[cut:]


def verdict(trades: list[dict], stop_reached: bool) -> tuple[str, dict]:
    """The registered verdict. trades carry 'net', 'net_stress', 'date', 'price'."""
    n = len(trades)
    info = {"n": n}
    if n < MIN_TRADES:
        return "NOT_ENOUGH_DATA", info
    if n < FULL_TRADES and not stop_reached:
        return "NOT_ENOUGH_DATA", info
    h1, h2 = split_halves(trades)
    nets = [t["net"] for t in trades]
    mean, se, z = cluster_mean_z([(t["date"], t["net"]) for t in trades])
    pf = profit_factor(nets)
    m1 = sum(t["net"] for t in h1) / len(h1) if h1 else 0.0
    m2 = sum(t["net"] for t in h2) / len(h2) if h2 else 0.0
    info.update(mean=mean, se=se, z=z, pf=pf, half1=m1, half2=m2, n1=len(h1), n2=len(h2), mde=2.8 * se,
                stress_mean=sum(t["net_stress"] for t in trades) / n)
    if not (m1 > 0 and m2 > 0) or pf < PF_BAR:
        return "FALSIFIED", info
    if info["stress_mean"] <= 0:
        return "FALSIFIED", info
    return "NOT_YET_FALSIFIED", info


# ---------------------------------------------------------------- reading the recorder's files

def _rows(data_dir, table):
    out = []
    for p in sorted(glob.glob(os.path.join(data_dir, "wxens", table, "**", "*.csv.gz"), recursive=True)):
        try:
            with gzip.open(p, "rt", newline="") as f:
                out += list(csv.DictReader(f))
        except (OSError, EOFError, ValueError):
            continue
    return out


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def look_ts(target_date: str, std_offset_h: int) -> int:
    """The primary look as a unix second: 10:00 local STANDARD time on the day before `target_date`."""
    d = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1) + timedelta(hours=PRIMARY_START_H - std_offset_h)
    return int(d.replace(tzinfo=timezone.utc).timestamp())


def primary_polls(quotes: list[dict], offsets: dict) -> dict:
    """{(city, target_date): [quote rows of the FIRST poll at or after the look and before 12:00 local standard time]}; no poll in that window means no entry (NoData)."""
    by = defaultdict(list)
    for r in quotes:
        if r["look"] == PRIMARY:
            by[(r["city"], r["target_date"])].append(r)
    out = {}
    for (city, d), rows in by.items():
        lo = look_ts(d, offsets[city])
        hi = lo + (PRIMARY_END_H - PRIMARY_START_H) * 3600
        ok = sorted({int(float(r["poll_ts"])) for r in rows if lo <= int(float(r["poll_ts"])) < hi})
        if ok:
            out[(city, d)] = [r for r in rows if int(float(r["poll_ts"])) == ok[0]]
    return out


def ens_members(ens: list[dict], vcol: str = "tmax_f") -> dict:
    """{(city, target_date, look, poll_ts): {model: [tmax]}}."""
    out = defaultdict(lambda: defaultdict(list))
    for r in ens:
        v = _f(r[vcol])
        if v is not None:
            out[(r["city"], r["target_date"], r["look"], int(float(r["poll_ts"])))][r["model"]].append(v)
    return out


def official_max(results: list[dict], obs: list[dict], ocol: str = "iem_max_tmpf") -> dict:
    """{(city, target_date): settled maximum}: the settled markets' expiration_value first, the IEM daily summary only when none is numeric."""
    out = {}
    for r in results:
        v = _f(r.get("expiration_value"))
        if v is not None:
            out[(r["city"], r["target_date"])] = v
    for r in obs:
        k = (r["city"], r["target_date"])
        if k not in out and _f(r.get(ocol)) is not None:
            out[k] = _f(r[ocol])
    return out


def result_seen_ts(results: list[dict]) -> dict:
    out = {}
    for r in results:
        k = (r["city"], r["target_date"])
        out[k] = min(out.get(k, 1 << 60), int(float(r["seen_ts"])))
    return out


def bias_for(city: str, target_date: str, look: int, errors: dict) -> float:
    """errors: {(city, target_date): (error, available_ts)}. Plain mean of the trailing 14 settled target dates whose result was recorded before `look`; 0 under 5 days."""
    d0 = datetime.strptime(target_date, "%Y-%m-%d").date()
    use = []
    for k in range(1, 40):
        key = (city, (d0 - timedelta(days=k)).isoformat())
        if key in errors and errors[key][1] <= look:
            use.append(errors[key][0])
        if len(use) == BIAS_DAYS:
            break
    return sum(use) / len(use) if len(use) >= BIAS_MIN_DAYS else 0.0


def build(data_dir: str, watchlist: str, sfx: str = "", vcol: str = "tmax_f", ocol: str = "iem_max_tmpf"):
    """Everything the count and the run need: per city-day the bracket table at the primary poll with model probabilities (no outcome except the bias inputs, which are earlier days)."""
    w = json.load(open(watchlist))
    offsets = {c["key"]: c["std_offset_h"] for c in w["cities"]}
    # sfx/vcol/ocol let WXLOW1 read the daily-low tables ("_low", "tmin_f", "iem_min_tmpf") with the SAME code; the defaults are the WXENS1 highs
    quotes, ens = _rows(data_dir, "quotes" + sfx), _rows(data_dir, "ens" + sfx)
    results, obs = _rows(data_dir, "results" + sfx), _rows(data_dir, "obs" + sfx)
    polls = primary_polls(quotes, offsets)
    members = ens_members(ens, vcol)
    official = official_max(results, obs, ocol)
    seen = result_seen_ts(results)
    # model errors at the primary look: official max minus the pooled ensemble mean at the first primary poll of that day
    errors = {}
    for (city, d), rows in polls.items():
        pts = rows[0]
        by = members.get((city, d, PRIMARY, int(float(pts["poll_ts"]))))
        mu = pooled_mean(by) if by else None
        if mu is not None and (city, d) in official:
            errors[(city, d)] = (official[(city, d)] - mu, seen.get((city, d), 1 << 60))
    days = {}
    for (city, d), rows in sorted(polls.items()):
        ts = int(float(rows[0]["poll_ts"]))
        by = members.get((city, d, PRIMARY, ts))
        shift = bias_for(city, d, ts, errors)
        br = []
        for r in rows:
            ask = _f(r["yes_ask"])
            p = bracket_prob(r["strike_type"], _f(r["floor_strike"]), _f(r["cap_strike"]), by, shift) if by else None
            br.append({"ticker": r["ticker"], "ask": ask, "bid": _f(r["yes_bid"]), "volume": _f(r["volume"]), "p": p})
        days[(city, d)] = {"poll_ts": ts, "brackets": br, "shift": shift}
    return days, official


def results_by_ticker(data_dir: str, sfx: str = "") -> dict:
    return {r["ticker"]: r["result"] for r in _rows(data_dir, "results" + sfx)}


def choose_cities(days: dict, n: int = N_CITIES, first_days: int = CITY_DAYS) -> list[str]:
    """The n cities with the highest median bracket volume over the first `first_days` distinct target dates that have a primary poll. Volume only, ties alphabetical."""
    dates = sorted({d for (_, d) in days})[:first_days]
    med = {}
    for (city, d), v in days.items():
        if d in dates:
            med.setdefault(city, []).extend(b["volume"] for b in v["brackets"] if b["volume"] is not None)
    ranked = sorted(((-(st.median(vs) if vs else 0.0), c) for c, vs in med.items()))
    return [c for _, c in ranked[:n]]


def trade_list(days: dict, cities: list[str], res: dict | None = None):
    """(selected, control): lists of dicts. With `res` (ticker -> result) each carries won, net and net_stress; without it only counts are possible."""
    sel, ctl = [], []
    for (city, d), v in sorted(days.items()):
        if city not in cities:
            continue
        for kind, rows in (("sel", choose_trades(v["brackets"])), ("ctl", control_trades(v["brackets"]))):
            for b in rows:
                t = {"city": city, "date": d, "ticker": b["ticker"], "price": b["ask"], "p": b["p"]}
                if res is not None:
                    if b["ticker"] not in res:
                        continue
                    won = res[b["ticker"]] == "yes"
                    t.update(won=won, net=net(b["ask"], won), net_stress=net(b["ask"], won, STRESS))
                (sel if kind == "sel" else ctl).append(t)
    return sel, ctl


# ---------------------------------------------------------------- command line

def _cities_file(data_dir):
    return os.path.join(data_dir, "wxens1_cities.json")


def cmd_cities(data_dir, watchlist):
    if os.path.exists(_cities_file(data_dir)):
        print("refused: the city set is already frozen:", open(_cities_file(data_dir)).read())
        return 1
    days, _ = build(data_dir, watchlist)
    dates = sorted({d for (_, d) in days})
    if len(dates) < CITY_DAYS:
        print("NOT YET: %d of %d target dates have a primary poll" % (len(dates), CITY_DAYS))
        return 1
    cs = choose_cities(days)
    json.dump({"cities": cs, "from_dates": dates[:CITY_DAYS]}, open(_cities_file(data_dir), "w"))
    print("frozen:", cs)
    return 0


def _frozen(data_dir):
    try:
        return json.load(open(_cities_file(data_dir)))["cities"]
    except (OSError, ValueError, KeyError):
        return None


def cmd_count(data_dir, watchlist):
    days, _ = build(data_dir, watchlist)
    cities = _frozen(data_dir) or sorted({c for (c, _) in days})
    sel, ctl = trade_list(days, cities)
    nd = len({d for (_, d) in days})
    per_day = len(sel) / nd if nd else 0.0
    left = max(0, MIN_TRADES - len(sel))
    eta = (datetime.now(timezone.utc) + timedelta(days=left / per_day)).date().isoformat() if per_day > 0 else "unknown"
    print("city set %s; target dates with a primary poll %d; selected trades %d (%.2f a day); control candidates %d; 150 trades about %s; counts only, no outcome read" % (
        "frozen" if _frozen(data_dir) else "NOT frozen (all recorded cities)", nd, len(sel), per_day, len(ctl), eta))
    return 0


def cmd_run(data_dir, watchlist):
    out = os.path.join(data_dir, "wxens1_result.txt")
    if os.path.exists(out):
        print("refused: the registered run was already done:", out)
        return 1
    cities = _frozen(data_dir)
    if not cities:
        print("refused: the city set is not frozen (python -m scalper.wxens1 cities DATA)")
        return 1
    days, _ = build(data_dir, watchlist)
    sel, _ = trade_list(days, cities)
    stop = datetime.now(timezone.utc).date().isoformat() >= STOP_DATE
    if len(sel) < FULL_TRADES and not stop:
        print("refused: %d of %d trades and before %s; use count" % (len(sel), FULL_TRADES, STOP_DATE))
        return 1
    sel, ctl = trade_list(days, cities, results_by_ticker(data_dir))
    v, info = verdict(sel, stop)
    cm = sum(t["net"] for t in ctl) / len(ctl) if ctl else 0.0
    text = "%s\n%s\ncontrol (all cheap brackets): n %d mean %+.4f\nwin rate %.4f vs mean price %.4f\n" % (
        v, json.dumps(info, sort_keys=True), len(ctl), cm, (sum(t["won"] for t in sel) / len(sel)) if sel else 0.0, (sum(t["price"] for t in sel) / len(sel)) if sel else 0.0)
    if info.get("mde", 0) > 0.02 and v == "FALSIFIED":
        text += "not shown at this sample size: minimum detectable mean %.4f\n" % info["mde"]
    open(out, "w").write(text)
    print(text)
    return 0


def cmd_snapshot(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, "..", "..", "..", "scripts"))
    import record_wxens as rec
    wide = "--wide" in argv
    pos = [a for a in argv if not a.startswith("--")]
    data = pos[0] if pos else os.path.join(here, "..", "..", "data", "wxens_manual")
    print(rec.run(os.path.join(here, "..", "..", "workers", "WXENS1_WATCHLIST.json"), data, due_hours=(7, 8, 10, 11) if wide else None,
                  results=True if "--results" in argv else None))
    return 0


def main(argv):
    watch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "workers", "WXENS1_WATCHLIST.json")
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "snapshot":
        return cmd_snapshot(argv[1:])
    if cmd in ("cities", "count", "run") and len(argv) >= 2:
        return {"cities": cmd_cities, "count": cmd_count, "run": cmd_run}[cmd](argv[1], watch)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
