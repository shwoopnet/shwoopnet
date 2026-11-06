#!/usr/bin/env python3
"""PERPGEN data layer: Kalshi perpetual-market candles and funding history, cached, cleaned, split by date.

Research only. Public keyless GETs, no order, no key. Standard library only (run with python3 -I).
Registered protocol: workers/PERPGEN_PROTOCOL.md.

Commands (cwd anywhere; paths are relative to the kalshi-scalper folder that holds this file's src/):
  fetch   [--as-of ISO]   pull raw 1 minute and 1 hour candles and the funding history into data/perpgen/raw (resumable)
  clean                   raw -> data/perpgen/clean/{dev,holdout}/ csv.gz per ticker, plus funding; writes cuts.json
  report                  writes workers/PERPDATA_REPORT.md (counts only, no return of any kind)
  all                     fetch + clean + report

SCHEMA of a clean candle file (one row per minute or hour that the exchange served; no forward fill):
  ts      candle END time, unix seconds UTC (the bar covers [ts-period, ts)); every close field is the quote AT ts
  bid_c, ask_c   close bid and close ask (quote currency units, floats); blank = invalid (no bid, no ask, int64 sentinel, ask>2*bid)
  bid_o,bid_h,bid_l, ask_o,ask_h,ask_l   same for the open/high/low fields, each screened on its own (ask high or open can be 9.2e14)
  px_o,px_h,px_l,px_c,px_m   trade price open/high/low/close/mean (blank when no trade in the bar)
  vol, vol_usd   contracts and notional traded in the bar;   oi, oi_usd   open interest at the close
  ok      1 if bid_c > 0 and ask_c valid and ask_c >= bid_c (a usable close quote), else 0
Funding file: ticker, funding_time (ISO), ts (unix), funding_rate (decimal per funding interval, as served), mark_price.

SPLIT: per ticker, calendar days (UTC) from its first usable bar to the last day before as_of are cut into thirds:
discovery = first third, validation = second, holdout = last. Dev files hold discovery+validation only, the holdout rows are in
a separate directory the loader will not open without a read-once guard (see load_holdout).
"""
import csv, gzip, io, json, math, os, sys, time, statistics as st
import urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))                # kalshi-scalper/
DATA = os.path.join(ROOT, "data", "perpgen")                          # git-ignored
RAW, CLEAN, HOLD = (os.path.join(DATA, x) for x in ("raw", "clean/dev", "clean/holdout"))
MANIFEST = os.path.join(DATA, "MANIFEST.json")
CUTS = os.path.join(DATA, "cuts.json")
GUARD = os.path.join(DATA, "holdout_guard.json")
BASE = "https://external-api.kalshi.com/trade-api/v2"
UA = {"User-Agent": "shwoopnet-research"}
CLASSES = ("Crypto", "Metals", "Indices", "Energy")
CHUNK_1M = 3 * 86400                  # 4,320 one minute candles per request; the API limit is 5,000
SLEEP = 0.4
SENTINEL = 1e9                        # any price above this is the int64 "no ask" value (9.2e14), never a quote


class Blocked(RuntimeError):
    """Repeated 429 or a refusal: stop and report, never work around."""


def _get(path, params=None):
    q = ("?" + urllib.parse.urlencode(params)) if params else ""
    n429 = 0
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(BASE + path + q, headers=UA), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                n429 += 1
                if n429 >= 3:
                    raise Blocked("repeated 429 on " + path)
                time.sleep(max(10.0, float(e.headers.get("Retry-After", 0) or 0)))
            elif e.code in (401, 403):
                raise Blocked("HTTP %d on %s" % (e.code, path))
            elif e.code == 400:
                raise RuntimeError("HTTP 400 %s %s" % (path, e.read()[:200]))
            else:
                time.sleep(2 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("GET failed " + path)


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_ts(s):
    return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())


def day(ts):
    return iso(ts)[:10]


