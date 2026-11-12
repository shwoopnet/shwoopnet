#!/usr/bin/env python3
"""UNRATEROUND (Desk B card 4) against the slow-family paper screen (docs/POLITICS_RULES.md section 8). Testing Desk, Nov 12, 2026.
Research only: reads files, sends nothing. REGISTERED Nov 12, 2026 (Head of R&D ruling): kalshi-scalper/workers/testing/UNRATEROUND_REGISTRATION.md.
Commands: build-lists | events <s1 folder> | build-s2 <s1 folder> <bls_levels.csv> | score <s1 folder> <s2 folder(s)> <bls_levels.csv>
bls_levels.csv: year,month,unemployed,labor_force (BLS LNS13000000 and LNS11000000, thousands), supplied from a public BLS read.
"""
import calendar, csv, gzip, json, math, os, re, sys, time

CUTOFF = calendar.timegm((2026, 11, 5, 0, 0, 0))     # events whose first market closes on or after this are never read (forward only)
CUTOVER = calendar.timegm((2026, 9, 12, 0, 0, 0))
SERIES = ["KXU3", "KXUE"]                              # candidates; stage 0 says which one exists. Nothing else is pulled.
MONTHS = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
LO, HI, NEAR, EDGE8, MIN_EVENTS = 0.10, 0.80, 0.35, 0.08, 30
VINTAGE_FROM = (2026, 1)      # AMENDMENT 1 (Nov 12, 2026, before any data; Desk B's note): u0 must be the rate AS FIRST PUBLISHED. BLS revises the household survey's seasonal factors every January for the past five years, so levels
                              # pulled now for months before 2026-01 are not what the market saw; months from 2026-01 have not been revised since release. An event whose u0 month is earlier is dropped and COUNTED, unless a first-published source is approved.
