#!/usr/bin/env python3
"""SOCDRIFT plugin (Idea Desk C, Nov 16, 2026), build 1. Card: ../allkalshi/socdrift/SOCDRIFT_CARD.md (design CLEAN, Auditor B, amendment 1).
Copied from the signed nbatotal.py (c8275094) and changed: 15 soccer GAME series (winner markets: two teams and a tie), unit the game, decision times D = the last full hour at or before
K - 24 h, K - 12 h, K - 6 h with K = occurrence_datetime - 3 h (an ESTIMATE of kickoff), hourly candles, exits H (hold) or M2 (sell at the bid of the hourly candle ending at the last
hour boundary at or before K - 2 h), bands up to 0.85, 10 filters, 600 rules, the Head's live guard (a game whose winner market moves 0.15 or more in the hour before K is dropped from M2 only and
counted) and the M2 guard. close_time is never used for timing or selection (it is the full-time early close); the count of games with close_time before K is printed as information.
Data only through deskc_kp_load and deskc_candles_vol. Reads the result LAST."""
import calendar, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import deskc_candles_vol as CV
import engine1_core as K

SERIES = ("KXEPLGAME", "KXLALIGAGAME", "KXSERIEAGAME", "KXBUNDESLIGAGAME", "KXLIGUE1GAME", "KXMLSGAME", "KXLIGAMXGAME", "KXBRASILEIROGAME",
          "KXEFLTROPHYGAME", "KXUCLWGAME", "KXAPFDDHGAME", "KXEERSTEDIVGAME", "KXLIGAPORTUGALGAME", "KXLVAVIRGAME", "KXSERIECGAME")   # 15; Copa del Rey out (K wrong by more than 0.5 h)
LIST_JOB = "SOCDERIV_LISTS"
LIST_IDS = tuple("live_" + s for s in SERIES)
CANDLE_JOBS = ("SOCDRIFT_CANDLES_P1", "SOCDRIFT_CANDLES_P2")
WIN = (KL.iso("2026-09-18T00:00:00"), 1793328799)                       # close_time window [Sep 18 00:00Z, the W-CAT-SPORTS1 cut), tested first
KICK_S, HOUR = 10800, 3600                                              # K = occurrence - 3 h
DS = (86400, 43200, 21600)                                              # decision times: 24 h, 12 h, 6 h before K
BANDS = ((0.10, 0.25), (0.25, 0.40), (0.40, 0.55), (0.55, 0.70), (0.70, 0.85))
SIDES, EXITS = ("yes", "no"), ("H", "M2")
FILTERS = ("none", "move_down", "move_flat", "move_up", "spread2", "spread4", "vol_rise", "vol_notrise", "tie", "team")
N_RULES = len(DS) * len(EXITS) * len(BANDS) * len(SIDES) * len(FILTERS)  # 3 x 2 x 5 x 2 x 10 = 600
MOVE_S, VOL_S, MARK_BEFORE_K = 6 * HOUR, 3 * HOUR, 2 * HOUR             # 6 h move; volume 3 h against 3 h; exit mark 2 h before K
MOVE_T, SPREAD_A, SPREAD_B, GUARD_T = 0.02, 0.02, 0.04, 0.15
EPS = 1e-9
MIN_DAYS_TRADES, MIN_GAMES, MIN_N, MIN_SIGNALS, ALPHA = 10, 40, 100, 48, 0.05
MONTHS = {m: i for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}


def parse(t):
    """KXEPLGAME-26NOV08MUNAVL-TIE: the game is the event, the outcome is the last segment ('TIE' or a team code). Returns (game key, outcome)."""
    p = t.split("-")
    return (p[1], p[2]) if len(p) == 3 and p[1] and p[2] else (None, None)


def ticker_day(e):
    """'26NOV08MUNAVL' -> the UTC midnight of 2026-11-08, or None."""
    try:
        return calendar.timegm((2000 + int(e[0:2]), MONTHS[e[2:5]], int(e[5:7]), 0, 0, 0))
    except (KeyError, ValueError, IndexError):
        return None


