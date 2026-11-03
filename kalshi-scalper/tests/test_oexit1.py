"""Synthetic tests for scalper.oexit1 (plain runner)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import oexit1

CT = 10_000
def cs(b60, b0, yes=True):
    # candle tuples (bid_c, ask_c, vol, oi); for NO side bid = 1 - ask
    if yes:
        return {CT - 60: (b60, b60 + .01, 1, 1), CT: (b0, min(b0 + .01, 1.0), 1, 1)}
    return {CT - 60: (1 - b60 - .01, 1 - b60, 1, 1), CT: (max(0, 1 - b0 - .01), 1 - b0, 1, 1)}

fails = 0
def check(name, cond):
    global fails
    if not cond:
        fails += 1; print("FAIL", name)

# fee rounding: 7% x 10 x .06 x .94 = 0.03948 -> 0.04
check("fee", abs(oexit1.fee_usd(.06, 10) - 0.04) < 1e-9)
# without: loss costs price plus fee
n, s, _ = oexit1.simulate(.06, True, cs(.1, .0), CT, False, 10)
check("loss", abs(n - (-0.6 - 0.04)) < 1e-9 and not s)
# 3x shown at -60 (0.20 >= 0.18), sale at close bid 0.999 half of 10, win
n_hold = oexit1.simulate(.06, True, cs(.2, .999), CT, True, 10)[0]
n, s, sp = oexit1.simulate(.06, True, cs(.2, .999), CT, True, 10, 3.0)
check("sold", s and sp == .999)
check("sold net", abs(n - (n_hold + 5 * (.999 - 1.0) - oexit1.fee_usd(.999, 5))) < 1e-9)
# below 3x: no sale, equal to hold
n, s, _ = oexit1.simulate(.06, True, cs(.17, .999), CT, True, 10, 3.0)
check("no trigger", not s and n == oexit1.simulate(.06, True, cs(.17, .999), CT, True, 10)[0])
# trigger on the last candle only: no later candle, no sale
n, s, _ = oexit1.simulate(.06, True, cs(.10, .999), CT, True, 10, 3.0)
check("last candle", not s)
# look-ahead: trigger at -60, close candle bid 0 -> no sale, loss stays a loss
n, s, _ = oexit1.simulate(.06, True, cs(.5, .0), CT, False, 10, 3.0)
check("no bid", not s)
# NO side uses 1 - ask as bid
n, s, sp = oexit1.simulate(.06, False, cs(.2, .99, yes=False), CT, True, 10, 3.0)
check("no side", s)
# odd count: 9 contracts sell 4
n9, s9, _ = oexit1.simulate(.5, True, cs(.9, .99), CT, True, 9, 1.5)
check("half of 9", s9 and abs(n9 - (9 * .5 - oexit1.fee_usd(.5, 9) + 4 * (.99 - 1) - oexit1.fee_usd(.99, 4))) < 1e-9)
# splits
sets, d = oexit1.split_dates(["d%02d" % i for i in range(9)])
check("thirds", len(sets["HOLD"]) == 3 and len(sets["H1"]) + len(sets["H2"]) == 6 and "d08" in sets["HOLD"])
# summarize
s = oexit1.summarize([1, -1, -1, -1, 2])
check("summ", s["longest_loss"] == 3 and abs(s["win"] - .4) < 1e-9 and abs(s["pf"] - 3 / 3) < 1e-9)
print("test_oexit1:", "ok" if not fails else f"{fails} FAILED"); sys.exit(1 if fails else 0)
