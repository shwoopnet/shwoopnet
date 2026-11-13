#!/usr/bin/env python3
"""SPXFV1 scorer, BUILD 1, re-frozen on the Head's rulings of 16:47Z and 16:49Z (Testing Desk, Nov 13, 2026). Research only: reads files, sends nothing, places nothing.
Written FROM THE CARD TEXT ALONE: DESK_A_SPX_CARDS_NOV13.md at 94c4dfbc (body, the Head's dated lines, D1 to D8) and, for the inherited shape only, section 12 of CFRTI_K_REGISTRATION.md. No Desk A or History Miner scorer was read.
NOT RUN ON DATA: no landed file is read until Auditor B is CLEAN on this code (rule 16/16b). Aggregates only in the output: counts, PF, mean, labels. No bar value and no per-window probability is ever printed (D8).

Rule (one specification, one try): for each KXINX15M window (close C from the settled list, result yes/no):
  F_now  = close of the ES 1 minute bar with ts_event = C - 180 s (it ends at C - 120 s);   F_open = close of the bar with ts_event = C - 960 s (it ends at C - 900 s)       (D7: ts_event is the bar START)
  F_now and F_open must carry the SAME instrument_id, else the window is SKIPPED and counted (roll).
  sd_1m = SAMPLE sd of the 10 one-minute log changes ending at the F_now bar (bars C-180-60k for k = 0..10; a change needs both its bars; at least 6 present);  sd = sd_1m * sqrt(119/60)   (D1)
  model chance of YES = Phi( ln(F_now / F_open) / sd ).   Decision candle = the Kalshi 1 minute candle ending at C - 120 s: YES bid and ask CLOSE.
  Cheaper side = the lower ask (YES ask vs NO ask = 1 - YES bid), a tie goes to YES.  Model chance of that side: Phi(z) for YES, 1 - Phi(z) for NO.
  BUY 1 contract of the cheaper side at its ask when: model chance - ask >= 0.05, YES spread (ask - bid) <= 0.03, cheaper-side ask in [0.05, 0.30]. Held to settlement.
  Fee (GOVERNING, Head 16:49Z): 0.07 x C x p x (1 - p), C = 1, rounded UP to the cent per order; every bar, label, z and kill reads it; the unrounded figure prints only as information. A void is a fee-only loss; an EMPTY result stops the run. Every comparison carries 1e-9.
  Quote: crossed or locked (yes_bid + no_bid >= 1 - 1e-9, no_bid = 1 - yes_ask) is no quote, counted. Ties (YES ask = NO ask) go to YES and are counted.
Development = windows closing before HELDOUT_FIRST (2026-12-01T00:00:00Z); a window on or after it is never opened in `dev` (counted, not read). `heldout` refuses before READ_DATE (2027-02-26) and needs the committed marker line.
Usage:  spxfv1.py dev <lists run>... --candles <candle run>... --es <ES ohlcv-1m csv>
        spxfv1.py heldout <marker file> <lists run>... --candles <candle run>... --es <ES csv>
"""
import json, math, os, statistics as st, sys, calendar, time, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

HELDOUT_FIRST = calendar.timegm((2026, 12, 1, 0, 0, 0))
READ_DATE = calendar.timegm((2027, 2, 26, 0, 0, 0))
MIN_TRADED = 150
SERIES = "KXINX15M"
TOL = 1e-9
H_SECONDS = 119.0                 # D1: from the end of the F_now bar (C - 120 s) to the settling second (the prior second to the close)
EDGE_MIN, SPREAD_MAX, BAND_LO, BAND_HI = 0.05, 0.03, 0.05, 0.30
MIN_CHANGES, N_CHANGES = 6, 10
AMBIG = "AMBIGUOUS"
AMBIGUITIES = [
    "F_now / F_open are the bar CLOSE prices ('the futures mark at that minute'); D7 names the bars, not the field. Taken as close.",
    "sd_1m is the sample sd (n - 1) of the changes that are present, mean subtracted; a change needs both of its bars ON F_now's instrument id (Head 16:47Z); fewer than 6 present drops the window.",
    "sd = 0 (all present changes equal) cannot give a probability: the window is dropped and counted, never traded.",
    "'Cheaper side' = lower ask; YES ask is the candle's yes_ask close, NO ask is 1 - yes_bid close; a tie goes to YES (the SOCDERIV convention).",
    "The 'YES spread' is yes_ask - yes_bid of the decision candle (closes). A missing bid or ask, or a crossed or locked quote, is no quote (counted).",
    "Two ES rows for one ts_event STOP the run, naming the window, when that bar is one the window reads (Head 16:51Z).",
    "The COMPARED z is clustered by the window's event ticker (Head 16:51Z); the UTC-day clustered z is printed beside it as INFORMATION ONLY.",
    "Thirds (Head 16:49Z): equal time spans from 2026-12-01T00:00Z to the last traded close at or before READ_DATE in the held-out read; in development (nothing reaches Dec 1) from the first to the last traded close. scorekit's equal-count windows are printed too.",
    "A result of 'void' is a fee-only loss; an empty result or any other text than yes, no or void STOPS the run, naming the window (Head 16:53Z).",
]


def phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def load_bars(path):
    """{ts_event epoch: (instrument_id, close)} from the Databento csv (ts_event is the bar START). Two rows on one ts mark it AMBIGUOUS."""
    out = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            sym = (r.get("symbol") or "").strip().upper()
            if sym and not (sym.startswith("ES") and not sym.startswith("MES")):
                raise SystemExit("STOP: row symbol %r is not ES (D7: ES only, MES is not registered)" % sym)
            ts = k.iso(r["ts_event"])
            try:
                c, iid = float(r["close"]), int(r["instrument_id"])
            except (KeyError, TypeError, ValueError):
                continue
            if ts is None:
                continue
            out[ts] = AMBIG if ts in out else (iid, c)
    return out


def futures_signal(close_ts, bars):
    """-> (status, sd, z) ; status is None when usable, else a drop reason."""
    now_b, open_b = bars.get(close_ts - 180), bars.get(close_ts - 960)
    if now_b == AMBIG or open_b == AMBIG:
        return "ambiguous bar", None, None
    if now_b is None:
        return "no F_now bar", None, None
    if open_b is None:
        return "no F_open bar", None, None
    if now_b[0] != open_b[0]:
        return "roll (instrument id differs)", None, None
    chg = []
    for j in range(N_CHANGES):
        a, b = bars.get(close_ts - 180 - 60 * j), bars.get(close_ts - 180 - 60 * (j + 1))
        if a == AMBIG or b == AMBIG:
            return "ambiguous bar", None, None
        if a is not None and b is not None and a[0] == now_b[0] and b[0] == now_b[0] and a[1] > 0 and b[1] > 0:
            chg.append(math.log(a[1] / b[1]))
    if len(chg) < MIN_CHANGES:
        return "fewer than %d one-minute changes" % MIN_CHANGES, None, None
    sd1 = st.stdev(chg)
    sd = sd1 * math.sqrt(H_SECONDS / 60.0)
    if not sd > 0:
        return "sd zero", None, None
    if not (now_b[1] > 0 and open_b[1] > 0):
        return "bad bar price", None, None
    return None, sd, math.log(now_b[1] / open_b[1]) / sd


def is_tie(yes_bid, yes_ask):
    """A tie is counted only on a two-sided quote, 0 < yes_bid < yes_ask < 1 and not crossed or locked (Head 16:53Z, Auditor B): an empty book (0.00 / 1.00) is not a tie."""
    if yes_bid is None or yes_ask is None:
        return False
    if not (yes_bid > TOL and yes_ask < 1.0 - TOL and yes_bid + (1.0 - yes_ask) < 1.0 - TOL):
        return False
    return abs(yes_ask - (1.0 - yes_bid)) <= TOL


