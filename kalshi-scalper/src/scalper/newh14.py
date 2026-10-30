"""NEWH14: volatility structures across the strikes of the hourly Bitcoin ladder (NOVIEW), and the GOLD2 count (research only).

Registration: workers/NEWH14_REGISTRATION.md (pushed before any scoring). Result: workers/NEWH14_RESULT.md.

    PYTHONPATH=src python -m scalper.newh14 counts    (events per stage by close time only; no quote, no spot, no result)
    PYTHONPATH=src python -m scalper.newh14 goldd     (GOLD2: count KXGOLDD daily closes on file and in Kalshi's public list; no quote, no result)
    PYTHONPATH=src python -m scalper.newh14 dv        (discovery and validation, scored once, plus the two information looks)
    PYTHONPATH=src python -m scalper.newh14 holdout NAME...   (frozen holdout, read once, only for a rule that passed dv)

Tries (3): STRANGLE-RV, CONDOR-RV, CONDOR-ALWAYS. Information looks (2, counted): I1 STRANGLE-ALWAYS (the mirror of
CONDOR-ALWAYS), I2 the market's P(inside) against the realised frequency, by bucket.

A structure is two legs on two strikes of the same hourly event, bought at the asks of the candle AFTER the signal candle,
held to settlement. The one-minute ladder candles carry no sizes, so a 10 contract fill on each leg is MODELLED, not observed.
"""
from __future__ import annotations

import math
import sqlite3
import statistics
import sys
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timezone
from statistics import NormalDist

from .paths import DATA_DIR
from .newh9 import stage, day, fee, net, pf, dayz, summ, fmt, zbar, load_ladder, START, END

N01 = NormalDist()
N_RUNNING_BEFORE = 728_623            # ledger after GEN11 (CENSUS 2026-10-30)
N_THIS = 5                            # 3 tries + 2 information looks (registered)

# rule constants (fixed in the registration)
SIG_LEADS = list(range(2700, 1800 - 1, -60))   # signal candles ending 45 to 30 minutes before the close, first signal wins
ALWAYS_LEAD = 2700                             # the unconditional structures look once, at 45 minutes
HI_TARGET, HI_BAND = 0.25, (0.15, 0.40)        # K_hi: the strike whose YES mid is nearest 0.25 (the upper wing)
LO_TARGET, LO_BAND = 0.75, (0.60, 0.85)        # K_lo: the strike whose YES mid is nearest 0.75 (the lower wing is its NO side)
MAX_SPREAD = 0.06                              # at the signal AND the fill candle, both strikes; else no trade
EDGE = 0.05                                    # model minus market, per set, before fees
RV_MINUTES = 1440                              # trailing realised volatility window (Coinbase BTC-USD 1 minute closes)
RV_MIN = 1200                                  # fewer returns than this: no model, counted
SPOT_SRC = "CB"                                # Coinbase BTC-USD (a BRTI constituent); Deribit perpetual not used


def _utc(ts):
    return datetime.fromtimestamp(ts, timezone.utc)


# ---------------------------------------------------------------- spot (public, newh7.sqlite, stamped by bar START)

def load_spot():
    db = sqlite3.connect(DATA_DIR / "newh7.sqlite")
    rows = db.execute("select ts, v from m1 where src=? order by ts", (SPOT_SRC,)).fetchall()
    ts = [r[0] + 60 for r in rows]            # the bar starting at ts ends at ts + 60: known from then on
    px = [r[1] for r in rows]
    return ts, px


def spot_at(S, t):
    """Close of the last spot bar that ENDED at or before t, and the trailing 1 minute log-return sd. None if thin."""
    ts, px = S
    i = bisect_right(ts, t) - 1
    if i < RV_MIN:
        return None
    if ts[i] < t - 120:                        # no bar in the last two minutes: no spot
        return None
    j = max(0, i - RV_MINUTES)
    rets = [math.log(px[k] / px[k - 1]) for k in range(j + 1, i + 1) if px[k] > 0 and px[k - 1] > 0]
    if len(rets) < RV_MIN:
        return None
    return px[i], statistics.pstdev(rets)


def p_inside(s_px, sd1, k_lo, k_hi, t_left_s):
    """Model P(K_lo < settlement <= K_hi): zero drift, sigma = sd1 * sqrt(minutes), settlement a 60 s average."""
    m = t_left_s / 60.0
    var_m = max(m - 1 + 1.0 / 3.0, 1.0 / 3.0)  # time average over the last minute of a Brownian path
    s = sd1 * math.sqrt(var_m)
    if s <= 0:
        return None
    return N01.cdf(math.log(k_hi / s_px) / s) - N01.cdf(math.log(k_lo / s_px) / s)


