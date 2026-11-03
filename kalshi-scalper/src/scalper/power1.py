"""POWER1: how soon can each forward-accruing test reach a decision, and what effect could it detect? (support analysis, N +0)

No new try, no outcome scored, no frozen holdout read. Every input is a number written in a registration or result file (cited per row in
SPECS) or an explicit assumption (flagged `assumed`). Output: workers/POWER1_TABLE.csv. Report: workers/POWER1_REPORT.md.

    PYTHONPATH=src python3 -m scalper.power1 table      (writes the CSV, prints the ranked summary)

Model (documented so it can be checked by hand)
  One Kalshi trade: 1 contract bought at mean price a, held to settlement, fee per contract = ceil(70 a (1-a)) cents / 10
  (7% x C x p x (1-p) rounded up to the cent, C = 10, divided by C). Break-even win rate c = a + fee. A true edge e (dollars per
  contract, after fee) means win probability p = c + e. Net per trade = win - c, so the per-trade sd is sqrt(p (1-p)) dollars.
  Day clustering: trades in one cluster (a day, a release date) have intra-class correlation rho, so the design effect is
  deff = 1 + (m - 1) rho with m trades per cluster and the standard error of the mean is sd sqrt(deff / n).
  Analytic (normal approximation):  z = e / se;  n for expected z = deff (z sd / e)^2;  n for power P = deff ((z + z_P) sd / e)^2;
  edge detectable with 80% power at n = (z + 0.8416) se.
  Monte Carlo (day clustering, beta-binomial clusters, cluster-robust z with the G/(G-1) factor) is used for the false positive rate
  and the pass probabilities, where the normal approximation is poor (cheap prices, small n).
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import numpy as np

Z80 = 0.8416212335729143
Z_DEFLATED = 5.27  # one-sided 0.05 / N with N about 730,000 (README running count)


# ---------------------------------------------------------------- basic formulas
def ncdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def nsf(x: float) -> float:
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def fee_dollars(a: float) -> float:
    """Fee per contract at C = 10: 7% x 10 x a (1-a) in dollars, rounded up to the cent, divided by 10."""
    cents = math.ceil(70.0 * a * (1.0 - a) - 1e-9)
    return cents / 100.0 / 10.0


def breakeven(a: float) -> float:
    return a + fee_dollars(a)


def sd_trade(a: float, edge: float = 0.0) -> float:
    p = min(max(breakeven(a) + edge, 1e-4), 1 - 1e-4)
    return math.sqrt(p * (1.0 - p))


def deff(m: float, rho: float) -> float:
    return 1.0 + max(m - 1.0, 0.0) * rho


def se_mean(sd: float, n: float, d: float) -> float:
    return sd * math.sqrt(d / n)


def edge_for_power(n: float, z: float, sd: float, d: float, power: float = 0.8) -> float:
    """True mean edge (dollars) that passes a one-sided z bar with the given power at n trades."""
    zp = Z80 if abs(power - 0.8) < 1e-9 else _inv(power)
    return (z + zp) * se_mean(sd, n, d)


def n_for_z(edge: float, z: float, sd: float, d: float, power: float | None = None) -> float:
    """Trades needed: expected z reaches `z` (power None, the median run), or power-probability of reaching it."""
    zp = 0.0 if power is None else (Z80 if abs(power - 0.8) < 1e-9 else _inv(power))
    return d * (sd * (z + zp) / edge) ** 2


def power_at(edge: float, n: float, z: float, sd: float, d: float) -> float:
    return nsf(z - edge / se_mean(sd, n, d))


def _inv(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if ncdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def poisson_cdf(k: int, mu: float) -> float:
    """P(Poisson(mu) <= k)."""
    if k < 0:
        return 0.0
    if mu <= 0:
        return 1.0
    term = math.exp(-mu)
    tot = term
    for i in range(1, k + 1):
        term *= mu / i
        tot += term
    return min(tot, 1.0)


def p_not_enough(lam: float, m: float, days: float, floor: int) -> float:
    """P(fewer than `floor` trades after `days`): clusters arrive Poisson at lam/m a day, each brings m trades."""
    if floor <= 0:
        return 0.0
    mu = lam / m * days
    need = math.ceil(floor / m)
    return poisson_cdf(need - 1, mu)


# ---------------------------------------------------------------- Monte Carlo
def simulate(a: float, edge: float, n: int, m: float, rho: float, sims: int, rng: np.random.Generator,
             pf_pool: float = 1.0, pf_half: float = 0.0) -> dict:
    """Clustered binary trades. Returns probabilities of z >= 2, 3, 5.27 (cluster-robust) and of the kill-rule survival."""
    m_i = max(int(round(m)), 1)
    G = max(int(round(n / m_i)), 2)
    c = breakeven(a)
    p = min(max(c + edge, 1e-4), 1 - 1e-4)
    if rho > 1e-9 and m_i > 1:
        ab = 1.0 / rho - 1.0
        pc = rng.beta(p * ab, (1 - p) * ab, size=(sims, G))
    else:
        pc = np.full((sims, G), p)
    wins = rng.binomial(m_i, pc)
    ntot = G * m_i
    cost1 = c
    S = wins * 1.0 - m_i * cost1  # cluster net
    mu = S.sum(axis=1) / ntot
    resid = S - m_i * mu[:, None]
    var = (G / (G - 1.0)) * (resid ** 2).sum(axis=1) / ntot ** 2
    se = np.sqrt(np.maximum(var, 1e-18))
    z = mu / se

    def pf(w, nn, cost):
        loss = (nn - w) * cost
        gain = w * (1.0 - cost)
        return np.where(loss > 0, gain / np.maximum(loss, 1e-12), np.inf)

    W = wins.sum(axis=1)
    pf_all = pf(W, ntot, cost1)
    pf_12 = pf(W, ntot, cost1 + 0.2 * fee_dollars(a))
    h = G // 2
    W1, W2 = wins[:, :h].sum(axis=1), wins[:, h:].sum(axis=1)
    n1, n2 = h * m_i, (G - h) * m_i
    mu1, mu2 = (W1 - n1 * cost1) / n1, (W2 - n2 * cost1) / n2
    pf1, pf2 = pf(W1, n1, cost1), pf(W2, n2, cost1)
    survive = (pf_all >= pf_pool) & (mu1 > 0) & (mu2 > 0) & (pf1 >= pf_half) & (pf2 >= pf_half) & (pf_12 > 1.0)
    out = {
        "z2": float((z >= 2.0).mean()),
        "z3": float((z >= 3.0).mean()),
        "z527": float((z >= Z_DEFLATED).mean()),
        "survive": float(survive.mean()),
        "survive_and_z3": float((survive & (z >= 3.0)).mean()),
        "n_used": ntot,
        "G": G,
    }
    return out


# ---------------------------------------------------------------- specs
# lam = trades per calendar day (central, low, high). m = trades per cluster (None: min(max(lam,1), 12)). rho = intra-cluster correlation.
# floor = trades required before any verdict other than NOT_ENOUGH_DATA. z_reg = the registered z bar (5.27 unless stated).
# pf_pool, pf_half = the registered profit factor kill levels (pooled, each half). stop_days = days from 2026-11-03 to a registered stop date.
SPECS = [
    dict(id="EVENT830", label="8:30 ET release windows, 8 series, cheaper side 5-50c", a=0.25, lam=(1.15, 0.93, 1.38), m=4.8, rho=0.30,
         floor=150, z_reg=5.27, pf_pool=1.2, pf_half=0.0, stop_days=None, kill_n=40,
         src="EVENT830_REGISTRATION.md l.53-54, l.63-69: ~35 trades/month (28-42), 4.8 trades per release date, 150 in ~4.3 months; a assumed 0.25 (band 0.05-0.50), rho assumed"),
    dict(id="WXENS1", label="Ensemble weather tail brackets, 8 cities, ask 3-30c", a=0.125, lam=(4.0, 1.6, 8.0), m=4.0, rho=0.20,
         floor=150, z_reg=5.27, pf_pool=1.5, pf_half=0.0, stop_days=117, kill_n=None,
         src="WXENS1_REGISTRATION.md l.41-42,48: ~4 trades/day (1.6-8), 150 in 38 days (19-94), mean price 0.10-0.15; read at 300 or 2027-02-28; recorder not yet on origin; rho assumed"),
    dict(id="MAKERTAIL1_comb", label="Hourly BTC far-tail resting bids (combined)", a=0.058, lam=(36.0, 21.0, 57.0), m=36.0, rho=0.05,
         floor=150, z_reg=5.27, pf_pool=1.0, pf_half=1.5, stop_days=None, kill_n=None,
         src="MAKERTAIL1_RESULT.md l.25 (36 fills/day, 82% pessimistic fill rate on 26-70 orders/day), l.19 (mean price 5.7-5.8c); rho assumed (BTC day move)"),
    dict(id="MAKERTAIL1_NO", label="MAKERTAIL1 NO-side tails alone (side split needs 150 on EACH side)", a=0.057, lam=(18.0, 10.0, 28.0), m=18.0, rho=0.05,
         floor=150, z_reg=5.27, pf_pool=1.0, pf_half=1.5, stop_days=None, kill_n=None,
         src="Amendment 1 side split; half of 36 fills/day assumed (DEV: 81 and 94 fills YES/NO)"),
    dict(id="MAKERTAIL1_YES", label="MAKERTAIL1 YES-side tails alone", a=0.058, lam=(18.0, 10.0, 28.0), m=18.0, rho=0.05,
         floor=150, z_reg=5.27, pf_pool=1.0, pf_half=1.5, stop_days=None, kill_n=None,
         src="as above"),
    dict(id="NOWCAST1", label="Release-series nowcast cheap tails (CPI, core CPI, core PCE, GDP)", a=0.12, lam=(0.023, 0.016, 0.030), m=1.0, rho=0.0,
         floor=150, z_reg=5.27, pf_pool=1.5, pf_half=0.0, stop_days=None, kill_n=40,
         src="NOWCAST1_RESULT.md l.24: 0.5-0.9 trades a month, 40 forward fills need 47-85 months"),
    dict(id="FEDIMPL1", label="FOMC KXFEDDECISION/KXFED vs bill-implied, ask 3-30c", a=0.10, lam=(0.068, 0.05, 0.11), m=1.0, rho=0.0,
         floor=150, z_reg=5.27, pf_pool=1.5, pf_half=0.0, stop_days=None, kill_n=30,
         src="FEDIMPL1_REGISTRATION.md l.11,60 and CALENDAR row 35: 150 trades = 4 to 8 years (~20-25 trades a year, 8 meetings); a assumed"),
    dict(id="COUNT1_weekly", label="Truth Social weekly count brackets, ask 3-30c", a=0.115, lam=(0.059, 0.04, 0.09), m=1.0, rho=0.0,
         floor=150, z_reg=5.27, pf_pool=1.5, pf_half=0.0, stop_days=None, kill_n=40,
         src="COUNT1_RESULT.md l.6,15: take-up 0.42 per week, ~1.8 trades a month; mean fill 11.5c"),
    dict(id="COUNT1_daily", label="Truth Social daily count brackets, ask 3-30c", a=0.10, lam=(0.10, 0.03, 0.30), m=1.0, rho=0.0,
         floor=150, z_reg=5.27, pf_pool=1.5, pf_half=0.0, stop_days=None, kill_n=40,
         src="COUNT1_REGISTRATION.md l.36 (take-up 10-50% per period, 2 brackets max); daily cell unmeasured (0 trades on 6 events): lam ASSUMED"),
    dict(id="BARRIER1", label="Monthly one-touch markets, 14 series, ask 3-30c", a=0.12, lam=(0.12, 0.10, 0.14), m=3.0, rho=0.50,
         floor=150, z_reg=5.27, pf_pool=1.5, pf_half=0.0, stop_days=None, kill_n=40,
         src="BARRIER1_RESULT.md l.40-41: 3-4 trades a month, 11-13 months to 40; rho assumed (one price path decides an event)"),
    dict(id="USWEEP1_NATGAS", label="[RULING NEEDED] KXNATGASD favourite 6 h, ask 85-97c", a=0.92, lam=(11.2, 8.0, 14.0), m=11.2, rho=0.60,
         floor=100, z_reg=2.0, pf_pool=1.0, pf_half=0.0, stop_days=None, kill_n=40, ruling=True,
         src="USWEEP1_RESULT.md l.52-58: 11.2 entries/day; LEAD rule n>=100, z>=2; probe kill 40 fills PF<1; rho assumed; favourite-and-hold ban"),
    dict(id="USWEEP1_GOLDD", label="[RULING NEEDED] KXGOLDD favourite 6 h", a=0.92, lam=(4.8, 3.0, 6.5), m=4.8, rho=0.50,
         floor=100, z_reg=2.0, pf_pool=1.0, pf_half=0.0, stop_days=None, kill_n=40, ruling=True, src="same table: 4.8/day"),
    dict(id="USWEEP1_SILVERD", label="[RULING NEEDED] KXSILVERD favourite 6 h", a=0.92, lam=(4.1, 2.5, 5.5), m=4.1, rho=0.50,
         floor=100, z_reg=2.0, pf_pool=1.0, pf_half=0.0, stop_days=None, kill_n=40, ruling=True, src="same table: 4.1/day"),
    dict(id="USWEEP1_BRENTD", label="[RULING NEEDED] KXBRENTD favourite 1 h", a=0.92, lam=(2.4, 1.5, 3.5), m=2.4, rho=0.50,
         floor=100, z_reg=2.0, pf_pool=1.0, pf_half=0.0, stop_days=None, kill_n=40, ruling=True, src="same table: 2.4/day"),
    dict(id="USWEEP1_HIGHTSATX", label="[RULING NEEDED] KXHIGHTSATX favourite 24 h (weather)", a=0.92, lam=(1.6, 1.0, 2.2), m=1.6, rho=0.30,
         floor=100, z_reg=2.0, pf_pool=1.0, pf_half=0.0, stop_days=None, kill_n=40, ruling=True, src="same table: 1.6/day"),
    dict(id="ELECT1_REF", label="Election-night rating-implied cheap side (one night, REF rule)", a=0.12, lam=(0.0, 0.0, 0.0), m=1.0, rho=0.0,
         floor=150, z_reg=5.27, pf_pool=1.5, pf_half=0.0, stop_days=0, n_fixed=5, kill_n=None,
         src="CALENDAR row 2: REF rule has 5 trades at the snapshot; CONTROL 117; no second night"),
    dict(id="RAINCAL", label="Daily rain markets vs NWS PoP, edge >= 8c", a=0.40, lam=(5.8, 4.2, 7.5), m=5.8, rho=0.15,
         floor=150, z_reg=5.27, pf_pool=1.2, pf_half=1.2, stop_days=59, kill_n=None,
         src="RAINCAL_REGISTRATION.md l.63: 250-450 trades in 60 days; read 2027-01-01; a and rho assumed"),
    dict(id="DERIBIT_IMPLIED", label="Hourly BTC ladder vs Deribit implied digital, edge >= 5c", a=0.50, lam=(2.33, 1.5, 3.5), m=2.33, rho=0.10,
         floor=150, z_reg=5.27, pf_pool=1.3, pf_half=1.3, stop_days=59, kill_n=None,
         src="DERIBIT_IMPLIED_REGISTRATION.md l.38: ~140 trades in 60 days; PF>=1.3 each half, z>=3, deflated 5.27; a (within 3% of spot) and rho assumed"),
    dict(id="SPORTSPRE", label="Pre-game moneyline cheaper side vs ESPN, edge >= 6c", a=0.38, lam=(8.3, 6.7, 10.0), m=8.3, rho=0.05,
         floor=200, z_reg=5.27, pf_pool=1.2, pf_half=1.2, stop_days=59, kill_n=None,
         src="SPORTSPRE_REGISTRATION.md l.76,81-86: 400-600 trades in 60 days in season; floor 200; PF>=1.2 each half, z>=3, 5.27; a and rho assumed"),
    dict(id="STRADDLE1", label="Pre-earnings straddle run-up (percent of premium, not cents)", a=None, lam=(0.0, 0.0, 0.0), m=10.0, rho=0.10,
         floor=300, z_reg=5.27, pf_pool=1.0, pf_half=0.0, stop_days=None, n_fixed=4355, kill_n=None, continuous=True, sd_pct=12.0,
         src="STRADDLE1_REGISTRATION.md l.18-21: sd ~12% of premium; 6,510 events, final third 2,155 frozen (first two thirds 4,355); z 2.9 / 5.27; cluster by entry date, m and rho assumed; blocked on data source"),
    # reference rows: published live numbers only (README, OICORE_LIVE_ORDERS.csv); the edge is the published point estimate
    dict(id="REF_L1_gold", label="Reference: live L1 gold (155 fills, 96.1% wins, +4.3c per contract)", a=0.93, lam=(7.8, 7.0, 8.5), m=7.8, rho=0.10,
         floor=0, z_reg=5.27, pf_pool=1.0, pf_half=0.0, stop_days=None, kill_n=None, ref_edge=0.043,
         src="README l.6855: 155 fills since 2026-10-07, 149 wins, +$44.06 at 6.7 contracts average; rho assumed; net per contract = 44.06 / (155 x 6.7)"),
    dict(id="REF_OICORE", label="Reference: OICORE Bitcoin cheap NO (history 358 trades, PF 2.3, 29% wins)", a=0.14, lam=(6.0, 4.8, 6.0), m=6.0, rho=0.10,
         floor=0, z_reg=5.27, pf_pool=1.0, pf_half=0.0, stop_days=None, kill_n=None, ref_edge=0.139,
         src="README l.8243 (358 trades, 60 dates, PF 2.33, win 29.1%); live CSV: 24 orders on 5 dates, 18 settled, 5 wins, +$25.03 (4.8 orders/day); history edge = 0.291 - 0.152"),
]

HORIZONS = (30, 60, 120)
GRID = (0.01, 0.02, 0.05)  # dollars per contract after fee: +1c, +2c, +5c
GRID_PCT = (0.005, 0.01, 0.02)  # straddle: +0.5%, +1%, +2% of premium (as fractions)


def _m(spec: dict) -> float:
    if spec.get("m") is not None:
        return float(spec["m"])
    return min(max(spec["lam"][0], 1.0), 12.0)


def row_for(spec: dict, rng: np.random.Generator, sims: int = 20000) -> dict:
    cont = spec.get("continuous", False)
    lam, lam_lo, lam_hi = spec["lam"]
    m = _m(spec)
    d = deff(m, spec["rho"])
    if cont:
        sd = spec["sd_pct"] / 100.0
        price_c = float("nan")
        grid = GRID_PCT
    else:
        a = spec["a"]
        sd = sd_trade(a)
        price_c = a * 100
        grid = GRID
    z_reg = spec["z_reg"]
    floor = spec["floor"]
    n_fixed = spec.get("n_fixed")
    r = {
        "id": spec["id"], "label": spec["label"], "unit": "pct_premium" if cont else "cents_per_contract",
        "price_c": round(price_c, 1) if not cont else "", "breakeven_win_rate": round(breakeven(spec["a"]), 4) if not cont else "",
        "sd_per_trade": round(sd * (100 if not cont else 100), 2), "m_per_cluster": round(m, 2), "rho": spec["rho"], "deff": round(d, 2),
        "lam_per_day": lam, "lam_low": lam_lo, "lam_high": lam_hi, "floor_n": floor, "z_registered": z_reg,
        "pf_pool_min": spec["pf_pool"], "pf_half_min": spec["pf_half"], "ruling_needed": "yes" if spec.get("ruling") else "",
    }
    sc = 100.0  # report edges in cents (or percent of premium for the straddle)
    # (a) edge with 80% power at the decision n and at 30/60/120 days
    ref = bool(spec.get("ref_edge"))
    n_dec = n_fixed if n_fixed else max(floor, 1)
    if not ref:
        r["e80_reg_at_floor"] = round(edge_for_power(n_dec, z_reg, sd, d) * sc, 2)
        r["e80_z3_at_floor"] = round(edge_for_power(n_dec, 3.0, sd, d) * sc, 2)
        r["e80_527_at_floor"] = round(edge_for_power(n_dec, Z_DEFLATED, sd, d) * sc, 2)
    for H in HORIZONS:
        nH = n_fixed if n_fixed else lam * H
        r[f"n_{H}d"] = round(nH, 1)
        r[f"verdict_possible_{H}d"] = "yes" if nH >= floor else "no"
        r[f"e80_527_{H}d"] = round(edge_for_power(max(nH, 1), Z_DEFLATED, sd, d) * sc, 2) if nH >= 1 else ""
        r[f"e80_z3_{H}d"] = round(edge_for_power(max(nH, 1), 3.0, sd, d) * sc, 2) if nH >= 1 else ""
    # days to the floor
    for tag, l in (("", lam), ("_lowrate", lam_lo), ("_highrate", lam_hi)):
        r["days_to_floor" + tag] = round(floor / l, 1) if (l and not n_fixed and floor) else ""
    if lam and not n_fixed and floor and m >= 1.0 and abs(m - lam) < 1e-9 and lam >= 1.0:
        # clusters are calendar days: fewer than about 10 clusters makes a day-clustered z unreliable (assumed minimum)
        r["days_to_floor_min10_clusters"] = round(max(floor / lam, 10.0), 1)
    # (b) n and days to z 2, 3, 5.27 at +1c, +2c, +5c (median run, and 80% power)
    for e in grid:
        tag = {GRID[0]: "e1", GRID[1]: "e2", GRID[2]: "e5"}[e] if not cont else {GRID_PCT[0]: "e1", GRID_PCT[1]: "e2", GRID_PCT[2]: "e5"}[e]
        for zl, zt in ((2.0, "z2"), (3.0, "z3"), (Z_DEFLATED, "z527")):
            n_med = n_for_z(e, zl, sd, d)
            n_80 = n_for_z(e, zl, sd, d, 0.8)
            n_med_eff, n_80_eff = max(n_med, floor), max(n_80, floor)
            r[f"n_{zt}_{tag}"] = int(math.ceil(n_med_eff))
            r[f"n80_{zt}_{tag}"] = int(math.ceil(n_80_eff))
            if lam and not n_fixed:
                r[f"days_{zt}_{tag}"] = round(n_med_eff / lam, 1)
                r[f"days80_{zt}_{tag}"] = round(n_80_eff / lam, 1)
            else:
                r[f"days_{zt}_{tag}"] = ""
                r[f"days80_{zt}_{tag}"] = ""
    # (c) Monte Carlo at the decision n: false positive and pass probabilities
    if ref:
        pass  # reference rows have no floor and no registered false positive question
    elif not cont:
        a = spec["a"]
        n_mc = int(n_fixed if n_fixed else max(floor, 30))
        for e, tag in ((0.0, "e0"), (0.02, "e2"), (0.05, "e5")):
            o = simulate(a, e, n_mc, m, spec["rho"], sims, rng, spec["pf_pool"], spec["pf_half"])
            r[f"mc_survive_{tag}"] = round(o["survive"], 4)
            r[f"mc_z2_{tag}"] = round(o["z2"], 4)
            r[f"mc_z3_{tag}"] = round(o["z3"], 4)
            r[f"mc_z527_{tag}"] = round(o["z527"], 5)
            r[f"mc_survive_z3_{tag}"] = round(o["survive_and_z3"], 4)
        r["mc_n_used"] = o["n_used"]
        r["normal_fp_527"] = f"{nsf(Z_DEFLATED):.2e}"
    else:
        for tag, e in (("e0", 0.0), ("e2", 0.01)):
            se = se_mean(sd, n_fixed, d)
            r[f"mc_z3_{tag}"] = round(power_at(e, n_fixed, 3.0, sd, d), 4)
            r[f"mc_z527_{tag}"] = round(power_at(e, n_fixed, Z_DEFLATED, sd, d), 5)
        r["normal_fp_527"] = f"{nsf(Z_DEFLATED):.2e}"
    # NOT_ENOUGH_DATA at the stop date (or at 120 days when there is none), low / central / high rate
    stop = spec["stop_days"] if spec["stop_days"] is not None else 120
    r["ned_horizon_days"] = stop
    for tag, l in (("low", lam_lo), ("central", lam), ("high", lam_hi)):
        if n_fixed:
            r[f"p_ned_{tag}"] = 1.0 if n_fixed < floor else 0.0
        elif floor:
            r[f"p_ned_{tag}"] = round(p_not_enough(l, m, stop, floor), 4)
        else:
            r[f"p_ned_{tag}"] = 0.0
    # reference rows: time to z 5.27 at the published edge
    if spec.get("ref_edge"):
        e = spec["ref_edge"]
        sdp = sd_trade(spec["a"], e)
        n_ = n_for_z(e, Z_DEFLATED, sdp, d)
        n8 = n_for_z(e, Z_DEFLATED, sdp, d, 0.8)
        r["ref_edge_c"] = round(e * 100, 1)
        r["ref_n_527_median"] = int(math.ceil(n_))
        r["ref_n_527_p80"] = int(math.ceil(n8))
        r["ref_days_527_median"] = round(n_ / lam, 1)
        r["ref_days_527_p80"] = round(n8 / lam, 1)
    r["source"] = spec["src"]
    return r


def build(sims: int = 20000, seed: int = 20261103) -> list[dict]:
    rng = np.random.default_rng(seed)
    return [row_for(s, rng, sims) for s in SPECS]


def write_csv(rows: list[dict], path: Path) -> None:
    cols: list[str] = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] != "table":
        print(__doc__)
        return 0
    root = Path(__file__).resolve().parents[2]
    rows = build()
    out = root / "workers" / "POWER1_TABLE.csv"
    write_csv(rows, out)
    print("wrote", out)
    for r in rows:
        print(f"{r['id']:20s} lam {r['lam_per_day']:>6} floor {r['floor_n']:>4} d_floor {str(r['days_to_floor']):>7} "
              f"e80@5.27 floor {r.get("e80_527_at_floor",""):>7}  120d {r.get('e80_527_120d', ''):>7}  "
              f"FP surv {r.get('mc_survive_e0', '')}  FP z3 {r.get('mc_z3_e0', '')}  NED {r['p_ned_low']}/{r['p_ned_central']}/{r['p_ned_high']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