def games(root):
    """event -> dict(O, K, rungs=[rec]). Window on close_time first; clock check drops a game unless occurrence is ONE value on a quarter hour and
    the ticker date is within one day of it."""
    mk = KL.markets(root, (LIST_JOB,), SERIES, "close", *WIN)
    ev = {}
    for t, r in mk.items():
        ev.setdefault(r["event"], []).append(r)
    out, drops = {}, []
    for e, L in sorted(ev.items()):
        occs = {r["occurrence_datetime"] for r in L}
        O = min(o for o in occs if o is not None) if any(o is not None for o in occs) else None
        day = ticker_day(e.split("-")[1]) if "-" in e else None
        if O is None or len(occs) != 1 or O % 900 != 0 or day is None or abs(O - day) > 2 * 86400:
            drops.append(e)
            continue
        out[e] = {"O": O, "K": O - KICK_S, "rungs": sorted(L, key=lambda r: r["ticker"])}
    return out, drops, len(mk)


def two(yb, ya):
    return yb is not None and ya is not None and yb > EPS and ya < 1 - EPS and ya - yb > EPS


def at(qt, ts):
    """the two-sided hourly candle ending in (ts - 1 h, ts] -> (yb, ya) or None"""
    k = max((x for x in qt if ts - HOUR < x <= ts and two(qt[x][0], qt[x][1])), default=None)
    return None if k is None else (qt[k][0], qt[k][1])


def vol(qt, lo, hi):
    return sum(v[2] for x, v in qt.items() if lo < x <= hi)


def mid(c):
    return (c[0] + c[1]) / 2


def jump(qt, lo, hi):
    """True if two consecutive two-sided candles ending in (lo, hi] differ in mid by GUARD_T or more."""
    tw = sorted(k for k, v in qt.items() if lo < k <= hi and two(v[0], v[1]))
    return any(abs(mid(qt[b]) - mid(qt[a])) >= GUARD_T - EPS for a, b in zip(tw, tw[1:]))


def decisions(root):
    """Every (rung, D) decision with its features. Returns (list, counts, game dict). Reads candles, never the result."""
    g, clock_drops, listed = games(root)
    cut = {r["ticker"]: x["K"] for x in g.values() for r in x["rungs"]}          # candles are read to K only (the live guard needs the hour before K)
    q = CV.candles(root, CANDLE_JOBS, cut)
    out, c = [], {"listed": listed, "clock_dropped_games": len(clock_drops), "games": len(g), "live_guard_dropped_m2": 0, "m2_dropped_games": 0,
                  "closed_before_K_info": 0, "closed_by_D": 0, "not_open": 0, "no_quote": 0}
    for e, x in g.items():
        O, Kt = x["O"], x["K"]
        Kh = Kt - Kt % HOUR                                                    # last hour boundary at or before K
        Mh = (Kt - MARK_BEFORE_K) - (Kt - MARK_BEFORE_K) % HOUR                # last hour boundary at or before K - 2 h
        if any(r["close_time"] < Kt for r in x["rungs"]):
            c["closed_before_K_info"] += 1                                     # information only (postponed or voided); never used to select
        # the Head's live guard: any winner market of the game whose mid moves 0.15 or more between the two-sided candles ending at Kh and at Kh - 1 h (the hour before K)
        live = False
        for r in x["rungs"]:
            qt_ = q.get(r["ticker"], {})
            c1_, c0_ = qt_.get(Kh), qt_.get(Kh - HOUR)
            if c1_ and c0_ and two(c1_[0], c1_[1]) and two(c0_[0], c0_[1]) and abs(mid(c1_) - mid(c0_)) >= GUARD_T - EPS:
                live = True
                break
        if live:
            c["live_guard_dropped_m2"] += 1                                    # Auditor B: a filter on the hour before K may touch the M2 exit only, never H
        m2_any = False
        for D_off in DS:
            D = Kt - D_off
            D = D - D % HOUR                                                   # the last full hour at or before K - D_off
            # M2 guard: any two consecutive two-sided candles in (D, mark] move 0.15 or more on any outcome: dropped from M2 only
            m2_guard = any(jump(q.get(r["ticker"], {}), D, Mh) for r in x["rungs"])
            m2_any = m2_any or m2_guard
            m2_ok = not (m2_guard or live)
            for r in x["rungs"]:
                if r["close_time"] <= D:
                    c["closed_by_D"] += 1
                    continue
                if r["open_time"] is not None and r["open_time"] > D:
                    c["not_open"] += 1
                    continue
                t = r["ticker"]; qt = q.get(t, {}); qq = at(qt, D)
                if qq is None:
                    c["no_quote"] += 1
                    continue
                prev = at(qt, D - MOVE_S)
                mv = None if prev is None else mid(qq) - mid(prev)
                pl, oc = parse(t)
                f = {"none": True}
                f["move_down"], f["move_flat"], f["move_up"] = (None, None, None) if mv is None else (mv <= -MOVE_T + EPS, abs(mv) < MOVE_T - EPS, mv >= MOVE_T - EPS)
                sp = qq[1] - qq[0]
                f["spread2"], f["spread4"] = sp <= SPREAD_A + EPS, sp <= SPREAD_B + EPS
                a, b = vol(qt, D - VOL_S, D), vol(qt, D - 2 * VOL_S, D - VOL_S)
                f["vol_rise"], f["vol_notrise"] = a > b, not (a > b)
                f["tie"], f["team"] = oc == "TIE", oc != "TIE"
                mark = qt.get(Mh)
                mk = (mark[0], mark[1]) if mark and two(mark[0], mark[1]) and r["close_time"] > Mh and Mh > D else None
                out.append({"t": t, "game": e, "O": O, "K": Kt, "D": D, "D_off": D_off, "Mh": Mh, "close": r["close_time"], "yb": qq[0], "ya": qq[1], "f": f, "mark": mk, "m2_ok": m2_ok})
        if m2_any:
            c["m2_dropped_games"] += 1                                         # the M2 guard fired at some decision time of this game (printed once per game)
    c["decisions"] = len(out)
    return out, c, g


