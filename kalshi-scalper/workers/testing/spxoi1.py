#!/usr/bin/env python3
"""SPXOI1 shadow tools, tool 1 (Testing Desk, Nov 13, 2026). Research only: reads files it is given, sends nothing. INVENTED rows only in tests (SPXOI1_TOOLS_HAND_CASES.md, committed first).
  load_nc15(path)            NC15 book file -> {ticker: [poll]} in scorekit.r6_book shape with EXCHANGE time (frozen NC15 sheet, lane (u)); the layout is ASSUMED to be the R6 layout (not verified on a real NC15 file).
  signal(polls, close_ts, oi_now, oi_prev, T, limit_add)    the SPXOI1 rule at one market: T and limit_add are REQUIRED arguments, never defaults.
  fill_check(polls, sig_index, limit)   NC15 fill check: next poll within 6 s; both polls offer 10 at or under the limit; fill = the higher walked price.
  spxoi1_shadow(polls_by_ticker, cs, T, limit_add)   the shadow dict liveshadow.compare reads.
"""
import bisect, csv, gzip, math, os, statistics as st, sys, calendar, time
from email.utils import parsedate_to_datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

TOL = 1e-9
BAND_LO, BAND_HI = 0.08, 0.50
LOOK_FROM_S, LOOK_TO_S = 180, 120          # seconds before the close
OI_RECENT_S, OI_EARLIER_S = 180, 360       # the candle ending close - 180 s minus the one ending close - 360 s
SIZE = 10
SECOND_LOOK_MAX_S = 6.0
OFFSET_ROWS = 120


