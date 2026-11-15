#!/usr/bin/env python3
"""ECONLAG FOMC cut test on MADE-UP data (EXPECTED_fomc_cut_nov15.md). In process; no network."""
import contextlib, csv, io, os, sys, tempfile, importlib.util
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
spec = importlib.util.spec_from_file_location("econlag", os.path.join(here, "econlag.py")); E = importlib.util.module_from_spec(spec); spec.loader.exec_module(E)
class Trap(dict):
    """A market that raises if any key other than close_time is read."""
    def __init__(self, close): super().__init__(close_time=close)
    def __getitem__(self, k):
        if k != "close_time": raise AssertionError("trap row read: %r" % (k,))
        return super().__getitem__(k)
    def get(self, k, d=None): raise AssertionError("trap row read via get: %r" % (k,))
    def __iter__(self): raise AssertionError("trap row iterated")
def mk(ev, close, n=3): return [{"ticker": "%s-%d" % (ev, i), "event_ticker": ev, "open_time": "2025-01-01T00:00:00Z", "close_time": close} for i in range(n)]
fed = mk("KXFEDDECISION-M1", "2025-07-30T18:00:00Z") + mk("KXFEDDECISION-M2", "2025-09-16T23:59:59Z")
fed += [Trap("2025-09-17T00:00:00Z") for _ in range(3)] + [Trap("2025-10-29T18:00:00Z") for _ in range(3)]
cpi = mk("KXCPI-25MAY", "2025-05-13T12:30:00Z", 2) + mk("KXCPI-25NOV", "2025-11-13T13:30:00Z", 2)
def fake(folder):
    return [({"id": "hist_KXFEDDECISION", "params": {"series_ticker": "KXFEDDECISION"}}, {"markets": fed}),
            ({"id": "live_KXCPI", "params": {"series_ticker": "KXCPI"}}, {"markets": cpi})]
E.load_run = fake
out = tempfile.mkdtemp(); buf = io.StringIO()
with contextlib.redirect_stdout(buf): E.cmd_calendar("unused", out)
o = buf.getvalue()
rows = list(csv.DictReader(open(os.path.join(out, "meetings.csv")))); prints = list(csv.DictReader(open(os.path.join(out, "prints.csv"))))
ok = []
ok.append(("1 no exception, 6 FOMC rows kept, only M1 and M2", len(rows) == 6 and {r["event"] for r in rows} == {"KXFEDDECISION-M1", "KXFEDDECISION-M2"}))
ok.append(("2 dropped count printed 6", "FOMC markets dropped at or after the cut (2025-09-17T00:00:00Z): 6" in o))
ok.append(("3 CPI prints unchanged by the cut (both CPI events kept in the range)", sorted(r["event"] for r in prints if r["series"] == "KXCPI") == ["KXCPI-25MAY", "KXCPI-25NOV"]))
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
