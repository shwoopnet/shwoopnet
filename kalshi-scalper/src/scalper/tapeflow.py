"""T1, early taker flow (ledger row L11). The rule, universe, prediction and kill criteria are fixed in README.md ("Pre-registration: T1"), before any trade was fetched.

For every settled market in the most recent 30 days, sum the taker contracts by side over the first 5 minutes after the open (trades stamped at or after the open and
strictly before open + 300 s, and nothing else). Signal: at least 50 taker contracts and |YES minus NO| / total at least 0.60. Entry: the favoured side at the candle
ending 360 s after the open (it STARTS after the signal minute, so the fill is on a later bar than the signal), a real two sided quote required, hold to settlement,
one contract, fee 0.07 p (1 - p). Public endpoint only; no account, key or order.

T2 (README, Pre-registration: T2) is the same signal and entry, closed at the bid on the candle ending 480 s after the open instead of held, so it is flat before L1.

Usage: python -m scalper.tapeflow fetch [days]     (resumable)
       python -m scalper.tapeflow run
"""
from __future__ import annotations

import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from . import api
from .analyze import valid_quote
from .calibration import cluster_mean_z
from .paths import DB
from .scalps import MIN_N, STRESS, Z_BAR, fee

WINDOW_S = 300          # trades in the first 5 minutes only
ENTRY_END_S = 360       # the candle that ends 360 s after the open starts after the signal
EXIT_END_S = 480        # T2 only: sell at the candle that ends 480 s after the open, 7 minutes before the close, ahead of L1's window (400 s to 330 s left)
MIN_TOTAL = 50          # taker contracts in the window
MIN_TOTAL_STRICT = 100  # the kill criterion: the result must survive this
MIN_IMBALANCE = 0.60
MIN_DAYS = 5
PAUSE_S = 0.12

SCHEMA = "CREATE TABLE IF NOT EXISTS tapeflow(ticker TEXT PRIMARY KEY, yes_ct REAL, no_ct REAL, n_trades INTEGER)"
# One row per second that had a trade. yes_px: price (of YES) at the first print by a taker buying YES in that second, an ask the taker paid. no_px: YES price at the
# first print by a taker buying NO, which is where the YES bid was. last_px: YES price of the last print. cy, cn: contracts by taker side.
BARS = "CREATE TABLE IF NOT EXISTS tape_s(ticker TEXT, sec INTEGER, yes_px REAL, no_px REAL, last_px REAL, cy REAL, cn REAL, PRIMARY KEY(ticker, sec))"

# T3 (README, Pre-registration: T3), all fixed before any bar was read
T3_LOOK_FROM_S = 20     # price at the end of second 20 ...
T3_SIGNAL_S = 60        # ... against the price at the end of second 60: the drift of the first minute
T3_MIN_DRIFT = 0.03     # at least 3c in one direction
T3_BAND = (0.55, 0.70)  # the side bought must cost 55c to 70c at the entry print
T3_TARGET = 0.05        # sell when the bid is 5c above the entry price
T3_TIME_EXIT_S = 240    # otherwise sell at the first bid print at or after 240 s (11 minutes left), long before L1's window

# T4 (README, Pre-registration: T4): the cheap side, scalped, fixed before any bar was read
T4_BAND = (0.04, 0.10)  # the side bought costs 4c to 10c at the entry print (the owner's example: 6.2%, 14.9x)
T4_ENTRY_FROM_S = 61    # first entry print at or after second 61 ...
T4_ENTRY_TO_S = 180     # ... and before second 180
T4_TARGET = 0.03        # sell when the bid is 3c above the entry price
T4_TIME_EXIT_S = 240    # otherwise the first bid print at or after 240 s


def window_flow(trades: list[dict], open_ts: int) -> tuple[float, float, int]:
    """(YES contracts, NO contracts, trades) from the trades that fall in [open, open + WINDOW_S). A trade stamped later is never counted."""
    yes = no = 0.0
    n = 0
    for t in trades:
        ts = int(datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp())
        if not (open_ts <= ts < open_ts + WINDOW_S):
            continue
        c = api.f(t.get("count_fp")) or 0.0
        if t.get("taker_side") == "yes":
            yes += c
        elif t.get("taker_side") == "no":
            no += c
        n += 1
    return yes, no, n


