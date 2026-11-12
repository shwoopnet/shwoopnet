#!/usr/bin/env python3
"""POL-i2 (overnight staleness) COUNT STEP. Testing Desk, Nov 12, 2026. Research only: reads files, sends nothing, reads NO outcome.
Card: kalshi-scalper/refine_tools/POLITICS_CARDS_NOV11.md on claude/refine-live, row POL-i2 (unchanged; pins below are declared before any answer exists).
Count only, no profit claim. The card's kill: fewer than 40 qualifying gaps in either half = NOT_ENOUGH_DATA, card closed.
PINS (the card is silent or its data cannot give them; all fixed here, before data):
  P1 universe: every series Kalshi tags category Politics, read from the series-list answer of Desk B's CENSUS_LISTING pull (zero extra requests; stage 0 is NOT dispatched), not a hand list. More than MAX_SERIES -> stop and ask the Head.
  P2 window (AMENDMENT 1, Nov 12): markets that CLOSED in (2026-09-12, 2026-11-05); halves the sample on purpose to stay within the request budget. HELD_OUT_FROM = 2026-11-05T00:00Z is a date constant: nothing closing on or after it is listed or requested (kept for the scoring step).
  P3 liquid market: lifetime volume >= 200 contracts in the list (pre-filter, to save requests); the card's rule (>= 200 contracts traded in the 7 days before 22:00 ET) is applied on the candles.
  P4 data: HOURLY candles (period 60). The card's 06:30 ET quote does not exist at hourly grain, so "the quote has not followed" is the PROXY |ask(07:00) - ask(06:00)| <= 1c for a YES buy (bid for a NO buy), candles ending 06:00 and 07:00 ET. This is a deviation from the card; the looser count without the proxy is reported beside it. The verdict uses the proxy count; if only the looser count clears 40 per half the Head decides.
  P5 qualifying gap (per market, per ET date D): two-sided closes at the candles ending 22:00 ET on D, 06:00 and 07:00 ET on D+1; |mid(07:00) - mid(22:00)| >= 0.05; the side bought (YES at the ask if the gap is up, NO at 1 - bid if down) priced 0.10 to 0.90 at 07:00; liquid per P3. One per market per day.
  P6 halves: the qualifying gaps in date order, first half = first floor(n/2). A cluster is (series, D); clusters are reported next to gaps.
  P7 request cap: stage 2 has STAGE2_CAP requests; if more would be needed, markets are dropped by lowest lifetime volume (a settled tally, not a price) and the number dropped is reported.
Commands: build-s1 <series-list folder: the census pull> | build-s2 <s1 folder> | count <s1 lists folder> <s2 candle folders...> | cost-screen <quote files...>   (folders are kalshi-pull-data run folders)
"""
import calendar, gzip, json, os, re, statistics as st, sys, time
from datetime import datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
except Exception:
    NY = None

