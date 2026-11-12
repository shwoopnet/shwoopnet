"""INPLAYJUMP (Desk B's registration `inplayjump/INPLAYJUMP_REGISTRATION.md` + `INPLAYJUMP_SERIES.json` on claude/idea-desk-b; built by Idea Desk A, Nov 12 2026, on the Testing Desk's scorekit).
Written and tested on SYNTHETIC candles BEFORE any real price of these series was opened. Research only: sends nothing.
  python3 -I inplayjump.py selftest [<scorekit dir>]
  python3 -I inplayjump.py dev <SERIES.json> <FAMILY> <lists dir ...> -- <candles dir ...>      one DEVELOPMENT read of one family (held-out is refused: no code path reads it)
Rule (registration, every number from the series file): in play (clock families: candle end >= S + 60 s, S read as US Eastern from the ticker key, guard close 4 to 90 min after S; tennis: at least 3 of the
20 one-minute steps ending at t-1 moved the two-sided mid 2c or more; the close time is NEVER used); jump = a contract's mid at in-play minute t is 0.10 or more above its mid at t-1, both two-sided,
volume at t above zero, mid at t-1 in 0.15 to 0.75 (the Tie never); the FIRST qualifying minute of the match; entry at the close of minute t+1: two-sided, ask 0.20 to 0.85, spread <= 0.04,
buy 1 at ask + 0.01; fee 0.07 p (1-p) rounded UP to the cent; hold. Cost kill BEFORE any result: median round trip (spread + two fees at the mid) over qualifying entries above 0.05 closes the family.
Placebo: the first in-play minute at which neither contract's mid moved 0.05 or more over the previous 5 minutes; buy the contract with the higher mid at ask + 0.01 (same band and spread) at the NEXT minute's close
(my reading, as for the rule; Desk B to confirm); grouped by price paid in 10c buckets and re-weighted to the rule's own price mix."""
import sys, os, math, json, statistics as st, collections, calendar, time, hashlib
DEV_BOUNDS = None                                   # set by dev() to the family's development window; a window outside it is refused
ONE_WAY_KILL = 0.04                                 # Head's ruling Nov 12 (hold to settlement): median one-way entry cost above 4c closes the family; Desk B writes the dated amendment
FRESH = "candle freshness measured on Bitcoin 15 minute only, not on these markets"
def two_sided(c): return c is not None and c.get("bid") is not None and c.get("ask") is not None and 0 < c["bid"] < c["ask"] < 1
def mid(c): return (c["bid"] + c["ask"]) / 2
def fee_up(p): return math.ceil(0.07 * p * (1 - p) * 100 - 1e-9) / 100.0           # rounded UP to the next whole cent
def clock_start(ticker):
    """scheduled start S (epoch s) from a ticker like KXESOCCERGAME-26NOV100722GIGIMADD-MADD: yy MON dd HHMM, US Eastern"""
    from zoneinfo import ZoneInfo
    import datetime as dt
    key = ticker.split("-")[1]
    try: d = dt.datetime.strptime(key[:11], "%y%b%d%H%M").replace(tzinfo=ZoneInfo("America/New_York"))
    except Exception: return None
    return int(d.timestamp())
def alive_in_play(by_ts, t):
    """tennis: minute t is in play if at least 3 of the 20 one-minute steps ending at t-1 moved the two-sided mid by 2c or more. Backward-looking only."""
    n = 0
    for k in range(1, 21):
        a, b = by_ts.get(t - 60 * (k + 1)), by_ts.get(t - 60 * k)
        if two_sided(a) and two_sided(b) and abs(mid(b) - mid(a)) >= 0.02 - 1e-9: n += 1
    return n >= 3
def in_play(kind, by_ts, t, S):
    return (t >= S + 60) if kind == "clock" else alive_in_play(by_ts, t)