# ---------------------------------------------------------------- the structures

def pick_wings(q):
    """At one candle: K_hi (YES mid nearest HI_TARGET inside HI_BAND) and K_lo (nearest LO_TARGET inside LO_BAND), both with
    0 < bid < ask < 1 and spread <= MAX_SPREAD, K_lo < K_hi. Returns (k_lo, k_hi) or None."""
    best_hi = best_lo = None
    for k in sorted(q):
        b, a, v = q[k]
        if not (0 < b < a < 1) or a - b > MAX_SPREAD + 1e-9:
            continue
        m = (b + a) / 2
        if HI_BAND[0] - 1e-9 <= m <= HI_BAND[1] + 1e-9:
            d = abs(m - HI_TARGET)
            if best_hi is None or d < best_hi[0] - 1e-12:
                best_hi = (d, k)
        if LO_BAND[0] - 1e-9 <= m <= LO_BAND[1] + 1e-9:
            d = abs(m - LO_TARGET)
            if best_lo is None or d < best_lo[0] - 1e-12:
                best_lo = (d, k)
    if best_hi is None or best_lo is None or not best_lo[1] < best_hi[1]:
        return None
    return best_lo[1], best_hi[1]


def legs_at(q, k_lo, k_hi, kind):
    """Asks of the two legs at one candle, or None if a leg is unquoted or wider than MAX_SPREAD.
    STRANGLE: YES at K_hi and NO at K_lo (pays 1 if the settlement is outside (K_lo, K_hi], else 0).
    CONDOR:   YES at K_lo and NO at K_hi (pays 2 inside, 1 outside)."""
    if k_lo not in q or k_hi not in q:
        return None
    blo, alo, vlo = q[k_lo]
    bhi, ahi, vhi = q[k_hi]
    for b, a in ((blo, alo), (bhi, ahi)):
        if not (0 < b < a < 1) or a - b > MAX_SPREAD + 1e-9:
            return None
    if kind == "STRANGLE":
        return [ahi, round(1 - blo, 6)], min(vlo, vhi)
    return [alo, round(1 - bhi, 6)], min(vlo, vhi)


def payoff(e, k_lo, k_hi, kind):
    yes_lo = e["res"][k_lo] == "yes"
    yes_hi = e["res"][k_hi] == "yes"
    if kind == "STRANGLE":
        return int(yes_hi or not yes_lo)
    return int(yes_lo) + int(not yes_hi)


def structure_trade(ev, S, close, kind, model, leads):
    """One trade per event. For each signal candle (ending `lead` s before the close) pick the wings; with `model`, require the
    model's edge over the market's set price at the signal candle to be at least EDGE; fill both legs at the NEXT candle's asks.
    Returns (trade or None, reason)."""
    e = ev[close]
    saw_wings = False
    for lead in leads:
        q = e["q"].get(close - lead)
        if not q:
            continue
        w = pick_wings(q)
        if w is None:
            continue
        saw_wings = True
        k_lo, k_hi = w
        sig = legs_at(q, k_lo, k_hi, kind)
        if sig is None:
            continue
        edge = None
        if model:
            sp = spot_at(S, close - lead)
            if sp is None:
                return None, "no spot"
            pin = p_inside(sp[0], sp[1], k_lo, k_hi, lead - 60)
            if pin is None:
                return None, "no spot"
            fair = (1 - pin) if kind == "STRANGLE" else (1 + pin)
            edge = fair - sum(sig[0])
            if edge < EDGE - 1e-12:
                continue
        f = e["q"].get(close - lead + 60)
        fill = legs_at(f, k_lo, k_hi, kind) if f else None
        if fill is None:
            return None, "no fill"
        legs, fv = fill
        return {"close": close, "stage": stage(close), "legs": legs, "payoff": payoff(e, k_lo, k_hi, kind),
                "zv": sig[1] <= 0 or fv <= 0, "k_lo": k_lo, "k_hi": k_hi, "lead": lead, "edge": edge,
                "sig_cost": sum(sig[0])}, "ok"
    return None, ("no signal" if saw_wings else "no wings")


