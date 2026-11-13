#!/usr/bin/env python3
"""INPLAYJUMP independent second scorer (Testing Desk, Nov 13, 2026), built from INPLAYJUMP_REGISTRATION.md (Amendments 1 to 6, claude/idea-desk-b 14f439cf), INPLAYJUMP_SERIES.json (sha256 34f70868...) and Desk A's float clarification text ONLY; inplayjump.py was NOT read.
Research only: reads files, sends nothing. No result is joined before the full read; the pilot report prints counts, validation and cost only. Refuses HELDOUT_ paths (scorekit.guard) and any market closing on or after its family's held-out start (counted).
Candle timestamps are the END of the minute. All comparisons carry a tolerance of 1e-9 (3e-9 on the tennis screen sum), in the direction the registration states.
Readings of the text where it leaves a choice are in AMBIGUITIES."""
import calendar, hashlib, json, math, os, statistics as st, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

NY = ZoneInfo("America/New_York")
MONTHS = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
TOL = 1e-9
SERIES_SHA256 = "34f708687df24f5a6243c710eb2d1f6b8d7559c965b8c18a97e27248c2ed06e8"
JUMP, PRE_LO, PRE_HI, ASK_LO, ASK_HI, SPREAD_MAX, SLIP = 0.10, 0.15, 0.75, 0.20, 0.85, 0.04, 0.01
AMBIGUITIES = [
    "1. first_in_play for tennis = the first minute at which the alive rule holds for EITHER contract; every minute is in play only if the alive rule holds AT THAT MINUTE (not 'from the first on'). Clock families: in play from the minute ending at S + 60 s.",
    "2. Elapsed minute e: clock = (t - S) / 60 with t the jump minute's END ts; tennis = (t - first in-play minute) / 60. The placebo's own minute is S_Y + 60 e (clock) or first_in_play_Y + 60 e (tennis).",
    "3. Placebo search: the NEXT matches after X in (start or open, ticker) order, no wrap-around, up to 20; a match is 'used' only when a placebo BET is made; ANY failed condition, including the entry price band or spread at e + 1, sends the search on to the next match.",
    "4. Two contracts qualifying in the same minute = no bet, counted (the first minute at which anything qualifies is the decision minute, no second chance).",
    "5. The mid before the jump is minute t - 1's two-sided mid; the entry reads minute t + 1's close (the minute ending 120 s after t - 60... i.e. end ts t + 60). Both minutes must be present and two-sided; volume above zero is tested on minute t only.",
    "6. Cost line (Desk A clarification Nov 13): the KILL reads the median over EVERY qualifying decision with a two-sided entry minute (before the band and spread filters); the median over the entries passing them is printed as information.",
    "7. A result that is not 'yes' or 'no' (void, missing) = price refunded, fee kept, a fee-only loss, counted in n, PF and z, count printed (rule and placebo alike).",
    "8. Halves (Desk A clarification Nov 13): bets sorted by (market close time, event ticker); first half = the first n // 2 bets, the rest = the second. Day for the day-z and the largest-day share = the UTC date of the market's CLOSE (a label, not a decision input).",
    "9. The placebo is re-weighted to the rule's price mix by price buckets min((round(p*100) - 20) // 10, 6); a bucket the rule uses but the placebo has no bet in is dropped and the remaining weights renormalised, and the dropped share is printed. The difference's standard error combines the rule's per-bet variance and the weighted bucket variances of the placebo.",
    "10. z by days: clusters = the UTC date of the market close; z by match: one bet a match, so each bet is a cluster; the smaller of the two is used.",
    "11. Tennis screen and validation lines are implemented as functions (screen_skip_hours, validation_counts) and are exercised on synthetic data; they run on landed hourly and minute files only after the full pilot data lands.",
]


def load_series(path=None):
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "inplayjump_series_frozen.json")
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != SERIES_SHA256: raise SystemExit("refused: the series file does not match the frozen sha256")
    return json.loads(raw)


