#!/usr/bin/env python3
"""LIQREV scorer, BUILD 2 (Testing Desk, Nov 13, 2026). Research only: reads files it is given, sends nothing, places nothing. DEVELOPMENT ONLY: refused before 2026-11-30T00:00Z; H is an INPUT, never computed here.
Built FROM THE CARD ALONE: Desk C's LIQREV_CARD.md at d2822839 (sha256 f0257cce) with Amendments 1 to 3 (readings R1 to R15). liqrev_score.py, its tests and hand-case files were NOT read.
Hand case: LIQREV_SECOND_HAND_CASE.md (committed first). Test: test_liqrev_second.py (INVENTED rows only). No real file is read by any test.
Window = a settled KXBTC15M market; development = closes 2026-11-17T00:00Z to before 2026-11-30T00:00Z, halves split at 2026-11-23T12:00Z; later closes are ignored and counted (held-out, never read).
Trigger (R3 to R5b): minutes t = close - 720 s .. close - 180 s step 60; L(t) per side = BTC of that side with t - 180 s <= ts < t; the first minute with L >= H (1e-9) for one side; both sides = no bet; 'sell' = a long was liquidated: bet YES, 'buy': bet NO.
Quote (R6): the first R6 poll with t_recv_ms in (t, t + 10 s]; YES ask = 1 - no_bid_px_1, NO ask = 1 - yes_bid_px_1, spread = YES ask - yes_bid_px_1; usable only if 0 < yes bid < YES ask < 1. Band 0.20 to 0.80 and spread <= 0.04 (R7), window USED either way.
Bet (R8): 1 contract at the ask, fee 0.07 p (1 - p) rounded up (scorekit.fee_rounded); a void is a fee-only loss and a bet. R15: scored only if one coverage interval [a, b) holds [close - 900, close - 180).
Coverage intervals are an INPUT (how they are built belongs to a separate row builder, the card says). R9: no conflict rule in the paper read.
Usage: a function API (dev_read); no command line reads a real file until the Head's go.
"""
import calendar, csv, gzip, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

TOL = 1e-9
SERIES = "KXBTC15M"
DEV_FROM = calendar.timegm((2026, 11, 17, 0, 0, 0))
DEV_TO = calendar.timegm((2026, 11, 30, 0, 0, 0))
HALF_SPLIT = calendar.timegm((2026, 11, 23, 12, 0, 0))
READ_NOT_BEFORE = DEV_TO
BAND_LO, BAND_HI, SPREAD_MAX = 0.20, 0.80, 0.04
FIRST_BEFORE_CLOSE_S, LAST_BEFORE_CLOSE_S, STEP_S, WINDOW_S = 720, 180, 60, 180
QUOTE_SPAN_S = 10
MIN_TRIGGERED, MIN_BETS, PF_MIN, HALF_PF_MIN, EVIDENCE_N = 60, 60, 1.0, 1.2, 100          # EVIDENCE_N 100: the Head's ruling of 21:15Z (the card's R14 text says 30)
USDT_CONTRACT_BTC, USD_CONTRACT_USD = 0.01, 100.0
AMBIGUITIES = [
    "R14 text vs the Head's ruling (21:15Z): the HEADLINE is development_verdict (closed if fewer than 60 bets, PF under 1.0, a half under 1.2, or the zero-try count under 60); evidence_label always prints beside it and below 100 bets reads 'no evidence at n = x' (the card says 30; the Head ruled 100). Neither replaces the other.",
    "R11 z: clustered by US Central date with scorekit.cluster_z (mean of per-day mean nets over its standard error across days with a bet); a per-day sum reading would differ (the Head ruled cluster_z for SPXFV1).",
    "R15 coverage interval [a, b) holds [close - 900, close - 180) = a <= close - 900 and close - 180 <= b.",
    "R6 unusable first poll (not 0 < yes bid < YES ask < 1) is counted as one_sided_quote, not a triggered window with a two-sided quote; the first poll only.",
    "A both-sided minute (R5b) uses the FIRST trigger minute only; no later minute is tried.",
    "Windows with closes before 2026-11-17 are ignored and counted; closes on or after 2026-11-30 are ignored and counted (the held-out is not read here).",
    "The fee is scorekit.fee_rounded (ceil of the cents after rounding to 6 decimals), the convention the Head ruled for CFRTI-K.",
]


def btc_size(inst_id, sz, bk_px):
    """R2: BTC-USDT-SWAP = sz x 0.01 BTC; BTC-USD-SWAP = sz x 100 USD / bk_px; any other instrument is refused."""
    sz = float(sz)
    if inst_id == "BTC-USDT-SWAP":
        return sz * USDT_CONTRACT_BTC
    if inst_id == "BTC-USD-SWAP":
        px = float(bk_px)
        if not px > 0:
            raise SystemExit("STOP: BTC-USD-SWAP row with bk_px %r" % bk_px)
        return sz * USD_CONTRACT_USD / px
    raise SystemExit("STOP: instrument %r is not BTC-USDT-SWAP or BTC-USD-SWAP (R2)" % inst_id)


