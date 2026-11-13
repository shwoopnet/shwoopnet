#!/usr/bin/env python3
"""VOIDSNAP stage 1, an INDEPENDENT SECOND BUILD (Forensics desk, 2026-11-13, on the Head of R&D's order). Written from Desk B's card with Amendments 1 and 2
(claude/idea-desk-b at a0cdeebe, kalshi-scalper/workers/voidsnap/VOIDSNAP_CARD.md, sha256 da37859d...) ALONE. Desk B's voidsnap.py was not read.
A zero-try HINDSIGHT MEASUREMENT, not a rule: the sample is chosen by the void result, so every figure is an upper bound.

usage: python3 -I voidsnap_second.py sample  --lists <lists run> [--compare <VOIDSNAP_SAMPLE.json>]
       python3 -I voidsnap_second.py measure --lists <lists run> --candles <candle run ...>
  a run is a kalshi-pull answer folder (manifest.json + NNNN.json.gz). ONLY the answers to request id live_KXCS2GAME are opened in the lists run: the hist_ answers
  are a held-out set and are never opened. Any path in or resolving into a HELDOUT_ folder is refused.

Places where the text leaves a choice (READINGS, printed with the output):
 a. Window edges (rule 6): a candle is inside an event's window if its end time is at or after S minus 185 minutes and at or before the earlier of the event's close and S plus 480 minutes (both edges count). Candles a batched request returned outside the event's own window are not seen.
 b. A minute after the window's end (rule 7), for example S when the market closed before S: the quote is still the last candle inside the window, under the carry in force. Nothing in rule 7 stops it; the detectors have their own "closed" test, question 1 has none.
 c. A quote (rule 7) needs a bid above 0.00 and an ask under 1.00, both present. A candle with a bid of 0.00 and an ask under 1.00, or an ask of 1.00 and a bid above 0.00, is "one side missing".
 d. The carries: registered = the last candle at or before the minute inside the window, whatever its age; 60 minute = the same if it ended 60 minutes or less before the minute (exactly 60 counts); none = only a candle ending exactly at the minute.
 e. Question 2's minutes are every whole minute from S minus 185 to the window's end, both counted. Each contract is a side; a side's ask, bid and spread are that contract's own YES quotes, and its settlement value is its own listed value.
 f. Printed for question 2: the first minute of the first run of 5 or more, per void the earliest over its two sides, summarised as lowest, median, highest in minutes against S; the median shortfall and the one-way cost are taken over every buyable (void, side, minute); the fee is 7% x p x (1 - p) at p = ask plus 1c, rounded up to the cent.
 g. Line 1's information count with the band: five consecutive minutes at or after the detector's minute in which the same side is buyable AND its ask is 15c to 64c.
 h. "Closed at or before that minute" (detectors) uses the event's close, the later of its two contracts' close times.
 i. D1: a present candle of the first-named contract ending after S and at or before S plus 60 that is not a quote (empty book or one side missing) fails D1. Only candles inside the window are looked at.
 j. D2's volume is the candles' volume_fp, summed over both contracts, candles inside the window ending after S and at or before S plus 60; an event with no such candle has volume 0 and is flagged unless closed.
 k. The implied share with no flagged event at all is "n/a" and line 2 fails.
 l. Line 1 counts a void only if the detector flags it under the same carry as the run.
 m. Line 3's best reference is chosen under each carry on its own.
 n. Drops (rule 2 and 3) are tested in this order: not two contracts, no close time, no ticker clock, outside the window, neither void nor played.
 o. A void contract with no listed settlement value is never buyable and is a miss in question 1 (counted).
 p. Rule 4's distance is the absolute difference of the two start times in seconds.
 q. When two references tie for line 3's best, the earlier one (S minus 180, then S minus 60, then S) is named; the share is the same either way.
 r. "At least 40" (line 1) is a whole count; "70% or more" and "30% or more" are tested on the share with the 1e-9 tolerance.
"""
import sys, os, json, gzip, re, bisect, statistics, collections
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
def iso(s): return int(datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
WINDOW = ("2026-09-12T00:00:00Z", "2026-10-22T23:59:59Z"); W0, W1 = iso(WINDOW[0]), iso(WINDOW[1])
LIST_ID = "live_KXCS2GAME"; SERIES = "KXCS2GAME"
EPS = 1e-9; MIN = 60; BACK, FWD = 185 * MIN, 480 * MIN
CARRIES = (("registered carry", None), ("60 minute carry", 60 * MIN), ("no carry", 0))
DETECTORS = (("D1", 60 * MIN, ("S-180", "S-60", "S")), ("D2", 60 * MIN, ("S-180", "S-60", "S")), ("D3", 0, ("S-180", "S-60")))
REF_AT = {"S-180": -180 * MIN, "S-60": -60 * MIN, "S": 0}
TAG = " [hindsight sample: events chosen by their void result; an upper bound, not a live rule]"
READINGS = [l.strip() for l in __doc__.split("READINGS, printed with the output):")[1].strip().split("\n")]


def refuse_heldout(path):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)):
            raise SystemExit("REFUSED: %s is in or resolves into a HELDOUT_ folder (standing rule (h))" % path)