HELD_OUT_FROM = calendar.timegm((2026, 11, 5, 0, 0, 0))
CUTOVER = calendar.timegm((2026, 9, 12, 0, 0, 0))     # live endpoints for markets closing after it, /historical before
WINDOW_FROM = CUTOVER                                  # AMENDMENT 1 (Nov 12, Head's ruling): only markets closing after 2026-09-12; halves the sample on purpose; no /historical call at all
MAX_SERIES, STAGE2_CAP, PACK, BUDGET = 400, 600, 9000, 400   # BUDGET: the Head places the count only if stage 1 + stage 2 <= 400 requests
GAP, LO, HI, STALE, LIQ, FLOOR = 0.05, 0.10, 0.90, 0.01, 200.0, 40
RUN = {"status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
       "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                      "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
REG = "kalshi-scalper/workers/testing/POLI2_COUNT_REGISTRATION.md"


def iso(s):
    try:
        return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception:
        return None


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def job(job_id, purpose, eps, reqs, series, tickers):
    j = {"job_id": job_id, "owner": "MAIN", "registration": REG, "purpose": purpose, "heldout": "none read; nothing closing on or after 2026-11-05T00:00Z is listed or requested (kept for the scoring step); no outcome is used by the count",
         "allowed_endpoints": eps, "series_allowlist": sorted(series), "ticker_allowlist": sorted(tickers), "max_requests": len(reqs), "notes": "POL-i2 count step"}
    j.update(RUN); j["requests"] = reqs
    return j


def build_s0():
    return job("POLI2_SERIES", "POL-i2 count step, stage 0: the list of series tagged Politics (one request, no price).",
               [{"name": "series_list", "method": "GET", "path_pattern": "/series", "params_allowed": ["category"]}],
               [{"id": "series_politics", "path": "/series", "params": {"category": "Politics"}}], [], [])


def answers(folder):
    m = json.load(open(os.path.join(__import__("scorekit").guard(folder), "manifest.json")))
    for row in m["rows"]:
        if row.get("status") == 200 and row.get("file") and not row.get("truncated") and row.get("body_kind", "object") == "object":
            yield row, json.load(gzip.open(os.path.join(folder, row["file"])))


FREQUENCIES = ("daily", "weekly", "monthly")   # AMENDMENT 2 (Nov 12, before any data): the census answer lists 2,469 Politics series, 93 percent one_off or custom; one list each is 2,469 requests


def politics_series(s0):
    """Politics-category series with a repeating frequency (daily, weekly, monthly), from the series-list answer of the census pull (complete: the category answer was 2.98 MB, not truncated)."""
    out = set()
    for row, body in answers(s0):
        for s in body.get("series", []) if isinstance(body, dict) else []:
            if isinstance(s, dict) and str(s.get("category", "")).lower() == "politics" and s.get("frequency") in FREQUENCIES and re.fullmatch(r"[A-Z0-9]{2,32}", str(s.get("ticker", ""))):
                out.add(s["ticker"])
    return sorted(out)


def build_s1(s0):
    ser = politics_series(s0)
    if not ser:
        raise SystemExit("stage 0 answer holds no Politics series (or was truncated); stop and tell the Head")
    if len(ser) > MAX_SERIES:
        raise SystemExit("%d Politics series is over MAX_SERIES %d; stop and tell the Head" % (len(ser), MAX_SERIES))
    reqs = []
    for s in ser:
        reqs.append({"id": "live_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "limit": 1000, "min_close_ts": WINDOW_FROM, "max_close_ts": HELD_OUT_FROM}, "max_pages": 3})
    eps = [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "limit", "cursor", "min_close_ts", "max_close_ts"]}]
    j = job("POLI2_LISTS", "POL-i2 count step, stage 1: settled market lists of the Politics series (time and volume fields only; no price, no result used).", eps, reqs, ser, [])
    j["max_requests"] = len(reqs) + 21               # 79 lists + 21 slack for a second page; the runner counts pages against the cap. Stage 2 is capped at BUDGET minus the requests actually SENT
    return j


def markets_from(s1):  # only markets closing after the cutover (live endpoints) are listed, so hist below is always empty
    seen = {}
    for row, body in answers(s1):
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            if not isinstance(m, dict) or m.get("result") not in ("yes", "no"):
                continue
            c, o = iso(m.get("close_time", "")), iso(m.get("open_time", ""))
            v = num(m.get("volume_fp", m.get("volume")))
            t = m.get("ticker", "")
            if c and o and v is not None and v >= LIQ and WINDOW_FROM <= c < HELD_OUT_FROM and re.fullmatch(r"[A-Za-z0-9_.-]{4,80}", t):
                seen[t] = (c, o, v, t.split("-")[0])
    return seen


def build_s2(s1):
    man = json.load(open(os.path.join(__import__("scorekit").guard(s1), "manifest.json")))
    cap = min(STAGE2_CAP, BUDGET - int(man.get("requests_sent", len(man["job"]["requests"]))))   # AMENDMENT 1: stage 1 + stage 2 together at most BUDGET
    if cap < 1: raise SystemExit("stage 1 alone is over the budget of %d requests; stop and tell the Head" % BUDGET)
    mk = markets_from(s1)
    ranked = sorted(mk.items(), key=lambda kv: (-kv[1][2], kv[0]))
    live = [(t, x) for t, x in ranked if x[0] > CUTOVER]
    hist = [(t, x) for t, x in ranked if x[0] <= CUTOVER]
    def packs(items):
        out, cur = [], []
        for t, x in sorted(items, key=lambda kv: kv[1][0]):
            trial = cur + [(t, x)]
            hours = (max(y[0] for _, y in trial) - min(y[1] for _, y in trial)) / 3600.0
            if cur and hours * len(trial) > PACK:
                out.append(cur); cur = [(t, x)]
            else:
                cur = trial
        if cur: out.append(cur)
        return out
    lp = packs(live)
    n_req = len(lp) + len(hist)
    dropped = 0
    while n_req > cap and ranked:                # P7: drop the lowest-volume market until under the cap
        t, x = ranked.pop()
        dropped += 1
        live = [(a, b) for a, b in live if a != t]; hist = [(a, b) for a, b in hist if a != t]
        lp = packs(live); n_req = len(lp) + len(hist)
    reqs = []
    for p in lp:
        reqs.append({"id": "b%04d" % len(reqs), "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for t, _ in p), "start_ts": min(x[1] for _, x in p), "end_ts": max(x[0] for _, x in p), "period_interval": 60}})
    for t, x in sorted(hist, key=lambda kv: kv[1][0]):
        reqs.append({"id": t, "path": "/historical/markets/%s/candlesticks" % t, "params": {"start_ts": x[1], "end_ts": x[0], "period_interval": 60}})
    eps = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]},
           {"name": "hist_candles", "method": "GET", "path_pattern": "/historical/markets/(?P<ticker>[A-Za-z0-9_.-]+)/candlesticks", "params_allowed": ["start_ts", "end_ts", "period_interval"]}]
    keep = [t for t, _ in live + hist]
    j = job("POLI2_CANDLES", "POL-i2 count step, stage 2: hourly candles of the liquid settled Politics markets that closed 2025-11-05 to 2026-11-04.", eps, reqs, sorted({mk[t][3] for t in keep}), keep)
    j["notes"] += "; markets dropped by the request cap: %d" % dropped
    return j


