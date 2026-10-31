"""MAKER5 and L1Q1 (workers/R6T_REGISTRATION.md) on recorder R6 (`origin/quote-data`, book15r6/). Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. Nothing here means trade.
    python -m scalper.r6tests count        (usable windows per market from coverage files only; no book or trade row is read)
    python -m scalper.r6tests run maker5   (two-sided resting quotes 12 to 7 minutes left, never re-priced, 5c stop, flat at T-7 min)
    python -m scalper.r6tests run l1q1     (L1's 6 minute entry as a resting bid; a: skip if unfilled at T-120 s, b: cross if still in band)
Each `run` refuses before 2026-11-06 00:00 UTC, below 300 usable windows, or a second time, and writes data/<id>_result.txt.

Queue model (MM1S / Q2B): an order joins behind all displayed size at its price, only trades move it forward, it fills by taker
volume at its price beyond the size ahead or by a print or recorded opposite quote through its price (the remainder at OUR price).
"""
from __future__ import annotations

import csv
import gzip
import io
import math
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from statistics import median

from .mm1 import central_date, order_fee, pf
from .mm1 import clustered_z as _cz
from .paths import DATA_DIR
from .quote2b import Pair, Poll

REPO = "/home/user/shwoopnet"
PREFIX = "book15r6/"
SERIES = ("KXGOLD15M", "KXBTC15M", "KXETH15M", "KXDOGE15M", "KXXRP15M")
READ_NOT_BEFORE = datetime(2026, 11, 6, tzinfo=timezone.utc).timestamp()
NEEDED = 300
SIZES = (1, 10)
TAKER, MAKER = 0.07, 0.0175
Z_BAR = 5.17
EPS = 5e-5
LIVE_DELAY_S = 1.0
RESULTS = {"maker5": DATA_DIR / "maker5_result.txt", "l1q1": DATA_DIR / "l1q1_result.txt"}
TRIES = {"maker5": 6, "l1q1": 12}
# MAKER5
M5_POST, M5_POST_GAP, M5_FLAT, M5_FLAT_LATE = 720, 30, 420, 402      # seconds before the close
M5_MID_LO, M5_MID_HI, M5_STOP = 0.20, 0.80, 0.05
M5_MARKOUTS, M5_MARKOUT_LATE = (30, 120), 20
# L1Q1
Q_SIGNAL, Q_SIGNAL_GAP, Q_EXPIRE = 360, 10, 120
BAND_LO, BAND_HI = 0.88, 0.97
# usable window by coverage
MIN_OK, MAX_GAP_MS = 0.80, 20_000
BAD_NOTES = ("tape incomplete", "tape page cap", "tape out of time")
BOOK_COLS = ["t_send_ms", "t_recv_ms", "server_date_header", "ticker", "series", "close_time"] \
    + [f"yes_bid_px_{i}" for i in range(1, 6)] + [f"yes_bid_sz_{i}" for i in range(1, 6)] \
    + [f"no_bid_px_{i}" for i in range(1, 6)] + [f"no_bid_sz_{i}" for i in range(1, 6)]


def clustered_z(vals, keys):
    """mm1's date-clustered z; 0 with fewer than 2 dates (one cluster has no between-date variance to measure)."""
    return _cz(vals, keys) if len(set(keys)) >= 2 else 0.0


def _ceil_cent(raw_cents):
    return math.ceil(raw_cents - 1e-9) / 100 if raw_cents > 0 else 0.0


def taker_fee(legs):
    """One crossing order over all its levels: 7% x q x p x (1-p) summed, rounded up to the cent."""
    return _ceil_cent(sum(TAKER * q * p * (1 - p) for p, q in legs) * 100)


def first_at(polls, t, late=None):
    for p in polls:
        if p.t >= t - 1e-9:
            return p if late is None or p.t <= t + late + 1e-9 else None
    return None


def last_at(polls, t, early):
    best = None
    for p in polls:
        if p.t <= t + 1e-9:
            best = p
        else:
            break
    return best if best is not None and best.t >= t - early - 1e-9 else None


def merged(polls, trades):
    """Events in time order; at the same instant trades come before the poll that shows their result."""
    ev = [(t, 0, (p, n, s)) for t, p, n, s in trades] + [(p.t, 1, p) for p in polls]
    ev.sort(key=lambda e: (e[0], e[1]))
    return ev