def pf(xs):
    w = sum(x for x in xs if x > 1e-12)
    l = -sum(x for x in xs if x < -1e-12)
    return None if not xs else (float("inf") if l == 0 and w > 0 else (w / l if l else None))


def game_z(rows):
    by = {}
    for g, x in rows:
        by[g] = by.get(g, 0.0) + x
    v = list(by.values())
    k = len(v)
    if k < 2:
        return None
    m = sum(v) / k
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (k - 1))
    return None if sd == 0 else m / (sd / math.sqrt(k))


def metrics(rows):
    """rows: [(close, ticker, game, day, net_primary_10, net_1c_10, net_2c_10, net_5)] sorted by (close, ticker)."""
    n = len(rows)
    h = n // 2
    out = {"n": n, "games": len({r[2] for r in rows}), "trade_days": len({r[3] for r in rows})}
    for k, idx in (("p", 4), ("c1", 5), ("c2", 6)):
        xs = [r[idx] for r in rows]
        out[k] = {"pf": pf(xs), "h1": pf(xs[:h]), "h2": pf(xs[h:])}
    out["z_game"] = game_z([(r[2], r[4]) for r in rows])
    out["net5"] = sum(r[7] for r in rows)
    return out


def p_one_sided(z):
    return None if z is None else 0.5 * math.erfc(z / math.sqrt(2))


def passes(m):
    z = lambda v: 0.0 if v is None else v
    return (m["n"] >= MIN_N and m["games"] >= MIN_GAMES and m["trade_days"] >= MIN_DAYS_TRADES and z(m["p"]["pf"]) >= 1.3
            and z(m["p"]["h1"]) >= 1.0 and z(m["p"]["h2"]) >= 1.0 and z(m["c2"]["pf"]) >= 1.0)


def band_ok(ask, i):
    lo, hi = BANDS[i]
    return lo - EPS <= ask < hi - EPS or (i == len(BANDS) - 1 and abs(ask - hi) <= EPS)


def net(e, side, ask, n, h_entry, exit_, mark, result):
    """-> (net dollars, reason). H settles on the result (a void refunds the price and keeps the fee). M2 sells at the mark's bid; no mark = 'no mark' (caller holds it, counted)."""
    ent = {"id": e["t"], "close_ts": e["close"], "day": "", "series": "SOCCER", "side": side, "ask": ask, "n": n, "entry_end": e["D"], "path": [], "result": result}
    if exit_ == "H":
        return K.score(ent, "H", h_entry, n)
    if mark is None:
        return None, "no mark"
    bid = mark[0] if side == "yes" else 1 - mark[1]
    if not (0 < bid < 1):
        return None, "no mark"
    paid = min(ask + h_entry, 0.99)
    h_ex = 0.02 if e["close"] - e["Mh"] <= 120 else h_entry
    s = max(bid - h_ex, 0.01)
    return round(s * n - (paid * n + K.fee_up_order(paid, n)) - K.fee_up_order(s, n), 9), "time"


