"""FLOW1 tests: synthetic trades and candles only (no network, no tape)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import flow1 as F  # noqa: E402

fails = []


def check(name, cond):
    if not cond:
        fails.append(name)
        print("FAIL", name)


# candle tuple: (bid_c, ask_c, vol, oi)
CT = 1_790_000_000
def cs_with(sig, fill):
    return {CT - 180: sig, CT - 120: fill}

# M1: YES cheap. Taker "yes" = bought the cheap side, taker "no" = sold it.
rows = [("yes", 30.0), ("no", 70.0)]
check("M1 yes-cheap, net selling", abs(F.flow_of(rows, "yes") - (30 - 70) / 100) < 1e-12)
# M2: NO cheap with the same rows: taker 'no' is now a buy of the cheap side, sign flips.
check("M2 no-cheap flips sign", abs(F.flow_of(rows, "no") - (70 - 30) / 100) < 1e-12)
check("M3 antisymmetric", abs(F.flow_of(rows, "yes") + F.flow_of(rows, "no")) < 1e-12)
# M4: duplicates all count (no dedupe)
check("M4 duplicates counted", abs(F.flow_of(rows + rows, "yes") - F.flow_of(rows, "yes")) < 1e-12 and
      abs(F.flow_of([("yes", 10.0)] * 2 + [("no", 10.0)], "yes") - (20 - 10) / 30) < 1e-12)
# M5: no trades -> None; unknown side counts in total only
check("M5 empty", F.flow_of([], "yes") is None)
check("M6 unknown in total", abs(F.flow_of([("yes", 10.0), ("?", 10.0)], "yes") - 0.5) < 1e-12)
# M7: threshold boundary
check("M7 threshold fixed", F.THRESH == -0.036 and (-0.036 <= F.THRESH) and not (-0.0359 <= F.THRESH))

# E1: YES cheap: yes ask 0.20, yes bid 0.18 -> no ask 0.82. fill candle yes ask 0.22
e, why = F.cheap_entry(cs_with((0.18, 0.20, 1, 1), (0.20, 0.22, 1, 1)), CT)
check("E1 yes cheap", e == ("yes", 0.20, 0.22) and why == "ok")
# E2: NO cheap: yes bid 0.80 -> no ask 0.20; fill: yes bid 0.77 -> no ask 0.23
e, why = F.cheap_entry(cs_with((0.80, 0.82, 1, 1), (0.77, 0.79, 1, 1)), CT)
check("E2 no cheap", e[0] == "no" and abs(e[1] - 0.20) < 1e-9 and abs(e[2] - 0.23) < 1e-9)
# E3: hard limit 0.50 on the fill
e, why = F.cheap_entry(cs_with((0.46, 0.48, 1, 1), (0.50, 0.52, 1, 1)), CT)
check("E3 over limit", e is None and why == "over_limit")
# E4: out of band (3c), tie, missing candles
check("E4 band", F.cheap_entry(cs_with((0.02, 0.03, 1, 1), (0.02, 0.03, 1, 1)), CT)[1] == "out_of_band")
check("E5 tie", F.cheap_entry(cs_with((0.50, 0.50, 1, 1), (0.50, 0.50, 1, 1)), CT)[1] == "tie")
check("E6 missing fill", F.cheap_entry({CT - 180: (0.18, 0.20, 1, 1)}, CT)[1] == "no_fill_candle")
check("E7 missing signal", F.cheap_entry({}, CT)[1] == "no_signal_candle")

# C1: cuts partition the range into thirds, R6 start
check("C1 cuts", F.START < F.CUT1 < F.CUT2 < F.END and abs((F.CUT1 - F.START) - (F.END - F.CUT2)) <= 2)
check("C2 no window from Nov 3", F.END == 1793664000)
# F1: fee rounds up (C=10, p=0.27): 0.07*10*0.27*0.73=0.13797 -> 14c / 10
from scalper.gen6 import fee
check("F1 fee", abs(fee(0.27, 10) - 0.014) < 1e-9)
# P1: PF
check("P1 pf", abs(F.pf([2.0, -1.0, -1.0]) - 1.0) < 1e-12)
# P2: permutation p small for a perfectly separated label, ~uniform for none
rows = []
for d in range(30):
    for i in range(6):
        low = i < 3
        rows.append({"day": f"d{d}", "net": (0.5 if low else -0.3) + 0.01 * i, "low": low})
obs, p = F.perm_p(rows, 300)
check("P2 perm separated", obs > 0 and p < 0.02)
print("FLOW1 tests:", "FAIL " + str(fails) if fails else "ok")
sys.exit(1 if fails else 0)