def answers(folder, only_id=None):
    refuse_heldout(folder)
    man = json.load(open(os.path.join(folder, "manifest.json")))
    for row in man["rows"]:
        if only_id is not None and row.get("id") != only_id: continue          # the hist_ answers are never opened
        if row.get("status") != 200 or not row.get("file"): continue
        refuse_heldout(os.path.join(folder, row["file"]))
        yield row, json.load(gzip.open(os.path.join(folder, row["file"]), "rt"))


def num(v):
    try:
        x = float(v)
        return x if x == x else None
    except (TypeError, ValueError): return None


def start_of(event):
    m = re.match(r"^(\d{2})([A-Z]{3})(\d{2})(\d{2})(\d{2})", event.split("-", 1)[1] if "-" in event else "")
    if not m or m.group(2) not in MON: return None
    try: return int(datetime(2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3)), int(m.group(4)), int(m.group(5)), tzinfo=NY).timestamp())
    except ValueError: return None


def sample(list_folders):
    """rules 1 to 4 -> (sample dict in Desk B's file shape, settlement values {ticker: value})"""
    ev = collections.defaultdict(dict)
    for f in list_folders:
        for row, body in answers(f, LIST_ID):
            for m in (body.get("markets") or []) if isinstance(body, dict) else []:
                t = str(m.get("ticker", ""))
                if t.split("-")[0] != SERIES: continue
                ev[m.get("event_ticker") or t.rsplit("-", 1)[0]][t] = m
    drops = collections.OrderedDict((k, 0) for k in ("not_two_contracts", "no_close_time", "no_ticker_clock", "outside_window", "neither_void_nor_played"))
    voids, played, settle = [], [], {}
    for e, ms in sorted(ev.items()):
        if len(ms) != 2: drops["not_two_contracts"] += 1; continue
        try: closes = {t: iso(m["close_time"]) for t, m in ms.items()}
        except Exception: drops["no_close_time"] += 1; continue
        S = start_of(e)
        if S is None: drops["no_ticker_clock"] += 1; continue
        close = max(closes.values())
        if not (W0 <= close <= W1): drops["outside_window"] += 1; continue
        res = sorted(str(m.get("result") or "").lower() for m in ms.values())
        rec = {"event": e, "tickers": sorted(ms), "S": S, "close": close}
        if res == ["no", "yes"]: played.append(rec)
        elif "yes" not in res and "no" not in res: voids.append(rec)
        else: drops["neither_void_nor_played"] += 1; continue
        for t, m in ms.items(): settle[t] = num(m.get("settlement_value_dollars"))
    voids.sort(key=lambda r: (r["S"], r["event"])); free = sorted(played, key=lambda r: (r["S"], r["event"])); pairs = []
    for v in voids:
        if not free: raise SystemExit("REFUSED: fewer played events than voids; the sample cannot be matched")
        p = min(free, key=lambda r: (abs(r["S"] - v["S"]), r["S"], r["event"])); free.remove(p); pairs.append({"void": v, "played": p})
    for pr in pairs:
        for r in pr.values():
            if not (W0 <= r["close"] <= W1): raise SystemExit("REFUSED: the sample holds an event closing outside the window: " + r["event"])
    return {"window": list(WINDOW), "base": {"void": len(voids), "played": len(played)}, "drops": dict(drops), "pairs": pairs}, settle


def read_candles(folders, wanted):
    out = {t: {} for t in wanted}; other = set()
    for f in folders:
        for row, body in answers(f):
            for m in (body.get("markets") or []) if isinstance(body, dict) else []:
                t = m.get("market_ticker")
                if t not in out: other.add(t); continue
                for c in m.get("candlesticks") or []:
                    ts = c.get("end_period_ts")
                    if not isinstance(ts, int): continue
                    px = lambda d: num(d.get("close_dollars")) if isinstance(d, dict) else None
                    out[t][ts] = (px(c.get("yes_bid")), px(c.get("yes_ask")), num(c.get("volume_fp")) or 0.0)
    return out, len(other)


