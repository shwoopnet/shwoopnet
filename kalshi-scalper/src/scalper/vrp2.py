"""VRP2 (README, Pre-registration: JUMP1, FIX1, VRP2 and the two data requests): a synthetic monthly 5%-wide SPX put credit spread priced at the VIX, on index history.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.vrp2 fetch   then   python -m scalper.vrp2 run     (`run` is once; a refused rerun unless the result file is deleted on purpose)
"""
from __future__ import annotations

import json
import math
import sys
import time
import urllib.parse
import urllib.request

from .fund1 import nw_mean_z
from .paths import DATA_DIR
from .slow1 import month_ends

BARS_FILE = DATA_DIR / "vrp2_bars.json"
RESULT_FILE = DATA_DIR / "vrp2_result.txt"
HOLD_DAYS, SHORT_K, LONG_K, COST, COST_STRESS = 21, 0.95, 0.90, 0.03, 0.04
MIN_MONTHS, Z_BAR = 300, 2.9


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    out = {}
    for sym in ("^GSPC", "^VIX"):
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?interval=1d&period1=0&period2={int(time.time())}"
        for attempt in range(6):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    res = json.load(r)["chart"]["result"][0]
                break
            except Exception:
                if attempt == 5:
                    raise
                time.sleep(5 * (attempt + 1))
        out[sym] = {time.strftime("%Y-%m-%d", time.gmtime(t)): c for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]) if c and c > 0}
        d = sorted(out[sym])
        print(f"{sym}: {len(d)} bars {d[0]} to {d[-1]}")
    BARS_FILE.write_text(json.dumps(out))


def _n(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_put(s: float, k: float, sigma: float, t: float) -> float:
    """Black-Scholes put, zero rate and dividend."""
    d1 = (math.log(s / k) + 0.5 * sigma * sigma * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    return k * _n(-d2) - s * _n(-d1)


def spread_month(s0: float, st: float, vix: float, cost: float) -> float | None:
    """Return on margin of one 5%-wide spread opened at s0 with VIX `vix` and settled at st, after `cost` as a share of the width."""
    ks, kl = SHORT_K * s0, LONG_K * s0
    sigma, t = vix / 100.0, HOLD_DAYS / 252.0
    credit = bs_put(s0, ks, sigma, t) - bs_put(s0, kl, sigma, t)
    width = ks - kl
    pnl = credit - max(ks - st, 0.0) + max(kl - st, 0.0) - cost * width
    return pnl / (width - credit)


def run() -> None:
    if RESULT_FILE.exists():
        sys.exit(f"{RESULT_FILE} exists: VRP2 is a single read. Delete it on purpose (a crash fix only) to rerun.")
    bars = json.loads(BARS_FILE.read_text())
    dates = sorted(set(bars["^GSPC"]) & set(bars["^VIX"]))
    spx = [bars["^GSPC"][d] for d in dates]
    vix = [bars["^VIX"][d] for d in dates]
    first = [i + 1 for i in month_ends(dates)]                 # first trading day of each month
    rows = []
    for i in first:
        j = i + HOLD_DAYS
        if j >= len(dates):
            break
        rows.append((dates[i], spread_month(spx[i], spx[j], vix[i], COST), spread_month(spx[i], spx[j], vix[i], COST_STRESS), spread_month(spx[i], spx[j], vix[i], 0.0)))
    n = len(rows)
    net = [r[1] for r in rows]
    m, z = nw_mean_z(net)
    h = n // 2
    h1, h2 = sum(net[:h]) / h, sum(net[h:]) / (n - h)
    post = [r[1] for r in rows if r[0] >= "2012-01-01"]
    stress = sum(r[2] for r in rows) / n
    eq, peak, dd = 1.0, 1.0, 0.0
    for x in net:
        eq *= 1 + 0.02 * x                                      # information: 2% of the account at risk per spread
        peak = max(peak, eq)
        dd = min(dd, eq / peak - 1)
    checks = {"months>=300": n >= MIN_MONTHS, "net>0": m > 0, f"z>={Z_BAR}": z >= Z_BAR, "both_halves>0": h1 > 0 and h2 > 0, "2012_on>0": sum(post) / len(post) > 0, "stress>0": stress > 0}
    verdict = "NOT_ENOUGH_DATA" if n < MIN_MONTHS else ("NOT_YET_FALSIFIED" if all(checks.values()) else "FALSIFIED")
    worst = sorted(rows, key=lambda r: r[1])[:5]
    res = {"verdict": verdict, "checks": checks, "months": n, "first": rows[0][0], "mean_net_return_on_margin": m, "nw_z": z, "h1": h1, "h2": h2, "post_2012": sum(post) / len(post),
           "stress": stress, "gross_mean_no_cost": sum(r[3] for r in rows) / n, "win_rate": sum(1 for x in net if x > 0) / n, "worst_five_months": [(d, round(v, 3)) for d, v, _, _ in worst],
           "max_drawdown_at_2pct_risk": dd}
    text = json.dumps(res, indent=1)
    RESULT_FILE.write_text(text)
    print(text)


if __name__ == "__main__":
    import urllib.parse
    {"fetch": fetch, "run": run}[sys.argv[1]]()
