"""Monte Carlo of a Topstep-style 50K Trading Combine then Express Funded Account (Standard path). Research only.
Rules as read from Topstep's help pages on 2026-11-09 (see workers/PROP_FIRM_MEMO.md): Combine start 50,000, trailing end-of-day MLL 2,000 (locks at
the starting balance once reached), profit target 3,000, consistency target (best day < 55% of target, else target = best day / 0.55), monthly fee,
reset fee after an MLL breach. XFA: balance starts 0, MLL starts -2,000 and trails up, locks at 0 once balance reaches 2,000; payout needs 5 winning
days of 150+ and positive net profit; request min(50% of balance, 2,000) (50K Standard cap), 90% split. Strategy: iid normal daily P&L with a given
annual Sharpe and daily dollar vol (a stand-in for a diversified micro portfolio). Not a model of a real strategy; real P&L is fatter-tailed and serially dependent."""
import numpy as np, sys
rng = np.random.default_rng(7)
DF = None      # None = normal; an integer df >= 3 = Student-t scaled to the same sd (fat tails)
def draw(mu, sd):
    if DF is None:
        return rng.normal(mu, sd)
    return mu + sd * rng.standard_t(DF) / np.sqrt(DF / (DF - 2.0))
MONTH = 21
FEE_M, RESET, ACT = 49.0, 49.0, 149.0
def combine(mu, sd, maxd=250):
    bal, mll, best, days = 50000.0, 48000.0, 0.0, 0
    prof = 0.0
    while days < maxd:
        x = draw(mu, sd)
        days += 1
        # intraday breach approximated by closing balance (optimistic) plus an intraday-low penalty
        low = bal + x - abs(rng.normal(0, sd * 0.5))      # intraday adverse excursion proxy
        if low <= mll:
            return False, days
        bal += x; best = max(best, x); prof = bal - 50000.0
        mll = max(mll, min(bal - 2000.0, 50000.0))
        target = max(3000.0, best / 0.55)
        if prof >= target:
            return True, days
    return False, days
def xfa(mu, sd, maxd=250):
    bal, mll, wins, days = 0.0, -2000.0, 0, 0
    while days < maxd:
        x = draw(mu, sd)
        days += 1
        low = bal + x - abs(rng.normal(0, sd * 0.5))
        if low <= mll:
            return None, days
        bal += x
        if x >= 150: wins += 1
        mll = max(mll, min(bal - 2000.0, 0.0))
        if wins >= 5 and bal > 0 and 0.5 * bal >= 125:
            return 0.9 * min(0.5 * bal, 2000.0), days
    return None, days
def trial(sharpe, sd):
    mu = sharpe / np.sqrt(252.0) * sd
    fees, days_tot = 0.0, 0
    for att in range(20):             # buy a Combine, reset (49) after each breach; give up after 20 attempts
        ok, d = combine(mu, sd)
        months = max(1, int(np.ceil(d / MONTH)))
        fees += FEE_M * months + (RESET if att > 0 else 0.0)
        days_tot += d
        if not ok: continue
        fees += ACT
        pay, d2 = xfa(mu, sd)
        days_tot += d2
        if pay is not None:
            return True, pay, fees, days_tot
        # XFA breach: buy a new Combine (fee counted next loop)
    return False, 0.0, fees, days_tot
def run(sharpe, sd, n=4000):
    res = [trial(sharpe, sd) for _ in range(n)]
    got = np.array([r[0] for r in res]); pay = np.array([r[1] for r in res]); fees = np.array([r[2] for r in res]); dd = np.array([r[3] for r in res])
    return got.mean(), np.median(fees[got]) if got.any() else np.nan, fees.mean(), (pay - fees).mean(), np.median(dd[got]) / 21 if got.any() else np.nan
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "fat":
    DF = 3
    print("FAT TAILS (Student-t df 3, same sd). sd/day  Sharpe  P(payout)  median fees  mean fees  mean net  median months")
    for sd in (300.0, 600.0):
        for s_ in (0.0, 0.5, 1.0, 1.5):
            p, mf, af, net, mo = run(s_, sd)
            print("%6.0f  %5.1f   %.3f   $%7.0f   $%7.0f   $%7.0f   %5.1f" % (sd, s_, p, mf, af, net, mo))
elif __name__ == "__main__":
    print("sd/day  Sharpe  P(first payout within 20 combines)  median fees to payout  mean fees  mean net (first payout - fees)  median months")
    for sd in (300.0, 600.0):
        for s in (0.0, 0.5, 1.0, 1.5):
            p, mf, af, net, mo = run(s, sd)
            print("%6.0f  %5.1f   %.3f   $%7.0f   $%7.0f   $%7.0f   %5.1f" % (sd, s, p, mf, af, net, mo))
