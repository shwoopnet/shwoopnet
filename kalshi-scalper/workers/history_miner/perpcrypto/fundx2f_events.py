"""fundx2f_events.py: FORWARD scorer plugin for FUNDX2-F (History Miner, 2026-11-17). Card FUNDX2F_CARD_NOV17.md. Pure functions, no I/O.
Same rules as fundx2_events.py 67d049b5 (entry = the first row strictly after the print, signal row = the last row at or before it, one position per ticker, funding strictly between entry and exit), with TWO differences:
the cut points come from the committed FUNDX2_THRESHOLDS.json (SEARCH-only, not recomputed here), and the trading window is 2026-11-17T00:00Z to before 2026-12-15T00:00Z."""
import calendar, collections
import perps_crypto_events as E
import fundx2_events as F
T = lambda *a: calendar.timegm(a + (0,) * (6 - len(a)))
FWD_START, FWD_END = T(2026, 11, 17), T(2026, 12, 15)
THRESHOLDS_SHA256 = "384aeec937440e88fcba7f79170923249dcedd1383bfacd817cd91d6a4239fd6"
FUNDX2F_CELLS = F.FUNDX2_CELLS


def cuts_from(doc, ticker, q):
    """doc = the committed FUNDX2_THRESHOLDS.json; q is 0.05 or 0.10. -> (lower, upper, n) or None (no threshold)."""
    c = doc["cuts"].get(ticker, {}).get("%g" % (q * 100))
    return (c["lower"], c["upper"], c["search_n"]) if c and c["has_threshold"] else None


def fundx2f_trades(rows_by_ticker, prints_by_ticker, doc, cell, cnt=None):
    q, di, h = cell; out = []; skips = cnt if cnt is not None else collections.Counter()
    if not prints_by_ticker:
        raise SystemExit("REFUSED: no labelled funding prints")
    for tk, rows in rows_by_ticker.items():
        pr = sorted(prints_by_ticker.get(tk, [])); cuts = cuts_from(doc, tk, q); busy_until = 0
        if cuts is None:
            skips["ticker has no committed threshold"] += 1; continue
        for ts, rate in pr:
            if not FWD_START <= ts < FWD_END:
                continue
            ext = F.extreme(rate, cuts)
            if not ext:
                continue
            i = max((j for j, r in enumerate(rows) if r[0] <= ts), default=None)
            if i is None or ts < busy_until or i + 1 >= len(rows) or rows[i + 1][0] <= ts:
                skips["no row at or before the print / busy / no row strictly after"] += 1; continue
            tr = E.execute(rows, i, -ext if di == "fade" else ext, h)
            if isinstance(tr, str):
                skips[tr] += 1; continue
            fund = sum(r for t, r in pr if tr["entry_ts"] < t < tr["exit_ts"])
            out.append({"ticker": tk, "signal_ts": ts, "trade": tr, "funding": fund}); busy_until = tr["exit_ts"]
    return out