SD_SPANS = [((2010, 1), (2019, 12)), ((2022, 1), (2025, 12))]
REG = "kalshi-scalper/workers/testing/UNRATEROUND_REGISTRATION.md"
RUN = {"status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
       "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                      "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
# READ-ONCE MARKER: not yet read; UNRATEROUND first read allowed on or after the Head's go; after the read: READ ON <date>, commit <hash>


def iso(s):
    try: return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None


def num(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def job(job_id, purpose, eps, reqs, series, tickers):
    j = {"job_id": job_id, "owner": "MAIN", "registration": REG, "purpose": purpose,
         "heldout": "none read; nothing closing on or after 2026-11-05T00:00Z is requested (forward only)", "allowed_endpoints": eps, "series_allowlist": sorted(series),
         "ticker_allowlist": sorted(tickers), "max_requests": len(reqs), "notes": "UNRATEROUND paper-screen read"}
    j.update(RUN); j["requests"] = reqs
    return j


def build_lists():
    """Stage 0 and 1 in one job (Head's ruling Nov 12): the settled lists of both candidate series, live and historical. 4 requests, at most 8 with paging.
    An empty or 404 answer for the series that is not unemployment is an answer. No price is used from these lists."""
    eps = [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "limit", "cursor", "max_close_ts"]},
           {"name": "hist_markets_list", "method": "GET", "path_pattern": "/historical/markets", "params_allowed": ["series_ticker", "limit", "cursor"]}]
    reqs = []
    for s in SERIES:
        reqs.append({"id": "live_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "limit": 1000, "max_close_ts": CUTOFF - 1}, "max_pages": 2})
        reqs.append({"id": "hist_" + s, "path": "/historical/markets", "params": {"series_ticker": s, "limit": 1000}, "max_pages": 2})
    return job("UNRATE_LISTS", "UNRATEROUND stages 0 and 1: settled market lists of the candidate unemployment series KXU3 and KXUE (strikes, close times, results, titles; no price).", eps, reqs, SERIES, [])


def answers(folder):
    m = json.load(open(os.path.join(folder, "manifest.json")))
    for row in m["rows"]:
        if row.get("status") == 200 and row.get("file"):
            yield row, json.load(gzip.open(os.path.join(folder, row["file"])))


def event_month(event):
    m = re.fullmatch(r"[A-Z0-9]+-(\d\d)([A-Z]{3})(\d\d)?", event)
    return (2000 + int(m.group(1)), MONTHS[m.group(2)]) if m and m.group(2) in MONTHS else None


def events_from(s1):
    ev = {}
    pages = [b for _, b in answers(s1)]
    unemp = {m.get("ticker", "").split("-")[0] for b in pages if isinstance(b, dict) for m in b.get("markets", []) if re.search(r"unemploy", json.dumps(m).lower())}
    for body in pages:
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            if m.get("ticker", "").split("-")[0] not in unemp: continue          # only the series whose markets say unemployment (KXU3 or KXUE, whichever it is)
            c = iso(m.get("close_time", "")); et = m.get("event_ticker", "")
            if not c or c >= CUTOFF or m.get("result") not in ("yes", "no") or not event_month(et): continue
            ev.setdefault(et, []).append({"ticker": m["ticker"], "close": c, "result": m["result"], "type": m.get("strike_type"), "floor": num(m.get("floor_strike")), "cap": num(m.get("cap_strike"))})
    ev = {e: v for e, v in ev.items() if event_month(e)[1] != 1}      # reference month January is excluded (annual population controls)
    if VINTAGE_FROM is not None:
        keep = {e: v for e, v in ev.items() if prev(event_month(e)) >= VINTAGE_FROM}
        events_from.excluded_for_vintage = len(ev) - len(keep)
        return keep
    events_from.excluded_for_vintage = 0
    return ev


def events_report(s1):
    ev = events_from(s1)
    n = len(ev)
    return {"events_excluding_january_before_cutoff": n, "excluded_u0_not_first_published": getattr(events_from, "excluded_for_vintage", 0), "label": ("no evidence at n = %d (under 30 independent events; no candle is pulled, nothing scored)" % n) if n < MIN_EVENTS else "n = %d events: enough to read once against the screen (the haircut line is n = %.1f)" % (n, 0.66 * n)}


def levels(path):
    d = {}
    for r in csv.DictReader(open(path)):
        d[(int(r["year"]), int(r["month"]))] = float(r["unemployed"]) / float(r["labor_force"]) * 100.0
    return d


def prev(ym): return (ym[0], ym[1] - 1) if ym[1] > 1 else (ym[0] - 1, 12)


def model_sd(lv):
    ch = []
    for (lo, hi) in SD_SPANS:
        for ym in sorted(lv):
            if lo <= ym <= hi and ym[1] != 1 and prev(ym) in lv and prev(ym) >= lo:
                ch.append(lv[ym] - lv[prev(ym)])
    mu = sum(ch) / len(ch)
    return math.sqrt(sum((x - mu) ** 2 for x in ch) / (len(ch) - 1)), len(ch)


def Phi(z): return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def p_yes(mk, u0, sd):
    """P(YES) under u1 ~ N(u0, sd), headline = u1 rounded half up to 0.1 (a pin: checked against the rules text at read)."""
    t, f, c = mk["type"], mk["floor"], mk["cap"]
    if t == "greater" and f is not None: return 1 - Phi((f + 0.05 - u0) / sd)
    if t == "less" and c is not None: return Phi((c - 0.05 - u0) / sd)
    if t == "between" and f is not None and c is not None: return Phi((c + 0.05 - u0) / sd) - Phi((f - 0.05 - u0) / sd)
    return None


def near(mk, u0):
    xs = [x for x in (mk["floor"], mk["cap"]) if x is not None]
    return bool(xs) and min(abs(x - u0) for x in xs) <= NEAR


def entry_ts(markets):
    return (min(m["close"] for m in markets) - 3 * 86400) // 3600 * 3600


def build_s2(s1, bls):
    lv = levels(bls); ev = events_from(s1); reqs, keep, ser = [], [], set()
    for e, ms in sorted(ev.items(), key=lambda kv: min(m["close"] for m in kv[1])):
        u0 = lv.get(prev(event_month(e)))
        if u0 is None: continue
        et = entry_ts(ms)
        for m in ms:
            if not near(m, u0): continue
            keep.append(m["ticker"]); ser.add(m["ticker"].split("-")[0])
            if m["close"] > CUTOVER:
                reqs.append({"id": m["ticker"], "path": "/markets/candlesticks", "params": {"market_tickers": m["ticker"], "start_ts": et - 12 * 3600, "end_ts": et + 3600, "period_interval": 60}})
            else:
                reqs.append({"id": m["ticker"], "path": "/historical/markets/%s/candlesticks" % m["ticker"], "params": {"start_ts": et - 12 * 3600, "end_ts": et + 3600, "period_interval": 60}})
    eps = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]},
           {"name": "hist_candles", "method": "GET", "path_pattern": "/historical/markets/(?P<ticker>[A-Za-z0-9_.-]+)/candlesticks", "params_allowed": ["start_ts", "end_ts", "period_interval"]}]
    return job("UNRATE_CANDLES", "UNRATEROUND stage 2: hourly candles around 3 days before each release for the markets whose strike is within 0.35 of the last unrounded rate.", eps, reqs, ser, keep)


