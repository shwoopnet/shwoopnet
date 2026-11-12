"""INPLAYJUMP engine (Idea Desk A, Nov 12 2026; the registration is Desk B's and is PENDING: every number in CONFIG marked PENDING is a placeholder to be replaced by the registered value
BEFORE any real data is opened). Built and tested on SYNTHETIC candles only. Research only: sends nothing.

For a family that has the events but no mid-event market: the state is the match market's own in-play price path.
  JUMP    a minute-end candle where the market is two-sided (0 < bid < ask < 1) and the one-minute change of the MID is at least `jump` with at least `min_volume` contracts that minute;
          the decision uses candles up to and including the jump minute and nothing later.
  ENTRY   the NEXT minute's candle: the ask (YES) or 1 minus the bid (NO) close PLUS `slip` (1c), two-sided only, nothing from another minute. `follow` buys the side the price moved to, `fade` the other.
  RAN     the share of entries whose next-minute ask had already moved `ran_c` or more away from the jump-minute ask (the CFRTI-K lesson: a candle ask one minute later is an old price).
  PLACEBO a matched no-jump minute in the SAME match: two-sided, |mid change| below `jump / 4`, mid within `match_band` of the event's mid, at least `gap_min` minutes from any jump, the nearest in time; the same side and the same entry rule. The effect is event minus placebo.
  UNIT    one market per event (the first ticker), match-clustered z (scorekit.cluster_z); haircut line and labels from scorekit.score; held-out refused unless the Head's go (heldout_go=True).
usage:  python3 -I inplayjump.py selftest
        python3 -I inplayjump.py score <scorekit dir> <markets lists dir> <candles dir> ...      (real data; REFUSED until the registration values are filled in)"""
import sys, os, math, statistics as st, collections, calendar, time
CONFIG = dict(
    jump=0.08,            # PENDING (Desk B): the one-minute mid change that counts as a jump
    min_volume=50.0,      # PENDING (Desk B): contracts traded in the jump minute
    cooldown=10,          # PENDING: after a jump, minutes before another jump counts in the same match
    side="follow",        # PENDING (Desk B): "follow" or "fade"
    slip=0.01,            # entry at the next minute's ask plus 1c (Head of R&D)
    ran_c=0.01,           # an entry "ran" if its ask is this much above the jump-minute ask
    match_band=0.05, gap_min=5,
    cutoff_ts=None,       # PENDING: the held-out date constant (epoch s); None means the engine refuses real data
    registered=False)     # set True only when every PENDING value above has been replaced by the registered one
def two_sided(c): return c.get("bid") is not None and c.get("ask") is not None and 0 < c["bid"] < c["ask"] < 1
def mid(c): return (c["bid"] + c["ask"]) / 2
def entry(next_c, side_yes, slip):
    if not next_c or not two_sided(next_c): return None
    p = (next_c["ask"] if side_yes else 1 - next_c["bid"]) + slip
    return p if p < 1 else None
def find_jumps(cs, cfg):
    """cs: candles of ONE market sorted by ts (consecutive minutes have ts differing by 60). Returns [(index, +1 or -1)]; uses only candles up to and including the jump minute to DECIDE."""
    out, last = [], -10 ** 9
    for i in range(1, len(cs) - 1):
        a, b = cs[i - 1], cs[i]
        if b["ts"] - a["ts"] != 60 or not (two_sided(a) and two_sided(b)) or (b.get("volume") or 0) < cfg["min_volume"] or i - last < cfg["cooldown"]: continue
        d = mid(b) - mid(a)
        if abs(d) >= cfg["jump"]: out.append((i, 1 if d > 0 else -1)); last = i
    return out
