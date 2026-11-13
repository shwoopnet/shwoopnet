#!/usr/bin/env python3
"""TIE3, an INDEPENDENT SECOND BUILD of the measurement (Forensics desk, 2026-11-13, on the Head of R&D's order under rule 16b), written from Desk B's registration
(claude/idea-desk-b, kalshi-scalper/workers/tie3/TIE3_REGISTRATION.md with its dated note and amendment, and TIE3_SERIES.json).
Disclosure: this desk leak-tested the Testing Desk's tie3.py on Nov 12 and scanned it for float comparisons on Nov 13, so it is not a clean-room reader.

A ZERO-TRY cost and price measurement. No rule is scored. The result field of a market closing on or after 2026-10-27T00:00:00Z (the price block) is DROPPED AT
READ TIME and never stored; a market closing on or after 2026-11-13T00:00:00Z (the held-out) is refused; any path in or resolving into a HELDOUT_ folder is refused.
Results are read for the base block only (closes before 2026-10-27), for one count: how often the period was level.

usage: python3 -I tie3_second.py <TIE3_SERIES.json> --lists <run folder ...> --candles <run folder ...>

Places where the text leaves a choice (AMBIGUITIES, printed with the output):
 1. An event's close, for the block it falls in: the close_time of its Tie market (for NHL_REG, of its single market).
 2. "Fewer than three settled markets": fewer than three markets listed for the event (one for NHL_REG), or no Tie market among them. Base block: also a Tie result that is neither yes nor no.
 3. The scheduled start: the Tie market's own occurrence_datetime minus 180 minutes. A missing or unreadable field is "start not derivable".
 4. "The game's first-period market": the event of first_period_series with the same game key (the part of the ticker between the series and the suffix); its close is the latest close_time over its markets. For soccer it is the event itself.
 5. T = start minus 30 minutes, rounded DOWN to a whole minute if the start is not on one.
 6. The share of two-sided games: two-sided over price-block games with a derivable start. The share over all price-block games is printed beside it.
 7. A price-block game whose own quarter or series has no base event has no base rate: it is counted and left out of the gap figures (it still counts as two-sided).
 8. The base rate is used unrounded. Quartiles: linear interpolation between order statistics (position (n-1) x p).
 9. History rows (the /historical endpoint) join the base block when they close before 2026-10-27; a ticker listed on both endpoints is counted once (the live row wins).
10. The cell minimum of 150 base events is on the cell's pooled base events; no minimum is set per quarter or per series.
11. Kill rule order: "nothing to buy" if under half of the price-block games (with a derivable start) are two-sided in EVERY cell with any such game; else "survives" if any measured cell has a median gap of 8c or more with a median spread of 4c or less; else "efficient, move on" with the best measured cell's median gap.
"""
import sys, os, json, gzip, math, statistics, collections
from datetime import datetime

def iso(s): return int(datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
EPS = 1e-9
OFFSET, BEFORE, STEP_BACK = 180 * 60, 30 * 60, 30
GUARD_LO, GUARD_HI = 30 * 60, 120 * 60                 # dated amendment of Nov 12 19:15Z: 30, not 20
MIN_BASE, MIN_PRICED, EDGE, SPREAD_MAX, RULE_EDGE = 150, 40, 0.08, 0.04, 0.10
FRESH = "candle freshness measured on Bitcoin 15 minute only, not on sports"
AMBIGUITIES = [l.strip() for l in __doc__.split("AMBIGUITIES, printed with the output):")[1].strip().split("\n")]


def refuse_heldout(path):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)):
            raise SystemExit("REFUSED: %s is in or resolves into a HELDOUT_ folder (standing rule (h))" % path)


def bodies(folder):
    refuse_heldout(folder)
    man = json.load(open(os.path.join(folder, "manifest.json")))
    for row in man["rows"]:
        if row.get("status") != 200 or not row.get("file"): continue
        yield row, json.load(gzip.open(os.path.join(folder, row["file"]), "rt"))


def quant(xs, p):
    xs = sorted(xs)
    if not xs: return None
    i = (len(xs) - 1) * p; a, b = math.floor(i), math.ceil(i)
    return xs[a] + (xs[b] - xs[a]) * (i - a)