def run_rule(ev, S, kind, model, leads):
    tr, info = [], defaultdict(int)
    for close in sorted(ev):
        if close < START or close >= END:
            continue
        info["events"] += 1
        t, why = structure_trade(ev, S, close, kind, model, leads)
        info[why] += 1
        if t:
            tr.append(t)
    return tr, dict(info)


ARMS = {
    "STRANGLE-RV": ("STRANGLE", True, SIG_LEADS),
    "CONDOR-RV": ("CONDOR", True, SIG_LEADS),
    "CONDOR-ALWAYS": ("CONDOR", False, [ALWAYS_LEAD]),
}
INFO = {
    "I1 STRANGLE-ALWAYS": ("STRANGLE", False, [ALWAYS_LEAD]),
}


# ---------------------------------------------------------------- commands

def loads():
    return load_ladder("conf2_lad.sqlite", "lad2.sqlite")


def counts():
    ev = loads()
    cl = [c for c in ev if START <= c < END]
    print("KXBTCD hourly events on file by close time:",
          {st: sum(stage(c) == st for c in cl) for st in ("disc", "val", "hold")},
          "first", _utc(min(cl)).strftime("%Y-%m-%d %H:%M"), "last", _utc(max(cl)).strftime("%Y-%m-%d %H:%M"), "UTC")
    S = load_spot()
    print(f"spot {SPOT_SRC} 1 minute bars: {len(S[0]):,}, {_utc(S[0][0]).strftime('%Y-%m-%d %H:%M')} to "
          f"{_utc(S[0][-1]).strftime('%Y-%m-%d %H:%M')} UTC (closes after the last bar have no model)")


