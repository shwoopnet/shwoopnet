import sys
sys.path.insert(0, "src")
from scalper import gas1 as T

r = lambda date, net, loss=0: {"date": date, "net": net, "stress": net, "loss": loss, "price": 0.94}
assert T.judge([r("2026-10-23", 0.03), r("2026-10-24", 0.03)])["verdict"] == "NOT_ENOUGH_DATA"       # under 300 entries and 30 dates
rows = [r(f"2026-11-{d:02d}", 0.03) for d in range(1, 31) for _ in range(11)]                        # 330 entries, 30 dates, no variance
v = T.judge(rows)
assert v["verdict"] in ("NOT_YET_FALSIFIED", "NOT_ENOUGH_DATA") and v["n"] == 330, v
bad = [r(f"2026-11-{d:02d}", -0.02, 1 if d % 5 == 0 else 0) for d in range(1, 31) for _ in range(11)]
assert T.judge(bad)["verdict"] == "FALSIFIED"
assert abs(T.stress_net("yes", 0.9, "yes") - (0.1 - 0.07 * 0.9 * 0.1 * 1.2)) < 1e-12
print("ok")