def ts_of(s): return calendar.timegm(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").timetuple())
def fee_up(p): return math.ceil(round(0.07 * p * (1 - p) * 100, 6)) / 100


def start_ts(event):
    key = event.split("-", 1)[1] if "-" in event else ""
    try: return int(datetime(2000 + int(key[0:2]), MONTHS[key[2:5]], int(key[5:7]), int(key[7:9]), int(key[9:11]), tzinfo=NY).timestamp())
    except (KeyError, ValueError, IndexError): return None


def two(c):
    return c is not None and c.get("bid") is not None and c.get("ask") is not None and 0 < c["bid"] < c["ask"] < 1


def mid(c): return (c["bid"] + c["ask"]) / 2


def bucket(p): return min((round(p * 100) - 20) // 10, 6)


# ---------- matches ----------
def build_matches(spec, list_folders):
    """-> (matches, counts). A match: dict(family, event, sort (S or open), S (clock) or None, open, close, codes {code: ticker}, results {code: result})."""
    raw = k.markets(list_folders); fam_of = {s: f for f in spec["families_ranked_by_events"] for s in f["series"]}
    by = {}
    for t, m in raw.items():
        if m["series"] in fam_of: by.setdefault(m["event"], []).append(m)
    out, c = [], {"events_listed": len(by), "held_out_refused": 0, "outside_development_window": 0, "not_two_team_contracts": 0, "no_clock_in_ticker_clock_family": 0, "market_with_no_close_time": 0}
    for e, ms in sorted(by.items()):
        fam = fam_of[ms[0]["series"]]; teams = [m for m in ms if not m["ticker"].endswith("-TIE")]
        if len(teams) != 2 or len({m["ticker"].rsplit("-", 1)[-1] for m in teams}) != 2: c["not_two_team_contracts"] += 1; continue
        closes = [m["close"] for m in teams]
        if any(x is None for x in closes): c["market_with_no_close_time"] += 1; continue
        close = max(closes); dev, ho = fam["development"], fam["held_out"]
        if close >= ts_of(ho["closes_from"]): c["held_out_refused"] += 1; continue
        if not (ts_of(dev["closes_from"]) <= close < ts_of(dev["closes_before"])): c["outside_development_window"] += 1; continue
        S = start_ts(e) if fam["in_play"] == "clock" else None
        if fam["in_play"] == "clock" and S is None: c["no_clock_in_ticker_clock_family"] += 1; continue
        opens = [m["open"] for m in teams if m["open"] is not None]
        out.append({"family": fam["family"], "kind": fam["in_play"], "event": e, "S": S, "open": min(opens) if opens else None, "close": close,
                    "sort": S if S is not None else (min(opens) if opens else 0), "codes": {m["ticker"].rsplit("-", 1)[-1]: m["ticker"] for m in teams}, "results": {m["ticker"].rsplit("-", 1)[-1]: m["result"] for m in teams}})
    return out, c


def start_check(matches):
    """Family-level check (Amendment 1): the share of development matches whose market closed 4 to 90 minutes after S; under 80% the family is 'start not derivable'."""
    r = {}
    for m in matches:
        if m["kind"] != "clock": continue
        a = r.setdefault(m["family"], [0, 0]); a[0] += 1; a[1] += 1 if 4 * 60 - TOL <= m["close"] - m["S"] <= 90 * 60 + TOL else 0
    return {f: {"matches": n, "closed_4_to_90_after_S": g, "share": round(g / n, 4), "start_derivable": g * 100 >= 80 * n} for f, (n, g) in r.items()}


# ---------- the engine on minute data ----------
def series_of(idx, m): return {c: idx.get(t, {}) for c, t in m["codes"].items()}


def jump_at(ser, t, vol_ok=True):
    """-> codes of the contracts that make a qualifying jump at minute t (END ts): mid(t) - mid(t-60) >= 0.10, both minutes two-sided, volume at t above zero, mid(t-60) in [0.15, 0.75]."""
    q = []
    for c, d in ser.items():
        a, b = d.get(t - 60), d.get(t)
        if not (two(a) and two(b)): continue
        if not ((b.get("volume") or 0) > 0): continue
        m0 = mid(a)
        if mid(b) - m0 >= JUMP - TOL and PRE_LO - TOL <= m0 <= PRE_HI + TOL: q.append(c)
    return q


def alive(ser, t):
    """Tennis: at least 3 of the 20 one-minute steps ending at t - 1 moved the mid 2c or more; both minutes of a step present and two-sided; strict reading (Amendment 5 point 4). Either contract."""
    for c, d in ser.items():
        n = 0
        for tau in range(t - 20 * 60, t, 60):                       # steps (tau - 60 -> tau) with tau = t-1200 .. t-60 (the 20 steps ending at minute t - 1)
            a, b = d.get(tau - 60), d.get(tau)
            if two(a) and two(b) and abs(mid(b) - mid(a)) >= 0.02 - TOL: n += 1
        if n >= 3: return True
    return False


def minutes_of(ser): return sorted({t for d in ser.values() for t in d})


def in_play(m, ser, t):
    return t >= m["S"] + 60 if m["kind"] == "clock" else alive(ser, t)


def first_in_play(m, ser):
    if m["kind"] == "clock": return m["S"] + 60
    for t in minutes_of(ser):
        if alive(ser, t): return t
    return None


def decide(m, idx):
    """-> dict(status, ...). status: 'bet' (entry passes), 'no_jump', 'two_contracts_same_minute', 'entry_minute_not_two_sided', 'entry_outside_band', plus the decision fields. No result touched."""
    ser = series_of(idx, m)
    if not any(ser.values()): return {"status": "no_candles"}
    fip = first_in_play(m, ser)
    if fip is None: return {"status": "never_in_play"}
    for t in minutes_of(ser):
        if t < fip or not in_play(m, ser, t): continue
        q = jump_at(ser, t)
        if not q: continue
        if len(q) > 1: return {"status": "two_contracts_same_minute", "t": t}
        c = q[0]; e = ser[c].get(t + 60)
        d = {"t": t, "code": c, "fip": fip, "elapsed": (t - (m["S"] if m["kind"] == "clock" else fip)) // 60}
        if not two(e): return dict(d, status="entry_minute_not_two_sided")
        d.update(entry_ask=e["ask"], entry_bid=e["bid"], entry_mid=mid(e), price=round(e["ask"] + SLIP, 4))
        d["cost_one_way"] = (e["ask"] - mid(e)) + fee_up(d["price"])
        if not (ASK_LO - TOL <= e["ask"] <= ASK_HI + TOL and e["ask"] - e["bid"] <= SPREAD_MAX + TOL): return dict(d, status="entry_outside_band")
        return dict(d, status="bet")
    return {"status": "no_jump"}


def placebo_for(bet_match, bet, matches_sorted, pos, idx, used):
    """Amendment 2 point 3 (+5, 6): the NEXT match of the family after X (by sort key then ticker) not yet served, at the same elapsed minute e; up to 20 matches; no wrap-around. -> (placebo dict or None, reason)."""
    e = bet["elapsed"]; tried = 0
    for j in range(pos + 1, len(matches_sorted)):
        y = matches_sorted[j]
        if y["family"] != bet_match["family"]: continue
        if y["event"] in used: continue
        tried += 1
        if tried > 20: break
        ser = series_of(idx, y); fip = first_in_play(y, ser)
        if fip is None: continue
        tY = (y["S"] if y["kind"] == "clock" else fip) + 60 * e
        if not any(tY in d for d in ser.values()) or not in_play(y, ser, tY): continue
        if any(two(d.get(tY)) is False for d in ser.values()): continue
        if any(jump_at(ser, tt) for tt in minutes_of(ser) if fip <= tt <= tY and in_play(y, ser, tt)): continue          # a qualifying jump at or before it
        quiet = True
        for c, d in ser.items():
            mids = [mid(d[tau]) for tau in range(tY - 5 * 60, tY + 60, 60) if tau in d and two(d[tau])]
            if not two(d.get(tY)) or not mids or max(mids) - min(mids) >= 0.05 - TOL: quiet = False
        if not quiet: continue
        best = max(ser, key=lambda c: mid(ser[c][tY]))
        ent = ser[best].get(tY + 60)
        if not two(ent) or not (ASK_LO - TOL <= ent["ask"] <= ASK_HI + TOL and ent["ask"] - ent["bid"] <= SPREAD_MAX + TOL): continue
        return {"event": y["event"], "code": best, "t": tY, "price": round(ent["ask"] + SLIP, 4)}, "ok"
    return None, "no_placebo_within_20"


def net_of(price, code, results):
    f = fee_up(price); r = results.get(code)
    if r not in ("yes", "no"): return -f, True
    return ((1 - price - f) if r == "yes" else (-price - f)), False


def family_run(fam_matches, idx, read_results=False):
    """Step 1 counts for one family (no result read unless read_results). Returns (report, decisions, placebo plan)."""
    ms = sorted(fam_matches, key=lambda m: (m["sort"], m["event"])); dec = {}; why = {}
    for m in ms:
        d = decide(m, idx); dec[m["event"]] = d; why[d["status"]] = why.get(d["status"], 0) + 1
    qual = [d for d in dec.values() if d["status"] in ("bet", "entry_outside_band")]
    bets = [d for d in dec.values() if d["status"] == "bet"]
    costs_all = [d["cost_one_way"] for d in qual]; costs_bet = [d["cost_one_way"] for d in bets]
    medc = lambda xs: None if not xs else round(st.median(xs), 4)
    rep = {"matches": len(ms), "status_counts": why, "qualifying_decisions_with_a_two_sided_entry_minute": len(qual), "passing_ask_band_and_spread": len(bets),
           "share_passing": None if not qual else round(len(bets) / len(qual), 4), "median_one_way_cost_all_qualifying": medc(costs_all), "median_one_way_cost_entries": medc(costs_bet),
           "cost_over_4c": None if not costs_all else st.median(costs_all) > 0.04 + TOL, "cost_kill_reads": "the median over EVERY qualifying decision with a two-sided entry minute (Desk A clarification Nov 13); the entries-only median is information"}
    return rep, dec, ms


def score_family(fam_matches, idx, dev_from, dev_to):
    """The full read for one family (results joined HERE and only for bets and placebo bets). Returns the printed lines."""
    rep, dec, ms = family_run(fam_matches, idx); by_ev = {m["event"]: m for m in ms}; used = set(); rule, plc, noplc = [], [], 0
    for pos, m in enumerate(ms):
        d = dec[m["event"]]
        if d["status"] != "bet": continue
        net, void = net_of(d["price"], d["code"], m["results"])
        rule.append({"event": m["event"], "price": d["price"], "net": net, "void": void, "win": net > 0, "t": d["t"], "elapsed": d["elapsed"], "ts": d["t"], "close": m["close"], "day": m["close"] // 86400})
        p, why = placebo_for(m, d, ms, pos, idx, used)
        if p is None: noplc += 1; continue
        used.add(p["event"]); pm = by_ev[p["event"]]; pn, pv = net_of(p["price"], p["code"], pm["results"]); plc.append({"price": p["price"], "net": pn, "void": pv, "elapsed": d["elapsed"], "t": p["t"]})
    out = dict(rep, bets=len(rule), voids=sum(r["void"] for r in rule), placebo_bets=len(plc), bets_with_no_placebo=noplc)
    if not rule: out["verdict"] = "NOT_ENOUGH_DATA at n = 0"; return out
    rule.sort(key=lambda r: (r["close"], r["event"]))                                              # Desk A clarification Nov 13: bets sorted by (market close time, event ticker); first half = the first n // 2 bets
    nets = [r["net"] for r in rule]; pf = k.pf(nets); h1 = nets[:len(nets) // 2]; h2 = nets[len(nets) // 2:]
    out.update(wins=sum(r["win"] for r in rule), mean_price=round(sum(r["price"] for r in rule) / len(rule), 4), cash_pf=pf, net_cents_per_contract=round(100 * sum(nets) / len(nets), 3),
               halves_pf=[k.pf(h1) if h1 else None, k.pf(h2) if h2 else None], share_paid_70_to_85=round(sum(1 for r in rule if r["price"] >= 0.70 - TOL) / len(rule), 4))
    byday = {}
    for r in rule: byday[r["day"]] = byday.get(r["day"], 0) + r["net"]
    tot = sum(byday.values()); out["largest_day_share_of_net"] = None if tot <= 0 else round(max(byday.values()) / tot, 3)
    zd = k.cluster_z([dict(r, event=r["event"], cluster=str(r["day"])) for r in rule]); zm = k.cluster_z([dict(r, cluster=r["event"]) for r in rule])
    zs = [x["z"] for x in (zd, zm) if x["z"] is not None]; out["z_by_days"], out["z_by_match"], out["z_smaller_used"] = zd, zm, (min(zs) if len(zs) == 2 else None)
    # placebo at the rule's price mix
    wr = {}
    for r in rule: wr[bucket(r["price"])] = wr.get(bucket(r["price"]), 0) + 1
    pb = {}
    for p in plc: pb.setdefault(bucket(p["price"]), []).append(p["net"])
    use = {b: w for b, w in wr.items() if b in pb}; wsum = sum(use.values())
    if wsum:
        pnet = sum((w / wsum) * (sum(pb[b]) / len(pb[b])) for b, w in use.items()); rnet = sum(nets) / len(nets)
        var_p = sum(((w / wsum) ** 2) * (st.pvariance(pb[b]) / len(pb[b]) if len(pb[b]) > 1 else 0.0) for b, w in use.items()); var_r = st.pvariance(nets) / len(nets) if len(nets) > 1 else 0.0
        out.update(placebo_net_cents_at_rule_mix=round(100 * pnet, 3), difference_cents=round(100 * (rnet - pnet), 3), difference_se_cents=round(100 * math.sqrt(var_p + var_r), 3), rule_bets_in_buckets_with_no_placebo=sum(w for b, w in wr.items() if b not in pb))
    out["median_elapsed_minute_rule"] = st.median(r["elapsed"] for r in rule); out["median_elapsed_minute_placebo"] = st.median(p["elapsed"] for p in plc) if plc else None
    n = len(rule); fals = n >= 300 and ((pf is not None and pf < 1.0 - TOL) or any(h is not None and h < 1.0 - TOL for h in out["halves_pf"]))
    met = n >= 300 and pf is not None and pf >= 1.5 - TOL and all(h is not None and h > 1.0 + TOL for h in out["halves_pf"]) and "difference_cents" in out and out["difference_cents"] >= 2 * out["difference_se_cents"] - TOL
    out["verdict"] = ("NOT_ENOUGH_DATA at n = %d" % n) if n < 300 else ("FALSIFIED" if fals else ("development bar met" if met else "bar not met"))
    out["label"] = "selected on development (cost line, start check); candle freshness measured on Bitcoin 15 minute only, not on these markets"
    return out


# ---------- tennis screen (Amendment 5 / 6) ----------
def screen_skip_hours(hourly, codes):
    """hourly: {code: {hour_end_ts: candle with bid_open/bid_high/bid_low/bid/ask_open/ask_high/ask_low/ask}}. -> set of hour end ts that may be skipped: no hourly candle = dead hour = skipped; otherwise skipped iff for EVERY contract bid range + ask range < 0.04 - 3e-9, the range taken over {high, low, open, last present close before H}."""
    hours = sorted({h for d in hourly.values() for h in d}); first, last = hours[0], hours[-1]
    skip = set()
    for h in range(first, last + 1, 3600):
        if not any(h in d for d in hourly.values()): skip.add(h); continue
        ok = True
        for c, d in hourly.items():
            x = d.get(h)
            if x is None: continue                                                           # this contract has no candle in the hour: it contributes nothing
            prev = [d[p] for p in sorted(d) if p < h]
            lc = prev[-1] if prev else None
            def rng(open_, hi, lo, close_key):
                vals = [v for v in (open_, hi, lo) if v is not None]
                if lc is not None and lc.get(close_key) is not None: vals.append(lc[close_key])
                return (max(vals) - min(vals)) if vals else None
            rb = rng(x.get("bid_open"), x.get("bid_high"), x.get("bid_low"), "bid"); ra = rng(x.get("ask_open"), x.get("ask_high"), x.get("ask_low"), "ask")
            if rb is None or ra is None or rb + ra >= 0.04 - 3e-9: ok = False
        if ok: skip.add(h)
    return skip


def validation_counts(minute_idx, hourly_idx, codes):
    """Self-checks per tennis family: (a) minute candles in an hour with no hourly candle; (b) minute closes whose bid or ask is outside that hour's own low to high."""
    a = b = 0
    for c, t in codes.items():
        hr = hourly_idx.get(t, {})
        for ts, cd in minute_idx.get(t, {}).items():
            h = -(-ts // 3600) * 3600
            if h not in hr: a += 1; continue
            x = hr[h]
            if cd.get("bid") is not None and x.get("bid_low") is not None and not (x["bid_low"] - TOL <= cd["bid"] <= x["bid_high"] + TOL): b += 1
            elif cd.get("ask") is not None and x.get("ask_low") is not None and not (x["ask_low"] - TOL <= cd["ask"] <= x["ask_high"] + TOL): b += 1
    return {"minute_candles_in_an_hour_with_no_hourly_candle": a, "minute_closes_outside_their_hour_low_to_high": b}


def pilot(list_folders, candle_folders):
    """The PILOT REPORT (counts, start check, cost; NO result read): per family, over the matches that have any candle in the pulled files."""
    spec = load_series(); ms, counts = build_matches(spec, list_folders)
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candle_folders).items()}
    have = [m for m in ms if any(t in idx for t in m["codes"].values())]
    out = {"counts_first": counts, "matches_with_candles": len(have), "start_check": start_check(have), "families": {}}
    for fam in sorted({m["family"] for m in have}):
        sub = [m for m in have if m["family"] == fam]; rep, _d, _s = family_run(sub, idx); out["families"][fam] = rep
    out["label"] = "selected on development; candle freshness measured on Bitcoin 15 minute only, not on these markets; NO result read"
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "pilot" and "--candles" in a:
        i = a.index("--candles"); print(json.dumps(pilot(a[1:i], a[i + 1:]), indent=1, default=str))
    else: print(__doc__); print("\n".join(AMBIGUITIES))
