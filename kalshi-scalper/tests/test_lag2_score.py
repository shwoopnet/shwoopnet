import sys
sys.path.insert(0, "src")
from scalper import lag2_score as S

rows = [{"ticker": "A", "left": 120, "ts": 1000, "signal": None, "yesBid": 0.40, "yesAsk": 0.42},
        {"ticker": "A", "left": 90, "ts": 1030, "signal": "yes", "yesBid": 0.40, "yesAsk": 0.42},
        {"ticker": "A", "left": 60, "ts": 1060, "signal": "no", "yesBid": 0.30, "yesAsk": 0.32},     # ignored: the first signal is the trade
        {"ticker": "B", "left": 60, "ts": 2000, "signal": "no", "yesBid": 0.60, "yesAsk": 0.62},
        {"ticker": "C", "left": 60, "ts": 3000, "signal": "yes", "yesBid": 0.5, "yesAsk": 0.52}]      # no result yet: not scored
t = S.trades(rows, {"A": "yes", "B": "yes"})
assert len(t) == 2
a = next(x for x in t if x["close_ts"] == 1030)
assert abs(a["net"] - (1 - 0.42 - 0.07 * 0.42 * 0.58)) < 1e-9          # yes bought at the ask 0.42 and won
b = next(x for x in t if x["close_ts"] == 2000)
assert b["net"] < -0.39                                                  # no bought at 1 - 0.60 = 0.40 and lost
print("ok")
