"""GOLDFV1, independent re-implementation (audit copy).

Research only: nothing here trades, signs, or calls any network.
Registration: kalshi-scalper/README.md, "## Pre-registration: GOLDFV1".
Written WITHOUT reading src/scalper/goldfv1.py, so the two can be compared.

    PYTHONPATH=src python -m scalper.goldfv1_aud run      # discovery + validation
    PYTHONPATH=src python -m scalper.goldfv1_aud holdout  # holdout only (read once)
    PYTHONPATH=src python -m scalper.goldfv1_aud counts   # counts only, no results

Ambiguity choices (the conservative reading each time):

 A1. Which future bars are readable at D. The registration says "START at or
     before D - 60 s" and also "the future bars used end one minute earlier"
     than the signal candle (which ends at D). A bar that STARTS at D - 60
     ends at D, the same minute as the signal candle, and is only complete
     at D. Both sentences are satisfied by bars that END at or before D - 60,
     i.e. START at or before D - 120. That is used (LAST_BAR_LAG = 120). It
     reads strictly less than the literal "start <= D - 60" rule.
 A2. d = close of the bar starting at D - 120 (the last readable bar, which
     must be present, see A4) minus close of the bar starting at O - 60.
 A3. "Missing bar within 2 minutes of O": every bar starting in
     [O - 120, O + 120] must be present (5 bars; all are before D).
 A4. "Missing bar within 2 minutes of D": every READABLE bar whose end lies
     within 2 minutes of D must be present, i.e. the bars starting at D - 180
     and D - 120. Bars after the readable cut are never looked at, not even
     for presence (that would be look-ahead on data availability).
 A5. sigma: the 60 one-minute slots ending at the last readable bar (starts
     D - 120 - 59*60 .. D - 120). At least 45 of those 60 bars present.
     Changes are close-to-close between bars exactly 60 s apart, both inside
     those slots (so at most 59 changes). Sample standard deviation (ddof 1,
     the larger of the two). Fewer than 2 changes, or sigma 0, is a skip.
 A6. Roll / bad-print skip: any change between CONSECUTIVE PRESENT bars
     (whatever the gap between them) of more than 0.5% of the earlier close,
     anywhere from the earliest bar read (sigma slots or O - 120) to the last
     readable bar. Comparing across a gap skips more, never fewer.
 A7. tau stays as registered: minutes from D to C (10 or 6), although the
     last price read is one minute older (A1). Not changed, it is fixed text.
 A8. Kalshi quotes: YES ask = ask_c, NO ask = 1 - bid_c. A side has no quote
     if its ask is 0.99 or more, or (NO side) bid_c is 0 or missing; a YES
     ask of 0 or missing is also no quote. A side with no quote cannot be
     bought. A candle present but with neither side quoted counts as a
     no-quote skip for that try.
 A9. S tries: if BOTH sides pass (edge >= 0.05 and ask in [0.10, 0.95]),
     which needs a crossed book, the market is skipped, not traded.
     F tries / L1 parent: the side with ask in [0.88, 0.97] inclusive; if
     both sides are in the band (crossed book) the market is skipped.
 A10. The L1 parent is reported twice: on the same model-scored set as
     kept + removed (so kept + removed = parent exactly), and on every
     market with a candle ending at D (the parent without model skips).
 A11. Next-candle fill: same side chosen at D, filled at the closing ask of
     the candle ending at D + 60. No re-check of the entry rule. If that
     candle is missing or the side has no quote in it, the trade does not
     fill (dropped). Zero-volume check is on the candle actually filled.
 A12. Zero-volume variant: a trade whose fill candle has volume 0 (or
     NULL) is unfillable and dropped.
 A13. P/L per order of C contracts: win (1 - ask) * C - fee, loss
     -ask * C - fee, fee = taker_fee(ask, C, mult), rounded up per order.
     PF = sum of positive order P/L / sum of |negative order P/L| ("inf" if
     no losing order). Cents per contract from the 1 contract run (the
     larger per-contract fee); the 10 contract figure is also printed.
 A14. Trading day = UTC calendar date of the close time. Day-clustered z
     (1 contract): z = total / sqrt(G/(G-1) * sum_d (S_d - n_d * mean)^2),
     G days, S_d the day's P/L sum, n_d its trades.
 A15. Universe: settled (result yes/no) KXGOLD15M markets with close in
     [2026-10-01 00:00 UTC, end of the last COMPLETE future bar]. A bar is
     complete when its start is minute aligned and start + 60 <= fetched;
     the in-progress bar (e.g. start not on a minute) is dropped. Windows are
     thirds of this full universe (model skips included), cut at n//3, 2n//3.
 A16. Same ticker in both files: market rows must match exactly, else the
     ticker is dropped. Candles are the union by end_ts; a candle present in
     both files with different values is treated as missing.
 A17. Gold bars with a non-positive or missing close are treated as absent.
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from scalper.fees import taker_fee

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
GC_FILE = DATA / "gc1m.json"
DB_FILES = [DATA / "book.sqlite", DATA / "five.sqlite"]
SERIES = "KXGOLD15M"

UNIVERSE_START = int(datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp())
LAST_BAR_LAG = 120          # A1
SIGMA_SLOTS = 60
SIGMA_MIN_BARS = 45
MAX_MOVE = 0.005
EDGE_MIN = 0.05
S_ASK_LO, S_ASK_HI = 0.10, 0.95
L1_LO, L1_HI = 0.88, 0.97
LOOKS = {10: 600, 6: 360}
EPS = 1e-9


# ---------------------------------------------------------------- loading

def load_bars():
    raw = json.loads(GC_FILE.read_text())
    fetched = int(raw.get("fetched") or 0)
    bars = {}
    dropped = 0
    for k, v in raw["bars"].items():
        s = int(k)
        c = v[3] if v and len(v) > 3 else None
        if s % 60 or (fetched and s + 60 > fetched) or c is None or not c > 0:
            dropped += 1
            continue
        bars[s] = float(c)
    return bars, dropped


def _candle_tuple(r):
    # (bid_c, ask_c, volume)
    return (r[0], r[1], r[2])


def load_markets(stats: Counter):
    markets = {}
    candles = defaultdict(dict)
    conflicts = defaultdict(set)
    bad = set()
    for f in DB_FILES:
        if not f.exists():
            continue
        con = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
        for t, o, c, res in con.execute(
                "select ticker, open_ts, close_ts, result from market where series=?", (SERIES,)):
            row = (int(o), int(c), res)
            if t in markets and markets[t] != row:
                bad.add(t)
            markets.setdefault(t, row)
        for t, e, bid, ask, vol in con.execute(
                "select ticker, end_ts, bid_c, ask_c, volume from candle where series=?", (SERIES,)):
            e = int(e)
            val = (bid, ask, vol)
            prev = candles[t].get(e)
            if prev is not None and prev != val:
                conflicts[t].add(e)
            candles[t].setdefault(e, val)
        con.close()
    for t in bad:
        markets.pop(t, None)
    n_conf = 0
    for t, es in conflicts.items():
        for e in es:
            candles[t].pop(e, None)
            n_conf += 1
    stats["tickers_dropped_row_mismatch"] = len(bad)
    stats["candles_dropped_conflict"] = n_conf
    return markets, candles


def universe(markets, bars):
    last_end = max(bars) + 60
    out = []
    for t, (o, c, res) in markets.items():
        if res not in ("yes", "no"):
            continue
        if UNIVERSE_START <= c <= last_end:
            out.append((c, t, o, res))
    out.sort()
    n = len(out)
    i1, i2 = n // 3, 2 * n // 3
    win = {}
    for i, (c, t, o, res) in enumerate(out):
        win[t] = "discovery" if i < i1 else ("validation" if i < i2 else "holdout")
    return out, win


# ---------------------------------------------------------------- model

def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def model_p_yes(bars, o, c, d_ts):
    """p_model(YES) or (None, reason). Reads only bars starting <= d_ts - 120."""
    last = d_ts - LAST_BAR_LAG
    for s in range(o - 120, o + 121, 60):
        if s not in bars:
            return None, "missing_bar_near_open"
    for s in (d_ts - 180, d_ts - 120):
        if s not in bars:
            return None, "missing_bar_near_decision"
    slots = range(last - (SIGMA_SLOTS - 1) * 60, last + 1, 60)
    present = [s for s in slots if s in bars]
    if len(present) < SIGMA_MIN_BARS:
        return None, "few_sigma_bars"
    changes = [bars[s] - bars[s - 60] for s in present if (s - 60) in bars and (s - 60) >= slots[0]]
    if len(changes) < 2:
        return None, "few_sigma_bars"
    first = min(slots[0], o - 120)
    seq = [s for s in range(first, last + 1, 60) if s in bars]
    for a, b in zip(seq, seq[1:]):
        if abs(bars[b] / bars[a] - 1.0) > MAX_MOVE:
            return None, "big_move"
    m = sum(changes) / len(changes)
    var = sum((x - m) ** 2 for x in changes) / (len(changes) - 1)
    sigma = math.sqrt(var)
    if not sigma > 0:
        return None, "sigma_zero"
    d = bars[last] - bars[o - 60]
    tau = (c - d_ts) / 60.0
    return phi(d / (sigma * math.sqrt(tau))), None


def side_asks(candle):
    """{'yes': ask or None, 'no': ask or None}, plus volume."""
    bid, ask, vol = candle
    ya = ask if (ask is not None and 0 < ask < 0.99) else None
    na = None
    if bid is not None and bid > 0:
        x = 1.0 - bid
        if x < 0.99:
            na = x
    return {"yes": ya, "no": na}, vol


# ---------------------------------------------------------------- trades

def build(bars, markets, candles, stats):
    """Returns {set name: [trade dict]} over the whole universe, and the windows."""
    uni, win = universe(markets, bars)
    stats["universe_markets"] = len(uni)
    for w in ("discovery", "validation", "holdout"):
        stats[f"universe_{w}"] = sum(1 for v in win.values() if v == w)
    sets = defaultdict(list)
    for c, t, o, res in uni:
        cs = candles.get(t, {})
        for look, lead in LOOKS.items():
            d_ts = c - lead
            sig = cs.get(d_ts)
            if sig is None:
                stats[f"skip{look}_missing_kalshi_candle"] += 1
                continue
            asks, vol = side_asks(sig)
            nxt = cs.get(d_ts + 60)

            def trade(side):
                a = asks[side]
                nx_ask = nx_vol = None
                if nxt is not None:
                    na, nv = side_asks(nxt)
                    nx_ask, nx_vol = na[side], nv
                return {"ticker": t, "close": c, "window": win[t], "side": side,
                        "won": res == side, "ask": a, "vol": vol,
                        "next_ask": nx_ask, "next_vol": nx_vol}

            # L1 parent on everything with a candle (A10)
            band = [s for s in ("yes", "no") if asks[s] is not None
                    and L1_LO - EPS <= asks[s] <= L1_HI + EPS]
            if len(band) == 2:
                stats[f"skip{look}_l1_crossed"] += 1
                band = []
            if band:
                sets[f"L1 parent {look} (all with candle)"].append(trade(band[0]))

            if asks["yes"] is None and asks["no"] is None:
                stats[f"skip{look}_no_quote"] += 1
                continue
            p_yes, why = model_p_yes(bars, o, c, d_ts)
            if p_yes is None:
                stats[f"skip{look}_{why}"] += 1
                continue
            stats[f"scored{look}"] += 1
            p = {"yes": p_yes, "no": 1.0 - p_yes}

            passing = [s for s in ("yes", "no") if asks[s] is not None
                       and S_ASK_LO - EPS <= asks[s] <= S_ASK_HI + EPS
                       and p[s] - asks[s] >= EDGE_MIN - EPS]
            if len(passing) == 2:
                stats[f"skip{look}_S_crossed"] += 1
            elif passing:
                sets[f"S{look}"].append(trade(passing[0]))

            if band:
                s = band[0]
                tr = trade(s)
                sets[f"L1 parent {look} (scored set)"].append(tr)
                if p[s] >= asks[s] - EPS:
                    sets[f"F{look} kept"].append(tr)
                else:
                    sets[f"F{look} removed"].append(tr)
    return sets, win


# ---------------------------------------------------------------- scoring

def order_pnl(ask, won, contracts, mult):
    fee = taker_fee(ask, contracts, mult)
    return ((1.0 - ask) if won else -ask) * contracts - fee


def pf(pnls):
    g = sum(x for x in pnls if x > 0)
    l = -sum(x for x in pnls if x < 0)
    if l == 0:
        return float("inf") if g > 0 else float("nan")
    return g / l


def day_of(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()


def clustered_z(trades, pnls):
    n = len(pnls)
    if n < 2:
        return float("nan")
    mean = sum(pnls) / n
    by = defaultdict(lambda: [0.0, 0])
    for tr, x in zip(trades, pnls):
        b = by[day_of(tr["close"])]
        b[0] += x
        b[1] += 1
    g = len(by)
    if g < 2:
        return float("nan")
    ss = sum((s - k * mean) ** 2 for s, k in by.values()) * g / (g - 1)
    if ss <= 0:
        return float("nan")
    return sum(pnls) / math.sqrt(ss)


def fills(trades, variant):
    out = []
    for tr in trades:
        if variant == "primary":
            a, v = tr["ask"], tr["vol"]
        elif variant == "nozero":
            a, v = tr["ask"], tr["vol"]
            if not v:
                continue
        else:  # next candle
            a, v = tr["next_ask"], tr["next_vol"]
            if a is None:
                continue
        out.append((tr, a))
    return out


def score(trades):
    prim = fills(trades, "primary")
    t1 = [tr for tr, _ in prim]
    p1 = [order_pnl(a, tr["won"], 1, 1.0) for tr, a in prim]
    p10 = [order_pnl(a, tr["won"], 10, 1.0) for tr, a in prim]
    p1f = [order_pnl(a, tr["won"], 1, 1.2) for tr, a in prim]
    p10f = [order_pnl(a, tr["won"], 10, 1.2) for tr, a in prim]
    nz = fills(trades, "nozero")
    nx = fills(trades, "next")
    pnz = [order_pnl(a, tr["won"], 1, 1.0) for tr, a in nz]
    pnx = [order_pnl(a, tr["won"], 1, 1.0) for tr, a in nx]
    n = len(p1)
    return {
        "n": n,
        "days": len({day_of(tr["close"]) for tr in t1}),
        "pf1": pf(p1), "pf10": pf(p10),
        "cpc1": (100 * sum(p1) / n) if n else float("nan"),
        "cpc10": (100 * sum(p10) / (10 * n)) if n else float("nan"),
        "z": clustered_z(t1, p1),
        "pf1_fee12": pf(p1f), "pf10_fee12": pf(p10f),
        "n_nozero": len(pnz), "pf_nozero": pf(pnz),
        "n_next": len(pnx), "pf_next": pf(pnx),
        "z_next": clustered_z([tr for tr, _ in nx], pnx),
    }


SET_ORDER = ["S10", "S6", "L1 parent 10 (scored set)", "F10 kept", "F10 removed",
             "L1 parent 6 (scored set)", "F6 kept", "F6 removed",
             "L1 parent 10 (all with candle)", "L1 parent 6 (all with candle)"]


def fmt(x, nd=2):
    if isinstance(x, float):
        if math.isnan(x):
            return "nan"
        if math.isinf(x):
            return "inf"
        return f"{x:.{nd}f}"
    return str(x)


def report(sets, windows):
    for w in windows:
        print(f"\n=== {w} ===")
        print("set | n | days | PF1 | PF10 | c/contract(1) | c/contract(10) | z(day) | "
              "PF1 fee1.2 | PF10 fee1.2 | n nozero | PF nozero | n next | PF next | z next")
        for name in SET_ORDER:
            r = score([tr for tr in sets.get(name, []) if tr["window"] == w])
            print(" | ".join([name, fmt(r["n"]), fmt(r["days"]), fmt(r["pf1"]), fmt(r["pf10"]),
                              fmt(r["cpc1"]), fmt(r["cpc10"]), fmt(r["z"]),
                              fmt(r["pf1_fee12"]), fmt(r["pf10_fee12"]),
                              fmt(r["n_nozero"]), fmt(r["pf_nozero"]),
                              fmt(r["n_next"]), fmt(r["pf_next"]), fmt(r["z_next"])]))


def counts(sets, stats, bar_drop, n_bars):
    """Counts only: no P/L, PF, win or z figure."""
    print(f"gold bars kept {n_bars}, dropped (incomplete / bad) {bar_drop}")
    for k in sorted(stats):
        print(f"{k}: {stats[k]}")
    print("\ntrades per set per window (counts only):")
    for name in SET_ORDER:
        c = Counter(tr["window"] for tr in sets.get(name, []))
        nz = Counter(tr["window"] for tr in sets.get(name, []) if tr["vol"])
        nx = Counter(tr["window"] for tr in sets.get(name, []) if tr["next_ask"] is not None)
        print(f"{name}: " + ", ".join(
            f"{w} {c[w]} (nozero {nz[w]}, next-fill {nx[w]})"
            for w in ("discovery", "validation", "holdout")))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "run"
    stats = Counter()
    bars, bar_drop = load_bars()
    markets, candles = load_markets(stats)
    stats["markets_loaded"] = len(markets)
    sets, win = build(bars, markets, candles, stats)
    if cmd == "run":
        report(sets, ["discovery", "validation"])
    elif cmd == "holdout":
        report(sets, ["holdout"])
    elif cmd == "counts":
        counts(sets, stats, bar_drop, len(bars))
    else:
        print("usage: python -m scalper.goldfv1_aud run|holdout|counts")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
