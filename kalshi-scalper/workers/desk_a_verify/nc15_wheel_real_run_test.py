"""Tests of nc15_wheel_real_run.py on INVENTED rows only. python3 -I nc15_wheel_real_run_test.py"""
import os, sys, gzip, csv, tempfile, subprocess
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import nc15_wheel_real_run as R
def w(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", newline="") as f: x = csv.DictWriter(f, cols); x.writeheader(); x.writerows(rows)
EX = "KXWTI15M-26NOV131715-15"; OK = "KXWTI15M-26NOV141500-00"
with tempfile.TemporaryDirectory() as d:
    root, stage = os.path.join(d, "nc15"), os.path.join(d, "stage"); run = os.path.join(root, "2026-11-13", "0000")
    w(os.path.join(run, "book.csv.gz"), [{"ticker": EX, "t_recv_ms": 1}, {"ticker": EX, "t_recv_ms": 2}, {"ticker": OK, "t_recv_ms": 3}], ["ticker", "t_recv_ms"])
    w(os.path.join(run, "coverage.csv.gz"), [{"ticker": EX, "result": "yes"}, {"ticker": OK, "result": "no"}], ["ticker", "result"])
    w(os.path.join(run, "trades.csv.gz"), [{"ticker": OK}], ["ticker"])
    dt, dr = R.filter_tree(root, stage, R.load_excluded())
    assert dt == {EX} and dr == 2, (dt, dr)
    rows = list(csv.DictReader(gzip.open(os.path.join(stage, "2026-11-13", "0000", "book.csv.gz"), "rt"))); assert [r["ticker"] for r in rows] == [OK]
    cov = list(csv.DictReader(gzip.open(os.path.join(stage, "2026-11-13", "0000", "coverage.csv.gz"), "rt"))); assert [r["ticker"] for r in cov] == [OK]
    assert not os.path.exists(os.path.join(stage, "2026-11-13", "0000", "trades.csv.gz")), "only book and coverage are copied"
    assert len(R.load_excluded()) == 28
    r = subprocess.run([sys.executable, "-I", os.path.join(here, "nc15_wheel_real_run.py"), root, "2026-11-20T00:00:00Z", os.path.join(d, "o.csv"), os.path.join(d, "s2")], capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
    assert r.returncode != 0 and "WHEEL_BLOCK_READ" in (r.stderr + r.stdout), "must refuse without WHEEL_BLOCK_READ=1"
print("ALL OK")