def _f(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _header_s(h):
    try:
        return parsedate_to_datetime(h).timestamp()
    except (TypeError, ValueError, IndexError):
        return None


def _levels(r, pre):
    out = []
    for i in range(1, 6):
        p, z = _f(r.get("%s_px_%d" % (pre, i))), _f(r.get("%s_sz_%d" % (pre, i)))
        if p is not None and z is not None:
            out.append((p, z))
    return out


def load_rows(rows):
    """rows: dicts with the book columns in the run's order. Rows with no readable receive time are dropped, the rest sorted STABLY by receive time; the offset of row i is the median of the last 120
    readable-header values up to and including row i (an unreadable header takes the median of the earlier readable ones and adds none); no offset at all = no exchange time = the row is skipped."""
    keep = []
    for r in rows:
        t = _f(r.get("t_recv_ms"))
        if t is not None:
            keep.append((t, r))
    keep.sort(key=lambda x: x[0])          # stable: rows of one instant keep the run's order
    hist, out = [], {}
    for t, r in keep:
        h = _header_s(r.get("server_date_header"))
        if h is not None:
            hist.append(h + 0.5 - t / 1000.0)
        if not hist:
            continue
        off = st.median(hist[-OFFSET_ROWS:])
        close = r.get("close_time")
        close_ts = k.iso(close) if isinstance(close, str) else _f(close)
        out.setdefault(r.get("ticker"), []).append({"t": t / 1000.0 + off, "recv": t / 1000.0, "yes_bids": _levels(r, "yes_bid"), "no_bids": _levels(r, "no_bid"), "close": close_ts})
    return {tk: sorted(v, key=lambda p: p["t"]) for tk, v in out.items()}


def load_nc15(path):
    op = gzip.open if str(path).endswith(".gz") else open
    with op(path, "rt", newline="") as fh:
        return load_rows(list(csv.DictReader(fh)))


def ask_of(poll, side):
    """The ask of the implied side: YES buy = 1 - best NO bid; NO buy = 1 - best YES bid. None if that side of the book is empty."""
    lv = poll["no_bids"] if side == "yes" else poll["yes_bids"]
    return None if not lv else 1.0 - max(p for p, _ in lv)


def cheaper(poll):
    ya, na = ask_of(poll, "yes"), ask_of(poll, "no")
    if ya is None or na is None:
        return None
    return ("yes", ya) if ya <= na + TOL else ("no", na)          # lower ask, tie to YES


def oi_rise(cs_ticker, close_ts):
    by = {c["ts"]: c for c in (cs_ticker or [])}
    a, b = by.get(close_ts - OI_RECENT_S), by.get(close_ts - OI_EARLIER_S)
    if a is None or b is None or a.get("oi") is None or b.get("oi") is None:
        return None
    return a["oi"] - b["oi"]


def signal(polls, close_ts, oi_now, oi_prev, T, limit_add):
    """-> ('signal', index into polls, side, ask, limit) | ('no_trade', reason) | ('no_data', reason). T and limit_add have no defaults."""
    if oi_now is None or oi_prev is None:
        return ("no_data", "no open interest")
    if not (oi_now - oi_prev >= T - TOL):
        return ("no_trade", "oi rise under T")
    cand = [i for i, p in enumerate(polls) if close_ts - LOOK_FROM_S - TOL <= p["t"] <= close_ts - LOOK_TO_S + TOL]
    if not cand:
        return ("no_data", "no poll in window")
    for i in cand:
        c = cheaper(polls[i])
        if c is None:
            continue
        if BAND_LO - TOL <= c[1] <= BAND_HI + TOL:
            return ("signal", i, c[0], c[1], c[1] + limit_add)
    return ("no_trade", "cheaper side outside 0.08 to 0.50")


def ladder(poll, side):
    lv = poll["no_bids"] if side == "yes" else poll["yes_bids"]
    return sorted(((1.0 - p, z) for p, z in lv), key=lambda x: x[0])


def offers(poll, side, limit, size=SIZE):
    return sum(z for a, z in ladder(poll, side) if a <= limit + TOL) >= size - TOL


def walked(poll, side, size=SIZE):
    """Size-weighted average ask of the first `size` contracts of the ladder (None if the ladder holds fewer)."""
    need, cost = float(size), 0.0
    for a, z in ladder(poll, side):
        take = min(need, z); cost += take * a; need -= take
        if need <= 1e-12:
            return cost / size
    return None


def fill_check(polls, i, side, limit):
    """-> ('filled', fill price) | ('miss', why) | ('not_fill_checked', why). The second poll is the NEXT poll of the same ticker, at most 6 s after the signal poll."""
    if i + 1 >= len(polls) or polls[i + 1]["t"] - polls[i]["t"] > SECOND_LOOK_MAX_S + TOL:
        return ("not_fill_checked", "no second poll within 6 s")
    a, b = polls[i], polls[i + 1]
    if not (offers(a, side, limit) and offers(b, side, limit)):
        return ("miss", "10 contracts not offered at or under the limit on both polls")
    return ("filled", max(walked(a, side), walked(b, side)))


def fee_up_order(p, contracts=SIZE):
    return math.ceil(0.07 * contracts * p * (1 - p) * 100 - 1e-9) / 100


def cash_cents(p, side, result, contracts=SIZE):
    """Whole cents, worse side (lane (g)): cents = floor(100 x cash + 1e-6). A void (or any result but yes/no) is price refunded, fee kept."""
    fee = fee_up_order(p, contracts)
    if result in ("yes", "no"):
        cash = contracts * ((1.0 if result == side else 0.0) - p) - fee
    else:
        cash = -fee
    return int(math.floor(100.0 * cash + 1e-6))


def spxoi1_shadow(polls_by_ticker, cs, T, limit_add):
    """{ticker: ('trade', side, ask, {...}) | ('no_trade', reason) | ('no_data', reason)} for liveshadow.compare. The close of a ticker is its polls' close column (exchange time)."""
    out = {}
    for tk, polls in polls_by_ticker.items():
        closes = [p["close"] for p in polls if p.get("close") is not None]
        if not closes:
            out[tk] = ("no_data", "no close time"); continue
        close = closes[0]
        ct = cs.get(tk) or []
        by = {c["ts"]: c for c in ct}
        a, b = by.get(close - OI_RECENT_S), by.get(close - OI_EARLIER_S)
        r = signal(polls, close, None if a is None else a.get("oi"), None if b is None else b.get("oi"), T, limit_add)
        out[tk] = ("trade", r[2], r[3], {"limit": r[4], "t": polls[r[1]]["t"]}) if r[0] == "signal" else r
    return out


if __name__ == "__main__":
    print(__doc__)
