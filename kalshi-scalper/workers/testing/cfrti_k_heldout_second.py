#!/usr/bin/env python3
"""CFRTI-K HELD-OUT reader, SECOND BUILD (Testing Desk, Nov 13, 2026). Research only: reads files, sends nothing, places nothing.
Built FROM THE CARD TEXT ALONE: CFRTI_K_REGISTRATION.md at 3be6d090 on claude/idea-desk-a (sha256 35b8a1fc6a9f5268), sections 1 to 13, the amendments and the dated lines (Nov 13, 17:04Z three labels; the EA's NO CALL line). Desk A's reader and cfrti_k.py were NOT read.
NOT RUN ON DATA. Hand case: CFRTI_K_HELD_HAND_CASE.md (committed before this code). Test: test_cfrti_k_heldout_second.py (made-up data only).

READ: refuses before READ_DATE (2026-11-20T00:00Z), before anything is loaded; needs the committed line starting 'READ-ONCE MARKER' in the registration file and refuses if it already says READ ON <date>;
      refuses if the local marker file CFRTI_K_HELDOUT_READ.local exists; n under 30, or n 30 to 49 with cash PF at or above 1.0, prints only 'NOT_ENOUGH_DATA, n = x' and writes NO marker (the read is not spent); every run is appended to CFRTI_K_HELDOUT_RUNS.log with its date and n; otherwise writes the local marker BEFORE printing.
Windows: settled KXBTC15M markets from the lists. The reader reads ONLY closes on or after 2026-11-14T00:00:00Z; earlier closes are not read (counted).
Rule (sections 7 and 12): decision candle = the KXBTC15M candle ending close - 120 s (YES bid and ask CLOSE both present, spread <= 0.03); cheap side YES if its ask is in [0.05, 0.30] else NO if 1 - yes_bid is in [0.05, 0.30];
  perp mid = (bid close + ask close)/2 of PERPBTC1M; model index = strike x (mid at the candle ending close - 120 / mid at the candle ending close - 900), a missing opening mid drops the window;
  volatility: mids at close - 120 - 60j (j = 0..10), log changes between neighbouring marks where both exist, at least 6 changes, sample sd (n - 1) x sqrt(4/3); chance(YES) = Phi(ln(mid_now/mid_open)/sd);
  buy 1 contract of the cheap side when chance(side) - ask >= 0.05, held to settlement, fee 0.07 p (1 - p) UNROUNDED, void = fee-only loss. Every comparison carries 1e-9; the bar and the labels read UNROUNDED figures.
Labels (section 4 as the Head ruled 17:09Z): n under 30 NOT_ENOUGH_DATA; n 30 to 49 FAIL if cash PF < 1.0 (marker, final) else NOT_ENOUGH_DATA; n >= 50 PASS = cash PF >= 1.3 and mean > 0, NO CALL = cash PF from 1.0 up to 1.3, FAIL = cash PF < 1.0.
Beside it: haircut (a), line (b) ran rows dropped, BOOK-REPLAY +2 s and +6 s and the stale-ask count (the last two only when R6 polls are given).
LINES FOLLOWED (quoted from CFRTI_K_REGISTRATION.md at 3be6d090, the registration text governs):
  FEE (sections 1 and 7): "One contract, held to settlement, fee 0.07 x p x (1 - p) unrounded, cash."  -> the fee is UNROUNDED in every decided figure; the rounded-up fee prints as information only.
  LABELS (dated line, 2026-11-13, the Head of R&D, 17:04Z): "the held-out read prints THREE labels at n of 50 or more: PASS = cash PF 1.3 or better and a mean above 0; NO CALL = cash PF from 1.0 up to 1.3 ...; FAIL = cash PF under 1.0 (then CFRTI-K is CLOSED FOR GOOD per the owner's decision). Under 50 rows it is NOT_ENOUGH_DATA."
  READ (dated line, 2026-11-13): "reading only closes from 2026-11-14T00:00:00Z, refusing before 2026-11-20, read-once marker checked before any data is read, only the count printed under 50."
Usage: cfrti_k_heldout_second.py <registration file> --lists <runs>... --candles <KXBTC15M candle runs>... --perp <PERPBTC1M runs>... [--r6 <root holding book15r6/>]
"""
import calendar, glob, json, math, os, random, statistics as st, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

