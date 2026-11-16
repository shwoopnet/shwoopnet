"""fundx2_events.py: scorer plugin for FUNDX2 (History Miner, Nov 16, 2026). Card FUNDX2_CARD_NOV16.md. Pure functions, no I/O. Reuses execute(), net(), summarise() of perps_crypto_events.py (clean, 8427becd) unchanged.
The cut points come from SEARCH funding prints ONLY; a print after SEARCH_END never enters them."""
import calendar, collections, math
import perps_crypto_events as E
T = lambda *a: calendar.timegm(a + (0,) * (6 - len(a)))
SEARCH_START, SEARCH_END, VALIDATE_END = T(2026, 6, 3), T(2026, 9, 15), T(2026, 11, 17)
QS = (0.05, 0.10)
MIN_PRINTS = 120
FUNDX2_CELLS = [(q, di, h) for q in QS for di in ("fade", "follow") for h in (8, 24)]


def cut_points(prints, q):
    """prints: [(ts, rate)] of ONE ticker, any period. Uses only prints with SEARCH_START <= ts < SEARCH_END. -> (lower, upper, n) or None when under MIN_PRINTS.
    n = number of SEARCH prints; sorted rates s; lower = s[ceil(q n) - 1]; upper = s[n - ceil(q n)]."""
    s = sorted(r for t, r in prints if SEARCH_START <= t < SEARCH_END and r is not None)
    n = len(s)
    if n < MIN_PRINTS:
        return None
    k = math.ceil(q * n - 1e-12)
    return s[k - 1], s[n - k], n


def extreme(rate, cuts):
    """+1 longs pay (rate at or above the upper cut and above 0), -1 shorts pay (at or below the lower cut and below 0), else 0."""
    if cuts is None or rate is None:
        return 0
    lo, hi, _ = cuts
    return 1 if rate >= hi and rate > 0 else (-1 if rate <= lo and rate < 0 else 0)


def fundx2_trades(rows_by_ticker, prints_by_ticker, cell, window="validate", cnt=None):
    """cell = (q, side, hold_h). window 'validate' trades only prints in [SEARCH_END, VALIDATE_END); 'search' only prints in [SEARCH_START, SEARCH_END) (printed apart, never counted toward a pass).
    The signal row is the first row at or after the print; ENTRY is the NEXT row (execute()). One position per ticker. Funding booked on prints after the entry up to the exit."""
    q, di, h = cell; out = []; skips = cnt if cnt is not None else collections.Counter()
    if not prints_by_ticker:
        raise SystemExit("REFUSED: no labelled funding prints")
    lo_t, hi_t = (SEARCH_END, VALIDATE_END) if window == "validate" else (SEARCH_START, SEARCH_END)
    for tk, rows in rows_by_ticker.items():
        pr = sorted(prints_by_ticker.get(tk, [])); cuts = cut_points(pr, q); busy_until = 0
        if cuts is None:
            skips["ticker has under %d SEARCH prints (no threshold)" % MIN_PRINTS] += 1; continue
        for ts, rate in pr:
            if not lo_t <= ts < hi_t:
                continue
            ext = extreme(rate, cuts)
            if not ext:
                continue
            i = next((j for j, r in enumerate(rows) if r[0] >= ts), None)
            if i is None or rows[i][0] <= busy_until:
                skips["no row at the print / busy"] += 1; continue
            tr = E.execute(rows, i, -ext if di == "fade" else ext, h)
            if isinstance(tr, str):
                skips[tr] += 1; continue
            fund = sum(r for t, r in pr if tr["entry_ts"] < t <= tr["exit_ts"])
            out.append({"ticker": tk, "signal_ts": ts, "trade": tr, "funding": fund}); busy_until = tr["exit_ts"]
    return out
