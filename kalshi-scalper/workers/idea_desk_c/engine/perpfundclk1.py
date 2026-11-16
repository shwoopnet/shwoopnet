#!/usr/bin/env python3
"""PERPFUNDCLK1 plugin (Idea Desk C, Nov 16, 2026), build 1. Card: ../allkalshi/perpfundclk1/PERPFUNDCLK1_CARD.md (card 9e2d14cb).
Positioning into the daily stock-perp funding print (21:00Z): 9 stock perps, 3 arms (A pre-print drift, B post-print reversion, C through the print with funding cash), 2 thresholds on the
previous print's rate, 10 cells. STAGE 1 reads FUNDING files only (counts, no price); if pooled trades a day is under 3 the card is parked and no candle is opened. STAGE 2 reads candles.
The loader and the metrics are perpscalp2's (signed): load rules, PF, halves, day z, BH."""
import calendar, csv, glob, gzip, hashlib, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perpscalp2 as P

STOCKS = ("KXNVDAPERP", "KXMUPERP", "KXSPCXPERP", "KXCOSTPERP", "KXTSLAPERP", "KXPLTRPERP", "KXMETAPERP", "KXAAPLPERP", "KXGOOGLPERP")
PRINT_S = 21 * 3600                                        # the print time of day, UTC seconds
H = (0.0002, 0.0005)                                       # gate, stress
FEE = 0.0012
CELLS = ([("A", off, thr) for off in (60, 30) for thr in ("nz", "med")] + [("C", off, thr) for off in (60, 30) for thr in ("nz", "med")] + [("B", 0, thr) for thr in ("nz", "med")])
N_CELLS = len(CELLS)                                       # 10
PREV_MAX_S = 4 * 86400                                     # the previous print must be at most 4 days earlier (a weekend)
MIN_PER_DAY = 3.0


def load_funding(root, end_epoch=P.END_EPOCH, manifest=None, stats=None):
    """{name: sorted [(time, rate)]} for the nine stocks only, first file wins, funding files only (no candle file is opened)."""
    st = stats if stats is not None else {}
    fu = {n: {} for n in STOCKS}
    end_epoch = min(end_epoch, P.H16_START - 1)
    for f in P._files(root, "funding", st):
        if manifest is not None:
            manifest.append((os.path.relpath(f, root), P._sha(f)))
        fh, rd = P._reader(f, P.FUND_COLS, st, "funding")
        with fh:
            for r in rd:
                n = r["ticker"]
                if n not in fu:
                    continue
                t, rate = P.iso(r["funding_time"]), float(r["funding_rate"])
                if t > end_epoch:
                    st["prints_after_end"] = st.get("prints_after_end", 0) + 1
                    continue
                if t in fu[n]:
                    k = "print_duplicate_differs" if fu[n][t] != rate else "print_duplicate_first_kept"
                    st[k] = st.get(k, 0) + 1
                    continue
                fu[n][t] = rate
    return {n: sorted(v.items()) for n, v in fu.items()}


def eligible(fu):
    """-> {name: [(T, prev_rate)]}: prints at 21:00Z whose previous print (at most 4 days earlier, at 21:00Z) has a nonzero rate; counts for every name."""
    out, cnt = {}, {"prints": 0, "prints_at_2100z": 0, "names_not_at_2100z": [], "with_previous": 0, "nonzero_previous": 0}
    for n, L in fu.items():
        at = [(t, r) for t, r in L if t % 86400 == PRINT_S]
        cnt["prints"] += len(L)
        cnt["prints_at_2100z"] += len(at)
        if L and not at:
            cnt["names_not_at_2100z"].append(n)
        out[n] = []
        for (t0, r0), (t1, r1) in zip(at, at[1:]):
            if 0 < t1 - t0 <= PREV_MAX_S:
                cnt["with_previous"] += 1
                if r0 != 0:
                    cnt["nonzero_previous"] += 1
                    out[n].append((t1, r0))
    return out, cnt


