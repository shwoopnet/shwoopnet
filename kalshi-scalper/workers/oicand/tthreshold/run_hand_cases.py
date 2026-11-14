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
import shutil
t2 = tempfile.mkdtemp()
def mk(*parts): q = os.path.join(t2, *parts); os.makedirs(q, exist_ok=True); return q
def runp(lists, cands, args=None):
    out, err = io.StringIO(), io.StringIO(); code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try: oicore_t.main(["--lists", lists, "--candles", cands, "--series", "S2", "--days", "3"] + (args or []), allowed=["S2"], cut=[])
        except SystemExit as e: code = e.code
    return code, out.getvalue(), err.getvalue()
src_l, src_c = d + "/lists/l1.json", d + "/cand/c1.json"
a_l = mk("OICAND_LISTS", "2026-11-14T0227Z_43546384963"); shutil.copy(src_l, a_l)
a_c = mk("OICAND_CANDLES_1", "2026-11-14T0253Z_43548715053"); shutil.copy(src_c, a_c)
for nm in ("2026-11-14T0413Z_43555574326", "2026-11-14T0501Z_43559459347", "2026-11-14T0541Z_43562765461"): mk("x", nm)
code, out, err = runp(a_l, a_c); ok.append(("h", code == 0 and "S2: listed windows 12 | windows used (n) 12" in out and "T 4 | NOT SEATED: T under 5" in out))
f_c = mk("POLGAPH_LISTS", "2026-11-13T0627Z_43378777252"); shutil.copy(src_c, f_c)
code, out, err = runp(a_l, f_c); ok.append(("f", isinstance(code, str) and code.startswith("REFUSED") and out == ""))
g_c = mk("HELDOUT_x"); shutil.copy(src_c, g_c)
code, out, err = runp(a_l, g_c); ok.append(("g", isinstance(code, str) and "HELDOUT_" in code))
i_c = mk("HELDOUT_y", "2026-11-14T0253Z_43548715053"); shutil.copy(src_c, i_c)
code, out, err = runp(a_l, i_c); ok.append(("i", isinstance(code, str) and "HELDOUT_" in code))
for k, v in ok: print(k, "PASS" if v else "FAIL")
sys.exit(0 if all(v for _, v in ok) else 1)
