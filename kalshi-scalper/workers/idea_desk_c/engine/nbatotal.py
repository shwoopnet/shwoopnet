#!/usr/bin/env python3
"""NBATOTAL plugin (Idea Desk C, Nov 16, 2026), build 1. Card: ../allkalshi/nbatotal/NBATOTAL_CARD.md (design CLEAN, Auditor B, 50d78b00).
Copied from the audited nbaladder.py (965d9ffe) and changed in five places: the series and jobs, the decision offsets and exit mark, the line (grouped by game,
not by player), the feature windows, and the grid (5 time and exit combinations x 4 bands x 2 sides x 13 filters = 520), plus the in-play guard.
Pre-game KXNBATOTAL rungs; D in {9 h, 5 h, 4 h} before the scheduled end (occurrence); exit H or M35 (the bid of the candle ending exactly 3.5 h before the end,
valid for D of 9 h and 5 h only). Data only through deskc_kp_load and deskc_candles_vol. Unit: the game."""
import math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL
import deskc_candles_vol as CV
import engine1_core as K

SERIES = ("KXNBATOTAL",)
LIST_JOB, LIST_ID = "KXNBATOTAL_LISTS_A", "dev_KXNBATOTAL"
CANDLE_JOBS = ("NBATOTAL_CANDLES_P1", "NBATOTAL_CANDLES_P2")
WIN = (KL.iso("2026-10-21T00:00:00"), KL.iso("2026-11-06T00:00:00"))      # close_time window, tested first
DS = (32400, 18000, 14400)                                                 # decision times, seconds before the scheduled end: 9 h, 5 h, 4 h
BANDS = ((0.30, 0.40), (0.40, 0.50), (0.50, 0.60), (0.60, 0.70))
SIDES, EXITS = ("yes", "no"), ("H", "M35")
M_VALID = (32400, 18000)                                                   # M35 only for D of 9 h and 5 h
FILTERS = ("none", "move_down", "move_flat", "move_up", "dist_below", "dist_at", "dist_above", "spread3", "spread6", "vol_rise", "vol_notrise", "age_lt24", "age_ge24")
N_RULES = (len(DS) + len(M_VALID)) * len(BANDS) * len(SIDES) * len(FILTERS)  # 5 combinations x 4 x 2 x 13 = 520
LOOKBACK_S, MOVE_S, VOL_S, MARK_S, SLIP_S = 180, 3600, 1800, 12600, 0         # move over 60 min; volume 30 min against 30 min; mark 3.5 h before the end
MOVE_T, SPREAD_A, SPREAD_B, AGE_S, GUARD_T = 0.03, 0.03, 0.06, 24 * 3600, 0.15
EPS = 1e-9
MIN_DAYS_TRADES, MIN_GAMES, MIN_N, MIN_SIGNALS, ALPHA = 10, 40, 100, 48, 0.05


def parse(t):
    """KXNBATOTAL-26NOV09CLECHA-215: the game is the event, the strike is the last segment. Returns (game key, strike)."""
    p = t.split("-")
    try:
        return p[1], int(p[2])
    except (IndexError, ValueError):
        return None, None


def games(root):
    """event -> dict(O, rungs=[rec]). Window on close_time first; clock check (one occurrence per game, exactly on :00 or :30) drops a game."""
    mk = KL.markets(root, (LIST_JOB,), SERIES, "close", *WIN)
    ev = {}
    for t, r in mk.items():
        ev.setdefault(r["event"], []).append(r)
    out, drops = {}, []
    for e, L in sorted(ev.items()):
        occs = {r["occurrence_datetime"] for r in L}
        O = min(o for o in occs if o is not None) if any(o is not None for o in occs) else None
        if O is None or len(occs) != 1 or O % 1800 != 0:
            drops.append(e)
            continue
        out[e] = {"O": O, "rungs": sorted(L, key=lambda r: r["ticker"])}
    return out, drops, len(mk)


def two(yb, ya):
    return yb is not None and ya is not None and yb > EPS and ya < 1 - EPS and ya - yb > EPS


def at(qt, ts):
    """latest two-sided candle ending in [ts - LOOKBACK_S, ts] -> (yb, ya) or None"""
    k = max((x for x in qt if ts - LOOKBACK_S <= x <= ts and two(qt[x][0], qt[x][1])), default=None)
    return None if k is None else (qt[k][0], qt[k][1])


