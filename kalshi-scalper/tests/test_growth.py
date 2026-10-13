"""Plain assert tests for GROWTH (src/scalper/growth.py); run with: python tests/test_growth.py. Each states a consequence, not a mechanism."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import growth as G


def e(series, close, price, net, day="2026-10-01"):
    return {"series": series, "close_ts": close, "price": price, "net": net, "day": day}


R = random.Random(1)
# No entries: the balance is exactly what was paid in, a deposit landing on day 30, 60 and so on.
p = G.simulate_path([[]], 0.0, R, horizon=95)
assert p[0] == 500.0 and p[29] == 500.0 and p[30] == 1000.0 and p[60] == 1500.0 and p[90] == 2000.0

# Size follows the start-of-day balance: $500 / $46.50 is 10 contracts, and never more than 40.
win = [[[e("KXBTC15M", 1000, 0.92, 0.05)]]]
assert abs(G.simulate_path(win, 0.0, R, horizon=1, fill=1.0)[0] - 500.5) < 1e-9
assert abs(G.simulate_path(win, 0.0, R, horizon=1, start=100000.0, fill=1.0)[0] - 100002.0) < 1e-9

# The daily stop is 5% of the starting balance ($25): losses of $9 each are placed until the day is down $27, then nothing more that day.
loss = lambda t: [e("KXBTC15M", t, 0.92, -0.9)]
day = [[loss(1000)], [loss(2000)], [loss(3000)], [loss(4000)], [loss(5000)]]
assert abs(G.simulate_path([[w[0] for w in day]], 0.0, R, horizon=1, fill=1.0)[0] - 473.0) < 1e-9, "three losses, then the stop ends the day: four and five are never placed"
assert abs(G.simulate_path([[w[0] for w in day[:2]]], 0.0, R, horizon=1, fill=1.0)[0] - 482.0) < 1e-9, "two losses ($18) are under the stop"
# ... and the stop only lasts the day: the next day trades again.
d2 = G.simulate_path([[[loss(1000)[0]], [loss(2000)[0]], [loss(3000)[0]], [loss(4000)[0]]]], 0.0, R, horizon=2, fill=1.0)
assert abs(d2[0] - 473.0) < 1e-9 and d2[1] < d2[0] and abs(d2[1] - (473.0 - 3 * 9.0 * (int(473.0 / 46.5) / 10))) < 1e-6

# The window cap: 4.5% of $500 is $22.50. Two 10 contract orders at 92c cost $18.40 together and fit; a third would make $27.60 and is skipped, the first is never cut.
w3 = [[[e("KXBTC15M", 1000, 0.92, 0.05), e("KXGOLD15M", 1000, 0.92, 0.05), e("KXETH15M", 1000, 0.92, 0.05)]]]
assert abs(G.simulate_path(w3, 0.0, R, horizon=1, fill=1.0)[0] - 501.0) < 1e-9, "only two of the three same-window entries are placed"
# Series order decides who goes without: Bitcoin and gold before Ethereum, whatever order the entries arrive in.
shuffled = [[[e("KXETH15M", 1000, 0.92, -0.9), e("KXGOLD15M", 1000, 0.92, 0.05), e("KXBTC15M", 1000, 0.92, 0.05)]]]
assert G.by_day([x for w in shuffled[0] for x in w])[0][0][-1]["series"] == "KXETH15M"
# The first order of a window is never cut to zero, even when it alone exceeds the cap (a $10 account: 4.5% is 45c, one contract costs 92c).
assert abs(G.simulate_path(win, 0.0, R, horizon=1, start=10.0, fill=1.0)[0] - 10.05) < 1e-9
# The edge shift is added to every entry's net per contract.
assert abs(G.simulate_path(win, 0.02, R, horizon=1, fill=1.0)[0] - (500.0 + 10 * 0.07)) < 1e-9
# The edge shift moves every entry's net equally, so a zero-fill account never changes whatever the shift.
assert G.simulate_path(win, 0.5, R, horizon=3, fill=0.0)[-1] == 500.0
# Percentile and summary helpers.
assert G.percentile([1, 2, 3, 4, 5], 0.5) == 3 and G.percentile([1, 2, 3, 4, 5], 0.0) == 1 and G.percentile([1, 2, 3, 4, 5], 1.0) == 5
s = G.summarize([[600.0] * 360, [300.0] * 360])
assert s[30]["paid"] == 500.0 and s[360]["paid"] == 500.0 + 500.0 * 11 and s[30]["below"] == 0.5
code = "\n".join(l.split("#")[0] for l in Path(G.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("GROWTH passed")