def match_decision(ev_close, tickers, candles, kind, K, drops, costs=None):
    """-> dict(kind of outcome..) for ONE match: the first qualifying jump and its entry, or None. candles: {ticker: {ts: candle}}. Uses nothing after the entry minute."""
    S = None
    if kind == "clock":
        S = clock_start(tickers[0])
        if S is None: drops["start not derivable from the ticker"] += 1; return None      # Amendment 1: no per-match close guard; the family-level share is printed in run_family
    cs = {tk: candles.get(tk, {}) for tk in tickers}
    all_ts = sorted({t for d in cs.values() for t in d})
    for t in all_ts:
        q = []
        for tk in tickers:
            a, b = cs[tk].get(t - 60), cs[tk].get(t)
            if not (two_sided(a) and two_sided(b)) or (b.get("volume") or 0) <= 0: continue
            if not in_play(kind, cs[tk], t, S): continue
            if mid(b) - mid(a) >= K["jump"] - 1e-9 and K["pre_jump_mid_band"][0] - 1e-9 <= mid(a) <= K["pre_jump_mid_band"][1] + 1e-9: q.append(tk)
        if not q: continue
        if len(q) > 1: drops["two contracts qualified in the same minute"] += 1; return None
        tk = q[0]; e = cs[tk].get(t + 60)
        if not two_sided(e): drops["entry minute not two-sided"] += 1; return None
        if costs is not None: costs.append((e["ask"] - mid(e)) + fee_up(round(e["ask"] + K["slip"], 6)))      # one-way cost at EVERY qualifying decision with a two-sided entry minute, before the band and spread filters
        lo, hi = K["entry_ask_band"]
        if not (lo - 1e-9 <= e["ask"] <= hi + 1e-9) or e["ask"] - e["bid"] > K["entry_spread_max"] + 1e-9: drops["entry ask or spread outside the band"] += 1; return None
        price = round(e["ask"] + K["slip"], 6)
        ow = (e["ask"] - mid(e)) + fee_up(price)                          # one-way entry cost (Head's ruling, hold to settlement): ask minus mid plus the fee as charged
        return dict(ticker=tk, t=t, price=price, one_way=ow, mid=mid(e), early=(ev_close - t) > 6 * 3600, into_play=(t - S) / 60.0 if S else None)
    return None
def placebo_decision(ev_close, tickers, candles, kind, K, drops):
    S = None
    if kind == "clock":
        S = clock_start(tickers[0])
        if S is None: return None
    cs = {tk: candles.get(tk, {}) for tk in tickers}
    for t in sorted({t for d in cs.values() for t in d}):
        if not all(two_sided(cs[tk].get(t)) and two_sided(cs[tk].get(t - 300)) for tk in tickers): continue
        if not all(in_play(kind, cs[tk], t, S) for tk in tickers): continue
        if any(abs(mid(cs[tk][t]) - mid(cs[tk][t - 300])) >= 0.05 - 1e-9 for tk in tickers): continue
        tk = max(tickers, key=lambda x: mid(cs[x][t])); e = cs[tk].get(t + 60)    # Head's ruling (a): the SAME instant and price rule as the real bet: t+1, ask plus 1c, same band and spread
        if not two_sided(e): return None
        lo, hi = K["entry_ask_band"]
        if not (lo - 1e-9 <= e["ask"] <= hi + 1e-9) or e["ask"] - e["bid"] > K["entry_spread_max"] + 1e-9: return None
        return dict(ticker=tk, t=t, price=round(e["ask"] + K["slip"], 6), into_play=(t - S) / 60.0 if S else None)
    return None
def net_of(price, win):
    f = fee_up(price); return (1 - price - f) if win else (-price - f)
