"""RISK1 (workers/RISK1_REGISTRATION.md): day-block bootstrap of the bot's account under the live rules on main at 2026-10-29
(gold ladder, Dogecoin 5, Ethereum 1 on the smooth climb, Bitcoin, XRP and the probes paused, gold quiet hours 20:00 to 24:00 CT,
one crypto order per window, 5.5% window cap, 12% loss stop over 24 hours with open orders counted as lost, 25c exit, pool with
the add-on cap). A risk estimate, not a strategy test: no pass bar. Research only; nothing here changes a live rule.
Usage: python -m scalper.risk1 run
"""
from __future__ import annotations

import math
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np

from . import hs1
from .analyze import valid_quote
from .lstrats import favorite
from .paths import DATA_DIR

CT = ZoneInfo("America/Chicago")
MKTS = ["KXGOLD15M", "KXDOGE15M", "KXETH15M"]          # L1_SERIES order minus PAUSED_SERIES
GOLD, DOGE, ETH = 0, 1, 2
SLIP = {"KXGOLD15M": 0.0060, "KXDOGE15M": 0.0086, "KXETH15M": 0.0087}   # workers/DRIFT.md, 30 day mean
LEFT = 360
BAND = (0.88, 0.97)
QUIET = (20, 24)                                       # QUIET_HOURS_CT gold
EXIT_LVL = 0.25
FIXED = {DOGE: 5, ETH: 1}
SIZE_FRAC, ORDER_CEIL, SIZE_CEIL, DOLLARS_PER, ADDON_FRAC = 0.02, 50, 40, 43, 0.25
REVIEW_MIN, FALL_MIN = 3 * 1440, 120
WIN_CAP, STOP_FRAC, MARGIN = 0.055, 0.12, 0.5
SEED, NPATH, HORIZON = 20261029, 10000, 90
RESULT = DATA_DIR / "risk1_result.txt"


# ---------- data ----------
def load_markets():
    by = {}
    for name in hs1.SOURCES + ["fresh"]:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        mine = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
        q = ("SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, c.volume, m.close_ts, m.result FROM candle c JOIN market m ON m.ticker = c.ticker "
             f"WHERE c.series IN ({','.join('?' * len(MKTS))}) ORDER BY c.ticker, c.end_ts")
        for s, tk, end, bc, ac, vol, close_ts, res in db.execute(q, MKTS):
            if tk in by or bc is None or ac is None:
                continue
            m = mine[tk]
            m["c"].append((end, bc, ac, vol or 0.0)); m["close"] = close_ts; m["res"] = res; m["s"] = s
        by.update(mine)
    return by


def side_mid(c, side):
    mid = (c[1] + c[2]) / 2
    return mid if side == "yes" else 1 - mid


def smooth(cs, side):
    """pathShape(...).smooth on the side's mids up to the decision candle: >= 4 earlier candles, every step >= -0.005, climb >= 0.10 (plain floats)."""
    path = [side_mid(c, side) for c in cs]
    if len(path) - 1 < 4:
        return False
    steps = [path[i] - path[i - 1] for i in range(1, len(path))]
    return min(steps) >= -0.005 and path[-1] - path[0] >= 0.10


def records(by):
    """{(ct_date, slot): {mkt index: rec}} and the list of markets per decision day (for coverage)."""
    out = defaultdict(dict)
    cover = defaultdict(lambda: defaultdict(int))
    for tk, m in by.items():
        if m["res"] not in ("yes", "no"):
            continue
        k = MKTS.index(m["s"])
        close = m["close"]
        t = close - LEFT
        dt = datetime.fromtimestamp(t, CT)
        mod = dt.hour * 60 + dt.minute
        if (mod - 9) % 15:
            continue
        day, slot = dt.date(), (mod - 9) // 15
        cover[day][k] += 1
        cs = m["c"]
        dec = next((c for c in cs if c[0] == t), None)
        if dec is None:
            continue
        f = favorite(dec[1], dec[2], BAND)
        if f is None:
            continue
        side, price = f
        won = 1.0 if m["res"] == side else 0.0
        sb_exit = math.nan
        for c in cs:
            if t < c[0] <= close - 60 and valid_quote(c[1], c[2]):          # the exit watch skips a quote bot.validQuote rejects
                sb = c[1] if side == "yes" else round(1 - c[2], 4)
                if 0 < sb <= EXIT_LVL + 1e-9:
                    sb_exit = sb
                    break
        rec = {"side": side, "price": price, "limit": math.ceil(round(price * 100, 6) - 1e-9) / 100, "won": won, "exit": sb_exit,
               "zv": dec[3] <= 0, "quiet": QUIET[0] <= dt.hour < QUIET[1],
               "smooth": smooth([c for c in cs if c[0] <= t], side) if k == ETH else True, "close": close}
        out[(day, slot)][k] = rec
    return out, cover


