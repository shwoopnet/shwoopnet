import os, tempfile, opengap1_fetch as f
calls = []
def stub(cost):
    def get(path, p): calls.append((path, p["dataset"], p["schema"], p["symbols"])); return str(cost) if path == "metadata.get_cost" else b"x,y\n"
    return get
# the three requests are exactly the registered ones; no EQUS.SUMMARY statistics; no streaming of anything else
assert [(r[1], r[2], r[3]) for r in f.REQUESTS] == [("XNAS.ITCH", "statistics", "QQQ,NVDA,AAPL"), ("ARCX.PILLAR", "statistics", "SPY"), ("EQUS.SUMMARY", "ohlcv-1d", "SPY,QQQ,NVDA,AAPL")] and (f.START, f.END, f.LIMIT) == ("2026-11-05", "2026-11-14", 0.01)
d = tempfile.mkdtemp()
f.get = stub(0.0001); f.main(d, True); assert [c[0] for c in calls] == ["metadata.get_cost"] * 3 and not os.listdir(d), calls          # cost-only pulls nothing
calls.clear(); f.main(d); assert [c[0] for c in calls] == ["metadata.get_cost"] * 3 + ["timeseries.get_range"] * 3 and sorted(os.listdir(d)) == ["arcx_stat.csv", "equs_1d.csv", "xnas_stat.csv"], calls
calls.clear(); f.get = stub(0.0100001)           # three costs of 0.0100001 are over the limit: nothing is pulled
d2 = tempfile.mkdtemp()
try: f.main(d2); raise AssertionError("must refuse")
except SystemExit as e: assert "over the limit" in str(e) and all(c[0] == "metadata.get_cost" for c in calls) and not os.listdir(d2)
# a scratch directory inside a git repository is refused
try: f.main(os.path.dirname(os.path.abspath(__file__)) + "/scratch_in_repo"); raise AssertionError("must refuse")
except SystemExit as e: assert "git repository" in str(e)
print("opengap1 fetch tests passed")