# ---------------------------------------------------------------- MAKER5, one market window

def simulate_maker5(polls, trades, close, size=1):
    """polls: [Poll] in exchange time; trades: [(t, yes_price, count, side)], side -1 = taker sold YES ("no"), +1 = bought YES.
    Returns a Pair (with .end) or None when no pair is posted. Pure."""
    post = first_at(polls, close - M5_POST, M5_POST_GAP)
    if post is None or post.bid is None or post.ask is None or not (post.bid < post.ask - EPS):
        return None
    if not (M5_MID_LO - EPS <= post.mid <= M5_MID_HI + EPS):
        return None
    pr = Pair(None, post.t, post.bid, post.ask, post.ybs[0], post.nbs[0], size)
    pending = False
    for t, kind, x in merged(polls, trades):
        if t > close - M5_FLAT + 1e-9:
            break
        if kind == 0:
            pr.trade(t, *x)
            continue
        if pending:
            pr.cross(x, "stop")
            return pr
        pr.quote(x)
        if pr.stop_hit(x):
            pending = True
    if abs(pr.inv) < 1e-12:
        pr.buy_on = pr.sell_on = False
        pr.end = "cycle" if pr.fb > 0 else "none"
        return pr
    p = first_at(polls, close - M5_FLAT, M5_FLAT - M5_FLAT_LATE)
    pr.cross(p if p is not None else Poll(close - M5_FLAT, [], [], [], []), "stop" if pending else "flatten")
    return pr


def maker5_pnl(pr, maker_rate, mult=1.0):
    return pr.gross() - mult * pr.fees(maker_rate)


def maker5_markouts(pr, polls, horizon):
    out = []
    for t, side, q, px in pr.fills:
        p = next((x for x in polls if x.t >= t + horizon and x.mid is not None), None)
        if p is None or p.t > t + horizon + M5_MARKOUT_LATE:
            continue
        out.append(((p.mid - px) if side == 1 else (px - p.mid), q))
    return out


# ---------------------------------------------------------------- L1Q1, one market window

def flip(p):
    """The same poll seen from the NO side: NO bids become the bids, YES bids the other side."""
    return Poll(p.t, p.nb, p.nbs, p.yb, p.ybs)


def simulate_l1q1(polls, trades, close, result, size=1):
    """L1's signal at the last poll at or before T-360 s (within 10 s), the side whose ask is 0.88 to 0.97.
    Returns None (no signal) or a dict with plain L1, the resting bid's fill, and variant b's cross. Pure."""
    S = last_at(polls, close - Q_SIGNAL, Q_SIGNAL_GAP)
    if S is None:
        return None
    yes_in = S.ask is not None and BAND_LO - EPS <= S.ask <= BAND_HI + EPS
    no_in = S.bid is not None and BAND_LO - EPS <= 1 - S.bid <= BAND_HI + EPS
    if yes_in == no_in:
        return None
    side = "yes" if yes_in else "no"
    if side == "no":
        polls = [flip(p) for p in polls]
        trades = [(t, 1 - px, n, -s) for t, px, n, s in trades]
        S = flip(S)
    win = (result == side)
    live = S.t + LIVE_DELAY_S
    P = first_at(polls, live)
    plain, _ = (P if P is not None else Poll(live, [], [], [], [])).walk(False, size)
    out = {"side": side, "win": win, "size": size, "plain": plain, "b": S.bid, "filled": 0.0, "t_fill": None, "cross": [],
           "ask_at_signal": S.ask}
    b = S.bid
    if b is not None:
        ahead = S.ybs[0]
        nxt = first_at(polls, live)
        if nxt is not None and nxt.bid is not None and abs(nxt.bid - b) < EPS:
            ahead = max(ahead, nxt.ybs[0])          # conservative: behind the larger displayed size
        cum, filled = 0.0, 0.0
        for t, kind, x in merged(polls, trades):
            if t < live:
                continue
            if t >= close - Q_EXPIRE:
                break
            new = filled
            if kind == 0:
                px, n, s = x
                if s == -1:                          # a taker selling our side hits resting bids
                    if abs(px - b) < EPS:
                        cum += n
                        new = max(filled, min(size, cum - ahead))
                    elif px < b - EPS:
                        new = size
            elif x.ask is not None and x.ask <= b + EPS:
                new = size
            if new > filled + 1e-12:
                filled = new
                out["t_fill"] = out["t_fill"] or t
            if filled >= size - 1e-12:
                break
        out["filled"] = filled
    rem = size - out["filled"]
    if rem > 1e-12:
        E = first_at(polls, close - Q_EXPIRE)
        if E is not None and E.ask is not None and BAND_LO - EPS <= E.ask <= BAND_HI + EPS:
            out["cross"], _ = E.walk(False, rem)
    return out