def is_quote(b, a): return b is not None and a is not None and b > EPS and a < 1 - EPS
def fee_up(p):
    import math
    return math.ceil(0.07 * p * (1 - p) * 100 - EPS) / 100.0


def has_run(flags, n=5):
    k = 0
    for f in flags:
        k = k + 1 if f else 0
        if k >= n: return True
    return False


def runs(flags):
    out = []; k = 0
    for i, f in enumerate(list(flags) + [False]):
        if f: k += 1
        else:
            if k: out.append((i - k, k))
            k = 0
    return out


def analyse(ev, settle, candles, carry, void):
    S = ev["S"]; ws = S - BACK; we = min(ev["close"], S + FWD); windowed = ev["close"] > ws
    rows = {t: (sorted((ts,) + v for ts, v in candles.get(t, {}).items() if ws <= ts <= we) if windowed else []) for t in ev["tickers"]}
    keys = {t: [r[0] for r in rows[t]] for t in rows}
    def q(t, m):
        i = bisect.bisect_right(keys[t], m) - 1
        if i < 0: return None
        ts, b, a, _ = rows[t][i]
        if carry is not None and m - ts > carry: return None
        return (b, a) if is_quote(b, a) else None
    def mid(t, m):
        x = q(t, m); return None if x is None else (x[0] + x[1]) / 2
    first = ev["tickers"][0]; closed = lambda m: ev["close"] <= m
    out = {"windowed": windowed, "candles": sum(len(r) for r in rows.values())}
    m0 = mid(first, S)
    out["D1"] = (not closed(S + 60 * MIN)) and m0 is not None and all(is_quote(b, a) and abs((b + a) / 2 - m0) <= 0.02 + EPS for ts, b, a, _ in rows[first] if S < ts <= S + 60 * MIN)
    out["D2"] = (not closed(S + 60 * MIN)) and sum(v for t in rows for ts, _, _, v in rows[t] if S < ts <= S + 60 * MIN) < 10 - EPS
    out["D3"] = (not closed(S)) and any(mid(t, S) is not None and mid(t, S - 180 * MIN) is not None and mid(t, S - 180 * MIN) - mid(t, S) >= 0.10 - EPS for t in ev["tickers"])
    if not void: return out
    v = settle.get(first); out["refs"] = {k: mid(first, S + d) for k, d in REF_AT.items()}
    out["refs"]["last two-sided"] = next(((b + a) / 2 for ts, b, a, _ in reversed(rows[first]) if is_quote(b, a)), None)
    out["near"] = {k: (None if (m is None or v is None) else abs(m - v)) for k, m in out["refs"].items()}
    minutes = list(range(ws, we + 1, MIN)) if windowed else []
    buy, band, short, cost = {}, {}, [], []
    for t in ev["tickers"]:
        sv = settle.get(t); buy[t] = []; band[t] = []
        for m in minutes:
            x = q(t, m); ok = inb = False
            if x is not None and sv is not None:
                b, a = x; ok = (a - b <= 0.04 + EPS) and (sv - a >= 0.10 - EPS)
                if ok: short.append(sv - a); cost.append((a - (a + b) / 2) + fee_up(a + 0.01)); inb = 0.15 - EPS <= a <= 0.64 + EPS
            buy[t].append(ok); band[t].append(ok and inb)
    r5 = [minutes[i] for t in buy for i, k in runs(buy[t]) if k >= 5]
    out["buyable_minutes"] = len(short); out["short"] = short; out["cost"] = cost
    out["run5"] = bool(r5); out["first_run_minute_vs_S"] = ((min(r5) - S) // MIN) if r5 else None
    out["longest_run"] = max((k for t in buy for _, k in runs(buy[t])), default=0)
    for name, at, _ in DETECTORS:
        idx = [i for i, m in enumerate(minutes) if m >= S + at]
        out["run5_from_" + name] = any(has_run([buy[t][i] for i in idx]) for t in buy)
        out["run5_band_from_" + name] = any(has_run([band[t][i] for i in idx]) for t in buy)
    return out


def measure(list_folders, candle_folders):
    smp, settle = sample(list_folders)
    voids = [p["void"] for p in smp["pairs"]]; played = [p["played"] for p in smp["pairs"]]
    wanted = {t for e in voids + played for t in e["tickers"]}
    candles, others = read_candles(candle_folders, wanted)
    nv, n_all = len(voids), smp["base"]["void"] + smp["base"]["played"]; b = smp["base"]["void"] / n_all if n_all else None
    med = lambda xs: statistics.median(xs) if xs else None
    out = {"build": "Forensics second build of VOIDSNAP stage 1", "label": "hindsight measurement, not a rule", "window": smp["window"], "base": smp["base"], "drops": smp["drops"],
           "base_rate": b, "sampled_voids": nv, "sampled_played": len(played), "void_contracts_with_no_settlement_value": sum(1 for e in voids for t in e["tickers"] if settle.get(t) is None),
           "voids_both_sides_at_50c": sum(1 for e in voids if all(settle.get(t) is not None and abs(settle[t] - 0.5) <= EPS for t in e["tickers"])),
           "events_with_no_window": {"voids": sum(1 for e in voids if e["close"] <= e["S"] - BACK), "played": sum(1 for e in played if e["close"] <= e["S"] - BACK)},
           "sampled_tickers_with_no_candle": sum(1 for t in wanted if not candles[t]), "candle_tickers_not_in_the_sample_ignored": others, "readings": READINGS, "carries": {}}
    state = {}
    for cname, carry in CARRIES:
        V = [analyse(e, settle, candles, carry, True) for e in voids]; P = [analyse(e, settle, candles, carry, False) for e in played]
        c = {"question_1": {k: {"voids_with_it": sum(1 for a in V if a["refs"][k] is not None), "within_1c": sum(1 for a in V if a["near"][k] is not None and a["near"][k] <= 0.01 + EPS),
                                "within_3c": sum(1 for a in V if a["near"][k] is not None and a["near"][k] <= 0.03 + EPS)} for k in ("S-180", "S-60", "S", "last two-sided")}}
        firsts = sorted(a["first_run_minute_vs_S"] for a in V if a["run5"]); short = [x for a in V for x in a["short"]]; cost = [x for a in V for x in a["cost"]]
        c["question_2"] = {"voids_with_any_buyable_minute": sum(1 for a in V if a["buyable_minutes"]), "buyable_side_minutes": len(short), "voids_with_a_run_of_5_or_more": len(firsts),
                           "first_run_minute_vs_S": {"lowest": firsts[0] if firsts else None, "median": med(firsts), "highest": firsts[-1] if firsts else None},
                           "longest_run_minutes_information_only": max((a["longest_run"] for a in V), default=0), "median_shortfall": med(short), "one_way_cost_median": med(cost)}
        c["detectors"] = {}
        for name, at, refs in DETECTORS:
            fv, fp = sum(1 for a in V if a[name]), sum(1 for a in P if a[name])
            rv, rp = (fv / nv if nv else 0.0), (fp / len(played) if played else 0.0)
            den = rv * b + rp * (1 - b) if b is not None else 0.0; share = (rv * b / den) if den > 0 else None
            l1 = sum(1 for a in V if a[name] and a["run5_from_" + name]); l1b = sum(1 for a in V if a[name] and a["run5_band_from_" + name])
            best = max(refs, key=lambda k: (c["question_1"][k]["within_3c"], -refs.index(k))); s3 = c["question_1"][best]["within_3c"] / nv if nv else 0.0
            d = {"voids_flagged": fv, "played_flagged": fp, "implied_share_of_voids": share, "line_1_count": l1, "line_1_count_with_ask_15c_to_64c_information_only": l1b,
                 "line_1": l1 >= 40, "line_2": share is not None and share >= 0.30 - EPS, "line_3_best_reference": best, "line_3_best_of": len(refs), "line_3_share": s3, "line_3": s3 >= 0.70 - EPS}
            d["all_three"] = d["line_1"] and d["line_2"] and d["line_3"]; d["failed"] = [k for k in ("line_1", "line_2", "line_3") if not d[k]]
            c["detectors"][name] = d; state.setdefault(name, []).append(d["all_three"])
        out["carries"][cname] = c
    out["detector_reading"] = {n: ("worth a rule" if all(s) else ("fails" if not any(s) else "mixed")) for n, s in state.items()}
    r = out["detector_reading"].values()
    out["verdict"] = "worth a rule" if "worth a rule" in r else ("depends on the carry: not decided" if "mixed" in r else "CLOSED, no try spent")
    out["carries_disagree"] = any(len(set(s)) > 1 for s in state.values())
    return out


def lines(out):
    f = lambda x, d=1: "n/a" if x is None else ("%." + str(d) + "f") % x
    pc = lambda x: "n/a" if x is None else "%.1f%%" % (100 * x)
    L = ["VOIDSNAP stage 1, second build: hindsight measurement, not a rule",
         "sample: %d voids and %d matched played events; base %d voids of %d events (%s); drops %s; no window: %s; sampled tickers with no candle %d" % (
             out["sampled_voids"], out["sampled_played"], out["base"]["void"], out["base"]["void"] + out["base"]["played"], pc(out["base_rate"]), out["drops"], out["events_with_no_window"], out["sampled_tickers_with_no_candle"])]
    for cname, c in out["carries"].items():
        L.append("[%s] QUESTION 1 (first-named contract's mid against its settlement value): " % cname + "; ".join("%s: %d have it, %d within 1c, %d within 3c" % (k, v["voids_with_it"], v["within_1c"], v["within_3c"]) for k, v in c["question_1"].items()))
        q2 = c["question_2"]; fr = q2["first_run_minute_vs_S"]
        L.append("[%s] QUESTION 2: voids with a run of 5 minutes or more %d (any buyable minute %d; buyable side-minutes %d); first run against S: lowest %s, median %s, highest %s minutes; median shortfall %sc; one-way cost %sc" % (
            cname, q2["voids_with_a_run_of_5_or_more"], q2["voids_with_any_buyable_minute"], q2["buyable_side_minutes"], f(fr["lowest"], 0), f(fr["median"]), f(fr["highest"], 0),
            f(None if q2["median_shortfall"] is None else 100 * q2["median_shortfall"]), f(None if q2["one_way_cost_median"] is None else 100 * q2["one_way_cost_median"])))
        for n, d in c["detectors"].items():
            L.append("[%s] %s: voids flagged %d of %d, played flagged %d of %d, implied share of voids %s | line 1: %d voids (needs 40; with the ask 15c to 64c: %d) %s | line 2 (30%% or more) %s | line 3: %s within 3c of the mid at %s, the best of %d (70%% or more) %s | %s" % (
                cname, n, d["voids_flagged"], out["sampled_voids"], d["played_flagged"], out["sampled_played"], pc(d["implied_share_of_voids"]), d["line_1_count"], d["line_1_count_with_ask_15c_to_64c_information_only"],
                "PASS" if d["line_1"] else "FAIL", "PASS" if d["line_2"] else "FAIL", pc(d["line_3_share"]), d["line_3_best_reference"], d["line_3_best_of"], "PASS" if d["line_3"] else "FAIL",
                "all three pass" if d["all_three"] else "failed: " + ", ".join(d["failed"])))
    L.append("detectors across the three carries: " + "; ".join("%s %s" % kv for kv in out["detector_reading"].items()))
    L.append("VERDICT: " + out["verdict"])
    L.append("the three carries %s on a detector's reading" % ("DISAGREE" if out["carries_disagree"] else "agree"))
    return [l + TAG for l in L]


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3 or a[0] not in ("sample", "measure") or "--lists" not in a: raise SystemExit(__doc__)
    i = a.index("--lists"); stop = min([a.index(x) for x in ("--candles", "--compare") if x in a] + [len(a)]); lists = a[i + 1:stop]
    if a[0] == "sample":
        smp, _ = sample(lists)
        print("sample: %d voids, %d played, drops %s, pairs %d" % (smp["base"]["void"], smp["base"]["played"], smp["drops"], len(smp["pairs"])))
        if "--compare" in a:
            theirs = json.load(open(a[a.index("--compare") + 1]))
            if theirs == smp: print("SAME as the compared sample file: window, base, drops and all %d pairs in order" % len(smp["pairs"]))
            else:
                for k in ("window", "base", "drops"):
                    if theirs.get(k) != smp[k]: print("DIFFERENT %s: theirs %s, mine %s" % (k, theirs.get(k), smp[k]))
                for n, (x, y) in enumerate(zip(theirs.get("pairs", []), smp["pairs"])):
                    if x != y: print("first different pair, number %d: theirs %s | mine %s" % (n + 1, json.dumps(x), json.dumps(y))); break
                print("pairs: theirs %d, mine %d" % (len(theirs.get("pairs", [])), len(smp["pairs"])))
        else: print(json.dumps(smp))
    else:
        if "--candles" not in a: raise SystemExit(__doc__)
        out = measure(lists, a[a.index("--candles") + 1:])
        print("\n".join(lines(out))); print(json.dumps(out, indent=1))