HELDOUT_FIRST = calendar.timegm((2026, 11, 14, 0, 0, 0))
READ_DATE = calendar.timegm((2026, 11, 20, 0, 0, 0))
MIN_ROWS = 50
FAIL_EARLY_N = 30
BAR_PF = 1.3
SERIES = "KXBTC15M"
PERP_TICKER = "KXBTCPERP"
TOL = 1e-9
EDGE_MIN, SPREAD_MAX, BAND_LO, BAND_HI = 0.05, 0.03, 0.05, 0.30
MIN_CHANGES, N_MARKS = 6, 10
HAIRCUT_FRACTION, HAIRCUT_DRAWS, HAIRCUT_SEED = 0.34, 1000, 20261114
RULES_PHRASE = "simple average of the sixty seconds"
LOCAL_MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CFRTI_K_HELDOUT_READ.local")
RUN_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CFRTI_K_HELDOUT_RUNS.log")
AMBIGUITIES = [
    "Cheap side: the YES test comes FIRST (YES if its ask is 0.05 to 0.30, else NO), as written in sections 1 and 7, not 'the lower ask'.",
    "Perp mid = (bid close + ask close)/2 (section 9); a mark with either missing is a missing mark.",
    "sd = 0 cannot give a probability: the window is dropped and counted ('sd zero'), never traded. The card is silent.",
    "Fee is UNROUNDED (section 1: 'fee 0.07 x p x (1 - p) unrounded, cash'); the rounded-up fee is printed as information only.",
    "A void result is a fee-only loss (the standing void rule); an empty or other result text STOPS the run naming the window (the Head's ruling for SPXFV1, applied here).",
    "PF exactly 1.0 is NO CALL ('from 1.0 up to 1.3'); an undefined PF (no wins and no losses) is NO CALL. PF >= 1.3 implies a positive net, so the mean test never binds on its own.",
    "Haircut (a): per draw a FIXED count round(0.34 n) of rows is dropped with rng.sample(range(n), k) from random.Random(20261114), 1,000 draws; the 5th and 95th percentiles are nearest rank. The card does not give these details.",
    "The 17:04Z dated line says the reader reads ONLY closes from 2026-11-14T00:00:00Z: the NOT BLIND print of closes 2026-11-09 to 2026-11-13 (an earlier amendment) is therefore not produced; those closes are not read. The Head to confirm.",
    "READ_DATE 2026-11-20 (the dated line: Nov 14 is only the START of the held-out window). If there are under 50 rows on Nov 20 the reader prints NOT_ENOUGH_DATA and is run again on the first day with 50, once.",
    "The perp ticker in the candle runs is taken as KXBTCPERP, or the only ticker present; anything else stops the run (the landed layout of the perp answer is the scorekit shape, unverified for this reader).",
    "R6 clock offsets (exchange time via the Date header) are NOT applied: poll time = t_recv_ms / 1000. The replay and stale-ask lines say so.",
    "The Cutoff guard compares each held-out row's WINDOW CLOSE (trade 'ts' = close) with HELDOUT_FIRST, since the card defines the held-out by close.",
]


def phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def mid_of(c):
    if c is None or c.get("bid") is None or c.get("ask") is None:
        return None
    return (c["bid"] + c["ask"]) / 2.0


