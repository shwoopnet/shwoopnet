"""Plain assert tests for SP1 (src/scalper/sp1.py); run with: python tests/test_sp1.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import sp1 as S
from scalper.scalps import STRESS, fee

# The registered rule, no more: twelve series, 12 hours before, YES ask 88c to 97c, history in its own file.
assert len(S.SERIES) == 12 and len(set(S.SERIES)) == 12 and S.SPORTS_DB.name == "sports.sqlite"
assert S.ENTRY_BEFORE_S == 12 * 3600 and S.BAND == (0.88, 0.97) and S.MIN_ENTRIES == 300 and S.MIN_DAYS == 10 and S.Z_BAR == 2.1

# The entry candle is the latest hour end at or before 12 h before the expected expiration: never later than the rule's time.
H = 3600
E = 1_800_000_000 - (1_800_000_000 % H) + 5400            # an expected expiration half way through an hour
assert S.entry_candle_end(E) <= E - S.ENTRY_BEFORE_S, "an entry later than 12 h before the start would use information the rule does not allow"
assert S.entry_candle_end(E) % H == 0 and E - S.ENTRY_BEFORE_S - S.entry_candle_end(E) < H
assert S.entry_candle_end(E - E % H + 12 * H) == E - E % H, "exactly on an hour boundary the candle ending then is the one used"

# Band edges are inclusive; outside, a bad quote or a crossed book is never taken. The YES side only.
assert S.take_entry(0.86, 0.88, "yes") is not None and S.take_entry(0.95, 0.97, "yes") is not None
assert S.take_entry(0.85, 0.87, "yes") is None and S.take_entry(0.96, 0.98, "yes") is None
assert S.take_entry(0.0, 0.90, "yes") is None and S.take_entry(0.9, 0.89, "yes") is None and S.take_entry(None, 0.9, "yes") is None and S.take_entry(0.9, None, "yes") is None
p, net, stress = S.take_entry(0.90, 0.92, "yes")
assert abs(net - (1 - 0.92 - fee(0.92))) < 1e-12 and abs(stress - (1 - 0.92 - fee(0.92, STRESS))) < 1e-12 and stress < net
assert abs(S.take_entry(0.90, 0.92, "no")[1] - (-0.92 - fee(0.92))) < 1e-12, "a favourite that loses costs the whole price plus the fee"

# Chunking: never more than 100 markets nor a span over 48 h in one request, nothing lost, nothing repeated.
ms = [{"ticker": f"T{i}", "exp_ts": 1_800_000_000 + i * 3600} for i in range(250)]
ch = S.chunk_markets(ms)
assert all(len(c) <= 100 and c[-1]["exp_ts"] - c[0]["exp_ts"] <= S.MAX_SPAN_S for c in ch)
assert sorted(m["ticker"] for c in ch for m in c) == sorted(m["ticker"] for m in ms) and S.chunk_markets([]) == []

# Simulation: a market is entered only if the entry candle exists; a missing candle means no entry, never a neighbouring candle.
close = 1_800_100_000
m = {"ticker": "A", "series": "KXNFLGAME", "exp_ts": E, "close_ts": close, "result": "yes"}
ce = S.entry_candle_end(E)
out = S.simulate([m], {"A": {ce: (0.90, 0.92, 10.0)}})
assert len(out) == 1 and out[0]["won"] == 1.0 and abs(out[0]["price"] - 0.92) < 1e-12
assert S.simulate([m], {"A": {ce - H: (0.90, 0.92, 10.0)}}) == [] and S.simulate([m], {}) == []
lose = S.simulate([dict(m, result="no")], {"A": {ce: (0.90, 0.92, 10.0)}})
assert lose[0]["won"] == 0.0 and lose[0]["net"] < -0.9

# Verdicts. Too little data is NOT_ENOUGH_DATA, never a pass or a fail.
def mk(n_days, per_day, loss_every, price=0.92):
    es = []
    for d in range(n_days):
        for i in range(per_day):
            won = 0.0 if (loss_every and (d * per_day + i) % loss_every == 0) else 1.0
            es.append({"day": f"2026-09-{d + 1:02d}", "price": price, "mid": price - 0.01, "won": won, "net": won - price - fee(price), "stress": won - price - fee(price, STRESS), "series": "X", "close_ts": d})
    return es
assert S.verdict(mk(5, 100, 20), [0.0])[0] == "NOT_ENOUGH_DATA" and S.verdict(mk(20, 5, 20), [0.0])[0] == "NOT_ENOUGH_DATA"
# A favourite that wins as often as its price says loses the fee: FALSIFIED.
assert S.verdict(mk(20, 20, 8), [-0.05] * 10)[0] == "FALSIFIED"
# Losses only 1 in 40 against a 92c price is a large real edge with both halves positive: clears the bar when nothing in the placebo does.
rows = []
for d in range(20):
    for i in range(20):
        won = 0.0 if (i == 0 and d % 2 == 0) else 1.0
        rows.append({"day": f"2026-09-{d + 1:02d}", "price": 0.92, "mid": 0.91, "won": won, "net": won - 0.92 - fee(0.92), "stress": won - 0.92 - fee(0.92, STRESS), "series": "X", "close_ts": d})
v, s = S.verdict(rows, [-0.03] * 10)
assert v == "NOT_YET_FALSIFIED" and s["mean"] > 0 and s["h1"] > 0 and s["h2"] > 0, (v, s)
# The same edge but a placebo that does as well: FALSIFIED. Beating random is part of the bar.
assert S.verdict(rows, [s["mean"] + 0.01] * 10)[0] == "FALSIFIED"
# One positive half is not enough.
bad = [dict(r, net=(-0.5 if r["day"] >= "2026-09-11" else 0.05)) for r in rows]
assert S.verdict(bad, [-0.03] * 10)[0] == "FALSIFIED"

# Each condition of the bar bites on its own, with the others satisfied.
def flat(day_net, day_stress=None):
    return [{"day": f"2026-09-{d + 1:02d}", "price": 0.92, "mid": 0.91, "won": 1.0, "net": day_net(d), "stress": (day_stress or day_net)(d), "series": "X", "close_ts": d} for d in range(20) for _ in range(20)]
wide_h2neg = flat(lambda d: 0.10 if d < 10 else -0.01)
vv, ss = S.verdict(wide_h2neg, [-0.03] * 10)
assert ss["mean"] > 0 and ss["z"] >= S.Z_BAR and ss["h1"] > 0 > ss["h2"] and ss["stress"] > 0 and vv == "FALSIFIED", (vv, ss)
vv, ss = S.verdict(flat(lambda d: -0.01 if d < 10 else 0.10), [-0.03] * 10)
assert ss["h1"] < 0 < ss["h2"] and ss["z"] >= S.Z_BAR and ss["stress"] > 0 and vv == "FALSIFIED", (vv, ss)
vv, ss = S.verdict(flat(lambda d: 0.10 if d < 10 else 0.01, lambda d: 0.01 if d < 10 else -0.05), [-0.03] * 10)
assert ss["h1"] > 0 and ss["h2"] > 0 and ss["z"] >= S.Z_BAR and ss["stress"] < 0 and vv == "FALSIFIED", (vv, ss)
vv, ss = S.verdict(flat(lambda d: 0.20 if d % 2 else -0.10), [-0.03] * 10)
assert ss["mean"] > 0 and ss["h1"] > 0 and ss["h2"] > 0 and ss["z"] < S.Z_BAR and vv == "FALSIFIED", (vv, ss)
vv, ss = S.verdict(flat(lambda d: 0.10 if d < 10 else 0.01), [-0.03] * 10)
assert ss["z"] >= S.Z_BAR and ss["h1"] > 0 and ss["h2"] > 0 and vv == "NOT_YET_FALSIFIED", (vv, ss)

# Close together markets fill a request to exactly 100 and no more.
dense = [{"ticker": f"D{i}", "exp_ts": 1_800_000_000 + i * 60} for i in range(250)]
assert [len(c) for c in S.chunk_markets(dense)] == [100, 100, 50]

code = "\n".join(l.split("#")[0] for l in Path(S.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("SP1 passed")
