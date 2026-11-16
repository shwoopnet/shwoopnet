"""perps_crypto_events.py: scorer plugin for PERPCRYPTO1 (History Miner, Nov 16, 2026). Card PERPCRYPTO1_CARD_NOV16.md. Pure functions, no I/O. Upper bound, not fill-checked.
Rows are (ts, bid, ask, price, reference_price, funding_cap) at HOURLY spacing, one list per ticker. A signal is made by a row; the ENTRY is the NEXT row's far touch; the hold counts from the entry row; the exit is the near touch of the first row at least H hours after the entry row."""
import collections, math, statistics, time
FEE_TAKER, FEE_MAKER = 0.0012, 0.0005                  # per side, of notional, ASSUMED (Kalshi's fee page unread)
HAIRCUTS = (0.0002, 0.0005)                            # per fill, relative: the perps convention
MAINT = 0.045                                          # maintenance margin, of notional, ASSUMED (gold measured 4.47 percent)
LMAX = {"KXBTCPERP": 15.4, "KXETHPERP": 10.5, "KXXRPPERP": 5.4, "KXSOLPERP": 3.0828, "KXDOGEPERP": 2.9405, "KXHYPEPERP": 2.2534}   # page max for the first three; API estimate for the last three
FRACTIONS = (0.10, 0.25, 0.50)
MAXGAP_NEXT, TOL_EXIT = 5400, 1800
BASIS_CELLS = [(th, mode, h) for th in (5, 10) for mode in ("converge", "follow") for h in (1, 4)]
FUNDX_CELLS = [(trig, di, h) for trig in ("decile", "clamp") for di in ("fade", "follow") for h in (8, 24)]
GATE_DAYS, RATE_GATE = 7, 3.0


def two(b, a):
    return b is not None and a is not None and 0 < b <= a


def pf(xs):
    g = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 else g / l


def liquidation_distance(ticker, f):
    lev = f * LMAX[ticker]
    return 1 / lev - MAINT, lev


def basis(row):
    """b = (price - reference_price) / reference_price, or None when either is missing."""
    _t, _b, _a, p, ref, _c = row
    return None if p is None or ref is None or ref <= 0 else (p - ref) / ref


def execute(rows, i, side, hold_h):
    """side +1 long, -1 short. Signal row i; entry = row i+1's far touch; exit = near touch of the first row at least hold_h hours after the entry row. -> dict or a skip reason string."""
    if i + 1 >= len(rows):
        return "no next row"
    r0, r1 = rows[i], rows[i + 1]
    if r1[0] - r0[0] > MAXGAP_NEXT:
        return "next row too far"
    if not two(r1[1], r1[2]):
        return "next row not two-sided"
    entry = r1[2] if side > 0 else r1[1]
    target = r1[0] + hold_h * 3600
    k = next((j for j in range(i + 1, len(rows)) if rows[j][0] >= target), None)
    if k is None or rows[k][0] - target > TOL_EXIT:
        return "no exit row"
    if not two(rows[k][1], rows[k][2]):
        return "exit row not two-sided"
    exit_px = rows[k][1] if side > 0 else rows[k][2]
    adv = 0.0
    for j in range(i + 1, k + 1):
        b, a = rows[j][1], rows[j][2]
        if side > 0 and b is not None:
            adv = max(adv, (entry - b) / entry)
        if side < 0 and a is not None:
            adv = max(adv, (a - entry) / entry)
    return {"entry_ts": r1[0], "exit_ts": rows[k][0], "entry": entry, "exit": exit_px, "side": side, "adverse": adv, "k": k}


def net(tr, fee, haircut, funding=0.0):
    """Return on notional: the move in the position's favour, less a fee and a haircut on each of the two fills, less funding paid (positive = paid by longs, sign ASSUMED)."""
    return tr["side"] * (tr["exit"] - tr["entry"]) / tr["entry"] - 2 * fee - 2 * haircut - tr["side"] * funding


def margin_return(tr, ticker, f, ret):
    dist, lev = liquidation_distance(ticker, f)
    return (-1.0, True) if tr["adverse"] >= dist else (ret * lev, False)


def basis_trades(rows_by_ticker, cell, cnt=None):
    """One position per ticker at a time. -> list of dicts with ticker, signal_ts, trade."""
    th, mode, h = cell; out = []; skips = cnt if cnt is not None else collections.Counter()
    for tk, rows in rows_by_ticker.items():
        i = 0
        while i < len(rows) - 1:
            b = basis(rows[i])
            if b is None:
                skips["price or reference_price missing"] += 1; i += 1; continue
            if abs(b) * 1e4 < th - 1e-9:
                i += 1; continue
            side = (-1 if b > 0 else 1) if mode == "converge" else (1 if b > 0 else -1)
            tr = execute(rows, i, side, h)
            if isinstance(tr, str):
                skips[tr] += 1; i += 1; continue
            out.append({"ticker": tk, "signal_ts": rows[i][0], "trade": tr}); i = tr["k"]
    return out