def l1q1_pnl(w, variant, maker_rate, mult=1.0):
    pay = 1.0 if w["win"] else 0.0
    if variant == "plain":
        q = sum(q for _, q in w["plain"])
        return q * pay - sum(p * q for p, q in w["plain"]) - mult * taker_fee(w["plain"])
    f, b = w["filled"], w["b"]
    x = (f * (pay - b) - mult * order_fee(maker_rate, f, b)) if f > 0 else 0.0
    if variant == "b" and w["cross"]:
        q = sum(q for _, q in w["cross"])
        x += q * pay - sum(p * q for p, q in w["cross"]) - mult * taker_fee(w["cross"])
    return x


# ---------------------------------------------------------------- statistics

def stats(rows):
    """rows: [(close, series, pnl)] -> PF pooled, thirds and halves by close time, net, z clustered by Central date."""
    rows = sorted(rows, key=lambda r: (r[0], r[1]))
    v = [r[2] for r in rows]
    n = len(v)
    thirds = [v[i * n // 3:(i + 1) * n // 3] for i in range(3)]
    halves = [v[:n // 2], v[n // 2:]]
    return {"n": n, "pf": pf(v), "thirds": [pf(t) for t in thirds], "halves": [pf(h) for h in halves], "net": sum(v),
            "per": sum(v) / n if n else 0.0, "z": clustered_z(v, [central_date(r[0]) for r in rows]),
            "third_net": [sum(t) / len(t) if t else 0.0 for t in thirds],
            "loss_rate": sum(1 for x in v if x < 0) / n if n else 0.0}


def bar(s, st):
    return (s["n"] >= NEEDED and s["pf"] >= 1.5 and all(t >= 1.5 for t in s["thirds"]) and all(h > 1 for h in s["halves"])
            and s["per"] > 0 and st["net"] > 0 and st["pf"] > 1.2 and s["z"] >= Z_BAR)


def fmt(s):
    return (f"n {s['n']}, PF {s['pf']:.2f} (thirds {' / '.join(f'{t:.2f}' for t in s['thirds'])}; halves "
            f"{' / '.join(f'{h:.2f}' for h in s['halves'])}), loss rate {100 * s['loss_rate']:.0f}%, net {100 * s['per']:+.3f}c per window, "
            f"total ${s['net']:+.2f}, z {s['z']:+.2f}")


def maker5_report(wins):
    """wins: [(close, series, {C: Pair}, {C: {h: markouts}}, had_trades)] with a pair posted. Returns (all_pass, lines)."""
    lines, ok = [], True
    for C in SIZES:
        for label, rate, mult in (("VERDICT maker fee = taker 7%", TAKER, 1.0), ("stress 7% x1.2", TAKER, 1.2),
                                  ("info maker 1.75%", MAKER, 1.0), ("info zero maker fee", 0.0, 1.0)):
            lines.append(f"C={C:>2} {label}: " + fmt(stats([(c, s, maker5_pnl(p[C], rate, mult)) for c, s, p, _, _ in wins])))
        s = stats([(c, se, maker5_pnl(p[C], TAKER)) for c, se, p, _, _ in wins])
        st = stats([(c, se, maker5_pnl(p[C], TAKER, 1.2)) for c, se, p, _, _ in wins])
        prs = [p[C] for _, _, p, _, _ in wins]
        spread = sum(p.spread() for p in prs)
        rest = -sum(min(0.0, p.gross() - p.spread()) for p in prs)
        ok &= bar(s, st) and rest < 0.5 * spread
        mk_b = sum(1 for p in prs if p.fills and any(sd == 1 for _, sd, _, _ in p.fills))
        mk_s = sum(1 for p in prs if p.fills and any(sd == -1 for _, sd, _, _ in p.fills))
        lines.append(f"C={C:>2} pairs {len(prs)}, YES bid filled {mk_b}, NO bid filled {mk_s}, cycles {sum(p.end == 'cycle' for p in prs)}, "
                     f"stops {sum(p.end == 'stop' for p in prs)}, flattens {sum(p.end == 'flatten' for p in prs)}, "
                     f"spread earned ${spread:.2f}, stop and flatten loss ${rest:.2f}, fees ${sum(p.fees(TAKER) for p in prs):.2f}, "
                     f"contracts beyond 5 levels {sum(p.beyond for p in prs):.0f}")
        ex = stats([(c, se, maker5_pnl(p[C], TAKER)) for c, se, p, _, tr in wins if tr])
        lines.append(f"C={C:>2} verdict fee, windows with no trades excluded: " + fmt(ex))
        for h in M5_MARKOUTS:
            xs = [(c, m, q) for c, _, _, mk, _ in wins for m, q in mk[C][h]]
            if xs:
                tot = sum(q for _, _, q in xs)
                z = clustered_z([m for _, m, _ in xs], [central_date(c) for c, _, _ in xs])
                lines.append(f"C={C:>2} markout {h}s: {len(xs)} fills, {tot:.0f} contracts, mean {100 * sum(m * q for _, m, q in xs) / tot:+.2f}c "
                             f"per contract (our way +), z {z:+.2f}")
            else:
                lines.append(f"C={C:>2} markout {h}s: no fills")
        for ser in SERIES:
            sub = [(c, se, maker5_pnl(p[C], TAKER)) for c, se, p, _, _ in wins if se == ser]
            if sub:
                lines.append(f"C={C:>2} {ser} verdict fee: " + fmt(stats(sub)))
    return ok, lines


def l1q1_report(wins):
    """wins: [(close, series, {C: window dict}, had_trades)] with a signal. Returns (all_pass, lines)."""
    lines, ok = [], True
    for C in SIZES:
        W = [(c, se, w[C]) for c, se, w, _ in wins]
        lines.append(f"C={C:>2} plain L1 (cross at the ask, the comparison): " + fmt(stats([(c, se, l1q1_pnl(w, 'plain', TAKER)) for c, se, w in W])))
        for v in ("a", "b"):
            for label, rate, mult in (("VERDICT maker fee = taker 7%", TAKER, 1.0), ("stress 7% x1.2", TAKER, 1.2),
                                      ("info maker 1.75%", MAKER, 1.0), ("info zero maker fee", 0.0, 1.0)):
                lines.append(f"C={C:>2} variant {v} {label}: " + fmt(stats([(c, se, l1q1_pnl(w, v, rate, mult)) for c, se, w in W])))
            s = stats([(c, se, l1q1_pnl(w, v, TAKER)) for c, se, w in W])
            st = stats([(c, se, l1q1_pnl(w, v, TAKER, 1.2)) for c, se, w in W])
            plain = stats([(c, se, l1q1_pnl(w, 'plain', TAKER)) for c, se, w in W])
            diff = sorted([(c, se, l1q1_pnl(w, v, TAKER) - l1q1_pnl(w, 'plain', TAKER)) for c, se, w in W], key=lambda r: (r[0], r[1]))
            better = all(a > p for a, p in zip(s["third_net"], plain["third_net"]))
            ok &= bar(s, st) and better
            dz = clustered_z([d for _, _, d in diff], [central_date(c) for c, _, _ in diff])
            lines.append(f"C={C:>2} variant {v} minus plain, per opportunity: {100 * sum(d for *_, d in diff) / max(1, len(diff)) / C:+.3f}c per contract "
                         f"(thirds {' / '.join(f'{100 * (a - p) / C:+.3f}' for a, p in zip(s['third_net'], plain['third_net']))}), z {dz:+.2f}")
        full = [w for _, _, w in W if w["filled"] >= C - 1e-12]
        part = [w for _, _, w in W if 1e-12 < w["filled"] < C - 1e-12]
        miss = [w for _, _, w in W if w["filled"] <= 1e-12]
        lines.append(f"C={C:>2} signals {len(W)}: bid filled fully {len(full)} ({100 * len(full) / max(1, len(W)):.0f}%), partly {len(part)}, "
                     f"not at all {len(miss)}; variant b crossed on {sum(1 for w in miss + part if w['cross'])}")
        filled = [w for w in full + part]
        f_pl = [w["filled"] * ((1.0 if w["win"] else 0.0) - w["b"]) - order_fee(TAKER, w["filled"], w["b"]) for w in filled]
        f_plain = [l1q1_pnl(w, "plain", TAKER) * w["filled"] / C for w in filled]
        m_plain = [l1q1_pnl(w, "plain", TAKER) for w in miss]
        nf = sum(w["filled"] for w in filled)
        lines.append(f"C={C:>2} FILLED entries at the bid: PF {pf(f_pl):.2f}, net {100 * sum(f_pl) / max(1e-9, nf):+.2f}c per contract, "
                     f"win rate {100 * sum(w['win'] for w in filled) / max(1, len(filled)):.1f}%; the same at plain L1's price PF {pf(f_plain):.2f}, "
                     f"net {100 * sum(f_plain) / max(1e-9, nf):+.2f}c per contract")
        lines.append(f"C={C:>2} MISSED signals at plain L1's price: PF {pf(m_plain):.2f}, net {100 * sum(m_plain) / max(1, len(miss) * C):+.2f}c per contract, "
                     f"win rate {100 * sum(w['win'] for w in miss) / max(1, len(miss)):.1f}%")
        ex = [(c, se, w[C]) for c, se, w, tr in wins if tr]
        lines.append(f"C={C:>2} variant a verdict fee, windows with no trades excluded: " + fmt(stats([(c, se, l1q1_pnl(w, 'a', TAKER)) for c, se, w in ex])))
        for ser in SERIES:
            sub = [(c, se, w) for c, se, w in W if se == ser]
            if sub:
                lines.append(f"C={C:>2} {ser}: signals {len(sub)}, filled {sum(1 for _, _, w in sub if w['filled'] > 0)}, "
                             f"plain {100 * stats([(c, s, l1q1_pnl(w, 'plain', TAKER)) for c, s, w in sub])['per'] / C:+.2f}c, "
                             f"a {100 * stats([(c, s, l1q1_pnl(w, 'a', TAKER)) for c, s, w in sub])['per'] / C:+.2f}c, "
                             f"b {100 * stats([(c, s, l1q1_pnl(w, 'b', TAKER)) for c, s, w in sub])['per'] / C:+.2f}c per contract per opportunity")
    lines.append("not modelled: one crypto order per window, window cap, Bitcoin and Ethereum smooth gate, XRP pause")
    return ok, lines


# ---------------------------------------------------------------- recorder data

def _git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True).stdout


def _csv(path):
    raw = _git("show", f"origin/quote-data:{path}")
    return list(csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw))))) if raw else []


