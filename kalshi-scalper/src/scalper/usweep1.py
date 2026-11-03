"""USWEEP1 (README, "USWEEP1"; workers/USWEEP1_REGISTRATION.md): the universe sweep. Public keyless Kalshi data only; places nothing; decides nothing.

Usage: python -m scalper.usweep1 census   every series Kalshi lists (not KXMVE parlays, not fifteen_min), its settled markets since the live cutoff -> cache
       python -m scalper.usweep1 select   the registered series list from the census (structure only, no outcome) -> workers/USWEEP1_SERIES.json
       python -m scalper.usweep1 fetch    candles at the registered looks for the selected series (and each market's result, kept in a separate file) -> cache
       python -m scalper.usweep1 score    ONE run of the registered rule grid on the development dates (the frozen last third is never scored) -> workers/USWEEP1_RESULT.json
Cache lives OUTSIDE the repo (USWEEP1_CACHE, default ../scratchpad style path given by the caller).
"""
from __future__ import annotations

import json
import math
import os
import statistics as st
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from . import api
from .calibration import cluster_mean_z

CACHE = Path(os.environ.get("USWEEP1_CACHE", "/tmp/usweep1_cache"))
WORKERS = Path(__file__).resolve().parents[2] / "workers"

# ---- registered constants (workers/USWEEP1_REGISTRATION.md) ----
WINDOW_DAYS = 60                      # markets closing in the last 60 days (Kalshi's live /markets keeps settled markets since its historical cutoff)
PAGE_CAP = 2                          # at most 2 pages of 1000 settled markets per series
MIN_MARKETS, MIN_DATES = 300, 20
SAMPLE_CAP = 600                      # at most the 600 most recent settled markets of a series are fetched and scored
LOOKS = {"H": (30, 15, 5), "D": (1440, 360, 60), "W": (4320, 1440, 360)}   # minutes before the anchor, by life class (see life_class)
RULES = {"tail": (0.05, 0.15), "fav": (0.85, 0.97)}
FEE_RATE, C = 0.07, 10
FROZEN_SHARE = 1 / 3                  # the latest third of a series' dates is never scored here
MIN_HALF_N, MIN_DEV_N = 40, 100
ANCHOR_NOTE = "expected_expiration_time when present, else close_time"


def iso_ts(s):
    if not s:
        return None
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def life_class(life_s: float) -> str | None:
    """H up to 4 hours, D up to 3 days, W longer. The class sets the three looks and the candle size."""
    if life_s <= 0:
        return None
    if life_s <= 4 * 3600:
        return "H"
    if life_s <= 3 * 86400:
        return "D"
    return "W"


def fee_per_contract(p: float, c: int = C, mult: float = 1.0) -> float:
    """Kalshi's fee for an order of c contracts at price p: 7% x c x p x (1 - p) rounded UP to the cent, spread per contract."""
    cents = math.ceil(round(FEE_RATE * mult * c * p * (1 - p) * 100, 6))
    return cents / 100.0 / c


def net_per_contract(side_won: bool, price: float, mult: float = 1.0) -> float:
    return (1.0 if side_won else 0.0) - price - fee_per_contract(price, C, mult)


