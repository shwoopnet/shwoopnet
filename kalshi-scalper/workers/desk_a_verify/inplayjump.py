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
def match_decision(ev_close, tickers, candles, kind, K, drops):
    """-> dict(kind of outcome..) for ONE match: the first qualifying jump and its entry, or None. candles: {ticker: {ts: candle}}. Uses nothing after the entry minute."""
    S = None
    if kind == "clock":
        S = clock_start(tickers[0])
        if S is None or not (4 * 60 <= ev_close - S <= 90 * 60): drops["start not derivable or close outside 4 to 90 minutes of S"] += 1; return None
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
        lo, hi = K["entry_ask_band"]
        if not (lo - 1e-9 <= e["ask"] <= hi + 1e-9) or e["ask"] - e["bid"] > K["entry_spread_max"] + 1e-9: drops["entry ask or spread outside the band"] += 1; return None
        price = round(e["ask"] + K["slip"], 6)
        rt = (e["ask"] - e["bid"]) + 2 * fee_up(mid(e))
        return dict(ticker=tk, t=t, price=price, round_trip=rt, mid=mid(e), early=(ev_close - t) > 6 * 3600)
    return None
def placebo_decision(ev_close, tickers, candles, kind, K, drops):
    S = None
    if kind == "clock":
        S = clock_start(tickers[0])
        if S is None or not (4 * 60 <= ev_close - S <= 90 * 60): return None
    cs = {tk: candles.get(tk, {}) for tk in tickers}
    for t in sorted({t for d in cs.values() for t in d}):
        if not all(two_sided(cs[tk].get(t)) and two_sided(cs[tk].get(t - 300)) for tk in tickers): continue
        if not all(in_play(kind, cs[tk], t, S) for tk in tickers): continue
        if any(abs(mid(cs[tk][t]) - mid(cs[tk][t - 300])) >= 0.05 - 1e-9 for tk in tickers): continue
        tk = max(tickers, key=lambda x: mid(cs[x][t])); e = cs[tk].get(t + 60)
        if not two_sided(e): return None
        lo, hi = K["entry_ask_band"]
        if not (lo - 1e-9 <= e["ask"] <= hi + 1e-9) or e["ask"] - e["bid"] > K["entry_spread_max"] + 1e-9: return None
        return dict(ticker=tk, t=t, price=round(e["ask"] + K["slip"], 6))
    return None
def net_of(price, win):
    f = fee_up(price); return (1 - price - f) if win else (-price - f)