def perp_mids(perp_cs):
    """{end_period_ts: mid} for the perpetual (the card's index is its mid; the 10,000 unit never enters)."""
    if PERP_TICKER in perp_cs:
        cand = perp_cs[PERP_TICKER]
    elif len(perp_cs) == 1:
        cand = next(iter(perp_cs.values()))
    else:
        raise SystemExit("STOP: the perp candle runs hold tickers %s; expected %s or exactly one ticker" % (sorted(perp_cs), PERP_TICKER))
    return {c["ts"]: mid_of(c) for c in cand if mid_of(c) is not None}


def signal(close_ts, mids):
    """-> (drop reason or None, sd, z) from the perp mids."""
    now, op = mids.get(close_ts - 120), mids.get(close_ts - 900)
    if now is None:
        return "no decision-minute perp mid", None, None
    if op is None:
        return "no opening minute", None, None
    marks = [mids.get(close_ts - 120 - 60 * j) for j in range(N_MARKS + 1)]
    chg = [math.log(marks[j] / marks[j + 1]) for j in range(N_MARKS) if marks[j] is not None and marks[j + 1] is not None and marks[j] > 0 and marks[j + 1] > 0]
    if len(chg) < MIN_CHANGES:
        return "fewer than %d changes" % MIN_CHANGES, None, None
    sd = st.stdev(chg) * math.sqrt(4.0 / 3.0)
    if not sd > 0:
        return "sd zero", None, None
    if not (now > 0 and op > 0):
        return "bad perp mid", None, None
    return None, sd, math.log(now / op) / sd


def decide(yes_bid, yes_ask, p_yes):
    """-> ((side, ask, chance), None) or (None, reason): the YES test comes first."""
    if yes_bid is None or yes_ask is None:
        return None, "no decision quotes"
    if not (yes_ask - yes_bid <= SPREAD_MAX + TOL):
        return None, "spread above 3c"
    if BAND_LO - TOL <= yes_ask <= BAND_HI + TOL:
        side, ask, chance = "yes", yes_ask, p_yes
    elif BAND_LO - TOL <= 1.0 - yes_bid <= BAND_HI + TOL:
        side, ask, chance = "no", 1.0 - yes_bid, 1.0 - p_yes
    else:
        return None, "cheap side outside 0.05 to 0.30"
    if not (chance - ask >= EDGE_MIN - TOL):
        return None, "edge under 5c"
    return (side, ask, chance), None


def ran_flag(side, ask, nxt):
    """True/False, or None when the next candle (end close - 60 s) cannot say: ran = the cheap side's ask close there is 1c or more above the ask seen."""
    if nxt is None:
        return None
    if side == "yes":
        a = nxt.get("ask")
    else:
        a = None if nxt.get("bid") is None else 1.0 - nxt["bid"]
    if a is None:
        return None
    return a - ask >= 0.01 - TOL


def build(mk, cs, mids):
    """-> (held-out trades, counts). Trade ts = the window close (the Cutoff guard reads it)."""
    g = {"windows_listed": 0, "closes_before_2026-11-14_not_read": 0, "heldout_windows": 0, "no decision candle": 0, "traded_heldout": 0, "void_traded": 0}
    held = []
    for tkr in sorted(mk):
        m = mk[tkr]
        if m["series"] != SERIES:
            continue
        g["windows_listed"] += 1
        c = m["close"]
        if c is None:
            g["no close time"] = g.get("no close time", 0) + 1; continue
        if c < HELDOUT_FIRST:
            g["closes_before_2026-11-14_not_read"] += 1; continue
        g["heldout_windows"] += 1
        res = m["result"]
        if res is None or str(res).strip() == "":
            raise SystemExit("STOP: empty result on window %s; a settled list must carry every result" % tkr)
        if res not in ("yes", "no", "void"):
            raise SystemExit("STOP: result %r on window %s is not yes, no or void" % (res, tkr))
        if not m.get("floor") or not m["floor"] > 0:
            g["no strike"] = g.get("no strike", 0) + 1; continue
        by = {x["ts"]: x for x in cs.get(tkr, [])}
        dec = by.get(c - 120)
        if dec is None or dec.get("bid") is None or dec.get("ask") is None:
            g["no decision candle"] += 1; continue
        why, sd, z = signal(c, mids)
        if why:
            g[why] = g.get(why, 0) + 1; continue
        pick, reason = decide(dec["bid"], dec["ask"], phi(z))
        if pick is None:
            g[reason] = g.get(reason, 0) + 1; continue
        side, ask, chance = pick
        void = res == "void"
        g["traded_heldout"] += 1; g["void_traded"] += void
        held.append({"event": m["event"] or tkr, "ticker": tkr, "ts": c, "t0": c - 120, "close": c, "side": side, "price": ask, "win": (res == side), "void": void,
                      "ran": ran_flag(side, ask, by.get(c - 60)), "day": time.strftime("%Y-%m-%d", time.gmtime(c))})
    return held, g