def manifest():
    return json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}


# ------------------------------------------------------------------ fetch
def universe():
    ms = _get("/margin/markets", {"limit": 200})["markets"]
    out = [dict(ticker=m["ticker"], cls=m["asset_class"], status=m["status"], title=m.get("title"), tick=m.get("tick_size"),
                contract_size=m.get("contract_size"), cap=m.get("funding_cap"), deadband=m.get("funding_deadband"))
           for m in ms if m["asset_class"] in CLASSES]
    return sorted(out, key=lambda m: (m["cls"], m["ticker"]))


def fetch(as_of):
    os.makedirs(RAW, exist_ok=True)
    mf = manifest()
    if mf.get("as_of") and mf["as_of"] != as_of:
        print("existing snapshot has as_of", mf["as_of"], "; delete data/perpgen to start a new one"); return
    end = to_ts(as_of)
    uni = universe()
    mf = dict(as_of=as_of, fetched=iso(int(time.time())), universe=uni)
    json.dump(mf, open(MANIFEST, "w"), indent=1)
    # funding: one call without a ticker returns everything
    fp = os.path.join(RAW, "funding.json")
    if not os.path.exists(fp):
        fr = _get("/margin/funding_rates/historical")["funding_rates"]
        json.dump(fr, open(fp, "w")); time.sleep(SLEEP)
        print("funding rows", len(fr))
    for m in uni:
        if m["status"] != "active":
            continue
        tk = m["ticker"]
        d = os.path.join(RAW, tk); os.makedirs(d, exist_ok=True)
        hp = os.path.join(d, "h60.json")
        if not os.path.exists(hp):
            c = _get("/margin/markets/%s/candlesticks" % tk, {"period_interval": 60, "start_ts": end - 200 * 86400, "end_ts": end})["candlesticks"]
            json.dump(c, open(hp, "w")); time.sleep(SLEEP)
        hc = json.load(open(hp))
        if not hc:
            print(tk, "no hourly candles"); continue
        first = min(x["end_period_ts"] for x in hc)
        g = (first // CHUNK_1M) * CHUNK_1M
        n = 0
        while g < end:
            cp = os.path.join(d, "m1_%d.json" % g)
            if not os.path.exists(cp):
                c = _get("/margin/markets/%s/candlesticks" % tk, {"period_interval": 1, "start_ts": g, "end_ts": min(g + CHUNK_1M, end)})["candlesticks"]
                json.dump(c, open(cp, "w")); time.sleep(SLEEP)
            n += 1; g += CHUNK_1M
        print(tk, "hourly", len(hc), "from", iso(first), "chunks", n, flush=True)


# ------------------------------------------------------------------ clean
def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and 0 < v < SENTINEL else None


def row_from(c, end):
    b = c.get("bid") or {}; a = c.get("ask") or {}; p = c.get("price") or {}
    bc, ac = num(b.get("close")), num(a.get("close"))
    r = dict(ts=c["end_period_ts"],
             bid_o=num(b.get("open")), bid_h=num(b.get("high")), bid_l=num(b.get("low")), bid_c=bc,
             ask_o=num(a.get("open")), ask_h=num(a.get("high")), ask_l=num(a.get("low")), ask_c=ac,
             px_o=num(p.get("open")), px_h=num(p.get("high")), px_l=num(p.get("low")), px_c=num(p.get("close")), px_m=num(p.get("mean")),
             vol=num(c.get("volume")), vol_usd=num(c.get("volume_notional_value_dollars")),
             oi=num(c.get("open_interest")), oi_usd=num(c.get("open_interest_notional_value_dollars")))
    for k in ("ask_o", "ask_h", "ask_l", "ask_c"):             # a no-ask sentinel or an ask wildly above its bid is not a quote
        if r[k] is not None and bc is not None and r[k] > 2 * bc:
            r[k] = None
    if r["ask_c"] is not None and r["bid_c"] is not None and r["ask_c"] < r["bid_c"]:
        r["_crossed"] = 1
    r["ok"] = 1 if (r["bid_c"] is not None and r["ask_c"] is not None and r["ask_c"] >= r["bid_c"]) else 0
    return r


FIELDS = ["ts", "bid_o", "bid_h", "bid_l", "bid_c", "ask_o", "ask_h", "ask_l", "ask_c", "px_o", "px_h", "px_l", "px_c", "px_m",
          "vol", "vol_usd", "oi", "oi_usd", "ok"]


def write_csv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for r in rows:
            w.writerow(["" if r.get(k) is None else r[k] for k in fields])


def raw_rows(tk, kind, end):
    d = os.path.join(RAW, tk)
    files = [os.path.join(d, "h60.json")] if kind == "h" else sorted(os.path.join(d, f) for f in os.listdir(d) if f.startswith("m1_"))
    seen = {}
    stats = dict(raw=0, dup=0, sentinel=0, crossed=0, noquote=0, after=0)
    for fp in files:
        for c in json.load(open(fp)):
            stats["raw"] += 1
            if c["end_period_ts"] > end:
                stats["after"] += 1; continue
            r = row_from(c, end)
            for v in (c.get("ask") or {}).values():
                try:
                    stats["sentinel"] += float(v) >= SENTINEL
                except (TypeError, ValueError):
                    pass
            stats["crossed"] += r.pop("_crossed", 0)
            stats["noquote"] += 1 - r["ok"]
            if r["ts"] in seen:
                stats["dup"] += 1
            seen[r["ts"]] = r
    return [seen[k] for k in sorted(seen)], stats


def thirds(first_ts, end):
    f = datetime.fromisoformat(day(first_ts)).date()
    last = datetime.fromisoformat(day(end - 1)).date()
    n = (last - f).days + 1
    d1 = f + timedelta(days=n // 3); d2 = f + timedelta(days=(2 * n) // 3)
    return dict(first_day=str(f), last_day=str(last), n_days=n, validation_start=str(d1), holdout_start=str(d2))


def clean():
    mf = manifest(); end = to_ts(mf["as_of"])
    cuts = {}; stats = {}
    for m in mf["universe"]:
        tk = m["ticker"]
        if m["status"] != "active" or not os.path.isdir(os.path.join(RAW, tk)):
            continue
        m1, s1 = raw_rows(tk, "m", end); h1, s2 = raw_rows(tk, "h", end)
        good = [r for r in m1 if r["ok"]]
        if not good:
            continue
        c = thirds(good[0]["ts"], end); c["holdout_ts"] = to_ts(c["holdout_start"] + "T00:00:00Z"); c["validation_ts"] = to_ts(c["validation_start"] + "T00:00:00Z")
        cuts[tk] = c; stats[tk] = dict(m1=s1, h1=s2)
        for name, rows in (("1m", m1), ("1h", h1)):
            dev = [r for r in rows if r["ts"] - (60 if name == "1m" else 3600) < c["holdout_ts"]]      # a bar belongs to the day it STARTS in
            hold = [r for r in rows if r["ts"] - (60 if name == "1m" else 3600) >= c["holdout_ts"]]
            write_csv(os.path.join(CLEAN, "%s_%s.csv.gz" % (tk, name)), dev, FIELDS)
            write_csv(os.path.join(HOLD, "%s_%s.csv.gz" % (tk, name)), hold, FIELDS)
    # funding
    fr = json.load(open(os.path.join(RAW, "funding.json")))
    seen = {}
    for x in fr:
        t = to_ts(x["funding_time"])
        if t < end:
            seen[(x["market_ticker"], t)] = dict(ticker=x["market_ticker"], funding_time=x["funding_time"], ts=t, funding_rate=x["funding_rate"], mark_price=x["mark_price"])
    ff = ["ticker", "funding_time", "ts", "funding_rate", "mark_price"]
    for tk, c in cuts.items():
        rows = sorted((v for k, v in seen.items() if k[0] == tk), key=lambda r: r["ts"])
        write_csv(os.path.join(CLEAN, "%s_funding.csv.gz" % tk), [r for r in rows if r["ts"] < c["holdout_ts"]], ff)
        write_csv(os.path.join(HOLD, "%s_funding.csv.gz" % tk), [r for r in rows if r["ts"] >= c["holdout_ts"]], ff)
    json.dump(dict(as_of=mf["as_of"], cuts=cuts, clean_stats=stats), open(CUTS, "w"), indent=1)
    print("cleaned", len(cuts), "tickers")


# ------------------------------------------------------------------ loader (the only supported way to read the data)
def _read(path):
    out = []
    with gzip.open(path, "rt") as f:
        for r in csv.DictReader(f):
            out.append({k: (float(v) if v != "" else None) for k, v in r.items() if k not in ("ticker", "funding_time")}
                       | ({"funding_time": r["funding_time"]} if "funding_time" in r else {}))
    return out


FROZEN = os.path.join(ROOT, "workers", "PERPGEN_CUTS.json")      # committed copy of the cuts and the universe
MAX_SPREAD_BP = 6.0                                              # universe rule: median 1 minute spread over the ticker's DISCOVERY bars, at most this
MIN_DISCOVERY_DAYS = 7                                            # and at least this many calendar days in its discovery third


def cuts():
    c = json.load(open(CUTS))["cuts"]
    if os.path.exists(FROZEN):                                    # the registered cuts win: a re-fetch that moves a cut is refused
        f = json.load(open(FROZEN))["cuts"]
        if {k: (v["validation_ts"], v["holdout_ts"]) for k, v in c.items() if k in f} != {k: (v["validation_ts"], v["holdout_ts"]) for k, v in f.items()}:
            raise RuntimeError("cuts differ from workers/PERPGEN_CUTS.json")
    return c


def universe_frozen():
    """{'CRYPTO': [...], 'NONCRYPTO': [...]} from the committed file."""
    return json.load(open(FROZEN))["universe"]


def freeze():
    """Write workers/PERPGEN_CUTS.json: the cuts, the cost-only universe and the group of each ticker. Run once, then commit."""
    mf = manifest(); cj = json.load(open(CUTS)); cu = cj["cuts"]
    cls = {m["ticker"]: m["cls"] for m in mf["universe"]}
    rows = {}
    for tk, c in cu.items():
        m1 = _read(os.path.join(CLEAN, "%s_1m.csv.gz" % tk))
        sp = [(r["ask_c"] - r["bid_c"]) / ((r["ask_c"] + r["bid_c"]) / 2) * 1e4 for r in m1 if r["ok"] and r["ts"] - 60 < c["validation_ts"]]
        days = (datetime.fromisoformat(c["validation_start"]) - datetime.fromisoformat(c["first_day"])).days
        rows[tk] = dict(cls=cls[tk], median_spread_bp_discovery=round(st.median(sp), 3), discovery_days=days)
    uni = {"CRYPTO": [], "NONCRYPTO": []}
    for tk, r in sorted(rows.items()):
        if r["median_spread_bp_discovery"] <= MAX_SPREAD_BP and r["discovery_days"] >= MIN_DISCOVERY_DAYS:
            uni["CRYPTO" if r["cls"] == "Crypto" else "NONCRYPTO"].append(tk)
    json.dump(dict(as_of=cj["as_of"], rule="median 1m spread over discovery bars <= %.1f bp and >= %d discovery days" % (MAX_SPREAD_BP, MIN_DISCOVERY_DAYS),
                   universe=uni, ticker_costs=rows, cuts=cu), open(FROZEN, "w"), indent=1, sort_keys=True)
    print(uni)


def selftest():
    """The holdout cannot be returned: dev rows stop before each cut; load_stage and load_holdout refuse without the guard."""
    cu = cuts(); n = 0
    for tk in universe_frozen()["CRYPTO"] + universe_frozen()["NONCRYPTO"]:
        for kind, per in (("1m", 60), ("1h", 3600), ("funding", 0)):
            rows = load(tk, kind)
            assert rows and max(r["ts"] for r in rows) - per < cu[tk]["holdout_ts"], (tk, kind)
            assert min(r["ts"] for r in rows) - per >= to_ts(cu[tk]["first_day"] + "T00:00:00Z") - 1
            n += 1
        try:
            load_stage(tk, "validation"); raise SystemExit("validation leaked")
        except PermissionError:
            pass
        for bad in ("holdout", "all"):
            try:
                load_stage(tk, bad); raise SystemExit("holdout leaked")
            except PermissionError:
                pass
    if not os.path.exists(GUARD):
        try:
            load_holdout(universe_frozen()["CRYPTO"][0], "x"); raise SystemExit("holdout leaked")
        except PermissionError:
            pass
    print("selftest ok:", n, "dev files checked; holdout refused without guard (guard file present: %s)" % os.path.exists(GUARD))


def stage_of(tk, ts_start):
    """'discovery', 'validation' or 'holdout' for a bar that STARTS at ts_start."""
    c = cuts()[tk]
    return "discovery" if ts_start < c["validation_ts"] else ("validation" if ts_start < c["holdout_ts"] else "holdout")


def load(tk, kind="1m"):
    """Development rows (discovery + validation) of one ticker: kind '1m', '1h' or 'funding'. Cannot return holdout dates:
    the holdout rows live in a different directory that this function never opens."""
    rows = _read(os.path.join(CLEAN, "%s_%s.csv.gz" % (tk, kind)))
    c = cuts()[tk]
    assert all(r["ts"] <= c["holdout_ts"] + (3600 if kind != "funding" else 0) for r in rows) or kind == "funding"
    return rows


def load_stage(tk, stage, kind="1m", frozen_id=None):
    """stage 'discovery' or 'validation' (dev only). 'holdout' is refused here; use load_holdout. 'validation' also needs
    workers/PERPGEN_FROZEN_<frozen_id>.json to exist (the committed discovery survivor list), so validation cannot be read first."""
    if stage not in ("discovery", "validation"):
        raise PermissionError("holdout is read only through load_holdout with a guard file")
    if stage == "validation" and not (frozen_id and os.path.exists(os.path.join(ROOT, "workers", "PERPGEN_FROZEN_%s.json" % frozen_id))):
        raise PermissionError("validation is locked until the discovery survivor list is frozen and committed")
    c = cuts()[tk]; per = {"1m": 60, "1h": 3600, "funding": 0}[kind]
    lo, hi = (0, c["validation_ts"]) if stage == "discovery" else (c["validation_ts"], c["holdout_ts"])
    return [r for r in load(tk, kind) if lo <= r["ts"] - per < hi]


def load_holdout(tk, frozen_id, kind="1m"):
    """Read ONCE. Requires data/perpgen/holdout_guard.json = {"unlock": {"<frozen_id>": {"tickers": [...]}}} written by hand AFTER the
    survivor list is frozen and committed. The first successful read of a (frozen_id, ticker) is recorded in the guard file and any
    second read raises. Cross-ticker features at a holdout time may use another ticker's holdout only if it is unlocked for the same id."""
    if not os.path.exists(GUARD):
        raise PermissionError("holdout guard file missing: holdout is locked")
    g = json.load(open(GUARD))
    u = (g.get("unlock") or {}).get(frozen_id)
    if not u or tk not in u.get("tickers", []):
        raise PermissionError("holdout not unlocked for %s / %s" % (frozen_id, tk))
    used = g.setdefault("used", {})
    key = "%s|%s|%s" % (frozen_id, tk, kind)
    if key in used:
        raise PermissionError("holdout already read once for " + key)
    used[key] = iso(int(time.time()))
    json.dump(g, open(GUARD, "w"), indent=1)
    return _read(os.path.join(HOLD, "%s_%s.csv.gz" % (tk, kind)))


# ------------------------------------------------------------------ report (counts only: no return, no outcome)
def pct(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))] if v else None


