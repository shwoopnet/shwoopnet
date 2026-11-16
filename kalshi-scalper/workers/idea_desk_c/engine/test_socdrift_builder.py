#!/usr/bin/env python3
"""SOCDRIFT builder test (synthetic, no network): builds the two candle job files from the hand-case list and runs the pull runner's OWN check_job and dry_run on them
(scripts/kalshi_pull.py of the repo; set KALSHI_PULL_PY to its path, default ../../../../scripts/kalshi_pull.py). Nothing is sent."""
import importlib.util, json, os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_socdrift as TS

RUNNER = os.environ.get("KALSHI_PULL_PY", os.path.join(HERE, "..", "..", "..", "..", "scripts", "kalshi_pull.py"))


class Builder(unittest.TestCase):
    def test_build_and_dry_run(self):
        root = TS.fixture()[0]
        pre = os.path.join(tempfile.mkdtemp(), "SOCDRIFT_CANDLES")
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "build_socdrift_candles.py"), root, pre], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        job = json.load(open(pre + "_P1.json"))
        self.assertEqual(len(job["requests"]), 1)                                  # one game in the fixture
        q = job["requests"][0]["params"]
        K = TS.KL.iso("2026-10-25T16:30:00")
        self.assertEqual((q["start_ts"], q["end_ts"], q["period_interval"]), (K - 31 * 3600, K, 60))
        self.assertEqual(len(q["market_tickers"].split(",")), 3)
        self.assertEqual(job["max_requests"], len(job["requests"]) + 12)
        self.assertTrue(os.path.exists(RUNNER), "runner not found: " + RUNNER)
        spec = importlib.util.spec_from_file_location("kalshi_pull", RUNNER)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        job["job_id"] = "SOCDRIFT_CANDLES_P1"
        self.assertTrue(m.check_job(job))                                          # raises Refused on any problem
        lines = []
        m.dry_run(job, out=lines.append)                                           # the runner's own dry run: no request, nothing written
        self.assertTrue(any("dry run: no request was sent" in l for l in lines))


if __name__ == "__main__":
    unittest.main()
