"""GOLDFILL: a fill-probability model for L1's gold entry (KXGOLD15M), built from quotes and trades only. Research only.

No outcome is read anywhere in this file: the market table is read for ticker and close time only (never `result`),
quote-recorder `results.csv.gz` files are never opened, and R6 coverage rows are read with the `result` field dropped.
This keeps the R6 windows clean for L1Q1's registered read (workers/R6T_REGISTRATION.md).

Usage (from kalshi-scalper/, PYTHONPATH=src):
  python -m scalper.goldfill fetch            public trade tape for every historical gold L1 signal (T-365 s to T-110 s) and for
                                              every quote-recorder gold window (T-155 s to T-25 s); cached in data/goldfill/
  python -m scalper.goldfill model QDIR       QDIR = an extracted copy of the quote-data branch (quotes/, book15r6/); prints the tables

Queue rule (MM1S / Q2B, the conservative one): a new resting buy joins BEHIND all displayed size at its price; only trades
move it forward (cancellations never do); it fills only after it is live (1.0 s after the decision) by (a) taker volume AT
its price beyond the size ahead, partial fills kept, or (b) a print strictly THROUGH its price, or a recorded quote of our
side's ask at or through its price, which fills the whole remainder at OUR price. A quote moving away is not a fill.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import sqlite3
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .paths import DATA_DIR

SERIES = "KXGOLD15M"
LO, HI = 0.88, 0.97
LEFT_S = 360                  # L1's decision: the candle ending 6 minutes before the close
LIVE_S = 1.0                  # an order is live 1.0 s after the decision poll (Q2B / L1Q1's choice)
HORIZONS = (30, 60, 120, 240)
SIZES = (1, 10, 20)
SINCE = 1788220800            # 2026-09-01 00:00 UTC: the tape's retention was checked back to here (MM1S)
DBS = ("fresh", "five", "book", "l1b")
CACHE = DATA_DIR / "goldfill"
EPS = 1e-6
# Price choices for the bought side. ASK is a resting (not IOC) bid AT the ask; IN1C is 1c inside the ask; IN01 is one tick (0.1c)
# inside the ask; BID joins the best bid. A price at or below the bid joins (or sits under) the bid queue.
KINDS = ("ASK", "IN01", "IN1C", "BID")


def r4(x: float) -> float:
    return round(x + 0.0, 4)


def fee_cents(p: float, c: float) -> int:
    """Kalshi taker formula, rounded UP to the cent per order: 7% x C x p x (1-p)."""
    import math
    return int(math.ceil(round(7.0 * c * p * (1 - p), 6) - 1e-9)) if c > 0 else 0


# ---------------------------------------------------------------- historical signals (candles; no result column is read)

def hist_signals() -> list[dict]:
    seen, out = set(), []
    for name in DBS:
        path = DATA_DIR / f"{name}.sqlite"
        if not path.exists():
            continue
        db = sqlite3.connect(path)
        for tk, close in db.execute("select ticker, close_ts from market where series=? and close_ts>=?", (SERIES, SINCE)).fetchall():
            if tk in seen:
                continue
            cs = {r[0]: r[1:] for r in db.execute(
                "select end_ts, bid_c, ask_c, ask_l, bid_h from candle where ticker=? and end_ts between ? and ?", (tk, close - LEFT_S, close - 60))}
            c = cs.get(close - LEFT_S)
            if c is None or c[0] is None or c[1] is None:
                continue
            ya, na = r4(c[1]), r4(1 - c[0])
            if LO - EPS <= ya <= HI + EPS and ya >= na:
                side, ask, bid = "yes", ya, r4(c[0])
            elif LO - EPS <= na <= HI + EPS:
                side, ask, bid = "no", na, r4(1 - c[1])
            else:
                continue
            seen.add(tk)
            # side-ask lows of the later candles, stamped at the candle END (a quote at or through our price inside the
            # candle is only known to have happened by its end: conservative timing)
            qev = []
            for e in range(close - LEFT_S + 60, close - 119, 60):
                x = cs.get(e)
                if x is None:
                    continue
                low = x[2] if side == "yes" else (None if x[3] is None else r4(1 - x[3]))
                if low is not None:
                    qev.append((float(e), r4(low)))
            # side bid at T-120 (price path only, for the dip diagnostic; not an outcome)
            x = cs.get(close - 120)
            bid120 = None
            if x is not None and x[0] is not None and x[1] is not None:
                bid120 = r4(x[0]) if side == "yes" else r4(1 - x[1])
            out.append({"ticker": tk, "close": int(close), "side": side, "ask": ask, "bid": bid, "S": float(close - LEFT_S),
                        "qev": qev, "bid120": bid120})
    out.sort(key=lambda s: s["close"])
    return out


# ---------------------------------------------------------------- public trade tape

def _trades(tk: str, lo: int, hi: int) -> list[tuple]:
    from . import api
    cur, rows = None, []
    while True:
        p = {"ticker": tk, "limit": 1000, "min_ts": lo, "max_ts": hi}
        if cur:
            p["cursor"] = cur
        d = api._get("/markets/trades", p)
        for t in d.get("trades", []):
            rows.append((datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp(),
                         float(t["yes_price_dollars"]), float(t["count_fp"]), 1 if t["taker_outcome_side"] == "yes" else -1))
        cur = d.get("cursor")
        if not cur or not d.get("trades"):
            break
        time.sleep(0.6)
    rows.sort()
    return rows


def _load(name: str) -> dict:
    p = CACHE / name
    return json.loads(p.read_text()) if p.exists() else {}


def fetch(qdir: str | None = None) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    jobs = [("hist_tape.json", s["ticker"], s["close"] - 365, s["close"] - 110) for s in hist_signals()]
    if qdir:
        for w in qrec_windows(Path(qdir)):
            jobs.append(("qrec_tape.json", w["ticker"], w["close"] - 155, w["close"] - 25))
    stores = {n: _load(n) for n in {j[0] for j in jobs}}
    # recorder windows first, then history newest first: the rate limit is shared, so the most recent windows are fetched first
    todo = [j for j in jobs if j[1] not in stores[j[0]]]
    todo.sort(key=lambda j: (j[0] != "qrec_tape.json", -j[2]))
    print(f"goldfill fetch: {len(jobs)} windows, {len(todo)} to fetch", flush=True)
    for i, (name, tk, lo, hi) in enumerate(todo):
        stores[name][tk] = _trades(tk, lo, hi)
        time.sleep(0.6)
        if i % 25 == 0 or i == len(todo) - 1:
            (CACHE / name).write_text(json.dumps(stores[name]))
            print(f"  {i + 1}/{len(todo)}", flush=True)
    for name, st in stores.items():
        (CACHE / name).write_text(json.dumps(st))


# ---------------------------------------------------------------- the fill engine (side terms)

def side_events(side: str, trades: list) -> list[tuple]:
    """Trades in the bought side's terms: (t, side price, count, kind). kind "sell" = a taker selling our side into resting
    bids (for YES: taker_outcome_side no; for NO: taker_outcome_side yes); kind "buy" = a taker buying our side from asks."""
    out = []
    for t, y, n, s in trades:
        if side == "yes":
            out.append((t, r4(y), n, "sell" if s == -1 else "buy"))
        else:
            out.append((t, r4(1 - y), n, "sell" if s == 1 else "buy"))
    return out


def rest_fill(L: float, C: float, Q: float, live: float, ev: list, qev: list, end: float, take: tuple | None = None) -> dict:
    """A resting buy of C at side price L, live at `live`, queue ahead Q (float('inf') = never reaches the front by trades
    at its price). ev: side events (t, p, n, kind); qev: (t, side ask) quote observations after live; take: (filled now, at
    price) for a marketable order's immediate cross at the live poll. Returns the fill path: list of (t, qty, price)."""
    fills = []
    got = 0.0
    if take and take[0] > 0:
        q = min(C, take[0]); fills.append((live, q, take[1], "cross")); got = q
    ahead = Q
    stream = [(t, 0, p, n, k) for t, p, n, k in ev if live <= t <= end] + [(t, 1, a, 0.0, "q") for t, a in qev if live <= t <= end]
    stream.sort(key=lambda x: (x[0], x[1]))
    for t, kind, p, n, k in stream:
        if got >= C - 1e-9:
            break
        rest = C - got
        if kind == 1:                                   # our side's ask quoted at or through our price: level cleared
            if p <= L + EPS:
                fills.append((t, rest, L, "quote")); got = C
            continue
        if k == "sell":
            if p < L - EPS:                             # a print strictly through our bid
                fills.append((t, rest, L, "through")); got = C
            elif abs(p - L) <= EPS:
                use = n
                if ahead > 0:
                    eat = min(ahead, use); ahead -= eat; use -= eat
                if use > 0:
                    q = min(rest, use); fills.append((t, q, L, "at")); got += q
        else:                                           # a taker bought our side from an ask at or below our bid: that ask was at or through us
            if p <= L + EPS:
                fills.append((t, rest, L, "ask_lifted")); got = C
    return {"fills": fills}