def fee_total(p, c):
    """7% x C x p x (1-p), rounded up to the cent per order (kalshiSignalLib.takerFee). Vectorised."""
    return np.ceil(np.round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def build_arrays(recs, days):
    """Arrays [day, slot, mkt]: eligible (live filters), limit, paid price, won, exit bid (nan = none), zero volume."""
    nd = len(days)
    el = np.zeros((nd, 96, 3), bool); lim = np.zeros((nd, 96, 3)); pp = np.zeros((nd, 96, 3)); won = np.zeros((nd, 96, 3))
    ex = np.full((nd, 96, 3), np.nan); zv = np.zeros((nd, 96, 3), bool)
    di = {d: i for i, d in enumerate(days)}
    for (day, slot), mk in recs.items():
        if day not in di:
            continue
        i = di[day]
        for k, r in mk.items():
            ok = not (k == GOLD and r["quiet"]) and r["smooth"]
            el[i, slot, k] = ok
            lim[i, slot, k] = r["limit"]; pp[i, slot, k] = r["price"] + SLIP[MKTS[k]]
            won[i, slot, k] = r["won"]; ex[i, slot, k] = r["exit"]; zv[i, slot, k] = r["zv"]
    return {"el": el, "lim": lim, "pp": pp, "won": won, "ex": ex, "zv": zv}


def per_contract_table(A, days, thirds):
    """Step 1 tallies, 1 contract each, with the live filters and the one-crypto rule (Dogecoin first)."""
    el = A["el"].copy()
    el[:, :, ETH] &= ~el[:, :, DOGE]
    p = A["pp"]; fin = fee_total(p, 1)
    ex = A["ex"]; hasx = ~np.isnan(ex)
    sb = np.where(hasx, ex, 0.0)
    net = np.where(hasx, sb - fee_total(sb, 1) - p - fin, A["won"] - p - fin)
    lines = ["| Market | Pool | Entries | Days | Lost at settle | Exits | Exit losses | Mean net c/contract | PF |", "|---|---|---|---|---|---|---|---|---|"]
    groups = [("ALL", list(range(len(days))))] + [(f"T{j + 1}", t) for j, t in enumerate(thirds)]
    for k, name in enumerate(MKTS):
        for g, idx in groups:
            m = el[idx, :, k]; x = net[idx, :, k][m]
            w = x[x > 0].sum(); l = -x[x < 0].sum()
            lost = ((A["won"][idx, :, k] == 0) & ~hasx[idx, :, k] & m).sum()
            nx = (hasx[idx, :, k] & m).sum(); nxl = (hasx[idx, :, k] & m & (net[idx, :, k] < 0)).sum()
            lines.append(f"| {name} | {g} | {m.sum()} | {len(idx)} | {lost} | {nx} | {nxl} | {100 * x.mean():+.2f} | {w / l if l else float('inf'):.2f} |")
    return "\n".join(lines)


# ---------- simulation ----------
def simulate(A, pool_days, start, variant, rng_days, zero_vol_unfilled=False):
    """variant: 'DAY' (stop: off to the end of the CT day, restart reseeded next day), 'END' (off to the end), 'NONE' (no stop).
    rng_days: (P, H) indices into A's day axis. Returns dict of per-path arrays at 30/60/90 days."""
    P, H = rng_days.shape
    el_all, lim_all, pp_all, won_all, ex_all = A["el"], A["lim"], A["pp"], A["won"], A["ex"]
    if zero_vol_unfilled:
        el_all = el_all & ~A["zv"]
    cash = np.full(P, float(start)); saved = np.zeros(P); pool = np.zeros(P); cum = np.zeros(P); hwm = np.zeros(P)
    target0 = max(1, min(SIZE_CEIL, math.floor(start / DOLLARS_PER + 1e-9)))
    cap = np.full(P, float(target0)); base = np.full(P, float(start)); reviewed = np.zeros(P); low_since = np.full(P, np.nan)
    active = np.ones(P, bool); nstops = np.zeros(P, int)
    ring = np.zeros((P, 96)); ring_al = np.zeros((P, 96))
    peak = cash.copy(); maxdd = np.zeros(P); maxdd_pct = np.zeros(P)
    out = {}
    ar = np.arange(P)
    step = 0
    gold_sz = np.zeros(P)
    for d in range(H):
        di = rng_days[:, d]
        for s in range(96):
            T = d * 1440 + 9 + 15 * s
            if variant == "DAY" and s == 0:
                rs = ~active
                if rs.any():
                    c = np.maximum(0, cash[rs] - saved[rs]); tgt = np.clip(np.floor(c / DOLLARS_PER + 1e-9), 1, SIZE_CEIL)
                    cap[rs] = np.clip(np.maximum(cap[rs], tgt), 1, SIZE_CEIL); base[rs] = c; reviewed[rs] = T; low_since[rs] = np.nan
                    ring[rs] = 0; ring_al[rs] = 0; active[rs] = True
            # reviewSizing on cash minus savings (active sessions only: the tick does not run when the bot is off)
            c = np.maximum(0, cash - saved); tgt = np.clip(np.floor(c / DOLLARS_PER + 1e-9), 1, SIZE_CEIL)
            low = active & (tgt < cap)
            low_since = np.where(low & np.isnan(low_since), T, low_since)
            conf = low & (T - low_since >= FALL_MIN)
            cap = np.where(conf, tgt, cap); base = np.where(conf, c, base); low_since = np.where(conf, np.nan, low_since)
            hi = active & ~low                         # if / else on the cap BEFORE this review, as reviewSizing
            low_since = np.where(hi, np.nan, low_since)
            due = hi & (T - reviewed >= REVIEW_MIN)
            base = np.where(due, c, base); reviewed = np.where(due, T, reviewed)
            cap = np.where(due & (tgt > cap), np.minimum(cap + 1, tgt), cap)
            cap = np.clip(cap, 1, SIZE_CEIL)
            # pre-check stop (orders of the last 96 windows, all settled)
            stop_at = STOP_FRAC * base
            if variant != "NONE":
                fire = active & (ring.sum(1) <= -(stop_at + ring_al.sum(1)) + 1e-9)
                if fire.any():
                    active &= ~fire; pool[fire] = 0; nstops += fire
            el = el_all[di, s]                      # (P, 3)
            lim = lim_all[di, s]; pp = pp_all[di, s]; won = won_all[di, s]; ex = ex_all[di, s]
            used = np.zeros(P); cash_left = cash.copy(); crypto = np.zeros(P, bool)
            counts = np.zeros((P, 3)); afrac = np.zeros((P, 3))
            addon = np.minimum(np.floor(pool / 0.93 + 1e-9), np.floor(cap * ADDON_FRAC + 1e-9))
            for k in (GOLD, DOGE, ETH):
                go = active & el[:, k]
                if k == ETH:
                    go &= ~crypto
                if not go.any():
                    continue
                w = lim[:, k]
                cost1 = w + fee_total(w, 1)
                if k == GOLD:
                    b2 = np.maximum(1, np.minimum(np.minimum(cap, ORDER_CEIL), np.floor(cash_left * SIZE_FRAC / cost1 + 1e-9)))
                    cnt = np.minimum(b2 + np.minimum(addon, np.floor(b2 * ADDON_FRAC + 1e-9)), ORDER_CEIL)
                    au = cnt - b2
                else:
                    cnt = np.full(P, float(FIXED[k])); au = np.zeros(P)
                room = WIN_CAP * base - used
                allowed = np.maximum(np.where(used <= 0, 1, 0), np.floor(room / cost1 + 1e-9))
                over = cnt - au > allowed
                skip = over & (allowed + au < 1)
                cnt = np.where(over & ~skip, allowed + au, cnt)
                lock = ORDER_CEIL if k == GOLD else FIXED[k]
                skip |= (cnt < 1) | (cnt > lock)
                cost = w * cnt + fee_total(w, cnt)
                skip |= cash_left < cost + MARGIN
                go &= ~skip
                counts[:, k] = np.where(go, cnt, 0)
                afrac[:, k] = np.where(go & (cnt > 0), au / np.maximum(cnt, 1), 0)
                addon_cost = cost * afrac[:, k]
                used = np.where(go, used + cost - addon_cost, used)
                cash_left = np.where(go, cash_left - cost, cash_left)
                if k == GOLD:
                    gold_sz = np.where(go, cnt, gold_sz)
                if k == DOGE:
                    crypto |= go
            C = counts
            paid = np.where(C > 0, pp * C + fee_total(pp, C), 0.0)
            hasx = ~np.isnan(ex)
            sb = np.where(hasx, ex, 0.0)
            proceeds = np.where(hasx, sb * C - fee_total(sb, C), won * C)
            pnl = np.where(C > 0, proceeds - paid, 0.0)
            # post-entry check, one minute later: the oldest window has left the 24 hours, this window is open and counted as lost
            pos = step % 96
            if variant != "NONE":
                net_after = ring.sum(1) - ring[:, pos]
                al_after = ring_al.sum(1) - ring_al[:, pos] + (paid * afrac).sum(1)
                fire = active & (C.sum(1) > 0) & (net_after - paid.sum(1) <= -(stop_at + al_after) + 1e-9)
                if fire.any():
                    active &= ~fire; pool[fire] = 0; nstops += fire
            # settle: fold in client order id order (DOGE, ETH, GOLD)
            for k in (DOGE, ETH, GOLD):
                x = pnl[:, k]; o = C[:, k] > 0
                cum = np.where(o, cum + x, cum)
                rise = np.where(o & (cum > hwm), cum - hwm, 0.0)
                saved += 0.5 * rise; hwm = np.maximum(hwm, np.where(o, cum, hwm))
                pool = np.where(o & (x > 0), pool + 0.5 * x, pool)
                pool = np.where(o & (x < 0), np.maximum(0, pool + x), pool)
            lost_al = np.where(hasx, np.where(pnl < 0, -pnl * afrac, 0.0), np.where((won == 0) & (C > 0), paid * afrac, 0.0)).sum(1)
            ring[:, pos] = pnl.sum(1); ring_al[:, pos] = lost_al
            cash = cash + pnl.sum(1)
            peak = np.maximum(peak, cash)
            dd = peak - cash
            maxdd = np.maximum(maxdd, dd); maxdd_pct = np.maximum(maxdd_pct, dd / peak)
            step += 1
        if d + 1 in (30, 60, 90):
            out[d + 1] = {"net": cash - start, "stops": nstops.copy(), "dd": maxdd.copy(), "ddp": maxdd_pct.copy(), "cap": cap.copy(), "gold": gold_sz.copy()}
    return out


def summarize(r, start):
    n = r["net"]
    q = np.percentile(n, [5, 25, 50, 75, 95])
    return {"p5": q[0], "p25": q[1], "p50": q[2], "p75": q[3], "p95": q[4], "mean": n.mean(), "stop1": (r["stops"] > 0).mean(), "nstops": r["stops"].mean(),
            "dd50": np.median(r["dd"]), "dd95": np.percentile(r["dd"], 95), "ddp50": np.median(r["ddp"]), "ddp95": np.percentile(r["ddp"], 95),
            "below": (n < 0).mean(), "cap": r["cap"].mean()}


def main(argv):
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    t0 = time.time()
    by = load_markets()
    recs, cover = records(by)
    alld = sorted(cover)
    # full days: not the first or last day of the files, and Dogecoin (every day of the week) has at least 85 of its 96 markets
    days = [d for d in alld[1:-1] if cover[d][DOGE] >= 85]
    A = build_arrays(recs, days)
    n3 = len(days)
    thirds = [list(range(0, n3 // 3)), list(range(n3 // 3, 2 * n3 // 3)), list(range(2 * n3 // 3, n3))]
    lines = [f"RISK1 run {datetime.now(CT):%Y-%m-%d %H:%M} CT. Full CT days: {len(days)} ({days[0]} to {days[-1]}); thirds: "
             + ", ".join(f"T{j + 1} {days[t[0]]} to {days[t[-1]]} ({len(t)} days)" for j, t in enumerate(thirds)),
             "Coverage (markets per day, gold/doge/eth, days under 90): " + ", ".join(f"{d}: {cover[d][0]}/{cover[d][1]}/{cover[d][2]}" for d in days if min(cover[d][1], cover[d][2]) < 90),
             "", "## Step 1: per-window outcomes at 1 contract (live filters, one crypto order per window, slippage and fees)", per_contract_table(A, days, thirds), ""]
    print("\n".join(lines), flush=True)
    rng = np.random.default_rng(SEED)
    pools = {"ALL": np.arange(n3), "T1": np.array(thirds[0]), "T2": np.array(thirds[1]), "T3": np.array(thirds[2])}
    draws = {k: v[rng.integers(0, len(v), size=(NPATH, HORIZON))] for k, v in pools.items()}
    res = {}
    for pool_name, dr in draws.items():
        for start in (528, 1028):
            for var in ("DAY", "END", "NONE"):
                r = simulate(A, None, start, var, dr)
                res[(pool_name, start, var)] = {h: summarize(r[h], start) for h in r}
                print(f"done {pool_name} {start} {var} {time.time() - t0:.0f}s", flush=True)
    for start in (528, 1028):
        for var in ("DAY", "END", "NONE"):
            r = simulate(A, None, start, var, draws["ALL"], zero_vol_unfilled=True)
            res[("ALL_ZV", start, var)] = {h: summarize(r[h], start) for h in r}
    hdr = "| Days | Start | Horizon | Stop rule | p5 | p25 | median | p75 | p95 | mean | stop >=1 | stops/path | worst DD median | worst DD p95 | DD% median | DD% p95 | below start | stop cost | gold cap end |"
    tab = [hdr, "|" + "---|" * 19]
    for pool_name in ("ALL", "T1", "T2", "T3", "ALL_ZV"):
        for start in (528, 1028):
            for h in (30, 60, 90):
                for var in ("DAY", "END", "NONE"):
                    s = res[(pool_name, start, var)][h]
                    cost = s["mean"] - res[(pool_name, start, "NONE")][h]["mean"] if var != "NONE" else float("nan")
                    tab.append(f"| {pool_name} | ${start} | {h}d | {var} | {s['p5']:+.0f} | {s['p25']:+.0f} | {s['p50']:+.0f} | {s['p75']:+.0f} | {s['p95']:+.0f} | {s['mean']:+.1f} | "
                               f"{100 * s['stop1']:.1f}% | {s['nstops']:.2f} | ${s['dd50']:.0f} | ${s['dd95']:.0f} | {100 * s['ddp50']:.1f}% | {100 * s['ddp95']:.1f}% | {100 * s['below']:.1f}% | "
                               + ("" if var == "NONE" else f"{cost:+.1f}") + f" | {s['cap']:.1f} |")
    lines += ["## Step 2: bootstrap (net in dollars at the horizon; DD = worst peak-to-trough of the balance)", *tab, f"", f"runtime {time.time() - t0:.0f}s"]
    RESULT.write_text("\n".join(lines) + "\n")
    print("\n".join(tab))


if __name__ == "__main__":
    main(sys.argv)
