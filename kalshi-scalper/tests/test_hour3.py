import sys
from datetime import datetime, timezone
sys.path.insert(0, "src")
from scalper import hour3 as T

ts = lambda h, mi: int(datetime(2026, 10, 1, h, mi, tzinfo=timezone.utc).timestamp())
rows = [{"close_ts": ts(5, 0)}, {"close_ts": ts(5, 15)}, {"close_ts": ts(5, 30)}, {"close_ts": ts(6, 0)}]
g, rest = T.split(rows)
assert len(g) == 2 and len(rest) == 2

assert T.forward(now=0.0).startswith("Refusing the registered read")      # before the read date nothing is scored
print("ok")