def goldd():
    """GOLD2 precondition: KXGOLDD daily closes on file (local databases) and in Kalshi's public market list. No quote, no result."""
    import glob
    from . import api
    seen = {}
    for f in sorted(glob.glob(str(DATA_DIR / "*.sqlite"))):
        try:
            db = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
            for (t,) in db.execute("select name from sqlite_master where type='table'"):
                cols = [c[1] for c in db.execute(f"pragma table_info({t})")]
                if "ticker" in cols and "close_ts" in cols:
                    n = db.execute(f"select count(distinct close_ts) from {t} where ticker like 'KXGOLDD-%'").fetchone()[0]
                    if n:
                        seen[f"{f.split('/')[-1]}:{t}"] = n
        except Exception as ex:  # noqa: BLE001
            print("skip", f, ex)
    print("local KXGOLDD distinct close times by file:table:", seen)
    # public list of settled KXGOLDD markets (event count = distinct close times); at most a handful of requests
    closes, cursor, n_mk = set(), None, 0
    for _ in range(40):
        params = {"series_ticker": "KXGOLDD", "status": "settled", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        js = api._get("/markets", params)
        for m in js.get("markets", []):
            n_mk += 1
            closes.add(m.get("close_time") or m.get("expiration_time"))
        cursor = js.get("cursor")
        if not cursor:
            break
        import time
        time.sleep(0.6)
    days = sorted({(c or "")[:10] for c in closes})
    print(f"Kalshi public list: {n_mk} settled KXGOLDD markets, {len(closes)} distinct close times, {len(days)} distinct days, "
          f"first {days[0] if days else None}, last {days[-1] if days else None}")
    d_disc = sum(1 for d in days if d < "2026-09-21")
    d_val = sum(1 for d in days if "2026-09-21" <= d < "2026-10-18")
    print(f"days by stage: discovery {d_disc}, validation {d_val}, holdout {len(days) - d_disc - d_val}; "
          f"discovery plus validation {d_disc + d_val} against the 100 needed")


def verdict_dv(d, v):
    if d["n"] < 100:
        return "NOT_ENOUGH_DATA"
    if d["pf10"] < 1.5 or d["netx"] <= 0:
        return "FALSIFIED"
    if v["n"] < 50:
        return "NOT_ENOUGH_DATA"
    if v["pf10"] < 1.5 or v["netx"] <= 0:
        return "FALSIFIED"
    return "PASSED_DV"


def dv_only(tr):
    return [t for t in tr if t["stage"] in ("disc", "val")]


def _report(name, kind, tr, info):
    tr_h = sum(t["stage"] == "hold" for t in tr)
    tr = dv_only(tr)
    d = summ([t for t in tr if t["stage"] == "disc"])
    v = summ([t for t in tr if t["stage"] == "val"])
    print(f"{name}: {info} (funnel includes holdout events; holdout trades not scored: {tr_h})")
    print(f"  disc: {fmt(d)}")
    print(f"  val : {fmt(v)}")
    for st in ("disc", "val"):
        x = [t for t in tr if t["stage"] == st]
        if x:
            ed = [t["edge"] for t in x if t["edge"] is not None]
            print(f"  {st}: mean set cost at fill {statistics.mean(sum(t['legs']) for t in x):.3f}, mean set cost at signal "
                  f"{statistics.mean(t['sig_cost'] for t in x):.3f}, mean payoff {statistics.mean(t['payoff'] for t in x):.3f}, "
                  f"inside share {statistics.mean((1 - t['payoff']) if kind == 'STRANGLE' else (t['payoff'] - 1) for t in x):.3f}"
                  + (f", mean model edge at signal {statistics.mean(ed):.3f}" if ed else "")
                  + f", median lead {statistics.median(t['lead'] for t in x):.0f} s")
    return d, v


def dv():
    ev = loads()
    S = load_spot()
    N = N_RUNNING_BEFORE + N_THIS
    print(f"NEWH14 dv (once). running N {N:,}; deflated one-sided z bar {zbar(N):.2f}\n")
    for name, (kind, model, leads) in ARMS.items():
        tr, info = run_rule(ev, S, kind, model, leads)
        d, v = _report(name, kind, tr, info)
        print(f"  VERDICT after discovery and validation: {verdict_dv(d, v)}\n")
    for name, (kind, model, leads) in INFO.items():
        tr, info = run_rule(ev, S, kind, model, leads)
        _report(name + " (information)", kind, tr, info)
        print()
    # I2: the market's P(inside) at the 45 minute candle against the realised frequency, by bucket (discovery and validation)
    print("I2 (information): market P(inside) = mid(K_lo) - mid(K_hi) at the 45 minute candle against the settled frequency, "
          "and the realised-vol model's P(inside), discovery and validation events")
    rows = []
    for close in sorted(ev):
        if not (START <= close < END) or stage(close) == "hold":
            continue
        e = ev[close]
        q = e["q"].get(close - ALWAYS_LEAD)
        if not q:
            continue
        w = pick_wings(q)
        if w is None:
            continue
        k_lo, k_hi = w
        mk = (q[k_lo][0] + q[k_lo][1]) / 2 - (q[k_hi][0] + q[k_hi][1]) / 2
        inside = int(e["res"][k_lo] == "yes" and e["res"][k_hi] == "no")
        sp = spot_at(S, close - ALWAYS_LEAD)
        pm = p_inside(sp[0], sp[1], k_lo, k_hi, ALWAYS_LEAD - 60) if sp else None
        rows.append((mk, inside, pm))
    for lo, hi in ((0.30, 0.40), (0.40, 0.50), (0.50, 0.60), (0.60, 0.70)):
        x = [r for r in rows if lo <= r[0] < hi]
        if x:
            pms = [r[2] for r in x if r[2] is not None]
            print(f"  market P(inside) {lo:.2f} to {hi:.2f}: n {len(x)}, market mean {statistics.mean(r[0] for r in x):.3f}, "
                  f"settled inside {statistics.mean(r[1] for r in x):.3f}"
                  + (f", model mean {statistics.mean(pms):.3f} on {len(pms)}" if pms else ""))
    pm_all = [r for r in rows if r[2] is not None]
    if pm_all:
        gap = [r[2] - r[0] for r in pm_all]
        print(f"  all {len(rows)} events; model minus market P(inside): mean {statistics.mean(gap):+.3f}, "
              f"sd {statistics.pstdev(gap):.3f}; share with model wider than market by 5c+ {statistics.mean(g <= -0.05 for g in gap):.2f}, "
              f"narrower by 5c+ {statistics.mean(g >= 0.05 for g in gap):.2f}")


def holdout(names):
    ev = loads()
    S = load_spot()
    N = N_RUNNING_BEFORE + N_THIS
    for name in names:
        kind, model, leads = ARMS[name]
        tr, info = run_rule(ev, S, kind, model, leads)
        h = summ([t for t in tr if t["stage"] == "hold"])
        print(f"{name} holdout: {fmt(h)}; pooled day z over all three windows {dayz(tr):.2f} against bar {zbar(N):.2f}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "counts":
        counts()
    elif cmd == "goldd":
        goldd()
    elif cmd == "dv":
        dv()
    elif cmd == "holdout":
        holdout(sys.argv[2:])
