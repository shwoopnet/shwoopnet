"""Weekly scaling, reinvest-and-skim and flat sizes, replayed on L1's 69 days of history. A measurement of sizing: no verdict, no variant counted, nothing here reads a result.

Each path draws 70 days (10 weeks) with replacement from the real days and fills each signal with probability FILL (a round number, not fitted). Rules:
flat N contracts; weekly scaling (cap = balance without savings / dollars per contract, one step up a week, down at once); reinvest-and-skim (only NEW net
profit highs are split, half to a pool that buys up to 2 extra contracts, half to savings that are not sized on). The loss stop is NOT applied, so the tails
shown are what the stop exists to cut. Mirrors functions/kalshiLiveLib.js (reviewSizing, foldSkim).

Usage: python -m scalper.sizing
"""
from __future__ import annotations

import random
import statistics as st
from collections import defaultdict

from . import lstrats as L
from .feerounding import order_cost
from .scalps import load as load_markets

def path(by, days, dpc, skim, addon_max, fixed, rng, ndays=70, fill=0.6, start=341.0, step_days=7, stop_frac=None, n_ceiling=10, cash_frac=None, base0=None, usable=None, trailing=False, addon_outside=False, cap_ceiling=10, cap0=None):
    """One path of `ndays` days. step_days: days between reviews (one step up at most per review, down at once). stop_frac: if set, the loss stop of the live bot:
    a day's result at or below minus stop_frac of the balance at the last review ends that day (the owner restarts the next morning), empties the pool and
    holds step-ups and the add-on for 7 days. Returns total, deepest drawdown, saved, final cap, peak, stops."""
    cash=start; base=start if base0 is None else base0; pool=0.0; saved=0.0; cum=0.0; hwm=0.0; cap=(3 if cap0 is None else cap0) if not fixed else fixed; peak=0.0; dd=0.0; total=0.0; stops=0; last_stop=-99
    for d_i in range(ndays):
        d=rng.choice(days)
        if not fixed:
            target=max(1,min(cap_ceiling,int(((cash if usable is None else min(cash,usable+total))-saved)/dpc)))
            if target<cap: cap=target; base=cash
            elif d_i>0 and d_i%step_days==0:
                base=cash
                if target>cap and d_i-last_stop>=7: cap=min(cap+1,target)
        day_pnl=0.0; day_peak=0.0; day_allow=0.0; stopped=False
        for e in by[d]:
            if stopped or rng.random()>=fill: continue
            add=min(addon_max,int(pool/0.93)) if (skim and d_i-last_stop>=7) else 0
            n=min(n_ceiling,cap+add)
            if cash_frac is not None:   # live l1Count: one order never risks more than cash_frac of cash, judged at one contract's cost
                n=max(1,min(n,int(cash_frac*cash/order_cost(e['price'],1)+1e-9)))
                if addon_outside:       # Oct 8 evening: only the account-funded part is held to cash_frac; the profit-funded add-on is added on top
                    n=min(n_ceiling,max(1,min(cap,n_ceiling,int(cash_frac*cash/order_cost(e['price'],1)+1e-9)))+add)
            cost=order_cost(e['price'],n); won=e['gross']+e['price']>0.5
            pnl=(n if won else 0)-cost
            if addon_outside and not won and n>0:
                day_allow+=cost*max(0,n-max(1,min(cap,n_ceiling,int((cash_frac or 1)*cash/order_cost(e['price'],1)+1e-9) if cash_frac else cap)))/n   # profit-funded share of a lost order
            cash+=pnl; total+=pnl; day_pnl+=pnl
            if skim:
                cum+=pnl
                if cum>hwm: rise=cum-hwm; hwm=cum; pool+=0.5*rise; saved+=0.5*rise
                elif pnl<0: pool=max(0.0,pool+pnl)
            peak=max(peak,total); dd=max(dd,peak-total)
            day_peak=max(day_peak,day_pnl)
            # trailing ('Stop follows the high point'): measured from the best result of the day so far instead of from zero
            if stop_frac is not None and ((day_peak-day_pnl>=stop_frac*base+day_allow-1e-9) if trailing else (day_pnl<=-(stop_frac*base+day_allow)-1e-9)):
                stopped=True; stops+=1; last_stop=d_i; pool=0.0
    return total,dd,saved,cap,peak,stops
def run(by, days, name, **kw):
    rng=random.Random(5); res=[path(by, days, rng=rng,**kw) for _ in range(3000)]
    t=sorted(x[0] for x in res); dds=sorted(x[1] for x in res)
    print(f"{name:42s} mean {st.mean(t):+7.1f}  5th {t[int(.05*len(t))]:+7.1f}  1st {t[int(.01*len(t))]:+7.1f}  dd95 {dds[int(.95*len(dds))]:6.1f}  P(loss) {sum(x<0 for x in t)/len(t):.1%}  end cap {st.mean(x[3] for x in res):.1f}  stop days {st.mean(x[5] for x in res):.2f}")