def dedupe(rows):
    """R12: OKX rows de-duplicated on the recorder's own key (inst_id, ts_ms, side, pos_side, bk_px, sz); the first keeps."""
    seen, out = set(), []
    for r in rows:
        key = tuple(str(r.get(c)) for c in ("inst_id", "ts_ms", "side", "pos_side", "bk_px", "sz"))
        if key in seen:
            continue
        seen.add(key); out.append(r)
    return out


def liq_events(rows):
    """-> {'sell': [(ts_ms, btc)], 'buy': [(ts_ms, btc)]} sorted by time. A side other than sell or buy is refused."""
    ev = {"sell": [], "buy": []}
    for r in dedupe(rows):
        side = str(r.get("side")).strip()
        if side not in ev:
            raise SystemExit("STOP: liquidation side %r is not sell or buy (R1)" % side)
        ev[side].append((int(float(r["ts_ms"])), btc_size(r["inst_id"], r["sz"], r.get("bk_px"))))
    return {s: sorted(v) for s, v in ev.items()}


def L_at(events_side, t):
    """R3: BTC of one side with t - 180 s <= ts < t (t a whole-minute boundary in seconds)."""
    lo, hi = (t - WINDOW_S) * 1000, t * 1000
    return sum(b for ts, b in events_side if lo <= ts < hi)


def covered(intervals, close):
    """R15: one interval [a, b) holds [close - 900, close - 180)."""
    lo, hi = close - (FIRST_BEFORE_CLOSE_S + WINDOW_S), close - LAST_BEFORE_CLOSE_S
    return any(a <= lo + TOL and hi <= b + TOL for a, b in intervals)


def trigger(ev, close, H):
    """-> (t, side) for the first minute with L >= H, ('both', t) when both sides reach H in that minute, or None. side is 'sell' or 'buy'."""
    t = close - FIRST_BEFORE_CLOSE_S
    while t <= close - LAST_BEFORE_CLOSE_S:
        ls, lb_ = L_at(ev["sell"], t) >= H - TOL, L_at(ev["buy"], t) >= H - TOL
        if ls and lb_:
            return (t, "both")
        if ls or lb_:
            return (t, "sell" if ls else "buy")
        t += STEP_S
    return None


def first_quote(polls, t):
    """R6: the first poll with t_recv_ms in (t, t + 10 s]; polls = [(recv_ms, yes_bid, no_bid)] sorted. -> poll or None."""
    lo, hi = t * 1000, (t + QUOTE_SPAN_S) * 1000
    for p in polls:
        if lo < p[0] <= hi + TOL:
            return p
    return None


def usable(yes_bid, no_bid):
    if yes_bid is None or no_bid is None:
        return None
    ya = 1.0 - no_bid
    if not (0 < yes_bid < ya < 1):
        return None
    return {"yes_ask": ya, "no_ask": 1.0 - yes_bid, "spread": ya - yes_bid}