def summarize_path(fills: list, live: float, C: float) -> dict:
    out = {}
    for h in HORIZONS:
        q = sum(f[1] for f in fills if f[0] <= live + h + 1e-9)
        out[h] = q
    full_t = None
    acc = 0.0
    for t, q, p, *_ in fills:
        acc += q
        if acc >= C - 1e-9:
            full_t = t; break
    out["full_t"] = full_t
    out["cost"] = sum(f[1] * f[2] for f in fills)
    out["qty"] = sum(f[1] for f in fills)
    out["mech"] = fills[-1][3] if fills else None
    return out


def limit_for(kind: str, ask: float, bid: float) -> float:
    if kind == "ASK":
        return ask
    if kind == "IN01":
        return r4(max(bid, ask - 0.001))
    if kind == "IN1C":
        return r4(ask - 0.01)
    return bid


# ---------------------------------------------------------------- historical model

def hist_model(sigs: list, tape: dict, Qbid: float | None) -> dict:
    """Qbid: queue ahead when our price equals the best bid (unknown in history): 0 = upper bound, inf = lower bound,
    a number = the measured recorder median. A price below the bid uses inf whatever Qbid is unless Qbid == 0."""
    res = {}
    for kind in KINDS:
        for C in SIZES:
            rows = []
            for s in sigs:
                tr = tape.get(s["ticker"])
                if tr is None:
                    continue
                L = limit_for(kind, s["ask"], s["bid"])
                if L > s["bid"] + EPS:
                    Q = 0.0
                elif abs(L - s["bid"]) <= EPS:
                    Q = Qbid
                else:
                    Q = 0.0 if Qbid == 0 else float("inf")
                live = s["S"] + LIVE_S
                ev = side_events(s["side"], tr)
                path = rest_fill(L, C, Q, live, ev, s["qev"], s["close"] - 119.0)
                sm = summarize_path(path["fills"], live, C)
                sm.update({"L": L, "ask": s["ask"], "bid": s["bid"], "close": s["close"], 
                           "bid120": s["bid120"], "notrade": not any(s["S"] <= t[0] <= s["close"] - 119 for t in tr)})
                rows.append(sm)
            res[(kind, C)] = rows
    return res