def net(t, rounded=False):
    f = k.fee_rounded(t["price"]) if rounded else k.fee(t["price"])
    return -f if t["void"] else ((1 - t["price"] - f) if t["win"] else (-t["price"] - f))


def pf_of(nets):
    return k.pf(nets)


def figures(rows, rounded=False):
    nets = [net(t, rounded) for t in rows]
    n = len(nets)
    p = pf_of(nets) if nets else None
    return {"n": n, "net": sum(nets), "mean": (sum(nets) / n if n else None), "pf": p, "win_rate": (sum(1 for t in rows if t["win"]) / n if n else None)}


def label(f):
    """Registration section 4 as the Head ruled at 17:09Z, on UNROUNDED figures: n under 30 NOT_ENOUGH_DATA; n 30 to 49 FAIL if cash PF is under 1.0, else NOT_ENOUGH_DATA; n >= 50 PASS / NO CALL / FAIL."""
    n, p, mean = f["n"], f["pf"], f["mean"]
    if n < MIN_ROWS:
        if n >= FAIL_EARLY_N and p is not None and p < 1.0 - TOL:
            return "FAIL (cash PF %s under 1.0, n = %d, under the 50-row line: section 4's 'under 1.0 at n of about 30 or more'): CFRTI-K is CLOSED FOR GOOD (the owner)" % (p, n)
        return "NOT_ENOUGH_DATA, n = %d" % n
    if p is not None and p >= BAR_PF - TOL and mean is not None and mean > TOL:
        return "PASS (cash PF %s >= 1.3, mean above 0, n = %d; the registered bar, NOT the research bar)" % (p, n)
    if p is not None and p < 1.0 - TOL:
        return "FAIL (cash PF %s under 1.0, n = %d): CFRTI-K is CLOSED FOR GOOD (the owner)" % (p, n)
    return "NO CALL (cash PF %s from 1.0 up to 1.3, n = %d): not a fail" % (p, n)


def read_outcome(f):
    """'read' = the read is made now (marker written, final): n >= 50, or n 30 to 49 with cash PF under 1.0; 'not_enough' = only the count prints and NO marker is written."""
    return "not_enough" if label(f).startswith("NOT_ENOUGH_DATA") else "read"


def log_run(path, now, n, outcome):
    with open(path, "a") as fh:
        fh.write("%s UTC  n = %d  %s\n" % (time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(now)), n, outcome))


def haircut_a(rows):
    n = len(rows)
    if n == 0:
        return None
    kdrop = int(round(HAIRCUT_FRACTION * n))
    rng = random.Random(HAIRCUT_SEED)
    nets = [net(t) for t in rows]
    pfs = []
    for _ in range(HAIRCUT_DRAWS):
        gone = set(rng.sample(range(n), kdrop))
        pfs.append(pf_of([x for i, x in enumerate(nets) if i not in gone]))
    num = sorted((x if x is not None else 0.0) for x in pfs)
    pick = lambda q: num[max(0, int(math.ceil(q * len(num))) - 1)]
    return {"drop_count_per_draw": kdrop, "draws": HAIRCUT_DRAWS, "seed": HAIRCUT_SEED, "median_pf": st.median(num), "p5_pf": pick(0.05), "p95_pf": pick(0.95)}


