#!/usr/bin/env python3
"""POLGAPH, an INDEPENDENT SECOND BUILD (Forensics desk, 2026-11-13, on the Head of R&D's order: a second build from the text by another desk BEFORE the lists job is
dispatched). Written from Desk B's registration with Amendments 1 and 2 (claude/idea-desk-b, kalshi-scalper/workers/polgap/POLGAPH_REGISTRATION.md at 0d043306, sha256
69eec8d6...) and POLGAPH_SERIES.json ALONE. Desk B's polgaph.py was not read. Nothing of this card has been requested or read by anyone: invented rows only.

Development only: a market closing on or after 2026-11-13T00:00:00Z is refused, and any path in or resolving into a HELDOUT_ folder is refused.
NO RESULT IS READ BEFORE THE COST LINE: the result fields are kept in a separate table that is opened only after the cost line has passed.

usage: python3 -I polgaph_second.py <POLGAPH_SERIES.json> --lists <run ...> --hourly <run ...> --minute <run ...>
  each run is a kalshi-pull answer folder (manifest.json + NNNN.json.gz); a candle answer is {"markets": [{"market_ticker", "candlesticks": [{end_period_ts, yes_bid, yes_ask, volume_fp}]}]}

Places where the text leaves a choice (AMBIGUITIES, printed with the output):
 1. Step 1's two failures are counted apart: "no look" (one of the three hourly candles is missing) and "not two-sided" (all three present, one is not 0 < bid < ask < 1).
 2. The gap side's quotes: YES uses the YES bid and ask; NO uses ask = 1 minus YES bid and bid = 1 minus YES ask. The spread of either side is the YES spread.
 3. A market's event is its event_ticker; its series is the ticker's first part. A market-morning is identified by the Eastern date of its 07:00 look.
 4. Step 7's pick is made among the event's markets that pass steps 1 to 6 on that morning; the others are counted as "not the event's pick". The pick is then walked in time
    order: blocked if the event holds an earlier FILLED bet whose market closes after this look; else the fill test.
 5. "The minute request was answered" for a market and morning: some request of a minute run answered 200, names the ticker in market_tickers, and its start_ts to end_ts
    span contains the minute ending 07:01. Otherwise "no fill data".
 6. In the 07:01 candle the bought side's ask is the YES ask for YES and 1 minus the YES bid for NO; a missing or zero YES bid is "no ask" for NO, a missing ask or an ask of 1 is "no ask" for YES.
 7. A void is any result that is neither yes nor no. The figure "with the settlement value paid instead" uses the list's settlement_value_dollars when it is a number (YES value; NO gets 1 minus it), and is left out otherwise.
 8. The optimistic, same-candle figure books every pick that was not blocked (filled, not filled and no fill data alike) at its limit.
 9. The largest number open at once is taken at each filled bet's look (bets with look at or before it and close after it).
10. Profit factor with no losses is infinite and passes a "1.5 or more" line; with no wins it is 0. The lines are tested with a 1e-9 tolerance on the float figure.
11. Family rule (Amendment 1, point 2): if the pooled read would survive and one family's net is more than half of the pooled net, the verdict is that family's own read.
12. The hourly volume of a candle is its volume_fp (or volume) field read as a number; a missing volume is 0.
"""
import sys, os, json, gzip, math, statistics, collections
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
def iso(s): return int(datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
DEV_FROM, HELD_FROM = iso("2026-09-12T00:00:00Z"), iso("2026-11-13T00:00:00Z")
HALF_DATE = "2026-10-13"
GAP, QUIET, STEADY, BAND, SPREAD, LIQUID, SLIP = 0.05, 0.02, 0.01, (0.10, 0.64), 0.04, 200.0, 0.01
MIN_FILLED, MIN_HALF, COST_LINE, PF_LINE, HALF_LINE = 150, 40, 0.04, 1.5, 1.0
EPS = 1e-9
FRESH = "candle freshness measured on Bitcoin 15 minute only, not on these markets"
AMBIGUITIES = [l.strip() for l in __doc__.split("AMBIGUITIES, printed with the output):")[1].strip().split("\n")]


def refuse_heldout(path):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)):
            raise SystemExit("REFUSED: %s is in or resolves into a HELDOUT_ folder (standing rule (h))" % path)