def decide(yes_bid, yes_ask, p_yes):
    """-> (side, ask, model_chance) or (None, reason). Pure rule on one decision candle and the model chance of YES."""
    if yes_bid is None or yes_ask is None:
        return None, "no decision quotes"
    if yes_bid + (1.0 - yes_ask) >= 1.0 - TOL:          # yes_bid + no_bid >= 1: crossed or locked
        return None, "crossed or locked quote"
    if not (yes_ask - yes_bid <= SPREAD_MAX + TOL):
        return None, "spread above 3c"
    no_ask = 1.0 - yes_bid
    side, ask = ("yes", yes_ask) if yes_ask <= no_ask + TOL else ("no", no_ask)          # lower ask, tie to YES
    if not (BAND_LO - TOL <= ask <= BAND_HI + TOL):
        return None, "cheap side outside 0.05 to 0.30"
    chance = p_yes if side == "yes" else 1.0 - p_yes
    if not (chance - ask >= EDGE_MIN - TOL):
        return None, "edge under 5c"
    return (side, ask, chance), None


def build(mk, cs, bars, cutoff_lo=None, cutoff_hi=None):
    """mk: scorekit.markets; cs: scorekit.candles; bars: load_bars. Windows with cutoff_lo <= close < cutoff_hi only (the others are counted, not read).
    -> (trades, gate0 counts). A trade is a scorekit Trade plus 'fee_rounded' bookkeeping done by the caller."""
    g = {"windows_listed": 0, "not_in_range_not_read": 0, "no_close_time": 0, "no_decision_candle": 0, "no_trade_signal": 0, "traded": 0, "void": 0, "ties_yes_ask_equals_no_ask": 0}
    trades = []
    for tkr in sorted(mk):
        m = mk[tkr]
        if m["series"] != SERIES:
            continue
        g["windows_listed"] += 1
        c = m["close"]
        if c is None:
            g["no_close_time"] += 1; continue
        if (cutoff_lo is not None and c < cutoff_lo) or (cutoff_hi is not None and c >= cutoff_hi):
            g["not_in_range_not_read"] += 1; continue
        res = m["result"]
        if res is None or str(res).strip() == "":
            raise SystemExit("STOP: empty result on %s; a settled list must carry every result (Head ruling)" % tkr)
        if res not in ("yes", "no", "void"):
            raise SystemExit("STOP: result %r on window %s is not yes, no or void (Head ruling: odd result text stops the run)" % (res, tkr))
        dec = next((x for x in cs.get(tkr, []) if x["ts"] == c - 120), None)
        if dec is None:
            g["no_decision_candle"] += 1; continue
        why, sd, z = futures_signal(c, bars)
        if why == "ambiguous bar":
            raise SystemExit("STOP: two ES rows share one ts_event inside the bars of window %s (Head ruling: a duplicate ts_event stops the run)" % tkr)
        if why:
            g[why] = g.get(why, 0) + 1; continue
        if is_tie(dec["bid"], dec["ask"]):
            g["ties_yes_ask_equals_no_ask"] += 1          # a valid two-sided quote whose two asks are equal: the tie goes to YES
        pick, reason = decide(dec["bid"], dec["ask"], phi(z))
        if pick is None:
            g[reason] = g.get(reason, 0) + 1; g["no_trade_signal"] += 1; continue
        side, ask, chance = pick
        void = res == "void"
        g["traded"] += 1; g["void"] += void
        trades.append({"event": m["event"] or tkr, "cluster": m["event"] or tkr, "day": time.strftime("%Y-%m-%d", time.gmtime(c)), "ts": c - 120, "close": c, "price": ask, "win": (res == side), "void": void, "chance": chance})
    return trades, g


def with_net(trades, rounded):
    f = k.fee_rounded if rounded else k.fee
    out = []
    for t in trades:
        fe = f(t["price"])
        net = -fe if t["void"] else ((1 - t["price"] - fe) if t["win"] else (-t["price"] - fe))
        out.append(dict(t, net=net))
    return out


def date_thirds(trades, lo=None):
    """Three equal time spans of the traded CLOSES: from `lo` (HELDOUT_FIRST in the held-out read; the first traded close in development) to the last traded close."""
    if not trades:
        return [[], [], []]
    hi = max(t["close"] for t in trades)
    lo = min(t["close"] for t in trades) if lo is None else lo
    span = (hi - lo) or 1
    th = [[], [], []]
    for t in trades:
        th[min(2, int(3 * (t["close"] - lo) / span))].append(t)
    return th