def read_markets(folders, series, base_before, held_from):
    """{ticker: {series, event, key, suffix, close, occ, result or None}}. A result is stored ONLY for a market closing before base_before."""
    out = {}; C = collections.Counter()
    for f in folders:
        for row, body in bodies(f):
            if not isinstance(body, dict): continue
            hist = "historical" in str(row.get("path", ""))
            for m in body.get("markets") or []:
                if not isinstance(m, dict): continue
                t = str(m.get("ticker", "")); parts = t.split("-")
                if parts[0] not in series or len(parts) < 3: continue
                try: close = iso(m.get("close_time"))
                except Exception: C["market with no close time, dropped"] += 1; continue
                if close >= held_from: C["market refused as held-out (close on or after 2026-11-13)"] += 1; continue
                if t in out and hist: continue                                   # the live row wins
                try: occ = iso(m["occurrence_datetime"])
                except Exception: occ = None
                out[t] = {"series": parts[0], "event": m.get("event_ticker") or "-".join(parts[:-1]), "key": parts[1], "suffix": parts[-1], "close": close, "occ": occ,
                          "result": (str(m.get("result") or "").lower() if close < base_before else None)}        # the price block's result never leaves this line
    return out, C


def read_candles(folders, wanted):
    out = {}
    def px(d):
        if not isinstance(d, dict): return None
        try: return float(d.get("close_dollars"))
        except (TypeError, ValueError): return None
    for f in folders:
        for row, body in bodies(f):
            for m in (body.get("markets") or []) if isinstance(body, dict) else []:
                t = m.get("market_ticker")
                if t not in wanted: continue
                d = out.setdefault(t, {})
                for c in m.get("candlesticks") or []:
                    if isinstance(c.get("end_period_ts"), int): d[c["end_period_ts"]] = (px(c.get("yes_bid")), px(c.get("yes_ask")))
    return out