def _ts(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _f(x):
    try:
        return float(x) if x not in (None, "") else None
    except ValueError:
        return None


def runs():
    _git("fetch", "-q", "origin", "quote-data")
    files = _git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split()
    mine = [f for f in files if f.startswith(PREFIX)]
    return sorted({f.rsplit("/", 1)[0] for f in mine if f.endswith("coverage.csv.gz")}), len(mine)


def windows():
    """{(close_ts, series): (run, coverage row)} from coverage files only; a duplicate keeps the row with more ok polls."""
    out = {}
    rs, _ = runs()
    for r in rs:
        for row in _csv(f"{r}/coverage.csv.gz"):
            if not row.get("ticker"):
                continue
            k = (int(_ts(row["close_time"])), row["series"])
            if k not in out or int(row["ok_polls"] or 0) > int(out[k][1]["ok_polls"] or 0):
                out[k] = (r, row)
    return out


def usable(card, close, row):
    polls, ok = int(row.get("polls") or 0), int(row.get("ok_polls") or 0)
    first, last = int(row.get("first_recv_ms") or 0) / 1000, int(row.get("last_recv_ms") or 0) / 1000
    note = row.get("note") or ""
    base = (bool(row.get("ticker")) and polls > 0 and ok / polls >= MIN_OK and int(row.get("max_gap_ms") or 0) <= MAX_GAP_MS
            and int(row.get("tape_pages") or 0) >= 1 and not any(b in note for b in BAD_NOTES) and first > 0)
    if card == "maker5":
        return base and first <= close - M5_POST + M5_POST_GAP and last >= close - M5_FLAT_LATE
    return base and first <= close - Q_SIGNAL - 5 and last >= close - Q_EXPIRE + 5 and row.get("result") in ("yes", "no")


def ready_date(n_usable, last_close):
    need = max(0, NEEDED - n_usable)
    est = (last_close or time.time()) + need * 900 / len(SERIES)
    return datetime.fromtimestamp(max(READ_NOT_BEFORE, est), timezone.utc)


def posted_flags(polls, close):
    """(maker5_posted, l1q1_signal) for one market window from POLL PRICES ONLY (no trade, fill, result or outcome).
    The same two tests simulate_maker5 and simulate_l1q1 apply first (workers/R6T_AMENDMENT_1.md). Pure."""
    post = first_at(polls, close - M5_POST, M5_POST_GAP)
    m5 = (post is not None and post.bid is not None and post.ask is not None and post.bid < post.ask - EPS
          and M5_MID_LO - EPS <= post.mid <= M5_MID_HI + EPS)
    S = last_at(polls, close - Q_SIGNAL, Q_SIGNAL_GAP)
    q = False
    if S is not None:
        yes_in = S.ask is not None and BAND_LO - EPS <= S.ask <= BAND_HI + EPS
        no_in = S.bid is not None and BAND_LO - EPS <= 1 - S.bid <= BAND_HI + EPS
        q = yes_in != no_in
    return m5, q


def gate_message(posted):
    """None when BOTH posted counts reach NEEDED, else the refusal text naming the short count(s). Pure."""
    short = [f"{c} {posted.get(c, 0)} of {NEEDED}" for c in ("maker5", "l1q1") if posted.get(c, 0) < NEEDED]
    return ("Refusing: posted-order gate not met (needs " + str(NEEDED) + " scored windows with an order posted for BOTH cards; short: "
            + ", ".join(short) + "). The run is not spent; the AUTO loop re-tries.") if short else None


def posted_by_window(ws=None):
    """{(close, series): (maker5_posted, l1q1_signal)} over windows usable for the card, reading book.csv.gz PRICE columns only
    (the trade file is never opened). A window counts for a card only if it is usable for that card by the registered coverage test."""
    ws = windows() if ws is None else ws
    byrun = defaultdict(list)
    for k, (r, row) in ws.items():
        if usable("maker5", k[0], row) or usable("l1q1", k[0], row):
            byrun[r].append((k, row))
    out = {}
    for r, ks in sorted(byrun.items()):
        book = _csv(f"{r}/book.csv.gz")
        off = _offset(book)
        if off is None:
            continue
        tick = {row["ticker"]: (k, row) for k, row in ks}
        polls = defaultdict(list)
        for x in book:
            if x["ticker"] in tick:
                polls[x["ticker"]].append(_poll(x, off))
        del book
        for tk, ((close, ser), row) in tick.items():
            ps = sorted(polls.get(tk, []), key=lambda p: p.t)
            m5, q = posted_flags(ps, close)
            out[(close, ser)] = (m5 and usable("maker5", close, row), q and usable("l1q1", close, row))
    return out


def posted_counts(ws=None):
    pw = posted_by_window(ws)
    return {"maker5": sum(1 for a, _ in pw.values() if a), "l1q1": sum(1 for _, b in pw.values() if b)}


def count():
    ws = windows()
    _, nfiles = runs()
    parts = []
    for card in ("maker5", "l1q1"):
        per = {s: sum(1 for (c, se), (_, row) in ws.items() if se == s and usable(card, c, row)) for s in SERIES}
        n = sum(per.values())
        last = max((c for c, _ in ws), default=None)
        parts.append(f"{card.upper()} {n} usable of {NEEDED} ({', '.join(f'{s[2:-3]} {v}' for s, v in per.items())}), "
                     f"earliest read {ready_date(n, last):%Y-%m-%d %H:%M} UTC")
    pc = posted_counts(ws)
    parts.append(f"POSTED (price rows only) MAKER5 {pc['maker5']} of {NEEDED}, L1Q1 {pc['l1q1']} of {NEEDED}")
    print(f"R6 count: {nfiles} files, {len(ws)} recorded market windows; " + "; ".join(parts))
    return len(ws)


def _offset(book):
    d = []
    for x in book:
        h = x.get("server_date_header")
        if h:
            try:
                d.append(parsedate_to_datetime(h).timestamp() + 0.5 - int(x["t_recv_ms"]) / 1000)
            except (TypeError, ValueError):
                pass
    return median(d) if d else None


def _poll(x, off):
    yb = [(_f(x[f"yes_bid_px_{i}"]), _f(x[f"yes_bid_sz_{i}"])) for i in range(1, 6)]
    nb = [(_f(x[f"no_bid_px_{i}"]), _f(x[f"no_bid_sz_{i}"])) for i in range(1, 6)]
    yb = [(p, s) for p, s in yb if p is not None and s is not None]
    nb = [(p, s) for p, s in nb if p is not None and s is not None]
    return Poll(int(x["t_recv_ms"]) / 1000 + off, [p for p, _ in yb], [s for _, s in yb], [p for p, _ in nb], [s for _, s in nb])


def run(card, now=None):
    now = time.time() if now is None else now
    if card not in RESULTS:
        print(__doc__)
        return
    out = RESULTS[card]
    if out.exists():
        print(f"Refusing to run again: {out} exists.")
        return
    if now < READ_NOT_BEFORE:
        print(f"Refusing: the read date is {datetime.fromtimestamp(READ_NOT_BEFORE, timezone.utc):%Y-%m-%d %H:%M} UTC.")
        return
    ws = windows()
    use = {k: v for k, v in ws.items() if usable(card, k[0], v[1])}
    if len(use) < NEEDED:
        print(f"Refusing: {len(use)} usable windows, {NEEDED} needed.")
        return
    msg = gate_message(posted_counts(ws))     # Amendment 1: price rows only; a refusal here is not the one run
    if msg:
        print(msg)
        return
    byrun = defaultdict(list)
    for k, (r, row) in use.items():
        byrun[r].append((k, row))
    scored, no_clock, mismatch, no_order = [], 0, 0, 0
    for r, ks in sorted(byrun.items()):
        book = _csv(f"{r}/book.csv.gz")
        if book and list(book[0]) != BOOK_COLS:
            print("NOT_RUNNABLE: recorder schema changed")
            return
        off = _offset(book)
        if off is None:
            no_clock += len(ks)
            continue
        tick = {row["ticker"]: (k, row) for k, row in ks}
        polls, trades = defaultdict(list), defaultdict(list)
        for x in book:
            if x["ticker"] in tick:
                polls[x["ticker"]].append(_poll(x, off))
        del book
        for x in _csv(f"{r}/trades.csv.gz"):
            if x["ticker"] in tick:
                trades[x["ticker"]].append((_ts(x["created_time"]), float(x["yes_price_dollars"]), float(x["count_fp"]),
                                            1 if x["taker_outcome_side"] == "yes" else -1))
        for tk, ((close, ser), row) in tick.items():
            ps = sorted(polls.get(tk, []), key=lambda p: p.t)
            tr = sorted(trades.get(tk, []))
            ts, vol = _f(row.get("tape_sum_count")), _f(row.get("volume_fp"))
            if ts is not None and vol and abs(ts - vol) > 0.01 * vol:
                mismatch += 1
            if card == "maker5":
                prs = {C: simulate_maker5(ps, tr, close, C) for C in SIZES}
                if prs[1] is None:
                    no_order += 1
                    continue
                mk = {C: {h: maker5_markouts(prs[C], ps, h) for h in M5_MARKOUTS} for C in SIZES}
                scored.append((close, ser, prs, mk, bool(tr)))
            else:
                w = {C: simulate_l1q1(ps, tr, close, row.get("result"), C) for C in SIZES}
                if w[1] is None:
                    no_order += 1
                    continue
                scored.append((close, ser, w, bool(tr)))
    if no_clock > 0.2 * len(use):
        print(f"NOT_RUNNABLE: {no_clock} of {len(use)} usable windows without a clock")
        return
    ok, lines = (maker5_report if card == "maker5" else l1q1_report)(scored)
    verdict = "NOT_ENOUGH_DATA" if len(scored) < NEEDED else ("NOT_YET_FALSIFIED" if ok else "FALSIFIED")
    lines.insert(0, f"{card.upper()} VERDICT {verdict} (usable windows {len(use)}, with an order posted {len(scored)}, no order {no_order}, "
                    f"no clock {no_clock}, tape and volume differ over 1% {mismatch}; minimum {NEEDED}; z bar {Z_BAR}; tries {TRIES[card]}, "
                    f"R6T 18, running count about 439,124)")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv):
    if len(argv) >= 2 and argv[1] == "count":
        count()
    elif len(argv) >= 3 and argv[1] == "run":
        run(argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