def upf(rows):
    """UNROUNDED profit factor of the governing nets (None when no loss and no win; inf when no loss)."""
    return k.pf([k.net_of(t) for t in rows])


def card_label(rnd, thirds, wr, mp, mean_net, z_event=None):
    """The card's own verdict (never a research-bar pass). Every bar and kill reads the UNROUNDED profit factor of the governing (rounded-fee) nets."""
    n = len(rnd)
    p = upf(rnd)
    kills = {"cash_pf_under_1_at_n_100_plus": bool(n >= 100 and p is not None and p < 1.0 - TOL),
             "win_rate_within_3_points_of_price_implied_at_n_150_plus": bool(n >= MIN_TRADED and wr is not None and abs(wr - mp) <= 0.03 + TOL)}
    if n < 100:
        label = "no evidence at n = %d (under 100 traded)" % n
    elif n < MIN_TRADED:
        label = "NOT_ENOUGH_DATA (%d traded windows, need %d)" % (n, MIN_TRADED) + (" and KILLED: cash PF under 1.0" if kills["cash_pf_under_1_at_n_100_plus"] else "")
    elif any(kills.values()):
        label = "KILLED (" + ", ".join(x for x, v in kills.items() if v) + ")"
    else:
        tp = [upf(x) for x in thirds]
        ok = p is not None and p >= 1.5 - TOL and all(x is not None and x >= 1.5 - TOL for x in tp) and all(len(x) > 0 for x in thirds)
        label = ("RESEARCH BAR MET (BAR MET and event-clustered z %.2f >= %.2f), n %d" % (z_event, k.Z_BAR, n) if (z_event is not None and z_event >= k.Z_BAR - TOL) else "BAR MET (not a research-bar pass): pooled PF and each third PF at 1.5 or better, n %d" % n) if ok else "BAR NOT MET (pooled PF %s, thirds PF %s)" % (None if p is None else round(p, 4), [None if x is None else round(x, 4) for x in tp])
    return label, kills, {"pooled_pf_unrounded": p, "thirds_pf_unrounded": [upf(x) for x in thirds]}


CONSTANTS = {"fee_governing": "0.07 x C x p x (1 - p), C = 1, rounded UP to the cent per order (every bar, label, z and kill reads this); unrounded printed as INFORMATION ONLY",
             "sd": "sample (n - 1) sd of consecutive one-minute log changes, both bars present on F_now's instrument id, at least 6 of 10, times sqrt(119/60)",
             "H_seconds": H_SECONDS, "edge_min": EDGE_MIN, "spread_max": SPREAD_MAX, "band": [BAND_LO, BAND_HI], "tolerance": TOL,
             "quote": "decision candle yes_bid and yes_ask closes; crossed or locked (yes_bid + no_bid >= 1 - 1e-9) is no quote",
             "tie": "equal asks go to YES; ties counted", "void": "fee-only loss", "empty_result": "stops the run", "odd_result_text": "stops the run, naming the window", "duplicate_ts_event": "stops the run, naming the window",
             "bars_and_kills": "read the UNROUNDED profit factor of the governing nets; the rounded PF is printed for reading only",
             "thirds": "equal time spans of traded closes: HELDOUT_FIRST to the last traded close at or before READ_DATE (held-out); first to last traded close (development)",
             "HELDOUT_FIRST": "2026-12-01T00:00:00Z", "READ_DATE": "2027-02-26T00:00:00Z", "min_traded": MIN_TRADED, "series": SERIES}