def funding_extreme(earlier, rate, cap, kind):
    """+1 if longs pay at an extreme, -1 if shorts pay, 0 if none. decile: needs at least 60 EARLIER prints, top or bottom tenth of them (nearest rank); clamp: |rate| >= cap."""
    if kind == "clamp":
        return 0 if cap is None or abs(rate) < cap - 1e-12 else (1 if rate > 0 else -1)
    if len(earlier) < 60:
        return 0
    s = sorted(earlier); hi, lo = s[math.ceil(0.9 * len(s)) - 1], s[math.ceil(0.1 * len(s)) - 1]
    return 1 if rate >= hi and rate > 0 else (-1 if rate <= lo and rate < 0 else 0)


def fundx_trades(rows_by_ticker, prints_by_ticker, cell, cnt=None):
    """prints_by_ticker: LABELLED prints only [(ts, rate)] sorted. The signal row is the first row at or after the print time; the ENTRY is the NEXT row after it (a quote at the print instant is never used), then as execute()."""
    trig, di, h = cell; out = []; skips = cnt if cnt is not None else collections.Counter()
    if not prints_by_ticker:
        raise SystemExit("REFUSED: no labelled funding prints")
    for tk, rows in rows_by_ticker.items():
        pr = prints_by_ticker.get(tk, []); busy_until = 0
        for n, (ts, rate) in enumerate(pr):
            cap = next((r[5] for r in rows if r[0] >= ts and r[5] is not None), None)
            ext = funding_extreme([x[1] for x in pr[:n]], rate, cap, trig)
            if not ext:
                continue
            i = next((j for j, r in enumerate(rows) if r[0] >= ts), None)
            if i is None or rows[i][0] <= busy_until:
                skips["no row at the print / busy"] += 1; continue
            side = -ext if di == "fade" else ext
            tr = execute(rows, i, side, h)
            if isinstance(tr, str):
                skips[tr] += 1; continue
            fund = sum(r for t, r in pr if tr["entry_ts"] < t <= tr["exit_ts"])
            out.append({"ticker": tk, "signal_ts": ts, "trade": tr, "funding": fund}); busy_until = tr["exit_ts"]
    return out


def summarise(trades, ticker_of=lambda x: x["ticker"]):
    """PF at taker with each haircut, halves by signal time, gate counts; margin returns and liquidation shares at 10, 25 and 50 percent of the maximum. Funding is booked when the trade carries it."""
    tr = sorted(trades, key=lambda x: x["signal_ts"]); res = {"n": len(tr)}
    for hc in HAIRCUTS:
        xs = [net(t["trade"], FEE_TAKER, hc, t.get("funding", 0.0)) for t in tr]; half = len(xs) // 2
        res["taker_h%d" % round(hc * 1e4)] = {"pf": pf(xs) if xs else None, "half1": pf(xs[:half]) if half else None, "half2": pf(xs[half:]) if xs else None}
    xm = [net(t["trade"], FEE_MAKER, HAIRCUTS[0], t.get("funding", 0.0)) for t in tr]; res["maker_h2"] = {"pf": pf(xm) if xm else None}
    res["margin"] = {}
    for f in FRACTIONS:
        rets, liq = [], 0
        for t in tr:
            r, l = margin_return(t["trade"], ticker_of(t), f, net(t["trade"], FEE_TAKER, HAIRCUTS[0], t.get("funding", 0.0)))
            rets.append(r); liq += l
        res["margin"]["%d" % round(f * 100)] = {"mean_margin_return": (sum(rets) / len(rets)) if rets else None, "liquidated_share": (liq / len(tr)) if tr else None}
    return res


def day(ts):
    return time.strftime("%Y-%m-%d", time.gmtime(ts))


def gate(trades_by_cell):
    """Fixed ONCE on the first 7 distinct signal days (decision counts only): {cell: {rate, dropped}} or None under 7 days."""
    days = sorted({day(t["signal_ts"]) for ts in trades_by_cell.values() for t in ts})
    if len(days) < GATE_DAYS:
        return None
    first = set(days[:GATE_DAYS])
    return {c: {"rate": sum(1 for t in ts if day(t["signal_ts"]) in first) / GATE_DAYS, "dropped": sum(1 for t in ts if day(t["signal_ts"]) in first) / GATE_DAYS < RATE_GATE} for c, ts in trades_by_cell.items()}