def stage1(root):
    manifest, st = [], {}
    fu = load_funding(root, P.END_EPOCH, manifest, st)
    el, cnt = eligible(fu)
    days = len({t // 86400 for L in fu.values() for t, r in L if t % 86400 == PRINT_S})
    n_el = sum(len(v) for v in el.values())
    absn = sorted(abs(r) for v in el.values() for t, r in v)
    med = None if not absn else (absn[len(absn) // 2] if len(absn) % 2 else (absn[len(absn) // 2 - 1] + absn[len(absn) // 2]) / 2)
    cnt.update({"print_days": days, "eligible_name_days": n_el, "trades_a_day_pooled": None if days == 0 else n_el / days, "median_nonzero_abs_prev_rate": med,
                "funding_rows": {n: len(v) for n, v in fu.items()}, "files_read": len(manifest), "manifest_sha256": hashlib.sha256(repr(sorted(manifest)).encode()).hexdigest(),
                "load": {k: v for k, v in st.items() if k != "headers_seen"}, "headers_seen": sorted(map(list, st.get("headers_seen", [])), key=repr)})
    cnt["parked"] = days == 0 or n_el / days < MIN_PER_DAY
    return fu, el, cnt, med


def usable_exit(c, x):
    """the candle at x, or one or two minutes before it (a gap is never bridged further); -> end ts or None"""
    return next((t for t in (x, x - 60, x - 120) if t in c), None)


def trade(c, fu, side, e, x, h):
    """e: entry candle end (must exist), x: planned exit end -> trade dict or None. Entry at the ask (long) or bid (short), exit at bid or ask, haircut h each taker leg, 12 bp a leg."""
    if e not in c:
        return None
    tx = usable_exit(c, x)
    if tx is None or tx <= e:
        return None
    qe, qx = c[e], c[tx]
    en = qe[1] * (1 + h) if side > 0 else qe[0] * (1 - h)
    ex = qx[0] * (1 - h) if side > 0 else qx[1] * (1 + h)
    gross = (ex - en) / en if side > 0 else (en - ex) / en
    fund, crossed = P.funding_of(fu, side, e, tx)
    return {"e": e, "x": tx, "side": side, "net": gross - 2 * FEE + fund, "gross": gross, "crossed": crossed, "stop_dist": 0.0,
            "day": P.datetime.fromtimestamp(e, P.ET).date().isoformat()}


def run(root, m_carried=6290660):
    fu, el, cnt, med = stage1(root)
    out = {"label": "candle replay, upper bound, not fill-checked; DEVELOPMENT through 2026-11-15, the same days as PERPSCALP1, PERPSCALP2, PERPSLANE4 and POOL1; the payer side is the previous print's rate (a persistence proxy); "
                    "day z is a normal approximation on a few days",
           "m_carried": m_carried, "m_new": N_CELLS, "m_total": N_CELLS + m_carried, "stage1": cnt}
    if cnt["parked"]:
        out["verdict"] = "PARKED at stage 1: under 3 pooled trades a day; no candle file was opened"
        return out
    manifest, st = [], {}
    c, fu2 = P.load(root, P.END_EPOCH, manifest, st)
    cells = []
    for (arm, off, thr) in CELLS:
        res, resS = [], []
        for n in STOCKS:
            for (T, prev) in el[n]:
                if thr == "med" and abs(prev) < med:
                    continue
                payer = 1 if prev > 0 else -1
                if arm == "B":
                    side, e, x = payer, T + 60, T + 31 * 60
                elif arm == "A":
                    side, e, x = -payer, T - off * 60, T - 5 * 60
                else:
                    side, e, x = -payer, T - off * 60, T + 31 * 60
                tr = trade(c[n], fu2[n], side, e, x, H[0])
                ts = trade(c[n], fu2[n], side, e, x, H[1])
                if tr is None or ts is None:
                    cnt["no_candle_or_exit"] = cnt.get("no_candle_or_exit", 0) + 1
                    continue
                tr["name"] = n
                res.append(tr); resS.append(ts)
        g, s = P.metrics(res), P.metrics(resS)
        g["mean_gross_bps"] = None if not res else 1e4 * sum(t["gross"] for t in res) / len(res)
        by = {}
        for t in res:
            by.setdefault(t["name"], []).append(t)
        cells.append({"cell": (arm, off, thr), "TT": g, "TS": s, "pass": P.passes(g, s), "margin": P.margin_row(by)})
    live = sorted((P.p_one_sided(r["TT"]["z"]), i) for i, r in enumerate(cells) if r["TT"]["n"] >= P.MIN_SIGNALS and r["TT"]["z"] is not None)
    mt = N_CELLS + m_carried
    kk = 0
    for rank, (p, i) in enumerate(live, 1):
        if p <= P.ALPHA * rank / mt:
            kk = rank
    surv = {i for _, i in live[:kk]}
    for i, r in enumerate(cells):
        r["bh_survivor"] = i in surv
    out.update({"cells": cells, "bh_survivors": len(surv), "passes": [r["cell"] for r in cells if r["pass"] and r["bh_survivor"]],
                "stage2": {"files_read": len(manifest), "manifest_sha256": hashlib.sha256(repr(sorted(manifest)).encode()).hexdigest(), "no_candle_or_exit": cnt.get("no_candle_or_exit", 0),
                           "load": {k: v for k, v in st.items() if k != "headers_seen"}}})
    return out
