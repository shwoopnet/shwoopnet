"""USWEEP3 (README "USWEEP3"; workers/USWEEP3_REGISTRATION.md): third universe sweep, everything that is not sports. Public keyless Kalshi data only; places nothing.

Usage: python -m scalper.usweep3 candidates   non-sports candidate series (structure) -> cache
       python -m scalper.usweep3 census       exact 60 day settled listing per candidate, round robin across strata (results to a file select never reads)
       python -m scalper.usweep3 select       the registered eligible list and stratified candle budget -> workers/USWEEP3_SERIES.json (structure only)
       python -m scalper.usweep3 fetch        batched candles for the development markets only (the frozen last third is never fetched)
       python -m scalper.usweep3 score        ONE run, tail only -> workers/USWEEP3_RESULT.json
Cache lives OUTSIDE the repo (USWEEP3_CACHE). Reuses usweep1/usweep2 functions; neither is edited. Tail only: no favourite entry exists in this module.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys
import threading
import time
from pathlib import Path

from . import api, usweep1 as u1, usweep2 as u2

CACHE = Path(os.environ.get("USWEEP3_CACHE", "/tmp/usweep3_cache"))
US2 = Path(os.environ.get("USWEEP2_CACHE", "/tmp/usweep2_cache"))
WORKERS = Path(__file__).resolve().parents[2] / "workers"

RECURRING = ("hourly", "daily", "weekly", "monthly", "quarterly")
CRAWL_MIN_MARKETS, CRAWL_MIN_DATES = 10, 2
MIN_MARKETS, MIN_DATES, MIN_EVENTS, MIN_MEDIAN_VOLUME = 100, 8, 8, 5.0   # Amendment 1 (before any candle or outcome): 15/17/20 left 11 series
SAMPLE_PER_SERIES = 40
CANDLE_BUDGET = 6000
BATCH = 8
STRATA = ["Economics", "Climate and Weather", "Politics", "Financials", "Crypto", "Commodities", "Companies", "Science and Technology", "Entertainment", "World", "Mentions", "Other"]
u2.SAMPLE_PER_SERIES = SAMPLE_PER_SERIES      # u2.sampled/dev_markets read this module global: same function, larger sample


def stratum(cat: str | None) -> str:
    if cat == "Elections":
        return "Politics"
    return cat if cat in STRATA else "Other"


def event_of(ticker: str) -> str:
    return ticker.rsplit("-", 1)[0]


def is_candidate(s: dict, crawl_counts: dict, excluded: set) -> bool:
    t = s["ticker"]
    if t in excluded or t.startswith("KXMVE") or s.get("frequency") == "fifteen_min" or s.get("category") == "Sports":
        return False
    if s.get("frequency") in RECURRING:
        return True
    c = crawl_counts.get(t)
    return bool(c and c["n"] >= CRAWL_MIN_MARKETS and len(c["dates"]) >= CRAWL_MIN_DATES)


def excluded_set() -> set:
    return {x["ticker"] for f in ("USWEEP1_SERIES.json", "USWEEP2_SERIES.json") for x in json.loads((WORKERS / f).read_text())["series"]}


def round_robin(items: list[dict], key=lambda x: x) -> list:
    """Order items so the strata take turns (stratum order fixed, within a stratum the given order)."""
    by = {s: [x for x in items if stratum(x.get("cat")) == s] for s in STRATA}
    out = []
    while any(by.values()):
        for s in STRATA:
            if by[s]:
                out.append(by[s].pop(0))
    return out


def candidates() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    meta = api._get("/series", {"limit": 20000}).get("series", [])
    (CACHE / "series_list.json").write_text(json.dumps(meta))
    cc: dict = {}
    for r in u2.load_crawl() if (u2.CACHE / "crawl.jsonl").exists() else []:
        anc = r[4] or r[3]
        if anc:
            s = cc.setdefault(r[1], {"n": 0, "dates": set()}); s["n"] += 1; s["dates"].add(time.strftime("%Y-%m-%d", time.gmtime(anc)))
    ex = excluded_set()
    cand = [{"ticker": s["ticker"], "cat": s.get("category"), "freq": s.get("frequency"), "title": s.get("title")} for s in meta if is_candidate(s, cc, ex)]
    (CACHE / "candidates.json").write_text(json.dumps(cand))
    import collections
    print(len(meta), "series;", len(cand), "candidates;", dict(collections.Counter(stratum(c["cat"]) for c in cand)), flush=True)


def census() -> None:
    from concurrent.futures import ThreadPoolExecutor
    cand = json.loads((CACHE / "candidates.json").read_text())
    path, rpath = CACHE / "census.jsonl", CACHE / "census_results.jsonl"
    done = {json.loads(x)["ticker"] for x in path.read_text().splitlines()} if path.exists() else set()
    f, rf = path.open("a"), rpath.open("a")
    # reuse USWEEP2's exact counts (same 60 day window, structure; its results come along into the separate results file)
    reuse = 0
    if (US2 / "census.jsonl").exists():
        want = {c["ticker"] for c in cand} - done
        res2 = {}
        for line in (US2 / "census_results.jsonl").read_text().splitlines():
            x = json.loads(line); res2[x["s"]] = x["r"]
        for line in (US2 / "census.jsonl").read_text().splitlines():
            r = json.loads(line)
            if r["ticker"] in want and not r.get("error"):
                f.write(json.dumps(r) + "\n"); rf.write(json.dumps({"s": r["ticker"], "r": res2.get(r["ticker"], {})}) + "\n"); done.add(r["ticker"]); reuse += 1
        f.flush(); rf.flush()
    todo = round_robin([c for c in cand if c["ticker"] not in done])
    print(f"{len(cand)} candidates, {reuse} reused from USWEEP2, {len(todo)} to count", flush=True)
    now = int(time.time()); lo = now - u1.WINDOW_DAYS * 86400
    lock = threading.Lock(); cnt = [0]; t0 = time.time()
    limit = float(os.environ.get("USWEEP3_CENSUS_MINUTES", "100")) * 60

    def one(c):
        if time.time() - t0 > limit:
            return
        t = c["ticker"]
        try:
            d = api._get("/markets", {"series_ticker": t, "status": "settled", "min_close_ts": lo, "max_close_ts": now, "limit": 1000})
            ms = d.get("markets", [])
            rec = {"ticker": t, "freq": c["freq"], "cat": c["cat"], "title": c["title"], "n": len(ms), "capped": bool(d.get("cursor")),
                   "markets": [[m["ticker"], u1.iso_ts(m.get("open_time")), u1.iso_ts(m.get("close_time")), u1.iso_ts(m.get("expected_expiration_time")),
                                float(m.get("volume_fp") or 0), bool(m.get("can_close_early"))] for m in ms]}
            rres = {"s": t, "r": {m["ticker"]: m.get("result") for m in ms if m.get("result") in ("yes", "no")}}
        except Exception as e:
            rec, rres = {"ticker": t, "error": str(e)[:100], "n": 0, "markets": []}, None
        with lock:
            f.write(json.dumps(rec) + "\n"); f.flush()
            if rres:
                rf.write(json.dumps(rres) + "\n"); rf.flush()
            cnt[0] += 1
            if cnt[0] % 25 == 0:
                print(f"  {cnt[0]} / {len(todo)} ({cnt[0] / ((time.time() - t0) / 60):.1f}/min)", flush=True)
        time.sleep(0.3)

    with ThreadPoolExecutor(2) as ex:
        list(ex.map(one, todo))
    print("census done (counted this run: %d)" % cnt[0], flush=True)


def eligible(rec: dict) -> dict | None:
    """The registered relaxed rule. Structure only."""
    if rec.get("error") or rec["ticker"].startswith("KXMVE") or rec.get("freq") == "fifteen_min" or rec.get("cat") == "Sports":
        return None
    pr = u1.series_profile(rec)
    if not pr or not pr["class"] or pr["n"] < MIN_MARKETS or pr["dates"] < MIN_DATES or pr["median_volume"] < MIN_MEDIAN_VOLUME:
        return None
    if len({event_of(m[0]) for m in rec["markets"]}) < MIN_EVENTS:
        return None
    pr.update({"ticker": rec["ticker"], "freq": rec.get("freq"), "cat": rec.get("cat"), "title": rec.get("title"), "capped": rec.get("capped", False)})
    return pr


def stratified_budget(elig: list[dict], dev_count: dict, budget: int) -> tuple[list, list]:
    """Strata take turns, highest median volume first within a stratum, until the budget is used. Returns (kept, skipped tickers)."""
    by = {s: sorted([x for x in elig if stratum(x["cat"]) == s], key=lambda x: (-x["median_volume"], x["ticker"])) for s in STRATA}
    kept, skipped, used = [], [], 0
    while any(by.values()):
        for s in STRATA:
            if by[s]:
                x = by[s].pop(0)
                k = dev_count[x["ticker"]]
                if k and used + k <= budget:
                    kept.append(x); used += k
                else:
                    skipped.append(x["ticker"])
    return kept, skipped


def load_census() -> dict:
    rows = [json.loads(x) for x in (CACHE / "census.jsonl").read_text().splitlines()]
    return {r["ticker"]: r for r in rows}


def select() -> None:
    byt = load_census()
    elig = [p for p in (eligible(r) for r in byt.values()) if p]
    dev_count = {x["ticker"]: len(u2.dev_markets(byt[x["ticker"]])[0]) for x in elig}
    kept, skipped = stratified_budget(elig, dev_count, CANDLE_BUDGET)
    used = sum(dev_count[x["ticker"]] for x in kept)
    kept.sort(key=lambda x: x["ticker"])
    import collections
    (WORKERS / "USWEEP3_SERIES.json").write_text(json.dumps({
        "rule": f"non-Sports, n>={MIN_MARKETS} settled in 60 days, >={MIN_DATES} close dates, >={MIN_EVENTS} events, median volume >={MIN_MEDIAN_VOLUME}, not USWEEP1/2, not KXMVE/fifteen_min",
        "counted": len(byt), "eligible": len(elig), "dev_markets": used, "budget_skipped": sorted(skipped),
        "by_stratum_tested": dict(collections.Counter(stratum(x["cat"]) for x in kept)), "series": kept}, indent=1))
    print(f"{len(byt)} counted; {len(elig)} eligible; {len(kept)} tested ({used} dev markets); {len(skipped)} NOT TESTED (budget)", flush=True)


def fetch() -> None:
    from concurrent.futures import ThreadPoolExecutor
    sel = json.loads((WORKERS / "USWEEP3_SERIES.json").read_text())["series"]
    byt = load_census()
    cpath = CACHE / "candles.jsonl"
    have = {json.loads(x)["t"] for x in cpath.read_text().splitlines()} if cpath.exists() else set()
    cf = cpath.open("a"); lock = threading.Lock()
    jobs = []
    for s in sel:
        ms, _ = u2.dev_markets(byt[s["ticker"]])
        interval = 1 if s["class"] == "H" else 60
        tmax = max(u1.LOOKS[s["class"]])
        ms = sorted((m for m in ms if m[0] not in have), key=u1.anchor_of)
        chunk = []
        for m in ms:
            cand = chunk + [m]
            span = (u1.anchor_of(cand[-1]) - u1.anchor_of(cand[0]) + tmax * 60 + 4 * interval * 60) / (interval * 60)
            if chunk and (span * len(cand) > 8500 or len(cand) > BATCH):
                jobs.append((s["ticker"], interval, tmax, chunk)); chunk = [m]
            else:
                chunk = cand
        if chunk:
            jobs.append((s["ticker"], interval, tmax, chunk))
    print(f"{len(jobs)} candle requests (batched) for {len(sel)} series", flush=True)
    n = [0]

    def run(job):
        t, interval, tmax, chunk = job
        lo = min(u1.anchor_of(m) for m in chunk) - tmax * 60 - 2 * interval * 60
        hi = max(u1.anchor_of(m) for m in chunk) + 60
        try:
            d = api._get("/markets/candlesticks", {"market_tickers": ",".join(m[0] for m in chunk), "start_ts": lo, "end_ts": hi, "period_interval": interval})
            cm = {x.get("market_ticker"): x.get("candlesticks", []) for x in d.get("markets", [])}
        except Exception as e:
            print("  fail", t, str(e)[:80], flush=True); return
        with lock:
            for m in chunk:
                anc = u1.anchor_of(m)
                cs = []
                for c in cm.get(m[0], []):
                    e = c.get("end_period_ts")
                    if e is None or not (anc - tmax * 60 - 2 * interval * 60 <= e <= anc + 60):
                        continue
                    b, a = c.get("yes_bid") or {}, c.get("yes_ask") or {}
                    cs.append([e, api.f(b.get("close_dollars")), api.f(a.get("close_dollars")), api.f(c.get("volume_fp"))])
                cf.write(json.dumps({"t": m[0], "s": t, "iv": interval, "c": cs}) + "\n")
            n[0] += 1; cf.flush()
            if n[0] % 20 == 0:
                print(f"  {n[0]} / {len(jobs)}", flush=True)
        time.sleep(0.3)

    with ThreadPoolExecutor(2) as ex:
        list(ex.map(run, jobs))
    cf.close(); print("fetch done", flush=True)


def pooled(cells_rows: dict) -> list:
    """Observation only: (stratum, class, look) groups of all tail entries, day-clustered z and the number of series."""
    out = []
    for (cat, cls, T), (rows, nser) in sorted(cells_rows.items()):
        s = u1.summarise(rows)
        out.append({"stratum": cat, "cls": cls, "T": T, "series": nser, "all": s})
    return out


def score() -> None:
    sel = json.loads((WORKERS / "USWEEP3_SERIES.json").read_text())["series"]
    byt = load_census()
    candles = {}
    for line in (CACHE / "candles.jsonl").read_text().splitlines():
        x = json.loads(line); candles[x["t"]] = x["c"]
    results = {}
    for line in (CACHE / "census_results.jsonl").read_text().splitlines():
        results.update(json.loads(line)["r"])
    cells, groups = [], {}
    for s in sel:
        dev, dev_days = u2.dev_markets(byt[s["ticker"]])
        half_cut = dev_days[len(dev_days) // 2] if dev_days else None
        ent = u2.entries_for(s, dev, candles, results)
        for (T, rule), rows in sorted(ent.items()):
            a = [r for r in rows if r[0] < half_cut]; b = [r for r in rows if r[0] >= half_cut]
            stress = [(r[0], r[3] - 0.2 * u1.fee_per_contract(r[1])) for r in rows]
            traded = [r for r in rows if r[4] > 0]
            cells.append({"series": s["ticker"], "title": s["title"], "cat": s["cat"], "freq": s["freq"], "cls": s["class"], "T": T, "rule": rule,
                          "all": u1.summarise(rows), "h1": u1.summarise(a), "h2": u1.summarise(b),
                          "stress_net": u1.cluster_mean_z(stress)[0] if len(stress) > 1 else 0.0, "traded": u1.summarise(traded) if traded else {"n": 0}})
            g = groups.setdefault((stratum(s["cat"]), s["class"], T), [[], 0])
            g[0].extend(rows); g[1] += 1
    (WORKERS / "USWEEP3_RESULT.json").write_text(json.dumps({"cells": cells, "pooled": pooled({k: (v[0], v[1]) for k, v in groups.items()})}, indent=0))
    print(f"{len(cells)} cells scored")


if __name__ == "__main__":
    {"candidates": candidates, "census": census, "select": select, "fetch": fetch, "score": score}[sys.argv[1]]()