def vol(qt, lo, hi):
    return sum(v[2] for x, v in qt.items() if lo < x <= hi)


def decisions(root):
    """Every (rung, D) decision with its features. Returns (list, counts, game dict). Reads candles for the rungs' windows, never the result."""
    g, clock_drops, listed = games(root)
    cut, rec = {}, {}
    for e, x in g.items():
        for r in x["rungs"]:
            cut[r["ticker"]] = x["O"] - MARK_S
            rec[r["ticker"]] = (e, x["O"], r)
    q = CV.candles(root, CANDLE_JOBS, cut)
    out, c = [], {"listed": listed, "clock_dropped_games": len(clock_drops), "games": len(g), "closed_by_D": 0, "no_quote": 0, "m35_dropped_games": 0}
    for e, x in g.items():
        O = x["O"]
        # the Head's guard (Nov 16, 18:40Z): a game whose real tip came more than 3.5 h before the scheduled end shows an in-play jump at the 3.5 h mark.
        # If ANY rung's last two two-sided candles ending at or before the mark differ in mid by 0.15 or more, the whole game is counted and dropped from M35 (it stays in H).
        mark_inplay = False
        for r in x["rungs"]:
            tw = sorted(k for k, v in q.get(r["ticker"], {}).items() if k <= O - MARK_S and two(v[0], v[1]))
            if len(tw) >= 2:
                a_, b_ = q[r["ticker"]][tw[-1]], q[r["ticker"]][tw[-2]]
                if abs((a_[0] + a_[1]) / 2 - (b_[0] + b_[1]) / 2) >= GUARD_T - EPS:
                    mark_inplay = True
                    break
        if mark_inplay:
            c["m35_dropped_games"] += 1
        for D_off in DS:
            D = O - D_off
            qs = {r["ticker"]: at(q.get(r["ticker"], {}), D) for r in x["rungs"] if r["close_time"] > D}
            # the game's current line at D: the rung of the same game whose YES mid is nearest 0.50 (ties to the higher strike)
            line = {}
            for r in x["rungs"]:
                qq = qs.get(r["ticker"])
                pl, k = parse(r["ticker"])
                if qq is None or pl is None:
                    continue
                d = abs((qq[0] + qq[1]) / 2 - 0.5)
                cur = line.get(pl)
                if cur is None or d < cur[0] - EPS or (abs(d - cur[0]) <= EPS and k > cur[1]):
                    line[pl] = (d, k)
            for r in x["rungs"]:
                if r["close_time"] <= D:
                    c["closed_by_D"] += 1
                    continue
                t = r["ticker"]; qt = q.get(t, {}); qq = qs.get(t)
                if qq is None:
                    c["no_quote"] += 1
                    continue
                two_ok = sorted(x for x in qt if x <= D and two(qt[x][0], qt[x][1]))
                if len(two_ok) >= 2:                                             # in-play guard (Auditor B): the last two two-sided candles before D
                    m1, m2 = (qt[two_ok[-1]][0] + qt[two_ok[-1]][1]) / 2, (qt[two_ok[-2]][0] + qt[two_ok[-2]][1]) / 2
                    if abs(m1 - m2) >= GUARD_T - EPS:
                        c["inplay_guard_%d" % (D_off // 3600)] = c.get("inplay_guard_%d" % (D_off // 3600), 0) + 1
                        continue
                prev = at(qt, D - MOVE_S)
                mv = None if prev is None else (qq[0] + qq[1]) / 2 - (prev[0] + prev[1]) / 2
                pl, k = parse(t)
                f = {"none": True}
                f["move_down"], f["move_flat"], f["move_up"] = (None, None, None) if mv is None else (mv <= -MOVE_T + EPS, abs(mv) < MOVE_T - EPS, mv >= MOVE_T - EPS)
                ln = line.get(pl)
                f["dist_below"], f["dist_at"], f["dist_above"] = (None, None, None) if ln is None else (k < ln[1], k == ln[1], k > ln[1])
                sp = qq[1] - qq[0]
                f["spread3"], f["spread6"] = sp <= SPREAD_A + EPS, sp <= SPREAD_B + EPS
                a, b = vol(qt, D - VOL_S, D), vol(qt, D - 2 * VOL_S, D - VOL_S)
                f["vol_rise"], f["vol_notrise"] = a > b, not (a > b)
                age = D - r["open_time"] if r["open_time"] is not None else None
                f["age_lt24"], f["age_ge24"] = (None, None) if age is None else (age < AGE_S, age >= AGE_S)
                mark = qt.get(O - MARK_S)
                mk = (mark[0], mark[1]) if mark and two(mark[0], mark[1]) and r["close_time"] > O - MARK_S else None
                out.append({"t": t, "game": e, "O": O, "D": D, "D_off": D_off, "close": r["close_time"], "yb": qq[0], "ya": qq[1], "f": f, "mark": mk, "m35_ok": not mark_inplay})
    c["decisions"] = len(out)
    return out, c, g


def band_ok(ask, i):
    lo, hi = BANDS[i]
    return lo - EPS <= ask < hi - EPS or (i == len(BANDS) - 1 and abs(ask - hi) <= EPS)


def net(e, side, ask, n, h_entry, exit_, mark, result):
    """-> (net dollars, reason). H settles on the result. M35 sells at the mark's bid; no mark = 'no mark' (caller decides held or dropped)."""
    ent = {"id": e["t"], "close_ts": e["close"], "day": "", "series": "KXNBATOTAL", "side": side, "ask": ask, "n": n, "entry_end": e["D"], "path": [], "result": result}
    if exit_ == "H":
        return K.score(ent, "H", h_entry, n)
    if mark is None:
        return None, "no mark"
    bid = mark[0] if side == "yes" else 1 - mark[1]
    if not (0 < bid < 1):
        return None, "no mark"
    paid = min(ask + h_entry, 0.99)
    h_ex = 0.02 if e["close"] - (e["O"] - MARK_S) <= 120 else h_entry
    s = max(bid - h_ex, 0.01)
    return round(s * n - (paid * n + K.fee_up_order(paid, n)) - K.fee_up_order(s, n), 9), "time"


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


def run(root, m_carried=0, days_window=16):
    """Enumerates all 624 cells. Reads the result LAST, for every rung that is a candidate in any cell. Returns the printable dict."""
    if KL.truncated(root, LIST_JOB, LIST_ID, WIN[0]):
        return {"stopped": "list truncated: not scored"}
    dec, counts, g = decisions(root)
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
                    if ex == "M35" and (d["D_off"] not in M_VALID or not d["m35_ok"]):
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
                if x is None and ex == "M35":                           # no mark: HELD to settlement (Auditor B), counted
                    x, why = net(d, side, ask, n_, h, "H", None, r)
                    no_mark[(D_off, bi, side, ex, fl)] = no_mark.get((D_off, bi, side, ex, fl), 0) + (1 if n_ == 10 and h == h_p else 0)
                nets.append(x)
            rows.append((d["close"], d["t"], d["game"], time.strftime("%Y-%m-%d", time.gmtime(d["D"])), nets[0], nets[1], nets[2], nets[3]))
        m = metrics(rows)
        m["cell"] = (D_off // 60, BANDS[bi], side, ex, fl)
        m["no_mark_held"] = no_mark.get((D_off, bi, side, ex, fl), 0)
        if ex == "M35":                                                  # printed both ways (Auditor B): rungs with a mark only
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
    out = {"label": "candle replay, upper bound, not fill-checked; development, spent for SIBHIT and the NBA fade and follow cards",
           "rules_in_m": N_RULES, "m_carried": m_carried, "m_total": mt, "counts": counts, "cells_with_trades": len(table), "cells_with_at_least_%d_trades" % MIN_SIGNALS: len(live),
           "cells_clearing_every_gate": len(gate), "bh_survivors": len(bh_keep), "unit": "game (z and p from game-level sums)",
           "top_by_dollars_a_week_at_5": [{"cell": m["cell"], "n": m["n"], "games": m["games"], "dollars_a_week": round(m["net5"] / (days_window / 7.0), 2), "no_mark_held": m["no_mark_held"], "marked_only": m.get("marked_only")} for m in ranked[:10]]}
    return out