def cents(node, key):
    if not isinstance(node, dict):
        return None
    for k in (key + "_dollars", key):
        v = num(node.get(k))
        if v is not None:
            return v / 100.0 if (k == key and v > 1.0) else v
    return None


def count_market(ticker, candles, close_ts):
    """Gaps of one market. Returns a list of dicts (date, series, strict, loose)."""
    by_end = {int(c["end_period_ts"]): c for c in candles}
    vol = sorted((int(c["end_period_ts"]), num(c.get("volume_fp", c.get("volume"))) or 0.0) for c in candles)
    ends = sorted(by_end)
    out = []
    seen_days = set()
    for e in ends:
        loc = datetime.fromtimestamp(e, NY)
        if not (loc.hour == 22 and loc.minute == 0):
            continue
        d = loc.date()
        if d in seen_days:
            continue
        seen_days.add(d)
        nxt = datetime(d.year, d.month, d.day, 7, 0, tzinfo=NY) + timedelta(days=1)
        t07 = int(nxt.timestamp()); t06 = t07 - 3600
        if t07 not in by_end or t06 not in by_end:
            continue
        def q(ts):
            c = by_end[ts]
            return cents(c.get("yes_bid"), "close"), cents(c.get("yes_ask"), "close")
        b22, a22 = q(e); b7, a7 = q(t07); b6, a6 = q(t06)
        if None in (b22, a22, b7, a7, b6, a6) or min(a22, a7, a6) <= 0 or b22 > a22 or b7 > a7:
            continue
        m22, m7 = (b22 + a22) / 2, (b7 + a7) / 2
        if abs(m7 - m22) < GAP - 1e-9:
            continue
        up = m7 > m22
        price = a7 if up else 1 - b7
        if not (LO - 1e-9 <= price <= HI + 1e-9):
            continue
        if sum(v for ts, v in vol if e - 7 * 86400 < ts <= e) < LIQ:
            continue
        stale = abs(a7 - a6) <= STALE + 1e-9 if up else abs(b7 - b6) <= STALE + 1e-9
        ent_b, ent_a = (b7, a7) if up else (b7, a7)
        mid7 = (b7 + a7) / 2
        out.append({"date": d.isoformat(), "series": ticker.split("-")[0], "ticker": ticker, "strict": stale, "loose": True, "within_24h_of_close": close_ts is not None and close_ts <= t07 + 86400, "no_exit": close_ts is not None and close_ts <= t07 + 86400,
                    "spread": a7 - b7, "round_trip": (a7 - b7) + 2 * 0.07 * mid7 * (1 - mid7)})
    return out


