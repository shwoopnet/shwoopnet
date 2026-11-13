"""Standing rule (h): refuse any folder that is, is inside, or points into a HELDOUT_ folder. Checks EVERY component of the absolute path AND of the resolved real path (so a nested part, a relative '.' with the cwd inside it, and an innocently named symlink are all caught).
  python3 -I heldout_guard.py selftest"""
import os, sys, tempfile
def refuse_heldout(path, who="this reader"):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)):
            raise SystemExit("REFUSED (%s): %s is, or is inside, or points into, a held-out folder (standing rule h); each card reads it once on the Head's own go" % (who, path))
def selftest():
    d = tempfile.mkdtemp(); h = os.path.join(d, "HELDOUT_X"); os.makedirs(os.path.join(h, "part1")); ok = os.path.join(d, "dev_ok"); os.makedirs(ok); link = os.path.join(d, "innocent"); os.symlink(h, link)
    refuse_heldout(ok)                                                     # an ordinary folder passes
    for shape, p in (("plain", h), ("nested", os.path.join(h, "part1")), ("symlink", link), ("symlink nested", os.path.join(link, "part1"))):
        try: refuse_heldout(p); raise AssertionError(shape + " not refused")
        except SystemExit: pass
    cwd = os.getcwd(); os.chdir(os.path.join(h, "part1"))
    try:
        try: refuse_heldout("."); raise AssertionError("relative '.' inside a held-out folder not refused")
        except SystemExit: pass
    finally: os.chdir(cwd)
    print("HELDOUT GUARD SELFTEST OK (plain, nested, relative, symlink, nested symlink)")
if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]: selftest()
    else: sys.exit(__doc__)
