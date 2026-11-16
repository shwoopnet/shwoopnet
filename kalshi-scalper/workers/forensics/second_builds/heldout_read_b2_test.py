#!/usr/bin/env python3
"""Tests of heldout_read_b2.py guards on invented files (no held-out data opened). python3 -I heldout_read_b2_test.py"""
import os, sys, tempfile, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import heldout_read_b2 as R
def main():
    b = tempfile.mkdtemp()
    R.check_pins()                                                          # the real files match their pins
    for n in R.PINS: shutil.copy(os.path.join(HERE, n), b)
    R.check_pins(b); open(os.path.join(b, "shadow_rank_b2.py"), "a").write("\n# changed\n")
    try: R.check_pins(b); raise AssertionError("a changed import must refuse")
    except SystemExit: pass
    fake = os.path.join(b, "fake.sqlite"); open(fake, "w").write("not the extract"); allow = os.path.join(b, "A.md")
    open(allow, "w").write("no line here\n")
    try: R.check_allow(fake, allow); raise AssertionError("no allow line must refuse")
    except SystemExit: pass
    me = os.path.abspath(R.__file__); open(allow, "w").write("x %s %s %s %s\n" % (os.path.basename(me), R.sha_of(me), R.EXTRACT_SHA, R.EXTRACT_XZ_SHA))
    try: R.check_allow(fake, allow); raise AssertionError("an extract that does not hash to the allowed value must refuse")
    except SystemExit: pass
    open(allow, "w").write("x %s %s %s\n" % (os.path.basename(me), "0" * 64, R.EXTRACT_SHA))
    try: R.check_allow(fake, allow); raise AssertionError("a line with another file sha must refuse")
    except SystemExit: pass
    print("heldout_read_b2 guards ok")
main()