# ---------------------------------------------------------------- quote recorder (last 150 s, top of book only)

def _gz_rows(path: Path):
    with gzip.open(path, "rt", newline="") as f:
        yield from csv.DictReader(f)


def qrec_windows(qdir: Path) -> list[dict]:
    """Gold windows of the quote recorder (quotes/<date>/<HHMM>/quotes.csv.gz); results.csv.gz is never opened.
    Decision = the first poll of the window (about T-150 s); a signal if the bought side's ask is 0.88 to 0.97."""
    out = []
    for qf in sorted((qdir / "quotes").glob("*/*/quotes.csv.gz")):
        offs = []
        cf = qf.parent / "clock.csv.gz"
        if cf.exists():
            offs = [float(r["offset_ms"]) for r in _gz_rows(cf) if r.get("offset_ms") not in (None, "")]
        off = statistics.median(offs) / 1000.0 if offs else 0.0
        closes = {}
        cov = qf.parent / "coverage.csv.gz"
        if cov.exists():
            for r in _gz_rows(cov):
                if r["ticker"].startswith(SERIES):
                    closes[r["ticker"]] = datetime.fromisoformat(r["window_close_utc"].replace("Z", "+00:00")).timestamp()
        by = {}
        for r in _gz_rows(qf):
            if not r["ticker"].startswith(SERIES):
                continue
            try:
                b, a = float(r["yes_bid"]), float(r["yes_ask"])
                bs, as_ = float(r["bid_size"] or 0), float(r["ask_size"] or 0)
            except ValueError:
                continue
            by.setdefault(r["ticker"], []).append((int(r["t_recv_ms"]) / 1000.0 + off, r4(b), r4(a), bs, as_))
        for tk, polls in by.items():
            if tk not in closes:
                continue
            polls.sort()
            out.append({"ticker": tk, "close": int(closes[tk]), "polls": polls})
    out.sort(key=lambda w: w["close"])
    return out