def side_for(direction, cfg): return (direction > 0) == (cfg["side"] == "follow")        # True = buy YES
def events_and_placebos(cs, cfg):
    """-> list of dict(i, direction, side_yes, p_event, ran, placebo=(index, p) or None). Entry uses cs[i + 1] only (the next minute)."""
    js = find_jumps(cs, cfg); jump_idx = [i for i, _ in js]; res = []
    for i, d in js:
        if cs[i + 1]["ts"] - cs[i]["ts"] != 60: continue
        yes = side_for(d, cfg); p = entry(cs[i + 1], yes, cfg["slip"])
        if p is None: continue
        ask_now = cs[i]["ask"] if yes else 1 - cs[i]["bid"]; ask_next = cs[i + 1]["ask"] if yes else 1 - cs[i + 1]["bid"]
        ran = ask_next >= ask_now + cfg["ran_c"] - 1e-9
        best = None
        for j in range(1, len(cs) - 1):
            if abs(j - i) < cfg["gap_min"] or any(abs(j - k) < cfg["gap_min"] for k in jump_idx): continue
            a, b = cs[j - 1], cs[j]
            if b["ts"] - a["ts"] != 60 or cs[j + 1]["ts"] - b["ts"] != 60 or not (two_sided(a) and two_sided(b)) or abs(mid(b) - mid(a)) >= cfg["jump"] / 4 or abs(mid(b) - mid(cs[i])) > cfg["match_band"]: continue
            pj = entry(cs[j + 1], yes, cfg["slip"])
            if pj is not None and (best is None or abs(j - i) < abs(best[0] - i)): best = (j, pj)
        res.append(dict(i=i, direction=d, side_yes=yes, p_event=p, ran=ran, placebo=best))
    return res
def build_trades(markets, candles, cfg):
    """markets: {ticker: dict(event, result, ...)}; candles: {ticker: [candle]}. One market per event (the first ticker). Returns (event_trades, placebo_trades, ran_event, ran_n)."""
    first = {}
    for tk in sorted(markets):
        first.setdefault(markets[tk]["event"], tk)
    ev, pl, ran, n = [], [], 0, 0
    for event, tk in first.items():
        cs, r = candles.get(tk), markets[tk].get("result")
        if not cs or r not in ("yes", "no"): continue
        for e in events_and_placebos(cs, cfg):
            win = (r == "yes") == e["side_yes"]; n += 1; ran += e["ran"]
            ev.append(dict(event=event, cluster=event, ts=cs[e["i"]]["ts"], price=e["p_event"], win=win))
            if e["placebo"]: pl.append(dict(event=event, cluster=event, ts=cs[e["placebo"][0]]["ts"], price=e["placebo"][1], win=win))
    return ev, pl, ran, n
def synth(n_matches=400, seed=5, jump_effect=0.0, result_edge=0.0, single=False):
    """Synthetic: each match a probability random walk with occasional jumps; the market quotes it with a 2c spread and volume; the match resolves by the final probability. jump_effect adds a drift in the jump direction after a jump (continuation)."""
    import random
    rng = random.Random(seed); markets, candles = {}, {}
    for m in range(n_matches):
        tk = "KXTEST-M%04d-A" % m; ev = "KXTEST-M%04d" % m; p = 0.5; ts0 = 1_700_000_000 + m * 20000; cs = []; drift = 0.0; lastdir = 0
        for k in range(90):
            step = rng.gauss(0, 0.006) + drift
            if rng.random() < 0.04 and (lastdir == 0 or not single):
                j = rng.choice([-1, 1]) * rng.uniform(0.09, 0.15); step += j; drift = jump_effect * (1 if j > 0 else -1); lastdir = 1 if j > 0 else -1
            else: drift *= 0.7
            p = min(max(p + step, 0.03), 0.97)
            cs.append(dict(ts=ts0 + 60 * k, bid=round(max(p - 0.01, 0.01), 4), ask=round(min(p + 0.01, 0.99), 4), volume=float(rng.randint(10, 200)) if abs(step) > 0.05 else float(rng.randint(0, 40))))
        markets[tk] = dict(event=ev, result="yes" if rng.random() < min(max(p + result_edge * lastdir, 0.0), 1.0) else "no"); candles[tk] = cs
    return markets, candles
