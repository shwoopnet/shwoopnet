import sys
from datetime import datetime, timezone
sys.path.insert(0, "src")
from scalper import comm1 as T

close = int(datetime(2026, 10, 3, 14, 30, tzinfo=timezone.utc).timestamp())          # a Saturday, 14:30 UTC
raw = ("A", "KXSILVER15M", [(close - 900 + 60 * k, 0.50 + 0.04 * k, 0.51 + 0.04 * k, 0.5, 0.5) for k in range(0, 8)] + [(close - 360, 0.91, 0.92, 0.9, 0.9)], close, "yes")
m = T.as_market(raw)
assert m["c"][0]["bid"] == 0.50 and m["close"] == close
R = dict((n, f) for n, f in T.rules() if f is not None)
c, e = T.I.at(m, 360)
band = (0.88, 0.97)
assert R["SESSION_12_18"](m, c, e, band) == ("yes", 0.92) and R["SESSION_00_06"](m, c, e, band) is None
assert R["WEEKEND"](m, c, e, band) is not None and R["WEEKDAY"](m, c, e, band) is None
assert R["NO_DOWN_MINUTE"](m, c, e, band) is not None
assert len(T.rules()) == 13 and len([r for r in T.rules() if r[1] is not None]) == 9 and len(T.band_rules()) == 4      # 9 plain rules + 4 band rules = 13 per entry
print("ok")