# ---------------------------------------------------------------- census
def census() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    allseries = api._get("/series", {"limit": 20000}).get("series", [])
    (CACHE / "series_list.json").write_text(json.dumps(allseries))
    skip = [s for s in allseries if s["ticker"].startswith("KXMVE") or s.get("frequency") == "fifteen_min"]
    todo = [s for s in allseries if s not in skip]
    now = int(time.time())
    lo = now - WINDOW_DAYS * 86400
    out_path = CACHE / "census.jsonl"
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            try:
                done.add(json.loads(line)["ticker"])
            except Exception:
                pass
    todo = [s for s in todo if s["ticker"] not in done]
    tier = {"hourly": 0, "daily": 0, "weekly": 0, "monthly": 0, "quarterly": 0}
    todo.sort(key=lambda s: (tier.get(s.get("frequency"), 1), s["ticker"]))      # the recurring series first, then custom, one_off and annual
    print(f"{len(allseries)} series listed, {len(skip)} skipped (KXMVE parlays or fifteen_min), {len(done)} already done, {len(todo)} to read", flush=True)
    lock = threading.Lock()
    f = out_path.open("a")
    cnt = [0]

    def one(s):
        t = s["ticker"]
        ms, cur, pages = [], None, 0
        try:
            while pages < PAGE_CAP:
                p = {"series_ticker": t, "status": "settled", "min_close_ts": lo, "max_close_ts": now, "limit": 1000}
                if cur:
                    p["cursor"] = cur
                d = api._get("/markets", p)
                ms += d.get("markets", [])
                pages += 1
                cur = d.get("cursor")
                if not cur:
                    break
            rec = {"ticker": t, "freq": s.get("frequency"), "cat": s.get("category"), "title": s.get("title"), "n": len(ms), "capped": bool(cur)}
            # structure only. The market's result is deliberately NOT kept here.
            rec["markets"] = [[m["ticker"], iso_ts(m.get("open_time")), iso_ts(m.get("close_time")), iso_ts(m.get("expected_expiration_time")),
                               float(m.get("volume_fp") or 0), bool(m.get("can_close_early"))] for m in ms]
        except Exception as e:
            rec = {"ticker": t, "freq": s.get("frequency"), "cat": s.get("category"), "title": s.get("title"), "error": str(e)[:100], "n": 0, "markets": []}
        with lock:
            f.write(json.dumps(rec) + "\n"); f.flush()
            cnt[0] += 1
            if cnt[0] % 200 == 0:
                f.flush()
                print(f"  {cnt[0]} / {len(todo)}", flush=True)
        time.sleep(0.25)

    with ThreadPoolExecutor(2) as ex:
        list(ex.map(one, todo))
    f.close()
    print("census done", flush=True)


def load_census() -> list[dict]:
    return [json.loads(x) for x in (CACHE / "census.jsonl").read_text().splitlines()]


def anchor_of(m) -> int | None:
    """[ticker, open_ts, close_ts, expected_ts, volume, early]"""
    return m[3] or m[2]


def series_profile(rec: dict) -> dict:
    ms = [m for m in rec["markets"] if m[1] and m[2]]
    if not ms:
        return {}
    lives = [(anchor_of(m) - m[1]) for m in ms if anchor_of(m) and anchor_of(m) > m[1]]
    dates = {datetime.fromtimestamp(anchor_of(m), timezone.utc).strftime("%Y-%m-%d") for m in ms if anchor_of(m)}
    med_life = st.median(lives) if lives else 0
    return {"n": len(ms), "dates": len(dates), "median_life_s": med_life, "median_volume": st.median([m[4] for m in ms]), "class": life_class(med_life)}


def select() -> None:
    rows = load_census()
    sel, info = [], []
    for r in rows:
        pr = series_profile(r)
        if not pr:
            continue
        pr.update({"ticker": r["ticker"], "freq": r["freq"], "cat": r["cat"], "title": r["title"], "capped": r.get("capped", False)})
        info.append(pr)
        if pr["n"] >= MIN_MARKETS and pr["dates"] >= MIN_DATES and pr["class"]:
            sel.append(pr)
    sel.sort(key=lambda x: x["ticker"])
    (WORKERS / "USWEEP1_SERIES.json").write_text(json.dumps({"rule": "n>=300 settled markets in 60 days, >=20 close dates, life class from median anchor-open", "series": sel}, indent=1))
    (CACHE / "census_profile.json").write_text(json.dumps(info))
    print(f"{len(rows)} series read; {len(info)} with a settled market in {WINDOW_DAYS} days; {len(sel)} selected")


# ---------------------------------------------------------------- fetch
def split_dates(days: list[str]) -> tuple[list[str], list[str]]:
    """(development dates, frozen dates): the latest third of the sorted distinct dates is frozen. Dates only, no outcome."""
    d = sorted(set(days))
    k = int(len(d) * (1 - FROZEN_SHARE))
    return d[:k], d[k:]


def market_date(m) -> str:
    return datetime.fromtimestamp(anchor_of(m), timezone.utc).strftime("%Y-%m-%d")


def sampled(rec: dict) -> list:
    ms = [m for m in rec["markets"] if m[1] and m[2] and anchor_of(m) and anchor_of(m) > m[1]]
    ms.sort(key=lambda m: anchor_of(m), reverse=True)
    return ms[:SAMPLE_CAP]


