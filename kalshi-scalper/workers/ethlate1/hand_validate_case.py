#!/usr/bin/env python3
"""INDEPENDENT hand calculation (no engine code) for test 8 of the ETHLATE1 adapter: invented SEARCH and VALIDATE markets for two cells, A (cheap side yes at 0.30, band 6) and B (cheap side no at 0.42, band 8).
Per day 9 markets of each cell, 12 SEARCH days (2026-11-01 to 11-12) and 12 VALIDATE days (2026-11-13 to 11-24). Prints the figures the adapter must reproduce at the 2c haircut, hold exit, 10 contracts."""
import math
WINS = {"A_S": [3, 7, 2, 8, 4, 6, 5, 7, 3, 6, 4, 8], "A_V": [3, 7, 2, 8, 4, 6, 5, 7, 3, 6, 4, 8],
        "B_S": [6, 7, 5, 6, 7, 5, 6, 7, 5, 6, 7, 5], "B_V": [9, 9, 9, 9, 9, 8, 1, 1, 0, 0, 1, 1]}
def fee(p, n=10): return math.ceil(round(0.07 * n * p * (1 - p) * 100, 9)) / 100
def cell(paid2, wins):
    cost = paid2 * 10 + fee(paid2); w, l = 10 - cost, -cost
    days = [(wk * w + (9 - wk) * l) for wk in wins]
    xs = []                                   # entry order: day by day, wins first inside a day is NOT assumed: the engine sorts by (close, id); the half split below uses the day order
    return w, l, days
def pf(days_w): return None
for name, paid2, key in (("A", 0.32, ("A_S", "A_V")), ("B", 0.42, ("B_S", "B_V"))):
    w, l, _ = cell(paid2, [])
    print(name, "win %.2f loss %.2f" % (w, l))
    for k in key:
        wins = WINS[k]; tw = sum(wins); n = 9 * len(wins); tl = n - tw
        net = [wk * w + (9 - wk) * l for wk in wins]
        PF = tw * w / (tl * -l) if tl else float("inf")
        half = len(wins) // 2; h1, h2 = wins[:half], wins[half:]
        pf1 = sum(h1) * w / ((9 * half - sum(h1)) * -l) if 9 * half - sum(h1) else float("inf"); pf2 = sum(h2) * w / ((9 * half - sum(h2)) * -l) if 9 * half - sum(h2) else float("inf")
        m = sum(net) / len(net); sd = math.sqrt(sum((x - m) ** 2 for x in net) / (len(net) - 1)); z = m / (sd / math.sqrt(len(net))); p = 0.5 * math.erfc(z / math.sqrt(2))
        print("  %s: n %d wins %d PF2c %.4f | day-half wins %d / %d (PF halves by DAY order %.4f / %.4f) | day z %.4f p %.3e" % (k, n, tw, PF, sum(h1), sum(h2), pf1, pf2, z, p))
alpha = 0.05
print("BH threshold alpha*i/m at m = 6290756, i = 1: %.3e; i = 2: %.3e; at m = 2: %.3e and %.3e" % (alpha / 6290756, 2 * alpha / 6290756, alpha / 2, alpha))
