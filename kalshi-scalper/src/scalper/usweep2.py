"""USWEEP2 (README "USWEEP2"; workers/USWEEP2_REGISTRATION.md): the faster, broader universe sweep. Public keyless Kalshi data only; places nothing.

Usage: python -m scalper.usweep2 crawl    bulk /markets (no series filter, mve_filter=exclude) one hour window at a time for the last CRAWL_DAYS days -> structure only
       python -m scalper.usweep2 census   per candidate series, its settled markets in 60 days (one page) -> structure (+ results kept in a file the selector never reads)
       python -m scalper.usweep2 select   the registered eligible list -> workers/USWEEP2_SERIES.json (structure only)
       python -m scalper.usweep2 fetch    candles for the sample's development dates; results from the census results file
       python -m scalper.usweep2 score    ONE run of the USWEEP1 rule grid on the development dates -> workers/USWEEP2_RESULT.json
Cache lives OUTSIDE the repo (USWEEP2_CACHE). Reuses usweep1 functions; usweep1.py is not edited.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

from . import api, usweep1 as u1

CACHE = Path(os.environ.get("USWEEP2_CACHE", "/tmp/usweep2_cache"))
WORKERS = Path(__file__).resolve().parents[2] / "workers"

CRAWL_DAYS = 3                 # contiguous days crawled with the bulk endpoint (stopped at 72 hourly windows: the crawl ran at about 5 pages a minute)
SCREEN_MIN_MARKETS, SCREEN_MIN_DATES = 15, 2   # stage A screen: a candidate needs this much in the crawled days to get an exact 60 day count
MIN_MARKETS, MIN_DATES, MIN_MEDIAN_VOLUME = 300, 20, 100.0
SAMPLE_PER_SERIES = 30
CANDLE_BUDGET = 1200           # candle requests (one per development market); series taken by descending median volume until the budget is used
# Amendment 1 (owner decision, Oct 28 rule held strictly): NO buy-the-favourite research. entries_for below is the tail-only copy of usweep1.entries_for
# (usweep1.py and its RULES are not touched); no favourite entry is built and no favourite result is computed or printed.
TAIL = u1.RULES["tail"]
PAGE_CAP = 1                   # exact census: one page of 1000 per candidate (capped flag kept)


def series_of(event_ticker: str) -> str:
    return event_ticker.split("-")[0]


def row_of(m: dict) -> list:
    return [m["ticker"], series_of(m.get("event_ticker") or m["ticker"]), u1.iso_ts(m.get("open_time")), u1.iso_ts(m.get("close_time")),
            u1.iso_ts(m.get("expected_expiration_time")), float(m.get("volume_fp") or 0), bool(m.get("can_close_early"))]


def sample_key(ticker: str) -> str:
    return hashlib.md5(ticker.encode()).hexdigest()


def crawl() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    state = CACHE / "crawl_done.txt"
    done = set(state.read_text().split()) if state.exists() else set()
    now = int(time.time()) // 3600 * 3600
    out = (CACHE / "crawl.jsonl").open("a")
    t0, nm, pages = time.time(), 0, 0
    for h in range(CRAWL_DAYS * 24):
        hi = now - h * 3600
        lo = hi - 3600
        if str(lo) in done:
            continue
        cur = None
        while True:
            p = {"status": "settled", "min_close_ts": lo, "max_close_ts": hi - 1, "limit": 1000, "mve_filter": "exclude"}
            if cur:
                p["cursor"] = cur
            d = api._get("/markets", p)
            pages += 1
            for m in d.get("markets", []):
                out.write(json.dumps(row_of(m)) + "\n"); nm += 1
            cur = d.get("cursor")
            time.sleep(0.3)
            if not cur:
                break
        out.flush()
        with state.open("a") as f:
            f.write(f"{lo}\n")
        print(f"window {h + 1}/{CRAWL_DAYS * 24} markets {nm} pages {pages} {pages / ((time.time() - t0) / 60):.1f} pages/min", flush=True)
    print("crawl done", flush=True)


def load_crawl() -> list[list]:
    seen, rows = set(), []
    for line in (CACHE / "crawl.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r[0] not in seen:
            seen.add(r[0]); rows.append(r)
    return rows


def candidates(rows: list[list]) -> dict:
    """Stage A: per series counts in the crawled days. Structure only."""
    by: dict = {}
    for r in rows:
        anc = r[4] or r[3]
        if not anc:
            continue
        s = by.setdefault(r[1], {"n": 0, "dates": set()})
        s["n"] += 1
        s["dates"].add(time.strftime("%Y-%m-%d", time.gmtime(anc)))
    return {k: v for k, v in by.items() if v["n"] >= SCREEN_MIN_MARKETS and len(v["dates"]) >= SCREEN_MIN_DATES}


def census() -> None:
    rows = load_crawl()
    cand = candidates(rows)
    meta = {s["ticker"]: s for s in api._get("/series", {"limit": 20000}).get("series", [])}
    (CACHE / "series_list.json").write_text(json.dumps(list(meta.values())))
    todo = sorted((k for k in cand if not (meta.get(k, {}).get("frequency") == "fifteen_min" or k.startswith("KXMVE"))), key=lambda k: (-cand[k]["n"], k))      # busiest first (stage A count, structure only): the census is stopped by count, see Amendment 1
    path, rpath = CACHE / "census.jsonl", CACHE / "census_results.jsonl"
    done = {json.loads(x)["ticker"] for x in path.read_text().splitlines()} if path.exists() else set()
    todo = [t for t in todo if t not in done]
    print(f"{len(rows)} markets crawled, {len(cand)} candidate series, {len(todo)} to count exactly", flush=True)
    now = int(time.time()); lo = now - u1.WINDOW_DAYS * 86400
    f, rf = path.open("a"), rpath.open("a")
    for i, t in enumerate(todo):
        try:
            d = api._get("/markets", {"series_ticker": t, "status": "settled", "min_close_ts": lo, "max_close_ts": now, "limit": 1000})
            ms = d.get("markets", [])
            rec = {"ticker": t, "freq": meta.get(t, {}).get("frequency"), "cat": meta.get(t, {}).get("category"), "title": meta.get(t, {}).get("title"),
                   "n": len(ms), "capped": bool(d.get("cursor")),
                   "markets": [[m["ticker"], u1.iso_ts(m.get("open_time")), u1.iso_ts(m.get("close_time")), u1.iso_ts(m.get("expected_expiration_time")),
                                float(m.get("volume_fp") or 0), bool(m.get("can_close_early"))] for m in ms]}
            rf.write(json.dumps({"s": t, "r": {m["ticker"]: m.get("result") for m in ms if m.get("result") in ("yes", "no")}}) + "\n"); rf.flush()
        except Exception as e:
            rec = {"ticker": t, "error": str(e)[:100], "n": 0, "markets": []}
        f.write(json.dumps(rec) + "\n"); f.flush()
        time.sleep(0.3)
        if (i + 1) % 50 == 0:
            print(f"  {i + 1} / {len(todo)}", flush=True)
    print("census done", flush=True)


def eligible(rec: dict, excluded: set) -> dict | None:
    """The registered rule. Structure only (counts, dates, median life, median volume)."""
    if rec["ticker"] in excluded or rec["ticker"].startswith("KXMVE") or rec.get("freq") == "fifteen_min":
        return None
    pr = u1.series_profile(rec)
    if not pr or pr["n"] < MIN_MARKETS or pr["dates"] < MIN_DATES or not pr["class"] or pr["median_volume"] < MIN_MEDIAN_VOLUME:
        return None
    pr.update({"ticker": rec["ticker"], "freq": rec.get("freq"), "cat": rec.get("cat"), "title": rec.get("title"), "capped": rec.get("capped", False)})
    return pr


def select() -> None:
    excluded = {s["ticker"] for s in json.loads((WORKERS / "USWEEP1_SERIES.json").read_text())["series"]}
    rows = [json.loads(x) for x in (CACHE / "census.jsonl").read_text().splitlines()]
    rows = list({r["ticker"]: r for r in rows}.values())
    sel = [p for p in (eligible(r, excluded) for r in rows) if p]
    sel.sort(key=lambda x: (-x["median_volume"], x["ticker"]))
    byt = {r["ticker"]: r for r in rows}
    kept, used, skipped = [], 0, []
    for x in sel:
        k = len(dev_markets(byt[x["ticker"]])[0])
        if used + k <= CANDLE_BUDGET:
            kept.append(x); used += k
        else:
            skipped.append(x["ticker"])
    sel = sorted(kept, key=lambda x: x["ticker"])
    print(f"budget: {used} candle requests; {len(skipped)} eligible series NOT tested (budget)")
    (WORKERS / "USWEEP2_SERIES.json").write_text(json.dumps({"rule": f"n>={MIN_MARKETS} settled in 60 days, >={MIN_DATES} close dates, median volume >={MIN_MEDIAN_VOLUME}, not in USWEEP1_SERIES, not KXMVE, not fifteen_min", "budget_skipped": skipped, "series": sel}, indent=1))
    print(f"{len(rows)} exact-counted; {len(sel)} eligible")


def entries_for(rec: dict, ms: list, candles: dict, results: dict) -> dict:
    """{(look_minutes, "tail"): [(date, price_paid, won, net, volume, spread)]}: the side whose ask is 0.05 to 0.15 (the cheaper if both). Nothing else."""
    cls = rec["class"]; interval = 1 if cls == "H" else 60
    out: dict = {}
    for m in ms:
        t, open_ts, close_ts = m[0], m[1], m[2]
        res, cs = results.get(t), candles.get(t)
        if res is None or cs is None:
            continue
        anc = u1.anchor_of(m)
        for T in u1.LOOKS[cls]:
            target = anc - T * 60
            if target <= open_ts or target >= close_ts:
                continue
            q = u1.decision_quote(cs, target, interval)
            if not q:
                continue
            _, bid, ask, vol = q
            picks = [(s, p) for s, p in (("yes", ask), ("no", round(1 - bid, 4))) if TAIL[0] <= p <= TAIL[1]]
            if picks:
                side, p = min(picks, key=lambda x: x[1])
                won = side == res
                out.setdefault((T, "tail"), []).append((u1.market_date(m), p, won, u1.net_per_contract(won, p), vol or 0.0, ask - bid))
    return out


def sampled(rec: dict) -> list:
    """At most SAMPLE_PER_SERIES markets with the smallest md5(ticker); the sample, then the frozen third by date, are fixed by structure."""
    ms = [m for m in rec["markets"] if m[1] and m[2] and u1.anchor_of(m) and u1.anchor_of(m) > m[1]]
    ms.sort(key=lambda m: sample_key(m[0]))
    return ms[:SAMPLE_PER_SERIES]


def dev_markets(rec: dict) -> tuple[list, list]:
    ms = sampled(rec)
    dev_days, _fz = u1.split_dates([u1.market_date(m) for m in ms])
    ds = set(dev_days)
    return [m for m in ms if u1.market_date(m) in ds], dev_days


def fetch() -> None:
    from concurrent.futures import ThreadPoolExecutor
    import threading
    sel = json.loads((WORKERS / "USWEEP2_SERIES.json").read_text())["series"]
    byt = {}
    for x in (CACHE / "census.jsonl").read_text().splitlines():
        r = json.loads(x); byt[r["ticker"]] = r
    cpath = CACHE / "candles.jsonl"
    have = {json.loads(x)["t"] for x in cpath.read_text().splitlines()} if cpath.exists() else set()
    cf = cpath.open("a"); lock = threading.Lock()
    jobs = []
    for s in sel:
        ms, _ = dev_markets(byt[s["ticker"]])
        interval = 1 if s["class"] == "H" else 60
        tmax = max(u1.LOOKS[s["class"]])
        for m in ms:
            if m[0] not in have:
                jobs.append((s["ticker"], interval, tmax, m))
    print(f"{len(jobs)} candle requests for {len(sel)} series", flush=True)
    n = [0]

    def run(job):
        t, interval, tmax, m = job
        anc = u1.anchor_of(m)
        try:
            d = api._get("/markets/candlesticks", {"market_tickers": m[0], "start_ts": anc - tmax * 60 - 2 * interval * 60, "end_ts": anc + 60, "period_interval": interval})
            cm = {x.get("market_ticker"): x.get("candlesticks", []) for x in d.get("markets", [])}
        except Exception as e:
            print("  fail", t, str(e)[:80], flush=True); return
        cs = []
        for c in cm.get(m[0], []):
            b, a = c.get("yes_bid") or {}, c.get("yes_ask") or {}
            cs.append([c.get("end_period_ts"), api.f(b.get("close_dollars")), api.f(a.get("close_dollars")), api.f(c.get("volume_fp"))])
        with lock:
            cf.write(json.dumps({"t": m[0], "s": t, "iv": interval, "c": cs}) + "\n")
            n[0] += 1
            if n[0] % 100 == 0:
                cf.flush(); print(f"  {n[0]} / {len(jobs)}", flush=True)
        time.sleep(0.3)

    with ThreadPoolExecutor(2) as ex:
        list(ex.map(run, jobs))
    cf.close(); print("fetch done", flush=True)


def score() -> None:
    sel = json.loads((WORKERS / "USWEEP2_SERIES.json").read_text())["series"]
    byt = {}
    for x in (CACHE / "census.jsonl").read_text().splitlines():
        r = json.loads(x); byt[r["ticker"]] = r
    candles = {}
    for line in (CACHE / "candles.jsonl").read_text().splitlines():
        x = json.loads(line); candles[x["t"]] = x["c"]
    results = {}
    for line in (CACHE / "census_results.jsonl").read_text().splitlines():
        results.update(json.loads(line)["r"])
    cells = []
    for s in sel:
        dev, dev_days = dev_markets(byt[s["ticker"]])
        half_cut = dev_days[len(dev_days) // 2] if dev_days else None
        ent = entries_for(s, dev, candles, results)
        for (T, rule), rows in sorted(ent.items()):
            a = [r for r in rows if r[0] < half_cut]; b = [r for r in rows if r[0] >= half_cut]
            stress = [(r[0], r[3] - 0.2 * u1.fee_per_contract(r[1])) for r in rows]
            traded = [r for r in rows if r[4] > 0]
            cells.append({"series": s["ticker"], "title": s["title"], "cat": s["cat"], "freq": s["freq"], "cls": s["class"], "T": T, "rule": rule,
                          "all": u1.summarise(rows), "h1": u1.summarise(a), "h2": u1.summarise(b),
                          "stress_net": u1.cluster_mean_z(stress)[0] if len(stress) > 1 else 0.0, "traded": u1.summarise(traded) if traded else {"n": 0}})
    (WORKERS / "USWEEP2_RESULT.json").write_text(json.dumps({"cells": cells}, indent=0))
    print(f"{len(cells)} cells scored")


if __name__ == "__main__":
    {"crawl": crawl, "census": census, "select": select, "fetch": fetch, "score": score}[sys.argv[1]]()