def fetch() -> None:
    sel = json.loads((WORKERS / "USWEEP1_SERIES.json").read_text())["series"]
    byt = {r["ticker"]: r for r in load_census()}
    CACHE.mkdir(parents=True, exist_ok=True)
    cpath, opath = CACHE / "candles.jsonl", CACHE / "outcomes.jsonl"
    have = set()
    if cpath.exists():
        have = {json.loads(x)["t"] for x in cpath.read_text().splitlines()}
    cf, of = cpath.open("a"), opath.open("a")
    lock = threading.Lock()
    work = []
    for s in sel:
        ms = sampled(byt[s["ticker"]])
        dev_days, _ = split_dates([market_date(m) for m in ms])
        devset = set(dev_days)
        ms = [m for m in ms if market_date(m) in devset]     # frozen third: not even downloaded
        work.append((s, ms))
    jobs = []
    for s, ms in work:
        cls = s["class"]
        interval = 1 if cls == "H" else 60
        tmax = max(LOOKS[cls])
        ms = [m for m in ms if m[0] not in have]
        ms.sort(key=lambda m: anchor_of(m))
        step = 20 if cls != "H" else 20
        for i in range(0, len(ms), step):
            jobs.append((s["ticker"], interval, tmax, ms[i:i + step]))
    print(f"{len(jobs)} candle requests for {len(work)} series", flush=True)
    n = [0]

    def run(job):
        t, interval, tmax, chunk = job
        lo = min(anchor_of(m) for m in chunk) - tmax * 60 - 2 * interval * 60
        hi = max(anchor_of(m) for m in chunk) + 60
        # one request spans the chunk's whole range; keep chunks inside the 10,000 candles limit
        lo_ = min(lo, min(m[1] for m in chunk)) if False else lo
        for sub in ([chunk] if (hi - lo) / (interval * 60) * len(chunk) <= 9000 else [[m] for m in chunk]):
            lo2 = min(anchor_of(m) for m in sub) - tmax * 60 - 2 * interval * 60
            hi2 = max(anchor_of(m) for m in sub) + 60
            try:
                d = api._get("/markets/candlesticks", {"market_tickers": ",".join(m[0] for m in sub), "start_ts": lo2, "end_ts": hi2, "period_interval": interval})
                cm = {x.get("market_ticker"): x.get("candlesticks", []) for x in d.get("markets", [])}
            except Exception as e:
                print("  fail", t, str(e)[:80], flush=True)
                continue
            with lock:
                for m in sub:
                    cs = []
                    for c in cm.get(m[0], []):
                        b, a = c.get("yes_bid") or {}, c.get("yes_ask") or {}
                        cs.append([c.get("end_period_ts"), api.f(b.get("close_dollars")), api.f(a.get("close_dollars")), api.f(c.get("volume_fp"))])
                    cf.write(json.dumps({"t": m[0], "s": t, "iv": interval, "c": cs}) + "\n")
        n[0] += 1
        if n[0] % 50 == 0:
            cf.flush()
            print(f"  {n[0]} / {len(jobs)}", flush=True)
        time.sleep(0.25)

    with ThreadPoolExecutor(2) as ex:
        list(ex.map(run, jobs))
    cf.close()
    # results, kept apart from the structure file: the only place an outcome is stored. One listing per series (its development dates are inside it).
    odone = set()
    if opath.exists():
        odone = {json.loads(x)["s"] for x in opath.read_text().splitlines()}
    now = int(time.time())
    lo = now - WINDOW_DAYS * 86400
    for s, ms in work:
        if s["ticker"] in odone:
            continue
        want = {m[0] for m in ms}
        res, cur = {}, None
        for _ in range(PAGE_CAP):
            p = {"series_ticker": s["ticker"], "status": "settled", "min_close_ts": lo, "max_close_ts": now, "limit": 1000}
            if cur:
                p["cursor"] = cur
            d = api._get("/markets", p)
            for m in d.get("markets", []):
                if m["ticker"] in want and m.get("result") in ("yes", "no"):
                    res[m["ticker"]] = m["result"]
            cur = d.get("cursor")
            if not cur:
                break
        of.write(json.dumps({"s": s["ticker"], "r": res}) + "\n")
        of.flush()
        time.sleep(0.1)
    of.close()
    print("fetch done", flush=True)


# ---------------------------------------------------------------- score
def decision_quote(cs: list, target: int, interval: int):
    """The candle (end, bid, ask, volume) that ends at or before target and no more than one candle period before it, with a valid two sided quote; else None."""
    best = None
    for c in cs:
        if c[0] is None or c[0] > target:
            continue
        if best is None or c[0] > best[0]:
            best = c
    if best is None or target - best[0] > interval * 60:
        return None
    _, bid, ask, _v = best
    if bid is None or ask is None or not (0 < bid < ask < 1):
        return None
    return best


