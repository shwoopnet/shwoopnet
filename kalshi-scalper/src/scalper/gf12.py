"""GF1 and GF2 (workers/GOLDFILL_PROPOSAL.md) on recorder R6 (`origin/quote-data`, book15r6/). Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. Nothing here means trade.
    python -m scalper.gf12 count      readiness from R6 BOOK files only (recorded windows, L1 signals); no coverage file, no
                                      result, no trade row is read
    python -m scalper.gf12 run gf1    rest 1c inside the ask for 30 s, then cross with a 1c chase cap, hold to settlement
    python -m scalper.gf12 run gf2    the 30 s hold: enter (capped cross) only if a 1c-inside bid would NOT have filled in 30 s
Each `run` refuses before 2026-11-14 00:00 UTC and refuses a second time (data/gf12_<card>_started is written before any
outcome is read; data/<card>_result.txt holds the result). Below 300 scored windows with an order the verdict is
NOT_ENOUGH_DATA. Gold is reported on its own beside the five-market pooled verdict.

Rules not restated here are R6T's shared rules and L1Q1's usable-window rule (workers/R6T_REGISTRATION.md), reused from
`scalper.r6tests`; the resting leg and GF2's test use `scalper.goldfill.rest_fill`. Readings of anything the proposal leaves
open are in workers/GF12_NOTES.md.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from . import r6tests as R6
from .goldfill import rest_fill, side_events
from .mm1 import central_date, order_fee, pf
from .paths import DATA_DIR
from .quote2b import Poll

SERIES = R6.SERIES                               # gold first
GOLD = "KXGOLD15M"
READ_NOT_BEFORE = datetime(2026, 11, 14, tzinfo=timezone.utc).timestamp()
LAST_OPEN = datetime(2026, 11, 13, 23, 59, tzinfo=timezone.utc).timestamp()   # R6 records no window opening at or after this
NEEDED = 300
SIZES = R6.SIZES
TAKER, MAKER = R6.TAKER, R6.MAKER
Z_BAR, GF2_Z_GATE = R6.Z_BAR, 2.0
EPS = R6.EPS
LIVE_S = 1.0                                     # an order is live 1.0 s after its posting poll
REST_END_S = 31.0                                # the resting bid is cancelled at S + 31.0 s (30 s after live)
INSIDE, CHASE_CAP = 0.01, 0.01                   # L = ask(S) - 1c; chase only at or under ask(S) + 1c
BAND_LO, BAND_HI = R6.BAND_LO, R6.BAND_HI
SIGNAL_S, SIGNAL_GAP = R6.Q_SIGNAL, R6.Q_SIGNAL_GAP
CARDS = ("gf1", "gf2")
RESULTS = {c: DATA_DIR / f"{c}_result.txt" for c in CARDS}
MARKERS = {c: DATA_DIR / f"gf12_{c}_started" for c in CARDS}
COUNT_CACHE = DATA_DIR / "gf12_count_cache.json"
TRIES = {"gf1": 6, "gf2": 2}
INF = float("inf")


# ---------------------------------------------------------------- one market window (pure)

def signal(polls, close):
    """L1Q1's signal: S = the last poll at or before T-360 s, within 10 s; the side whose ask at S is 0.88 to 0.97, exactly
    one. Returns (side, S, polls) with S and polls seen from the bought side (its bids in .yb, its ask = .ask), or None."""
    S = R6.last_at(polls, close - SIGNAL_S, SIGNAL_GAP)
    if S is None:
        return None
    yes_in = S.ask is not None and BAND_LO - EPS <= S.ask <= BAND_HI + EPS
    no_in = S.bid is not None and BAND_LO - EPS <= 1 - S.bid <= BAND_HI + EPS
    if yes_in == no_in:
        return None
    if yes_in:
        return "yes", S, polls
    fp = [R6.flip(p) for p in polls]
    return "no", R6.flip(S), fp


def queue_at(p, L):
    """Displayed size at side price L on the side's bids of poll p. L under all 5 recorded levels of a full side: unknown,
    taken as infinite (only a print or quote through L can fill it). No level at L otherwise: 0."""
    if p is None:
        return 0.0
    q = sum(s for px, s in zip(p.yb, p.ybs) if abs(px - L) < EPS)
    if q == 0 and len(p.yb) >= 5 and L < min(p.yb) - EPS:
        return INF
    return q


def rest_leg(side, S, polls, trades, C):
    """GF1's resting bid of C at L = ask(S) - 0.01 from S + 1.0 s to S + 31.0 s (exclusive), queue behind the larger of the
    size at L at S and at the first poll at or after live. trades in YES terms (t, yes_px, n, -1 taker sold YES / +1 bought).
    Returns (L, filled qty, fills)."""
    L = round(S.ask - INSIDE, 3)
    live = S.t + LIVE_S
    end = S.t + REST_END_S - 1e-6
    P = R6.first_at(polls, live)
    Q = max(queue_at(S, L), queue_at(P, L) if P is not None and P.t <= end else 0.0)
    qev = [(p.t, round(p.ask, 4)) for p in polls if live - 1e-9 <= p.t <= end and p.ask is not None]
    fills = rest_fill(L, C, Q, live, side_events(side, trades), qev, end)["fills"]
    return L, min(C, sum(f[1] for f in fills)), fills


def capped_cross(polls, S, q):
    """At the first poll at or after S + 31.0 s: if the side's ask is 0.88 to 0.97 and at most ask(S) + 0.01, buy q walking
    the recorded levels priced at most ask(S) + 0.01. Returns (status "cross" or "skip", legs [(price, qty)], qty not bought)."""
    E = R6.first_at(polls, S.t + REST_END_S)
    cap = S.ask + CHASE_CAP
    if E is None or E.ask is None or not (BAND_LO - EPS <= E.ask <= BAND_HI + EPS and E.ask <= cap + EPS):
        return "skip", [], q
    legs, left = [], q
    for p, s in ((round(1 - nb, 4), s) for nb, s in zip(E.nb, E.nbs)):
        if left <= 1e-12 or p > cap + EPS:
            break
        take = min(left, s)
        if take > 0:
            legs.append((p, take)); left -= take
    return "cross", legs, left


def simulate(polls, trades, close, result, C=1):
    """One market window at size C. polls: [Poll] exchange time, YES terms; trades: [(t, yes_px, n, side)]. None = no signal."""
    sig = signal(polls, close)
    if sig is None:
        return None
    side, S, sp = sig
    plain_poll = R6.first_at(sp, S.t + LIVE_S)
    plain, _ = (plain_poll if plain_poll is not None else Poll(S.t + LIVE_S, [], [], [], [])).walk(False, C)
    L, q, fills = rest_leg(side, S, sp, trades, C)
    w = {"side": side, "win": result == side, "C": C, "ask_s": S.ask, "L": L, "plain": plain, "rest_q": q,
         "rest_mech": fills[-1][3] if fills else None, "trades_seen": bool(trades)}
    rem = C - q
    if rem > 1e-12:
        w["chase_status"], w["chase"], w["chase_unbought"] = capped_cross(sp, S, rem)
    else:
        w["chase_status"], w["chase"], w["chase_unbought"] = "not needed", [], 0.0
    # GF2: the C = 1 resting test decides for every size (the filter must not depend on the order size)
    _, q1, _ = rest_leg(side, S, sp, trades, 1) if C != 1 else (L, q, fills)
    w["gf2_dip"] = q1 >= 1 - 1e-12
    if w["gf2_dip"]:
        w["gf2_status"], w["gf2"], w["gf2_unbought"] = "filtered", [], 0.0
    else:
        w["gf2_status"], w["gf2"], w["gf2_unbought"] = capped_cross(sp, S, C)
        if w["gf2_status"] == "cross" and not w["gf2"]:
            w["gf2_status"] = "skip"
    return w


def _legs_pnl(legs, pay, mult):
    return sum(q for _, q in legs) * pay - sum(p * q for p, q in legs) - mult * R6.taker_fee(legs)


def plain_pnl(w, mult=1.0):
    return _legs_pnl(w["plain"], 1.0 if w["win"] else 0.0, mult)


def rest_pnl(w, rate=TAKER, mult=1.0):
    q = w["rest_q"]
    return q * ((1.0 if w["win"] else 0.0) - w["L"]) - mult * order_fee(rate, q, w["L"]) if q > 0 else 0.0


def chase_pnl(w, mult=1.0):
    return _legs_pnl(w["chase"], 1.0 if w["win"] else 0.0, mult) if w["chase"] else 0.0


def gf1_pnl(w, rate=TAKER, mult=1.0):
    return rest_pnl(w, rate, mult) + chase_pnl(w, mult)


def gf2_pnl(w, mult=1.0):
    return _legs_pnl(w["gf2"], 1.0 if w["win"] else 0.0, mult) if w["gf2"] else 0.0


def qty(legs):
    return sum(q for _, q in legs)


def entered(w):
    return bool(w["gf2"])


# ---------------------------------------------------------------- reports (pure)

def _thirds(rows):
    rows = sorted(rows, key=lambda r: (r[0], r[1]))
    n = len(rows)
    return [rows[i * n // 3:(i + 1) * n // 3] for i in range(3)]


def _per_contract(pnls, qs):
    tq = sum(qs)
    return sum(pnls) / tq if tq > 0 else None


def _c(x):
    return "n/a" if x is None else f"{100 * x:+.3f}c"


def gf1_report(wins):
    """wins: [(close, series, {C: window}, had_trades)] with a signal (GF1 posts an order at every signal)."""
    lines, ok = [], True
    for C in SIZES:
        W = [(c, se, w[C]) for c, se, w, _ in wins]
        plain = R6.stats([(c, se, plain_pnl(w)) for c, se, w in W])
        lines.append(f"C={C:>2} plain L1 (cross at S + 1 s, the comparison): " + R6.fmt(plain))
        for label, rate, mult in (("VERDICT maker fill pays taker 7%", TAKER, 1.0), ("stress 7% x1.2", TAKER, 1.2),
                                  ("info resting leg maker 1.75%", MAKER, 1.0), ("info resting leg zero fee", 0.0, 1.0)):
            lines.append(f"C={C:>2} GF1 {label}: " + R6.fmt(R6.stats([(c, se, gf1_pnl(w, rate, mult)) for c, se, w in W])))
        s = R6.stats([(c, se, gf1_pnl(w)) for c, se, w in W])
        st = R6.stats([(c, se, gf1_pnl(w, TAKER, 1.2)) for c, se, w in W])
        better = all(a > p for a, p in zip(s["third_net"], plain["third_net"]))
        gw = [(c, se, w) for c, se, w in W if se == GOLD]
        g_gf1 = R6.stats([(c, se, gf1_pnl(w)) for c, se, w in gw])
        g_pl = R6.stats([(c, se, plain_pnl(w)) for c, se, w in gw])
        gold_better = bool(gw) and g_gf1["per"] > g_pl["per"]
        ok &= R6.bar(s, st) and better and gold_better
        diff = sorted([(c, se, gf1_pnl(w) - plain_pnl(w)) for c, se, w in W], key=lambda r: (r[0], r[1]))
        dz = R6.clustered_z([d for *_, d in diff], [central_date(c) for c, *_ in diff])
        lines.append(f"C={C:>2} GF1 minus plain, per opportunity: {100 * sum(d for *_, d in diff) / max(1, len(diff)) / C:+.3f}c per contract "
                     f"(thirds {' / '.join(f'{100 * (a - p) / C:+.3f}' for a, p in zip(s['third_net'], plain['third_net']))}), "
                     f"z {dz:+.2f}; gold alone pooled {100 * (g_gf1['per'] - g_pl['per']) / C:+.3f}c; card gate "
                     f"{'held' if better and gold_better else 'failed'}")
        n = max(1, len(W))
        full = [w for *_, w in W if w["rest_q"] >= C - 1e-12]
        part = [w for *_, w in W if 1e-12 < w["rest_q"] < C - 1e-12]
        none = [w for *_, w in W if w["rest_q"] <= 1e-12]
        chased = [w for *_, w in W if w["chase_status"] == "cross" and w["chase"]]
        skipped = [w for *_, w in W if w["chase_status"] == "skip" or (w["chase_status"] == "cross" and not w["chase"])]
        lines.append(f"C={C:>2} signals {len(W)}: resting bid full by 30 s {len(full)} ({100 * len(full) / n:.0f}%), partial "
                     f"{len(part)} ({100 * len(part) / n:.0f}%), none {len(none)} ({100 * len(none) / n:.0f}%); chase taken "
                     f"{len(chased)} ({100 * len(chased) / n:.0f}%), skipped {len(skipped)} ({100 * len(skipped) / n:.0f}%); "
                     f"contracts not bought at the cap {sum(w['chase_unbought'] for w in chased):.0f}")
        if chased:
            vw = [(sum(p * q for p, q in w["chase"]) / qty(w["chase"]) - w["ask_s"]) for w in chased]
            lines.append(f"C={C:>2} chase price minus ask(S): mean {100 * sum(vw) / len(vw):+.2f}c, median {100 * statistics.median(vw):+.2f}c")
        rf = [w for *_, w in W if w["rest_q"] > 0]
        r_pl = [rest_pnl(w) for w in rf]
        r_plain = [plain_pnl(w) * w["rest_q"] / max(1e-12, qty(w["plain"])) for w in rf]
        rq = [w["rest_q"] for w in rf]
        c_pl = [chase_pnl(w) for w in chased]
        c_plain = [plain_pnl(w) * qty(w["chase"]) / max(1e-12, qty(w["plain"])) for w in chased]
        cq = [qty(w["chase"]) for w in chased]
        lines.append(f"C={C:>2} RESTING fills: PF {pf(r_pl):.2f}, net {_c(_per_contract(r_pl, rq))} per contract, win rate "
                     f"{100 * sum(w['win'] for w in rf) / max(1, len(rf)):.1f}%; same contracts at plain L1's price PF {pf(r_plain):.2f}, "
                     f"net {_c(_per_contract(r_plain, rq))}")
        lines.append(f"C={C:>2} CHASE fills: PF {pf(c_pl):.2f}, net {_c(_per_contract(c_pl, cq))} per contract, win rate "
                     f"{100 * sum(w['win'] for w in chased) / max(1, len(chased)):.1f}%; same contracts at plain L1's price "
                     f"PF {pf(c_plain):.2f}, net {_c(_per_contract(c_plain, cq))}")
        ex = [(c, se, w[C]) for c, se, w, tr in wins if tr]
        lines.append(f"C={C:>2} GF1 verdict fee, windows with no trades excluded: " + R6.fmt(R6.stats([(c, se, gf1_pnl(w)) for c, se, w in ex])))
        for ser in SERIES:
            sub = [(c, se, w) for c, se, w in W if se == ser]
            if sub:
                a = R6.stats([(c, se, gf1_pnl(w)) for c, se, w in sub])
                p = R6.stats([(c, se, plain_pnl(w)) for c, se, w in sub])
                lines.append(f"C={C:>2} {ser}{' (GOLD ALONE, beside the pooled verdict)' if ser == GOLD else ''}: signals {len(sub)}, "
                             f"rest full {100 * sum(1 for *_, w in sub if w['rest_q'] >= C - 1e-12) / len(sub):.0f}%, GF1 "
                             f"{100 * a['per'] / C:+.2f}c, plain {100 * p['per'] / C:+.2f}c per contract per opportunity, GF1 PF "
                             f"{a['pf']:.2f} (thirds {' / '.join(f'{t:.2f}' for t in a['thirds'])})")
    lines.append("not modelled: one crypto order per window, window cap, Bitcoin and Ethereum smooth gate, XRP pause (as L1Q1)")
    return ok, lines


def gf2_report(wins):
    """wins: [(close, series, {C: window}, had_trades)] with a signal; GF2 scores the windows where it entered."""
    lines, ok = [], True
    for C in SIZES:
        W = [(c, se, w[C]) for c, se, w, _ in wins]
        E = [(c, se, w) for c, se, w in W if entered(w)]
        s = R6.stats([(c, se, gf2_pnl(w)) for c, se, w in E])
        st = R6.stats([(c, se, gf2_pnl(w, 1.2)) for c, se, w in E])
        lines.append(f"C={C:>2} GF2 VERDICT (entries only, taker 7%): " + R6.fmt(s))
        lines.append(f"C={C:>2} GF2 stress 7% x1.2: " + R6.fmt(st))
        plain = R6.stats([(c, se, plain_pnl(w)) for c, se, w in W])
        lines.append(f"C={C:>2} plain L1 on ALL signals (the comparison): " + R6.fmt(plain))
        # gate part 1: GF2's net per contract above plain L1's (all signals) in every third of the signal windows
        third_ok, tl = True, []
        for th in _thirds(W):
            g = _per_contract([gf2_pnl(w) for *_, w in th if entered(w)], [qty(w["gf2"]) for *_, w in th if entered(w)])
            p = _per_contract([plain_pnl(w) for *_, w in th], [qty(w["plain"]) for *_, w in th])
            third_ok &= g is not None and p is not None and g > p
            tl.append(f"{_c(g)} vs {_c(p)}")
        # gate part 2: date-clustered z of the per-contract difference, linearised per window (workers/GF12_NOTES.md, item 1)
        qg = sum(qty(w["gf2"]) for *_, w in W)
        qp = sum(qty(w["plain"]) for *_, w in W)
        rows = sorted(W, key=lambda r: (r[0], r[1]))
        d = [((gf2_pnl(w) / qg) if qg > 0 and entered(w) else 0.0) - (plain_pnl(w) / qp if qp > 0 else 0.0) for *_, w in rows]
        zb = R6.clustered_z([len(d) * x for x in d], [central_date(c) for c, *_ in rows]) if qg > 0 else 0.0
        # information: the same-window difference on GF2's entry windows (what waiting 30 s costs the trades it keeps)
        same = sorted([(c, gf2_pnl(w) / qty(w["gf2"]) - plain_pnl(w) / max(1e-12, qty(w["plain"]))) for c, se, w in E])
        za = R6.clustered_z([x for _, x in same], [central_date(c) for c, _ in same])
        gw = [w for c, se, w in W if se == GOLD]
        g_g = _per_contract([gf2_pnl(w) for w in gw if entered(w)], [qty(w["gf2"]) for w in gw if entered(w)])
        g_p = _per_contract([plain_pnl(w) for w in gw], [qty(w["plain"]) for w in gw])
        gold_ok = g_g is not None and g_p is not None and g_g > g_p
        gate = third_ok and zb >= GF2_Z_GATE and gold_ok
        ok &= R6.bar(s, st) and gate
        tot_g = _per_contract([gf2_pnl(w) for *_, w in E], [qty(w["gf2"]) for *_, w in E])
        tot_p = _per_contract([plain_pnl(w) for *_, w in W], [qty(w["plain"]) for *_, w in W])
        lines.append(f"C={C:>2} GF2 entries net {_c(tot_g)} per contract against plain L1 all signals {_c(tot_p)} "
                     f"(thirds {' ; '.join(tl)}), date-clustered z of the difference {zb:+.2f} (gate {GF2_Z_GATE}); gold alone "
                     f"pooled {_c(g_g)} vs {_c(g_p)}; card gate {'held' if gate else 'failed'}")
        lines.append(f"C={C:>2} information: same-window difference on entry windows (GF2 minus plain, per contract) "
                     f"{_c(sum(x for _, x in same) / len(same)) if same else 'n/a'}, z {za:+.2f}")
        n = max(1, len(W))
        filt = [w for *_, w in W if w["gf2_status"] == "filtered"]
        skip = [w for *_, w in W if w["gf2_status"] == "skip"]
        ent = [w for *_, w in E]
        lines.append(f"C={C:>2} signals {len(W)}: entries {len(ent)} ({100 * len(ent) / n:.0f}%), dropped by the 30 s dip test "
                     f"{len(filt)} ({100 * len(filt) / n:.0f}%), skipped (out of band or over ask(S) + 1c) {len(skip)} "
                     f"({100 * len(skip) / n:.0f}%); contracts not bought at the cap {sum(w['gf2_unbought'] for w in ent):.0f}")
        if ent:
            vw = [sum(p * q for p, q in w["gf2"]) / qty(w["gf2"]) - w["ask_s"] for w in ent]
            e_pl = [gf2_pnl(w) for w in ent]
            lines.append(f"C={C:>2} entry price minus ask(S): mean {100 * sum(vw) / len(vw):+.2f}c, median {100 * statistics.median(vw):+.2f}c; "
                         f"entries PF {pf(e_pl):.2f}, win rate {100 * sum(w['win'] for w in ent) / len(ent):.1f}% (plain L1 all signals "
                         f"{100 * sum(w['win'] for *_, w in W) / n:.1f}%)")
        drop = [w for *_, w in W if not entered(w)]
        d_pl = [plain_pnl(w) for w in drop]
        lines.append(f"C={C:>2} signals GF2 did not enter, at plain L1's price: PF {pf(d_pl):.2f}, net "
                     f"{_c(_per_contract(d_pl, [qty(w['plain']) for w in drop]))} per contract, win rate "
                     f"{100 * sum(w['win'] for w in drop) / max(1, len(drop)):.1f}%")
        lines.append(f"C={C:>2} GF2 per opportunity (all signals, 0 when no entry): {100 * sum(gf2_pnl(w) for *_, w in W) / n / C:+.3f}c "
                     f"per contract against plain {100 * plain['per'] / C:+.3f}c")
        ex = [(c, se, w[C]) for c, se, w, tr in wins if tr and entered(w[C])]
        lines.append(f"C={C:>2} GF2 verdict, windows with no trades excluded: " + R6.fmt(R6.stats([(c, se, gf2_pnl(w)) for c, se, w in ex])))
        for ser in SERIES:
            sub = [w for c, se, w in W if se == ser]
            if sub:
                es = [w for w in sub if entered(w)]
                lines.append(f"C={C:>2} {ser}{' (GOLD ALONE, beside the pooled verdict)' if ser == GOLD else ''}: signals {len(sub)}, "
                             f"entries {len(es)}, GF2 entries {_c(_per_contract([gf2_pnl(w) for w in es], [qty(w['gf2']) for w in es]))} "
                             f"per contract, PF {pf([gf2_pnl(w) for w in es]):.2f}; plain all signals "
                             f"{_c(_per_contract([plain_pnl(w) for w in sub], [qty(w['plain']) for w in sub]))}")
    lines.append("not modelled: one crypto order per window, window cap, Bitcoin and Ethereum smooth gate, XRP pause (as L1Q1)")
    return ok, lines


# ---------------------------------------------------------------- readiness (book files only; no coverage, result or trade row)

def _blobs():
    R6._git("fetch", "-q", "origin", "quote-data")
    out = []
    for ln in R6._git("ls-tree", "-r", "--full-tree", "origin/quote-data").decode().splitlines():
        meta, path = ln.split("\t", 1)
        if path.startswith(R6.PREFIX) and path.endswith("/book.csv.gz"):
            out.append((path, meta.split()[2]))
    return out


def book_signals(rows):
    """rows: book.csv dicts of one run. Returns {ticker: [series, close, has S poll, signal side or ""]}. Prices only."""
    offs, near, meta = [], defaultdict(list), {}
    for x in rows:
        h = x.get("server_date_header")
        tr = int(x["t_recv_ms"]) / 1000
        if h:
            try:
                offs.append(parsedate_to_datetime(h).timestamp() + 0.5 - tr)
            except (TypeError, ValueError):
                pass
        tk = x["ticker"]
        if tk not in meta:
            meta[tk] = (x["series"], int(R6._ts(x["close_time"])))
        if abs(tr - (meta[tk][1] - SIGNAL_S)) <= 90:
            near[tk].append((tr, R6._f(x.get("yes_bid_px_1")), R6._f(x.get("no_bid_px_1"))))
    off = statistics.median(offs) if offs else None
    out = {}
    for tk, (ser, close) in meta.items():
        side, has = "", False
        if off is not None:
            ps = [Poll(t + off, [y] if y is not None else [], [1] if y is not None else [], [n] if n is not None else [],
                       [1] if n is not None else []) for t, y, n in sorted(near.get(tk, []))]
            S = R6.last_at(ps, close - SIGNAL_S, SIGNAL_GAP)
            has = S is not None
            sig = signal(ps, close) if has else None
            side = sig[0] if sig else ""
        out[tk] = [ser, close, has, side]
    return out


def count():
    try:
        cache = json.loads(COUNT_CACHE.read_text())
    except Exception:
        cache = {}
    files = _blobs()
    wins = {}
    for path, blob in files:
        if blob not in cache:
            raw = R6._git("cat-file", "blob", blob)
            cache[blob] = book_signals(csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw)))))
        for tk, v in cache[blob].items():
            if v[1] - 900 >= LAST_OPEN or v[0] not in SERIES:
                continue
            if tk not in wins or (v[2] and not wins[tk][2]):
                wins[tk] = v
    COUNT_CACHE.parent.mkdir(parents=True, exist_ok=True)
    COUNT_CACHE.write_text(json.dumps(cache))
    per = {s: sum(1 for v in wins.values() if v[0] == s and v[3]) for s in SERIES}
    n_sig = sum(per.values())
    n_s = sum(1 for v in wins.values() if v[2])
    gold_w = sum(1 for v in wins.values() if v[0] == GOLD)
    print(f"GF12 count: {len(files)} R6 book files, {len(wins)} recorded market windows (gold {gold_w}), {n_s} with a poll at "
          f"T-360 s; L1 signals {n_sig} ({', '.join(f'{s[2:-3]} {v}' for s, v in per.items())}); GF1 needs {NEEDED} orders posted "
          f"(= signals in usable windows), GF2 {NEEDED} entries (counted only at the run); book files only, no coverage or "
          f"result read, so an upper bound; earliest read {datetime.fromtimestamp(READ_NOT_BEFORE, timezone.utc):%Y-%m-%d %H:%M} UTC")
    return n_sig


# ---------------------------------------------------------------- the run (reads outcomes; once only)

def usable(close, row):
    return close - 900 < LAST_OPEN and R6.usable("l1q1", close, row)


def run(card, now=None):
    now = time.time() if now is None else now
    if card not in CARDS:
        print(__doc__)
        return
    out, mark = RESULTS[card], MARKERS[card]
    if out.exists():
        print(f"Refusing to run again: {out} exists.")
        return
    if mark.exists():
        print(f"Refusing to run again: {mark} exists (a run started before and did not write its result; the lead decides).")
        return
    if now < READ_NOT_BEFORE:
        print(f"Refusing: the read date is {datetime.fromtimestamp(READ_NOT_BEFORE, timezone.utc):%Y-%m-%d %H:%M} UTC.")
        return
    mark.parent.mkdir(parents=True, exist_ok=True)
    mark.write_text(f"{card} started {datetime.now(timezone.utc).isoformat()}\n")   # before any outcome is read

    def finish(lines):
        out.write_text("\n".join(lines) + "\n")
        print("\n".join(lines))

    ws = R6.windows()
    use = {k: v for k, v in ws.items() if usable(k[0], v[1])}
    byrun = defaultdict(list)
    for k, (r, row) in use.items():
        byrun[r].append((k, row))
    scored, no_clock, mismatch, no_signal = [], 0, 0, 0
    for r, ks in sorted(byrun.items()):
        book = R6._csv(f"{r}/book.csv.gz")
        if book and list(book[0]) != R6.BOOK_COLS:
            finish([f"{card.upper()} VERDICT NOT_RUNNABLE: recorder schema changed ({r}/book.csv.gz)"])
            return
        off = R6._offset(book)
        if off is None:
            no_clock += len(ks)
            continue
        tick = {row["ticker"]: (k, row) for k, row in ks}
        polls, trades = defaultdict(list), defaultdict(list)
        for x in book:
            if x["ticker"] in tick:
                polls[x["ticker"]].append(R6._poll(x, off))
        del book
        for x in R6._csv(f"{r}/trades.csv.gz"):
            if x["ticker"] in tick:
                trades[x["ticker"]].append((R6._ts(x["created_time"]), float(x["yes_price_dollars"]), float(x["count_fp"]),
                                            1 if x["taker_outcome_side"] == "yes" else -1))
        for tk, ((close, ser), row) in tick.items():
            ps = sorted(polls.get(tk, []), key=lambda p: p.t)
            tr = sorted(trades.get(tk, []))
            ts, vol = R6._f(row.get("tape_sum_count")), R6._f(row.get("volume_fp"))
            if ts is not None and vol and abs(ts - vol) > 0.01 * vol:
                mismatch += 1
            w = {C: simulate(ps, tr, close, row.get("result"), C) for C in SIZES}
            if w[1] is None:
                no_signal += 1
                continue
            scored.append((close, ser, w, bool(tr)))
    if use and no_clock > 0.2 * len(use):
        finish([f"{card.upper()} VERDICT NOT_RUNNABLE: {no_clock} of {len(use)} usable windows without a clock"])
        return
    if card == "gf1":
        n_order = len(scored)
        ok, lines = gf1_report(scored) if scored else (False, [])
    else:
        n_order = sum(1 for *_, w, _ in scored if entered(w[1]))
        ok, lines = gf2_report(scored) if scored else (False, [])
    verdict = "NOT_ENOUGH_DATA" if n_order < NEEDED else ("NOT_YET_FALSIFIED" if ok else "FALSIFIED")
    lines.insert(0, f"{card.upper()} VERDICT {verdict} (five markets pooled; gold reported alone below; usable windows {len(use)}, "
                    f"signals {len(scored)}, scored windows with {'an order posted' if card == 'gf1' else 'an entry'} {n_order}, "
                    f"no signal {no_signal}, no clock {no_clock}, tape and volume differ over 1% {mismatch}; minimum {NEEDED}; "
                    f"z bar {Z_BAR}; tries {TRIES[card]}, GOLDFILL 8, running count about 439,132)")
    finish(lines)


def main(argv):
    if len(argv) >= 2 and argv[1] == "count":
        count()
    elif len(argv) >= 3 and argv[1] == "run":
        run(argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