def side_book(side: str, poll: tuple) -> tuple:
    """(side bid, size, side ask, size) from a top-of-book poll (t, yes_bid, yes_ask, bid_size, ask_size)."""
    _, b, a, bs, as_ = poll
    if side == "yes":
        return b, bs, a, as_
    return r4(1 - a), as_, r4(1 - b), bs


def qrec_model(wins: list, tape: dict) -> tuple[dict, dict]:
    res, info = {}, {"windows": len(wins), "signals": 0, "late_first_poll": 0, "no_tape": 0, "bid_sizes": [], "ask_sizes": [], "spreads": []}
    sigs = []
    for w in wins:
        p0 = w["polls"][0]
        if p0[0] > w["close"] - 140:                   # the first poll must be at or before T-140 s (fixed before any fill)
            info["late_first_poll"] += 1; continue
        b, a = p0[1], p0[2]
        if not (0 < b < a < 1):
            continue
        ya, na = a, r4(1 - b)
        side = "yes" if (LO - EPS <= ya <= HI + EPS and ya >= na) else ("no" if LO - EPS <= na <= HI + EPS else None)
        if side is None:
            continue
        if w["ticker"] not in tape:
            info["no_tape"] += 1; continue
        sb, sbs, sa, sas = side_book(side, p0)
        info["signals"] += 1; info["bid_sizes"].append(sbs); info["ask_sizes"].append(sas); info["spreads"].append(round(100 * (sa - sb), 2))
        sigs.append((w, side, sb, sbs, sa, sas))
    for kind in KINDS + ("IOC",):
        for C in SIZES:
            rows = []
            for w, side, sb, sbs, sa, sas in sigs:
                S = w["polls"][0][0]; live = S + LIVE_S
                end = min(live + max(HORIZONS), w["close"] - 20.0)
                lp = next((p for p in w["polls"] if p[0] >= live), None)
                if lp is None:
                    continue
                lb, lbs, la, las = side_book(side, lp)
                ev = side_events(side, tape[w["ticker"]])
                if kind == "IOC":                       # the bot's order: immediate-or-cancel, limit = the ask rounded up to the next cent
                    import math
                    lim = math.ceil(sa * 100 - 1e-9) / 100
                    q = min(C, las) if la <= lim + EPS else 0.0
                    fills = [(live, q, la, "cross")] if q > 0 else []
                    if 0 < q < C:
                        pass                            # deeper levels are not recorded: the rest is counted as not filled
                    sm = summarize_path(fills, live, C)
                    for h in HORIZONS:
                        sm[h] = q
                    sm.update({"ask": sa, "L": lim})
                    rows.append(sm); continue
                L = limit_for(kind, sa, sb)
                take = (las, la) if la <= L + EPS else None
                Q = (lbs if abs(lb - L) <= EPS else 0.0) if take is None else 0.0
                if take is None and L < lb - EPS:
                    Q = float("inf")                   # under the best bid: the deeper book is not recorded
                if take is None:
                    nxt = next((p for p in w["polls"] if p[0] > lp[0]), None)
                    if nxt is not None:
                        nb, nbs, _, _ = side_book(side, nxt)
                        if abs(nb - L) <= EPS:
                            Q = max(Q, nbs)
                qev = []
                for p in w["polls"]:
                    if p[0] > lp[0]:
                        _, _, xa, _ = side_book(side, p)
                        if 0 < xa < 1:
                            qev.append((p[0], xa))
                rem = C - (min(C, take[0]) if take else 0.0)
                path = rest_fill(L, C, Q, live, ev, qev, end, take=take) if rem > 0 or take else None
                sm = summarize_path(path["fills"], live, C)
                for h in HORIZONS:
                    if live + h > end + 1e-9:
                        sm[h] = None if h > 120 else sm[h]
                sm.update({"ask": sa, "L": L})
                rows.append(sm)
            res[(kind, C)] = rows
    return res, info