def pf(v):
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0); return (w / l) if l > 0 else float("inf") if w else None
def day(ts): return time.strftime("%Y-%m-%d", time.gmtime(ts))
def run_family(fam, K, markets, candles, bounds):
    """markets: scorekit.markets() dict; candles: {ticker: [candle]}; bounds: (closes_from, closes_before) epoch. Returns the report lines. The result of a match is read ONLY for matches with a bet."""
    if DEV_BOUNDS is not None and not (DEV_BOUNDS[0] <= bounds[0] and bounds[1] <= DEV_BOUNDS[1]): raise SystemExit("REFUSED: the window is not inside the development window; the held-out is read only on the Head's go (no code path reads it)")
    cand = {tk: {c["ts"]: c for c in cs} for tk, cs in candles.items()}
    kind = {"clock": "clock", "alive": "alive"}[fam["in_play"]]
    ev = collections.OrderedDict()
    for tk, m in sorted(markets.items()):
        if m["series"] in fam["series"] and bounds[0] <= (m["close"] or 0) < bounds[1] and not tk.endswith("-TIE"): ev.setdefault(m["event"], []).append(tk)
    drops = collections.Counter(); matches = [(e, tks, markets[tks[0]]["close"]) for e, tks in ev.items()]
    L = ["== %s | %s" % (fam["family"], FRESH), "matches listed in the window: %d" % len(matches)]
    if kind == "clock" and matches:                                                    # Amendment 1: the share is printed once per family; under 80% the start is not derivable and nothing of it is read
        ok = sum(1 for _, tks, c in matches if clock_start(tks[0]) is not None and 4 * 60 <= c - clock_start(tks[0]) <= 90 * 60); share = ok / len(matches)
        L.append("start check: %.1f%% of matches closed 4 to 90 minutes after the ticker's start (%d of %d)" % (100 * share, ok, len(matches)))
        if share < 0.80: L.append("START NOT DERIVABLE for this family; no result of it is read"); return L, None
    dec = []; costs = []
    for e, tks, c in matches:
        d = match_decision(c, tks, cand, kind, K, drops, costs)
        if d: dec.append((e, c, d))
    L.append("matches with a qualifying jump and an entry that passes: %d | not a bet and why: %s" % (len(dec), dict(drops)))
    if not costs: L.append("NOT_ENOUGH_DATA at n = 0"); return L, None
    ow = st.median(costs)
    L.append("COST LINE (no result read): median ONE-WAY entry cost (ask minus mid plus the fee as charged) over %d qualifying decisions = %.3f (kill above %.2f); bets made more than 6 hours before the close: %d; median minutes into play of the bet: %s" % (len(costs), ow, ONE_WAY_KILL, sum(d["early"] for _, _, d in dec), "%.1f" % st.median(d["into_play"] for _, _, d in dec) if (kind == "clock" and dec) else "n/a"))
    if ow > ONE_WAY_KILL + 1e-9: L.append("FAMILY CLOSED ON COST; no result of it is read"); return L, None
    if not dec: L.append("NOT_ENOUGH_DATA at n = 0"); return L, None
    bets = []; voids = 0
    for e, c, d in dec:                                                  # results are read here, for matches with a bet only
        r = markets[d["ticker"]]["result"]
        if r == "void": voids += 1; continue                       # Head's ruling (b): refund, net 0, NOT in n, PF or z, both arms; the count is printed beside n
        if r not in ("yes", "no"): bets.append(dict(event=e, close=c, price=d["price"], win=False, net=-fee_up(d["price"]), day=day(c), nores=True)); continue   # fired bet with no result that is not a void: fee-only loss, counted
        win = r == "yes"; bets.append(dict(event=e, close=c, price=d["price"], win=win, net=net_of(d["price"], win), day=day(c)))
    L.append("voided bets (refunded, excluded from n, PF and z): %d | bets with no result that are not voids (fee-only loss, counted): %d" % (voids, sum(1 for b in bets if b.get("nores"))))
    if not bets: L.append("NOT_ENOUGH_DATA at n = 0"); return L, None
    n = len(bets); nets = [b["net"] for b in bets]; bets.sort(key=lambda b: b["close"]); h = n // 2
    byday = collections.defaultdict(float)
    for b in bets: byday[b["day"]] += b["net"]
    ds = list(byday.values()); z = (st.mean(ds) / (st.stdev(ds) / math.sqrt(len(ds)))) if len(ds) > 2 and st.stdev(ds) > 0 else None
    zm = (st.mean(nets) / (st.stdev(nets) / math.sqrt(n))) if n > 2 and st.stdev(nets) > 0 else None
    zmin = min(x for x in (z, zm) if x is not None) if (z is not None or zm is not None) else None
    topshare = max(byday.values()) / sum(nets) if sum(nets) > 0 else None
    plb = []
    for e, tks, c in matches:
        d = placebo_decision(c, tks, cand, kind, K, drops)
        if d: plb.append(dict(price=d["price"], win=markets[d["ticker"]]["result"] == "yes", void=markets[d["ticker"]]["result"] == "void", into_play=d["into_play"], day=day(c)))
    bucket = lambda p: min(int((p - 0.20) / 0.10), 6)
    pb = collections.defaultdict(list)
    for p in plb:
        if not p["void"]: pb[bucket(p["price"])].append(net_of(p["price"], p["win"]))
    mix = collections.Counter(bucket(b["price"]) for b in bets); wsum = 0.0; pnet = 0.0; var = 0.0
    for bkt, cnt in mix.items():
        v = pb.get(bkt)
        if not v: continue
        w = cnt / n; wsum += w; pnet += w * st.mean(v); var += (w ** 2) * (st.variance(v) / len(v) if len(v) > 1 else 0)
    pnet = pnet / wsum if wsum else None
    se = math.sqrt(var) / wsum if wsum else None
    rule_mean = st.mean(nets); rse = st.stdev(nets) / math.sqrt(n) if n > 1 else 0
    diff = (rule_mean - pnet) if pnet is not None else None; dse = math.sqrt(rse ** 2 + (se or 0) ** 2)
    h1, h2 = pf(nets[:0] or [b["net"] for b in bets[:h]]), pf([b["net"] for b in bets[h:]])
    L.append("bets %d | wins %d | mean price paid %.3f | cash PF %s | net %+.2fc a contract | halves by date PF %s / %s | share paid 70c to 85c %.1f%% | largest day share of net %s | z (days) %s | z (matches, one bet each) %s | the smaller is used: %s" %
             (n, sum(b["win"] for b in bets), st.mean(b["price"] for b in bets), "%.2f" % pf(nets), 100 * rule_mean, h1 and "%.2f" % h1, h2 and "%.2f" % h2, 100 * sum(1 for b in bets if b["price"] >= 0.70) / n, topshare and "%.0f%%" % (100 * topshare), z and "%.2f" % z, zm and "%.2f" % zm, zmin and "%.2f" % zmin))
    L.append("PLACEBO (registered: first quiet in-play minute, the higher-mid contract): %d placebo bets; median minutes into play %s (rule %s); net at the rule's price mix %s; difference %s (se %s)" % (len(plb), ("%.1f" % st.median(p["into_play"] for p in plb)) if plb and kind == "clock" else "n/a", ("%.1f" % st.median(d["into_play"] for _, _, d in dec)) if kind == "clock" else "n/a", "%+.2fc" % (100 * pnet) if pnet is not None else "n/a (no placebo in the rule's price buckets)", "%+.2fc" % (100 * diff) if diff is not None else "n/a", "%.2fc" % (100 * dse)))
    p = pf(nets)
    if n < K["min_development_bets"]: lab = "NOT_ENOUGH_DATA at n = %d" % n
    elif p < 1.0 or (h1 is not None and h1 < 1.0) or (h2 is not None and h2 < 1.0): lab = "FALSIFIED (cash PF %.2f overall, halves %s / %s)" % (p, h1 and "%.2f" % h1, h2 and "%.2f" % h2)
    elif p >= 1.5 and h1 > 1.0 and h2 > 1.0 and diff is not None and diff >= 2 * dse: lab = "development bar met (held-out asked for the same hour; NOT the research bar)"
    else: lab = "bar not met"
    L.append("LABEL: " + lab); return L, bets