def build_bars(trades: list[dict], open_ts: int) -> list[tuple]:
    """Second by second summary of the trades inside [open, open + WINDOW_S). Trades are taken in time order; a second keeps the FIRST taker print on each side."""
    rows = []
    for t in trades:
        ts = datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp()
        sec = int(ts - open_ts)
        if not (0 <= sec < WINDOW_S):
            continue
        rows.append((ts, sec, t.get("taker_side"), api.f(t.get("yes_price_dollars")), api.f(t.get("count_fp")) or 0.0))
    rows.sort(key=lambda r: r[0])
    by: dict[int, dict] = {}
    for _, sec, side, px, c in rows:
        b = by.setdefault(sec, {"yes_px": None, "no_px": None, "last_px": None, "cy": 0.0, "cn": 0.0})
        if px is None:
            continue
        b["last_px"] = px
        if side == "yes":
            b["cy"] += c
            if b["yes_px"] is None:
                b["yes_px"] = px
        elif side == "no":
            b["cn"] += c
            if b["no_px"] is None:
                b["no_px"] = px
    return [(sec, b["yes_px"], b["no_px"], b["last_px"], b["cy"], b["cn"]) for sec, b in sorted(by.items())]


def fetch_one(ticker: str, open_ts: int) -> tuple[float, float, int, list[tuple]]:
    trades, cursor = [], None
    while True:
        params = {"ticker": ticker, "min_ts": open_ts, "max_ts": open_ts + WINDOW_S - 1, "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        r = api._get("/markets/trades", params)
        trades += r.get("trades", [])
        cursor = r.get("cursor")
        time.sleep(PAUSE_S)
        if not cursor or not r.get("trades"):
            break
    y, n, k = window_flow(trades, open_ts)
    return y, n, k, build_bars(trades, open_ts)


FETCH_PASSES = (0, 4, 2, 6, 1, 5, 3, 7)    # the order markets are fetched in: every 8th market of the 30 days, then the next offset, so ANY stopping point is an even sample of all days
FETCH_LIMIT = 1240                          # the pre-stated stopping point: two passes (offsets 0 and 4), about 620 markets each, unless the fetch finishes sooner


def fetch(days: int = 30, limit: int = FETCH_LIMIT) -> None:
    db = sqlite3.connect(DB)
    db.execute(SCHEMA)
    db.execute(BARS)
    last = db.execute("SELECT MAX(close_ts) FROM market").fetchone()[0]
    rows = db.execute("SELECT ticker, open_ts FROM market WHERE close_ts >= ? AND result IN ('yes','no') ORDER BY close_ts", (last - days * 86400,)).fetchall()
    have = {r[0] for r in db.execute("SELECT ticker FROM tapeflow")}
    order = {off: k for k, off in enumerate(FETCH_PASSES)}
    ranked = sorted(enumerate(rows), key=lambda ir: (order[ir[0] % 8], ir[0]))
    todo = [r for _, r in ranked if r[0] not in have][:max(0, limit - len(have))]
    print(f"{len(rows)} markets in the last {days} days, {len(have)} stored, {len(todo)} to fetch (stop at {limit})")
    for i, (ticker, open_ts) in enumerate(todo, 1):
        for attempt in range(12):       # a rate limit that outlasts the client's own retries is waited out, not fatal: the run resumes on the same market
            try:
                y, n, k, bars = fetch_one(ticker, open_ts)
                break
            except RuntimeError as e:
                print(f"  {ticker}: {str(e)[:90]} (attempt {attempt + 1}); waiting 120 s")
                db.commit()
                time.sleep(120)
        else:
            print(f"  {ticker}: gave up after 12 attempts, left unfetched")
            continue
        db.executemany("INSERT OR REPLACE INTO tape_s VALUES (?,?,?,?,?,?,?)", [(ticker, *b) for b in bars])
        db.execute("INSERT OR REPLACE INTO tapeflow VALUES (?,?,?,?)", (ticker, y, n, k))
        if i % 50 == 0:
            db.commit(); print(f"  {i} fetched")
    db.commit()


def signals(rows: list[tuple], min_total: float = MIN_TOTAL) -> list[tuple]:
    """rows: (ticker, yes_ct, no_ct). Returns (ticker, side) for markets that clear the volume and imbalance bars."""
    out = []
    for ticker, y, n in rows:
        tot = y + n
        if tot < min_total or tot <= 0:
            continue
        imb = (y - n) / tot
        if abs(imb) >= MIN_IMBALANCE:
            out.append((ticker, "yes" if imb > 0 else "no"))
    return out


def entries(db, min_total: float = MIN_TOTAL, roundtrip: bool = False) -> list[dict]:
    """roundtrip=False is T1 (hold to settlement). roundtrip=True is T2: the same signal and entry, sold at the bid on the candle ending EXIT_END_S after the open
    (a real two sided quote required, otherwise the market has no observation), with the fee on both legs, so the position is closed before L1's window opens."""
    flow = db.execute("SELECT ticker, yes_ct, no_ct FROM tapeflow").fetchall()
    out = []
    for ticker, side in signals(flow, min_total):
        open_ts, close_ts, res = db.execute("SELECT open_ts, close_ts, result FROM market WHERE ticker=?", (ticker,)).fetchone()
        c = db.execute("SELECT bid_c, ask_c FROM candle WHERE ticker=? AND end_ts=?", (ticker, open_ts + ENTRY_END_S)).fetchone()
        if c is None or not valid_quote(c[0], c[1]):
            continue
        price = c[1] if side == "yes" else round(1 - c[0], 4)
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        if roundtrip:
            x = db.execute("SELECT bid_c, ask_c FROM candle WHERE ticker=? AND end_ts=?", (ticker, open_ts + EXIT_END_S)).fetchone()
            if x is None or not valid_quote(x[0], x[1]):
                continue
            sell = x[0] if side == "yes" else round(1 - x[1], 4)
            gross = sell - price
            out.append({"ticker": ticker, "day": day, "close_ts": close_ts, "price": price, "won": gross > 0,
                        "net": gross - fee(price) - fee(sell), "stress": gross - fee(price, STRESS) - fee(sell, STRESS)})
            continue
        won = (res == "yes") == (side == "yes")
        gross = (1.0 if won else 0.0) - price
        out.append({"ticker": ticker, "day": day, "close_ts": close_ts, "price": price,
                    "won": won, "net": gross - fee(price), "stress": gross - fee(price, STRESS)})
    return sorted(out, key=lambda e: e["close_ts"])


def t3_trade(bars: list[tuple]) -> dict | None:
    """T3 on one market's bars, or None when there is no observation. bars: (sec, yes_px, no_px, last_px, cy, cn) in time order.
    Signal from prints before second T3_SIGNAL_S only. Entry: the first print by a taker buying the leaning side at second T3_SIGNAL_S + 1 or later (one second of
    latency), price inside T3_BAND. Exit: the first LATER second whose opposite taker print puts our bid at entry + T3_TARGET or better, else the first opposite taker
    print at or after T3_TIME_EXIT_S. A market that never prints an exit has no observation. Fee on both legs."""
    def last_before(sec: int):
        v = None
        for b in bars:
            if b[0] < sec and b[3] is not None:
                v = b[3]
        return v
    p0, p1 = last_before(T3_LOOK_FROM_S), last_before(T3_SIGNAL_S)
    if p0 is None or p1 is None:
        return None
    drift = p1 - p0
    if abs(drift) < T3_MIN_DRIFT:
        return None
    side = "yes" if drift > 0 else "no"
    entry = None
    for b in bars:
        if b[0] < T3_SIGNAL_S + 1:
            continue
        px = b[1] if side == "yes" else (None if b[2] is None else round(1 - b[2], 4))   # a NO taker print at yes price q pays 1 - q for NO
        taker_buys_side = (b[1] is not None) if side == "yes" else (b[2] is not None)
        if taker_buys_side and px is not None and T3_BAND[0] <= px <= T3_BAND[1]:
            entry = (b[0], px)
            break
    if entry is None:
        return None
    esec, price = entry
    exit_ = None
    for b in bars:
        if b[0] <= esec:
            continue
        # our bid: a taker buying the OTHER side pays 1 - (what we hold); for YES that is the YES price a NO taker sells at
        bid = b[2] if side == "yes" else (None if b[1] is None else round(1 - b[1], 4))
        if bid is None:
            continue
        if bid >= price + T3_TARGET or b[0] >= T3_TIME_EXIT_S:
            exit_ = (b[0], bid)
            break
    if exit_ is None:
        return None
    gross = exit_[1] - price
    return {"price": price, "sell": exit_[1], "hold": exit_[0] - esec, "side": side, "net": gross - fee(price) - fee(exit_[1]),
            "stress": gross - fee(price, STRESS) - fee(exit_[1], STRESS), "won": gross > 0}


def _sell_scan(bars: list[tuple], side: str, esec: int, price: float, target: float, time_exit_s: int):
    """The first later second whose opposite taker print puts our bid at price + target or better, else the first such print at or after time_exit_s.
    Our bid for YES is the YES price a NO taker paid; for NO it is 1 minus the YES price a YES taker paid. None when no exit prints."""
    for b in bars:
        if b[0] <= esec:
            continue
        bid = b[2] if side == "yes" else (None if b[1] is None else round(1 - b[1], 4))
        if bid is None:
            continue
        if bid >= price + target or b[0] >= time_exit_s:
            return b[0], bid
    return None


def t4_trade(bars: list[tuple]) -> dict | None:
    """T4 on one market's bars. No signal: the first print, from second T4_ENTRY_FROM_S up to (not including) T4_ENTRY_TO_S, by a taker buying a side that costs
    T4_BAND (YES at its price, NO at 1 minus the YES price of a NO taker print). Exit as T3 with T4_TARGET and T4_TIME_EXIT_S. Fee on both legs."""
    entry = None
    for b in bars:
        if not (T4_ENTRY_FROM_S <= b[0] < T4_ENTRY_TO_S):
            continue
        cands = []
        if b[1] is not None:
            cands.append(("yes", b[1]))
        if b[2] is not None:
            cands.append(("no", round(1 - b[2], 4)))
        hit = [c for c in cands if T4_BAND[0] <= c[1] <= T4_BAND[1]]
        if hit:
            entry = (b[0], hit[0][0], hit[0][1])
            break
    if entry is None:
        return None
    esec, side, price = entry
    ex = _sell_scan(bars, side, esec, price, T4_TARGET, T4_TIME_EXIT_S)
    if ex is None:
        return None
    gross = ex[1] - price
    return {"price": price, "sell": ex[1], "hold": ex[0] - esec, "side": side, "net": gross - fee(price) - fee(ex[1]),
            "stress": gross - fee(price, STRESS) - fee(ex[1], STRESS), "won": gross > 0}


def t3_entries(db, min_total: float = 0.0, trade=None) -> tuple[list[dict], int, int]:
    """(observations, markets with bars, markets with no observation)."""
    out, seen = [], 0
    flow = {t: y + n for t, y, n in db.execute("SELECT ticker, yes_ct, no_ct FROM tapeflow")}
    for ticker, open_ts, close_ts in db.execute("SELECT ticker, open_ts, close_ts FROM market WHERE ticker IN (SELECT ticker FROM tapeflow) ORDER BY close_ts").fetchall():
        if flow.get(ticker, 0.0) < min_total:
            continue
        seen += 1
        bars = db.execute("SELECT sec, yes_px, no_px, last_px, cy, cn FROM tape_s WHERE ticker=? ORDER BY sec", (ticker,)).fetchall()
        t = (trade or t3_trade)(bars)
        if t is None:
            continue
        out.append(dict(t, ticker=ticker, close_ts=close_ts, day=datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")))
    return out, seen, seen - len(out)


def verdict(es: list[dict], es_strict: list[dict]) -> tuple[str, dict]:
    mean, se, z = cluster_mean_z([(e["day"], e["net"]) for e in es])
    days = sorted({e["day"] for e in es})
    mid = (es[0]["close_ts"] + es[-1]["close_ts"]) / 2 if es else 0
    h1 = [e["net"] for e in es if e["close_ts"] < mid]
    h2 = [e["net"] for e in es if e["close_ts"] >= mid]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    stress = sum(e["stress"] for e in es) / len(es) if es else 0.0
    strict_mean = sum(e["net"] for e in es_strict) / len(es_strict) if es_strict else 0.0
    ok = len(es) >= MIN_N and len(days) >= MIN_DAYS and z >= Z_BAR and mean > 0 and stress > 0 and m1 > 0 and m2 > 0 and strict_mean > 0
    win = sum(e["won"] for e in es) / len(es) if es else 0.0
    paid = sum(e["price"] for e in es) / len(es) if es else 0.0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": len(es), "days": len(days), "mean": mean, "z": z, "h1": m1, "h2": m2, "stress": stress,
            "strict_n": len(es_strict), "strict_mean": strict_mean, "win": win, "paid": paid}


def run() -> None:
    db = sqlite3.connect(DB)
    es, strict = entries(db), entries(db, MIN_TOTAL_STRICT)
    v, s = verdict(es, strict)
    f = lambda x: f"{x * 100:+.2f}c"
    print(f"T1 early taker flow: n={s['n']} on {s['days']} days, net {f(s['mean'])} per contract, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, "
          f"fees x{STRESS} {f(s['stress'])}, win {s['win']:.1%} against {s['paid']:.1%} paid, at 100 contracts n={s['strict_n']} net {f(s['strict_mean'])}")
    print(f"VERDICT: {v}")
    r, rs = entries(db, roundtrip=True), entries(db, MIN_TOTAL_STRICT, roundtrip=True)
    v2, s2 = verdict(r, rs)
    print(f"T2 early taker flow, sold at 7 minutes left: n={s2['n']} on {s2['days']} days, net {f(s2['mean'])} per contract, z {s2['z']:+.2f}, halves {f(s2['h1'])} / {f(s2['h2'])}, "
          f"fees x{STRESS} {f(s2['stress'])}, up {s2['win']:.1%}, at 100 contracts n={s2['strict_n']} net {f(s2['strict_mean'])}")
    print(f"VERDICT: {v2}")
    t3, seen, none = t3_entries(db)
    t3s, _, _ = t3_entries(db, MIN_TOTAL_STRICT)
    v3, s3 = verdict(t3, t3s)
    holds = sorted(e["hold"] for e in t3)
    print(f"T3 early drift scalp, tick level: {seen} markets read, {none} with no observation; n={s3['n']} on {s3['days']} days, net {f(s3['mean'])} per contract, z {s3['z']:+.2f}, "
          f"halves {f(s3['h1'])} / {f(s3['h2'])}, fees x{STRESS} {f(s3['stress'])}, up {s3['win']:.1%}, median hold {holds[len(holds) // 2] if holds else 0:.0f}s, "
          f"at 100 contracts n={s3['strict_n']} net {f(s3['strict_mean'])}")
    print(f"VERDICT: {v3}")
    t4, seen4, none4 = t3_entries(db, trade=t4_trade)
    t4s, _, _ = t3_entries(db, MIN_TOTAL_STRICT, trade=t4_trade)
    v4, s4 = verdict(t4, t4s)
    holds4 = sorted(e["hold"] for e in t4)
    print(f"T4 cheap side scalp, tick level: {seen4} markets read, {none4} with no observation; n={s4['n']} on {s4['days']} days, net {f(s4['mean'])} per contract, z {s4['z']:+.2f}, "
          f"halves {f(s4['h1'])} / {f(s4['h2'])}, fees x{STRESS} {f(s4['stress'])}, up {s4['win']:.1%}, median hold {holds4[len(holds4) // 2] if holds4 else 0:.0f}s, "
          f"at 100 contracts n={s4['strict_n']} net {f(s4['strict_mean'])}")
    print(f"VERDICT: {v4}")


if __name__ == "__main__":
    fetch(int(sys.argv[2]) if len(sys.argv) > 2 else 30) if sys.argv[1:2] == ["fetch"] else run()