def report():
    mf = manifest(); end = to_ts(mf["as_of"]); cj = json.load(open(CUTS)); cu = cj["cuts"]
    L = ["# PERPDATA report (data layer for PERPGEN; counts and costs only, no return or outcome of any rule computed)", "",
         "Snapshot as_of **%s** (candle end times before this instant; fetched %s). Source: `GET %s/margin/markets/{ticker}/candlesticks` (period 1 and 60) and `GET /margin/funding_rates/historical`, keyless. Cache `data/perpgen/` (git-ignored). Code `src/scalper/perpdata.py`." % (mf["as_of"], mf["fetched"], BASE), "",
         "Universe fetched: every ACTIVE perp of class Crypto, Metals, Indices, Energy at fetch time (%d). Inactive and skipped: %s. Equities (58 active) are excluded by the protocol (history since 2026-11-05)." % (
             sum(1 for m in mf["universe"] if m["status"] == "active"), ", ".join(m["ticker"] for m in mf["universe"] if m["status"] != "active") or "none"), "",
         "## Candles per ticker (1 minute; spread = (ask_c - bid_c) / mid in bps over usable bars, discovery region only; median spread is the COST used for the universe)", "",
         "| ticker | class | first bar (UTC) | last bar | span days | 1m bars | expected | missing | usable quote | sentinel fields | crossed | no quote | dup | spread med bp (discovery) | p90 | disc / valid / holdout start | 1h bars | 1h vs 1m close mismatch |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    cls = {m["ticker"]: m["asset_class"] if "asset_class" in m else m["cls"] for m in mf["universe"]}
    summ = {}
    for tk in sorted(cu, key=lambda t: (cls[t], t)):
        c = cu[tk]; st_ = cj["clean_stats"][tk]
        m1 = _read(os.path.join(CLEAN, "%s_1m.csv.gz" % tk)); mh = _read(os.path.join(HOLD, "%s_1m.csv.gz" % tk))
        h1 = _read(os.path.join(CLEAN, "%s_1h.csv.gz" % tk)) + _read(os.path.join(HOLD, "%s_1h.csv.gz" % tk))
        allr = m1 + mh
        good = [r for r in allr if r["ok"]]
        first, last = good[0]["ts"], good[-1]["ts"]
        exp = (last - first) // 60 + 1
        sp = [(r["ask_c"] - r["bid_c"]) / ((r["ask_c"] + r["bid_c"]) / 2) * 1e4 for r in m1 if r["ok"] and r["ts"] - 60 < c["validation_ts"]]
        sp_all = [(r["ask_c"] - r["bid_c"]) / ((r["ask_c"] + r["bid_c"]) / 2) * 1e4 for r in good]
        m1c = {r["ts"]: r for r in allr}
        mm = tot = 0
        for r in h1:
            o = m1c.get(r["ts"])
            if o and o["ok"] and r["ok"]:
                tot += 1; mm += abs(o["bid_c"] - r["bid_c"]) > 1e-9 or abs(o["ask_c"] - r["ask_c"]) > 1e-9
        s = st_["m1"]
        summ[tk] = dict(med=st.median(sp) if sp else None, p90=pct(sp, .9), med_all=st.median(sp_all))
        L.append("| %s | %s | %s | %s | %d | %d | %d | %d | %d | %d | %d | %d | %d | %.2f | %.2f | %s / %s / %s | %d | %d of %d |" % (
            tk, cls[tk], iso(first), iso(last), c["n_days"], len(allr), exp, exp - len(allr), len(good), s["sentinel"], s["crossed"], s["noquote"], s["dup"],
            summ[tk]["med"], summ[tk]["p90"], c["first_day"], c["validation_start"], c["holdout_start"], len(h1), mm, tot))
    L += ["", "Notes: `missing` = minutes between the first and last usable bar that the exchange did not serve (no forward fill is done anywhere). `sentinel fields` counts open/high/low/close ask fields at 9.2e14 (the int64 no-ask value) in the raw rows; they are set blank. `crossed` = ask close below bid close (set unusable). `no quote` = bars with no usable close quote. The spread column uses the discovery region of each ticker only; the full-history median is in the table below.", "",
          "## Median spread, all dates (information) and by hour of day UTC (discovery region)", "", "| ticker | median bp all | " + " | ".join("%02d" % h for h in range(0, 24, 3)) + " |", "|---|---|" + "---|" * 8]
    for tk in sorted(cu, key=lambda t: (cls[t], t)):
        c = cu[tk]; m1 = _read(os.path.join(CLEAN, "%s_1m.csv.gz" % tk))
        by = {}
        for r in m1:
            if r["ok"] and r["ts"] - 60 < c["validation_ts"]:
                by.setdefault(((r["ts"] - 60) // 3600 % 24) // 3, []).append((r["ask_c"] - r["bid_c"]) / ((r["ask_c"] + r["bid_c"]) / 2) * 1e4)
        L.append("| %s | %.2f | %s |" % (tk, summ[tk]["med_all"], " | ".join("%.1f" % st.median(by[i]) if by.get(i) else "" for i in range(8))))
    # funding calendar
    L += ["", "## Funding history (all markets, one call; `funding_rate` as served, decimal per funding interval)", "",
          "| ticker | rows | first | last | funding hours (UTC, count) | median gap h | nonzero rate | min | max | rows in dev | rows in holdout |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for tk in sorted(cu, key=lambda t: (cls[t], t)):
        fd = _read(os.path.join(CLEAN, "%s_funding.csv.gz" % tk)); fh = _read(os.path.join(HOLD, "%s_funding.csv.gz" % tk))
        a = fd + fh
        if not a:
            L.append("| %s | 0 | | | | | | | | 0 | 0 |" % tk); continue
        hrs = {}
        for r in a:
            h = int(r["funding_time"][11:13]); hrs[h] = hrs.get(h, 0) + 1
        gaps = [(a[i + 1]["ts"] - a[i]["ts"]) / 3600 for i in range(len(a) - 1)]
        v = [r["funding_rate"] for r in a]
        L.append("| %s | %d | %s | %s | %s | %.1f | %d | %.6f | %.6f | %d | %d |" % (tk, len(a), a[0]["funding_time"], a[-1]["funding_time"], " ".join("%02d:%d" % kv for kv in sorted(hrs.items())),
                                                                          st.median(gaps) if gaps else 0, sum(1 for x in v if x != 0), min(v), max(v), len(fd), len(fh)))
    L += ["", "Funding calendar facts: crypto settles every 8 hours (04, 12, 20 UTC; the 05, 13, 21 hours are the same slots after the US clock change); metals and indices and WTI settle on their own hours listed above. `funding_time` is the stamp of the settlement; the protocol uses a funding rate only from `funding_time` onward, never before, because when the rate becomes public is not documented.", ""]
    open(os.path.join(ROOT, "workers", "PERPDATA_REPORT.md"), "w").write("\n".join(L))
    print("report written")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    asof = sys.argv[sys.argv.index("--as-of") + 1] if "--as-of" in sys.argv else "2026-11-06T00:00:00Z"
    try:
        if cmd in ("fetch", "all"): fetch(asof)
        if cmd in ("clean", "all"): clean()
        if cmd in ("report", "all"): report()
        if cmd == "freeze": freeze()
        if cmd == "selftest": selftest()
    except Blocked as e:
        print("BLOCKED, stopping:", e); sys.exit(2)