def line_b(rows):
    seen = [t for t in rows if t["ran"] is not None]
    keep = [t for t in seen if not t["ran"]]
    f = figures(keep)
    return {"rows_with_a_next_candle": len(seen), "rows_without_a_next_candle_excluded": len(rows) - len(seen), "ran_rows": len(seen) - len(keep),
            "ran_share": ((len(seen) - len(keep)) / len(seen) if seen else None), "pf_non_ran": f["pf"], "n_non_ran": f["n"], "mean_non_ran": f["mean"]}


def replay_lines(rows, r6):
    """BOOK-REPLAY +2 s and +6 s (scorekit.fill_ioc, Desk A's convention as ruled) and the stale-ask count. r6 = {ticker: [poll]} or None."""
    if not r6:
        return "NOT COMPUTED: no R6 polls given"
    out = {"clock": "R6 poll time = t_recv_ms / 1000, NO exchange-time offset applied"}
    for d in (2, 6):
        got = []
        for t in rows:
            polls = r6.get(t["ticker"])
            if not polls:
                continue
            p = k.fill_ioc(polls, t["side"], t["price"], t["t0"], d)
            if p is None:
                continue
            fee = k.fee(p)
            got.append(-fee if t["void"] else ((1 - p - fee) if t["win"] else (-p - fee)))
        out["+%d s" % d] = {"filled": len(got), "of_signals": len(rows), "pf": (pf_of(got) if got else None), "net": sum(got), "mean": (sum(got) / len(got) if got else None)}
    withbook = stale = 0
    for t in rows:
        polls = r6.get(t["ticker"]) or []
        cand = [p for p in polls if t["t0"] - 4 - TOL <= p["t"] <= t["t0"] - 0.25 + TOL]
        if not cand:
            continue
        p = max(cand, key=lambda x: x["t"])
        lv = p["no_bids"] if t["side"] == "yes" else p["yes_bids"]
        if not lv:
            continue
        withbook += 1
        ask = min(1 - px for px, _ in lv)
        stale += (ask - t["price"] > 0.01 + TOL)
    out["rows_with_a_book_at_decision"] = withbook
    out["ask_not_on_the_book"] = stale
    return out


def group_report(rows, r6=None):
    reg, rnd = figures(rows), figures(rows, rounded=True)
    byday = k.cluster_z([dict(net=net(t), event=t["event"], cluster=t["day"], price=t["price"], win=t["win"]) for t in rows]) if rows else None
    return {"LABEL": label(reg), "registered_line_unrounded_fee": reg, "haircut_a_random_34pct_drop": haircut_a(rows), "line_b_ran_rows_dropped": line_b(rows),
            "book_replay_R6": replay_lines(rows, r6), "INFORMATION_rounded_up_fee": rnd, "INFORMATION_UTC_day_clustered_z": byday}


def check_rules_text(lists):
    """Section 12: print the rules_primary text of the first market with it; STOP if it does not carry the registered sentence."""
    for f in lists:
        for _, body in k.iter_answers(f):
            for m in (body.get("markets", []) if isinstance(body, dict) else []):
                if isinstance(m, dict) and str(m.get("ticker", "")).startswith(SERIES) and m.get("rules_primary"):
                    txt = m["rules_primary"]
                    if RULES_PHRASE not in txt or "at least" not in txt:
                        raise SystemExit("STOP: rules_primary does not say the registered strike is the settlement average at the open; the Head must be told before any figure: %r" % txt[:300])
                    return txt
    return None


def load_r6(root):
    out = {}
    for f in sorted(glob.glob(os.path.join(root, "**", "book.csv.gz"), recursive=True)):
        for t, v in k.r6_book(f).items():
            out.setdefault(t, []).extend(v)
    return {t: sorted(v, key=lambda p: p["t"]) for t, v in out.items()}