def answers(folder):
    refuse_heldout(folder)
    man = json.load(open(os.path.join(folder, "manifest.json")))
    for row in man["rows"]:
        if row.get("status") != 200 or not row.get("file"): continue
        yield row, json.load(gzip.open(os.path.join(folder, row["file"]), "rt"))


def num(v):
    try:
        x = float(v)
        return x if x == x else None
    except (TypeError, ValueError): return None


def px(d): return num(d.get("close_dollars")) if isinstance(d, dict) else None
def two(q): return q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1] < 1
def fee_up(p): return math.ceil(0.07 * p * (1 - p) * 100 - EPS) / 100.0
def side_quote(q, side): return (q[0], q[1]) if side == "yes" else (1 - q[1], 1 - q[0])          # (bid, ask) of the bought side
def et_ts(date, hour): return int(datetime(date.year, date.month, date.day, hour, 0, tzinfo=ET).timestamp())


def read_lists(folders, series):
    """-> markets {ticker: {...no result...}}, results {ticker: (result, settlement value)}, counts. Results live in their own table."""
    mk, res, C = {}, {}, collections.Counter(); asked = set()
    for f in folders:
        for row, body in answers(f):
            s = (row.get("params") or {}).get("series_ticker")
            if s: asked.add(s)
            for m in (body.get("markets") or []) if isinstance(body, dict) else []:
                t = str(m.get("ticker", "")); ser = t.split("-")[0]
                if ser not in series: continue
                try: op, cl = iso(m["open_time"]), iso(m["close_time"])
                except Exception: C["markets with no open or close time, dropped"] += 1; continue
                if cl >= HELD_FROM: C["markets refused as held-out (close on or after 2026-11-13)"] += 1; continue
                if cl < DEV_FROM: C["markets closing before 2026-09-12, not in the window"] += 1; continue
                mk[t] = {"ticker": t, "series": ser, "event": m.get("event_ticker") or t.rsplit("-", 1)[0], "open": op, "close": cl}
                res[t] = (str(m.get("result") or "").lower(), num(m.get("settlement_value_dollars")))
    C["series asked"] = len(asked & set(series)) or len(series); C["series with any settled market in the window"] = len({m["series"] for m in mk.values()}); C["markets"] = len(mk)
    return mk, res, C


def read_candles(folders, wanted, want_interval):
    """-> {ticker: {end_ts: (bid, ask, volume)}}, and the answered spans [(tickers set, start_ts, end_ts)]"""
    out = {}; spans = []
    for f in folders:
        for row, body in answers(f):
            p = row.get("params") or {}
            if want_interval is not None and p.get("period_interval") not in (None, want_interval): continue
            spans.append((set(str(p.get("market_tickers", "")).split(",")), p.get("start_ts"), p.get("end_ts")))
            for m in (body.get("markets") or []) if isinstance(body, dict) else []:
                t = m.get("market_ticker")
                if t not in wanted: continue
                d = out.setdefault(t, {})
                for c in m.get("candlesticks") or []:
                    if isinstance(c.get("end_period_ts"), int):
                        v = num(c.get("volume_fp")); v = num(c.get("volume")) if v is None else v
                        d[c["end_period_ts"]] = (px(c.get("yes_bid")), px(c.get("yes_ask")), v or 0.0)
    return out, spans


def pf(v):
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return None if (w == 0 and l == 0) else (float("inf") if l == 0 else w / l)


def stats(bets, key="net"):
    v = [b[key] for b in bets]; n = len(v)
    by = collections.defaultdict(float)
    for b in bets: by[b["event"]] += b[key]
    den = math.sqrt(sum(s * s for s in by.values()))
    return {"n": n, "wins": sum(1 for b in bets if b["win"] is True), "voids": sum(1 for b in bets if b["win"] is None), "pf": pf(v), "mean": (sum(v) / n) if n else None, "net": sum(v),
            "z_event_clustered": (sum(v) / den) if den > 0 else 0.0}