def run(root, m_carried=0, days_window=(WIN[1] - WIN[0]) / 86400.0):          # the exact span, 42.1203588 days
    """Enumerates all 600 cells. Reads the result LAST, for every rung that is a candidate in any cell. Returns the printable dict."""
    have = [i for i in LIST_IDS if any(True for _ in KL.bodies(root, LIST_JOB, i))]
    bad = [i for i in have if KL.truncated(root, LIST_JOB, i, WIN[0])]
    if bad:
        return {"stopped": "list truncated: not scored", "series": bad}
    dec, counts, g = decisions(root)
    counts["series_lists_absent"] = len(LIST_IDS) - len(have)
    res = KL.results(root, (LIST_JOB,), {d["t"] for d in dec})            # LAST
    cells = {}
    for d in dec:
        r = res.get(d["t"], "")
        if r not in ("yes", "no", "void"):
            continue
        for side in SIDES:
            ask = d["ya"] if side == "yes" else 1 - d["yb"]
            bi = next((i for i in range(len(BANDS)) if band_ok(ask, i)), None)
            if bi is None:
                continue
            for fl in FILTERS:
                if d["f"].get(fl) is not True:
                    continue
                for ex in EXITS:
                    if ex == "M2" and not d["m2_ok"]:
                        continue
                    cells.setdefault((d["D_off"], bi, side, ex, fl), []).append((d, ask, r))
    table, no_mark = [], {}
    for (D_off, bi, side, ex, fl), L in sorted(cells.items()):
        rows = []
        for d, ask, r in sorted(L, key=lambda x: (x[0]["close"], x[0]["t"])):
            h_p = 0.02 if d["close"] - d["D"] <= 120 else 0.01
            nets = []
            for n_, h in ((10, h_p), (10, 0.01), (10, 0.02), (5, 0.01)):
                x, why = net(d, side, ask, n_, h, ex, d["mark"], r)
                if x is None and ex == "M2":                           # no mark: HELD to settlement (Auditor B), counted
                    x, why = net(d, side, ask, n_, h, "H", None, r)
                    no_mark[(D_off, bi, side, ex, fl)] = no_mark.get((D_off, bi, side, ex, fl), 0) + (1 if n_ == 10 and h == h_p else 0)
                nets.append(x)
            rows.append((d["close"], d["t"], d["game"], time.strftime("%Y-%m-%d", time.gmtime(d["D"])), nets[0], nets[1], nets[2], nets[3]))
        m = metrics(rows)
        m["cell"] = (D_off // 60, BANDS[bi], side, ex, fl)
        m["no_mark_held"] = no_mark.get((D_off, bi, side, ex, fl), 0)
        if ex == "M2":                                                   # printed both ways (Auditor B): rungs with a mark only
            mrows = [r for r, (d, a, rs) in zip(rows, sorted(L, key=lambda x: (x[0]["close"], x[0]["t"]))) if d["mark"] is not None]
            mm = metrics(mrows) if mrows else None
            m["marked_only"] = None if mm is None else {"n": mm["n"], "games": mm["games"], "pf_primary": mm["p"]["pf"]}
        table.append(m)
    live = [m for m in table if m["n"] >= MIN_SIGNALS]
    ps = sorted((p_one_sided(m["z_game"]), i) for i, m in enumerate(live) if m["z_game"] is not None)
    mt = N_RULES + m_carried
    k_bh = 0
    for rank, (p, i) in enumerate(ps, 1):
        if p <= ALPHA * rank / mt:
            k_bh = rank
    bh_keep = {i for _, i in ps[:k_bh]}
    gate = [m for m in live if passes(m)]
    ranked = sorted(gate, key=lambda m: -m["net5"])
    out = {"label": "candle replay, upper bound, not fill-checked; development; closes 2026-09-18 to before the 2026-10-30T02:53:19Z cut; K = occurrence - 3 h is an estimate",
           "rules_in_m": N_RULES, "m_carried": m_carried, "m_total": mt, "counts": counts, "cells_with_trades": len(table), "cells_with_at_least_%d_trades" % MIN_SIGNALS: len(live),
           "cells_clearing_every_gate": len(gate), "bh_survivors": len(bh_keep), "unit": "game (z and p from game-level sums)",
           "top_by_dollars_a_week_at_5": [{"cell": m["cell"], "n": m["n"], "games": m["games"], "dollars_a_week": round(m["net5"] / (days_window / 7.0), 2), "no_mark_held": m["no_mark_held"], "marked_only": m.get("marked_only")} for m in ranked[:10]]}
    return out