def report(trades, g, label_cfg, lo=None):
    raw, rnd = with_net(trades, False), with_net(trades, True)
    n = len(trades)
    sc = k.score(rnd, dict(label_cfg, price_source="Kalshi 1 minute candle close (yes_bid, yes_ask) at the decision candle ending C - 120 s", freshness="candle bid and ask close: the book at the minute's end (CANDLEVSBOOK1: 95.9% within 1c on KXBTC15M; NOT measured for KXINX15M)"))
    day = k.cluster_z([dict(t, cluster=t["day"]) for t in rnd]) if rnd else None
    wr = (sum(1 for t in trades if t["win"]) / n) if n else None
    mp = (sum(t["price"] for t in trades) / n) if n else None
    th = date_thirds(rnd, lo)
    gov = k.stats(rnd)
    label, kills, exact = card_label(rnd, th, wr, mp, (gov["mean"] if n else None), sc["cluster_z"]["z"])
    return {"constants": CONSTANTS, "gate0_counts": g, "traded": n, "CARD_LABEL": label, "kill_flags": kills, "unrounded_pf": exact,
            "win_rate": None if wr is None else round(wr, 4), "mean_price_paid": None if mp is None else round(mp, 4),
            "win_rate_minus_price_points": None if wr is None else round(100 * (wr - mp), 2),
            "GOVERNING_fee_rounded_up_per_order": gov, "date_thirds_governing": [k.stats(x) for x in th],
            "COMPARED_z_by_event_ticker": sc["cluster_z"],
            "cluster_z_by_UTC_day_INFORMATION_ONLY": day,
            "INFORMATION_scorekit_generic_label_and_equal_count_windows": {"label": sc["label"], "windows": sc["windows"], "haircut_line": sc["haircut_line"], "price_source": sc["price_source"], "freshness": sc["freshness"]},
            "INFORMATION_ONLY_unrounded_fee": k.stats(raw), "ambiguities": AMBIGUITIES}


def _load(lists, candles, es):
    for f in list(lists) + list(candles):
        k.guard(f)
    return k.markets(lists), k.candles(candles), load_bars(es)


def dev_read(lists, candles, es):
    mk, cs, bars = _load(lists, candles, es)
    trades, g = build(mk, cs, bars, cutoff_hi=HELDOUT_FIRST)
    return report(trades, g, {"name": "SPXFV1 DEVELOPMENT (closes before 2026-12-01), small sample: under 100 traded is 'no evidence at n = x'"})


LOCAL_MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SPXFV1_HELDOUT_READ.local")


def heldout_read(marker, lists, candles, es, now=None, local_marker=None):
    now = time.time() if now is None else now
    if now < READ_DATE:          # before anything is loaded
        raise SystemExit("refused: before READ_DATE 2027-02-26T00:00Z")
    cut = k.Cutoff(HELDOUT_FIRST, marker, "READ-ONCE MARKER", not_before=READ_DATE, held_out=True)
    cut.marker_line()
    local_marker = local_marker or LOCAL_MARKER
    if os.path.exists(local_marker):          # read-once by a local file written BEFORE anything is printed (a second run refuses even before the committed marker line changes)
        raise SystemExit("refused: %s exists; the held-out read was already made: %s" % (local_marker, open(local_marker).read().strip()))
    mk, cs, bars = _load(lists, candles, es)
    trades, g = build(mk, cs, bars, cutoff_lo=HELDOUT_FIRST, cutoff_hi=READ_DATE + 1)          # closes at or before READ_DATE
    cut.check(trades, now)
    with open(local_marker, "w") as fh:
        fh.write("HELD-OUT READ MADE at %s UTC; folders %s; ES file sha256 %s\n" % (time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(now)), [os.path.basename(x.rstrip("/")) for x in list(lists) + list(candles)], __import__("hashlib").sha256(open(es, "rb").read()).hexdigest()))
    if len(trades) < MIN_TRADED:
        return {"NOT_ENOUGH_DATA": "%d traded windows, need %d; count only, no figure" % (len(trades), MIN_TRADED), "gate0_counts": g}
    return report(trades, g, {"name": "SPXFV1 HELD-OUT (closes from 2026-12-01 to READ_DATE), read once"}, lo=HELDOUT_FIRST)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] in ("dev", "heldout"):
        mode = a[0]
        marker = a[1] if mode == "heldout" else None
        rest = a[2:] if mode == "heldout" else a[1:]
        i, j = rest.index("--candles"), rest.index("--es")
        lists, cands, es = rest[:i], rest[i + 1:j], rest[j + 1]
        out = dev_read(lists, cands, es) if mode == "dev" else heldout_read(marker, lists, cands, es)
        print(json.dumps(out, indent=1, default=str))
    else:
        print(__doc__); print("\n".join(AMBIGUITIES))