def pilot(fam, K, markets, candles, bounds):
    """Head-approved pilot: cost and tradeability only. markets' results are NEVER touched (a market with a 'result' key is read for event and close only)."""
    cand = {tk: {c["ts"]: c for c in cs} for tk, cs in candles.items()}; kind = fam["in_play"]
    ev = collections.OrderedDict()
    for tk, m in sorted(markets.items()):
        if m["series"] in fam["series"] and bounds[0] <= (m["close"] or 0) < bounds[1] and not tk.endswith("-TIE"): ev.setdefault(m["event"], []).append(tk)
    drops = collections.Counter(); costs = []; ok = 0; nm = 0
    for e, tks in ev.items():
        nm += 1; before = len(costs); d = match_decision(markets[tks[0]]["close"], tks, cand, kind, K, drops, costs); ok += 1 if d else 0
    return ["PILOT %s | %s | matches %d | qualifying decisions with a two-sided entry minute %d | of them passing ask band and spread <= 4c %d (%.0f%%) | median one-way cost %s | not a bet and why: %s | NO result read" % (fam["family"], FRESH, nm, len(costs), ok, 100 * ok / len(costs) if costs else 0, "%.3f" % st.median(costs) if costs else "n/a", dict(drops))]
# ---------------------------------------------------------------- synthetic tests
def synth_event(i, S, jump_at=None, rng=None, tie=False, edge=0.0, size=0.12, start_mid=0.5):
    import random
    rng = rng or random.Random(i); key = "26NOV10%04d" % 722 if False else None
    pass
