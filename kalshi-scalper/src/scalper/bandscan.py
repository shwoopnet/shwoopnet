"""H4: does H2's rule (buy, sell at 80c, else hold) work from a 30c entry? (rules in the README,
fixed 2026-10-06 before this was written or run.)

It reuses H2's simulator unchanged, so the only thing that differs from H2 is the entry band.
Verdict: the README's kill criteria for the 30c band alone. A table of the same rule at other
entry prices follows, for information only: it is NOT used to choose a band, and no verdict
means "trade".

Usage: python -m scalper.bandscan
"""
from __future__ import annotations

from datetime import datetime, timezone

from .scalps import BANDS, MIN_N, STRESS, Z_BAR, judge, load, simulate

H4_BAND = ("30c", (0.28, 0.32))
# Information only. 40c and 50c are H2's own bands, so their rows must equal H2's printed result.
INFO_BANDS = {"20c": (0.18, 0.22), "30c": H4_BAND[1], "40c": BANDS["40c"], "50c": BANDS["50c"], "60c": (0.58, 0.62)}


def rows_for(markets: list[tuple], band: tuple[float, float]) -> list[tuple]:
    """(day, close_ts, net, net at fees x1.2, outcome) for every market with an entry in the band."""
    out = []
    for _, _, candles, close_ts, res in markets:
        t = simulate(candles, close_ts, res, band)
        if t:
            s = simulate(candles, close_ts, res, band, fee_mult=STRESS)
            day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
            out.append((day, close_ts, t["net"], s["net"], t["outcome"]))
    return out


def main() -> None:
    markets, mid = load()
    if not markets:
        print("No data. Run: python -m scalper.backfill")
        return
    name, band = H4_BAND
    rows = rows_for(markets, band)
    v, summ = judge({name: [x[:4] for x in rows]}, mid)
    print(f"{len(markets)} markets. H4: buy at ~30c (ask 28c to 32c), sell at 80c, else hold to settlement. Net per contract, cents.\n")
    print(f"{'band':>5} {'n':>6} {'mean':>7} {'se':>6} {'z':>6} {'1st half':>9} {'2nd half':>9} {'fees x1.2':>10} {'detectable':>11} {'passes':>7}")
    for s in summ:
        print(f"{s['band']:>5} {s['n']:>6} {s['mean']*100:>7.2f} {s['se']*100:>6.2f} {s['z']:>6.2f} {s['h1']*100:>9.2f} "
              f"{s['h2']*100:>9.2f} {s['stress']*100:>10.2f} {s['detectable']*100:>10.2f}c {str(s['ok']):>7}")
    print(f"\nVERDICT (pre-registered, bar z>={Z_BAR}, n>={MIN_N}, both halves, fees x{STRESS}): {v}")
    print("  " + ("The 30c band does not clear every criterion." if v == "FALSIFIED" else
                  "Permission to test on unseen days. Not evidence of an edge."))
    if rows:
        wins = [x[2] for x in rows if x[2] > 0]
        losses = [x[2] for x in rows if x[2] <= 0]
        n = len(rows)
        cnt = lambda k: sum(1 for x in rows if x[4] == k)
        need = ((-sum(losses) / len(losses)) / (sum(wins) / len(wins) + (-sum(losses) / len(losses)))) if wins and losses else float("nan")
        print(f"\nHow the 30c trades ended: target {cnt('target')/n*100:.1f}%, settle win {cnt('win')/n*100:.1f}%, settle loss {cnt('loss')/n*100:.1f}%; "
              f"avg win {sum(wins)/len(wins)*100:.1f}c, avg loss {sum(losses)/len(losses)*100:.1f}c; "
              f"break-even needs {need*100:.1f}% winners, got {len(wins)/n*100:.1f}%.")
    print("\nINFORMATION ONLY, affects nothing above and is not used to pick a band. Same rule by entry price, net per contract:")
    print(f"{'entry':>6} {'n':>6} {'mean':>8} {'1st half':>9} {'2nd half':>9}")
    for b, bd in INFO_BANDS.items():
        r = rows_for(markets, bd)
        if not r:
            print(f"{b:>6} {0:>6}")
            continue
        h1 = [x[2] for x in r if x[1] < mid]
        h2 = [x[2] for x in r if x[1] >= mid]
        m = lambda xs: f"{sum(xs)/len(xs)*100:>8.2f}c" if xs else f"{'-':>9}"
        print(f"{b:>6} {len(r):>6} {m([x[2] for x in r]):>9} {m(h1)} {m(h2)}")


if __name__ == "__main__":
    main()