def main() -> None:
    markets, _ = load_markets()
    ents = L.hold_rule(markets, **L.L1)
    by = defaultdict(list)
    for e in ents: by[e["day"]].append(e)
    days = sorted(by)
    print("10 weeks, start $341, 60% fills, no loss stop applied (stops would cut the tails)")
    run(by, days, "now: cap 3 flat",dpc=100,skim=False,addon_max=0,fixed=3)
    run(by, days, "cap 4 flat",dpc=100,skim=False,addon_max=0,fixed=4)
    run(by, days, "cap 5 flat",dpc=100,skim=False,addon_max=0,fixed=5)
    run(by, days, "cap 8 flat",dpc=100,skim=False,addon_max=0,fixed=8)
    run(by, days, "weekly $100/contract only",dpc=100,skim=False,addon_max=0,fixed=0)
    run(by, days, "weekly $100 + skim 50%, add-on max 2",dpc=100,skim=True,addon_max=2,fixed=0)
    run(by, days, "weekly $85 + skim 50%, add-on max 2 (chosen)",dpc=85,skim=True,addon_max=2,fixed=0)
    run(by, days, "weekly $60 + skim 50%, add-on max 2",dpc=60,skim=True,addon_max=2,fixed=0)
    print("\nFaster steps and cheaper contracts: 10 weeks, start $344, 60% fills, WITH the live loss stop (10% of the balance at the last review; restart next morning)")
    for step in (7, 3):
        for dpc in (100, 85, 70, 60, 50):
            run(by, days, f"every {step} days, $ {dpc} per contract, skim", dpc=dpc, skim=True, addon_max=2, fixed=0, start=344.0, step_days=step, stop_frac=0.10)


def current() -> None:
    """The rule as deployed on 2026-10-08 after the balance reached $504.82 ($348.02 usable on the bot's shard, $156.80 on other shards): cap starts at 3,
    base $344 at the last review, 3 day steps, $85 a contract, stop 5% of base, add-on bounded only by the pool, one position at most 1% of cash, order
    ceiling 50. Compares sizing on the TOTAL balance (what runL1Tick does) with sizing on the usable shard only."""
    markets, _ = load_markets()
    ents = L.hold_rule(markets, **L.L1)
    by = defaultdict(list)
    for e in ents: by[e["day"]].append(e)
    days = sorted(by)
    print("10 weeks from $504.82, 60% fills, WITH the loss stop (5% of base, base $344 until the first review)")
    kw = dict(dpc=85, skim=True, fixed=0, start=504.82, step_days=3, stop_frac=0.05, base0=344.0, cash_frac=0.01)
    run(by, days, "old: add-on max 2, ceiling 10, total balance", addon_max=2, n_ceiling=10, **kw)
    run(by, days, "now: add-on uncapped, total balance", addon_max=999, n_ceiling=50, **kw)
    run(by, days, "add-on outside the 1% rule (this change)", addon_max=999, n_ceiling=50, addon_outside=True, **kw)
    run(by, days, "now: add-on uncapped, usable shard only", addon_max=999, n_ceiling=50, usable=348.02, **kw)
    run(by, days, "now + trailing stop, total balance", addon_max=999, n_ceiling=50, trailing=True, **kw)
    run(by, days, "cap 3 flat (the old stake), for scale", dpc=100, skim=False, addon_max=0, fixed=3, start=504.82, step_days=3, stop_frac=0.05, base0=344.0, cash_frac=0.01)


def base2() -> None:
    """Oct 9, 2026, information only: the owner asked for a 2% base per position (ladder $43 a contract) instead of 1% ($85). Both rows start at the
    current $547.96 with the base re-seeded to it (what Start does), pool add-on outside the base rule, order ceiling 50, 5% stop, 3 day steps,
    60% fills, the same 69 days of history. A replay of the past, not a forecast: the add-on and the stop are modelled as deployed."""
    markets, _ = load_markets()
    ents = L.hold_rule(markets, **L.L1)
    by = defaultdict(list)
    for e in ents: by[e["day"]].append(e)
    days = sorted(by)
    print("from $547.96, base re-seeded, 60% fills, WITH the loss stop (5% of base)")
    kw = dict(skim=True, fixed=0, start=547.96, step_days=3, stop_frac=0.05, base0=547.96, addon_max=999, n_ceiling=50, addon_outside=True)
    # Corrected 2026-10-09: the first version left the cap at 3 and the ladder ceiling at 10, which is not what Start (reseed) and the deployed 25 do.
    run(by, days, "1% base, $85, ceiling 10 (as of Oct 8)", dpc=85, cash_frac=0.01, cap0=6, cap_ceiling=10, **kw)
    run(by, days, "2% base, $43, ceiling 25 (Oct 9 change)", dpc=43, cash_frac=0.02, cap0=12, cap_ceiling=25, **kw)

if __name__ == "__main__":
    import sys
    base2() if "base2" in sys.argv[1:] else current() if "current" in sys.argv[1:] else main()