# ---------------------------------------------------------------- R6 (book15r6/: 5 levels each side, whole window)

def r6_windows(qdir: Path) -> list[dict]:
    root = qdir / "book15r6"
    out = []
    if not root.exists():
        return out
    for run in sorted(root.glob("*/*")):
        bf, tf = run / "book.csv.gz", run / "trades.csv.gz"
        if not bf.exists() or not tf.exists():
            continue
        rows, offs = {}, []
        for r in _gz_rows(bf):
            if r["series"] != SERIES:
                continue
            tr = int(r["t_recv_ms"]) / 1000.0
            if r.get("server_date_header"):
                try:
                    hd = datetime.strptime(r["server_date_header"], "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=timezone.utc).timestamp()
                    offs.append(hd + 0.5 - tr)
                except ValueError:
                    pass
            def lv(pfx):
                o = []
                for i in range(1, 6):
                    px, sz = r.get(f"{pfx}_px_{i}"), r.get(f"{pfx}_sz_{i}")
                    if px not in (None, "") and sz not in (None, ""):
                        o.append((r4(float(px)), float(sz)))
                return o
            rows.setdefault(r["ticker"], []).append((tr, lv("yes_bid"), lv("no_bid"), r["close_time"]))
        if not offs:
            continue                                     # no clock: NOT_RUNNABLE for this run's windows (counted by the caller)
        off = statistics.median(offs)
        trades = {}
        for r in _gz_rows(tf):
            if not r["ticker"].startswith(SERIES):
                continue
            t = datetime.fromisoformat(r["created_time"].replace("Z", "+00:00")).timestamp()
            trades.setdefault(r["ticker"], []).append((t, float(r["yes_price_dollars"]), float(r["count_fp"]),
                                                       1 if r["taker_outcome_side"] == "yes" else -1))
        for tk, polls in rows.items():
            close = datetime.fromisoformat(polls[0][3].replace("Z", "+00:00")).timestamp()
            ps = sorted((t + off, yb, nb) for t, yb, nb, _ in polls)
            out.append({"ticker": tk, "close": int(close), "polls": ps, "trades": sorted(trades.get(tk, []))})
    out.sort(key=lambda w: w["close"])
    return out


def r6_side(side: str, poll: tuple):
    """(side bids [(px, sz)], side asks [(px, sz)]) best first, from (t, yes_bids, no_bids)."""
    _, yb, nb = poll
    if side == "yes":
        return yb, [(r4(1 - p), s) for p, s in nb]
    return nb, [(r4(1 - p), s) for p, s in yb]


def r6_model(wins: list) -> tuple[dict, dict]:
    res, info = {}, {"windows": len(wins), "signals": 0, "no_signal_poll": 0, "bid_sizes": [], "ask_sizes": [], "spreads": []}
    sigs = []
    for w in wins:
        T = w["close"]
        before = [p for p in w["polls"] if p[0] <= T - LEFT_S]
        if not before or before[-1][0] < T - LEFT_S - 10:
            info["no_signal_poll"] += 1; continue
        S = before[-1]
        yb, nb = S[1], S[2]
        if not yb or not nb:
            continue
        ya, na = r4(1 - nb[0][0]), r4(1 - yb[0][0])
        side = "yes" if (LO - EPS <= ya <= HI + EPS and ya >= na) else ("no" if LO - EPS <= na <= HI + EPS else None)
        if side is None:
            continue
        bids, asks = r6_side(side, S)
        info["signals"] += 1; info["bid_sizes"].append(bids[0][1]); info["ask_sizes"].append(asks[0][1]); info["spreads"].append(round(100 * (asks[0][0] - bids[0][0]), 2))
        sigs.append((w, side, S, bids, asks))
    for kind in KINDS + ("IOC",):
        for C in SIZES:
            rows = []
            for w, side, S, bids, asks in sigs:
                sb, sa = bids[0][0], asks[0][0]
                live = S[0] + LIVE_S; end = w["close"] - 119.0
                lp = next((p for p in w["polls"] if p[0] >= live), None)
                if lp is None:
                    continue
                lbids, lasks = r6_side(side, lp)
                ev = side_events(side, w["trades"])
                import math
                L = math.ceil(sa * 100 - 1e-9) / 100 if kind == "IOC" else limit_for(kind, sa, sb)
                got, cost = 0.0, 0.0
                for px, sz in lasks:                    # immediate cross of whatever is at or under our price at the live poll
                    if px <= L + EPS and got < C:
                        q = min(C - got, sz); got += q; cost += q * px
                if kind == "IOC":
                    fills = [(live, got, cost / got, "cross")] if got > 0 else []
                    sm = summarize_path(fills, live, C)
                    sm.update({"ask": sa, "L": L}); rows.append(sm); continue
                take = (got, cost / got) if got > 0 else None
                Q = sum(sz for px, sz in lbids if abs(px - L) <= EPS) if not take else 0.0
                if not take and lbids and L < lbids[-1][0] - EPS and len(lbids) >= 5:
                    Q = float("inf")                     # under the 5 recorded levels: the size at our price is not recorded
                # bids at better prices fill first by price priority, and a trade at our price only happens after them, so only the size AT L is ahead
                nxt = next((p for p in w["polls"] if p[0] > lp[0]), None)
                if nxt is not None and not take:
                    nbids, _ = r6_side(side, nxt)
                    Q = max(Q, sum(sz for px, sz in nbids if abs(px - L) <= EPS))
                qev = []
                for p in w["polls"]:
                    if p[0] > lp[0]:
                        _, xas = r6_side(side, p)
                        if xas:
                            qev.append((p[0], xas[0][0]))
                path = rest_fill(L, C, Q, live, ev, qev, end, take=take)
                sm = summarize_path(path["fills"], live, C)
                sm.update({"ask": sa, "L": L}); rows.append(sm)
            res[(kind, C)] = rows
    return res, info


# ---------------------------------------------------------------- report

def fmt_table(title: str, res: dict, hz=HORIZONS) -> list[str]:
    """One row per order type and size: share of signals FULLY filled by each horizon after the order is live, share with
    any fill by the last horizon, the missed share (not fully filled) at the last horizon, the mean price saved per filled
    contract against the side's ask at the decision, and the saving per opportunity (unfilled = 0)."""
    last = max(hz)
    lines = [f"### {title}", "", "| Order | C | n | " + " | ".join(f"full by {h} s" for h in hz) + f" | any by {last} s | missed at {last} s | saved per filled contract | saved per opportunity |",
             "|---|---|---|" + "---|" * (len(hz) + 4)]
    for (kind, C), rows in res.items():
        n = len(rows)
        if not n:
            lines.append(f"| {kind} | {C} | 0 |" + " n/a |" * (len(hz) + 4)); continue
        def share(h, full=True):
            vals = [r[h] for r in rows if r.get(h) is not None]
            if not vals:
                return None
            return sum(1 for v in vals if (v >= C - 1e-9 if full else v > 1e-9)) / len(vals)
        filled = [r for r in rows if r["qty"] > 1e-9]
        saved = statistics.mean(100 * (r["ask"] - r["cost"] / r["qty"]) for r in filled) if filled else None
        per_opp = sum(100 * (r["ask"] * r["qty"] - r["cost"]) for r in rows) / (n * C)
        f = lambda x: "n/a" if x is None else f"{100 * x:.0f}%"
        ml = share(last)
        lines.append(f"| {kind} | {C} | {n} | " + " | ".join(f(share(h)) for h in hz) + f" | {f(share(last, False))} | {f(None if ml is None else 1 - ml)} | "
                     + ("n/a" if saved is None else f"{saved:+.2f}c") + f" | {per_opp:+.2f}c |")
    return lines + [""]


def model(qdir: str) -> None:
    q = Path(qdir)
    out = []
    sigs = hist_signals()
    tape = _load("hist_tape.json")
    have = [s for s in sigs if s["ticker"] in tape]
    notrade = sum(1 for s in have if not any(s["S"] <= t[0] <= s["close"] - 119 for t in tape[s["ticker"]]))
    out.append(f"HISTORY: {len(sigs)} gold L1 signals since 2026-09-01, tape for {len(have)}; windows with no trade between the decision and T-119 s: {notrade}")
    spreads = [round(100 * (s["ask"] - s["bid"]), 1) for s in have]
    out.append(f"  spread at the decision (cents): median {statistics.median(spreads):.1f}, share at one tick (0.1c) {100 * sum(1 for x in spreads if x <= 0.1 + 1e-9) / len(spreads):.0f}%, at 1c or more {100 * sum(1 for x in spreads if x >= 1 - 1e-9) / len(spreads):.0f}%")
    wins = qrec_windows(q)
    qtape = _load("qrec_tape.json")
    qres, qinfo = qrec_model(wins, qtape)
    medq = statistics.median(qinfo["bid_sizes"]) if qinfo["bid_sizes"] else None
    for label, Qb in (("upper bound: nobody ahead at the bid (Q = 0)", 0.0),
                      (f"central: Q at the bid = the recorder's median favourite bid size ({medq})", medq if medq is not None else float("inf")),
                      ("lower bound: trades at our price never reach us at the bid (Q = infinite)", float("inf"))):
        res = hist_model(have, tape, Qb)
        out += fmt_table(f"History at the 6 minute decision, {label}", res)
        if Qb == float("inf"):
            out.append(dip_lines(res))
            out.append(mech_lines(res))
            out.append(mtm_lines(res))
            ex = {k: [r for r in v if not r["notrade"]] for k, v in res.items()}
            out += fmt_table("History, lower bound, windows with no trade after the decision excluded", ex)
    out.append(f"QUOTE RECORDER: {qinfo['windows']} gold windows, {qinfo['signals']} signals at the first poll (about T-150 s), first poll later than T-140 s: {qinfo['late_first_poll']}, no tape: {qinfo['no_tape']}")
    if qinfo["bid_sizes"]:
        out.append(f"  favourite bid size at the decision: median {statistics.median(qinfo['bid_sizes']):.0f}, quartiles {_q(qinfo['bid_sizes'])}; ask size median {statistics.median(qinfo['ask_sizes']):.0f}, quartiles {_q(qinfo['ask_sizes'])}; spread cents {_q(qinfo['spreads'])}")
    out += fmt_table("Quote recorder, decision at about T-150 s (horizons to T-20 s; 240 s does not fit)", qres, (30, 60, 120))
    r6w = r6_windows(q)
    rres, rinfo = r6_model(r6w)
    out.append(f"R6: {rinfo['windows']} gold windows, {rinfo['signals']} signals at the 6 minute poll, no poll within 10 s of T-360 s: {rinfo['no_signal_poll']}")
    if rinfo["signals"]:
        out.append(f"  favourite bid size {_q(rinfo['bid_sizes'])}; ask size {_q(rinfo['ask_sizes'])}; spread cents {_q(rinfo['spreads'])}")
        out += fmt_table("R6, at the 6 minute decision (measured 5 level book, measured queue)", rres)
    print("\n".join(out))


def _q(xs):
    xs = sorted(xs)
    if not xs:
        return "n/a"
    def at(f):
        return xs[min(len(xs) - 1, int(f * len(xs)))]
    return f"{at(0.25):g} / {at(0.5):g} / {at(0.75):g}"


def dip_lines(res: dict) -> str:
    """Price path only: the bought side's bid at T-120 s minus the decision bid, for BID orders filled vs not filled by 240 s.
    Not a settlement outcome; it shows whether fills come with a falling price (MAKER2's mechanism)."""
    rows = res[("BID", 1)]
    f = [100 * (r["bid120"] - r["bid"]) for r in rows if r["bid120"] is not None and r[240] >= 1 - 1e-9]
    u = [100 * (r["bid120"] - r["bid"]) for r in rows if r["bid120"] is not None and r[240] < 1 - 1e-9]
    g = lambda xs: f"{statistics.mean(xs):+.2f}c (n {len(xs)})" if xs else "n/a"
    rows2 = res[("IN1C", 1)]
    f2 = [100 * (r["bid120"] - r["bid"]) for r in rows2 if r["bid120"] is not None and r[240] >= 1 - 1e-9]
    u2 = [100 * (r["bid120"] - r["bid"]) for r in rows2 if r["bid120"] is not None and r[240] < 1 - 1e-9]
    return (f"Dip check (lower bound, C = 1; side bid at T-120 s minus the decision bid): BID filled {g(f)}, BID not filled {g(u)}; "
            f"IN1C filled {g(f2)}, IN1C not filled {g(u2)}\n")


def mtm_lines(res: dict) -> str:
    """Market-implied value at T-120 s (history only; NOT a settled outcome): the bought side's bid at T-120 s minus the
    price paid, in cents per contract, for orders fully filled by 240 s and for the missed ones had they been bought at
    the ask at the decision. It says how much the missed signals were worth to the market two minutes before the close."""
    parts = []
    for kind in ("IN01", "IN1C", "BID"):
        rows = [r for r in res[(kind, 1)] if r["bid120"] is not None]
        f = [100 * (r["bid120"] - r["L"]) for r in rows if r[240] >= 1 - 1e-9]
        m = [100 * (r["bid120"] - r["ask"]) for r in rows if r[240] < 1 - 1e-9]
        g = lambda xs: f"{statistics.mean(xs):+.2f}c (n {len(xs)})" if xs else "n/a"
        allask = [100 * (r["bid120"] - r["ask"]) for r in rows]
        parts.append(f"{kind}: filled at our price {g(f)}, missed at the ask {g(m)}, every signal at the ask {g(allask)}")
    return "Market-implied value at T-120 s, side bid minus price, C = 1, before fees: " + "; ".join(parts) + "\n"


def mech_lines(res: dict) -> str:
    """How the full fills by 240 s came about (the last fill that completed the order): a taker selling AT our price past the
    queue ("at"), a print strictly through our price ("through"), a taker lifting an ask at or under our price ("ask_lifted"),
    or our side's ask quoted at or under our price ("quote"). The last three need the price to come down to us."""
    import collections
    parts = []
    for kind in ("ASK", "IN01", "IN1C", "BID"):
        for C in (1, 10):
            rows = [r for r in res[(kind, C)] if r[240] >= C - 1e-9]
            cnt = collections.Counter(r["mech"] for r in rows)
            parts.append(f"{kind} C={C}: " + ", ".join(f"{k} {v}" for k, v in cnt.most_common()))
    return "Fill mechanism (full fills by 240 s): " + "; ".join(parts) + "\n"


def main(argv: list[str]) -> None:
    if len(argv) >= 2 and argv[1] == "fetch":
        fetch(argv[2] if len(argv) > 2 else None)
    elif len(argv) >= 3 and argv[1] == "model":
        model(argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
