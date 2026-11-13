#!/usr/bin/env python3
"""CFRTI-K HELD-OUT reader, SECOND BUILD (Testing Desk, Nov 13, 2026). Research only: reads files, sends nothing, places nothing.
Built FROM THE CARD TEXT ALONE: CFRTI_K_REGISTRATION.md at 57e2b153 on claude/idea-desk-a (sha256 f42574fb), sections 1 to 13, the Nov 12 and Nov 13 amendments and the dated lines. Desk A's reader and cfrti_k.py were NOT read.
NOT RUN ON DATA. Hand case: CFRTI_K_HELD_HAND_CASE.md (committed before this code). Test: test_cfrti_k_heldout_second.py (made-up data only).

READ: refuses before READ_DATE (2026-11-20T00:00Z), before anything is loaded; needs the committed line starting 'READ-ONCE MARKER' in the registration file and refuses if it already says READ ON <date>;
      refuses if the local marker file CFRTI_K_HELDOUT_READ.local exists; under 50 held-out rows prints NOT_ENOUGH_DATA with the count only and writes NO marker (the read is not spent); otherwise writes the local marker BEFORE printing.
Windows: settled KXBTC15M markets from the lists. HELDOUT = closes on or after 2026-11-14T00:00:00Z. NOT BLIND = closes 2026-11-09T00:00Z up to 2026-11-14T00:00Z, printed separately, never pooled. Earlier closes are not read (counted).
Rule (sections 7 and 12): decision candle = the KXBTC15M candle ending close - 120 s (YES bid and ask CLOSE both present, spread <= 0.03); cheap side YES if its ask is in [0.05, 0.30] else NO if 1 - yes_bid is in [0.05, 0.30];
  perp mid = (bid close + ask close)/2 of PERPBTC1M; model index = strike x (mid at the candle ending close - 120 / mid at the candle ending close - 900), a missing opening mid drops the window;
  volatility: mids at close - 120 - 60j (j = 0..10), log changes between neighbouring marks where both exist, at least 6 changes, sample sd (n - 1) x sqrt(4/3); chance(YES) = Phi(ln(mid_now/mid_open)/sd);
  buy 1 contract of the cheap side when chance(side) - ask >= 0.05, held to settlement, fee 0.07 p (1 - p) UNROUNDED, void = fee-only loss. Every comparison carries 1e-9; the bar and the labels read UNROUNDED figures.
Bar (section 4): n >= 50, cash PF >= 1.3, mean > 0: 'cleared its registered bar (NOT the research bar)'; cash PF < 1.0 at n >= 30: FALSIFIED; else 'no call at n = x'.
Beside it: haircut (a), line (b) ran rows dropped, BOOK-REPLAY +2 s and +6 s and the stale-ask count (the last two only when R6 polls are given).
Usage: cfrti_k_heldout_second.py <registration file> --lists <runs>... --candles <KXBTC15M candle runs>... --perp <PERPBTC1M runs>... [--r6 <root holding book15r6/>]
"""
import calendar, glob, json, math, os, random, statistics as st, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

