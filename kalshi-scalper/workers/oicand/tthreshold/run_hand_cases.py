#!/usr/bin/env python3
"""Runs the hand cases of EXPECTED_hand_t.md (the scope guard and the fixture figures). Made-up data only. Prints PASS or FAIL per case."""
import contextlib, io, os, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import oicore_t
d = tempfile.mkdtemp(); subprocess.run([sys.executable, os.path.join(here, "make_t_fixture.py"), d], check=True)
base = ["--lists", d + "/lists", "--candles", d + "/cand"]
def run(args, **kw):
    out, err = io.StringIO(), io.StringIO(); code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try: oicore_t.main(base + args, **kw)
        except SystemExit as e: code = e.code if isinstance(e.code, int) else 1
    return code, out.getvalue(), err.getvalue()
def cli(args): return subprocess.run([sys.executable, os.path.join(here, "oicore_t.py")] + base + args, capture_output=True, text=True)
ok = []
r = cli(["--series", "KXXRP15M"]); ok.append(("a", r.returncode == 2 and "series not allowed" in r.stderr and "OICORE-NC15" not in r.stdout))
r = cli(["--allowed-series", "S1", "--series", "S1"]); ok.append(("b", r.returncode == 2 and "unrecognized arguments" in r.stderr))
r = cli(["--cut-series", "S5", "--series", "KXHYPE15M"]); ok.append(("c", r.returncode == 2 and "unrecognized arguments" in r.stderr))
r = cli(["--series", "S1"]); ok.append(("d", r.returncode == 2 and "series not allowed" in r.stderr))
code, out, err = run(["--series", "S1", "S2", "S3", "S4", "S5", "--days", "3"], allowed=["S1", "S2", "S3", "S4", "S5"], cut=["S5"])
want = ["S1: listed windows 18 | windows used (n) 12", "T 110 | SEATED", "S2: listed windows 12 | windows used (n) 12", "T 4 | NOT SEATED: T under 5", "T n/a | NOT SEATED: fewer than 3", "S4: listed windows 19 | windows used (n) 14", "T 500 | SEATED", "S5: listed windows 13 | windows used (n) 13", "T 120 | SEATED | dropped: event830_forward_close=1"]
ok.append(("e", code == 0 and all(w in out for w in want)))
for k, v in ok: print(k, "PASS" if v else "FAIL")
sys.exit(0 if all(v for _, v in ok) else 1)