def candles_of(body, ticker):
    nodes = body.get("markets") if isinstance(body, dict) and "markets" in body else [body]
    for n in nodes:
        t = n.get("market_ticker") or n.get("ticker") or ticker
        if isinstance(n.get("candlesticks"), list) and (t == ticker or ticker is None):
            yield t, n["candlesticks"]


COST_MAX = 0.05      # AMENDMENT 3: median round trip at the entry hour above 5c closes the card on cost


def tally(gaps):
    """AMENDMENT 3 (Nov 12, Head of R&D, credited to Desk B's wording): the unit of the kill is the SERIES-MORNING (series, date D): several markets of one event moving together count once.
    CLOSED if fewer than 40 series-mornings with a qualifying gap in either half (halves by date); CLOSED on cost if the median round trip at the entry hour is above 5c. Gaps are still reported beside."""
    res = {}
    no_exit = sum(1 for g in gaps if g.get("no_exit"))                     # Desk B's point: a market that closes within 24 hours of the entry has no 24 hour time exit, so it cannot be a gap
    gaps = [g for g in gaps if not g.get("no_exit")]
    for name in ("strict", "loose"):
        sel = [g for g in gaps if g[name]]
        mornings = sorted({(g["date"], g["series"]) for g in sel})
        k = len(mornings) // 2
        h1, h2 = mornings[:k], mornings[k:]
        res[name] = {"series_mornings": len(mornings), "first_half": len(h1), "second_half": len(h2), "gaps": len(sel), "series_with_a_gap": len({g["series"] for g in sel}),
                     "within_24h_of_close": sum(1 for g in sel if g["within_24h_of_close"]),
                     "median_round_trip_at_entry": round(st.median([g["round_trip"] for g in sel]), 4) if sel else None, "median_spread_at_entry": round(st.median([g["spread"] for g in sel]), 4) if sel else None}
    s_ = res["strict"]; l_ = res["loose"]
    clears = lambda r: r["first_half"] >= FLOOR and r["second_half"] >= FLOOR
    rt = s_["median_round_trip_at_entry"]
    if rt is not None and rt > COST_MAX:
        verdict = "CLOSED on cost: the median round trip at the entry hour is %.1fc, above 5c (no further read)" % (100 * rt)
    elif clears(s_):
        verdict = "COUNT CLEARS 40 series-mornings per half on the strict (proxy) basis; this is a count, not a result"
    elif clears(l_):
        verdict = "ONLY the loose count clears 40 series-mornings per half: the Head decides (the proxy is a deviation from the card)"
    else:
        verdict = "CLOSED: fewer than 40 series-mornings with a qualifying gap in a half; no further read"
    n = s_["series_mornings"]
    label = "no evidence at n = %d series-mornings" % n if n < 100 else "count only; any scoring needs its own registration and the held-out from 2026-11-05"
    return {"strict": s_, "loose": l_, "verdict": verdict, "label": label, "gaps_excluded_no_24h_exit": no_exit,
            "premise_note": "The card's premise (a quote that has not yet followed) is NOT tested at hourly resolution; what is counted is overnight gaps, with the 06:00-to-07:00 hourly ask proxy"}