def load_r6_top(path):
    """{ticker: [(t_recv_ms, yes_bid_px_1, no_bid_px_1)]} from a book.csv.gz; an empty cell is None (never a shifted level)."""
    op = gzip.open if str(path).endswith(".gz") else open
    out = {}
    with op(path, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            f = lambda v: (float(v) if v not in (None, "") else None)
            try:
                out.setdefault(r["ticker"], []).append((int(float(r["t_recv_ms"])), f(r.get("yes_bid_px_1")), f(r.get("no_bid_px_1"))))
            except (KeyError, ValueError):
                continue
    return {tk: sorted(v) for tk, v in out.items()}


def markets_from_lists(folders):
    """Settled-list markets with duplicates PRESERVED (scorekit.markets would overwrite them): [{ticker, close, result}]."""
    out = []
    for f in ([folders] if isinstance(folders, str) else folders):
        for _, body in k.iter_answers(f):
            for m in (body.get("markets", []) if isinstance(body, dict) else []):
                if isinstance(m, dict) and m.get("ticker"):
                    out.append({"ticker": m["ticker"], "close": k.iso(m.get("close_time", "")), "result": m.get("result")})
    return out


def evidence_label(n, threshold):
    return ("no evidence at n = %d" % n) if n < threshold else "n = %d bets" % n


def central_day(t):
    import datetime, zoneinfo
    return datetime.datetime.fromtimestamp(t, zoneinfo.ZoneInfo("America/Chicago")).date().isoformat()


def pf_of(nets):
    return k.pf(nets)


def stats(bets):
    nets = [b["net"] for b in bets]
    n = len(nets)
    return {"n": n, "net": sum(nets), "mean": (sum(nets) / n if n else None), "pf": (pf_of(nets) if nets else None)}


def dev_read(markets, liq_rows, r6, coverage, H, now):
    """The development read. `now` is a stated argument; refused before 2026-11-30T00:00Z before anything is looked at; H is required."""
    if now < READ_NOT_BEFORE:
        raise SystemExit("refused: the development read is not allowed before 2026-11-30T00:00Z (R13)")
    if H is None or not (isinstance(H, (int, float)) and H > 0):
        raise SystemExit("STOP: H is a required input (a positive number of BTC)")
    ev = liq_events(liq_rows)
    c = {"windows_listed": 0, "before_development_not_read": 0, "heldout_ignored": 0, "no_liq_coverage": 0, "no_trigger": 0, "both_sides": 0, "no_quote": 0, "one_sided_quote": 0,
         "band_or_spread_fail": 0, "bets": 0, "voids": 0}
    seen, bets = set(), []
    for m in sorted(markets, key=lambda x: x["ticker"]):
        if not str(m["ticker"]).startswith(SERIES + "-"):
            continue
        tk = m["ticker"]
        if tk in seen:
            raise SystemExit("STOP: duplicate window %s (R8)" % tk)
        seen.add(tk)
        c["windows_listed"] += 1
        close = m["close"]
        if close is None:
            raise SystemExit("STOP: window %s has no close time" % tk)
        if close < DEV_FROM:
            c["before_development_not_read"] += 1; continue
        if close >= DEV_TO:
            c["heldout_ignored"] += 1; continue
        res = m["result"]
        if res is None or str(res).strip() == "" or res not in ("yes", "no", "void"):
            raise SystemExit("STOP: result %r on window %s is not yes, no or void (R8)" % (res, tk))
        if not covered(coverage, close):
            c["no_liq_coverage"] += 1; continue
        trig = trigger(ev, close, H)
        if trig is None:
            c["no_trigger"] += 1; continue
        t, side = trig
        if side == "both":
            c["both_sides"] += 1; continue
        poll = first_quote(r6.get(tk, []), t)
        if poll is None:
            c["no_quote"] += 1; continue
        q = usable(poll[1], poll[2])
        if q is None:
            c["one_sided_quote"] += 1; continue
        bet = "yes" if side == "sell" else "no"          # R1: sell = a long was liquidated: forced selling, bet YES
        ask = q["yes_ask"] if bet == "yes" else q["no_ask"]
        if not (BAND_LO - TOL <= ask <= BAND_HI + TOL and q["spread"] <= SPREAD_MAX + TOL):
            c["band_or_spread_fail"] += 1; continue
        fee = k.fee_rounded(ask)
        net = -fee if res == "void" else ((1.0 - ask - fee) if res == bet else (-ask - fee))
        c["bets"] += 1; c["voids"] += (res == "void")
        bets.append({"ticker": tk, "close": close, "net": net, "win": res == bet, "void": res == "void", "half": 1 if close < HALF_SPLIT else 2,
                     "day": central_day(close)})
    allb = stats(bets)
    h1, h2 = stats([b for b in bets if b["half"] == 1]), stats([b for b in bets if b["half"] == 2])
    triggered = c["bets"] + c["band_or_spread_fail"]
    z = k.cluster_z([dict(b, cluster=b["day"], event=b["ticker"], price=0.5) for b in bets]) if bets else None
    reasons = []
    if triggered < MIN_TRIGGERED:
        reasons.append("zero-try count: %d triggered windows with a two-sided quote, need %d" % (triggered, MIN_TRIGGERED))
    if allb["n"] < MIN_BETS:
        reasons.append("fewer than %d bets (n = %d)" % (MIN_BETS, allb["n"]))
    if allb["pf"] is not None and allb["pf"] < PF_MIN - TOL:
        reasons.append("cash PF under 1.0")
    for name, h in (("half 1", h1), ("half 2", h2)):
        if h["pf"] is not None and h["pf"] < HALF_PF_MIN - TOL:
            reasons.append("%s PF under 1.2" % name)
        elif h["pf"] is None and allb["n"] >= MIN_BETS:
            reasons.append("%s has no bets" % name)
    return {"counts": c, "triggered_with_two_sided_quote": triggered, "development_verdict": ("CLOSED (" + "; ".join(reasons) + ")") if reasons else "CONTINUE",
            "evidence_label": evidence_label(allb["n"], EVIDENCE_N),
            "all": allb, "half1": h1, "half2": h2, "z_by_central_day_cluster_z": z, "H_btc": H, "ambiguities": AMBIGUITIES}


if __name__ == "__main__":
    print(__doc__); print("\n".join(AMBIGUITIES))