def book(b, results, key="net"):
    """sets the cash result of a bet from the results table: win 1 - limit - fee; loss -(limit + fee); void -fee."""
    r, sv = results[b["ticker"]]; lim, fee = b["limit"], b["fee"]
    if r in ("yes", "no"): b["win"] = (r == b["side"]); b[key] = (1 - lim - fee) if b["win"] else -(lim + fee)
    else: b["win"] = None; b[key] = -fee
    if key == "net": b["net_with_settlement_value"] = b[key] if r in ("yes", "no") or sv is None else ((sv if b["side"] == "yes" else 1 - sv) - lim - fee)
    return b


def measure(spec, list_folders, hourly_folders, minute_folders):
    series = set(spec["series"]); fam = {s: f for f, ss in spec["families"].items() for s in ss}
    mk, results, C = read_lists(list_folders, series)
    hourly, _ = read_candles(hourly_folders, set(mk), 60)
    C["markets with any hourly candle"] = sum(1 for t in mk if hourly.get(t))
    cand = []; quiet = []; cost = []
    for t, m in sorted(mk.items()):
        h = hourly.get(t) or {}
        d = datetime.fromtimestamp(m["open"], ET).date(); last = datetime.fromtimestamp(m["close"], ET).date()
        while d <= last:
            look = et_ts(d, 7)
            if m["open"] < look < m["close"]:
                C["market-mornings"] += 1
                prev = d - timedelta(days=1); t22, t06 = et_ts(prev, 22), et_ts(d, 6)
                q22, q06, q07 = h.get(t22), h.get(t06), h.get(look)
                if q22 is None or q06 is None or q07 is None: C["no look (an hourly candle missing)"] += 1
                elif not (two(q22) and two(q06) and two(q07)): C["not two-sided at one of the three candles"] += 1
                else:
                    C["1. three two-sided candles"] += 1
                    gap = (q07[0] + q07[1]) / 2 - (q22[0] + q22[1]) / 2
                    vol = sum(v[2] for ts, v in h.items() if t22 - 7 * 86400 < ts <= t22)
                    def passes(side):
                        b6, a6 = side_quote(q06, side); b7, a7 = side_quote(q07, side)
                        if abs(a7 - a6) > STEADY + EPS: return "3. steady", None
                        if not (BAND[0] - EPS <= a7 <= BAND[1] + EPS): return "4. band", None
                        if a7 - b7 > SPREAD + EPS: return "5. spread", None
                        if vol < LIQUID - EPS: return "6. liquid", None
                        return None, (b7, a7)
                    base = {"ticker": t, "event": m["event"], "series": m["series"], "family": fam[m["series"]], "date": d.isoformat(), "look": look, "close": m["close"]}
                    if abs(gap) >= GAP - EPS:
                        side = "yes" if gap > 0 else "no"; C["2. gap of 5c or more"] += 1
                        b7, a7 = side_quote(q07, side); lim = round(a7 + SLIP, 6)
                        cost.append(((a7 - (a7 + b7) / 2) + fee_up(lim), (lim - (a7 + b7) / 2) + fee_up(lim)))
                        why, q = passes(side)
                        if why:
                            for step in ("3. steady", "4. band", "5. spread", "6. liquid"):
                                if step == why: C["failed " + step] += 1; break
                                C["left after " + step] += 1
                        else:
                            for step in ("3. steady", "4. band", "5. spread", "6. liquid"): C["left after " + step] += 1
                            cand.append(dict(base, side=side, ask=q[1], limit=lim, fee=fee_up(lim)))
                    elif abs(gap) < QUIET - EPS:
                        ok = [(s_, passes(s_)[1]) for s_ in ("yes", "no")]; ok = [(s_, q) for s_, q in ok if q is not None]
                        if ok:
                            s_, q = min(ok, key=lambda x: (round(abs(x[1][1] - 0.5), 9), 0 if x[0] == "yes" else 1)); lim = round(q[1] + SLIP, 6)
                            quiet.append(dict(base, side=s_, ask=q[1], limit=lim, fee=fee_up(lim)))
            d += timedelta(days=1)
    nearest = lambda rows: min(rows, key=lambda r: (round(abs(r["ask"] - 0.5), 9), r["ticker"]))
    def one_per_event(rows):
        g = collections.defaultdict(list)
        for r in rows: g[(r["event"], r["date"])].append(r)
        return sorted((nearest(v) for v in g.values()), key=lambda r: (r["look"], r["ticker"]))
    picks = one_per_event(cand); C["left after 7. one per event and morning (the event's pick)"] = len(picks); C["not the event's pick"] = len(cand) - len(picks)
    minute, spans = read_candles(minute_folders, {p["ticker"] for p in picks}, 1)
    answered = lambda tk, ts: any(tk in s and (a is None or a < ts) and (b is None or ts <= b) for s, a, b in spans)
    open_bets = collections.defaultdict(list); fired = []
    for p in picks:
        if any(c > p["look"] for c in open_bets[p["event"]]): C["blocked: the event holds an earlier filled, unsettled bet"] += 1; continue
        C["fired"] += 1; fired.append(p); t01 = p["look"] + 60
        if not answered(p["ticker"], t01): p["fill"] = "no fill data"; C["no fill data (the minute request was not answered)"] += 1; continue
        c = (minute.get(p["ticker"]) or {}).get(t01)
        if c is None: p["fill"] = "unchanged minute"; C["filled on an unchanged minute (no 07:01 candle)"] += 1
        else:
            hb, ha = (c[0] is not None and c[0] > EPS), (c[1] is not None and c[1] < 1 - EPS)
            a = (c[1] if ha else None) if p["side"] == "yes" else ((1 - c[0]) if hb else None)
            if (not hb and not ha) or a is None or a > p["limit"] + EPS: p["fill"] = "not filled"; C["not filled"] += 1; continue
            p["fill"] = "present candle"; C["filled on a present candle"] += 1
        open_bets[p["event"]].append(p["close"])
    filled = [p for p in fired if p["fill"] in ("present candle", "unchanged minute")]
    half = lambda rows, k: [r for r in rows if (r["date"] < HALF_DATE) == (k == 0)]
    out = {"build": "Forensics second build of POLGAPH", "label": FRESH, "counts": dict(C), "ambiguities": AMBIGUITIES}
    out["filled_bets"] = {"development": len(filled), "first_half": len(half(filled, 0)), "second_half": len(half(filled, 1))}
    out["distinct_among_filled"] = {("first half", "second half")[k]: {"events": len({b["event"] for b in half(filled, k)}), "series": len({b["series"] for b in half(filled, k)}), "mornings": len({b["date"] for b in half(filled, k)})} for k in (0, 1)}
    out["largest_number_open_at_once"] = max((sum(1 for o in filled if o["look"] <= b["look"] < o["close"]) for b in filled), default=0)
    med = (statistics.median(c[0] for c in cost), statistics.median(c[1] for c in cost)) if cost else (None, None)
    out["one_way_cost"] = {"market_mornings": len(cost), "median_ask_minus_mid_plus_fee_at_the_limit": med[0], "cost_as_paid_at_the_limit_information_only": med[1]}
    if med[0] is not None and med[0] > COST_LINE + EPS:
        out["verdict"] = "CLOSED on cost: median one-way cost %.4f above 0.04; no result is read" % med[0]; return out
    # ---- only now are results opened
    for b in fired: book(b, results)
    def block(rows): return {"development": stats(rows), "first_half": stats(half(rows, 0)), "second_half": stats(half(rows, 1))}
    out["filled"] = block(filled); out["filled_on_a_present_candle_only"] = block([b for b in filled if b["fill"] == "present candle"]); out["optimistic_same_candle_fill_information_only"] = block(fired)
    out["voids_among_filled"] = sum(1 for b in filled if b["win"] is None)
    out["filled_with_the_settlement_value_paid_for_voids_information_only"] = stats(filled, "net_with_settlement_value")
    base = [book(dict(b), results) for b in one_per_event(quiet)]
    out["baseline_gap_under_2c_information_only"] = block(base)
    fams = {}
    for f in spec["families"]:
        rows = [b for b in filled if b["family"] == f]; fams[f] = dict(block(rows), fired=sum(1 for b in fired if b["family"] == f), optimistic=stats([b for b in fired if b["family"] == f]))
    out["by_family"] = fams
    def read(rows, name):
        s = block(rows); n, n0, n1 = s["development"]["n"], s["first_half"]["n"], s["second_half"]["n"]
        if n < MIN_FILLED or n0 < MIN_HALF or n1 < MIN_HALF: return "no evidence at n = %d (%s; halves %d and %d)" % (n, name, n0, n1), False
        ge = lambda x, line: x is not None and x >= line - EPS
        ok = ge(s["development"]["pf"], PF_LINE) and ge(s["first_half"]["pf"], HALF_LINE) and ge(s["second_half"]["pf"], HALF_LINE)
        return ("survives development (%s): a candidate for a wheel shadow place, never a pass of the research bar" % name) if ok else ("FALSIFIED (%s)" % name), ok
    v, ok = read(filled, "pooled"); net = out["filled"]["development"]["net"]
    if ok and net > 0:
        big = [f for f, s in fams.items() if s["development"]["net"] > net / 2 + EPS]
        if big:
            v2, _ = read([b for b in filled if b["family"] == big[0]], "the family '%s' alone, which supplies more than half of the pooled net" % big[0]); v = "the pooled pass does not count; " + v2
    out["verdict"] = v
    return out


