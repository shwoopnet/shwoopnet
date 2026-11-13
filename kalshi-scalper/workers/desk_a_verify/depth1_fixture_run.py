"""Run V2's DEPTH1 read through Desk A's wrapper on a MADE-UP fixture directory (Forensics' second build comparison, Nov 13 2026). Not a read of real data.
  python3 -I depth1_fixture_run.py <V2 kalshi-scalper dir> <fixture dir with MADE_UP_DATA> <result out dir>
Layout: <fixture>/<date>/<HHMM>/{book,trades,coverage,clock}.csv.gz. History and OICORE overlap are stubbed (no candle file): every window is 'not held'."""
import sys, os, csv, gzip, io, tempfile, contextlib, importlib.util
from pathlib import Path
root, fx, outd = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
assert (fx / "MADE_UP_DATA").exists(), "fixture must carry MADE_UP_DATA"
sys.path.insert(0, str(root / "src")); from scalper import depth1 as D
spec = importlib.util.spec_from_file_location("w", str(Path(__file__).with_name("depth1_wrapper.py"))); W = importlib.util.module_from_spec(spec); spec.loader.exec_module(W)
outd.mkdir(parents=True, exist_ok=True)
D.RESULT_TXT, D.RESULT_MD, D.MARKER = outd / "r.txt", outd / "r.md", outd / "started"
for p in (D.RESULT_TXT, D.RESULT_MD, D.MARKER):
    if p.exists(): p.unlink()
PFX = "book15r6/"
def names(): return [PFX + str(p.relative_to(fx)) for p in fx.glob("*/*/*.csv.gz")]
def blob(path):
    p = fx / path[len(PFX):]
    return list(csv.DictReader(io.TextIOWrapper(gzip.open(p)))) if p.exists() else []
D._names, D._blob = names, blob
D._oicore_held = lambda tk: {t: False for t in tk}
def history(): raise RuntimeError("history check skipped (no candle file in the fixture)")
D.history_check = history
W.install(D)
out = io.StringIO()
with contextlib.redirect_stdout(out): v = D.run(now=D.READ_NOT_BEFORE + 7200)
print("verdict:", v); print(out.getvalue()); print(D.RESULT_TXT.read_text() if D.RESULT_TXT.exists() else "(no result file)")