def heldout_read(marker, lists, cands, perp, r6_root=None, now=None, local_marker=None, run_log=None):
    now = time.time() if now is None else now
    if now < READ_DATE:
        raise SystemExit("refused: before READ_DATE 2026-11-20T00:00Z")
    cut = k.Cutoff(HELDOUT_FIRST, marker, "READ-ONCE MARKER", not_before=READ_DATE, held_out=True)
    cut.marker_line()
    local_marker = local_marker or LOCAL_MARKER
    if os.path.exists(local_marker):
        raise SystemExit("refused: %s exists; the held-out read was already made: %s" % (local_marker, open(local_marker).read().strip()))
    for f in list(lists) + list(cands) + list(perp):
        k.guard(f)
    rules = check_rules_text(lists)
    mk, cs, pc = k.markets(lists), k.candles(cands), k.candles(perp)
    held, g = build(mk, cs, perp_mids(pc))
    run_log = run_log or RUN_LOG
    if read_outcome(figures(held)) == "not_enough":
        log_run(run_log, now, len(held), "NOT_ENOUGH_DATA, no marker written (the read is not spent)")
        return {"NOT_ENOUGH_DATA": "n = %d" % len(held)}          # only the count; no marker, the read is not spent
    cut.check(held, now)
    with open(local_marker, "w") as fh:
        fh.write("HELD-OUT READ MADE at %s UTC; folders %s\n" % (time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(now)), [os.path.basename(x.rstrip("/")) for x in list(lists) + list(cands) + list(perp)]))
    r6 = load_r6(r6_root) if r6_root else None
    log_run(run_log, now, len(held), "READ MADE, marker written: %s" % label(figures(held)).split(" (")[0].split(",")[0])
    return {"constants": {"card": "CFRTI_K_REGISTRATION.md at Desk A 3be6d090, sha256 35b8a1fc6a9f5268", "fee_line_followed": "fee 0.07 x p x (1 - p) unrounded, cash (sections 1 and 7)",
                          "label_line_followed": "dated line 2026-11-13 17:04Z: PASS = cash PF 1.3 or better and a mean above 0; NO CALL = cash PF from 1.0 up to 1.3; FAIL = cash PF under 1.0; under 50 NOT_ENOUGH_DATA", "HELDOUT_FIRST": "2026-11-14T00:00:00Z", "READ_DATE": "2026-11-20T00:00:00Z", "min_rows": MIN_ROWS, "n_under_30": "NOT_ENOUGH_DATA, no marker", "n_30_to_49": "FAIL if cash PF < 1.0 (marker written, final), else NOT_ENOUGH_DATA with no marker", "PASS": "n >= 50, cash PF >= 1.3, mean > 0 (unrounded)", "NO_CALL": "cash PF from 1.0 up to 1.3", "FAIL": "cash PF < 1.0 (then CLOSED FOR GOOD)", "fee": "0.07 p (1 - p) unrounded", "edge_min": EDGE_MIN, "spread_max": SPREAD_MAX, "band": [BAND_LO, BAND_HI], "tolerance": TOL, "vol": "sample sd of up to 10 one-minute log changes (>= 6) x sqrt(4/3)",
                          "haircut_seed": HAIRCUT_SEED}, "rules_primary_text": rules, "counts": g,
            "HELDOUT": group_report(held, r6), "ambiguities": AMBIGUITIES}


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) > 6 and a[1] == "--lists":
        marker = a[0]
        opts, cur = {"--lists": [], "--candles": [], "--perp": [], "--r6": []}, None
        for x in a[1:]:
            if x in opts: cur = x
            else: opts[cur].append(x)
        out = heldout_read(marker, opts["--lists"], opts["--candles"], opts["--perp"], (opts["--r6"] or [None])[0])
        print(json.dumps(out, indent=1, default=str))
    else:
        print(__doc__); print("\n".join(AMBIGUITIES))