def entries_for(rec: dict, ms: list, candles: dict, results: dict) -> dict:
    """{(look_minutes, rule): [(date, price_paid, won, net, volume)]} for one series on the markets given."""
    cls = rec["class"]
    interval = 1 if cls == "H" else 60
    out: dict = {}
    for m in ms:
        t, open_ts, close_ts, _exp, _v, early = m
        res = results.get(t)
        cs = candles.get(t)
        if res is None or cs is None:
            continue
        anc = anchor_of(m)
        for T in LOOKS[cls]:
            target = anc - T * 60
            if target <= open_ts or target >= close_ts:
                continue                                  # not yet open, or already closed at the look: not tradeable then
            q = decision_quote(cs, target, interval)
            if not q:
                continue
            _, bid, ask, vol = q
            yes_ask, no_ask = ask, round(1 - bid, 4)
            for rule, (lo, hi) in RULES.items():
                picks = [(s, p) for s, p in (("yes", yes_ask), ("no", no_ask)) if lo <= p <= hi]
                if rule == "fav" and len(picks) > 1:
                    picks = [max(picks, key=lambda x: x[1])]
                if rule == "tail" and len(picks) > 1:
                    picks = [min(picks, key=lambda x: x[1])]
                for side, p in picks:
                    won = (side == res)
                    out.setdefault((T, rule), []).append((market_date(m), p, won, net_per_contract(won, p), vol or 0.0, ask - bid))
    return out


def summarise(rows: list) -> dict:
    n = len(rows)
    if n == 0:
        return {"n": 0}
    nets = [r[3] for r in rows]
    mean, se, z = cluster_mean_z([(r[0], r[3]) for r in rows])
    gains = sum(x for x in nets if x > 0)
    losses = -sum(x for x in nets if x < 0)
    return {"n": n, "dates": len({r[0] for r in rows}), "win": sum(1 for r in rows if r[2]) / n, "price": sum(r[1] for r in rows) / n,
            "excess": sum(1.0 if r[2] else 0.0 for r in rows) / n - sum(r[1] for r in rows) / n, "net": mean, "z": z,
            "pf": (gains / losses) if losses > 0 else None, "traded": sum(1 for r in rows if r[4] > 0) / n,
            "spread": st.median(r[5] for r in rows)}


def score() -> None:
    sel = json.loads((WORKERS / "USWEEP1_SERIES.json").read_text())["series"]
    byt = {r["ticker"]: r for r in load_census()}
    candles = {}
    for line in (CACHE / "candles.jsonl").read_text().splitlines():
        x = json.loads(line)
        candles[x["t"]] = x["c"]
    results = {}
    for line in (CACHE / "outcomes.jsonl").read_text().splitlines():
        x = json.loads(line)
        results.update(x["r"])
    cells = []
    for s in sel:
        ms = sampled(byt[s["ticker"]])
        dev_days, _fz = split_dates([market_date(m) for m in ms])
        dev = [m for m in ms if market_date(m) in set(dev_days)]
        half_cut = dev_days[len(dev_days) // 2] if dev_days else None
        ent = entries_for(s, dev, candles, results)
        for (T, rule), rows in sorted(ent.items()):
            a = [r for r in rows if r[0] < half_cut]
            b = [r for r in rows if r[0] >= half_cut]
            stress = [(r[0], r[3] - 0.2 * fee_per_contract(r[1])) for r in rows]
            traded = [r for r in rows if r[4] > 0]
            cells.append({"series": s["ticker"], "title": s["title"], "cat": s["cat"], "freq": s["freq"], "cls": s["class"], "T": T, "rule": rule, "all": summarise(rows),
                          "h1": summarise(a), "h2": summarise(b),
                          "stress_net": cluster_mean_z(stress)[0] if len(stress) > 1 else 0.0,
                          "traded": summarise(traded) if traded else {"n": 0}})
    (WORKERS / "USWEEP1_RESULT.json").write_text(json.dumps({"cells": cells}, indent=0))
    print(f"{len(cells)} cells scored")


def z_bar(n_total: float, alpha: float = 0.05) -> float:
    """One sided Bonferroni-style bar for n_total tries, as the ledger quotes it (5.27 at 728,702)."""
    from statistics import NormalDist
    return NormalDist().inv_cdf(1 - alpha / n_total)


if __name__ == "__main__":
    {"census": census, "select": select, "fetch": fetch, "score": score}[sys.argv[1]]()