def measure(spec, list_folders, candle_folders):
    B = spec["blocks"]; base_before, price_from, price_before, held_from = iso(B["base_closes_before"]), iso(B["price_block_from"]), iso(B["price_block_before"]), iso(B["held_out_from"])
    series = {s for c in spec["cells"] for s in c["series"]} | {c["first_period_series"] for c in spec["cells"] if c["first_period_series"] != "same series"}
    mk, C0 = read_markets(list_folders, series, base_before, held_from)
    by_event = collections.defaultdict(list)
    for t, m in mk.items(): by_event[m["event"]].append((t, m))
    first_close = collections.defaultdict(int)                                   # (series, game key) -> latest close over that event's markets
    for t, m in mk.items(): first_close[(m["series"], m["key"])] = max(first_close[(m["series"], m["key"])], m["close"])
    cells = {}; wanted = set(); plan = {}
    for c in spec["cells"]:
        reg = c["cell"] == "NHL_REG"; need = 1 if reg else 3; C = collections.Counter(); base = collections.defaultdict(lambda: [0, 0]); priced = []
        for ev, ms in sorted(by_event.items()):
            if ms[0][1]["series"] not in c["series"]: continue
            tie = [(t, m) for t, m in ms if (m["suffix"] == "1" if reg else m["suffix"] == "TIE")]
            if len(ms) < need or len(tie) != 1: C["events with fewer than %d markets or no Tie market, dropped" % need] += 1; continue
            tt, tm = tie[0]
            if tm["close"] < base_before:
                if tm["result"] not in ("yes", "no"): C["base events with no yes or no Tie result, dropped"] += 1; continue
                base[tm["series"]][0] += 1; base[tm["series"]][1] += tm["result"] == "yes"; C["base events"] += 1
            elif price_from <= tm["close"] < price_before:
                C["price-block games"] += 1
                fps = tm["series"] if c["first_period_series"] == "same series" else c["first_period_series"]
                fc = first_close.get((fps, tm["key"]))
                if tm["occ"] is None or not fc: C["start not derivable: no occurrence time or no first-period market"] += 1; continue
                start = tm["occ"] - OFFSET
                if not (GUARD_LO <= fc - start <= GUARD_HI): C["start not derivable: first-period market did not close 30 to 120 minutes after the start"] += 1; continue
                C["price-block games with a derivable start"] += 1
                priced.append({"ticker": tt, "series": tm["series"], "event": ev, "T": ((start - BEFORE) // 60) * 60}); wanted.add(tt)
        cells[c["cell"]] = (C, base, priced)
    cd = read_candles(candle_folders, wanted)
    res = {}
    for name, (C, base, priced) in cells.items():
        rates = {k: {"n": v[0], "level": v[1], "rate": v[1] / v[0], "se": math.sqrt((v[1] / v[0]) * (1 - v[1] / v[0]) / v[0])} for k, v in sorted(base.items()) if v[0]}
        nb, lv = sum(v[0] for v in base.values()), sum(v[1] for v in base.values())
        gaps, spreads, fires, two, nobase, exact = [], [], 0, 0, 0, 0
        for g in priced:
            series_c = cd.get(g["ticker"], {}); got = None
            for j in range(0, STEP_BACK + 1):
                q = series_c.get(g["T"] - 60 * j)
                if q and q[0] is not None and q[1] is not None and 0 < q[0] < q[1] < 1: got = q; exact += j == 0; break
            if got is None: C["not two-sided at the instant or the 30 minutes before"] += 1; continue
            two += 1; sp = got[1] - got[0]; spreads.append(sp)
            r = rates.get(g["series"])
            if r is None: nobase += 1; continue
            gap = r["rate"] - got[1]; gaps.append(gap)
            if gap >= RULE_EDGE - EPS and sp <= SPREAD_MAX + EPS: fires += 1
        npd, npb = len(priced), C["price-block games"]
        measured = nb >= MIN_BASE and two >= MIN_PRICED
        res[name] = {"counts": dict(C), "base_events": nb, "base_rate_pooled": (lv / nb) if nb else None, "base_rate_pooled_se": math.sqrt((lv / nb) * (1 - lv / nb) / nb) if nb else None,
                     "base_rates_by_series": {k: {"n": v["n"], "rate": round(v["rate"], 4), "se": round(v["se"], 4)} for k, v in rates.items()},
                     "price_block_games": npb, "with_a_derivable_start": npd, "two_sided": two, "two_sided_from_the_exact_minute": exact,
                     "share_two_sided_of_derivable": (two / npd) if npd else None, "share_two_sided_of_all_price_block_games": (two / npb) if npb else None,
                     "two_sided_games_with_no_base_rate_for_their_series": nobase,
                     "median_spread": statistics.median(spreads) if spreads else None,
                     "gap_base_rate_minus_ask_q1_median_q3": [quant(gaps, .25), quant(gaps, .5), quant(gaps, .75)] if len(gaps) >= 2 else None,
                     "share_of_two_sided_games_with_ask_10c_under_and_spread_4c_or_less": (fires / two) if two else None, "fires": fires,
                     "status": "measured" if measured else "no evidence at n = %d base events / %d two-sided games" % (nb, two)}
    meas = {n: r for n, r in res.items() if r["status"] == "measured"}
    survive = [n for n, r in meas.items() if r["gap_base_rate_minus_ask_q1_median_q3"] and r["gap_base_rate_minus_ask_q1_median_q3"][1] >= EDGE - EPS and r["median_spread"] <= SPREAD_MAX + EPS]
    withgames = [r for r in res.values() if r["with_a_derivable_start"]]
    if withgames and all(r["share_two_sided_of_derivable"] < 0.5 - EPS for r in withgames): verdict = "CLOSED: nothing to buy (under half of the price-block games are two-sided in every cell)"
    elif survive: verdict = "SURVIVES the measurement in %d cell(s) %s: a separate registration, tries = surviving cells" % (len(survive), survive)
    elif meas:
        best = max(meas.items(), key=lambda kv: kv[1]["gap_base_rate_minus_ask_q1_median_q3"][1] if kv[1]["gap_base_rate_minus_ask_q1_median_q3"] else -9)
        verdict = "CLOSED: efficient, move on (best measured cell %s, median gap %+.1fc)" % (best[0], 100 * best[1]["gap_base_rate_minus_ask_q1_median_q3"][1])
    else: verdict = "no evidence: no cell reached 150 base events and 40 two-sided price-block games"
    return {"build": "Forensics second build of the TIE3 measurement", "tries": 0, "rule_scored": False, "price_block_results_read": 0, "label": FRESH, "reader_counts": dict(C0), "cells": res, "verdict": verdict, "ambiguities": AMBIGUITIES}


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 5 or "--lists" not in a or "--candles" not in a: raise SystemExit(__doc__)
    i, j = a.index("--lists"), a.index("--candles")
    print(json.dumps(measure(json.load(open(a[0])), a[i + 1:j], a[j + 1:]), indent=1))