HELDOUT_FIRST = calendar.timegm((2026, 11, 14, 0, 0, 0))
NOTBLIND_FROM = calendar.timegm((2026, 11, 9, 0, 0, 0))
READ_DATE = calendar.timegm((2026, 11, 20, 0, 0, 0))
MIN_ROWS = 50
FALSIFY_N = 30
BAR_PF = 1.3
SERIES = "KXBTC15M"
PERP_TICKER = "KXBTCPERP"
TOL = 1e-9
EDGE_MIN, SPREAD_MAX, BAND_LO, BAND_HI = 0.05, 0.03, 0.05, 0.30
MIN_CHANGES, N_MARKS = 6, 10
HAIRCUT_FRACTION, HAIRCUT_DRAWS, HAIRCUT_SEED = 0.34, 1000, 20261114
RULES_PHRASE = "simple average of the sixty seconds"
LOCAL_MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CFRTI_K_HELDOUT_READ.local")
AMBIGUITIES = [
    "Cheap side: the YES test comes FIRST (YES if its ask is 0.05 to 0.30, else NO), as written in sections 1 and 7, not 'the lower ask'.",
    "Perp mid = (bid close + ask close)/2 (section 9); a mark with either missing is a missing mark.",
    "sd = 0 cannot give a probability: the window is dropped and counted ('sd zero'), never traded. The card is silent.",
    "Fee is UNROUNDED (section 1: 'fee 0.07 x p x (1 - p) unrounded, cash'); the rounded-up fee is printed as information only.",
    "A void result is a fee-only loss (the standing void rule); an empty or other result text STOPS the run naming the window (the Head's ruling for SPXFV1, applied here).",
    "'About 30' for the falsified line is 30. Under 50 rows the read is NOT_ENOUGH_DATA (the Head), so FALSIFIED is reachable only at 50 rows or more.",
    "Haircut (a): per draw a FIXED count round(0.34 n) of rows is dropped with rng.sample(range(n), k) from random.Random(20261114), 1,000 draws; the 5th and 95th percentiles are nearest rank. The card does not give these details.",
    "Windows with closes 2026-11-05 to 2026-11-09 are not named by any amendment: they are NOT READ and counted.",
    "READ_DATE is the Head's 2026-11-20. The owner's dated line (Nov 13) says the frozen read runs on Nov 14 once: if the Head wants it earlier the constant changes and the build is re-audited; nothing here overrides it.",
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
    """-> (held-out trades, not-blind trades, counts). Trade ts = the window close (the Cutoff guard reads it)."""
    g = {"windows_listed": 0, "closes_before_2026-11-09_not_read": 0, "heldout_windows": 0, "not_blind_windows": 0, "no decision candle": 0, "traded_heldout": 0, "traded_not_blind": 0, "void_traded": 0}
    held, nb = [], []
    for tkr in sorted(mk):
        m = mk[tkr]
        if m["series"] != SERIES:
            continue
        g["windows_listed"] += 1
        c = m["close"]
        if c is None:
            g["no close time"] = g.get("no close time", 0) + 1; continue
        if c < NOTBLIND_FROM:
            g["closes_before_2026-11-09_not_read"] += 1; continue
        group = held if c >= HELDOUT_FIRST else nb
        g["heldout_windows" if c >= HELDOUT_FIRST else "not_blind_windows"] += 1
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
        g["traded_heldout" if c >= HELDOUT_FIRST else "traded_not_blind"] += 1; g["void_traded"] += void
        group.append({"event": m["event"] or tkr, "ticker": tkr, "ts": c, "t0": c - 120, "close": c, "side": side, "price": ask, "win": (res == side), "void": void,
                      "ran": ran_flag(side, ask, by.get(c - 60)), "day": time.strftime("%Y-%m-%d", time.gmtime(c))})
    return held, nb, g


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
    n, p, mean = f["n"], f["pf"], f["mean"]
    if n >= MIN_ROWS and p is not None and p >= BAR_PF - TOL and mean is not None and mean > TOL:
        return "cleared its registered bar (NOT the research bar): cash PF >= 1.3, positive mean, n >= %d" % MIN_ROWS
    if n >= FALSIFY_N and p is not None and p < 1.0 - TOL:
        return "FALSIFIED (cash PF under 1.0 at n = %d)" % n
    return "no call at n = %d" % n


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


def heldout_read(marker, lists, cands, perp, r6_root=None, now=None, local_marker=None):
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
    held, nb, g = build(mk, cs, perp_mids(pc))
    if len(held) < MIN_ROWS:
        return {"NOT_ENOUGH_DATA": "%d held-out rows, need %d; count only, no figure, the read is NOT spent (no marker written)" % (len(held), MIN_ROWS), "counts": g}
    cut.check(held, now)
    with open(local_marker, "w") as fh:
        fh.write("HELD-OUT READ MADE at %s UTC; folders %s\n" % (time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(now)), [os.path.basename(x.rstrip("/")) for x in list(lists) + list(cands) + list(perp)]))
    r6 = load_r6(r6_root) if r6_root else None
    return {"constants": {"HELDOUT_FIRST": "2026-11-14T00:00:00Z", "NOT_BLIND_FROM": "2026-11-09T00:00:00Z", "READ_DATE": "2026-11-20T00:00:00Z", "min_rows": MIN_ROWS, "bar": "n >= 50, cash PF >= 1.3, mean > 0 (unrounded)",
                          "falsified": "cash PF < 1.0 at n >= 30", "fee": "0.07 p (1 - p) unrounded", "edge_min": EDGE_MIN, "spread_max": SPREAD_MAX, "band": [BAND_LO, BAND_HI], "tolerance": TOL, "vol": "sample sd of up to 10 one-minute log changes (>= 6) x sqrt(4/3)",
                          "haircut_seed": HAIRCUT_SEED}, "rules_primary_text": rules, "counts": g,
            "HELDOUT": group_report(held, r6), "NOT_BLIND_shares_Bitcoin_windows_with_DEPTH1_never_pooled": group_report(nb, r6), "ambiguities": AMBIGUITIES}


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
