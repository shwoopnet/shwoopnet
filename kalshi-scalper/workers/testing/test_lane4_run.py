import json
import lane4_run as R, lane4_fixture_second as fx
J = fx.build(); data = {n: {int(t): tuple(v) for t, v in s.items()} for n, s in J["data"].items()}; fund = {n: {int(t): r for t, r in f.items()} for n, f in J["funding"].items()}
names = R.pool(data, fund); assert "KXFFFPERP" not in names and len(names) == 7          # the name with no prints is out
short = {n: dict(list(sorted(s.items()))[:900]) for n, s in data.items()}; assert R.pool(short, fund) == []          # under 5 ET dates of candles: out
one = dict(fund); one["KXAAAPERP"] = dict(list(sorted(fund["KXAAAPERP"].items()))[:1]); assert "KXAAAPERP" not in R.pool(data, one)          # under 2 prints: out
print("lane4 run tests passed")