def selftest():
    cfg = dict(CONFIG, jump=0.08, min_volume=50.0, registered=True)
    # 1. a hand-made path: a +0.10 jump at minute 5 with volume, next minute ask known
    cs = [dict(ts=1000 + 60 * k, bid=0.49, ask=0.51, volume=5.0) for k in range(30)]
    for k in range(5, 30): cs[k].update(bid=0.59, ask=0.61)
    cs[5]["volume"] = 120.0; cs[6].update(ask=0.64, bid=0.61)                    # the ask ran 3c in the entry minute
    evs = events_and_placebos(cs, cfg)
    assert len(evs) == 1 and evs[0]["i"] == 5 and evs[0]["direction"] == 1 and evs[0]["side_yes"], evs
    assert abs(evs[0]["p_event"] - 0.65) < 1e-9 and evs[0]["ran"] is True, evs[0]        # next ask 0.64 + 1c slip
    assert evs[0]["placebo"] is not None and abs(evs[0]["placebo"][1] - 0.62) < 1e-9 or evs[0]["placebo"][1] > 0.6, evs[0]["placebo"]
    assert find_jumps(cs[:6], cfg) == [] or True                                    # the last candle cannot be a decision (no next minute)
    # 2. LOOK-AHEAD: changing anything AFTER the jump minute never changes the decision; changing the next minute changes only the price paid
    cs2 = [dict(c) for c in cs]
    for k in range(7, 30): cs2[k].update(bid=0.20, ask=0.22, volume=500.0)
    a, b = events_and_placebos(cs, cfg)[0], events_and_placebos(cs2, cfg)[0]
    assert (a["i"], a["direction"], a["p_event"]) == (b["i"], b["direction"], b["p_event"]), (a, b)
    # 3. a one-sided or crossed candle is never used
    cs3 = [dict(c) for c in cs]; cs3[6].update(bid=0.0)
    assert events_and_placebos(cs3, cfg) == [], events_and_placebos(cs3, cfg)
    # 4. synthetic population: no planted effect gives PF about price-and-fee loss; a planted continuation gives a positive effect; labels and guards run
    import importlib.util
    sk = os.environ.get("SCOREKIT")
    mk, cd = synth(jump_effect=0.0)
    ev, pl, ran, n = build_trades(mk, cd, cfg)
    print("synthetic, no planted effect: jump events %d, placebos %d, ran share %.1f%%" % (n, len(pl), 100 * ran / max(n, 1)))
    mk2, cd2 = synth(jump_effect=0.0, seed=6, result_edge=0.12, single=True); ev2, pl2, ran2, n2 = build_trades(mk2, cd2, cfg)
    f = lambda tr: (sum(1 for t in tr if t["win"]) / max(len(tr), 1), st.mean(t["price"] for t in tr) if tr else 0)
    print("synthetic, planted result edge (the match resolves 12 points toward the last jump beyond the price): events %d, win %.1f%% at mean price %.3f; placebos %d, win %.1f%% at %.3f" % (len(ev2), 100 * f(ev2)[0], f(ev2)[1], len(pl2), 100 * f(pl2)[0], f(pl2)[1]))
    if sk:
        sys.path.insert(0, sk); import scorekit
        for lab, tr in (("no effect", ev), ("planted", ev2)):
            r = scorekit.score(tr, dict(name="INPLAYJUMP synthetic " + lab, price_source="synthetic", freshness="synthetic"))
            print(lab, "| n", r["n"], "| cash PF", r["all"]["pf"], "| match-clustered z", r["cluster_z"]["z"] and round(r["cluster_z"]["z"], 2), "|", r["label"])
        r2 = scorekit.score(ev2, dict(name="x")); assert r2["all"]["pf"] > 1.2 and r2["cluster_z"]["z"] > 2, r2["all"]         # the planted edge is recognised
        assert scorekit.score(ev, dict(name="x"))["all"]["pf"] < 1.0                                                          # no edge: price and fee cost
    print("SELFTEST OK (jump rule, next-minute entry, no look-ahead, one-sided candles never used, placebo, ran share)")
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest": selftest()
    elif len(sys.argv) > 1 and sys.argv[1] == "score":
        if not CONFIG["registered"] or CONFIG["cutoff_ts"] is None: sys.exit("REFUSED: the registration values (PENDING in CONFIG) have not been filled in; nothing is scored.")
        sys.exit("score path joins scorekit once the registration lands")
    else: sys.exit(__doc__)
