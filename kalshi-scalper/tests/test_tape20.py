import sys
sys.path.insert(0, "src")
from scalper import tape20 as T

f = {"yes": 600.0, "no": 400.0, "yes60": 200.0, "no60": 100.0, "n": 50, "n60": 30, "max": 400.0, "pages": 1}
assert abs(T.share(f, "yes") - 0.6) < 1e-9 and abs(T.share(f, "no") - 0.4) < 1e-9
assert abs(T.share(f, "yes", True) - 2 / 3) < 1e-9
assert abs(T.head_share(f, "yes") - 400 / 700) < 1e-9            # (600-200) / ((600-200) + (400-100))
rows = [{"ticker": "A", "side": "yes", "series": "KXBTC15M", "day": "2026-10-01", "net": 0.05}]
a = T.attach(rows, {"A": f})
assert len(a) == 1 and a[0]["maxr"] == 400.0 / 20.0 and abs(a[0]["burst"] - 0.6) < 1e-9
assert T.attach(rows, {}) == []
assert len(T.rules(a)) == 16
print("ok")
