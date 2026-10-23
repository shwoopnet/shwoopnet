import sys
from datetime import datetime, timezone
sys.path.insert(0, "src")
from scalper import hour2 as T

ts = lambda h: int(datetime(2026, 10, 1, h, 0, tzinfo=timezone.utc).timestamp())
rows = [{"close_ts": ts(h)} for h in (3, 4, 7, 8, 0)]
night, rest = T.split(rows)
assert [T.hour(r) for r in night] == [4, 7] and [T.hour(r) for r in rest] == [3, 8, 0]      # 04:00 to 07:59 inclusive, 08:00 is out
n2, r2 = T.split(rows, (0, 4))
assert [T.hour(r) for r in n2] == [3, 0]
print("ok")
