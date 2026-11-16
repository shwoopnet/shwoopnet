import os, tempfile, opengap1_fetch as f
calls = []
S, E = "2026-11-16", "2026-11-21"
def stub(cost):
    def get(path, p): calls.append((path, p["dataset"], p["schema"], p["symbols"])); return str(cost) if path == "metadata.get_cost" else b"x,y\n"
    return get
# the three requests are exactly the registered ones; no EQUS.SUMMARY statistics; no streaming of anything else
assert [(r[1], r[2], r[3]) for r in f.REQUESTS] == [("XNAS.ITCH", "statistics", "QQQ,NVDA,AAPL"), ("ARCX.PILLAR", "statistics", "SPY"), ("EQUS.SUMMARY", "ohlcv-1d", "SPY,QQQ,NVDA,AAPL")] and (f.FIRST_START, f.LAST_END, f.MAX_DAYS, f.LIMIT) == ("2026-11-13", "2027-02-02", 10, 0.01)
d = tempfile.mkdtemp()
f.get = stub(0.0001); f.main(d, S, E, True); assert [c[0] for c in calls] == ["metadata.get_cost"] * 3 and not os.listdir(d), calls          # cost-only pulls nothing
calls.clear(); f.main(d, S, E); assert [c[0] for c in calls] == ["metadata.get_cost"] * 3 + ["timeseries.get_range"] * 3 and sorted(os.listdir(d)) == ["arcx_stat.csv", "equs_1d.csv", "xnas_stat.csv"], calls
calls.clear(); f.get = stub(0.0100001)           # three costs of 0.0100001 are over the limit: nothing is pulled
d2 = tempfile.mkdtemp()
try: f.main(d2, S, E); raise AssertionError("must refuse")
except SystemExit as e: assert "over the limit" in str(e) and all(c[0] == "metadata.get_cost" for c in calls) and not os.listdir(d2)
# a scratch directory inside a git repository is refused
try: f.main(os.path.dirname(os.path.abspath(__file__)) + "/scratch_in_repo", S, E); raise AssertionError("must refuse")
except SystemExit as e: assert "git repository" in str(e)
# dates: the first weekly pull (Mon Nov 16 to Fri Nov 20, end exclusive Nov 21) is allowed; before Nov 13, after Feb 2, longer than 10 days, empty or reversed is refused, and a refusal happens before any request
for st, en, ok in (("2026-11-16", "2026-11-21", True), ("2026-11-13", "2026-11-23", True), ("2026-11-12", "2026-11-20", False), ("2026-11-13", "2026-11-24", False), ("2027-01-26", "2027-02-02", True), ("2027-01-27", "2027-02-03", False), ("2026-11-16", "2026-11-16", False), ("2026-11-20", "2026-11-16", False)):
    calls.clear(); f.get = stub(0.0001)
    try: f.main(tempfile.mkdtemp(), st, en, True); got = True
    except SystemExit as e: got = False; assert "dates" in str(e) and not calls, (st, en, str(e), calls)
    assert got == ok, (st, en)
print("opengap1 fetch tests passed")