def cost_screen(quote_files, series_set=None):
    """AMENDMENT 3 step 4, zero extra requests. Median round trip (the whole spread plus two taker fees 0.07 x mid x (1 - mid), Forensics' definition in HOW_TO_PRICE_A_PAPER_TRADE.md) for two-sided quotes priced 20c to 80c
    (mid), from politics recorder quote files (`pol-data` polrec/*/quotes.csv.gz, columns series, ticker, yes_bid, yes_ask). A list quote is good enough for a spread LEVEL (up to 11 s old). Reads quotes only; results.csv is never opened.
    series_set = the 79 series (restrict to them). Why not the lists answer: settled (finalized) markets in a lists answer carry yes_bid 0 and yes_ask 1 (checked on 3,000 of CFRTI_K_LISTS), so they hold no spread."""
    import csv
    rts, sps, ms, ser = [], [], set(), set()
    for f in quote_files:
        op = gzip.open if f.endswith(".gz") else open
        with op(f, "rt") as fh:
            for r in csv.DictReader(fh):
                if series_set is not None and r["series"] not in series_set: continue
                b, a = num(r.get("yes_bid")), num(r.get("yes_ask"))
                if b is None or a is None or not (0 < b < a < 1): continue
                m = (a + b) / 2
                if not (0.20 <= m <= 0.80): continue
                rts.append((a - b) + 2 * 0.07 * m * (1 - m)); sps.append(a - b); ms.add(r["ticker"]); ser.add(r["series"])
    if not rts: return {"quotes": 0, "verdict": "no two-sided quote priced 20c to 80c: cannot screen"}
    med = st.median(rts)
    return {"quotes": len(rts), "distinct_markets": len(ms), "series": len(ser), "median_round_trip": round(med, 4), "median_spread": round(st.median(sps), 4),
            "verdict": ("CLOSED on cost: median round trip %.1fc is above 5c; stage 2 is never sent" % (100 * med)) if med > COST_MAX else ("under the 5c line (%.1fc): send the stage 2 request count to the Head for a go" % (100 * med))}


def count(folders, lists=None):
    """lists = the stage 1 lists folder (REQUIRED: the market's close time decides whether a 24 hour exit exists)."""
    if lists is None: raise ValueError("the lists folder is required: a market closing within 24 hours of the entry cannot be a gap (no 24 hour exit)")
    closes = {t: v[0] for t, v in markets_from(lists).items()}
    gaps, seen = [], 0
    for f in folders:
        man = json.load(open(os.path.join(__import__("scorekit").guard(f), "manifest.json")))
        for row, body in answers(f):
            rid = row["id"]
            hint = None if rid.startswith("b") and re.fullmatch(r"b\d{4}", rid) else rid
            for t, cs in candles_of(body, hint):
                seen += 1
                gaps += count_market(t, cs, closes.get(t))
    out = tally(gaps)
    out["markets_read"] = seen
    return out


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    if c == "build-s0": print(json.dumps(build_s0(), indent=1))
    elif c == "build-s1": print(json.dumps(build_s1(sys.argv[2]), indent=1))
    elif c == "build-s2": print(json.dumps(build_s2(sys.argv[2]), indent=1))
    elif c == "count": print(json.dumps(count(sys.argv[3:], sys.argv[2]), indent=1))
    elif c == "cost-screen": print(json.dumps(cost_screen(sys.argv[2:]), indent=1))
    else: print(__doc__)