def selftest():
    K = dict(jump=0.10, pre_jump_mid_band=[0.15, 0.75], entry_ask_band=[0.20, 0.85], entry_spread_max=0.04, slip=0.01, cost_kill_round_trip=0.05, min_development_bets=300)
    d = collections.Counter()
    assert fee_up(0.50) == 0.02 and fee_up(0.10) == 0.01 and fee_up(0.93) == 0.01 and fee_up(0.25) == 0.02, (fee_up(0.5), fee_up(0.1), fee_up(0.93), fee_up(0.25))
    # clock start: 26NOV100722 is 07:22 Eastern on Nov 10 2026 = 12:22Z (EST); 26OCT100722 is EDT = 11:22Z
    assert clock_start("KXESOCCERGAME-26NOV100722GIGIMADD-MADD") == calendar.timegm(time.strptime("2026-11-10 12:22", "%Y-%m-%d %H:%M"))
    assert clock_start("KXESOCCERGAME-26OCT100722GIGIMADD-MADD") == calendar.timegm(time.strptime("2026-10-10 11:22", "%Y-%m-%d %H:%M"))
    S = clock_start("KXESOCCERGAME-26OCT100722AAABBB-AAA"); close = S + 30 * 60
    def build(jumper_mid_before=0.40, jump=0.12, vol=20.0, tie_jumps=False, entry_spread=0.02, entry_mid_shift=0.0):
        A, B = "KXESOCCERGAME-26OCT100722AAABBB-AAA", "KXESOCCERGAME-26OCT100722AAABBB-BBB"; T = "KXESOCCERGAME-26OCT100722AAABBB-TIE"; c = {A: {}, B: {}, T: {}}
        for k in range(0, 30):
            t = S + 60 * k; a = jumper_mid_before + (jump if k >= 10 else 0.0) + (entry_mid_shift if k >= 11 else 0.0)
            c[A][t] = dict(ts=t, bid=round(a - 0.01, 4), ask=round(a + 0.01, 4), volume=vol if k == 10 else 3.0)
            c[B][t] = dict(ts=t, bid=round(1 - a - 0.01, 4), ask=round(1 - a + 0.01, 4), volume=3.0)
            c[T][t] = dict(ts=t, bid=0.05, ask=0.07, volume=(500.0 if tie_jumps and k == 10 else 1.0))
        if entry_spread != 0.02:
            e = c[A][S + 660]; e["bid"] = round(e["ask"] - entry_spread, 4)
        return A, B, T, c
    A, B, T, c = build(); r = match_decision(close, [A, B], c, "clock", K, d)
    assert r and r["ticker"] == A and r["t"] == S + 600 and abs(r["price"] - (0.53 + 0.01)) < 1e-9, r                  # ask at t+1 is 0.53, plus 1c slip
    assert match_decision(close, [A, B], build(vol=0.0)[3], "clock", K, d) is None                                    # no volume: no jump
    assert match_decision(close, [A, B], build(jumper_mid_before=0.80, jump=0.10)[3], "clock", K, d) is None          # mid before outside 0.15 to 0.75
    assert match_decision(close, [A, B], build(jump=0.09)[3], "clock", K, d) is None                                   # jump under 0.10
    assert match_decision(close, [A, B], build(entry_spread=0.06)[3], "clock", K, d) is None                           # entry spread above 0.04
    assert match_decision(S + 100 * 60 + 60, [A, B], build()[3], "clock", K, d) is not None       # Amendment 1: a late close no longer drops a match; the close is never used
    # before S + 60 s the minute is not in play: a jump at k = 0 or 1 does not count
    A2, B2, T2, c2 = build(); 
    for tk in (A2, B2): pass
    c3 = {A: {}, B: {}}
    for k in range(-1, 30):                       # the jump lands at minute S (k = 0): the candle ends at S, before S + 60 s, so it is not in play
        t = S + 60 * k; a = 0.40 + (0.12 if k >= 0 else 0.0)
        c3[A][t] = dict(ts=t, bid=round(a - .01, 4), ask=round(a + .01, 4), volume=50.0 if k == 0 else 3.0); c3[B][t] = dict(ts=t, bid=round(1 - a - .01, 4), ask=round(1 - a + .01, 4), volume=3.0)
    assert match_decision(close, [A, B], c3, "clock", K, collections.Counter()) is None, "a jump at the minute ending at S must not count"
    c4 = {A: {}, B: {}}
    for k in range(0, 30):                        # the jump lands at S + 60 s (k = 1): the candle ends at S + 60 s, which is in play
        t = S + 60 * k; a = 0.40 + (0.12 if k >= 1 else 0.0)
        c4[A][t] = dict(ts=t, bid=round(a - .01, 4), ask=round(a + .01, 4), volume=50.0 if k == 1 else 3.0); c4[B][t] = dict(ts=t, bid=round(1 - a - .01, 4), ask=round(1 - a + .01, 4), volume=3.0)
    assert match_decision(close, [A, B], c4, "clock", K, collections.Counter())["t"] == S + 60
    # the Tie contract is never the jumper (it is not passed in) ; a tie jump changes nothing
    assert match_decision(close, [A, B], build(tie_jumps=True)[3], "clock", K, collections.Counter())["ticker"] == A
    # NO LOOK-AHEAD: changing every candle after the entry minute, and the close time inside the window, changes nothing
    A, B, T, c = build(); base = match_decision(close, [A, B], c, "clock", K, collections.Counter())
    c9 = {tk: {t: (dict(x, bid=0.01, ask=0.03, volume=999.0) if t > S + 660 else x) for t, x in d_.items()} for tk, d_ in c.items()}
    r9 = match_decision(close + 600, [A, B], c9, "clock", K, collections.Counter())
    assert (r9["ticker"], r9["t"], r9["price"]) == (base["ticker"], base["t"], base["price"]), (r9, base)
    # tennis alive rule: backward-looking only; it ignores the close
    tc = {"X": {}}; 
    for k in range(0, 60):
        t = 100000 + 60 * k; m = 0.50 + (0.03 if (k % 4 == 0 and k < 30) else 0.0) * (1 if k % 8 else -1)
        tc["X"][t] = dict(ts=t, bid=round(m - .01, 4), ask=round(m + .01, 4), volume=5.0)
    assert alive_in_play(tc["X"], 100000 + 60 * 25) is True and alive_in_play(tc["X"], 100000 + 60 * 5) is False
    # round trip and cost kill
    assert abs(r["one_way"] - (0.01 + fee_up(0.54))) < 1e-9, r["one_way"]
    # family level: a synthetic family where the jumper wins 80% (an edge) and one where it wins 50%; the cost kill; NOT_ENOUGH_DATA below 300 bets
    import random
    def fam(n, win_p, spread=0.01, seed=1):
        rng = random.Random(seed); mk, cd = {}, {}
        for i in range(n):
            keyd = "26OCT%02d0722" % (10 + i // 40); S0 = clock_start("KXESOCCERGAME-%sAAABBB-AAA" % keyd); cl = S0 + 30 * 60
            ev = "KXESOCCERGAME-%sAAABBB%d" % (keyd, i); A, B = ev + "-AAA", ev + "-BBB"
            rA = "yes" if rng.random() < win_p else "no"
            for tk, res in ((A, rA), (B, "no" if rA == "yes" else "yes")): mk[tk] = dict(ticker=tk, event=ev, series="KXESOCCERGAME", close=cl, result=res)
            cd[A], cd[B] = [], []
            for k in range(0, 30):
                t = S0 + 60 * k; a = 0.40 + (0.12 if k >= 10 else 0.0)
                cd[A].append(dict(ts=t, bid=round(a - spread / 2, 4), ask=round(a + spread / 2, 4), volume=20.0 if k == 10 else 3.0)); cd[B].append(dict(ts=t, bid=round(1 - a - spread / 2, 4), ask=round(1 - a + spread / 2, 4), volume=3.0))
        return mk, cd
    FAMILY = dict(family="ESOCCER", series=["KXESOCCERGAME"], in_play="clock")
    far = (0, 10 ** 12)
    mk, cd = fam(400, 0.80); L, bets = run_family(FAMILY, K, mk, cd, far); assert bets and len(bets) == 400
    print("\n".join(L))
    mk, cd = fam(400, 0.50, seed=2); L2, b2 = run_family(FAMILY, K, mk, cd, far); assert "FALSIFIED" in L2[-1], L2[-1]
    mk, cd = fam(120, 0.80, seed=3); L3, b3 = run_family(FAMILY, K, mk, cd, far); assert "NOT_ENOUGH_DATA at n = 120" in L3[-1], L3[-1]
    mk, cd = fam(400, 0.80, spread=0.06, seed=4); L4, b4 = run_family(FAMILY, K, mk, cd, far); assert b4 is None and "CLOSED ON COST" in L4[-1], L4     # entry spread 6c: one-way 5c > 4c, killed before any result
    mk, cd = fam(200, 0.80, seed=5)
    for tk in list(mk)[:40]: mk[tk]["result"] = "void"
    L5, b5 = run_family(FAMILY, K, mk, cd, far); assert any("voided bets (refunded, excluded from n, PF and z): 20" in x for x in L5) and len(b5) == 180, L5
    mk, cd = fam(100, 0.80, seed=6)
    for tk, m in mk.items(): m["close"] += 3 * 3600                                      # every close 3 h after its start: start not derivable
    L6, b6 = run_family(FAMILY, K, mk, cd, far); assert b6 is None and "START NOT DERIVABLE" in L6[-1], L6
    global DEV_BOUNDS
    DEV_BOUNDS = (0, 100)
    try: run_family(FAMILY, K, *fam(10, 0.5), (0, 200)); raise AssertionError("held-out window not refused")
    except SystemExit as ex: assert "REFUSED" in str(ex)
    DEV_BOUNDS = None
    # the pilot never reads a result: strip them and it still runs
    mk, cd = fam(60, 0.8, seed=7)
    for m in mk.values(): m.pop("result")
    P = pilot(FAMILY, K, mk, cd, far); assert "NO result read" in P[0] and "median one-way cost 0.0" in P[0], P
    # placebo is the registered one: a quiet in-play minute, the higher-mid contract, priced at that minute
    _S = clock_start("KXESOCCERGAME-26OCT100722AAABBB-AAA"); _A, _B = "KXESOCCERGAME-26OCT100722AAABBB-AAA", "KXESOCCERGAME-26OCT100722AAABBB-BBB"; pc = {_A: {}, _B: {}}
    for k in range(0, 12):
        t = _S + 60 * k
        for tk, m in ((_A, 0.60), (_B, 0.40)): pc[tk][t] = dict(ts=t, bid=round(m - .01, 4), ask=round(m + .01, 4), volume=3.0)
    pd = placebo_decision(_S + 1800, [_A, _B], pc, "clock", K, collections.Counter()); assert pd and pd["ticker"] == _A and pd["t"] == _S + 300 and abs(pd["price"] - 0.62) < 1e-9, pd
    print("SELFTEST OK (fee rounded up, Eastern clock with DST, in-play start, jump rules, entry band and spread, tie never, no look-ahead, alive rule, round trip)")
def dev(series_path, family, lists, candles_dirs, scorekit_dir):
    sys.path.insert(0, scorekit_dir); import scorekit
    S = json.load(open(series_path)); K = S["constants"]; fam = next(f for f in S["families_ranked_by_events"] if f["family"] == family)
    iso = scorekit.iso; b = (iso(fam["development"]["closes_from"].replace("T00:00:00Z", "T00:00:00Z")), iso(fam["development"]["closes_before"]))
    print("series file sha256", hashlib.sha256(open(series_path, "rb").read()).hexdigest()[:16], "| development window", fam["development"])
    global DEV_BOUNDS; DEV_BOUNDS = b
    L, bets = run_family(fam, K, scorekit.markets(lists), scorekit.candles(candles_dirs), b); print("\n".join(L))
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest": selftest()
    elif len(sys.argv) > 1 and sys.argv[1] == "dev":
        a = sys.argv[2:]; i = a.index("--"); dev(a[0], a[1], a[2:i], a[i + 1:-1], a[-1])      # ... -- <candles dirs> <scorekit dir>
    else: sys.exit(__doc__)