def lines(out):
    f = lambda x, d=2: "n/a" if x is None else ("inf" if x == float("inf") else ("%." + str(d) + "f") % x)
    order = ["series asked", "series with any settled market in the window", "markets", "markets with any hourly candle", "market-mornings", "no look (an hourly candle missing)",
             "not two-sided at one of the three candles", "1. three two-sided candles", "2. gap of 5c or more", "left after 3. steady", "left after 4. band", "left after 5. spread", "left after 6. liquid",
             "left after 7. one per event and morning (the event's pick)", "not the event's pick", "blocked: the event holds an earlier filled, unsettled bet", "fired", "filled on a present candle",
             "filled on an unchanged minute (no 07:01 candle)", "not filled", "no fill data (the minute request was not answered)"]
    cnt = out["counts"]; keys = order + sorted(k for k in cnt if k not in order)
    L = ["verdict: " + out["verdict"], FRESH, "COUNTS: " + "; ".join("%s %d" % (k, cnt.get(k, 0)) for k in keys),
         "filled bets: %s | distinct among filled: %s | largest number open at once: %d" % (out["filled_bets"], out["distinct_among_filled"], out["largest_number_open_at_once"]),
         "ONE-WAY COST over %d market-mornings: median %sc (kill above 4c); as paid at the limit %sc (information only)" % (out["one_way_cost"]["market_mornings"], f(None if out["one_way_cost"]["median_ask_minus_mid_plus_fee_at_the_limit"] is None else 100 * out["one_way_cost"]["median_ask_minus_mid_plus_fee_at_the_limit"]), f(None if out["one_way_cost"]["cost_as_paid_at_the_limit_information_only"] is None else 100 * out["one_way_cost"]["cost_as_paid_at_the_limit_information_only"]))]
    def row(name, b):
        return "%s: " % name + " | ".join("%s n %d wins %d voids %d PF %s mean %sc net %s z %s" % (k, s["n"], s["wins"], s["voids"], f(s["pf"]), f(None if s["mean"] is None else 100 * s["mean"]), f(s["net"]), f(s["z_event_clustered"])) for k, s in b.items() if isinstance(s, dict) and "n" in s)
    for k in ("filled", "filled_on_a_present_candle_only", "optimistic_same_candle_fill_information_only", "baseline_gap_under_2c_information_only"):
        if k in out: L.append(row(k, out[k]))
    for fam, b in (out.get("by_family") or {}).items(): L.append(row("family " + fam, {k: v for k, v in b.items() if k in ("development", "first_half", "second_half")}) + " | fired %d" % b["fired"])
    if "voids_among_filled" in out: L.append("voids among filled %d; with the settlement value paid instead (information only): PF %s net %s" % (out["voids_among_filled"], f(out["filled_with_the_settlement_value_paid_for_voids_information_only"]["pf"]), f(out["filled_with_the_settlement_value_paid_for_voids_information_only"]["net"])))
    return L


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 7 or not all(x in a for x in ("--lists", "--hourly", "--minute")): raise SystemExit(__doc__)
    i, j, k = a.index("--lists"), a.index("--hourly"), a.index("--minute")
    out = measure(json.load(open(a[0])), a[i + 1:j], a[j + 1:k], a[k + 1:])
    print("\n".join(lines(out))); print(json.dumps(out, indent=1, default=str))
