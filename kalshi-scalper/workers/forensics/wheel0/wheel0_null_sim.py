"""WHEEL0: how often is a block HOT by luck alone, per band, under the lane's growing-block rule? Made-up fair bets only; no market data, no outcome.
A block: at least 60 orders (150 for the 88c to 97c favourites), running on until it holds 10 of the rarer outcome (wins on the cheap side, losses on the favourite side).
HOT: cash PF 1.3 or better on the block, 1.0 or better in each half (first floor(n/2), then the rest).
Fair = the side wins with probability equal to its mid (ask minus 1c, a 2c spread). Price paid = the ask. Fee = 0.07 x p x (1-p) x 10 rounded up to the cent, per order of 10.
usage: python3 -I wheel0_null_sim.py > WHEEL0_NULL_SIM.json"""
import math, random, json
BANDS = [("05-20", "cheap", 0.05, 0.19, 60), ("20-35", "cheap", 0.20, 0.34, 60), ("35-50", "cheap", 0.35, 0.50, 60), ("50-65", "fav", 0.51, 0.65, 60), ("65-80", "fav", 0.66, 0.80, 60), ("80-88", "fav", 0.81, 0.87, 60), ("88-97", "fav", 0.88, 0.97, 150)]
N, SEED = 40000, 20261112
def pf(x):
    w = sum(v for v in x if v > 0); l = -sum(v for v in x if v < 0)
    return float("inf") if l == 0 else w / l
def cash(p, win):
    fee = math.ceil(0.07 * p * (1 - p) * 10 * 100 - 1e-9) / 100
    return (10 * (1 - p) - fee) if win else (-10 * p - fee)
rng = random.Random(SEED); out = {"what": __doc__.split("\n")[0], "blocks_simulated_per_band": N, "seed": SEED, "hot_share_by_luck": {}, "median_block_length": {}, "p90_block_length": {}}
for name, kind, lo, hi, mn in BANDS:
    hot, lens = 0, []
    for _ in range(N):
        res, rare = [], 0
        while len(res) < mn or rare < 10:
            p = round(rng.uniform(lo, hi), 2); w = rng.random() < p - 0.01; res.append(cash(p, w)); rare += (w if kind == "cheap" else (not w))
        h = len(res) // 2; lens.append(len(res))
        if pf(res) >= 1.3 and pf(res[:h]) >= 1.0 and pf(res[h:]) >= 1.0: hot += 1
    lens.sort(); out["hot_share_by_luck"][name] = round(hot / N, 4); out["median_block_length"][name] = lens[N // 2]; out["p90_block_length"][name] = lens[int(0.9 * N)]
print(json.dumps(out, indent=1))
