"""INPLAYJUMP tennis screen check (Desk B Amendment 6; Head approved Nov 12): run the engine BOTH WAYS on the validation matches, screened (minute candles only from the screen's start) and full (every minute from the open), per tennis family.
Any mismatch in the bet, the in-play set (from 30 minutes after the screen's start) or the placebo, or a 2c step found inside an hour the screen would have skipped, VOIDS the screen for that family. No result is read.
  python3 -I inplayjump_screencheck.py selftest
  python3 -I inplayjump_screencheck.py run <INPLAYJUMP_SERIES.json> <lists folder> <minute answers folder(s) , separated> <hourly answers folder(s) , separated> <scorekit dir>"""
import sys, os, math, hashlib, collections, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "desk_a_jobs"))
import inplayjump as J, build_inplayjump_candles as B
def hourly_from_minutes(mins):
    """{ticker: [(end_ts, bid_high, bid_low, bid_close, ask_high, ask_low, ask_close)]} from minute candle dicts {ts: c}; for the selftest."""
    out = {}
    for tk, d in mins.items():
        hrs = collections.defaultdict(list)
        for ts, c in d.items(): hrs[(ts + 3599) // 3600 * 3600].append(c)
        out[tk] = [(e, max(c["bid"] for c in cs), min(c["bid"] for c in cs), sorted(cs, key=lambda c: c["ts"])[-1]["bid"], max(c["ask"] for c in cs), min(c["ask"] for c in cs), sorted(cs, key=lambda c: c["ts"])[-1]["ask"]) for e, cs in sorted(hrs.items())]
    return out
def check_match_set(matches, K, mins, hours):
    """matches: [(event, [tickers], open_ts, close_ts)]; mins: {ticker: {ts: candle}} FULL minute candles; hours: {ticker: [hourly tuples]}. -> list of mismatch strings (empty = the screen is valid on this set)."""
    bad = []; scr = {}; starts = {}
    for e, tks, o, c in matches:
        st = B.skip_start({tk: hours.get(tk, []) for tk in tks}, tks, o, c); starts[e] = st
        scr.update({tk: ({t: x for t, x in mins.get(tk, {}).items() if st is not None and t >= st}) for tk in tks})
        if st is None: continue
        # a 2c step inside a skipped hour (the leading hours up to the start + 30 minutes)
        for tk in tks:
            d = mins.get(tk, {})
            for t, x in d.items():
                y = d.get(t - 60)
                if t <= st + 1800 and J.two_sided(x) and J.two_sided(y) and abs(J.mid(x) - J.mid(y)) >= 0.02 - 1e-9: bad.append("2c step inside a skipped hour: %s at %d" % (tk, t))
    dec = {}
    for e, tks, o, c in matches:
        d1 = J.match_decision(c, tks, mins, "alive", K, collections.Counter()); d2 = J.match_decision(c, tks, scr, "alive", K, collections.Counter())
        k = lambda d: None if d is None else (d["ticker"], d["t"], round(d["price"], 6))
        if k(d1) != k(d2): bad.append("bet differs in %s: full %s, screened %s" % (e, k(d1), k(d2)))
        dec[e] = d1
        st = starts[e]
        if st is not None:                                                    # in-play set from 30 minutes after the start, where the screened history covers the 21 minute look back
            ts = sorted({t for tk in tks for t in mins.get(tk, {}) if t >= st + 1800})
            for t in ts:
                a = any(J.alive_in_play(mins.get(tk, {}), t) for tk in tks); b = any(J.alive_in_play(scr.get(tk, {}), t) for tk in tks)
                if a != b: bad.append("in-play differs in %s at %d" % (e, t)); break
    for e, tks, o, c in matches:                                               # placebo: each real bet's elapsed minute tried on every OTHER match, both ways
        d = dec[e]
        if d is None or d["elapsed"] is None: continue
        for e2, tks2, o2, c2 in matches:
            if e2 == e: continue
            p1 = J.placebo_try(tks2, mins, "alive", K, d["elapsed"]); p2 = J.placebo_try(tks2, scr, "alive", K, d["elapsed"])
            k = lambda p: None if p is None else (p["ticker"], p["t"], round(p["price"], 6))
            if k(p1) != k(p2): bad.append("placebo differs: bet in %s, match %s: full %s, screened %s" % (e, e2, k(p1), k(p2)))
    return bad
def selftest():
    import random
    K = dict(jump=0.10, pre_jump_mid_band=[0.15, 0.75], entry_ask_band=[0.20, 0.85], entry_spread_max=0.04, slip=0.01)
    rng = random.Random(5); matches, mins = [], {}
    base = 1_800_000_000 // 3600 * 3600
    for i in range(10):
        o = base + 600; c = o + 8 * 3600; tks = ["T%d-A" % i, "T%d-B" % i]; qs = 0.5; mins[tks[0]] = {}; mins[tks[1]] = {}
        start_play = o + (4 + i % 3) * 3600                                   # quiet (flat) until play starts hours later
        for t in range(o + 60, c + 1, 60):
            if t >= start_play: qs = min(0.95, max(0.05, qs + rng.uniform(-0.04, 0.04) + (0.12 if (t - start_play) == 1500 else 0)))
            for tk, m in ((tks[0], qs), (tks[1], 1 - qs)):
                mins[tk][t] = dict(ts=t, bid=round(m - 0.01, 2), ask=round(m + 0.01, 2), volume=5.0)
        matches.append(("E%d" % i, tks, o, c))
    hours = hourly_from_minutes(mins)
    bad = check_match_set(matches, K, mins, hours); assert bad == [], bad[:5]
    nb = sum(1 for e, tks, o, c in matches if J.match_decision(c, tks, mins, "alive", K, collections.Counter()))
    assert nb >= 3, nb                                                          # the check is not vacuous: bets exist
    # a planted failure: a 2c step hiding in the first hour, which the hourly screen would skip because the hour's range is small
    mins2 = {tk: dict(d) for tk, d in mins.items()}; t1 = matches[0][2] + 1800
    mins2[matches[0][1][0]][t1] = dict(ts=t1, bid=0.52, ask=0.54, volume=5.0); mins2[matches[0][1][0]][t1 + 60] = dict(ts=t1 + 60, bid=0.49, ask=0.51, volume=5.0)
    # hourly built from a DIFFERENT (quiet) source so the screen skips the hour that really holds a 2c step
    bad2 = check_match_set(matches, K, mins2, hours); assert any("2c step inside a skipped hour" in b for b in bad2), bad2[:3]
    print("SCREENCHECK SELFTEST OK (identical bets, in-play set and placebo on 10 synthetic tennis matches; a planted 2c step in a skipped hour voids the screen)")
def run(series_path, lists, minute_dirs, hourly_dirs, scorekit_dir):
    import heldout_guard
    for d_ in [lists] + minute_dirs.split(",") + hourly_dirs.split(","): heldout_guard.refuse_heldout(d_, "screencheck")
    sys.path.insert(0, scorekit_dir); import scorekit
    S = json.load(open(series_path)); K = S["constants"]; mk = B.read_lists(lists)
    mc = scorekit.candles(minute_dirs.split(",")); hc = scorekit.candles(hourly_dirs.split(","))
    for f, items in B.families(S, mk, False):
        ev = collections.defaultdict(list)
        for t, m in items: ev[m["event"]].append(t)
        pick = sorted(ev, key=lambda e: hashlib.md5(e.encode()).hexdigest())[:10]
        mins = {t: {c["ts"]: c for c in mc.get(t, [])} for e in pick for t in ev[e]}
        hours = {t: [(c["ts"], c["bid_high"], c["bid_low"], c["bid"], c["ask_high"], c["ask_low"], c["ask"]) for c in hc.get(t, [])] for e in pick for t in ev[e]}
        matches = [(e, ev[e], min((mk[t]["open"] or mk[t]["close"] - 20 * 3600) for t in ev[e]), max(mk[t]["close"] for t in ev[e])) for e in pick]
        a = sum(1 for e, tks, o, c in matches for tk in tks for t in mins[tk] if (t + 3599) // 3600 * 3600 not in {h[0] for h in hours.get(tk, [])})
        b = sum(1 for tk, d in mins.items() for t, x in d.items() for h in hours.get(tk, []) if h[0] == (t + 3599) // 3600 * 3600 and J.two_sided(x) and (not (h[2] - 1e-9 <= x["bid"] <= h[1] + 1e-9) or not (h[5] - 1e-9 <= x["ask"] <= h[4] + 1e-9)))
        bad = check_match_set(matches, K, mins, hours)
        print("%s: %d matches; (a) minute candles in an hour with no hourly candle %d; (b) minute closes outside their hour's low to high %d; mismatches %d -> %s" % (f["family"], len(matches), a, b, len(bad), "SCREEN VALID" if not bad and a == 0 and b == 0 else "SCREEN VOID: " + "; ".join(bad[:5])))
if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["selftest"]: selftest()
    elif a[:1] == ["run"] and len(a) == 6: run(*a[1:])
    else: sys.exit(__doc__)