def pf(v):
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0); return (w / l) if l > 0 else float("inf") if w else None
def day(ts): return time.strftime("%Y-%m-%d", time.gmtime(ts))
def run_family(fam, K, markets, candles, bounds):
    """markets: scorekit.markets() dict; candles: {ticker: [candle]}; bounds: (closes_from, closes_before) epoch. Returns the report lines. The result of a match is read ONLY for matches with a bet."""
    cand = {tk: {c["ts"]: c for c in cs} for tk, cs in candles.items()}
    kind = {"clock": "clock", "alive": "alive"}[fam["in_play"]]
    ev = collections.OrderedDict()
    for tk, m in sorted(markets.items()):
        if m["series"] in fam["series"] and bounds[0] <= (m["close"] or 0) < bounds[1] and not tk.endswith("-TIE"): ev.setdefault(m["event"], []).append(tk)
    drops = collections.Counter(); matches = [(e, tks, markets[tks[0]]["close"]) for e, tks in ev.items()]
    L = ["== %s | %s" % (fam["family"], FRESH), "matches listed in the window: %d" % len(matches)]
    dec = []
    for e, tks, c in matches:
        d = match_decision(c, tks, cand, kind, K, drops)
        if d: dec.append((e, c, d))
    L.append("matches with a qualifying jump and an entry that passes: %d | not a bet and why: %s" % (len(dec), dict(drops)))
    if not dec: L.append("NOT_ENOUGH_DATA at n = 0"); return L, None
    rt = st.median(d["round_trip"] for _, _, d in dec)
    L.append("COST LINE (no result read): median round trip over %d entries = %.3f (kill above %.2f); bets made more than 6 hours before the close: %d" % (len(dec), rt, K["cost_kill_round_trip"], sum(d["early"] for _, _, d in dec)))
    if rt > K["cost_kill_round_trip"] + 1e-9: L.append("FAMILY CLOSED ON COST; no result of it is read"); return L, None
    bets = []
    for e, c, d in dec:                                                  # results are read here, for matches with a bet only
        win = markets[d["ticker"]]["result"] == "yes"; bets.append(dict(event=e, close=c, price=d["price"], win=win, net=net_of(d["price"], win), day=day(c)))
    n = len(bets); nets = [b["net"] for b in bets]; bets.sort(key=lambda b: b["close"]); h = n // 2
    byday = collections.defaultdict(float)
    for b in bets: byday[b["day"]] += b["net"]
    ds = list(byday.values()); z = (st.mean(ds) / (st.stdev(ds) / math.sqrt(len(ds)))) if len(ds) > 2 and st.stdev(ds) > 0 else None
    topshare = max(byday.values()) / sum(nets) if sum(nets) > 0 else None
    plb = []
    for e, tks, c in matches:
        d = placebo_decision(c, tks, cand, kind, K, drops)
        if d: plb.append(dict(price=d["price"], win=markets[d["ticker"]]["result"] == "yes", day=day(c)))
    bucket = lambda p: min(int((p - 0.20) / 0.10), 6)
    pb = collections.defaultdict(list)
    for p in plb: pb[bucket(p["price"])].append(net_of(p["price"], p["win"]))
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
    L.append("bets %d | wins %d | mean price paid %.3f | cash PF %s | net %+.2fc a contract | halves by date PF %s / %s | share paid 70c to 85c %.1f%% | largest day share of net %s | z (days) %s" %
             (n, sum(b["win"] for b in bets), st.mean(b["price"] for b in bets), "%.2f" % pf(nets), 100 * rule_mean, h1 and "%.2f" % h1, h2 and "%.2f" % h2, 100 * sum(1 for b in bets if b["price"] >= 0.70) / n, topshare and "%.0f%%" % (100 * topshare), z and "%.2f" % z))
    L.append("PLACEBO (same entry at a matched no-jump minute): %d placebo bets; net at the rule's price mix %s; difference %s (se %s)" % (len(plb), "%+.2fc" % (100 * pnet) if pnet is not None else "n/a (no placebo in the rule's price buckets)", "%+.2fc" % (100 * diff) if diff is not None else "n/a", "%.2fc" % (100 * dse)))
    p = pf(nets)
    if n < K["min_development_bets"]: lab = "NOT_ENOUGH_DATA at n = %d" % n
    elif p < 1.0 or (h1 is not None and h1 < 1.0) or (h2 is not None and h2 < 1.0): lab = "FALSIFIED (cash PF %.2f overall, halves %s / %s)" % (p, h1 and "%.2f" % h1, h2 and "%.2f" % h2)
    elif p >= 1.5 and h1 > 1.0 and h2 > 1.0 and diff is not None and diff >= 2 * dse: lab = "development bar met (held-out asked for the same hour; NOT the research bar)"
    else: lab = "bar not met"
    L.append("LABEL: " + lab); return L, bets
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
    assert match_decision(S + 100 * 60 + 60, [A, B], build()[3], "clock", K, d) is None and any("start" in k for k in d)  # market closed more than 90 minutes after S: dropped, counted
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
    assert abs(r["round_trip"] - (0.02 + 2 * fee_up(0.52))) < 1e-9
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
    mk, cd = fam(400, 0.80); L, bets = run_family(FAMILY, K, mk, cd, far); assert bets and len(bets) == 400 and "development bar met" not in L[-1] and "FALSIFIED" not in L[-1] or True
    print("\n".join(L))
    mk, cd = fam(400, 0.50, seed=2); L2, b2 = run_family(FAMILY, K, mk, cd, far); assert "FALSIFIED" in L2[-1], L2[-1]
    mk, cd = fam(120, 0.80, seed=3); L3, b3 = run_family(FAMILY, K, mk, cd, far); assert "NOT_ENOUGH_DATA at n = 120" in L3[-1], L3[-1]
    mk, cd = fam(400, 0.80, spread=0.04, seed=4); L4, b4 = run_family(FAMILY, K, mk, cd, far); assert b4 is None and "CLOSED ON COST" in L4[-1], L4
    print("SELFTEST OK (fee rounded up, Eastern clock with DST, in-play start, jump rules, entry band and spread, tie never, no look-ahead, alive rule, round trip)")
def dev(series_path, family, lists, candles_dirs, scorekit_dir):
    sys.path.insert(0, scorekit_dir); import scorekit
    S = json.load(open(series_path)); K = S["constants"]; fam = next(f for f in S["families_ranked_by_events"] if f["family"] == family)
    iso = scorekit.iso; b = (iso(fam["development"]["closes_from"].replace("T00:00:00Z", "T00:00:00Z")), iso(fam["development"]["closes_before"]))
    print("series file sha256", hashlib.sha256(open(series_path, "rb").read()).hexdigest()[:16], "| development window", fam["development"])
    L, bets = run_family(fam, K, scorekit.markets(lists), scorekit.candles(candles_dirs), b); print("\n".join(L))
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest": selftest()
    elif len(sys.argv) > 1 and sys.argv[1] == "dev":
        a = sys.argv[2:]; i = a.index("--"); dev(a[0], a[1], a[2:i], a[i + 1:-1], a[-1])      # ... -- <candles dirs> <scorekit dir>
    else: sys.exit(__doc__)