def cents(node, key):
    if not isinstance(node, dict): return None
    for k in (key + "_dollars", key):
        v = num(node.get(k))
        if v is not None: return v / 100.0 if (k == key and v > 1.0) else v
    return None


def fee(p): return 0.07 * p * (1 - p)


def trade_for_event(e, ms, lv, sd, candles):
    """The single (market, side) with the largest model-minus-price among 0.10..0.80 priced sides; one per event. candles: {ticker: [candle]}."""
    u0 = lv.get(prev(event_month(e)))
    if u0 is None: return None, "no_u0"
    et = entry_ts(ms); best = None
    for m in ms:
        cs = candles.get(m["ticker"])
        if not cs or not near(m, u0): continue
        ok = [c for c in cs if int(c["end_period_ts"]) <= et + 3600 and int(c["end_period_ts"]) >= et - 6 * 3600]
        if not ok: continue
        c = max(ok, key=lambda x: int(x["end_period_ts"]))
        b, a = cents(c.get("yes_bid"), "close"), cents(c.get("yes_ask"), "close")
        p = p_yes(m, u0, sd)
        if b is None or a is None or p is None or a <= 0 or b > a or a >= 1: continue
        for side, price, edge, win in (("YES", a, p - a, m["result"] == "yes"), ("NO", 1 - b, b - p, m["result"] == "no")):
            if LO <= price <= HI and (best is None or edge > best["edge"]):
                best = {"event": e, "ticker": m["ticker"], "side": side, "price": price, "edge": edge, "win": win, "date": et}
    return best, ("ok" if best else "no_tradable_side")


def stats(trs, slip=0.0):
    w = sum(1 - (t["price"] + slip) - fee(t["price"] + slip) for t in trs if t["win"])
    l = sum((t["price"] + slip) + fee(t["price"] + slip) for t in trs if not t["win"])
    net = w - l
    return {"n": len(trs), "net": round(net, 4), "pf": (w / l) if l > 0 else None}


def score(s1, s2s, bls):
    lv = levels(bls); sd, nch = model_sd(lv); ev = events_from(s1); candles = {}
    for f in s2s:
        for row, body in answers(f):
            for n in (body.get("markets") if isinstance(body, dict) and "markets" in body else [body]):
                t = n.get("market_ticker") or n.get("ticker") or row["id"]
                if isinstance(n.get("candlesticks"), list): candles[t] = n["candlesticks"]
    trs, skipped = [], {}
    for e, ms in sorted(ev.items()):
        t, why = trade_for_event(e, ms, lv, sd, candles)
        if t: trs.append(t)
        else: skipped[why] = skipped.get(why, 0) + 1
    trs.sort(key=lambda t: (t["date"], t["event"]))
    k = len(trs) // 2; h1, h2 = trs[:k], trs[k:]
    s0, s1_, a, b = stats(trs), stats(trs, 0.01), stats(h1), stats(h2)
    n = len(trs)
    if n < MIN_EVENTS: label = "no evidence at n = %d" % n
    elif s0["pf"] is not None and s0["pf"] >= 1.3 and a["net"] > 0 and b["net"] > 0: label = "on the paper list (unproven)"
    else: label = "off the list (failed the screen)"
    ge8 = [t for t in trs if t["edge"] >= EDGE8]
    return {"label": label, "events": len(ev), "trades": n, "skipped": skipped, "sd": round(sd, 4), "sd_from_changes": nch, "all_events_rule": s0, "plus_1c": s1_, "first_half": a, "second_half": b,
            "original_rule_subset_edge_ge_8c": stats(ge8), "haircut_line": "after a 34 percent fill drop the expected n is %.1f against the screen's 30%s" % (0.66 * n, "" if 0.66 * n >= MIN_EVENTS else ": on this line the label is 'no evidence at n = %.0f', whatever the headline shows" % (0.66 * n)),
            "price_source": "hourly candle, freshness not measured on this series", "tries_against_the_screen": "this read is try 2 of the UNRATEROUND card; the Head states the running count"}


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    if c == "build-lists": print(json.dumps(build_lists(), indent=1))
    elif c == "events": print(json.dumps(events_report(sys.argv[2]), indent=1))
    elif c == "build-s2": print(json.dumps(build_s2(sys.argv[2], sys.argv[3]), indent=1))
    elif c == "score": print(json.dumps(score(sys.argv[2], sys.argv[3].split(","), sys.argv[4]), indent=1))
    else: print(__doc__)
