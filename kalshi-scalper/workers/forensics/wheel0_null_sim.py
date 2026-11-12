"""WHEEL0: how often is a block of 60 HOT by luck alone, per band? A simulation on made-up fair bets; no market data, no outcome.
Fair = the side wins with probability equal to the mid (ask minus half a 2c spread). Price paid = ask (the walked average is at most ask + 1c; ask is the generous case).
Fee = 0.07 x p x (1-p) x 10 rounded up to the cent, per order of 10. HOT = cash PF >= 1.3, each half (first 30, last 30) PF >= 1.0, at least 10 of the rarer outcome.
usage: python3 -I wheel0_null_sim.py"""
import math, random, json
BANDS = [("cheap 05-20", 0.05, 0.20), ("cheap 20-35", 0.20, 0.35), ("cheap 35-50", 0.35, 0.50), ("fav 50-65", 0.51, 0.65), ("fav 65-80", 0.66, 0.80), ("fav 80-88", 0.81, 0.87)]
def pf(x):
    w = sum(v for v in x if v > 0); l = -sum(v for v in x if v < 0)
    return float("inf") if l == 0 else w / l
def cash(p, win):
    fee = math.ceil(0.07 * p * (1 - p) * 10 * 100 - 1e-9) / 100
    return (10 * (1 - p) - fee) if win else (-10 * p - fee)
rng = random.Random(20261112); out = {}
for name, lo, hi in BANDS:
    hot = 0; N = 40000; best = 0.0
    for _ in range(N):
        res, wins = [], 0
        for _ in range(60):
            p = round(rng.uniform(lo, hi), 2); w = rng.random() < p - 0.01; wins += w; res.append(cash(p, w))
        if min(wins, 60 - wins) >= 10 and pf(res) >= 1.3 and pf(res[:30]) >= 1.0 and pf(res[30:]) >= 1.0: hot += 1
    # the best PF a block can have with exactly 10 of the rarer outcome, at the band's most favourable price
    if lo < 0.5: bestpf = None
    else:
        p = lo; bestpf = round(50 * cash(p, True) / (-10 * cash(p, False)), 2)
    out[name] = {"hot_share_by_luck": round(hot / N, 4), "max_pf_with_10_losses_at_the_cheapest_price_in_band": bestpf}
print(json.dumps(out, indent=1))
