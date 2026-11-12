"""Standing rule (h), Head of R&D, 2026-11-12 19:22Z: every scorer refuses a folder named HELDOUT_... unless its own flag is passed.
This test hands a made-up HELDOUT_ pull folder to every function in a desk's code that opens a pull folder, four ways:
  plain   : <tmp>/HELDOUT_X
  nested  : <tmp>/HELDOUT_X/part1          (a sub-folder of a joint pull)
  symlink : <tmp>/innocent -> HELDOUT_X    (an innocent name pointing at it)
  relative: "." with the working directory inside HELDOUT_X
PASS = the call raises (SystemExit or any error raised BEFORE a file of the folder is opened). FAIL = the folder's rows come back.
The folder holds one made-up market with a made-up result; no real data.
usage: python3 -I leak_heldout_folder.py testing <path to workers/testing>
       python3 -I leak_heldout_folder.py miner   <path to workers/history_miner>
"""
import sys, os, json, gzip, tempfile, importlib, importlib.util
kind, root = sys.argv[1], os.path.abspath(sys.argv[2])
res = []
def check(name, ok, detail=""):
    res.append(ok); print("%-96s %s %s" % (name, "PASS" if ok else "FAIL", detail))

def make(d):
    os.makedirs(d, exist_ok=True)
    body = {"markets": [{"ticker": "KXESOCCERGAME-26OCT251200ZZZ-TIE", "event_ticker": "KXESOCCERGAME-26OCT251200ZZZ", "close_time": "2026-10-25T16:20:00Z", "open_time": "2026-10-25T15:00:00Z", "result": "yes",
                         "candlesticks": [{"end_period_ts": 1792943940, "yes_bid": {"close_dollars": "0.2000"}, "yes_ask": {"close_dollars": "0.2200"}}], "market_ticker": "KXESOCCERGAME-26OCT251200ZZZ-TIE"}]}
    gzip.open(os.path.join(d, "0001.json.gz"), "wt").write(json.dumps(body))
    json.dump({"job": {"job_id": "X", "requests": [{"id": "r1"}]}, "rows": [{"id": "r1", "status": 200, "file": "0001.json.gz", "path": "/markets"}], "requests_sent": 1}, open(os.path.join(d, "manifest.json"), "w"))

tmp = tempfile.mkdtemp(prefix="hf_"); held = os.path.join(tmp, "HELDOUT_X"); make(held); make(os.path.join(held, "part1"))
os.symlink(held, os.path.join(tmp, "innocent"))
ok_dir = os.path.join(tmp, "DEV_X"); make(ok_dir)
CASES = [("plain", held, None), ("nested", os.path.join(held, "part1"), None), ("symlink", os.path.join(tmp, "innocent"), None), ("relative", ".", held)]

def consume(x):
    if x is None or isinstance(x, (dict, list, tuple, str, int, float)): return x
    try: return list(x)
    except TypeError: return x

def run(label, fn):
    """fn(folder) -> anything. First prove the call WORKS on an ordinary folder (else a refusal proves nothing), then try the four held-out shapes."""
    try: consume(fn(ok_dir)); works = True
    except BaseException as e: works = False; why = type(e).__name__
    if not works:
        print("%-96s SKIP (does not run on an ordinary made-up folder: %s; not counted)" % (label, why)); return
    for name, path, cwd in CASES:
        here = os.getcwd()
        try:
            if cwd: os.chdir(cwd)
            out = consume(fn(path)); refused = False
        except SystemExit as e: refused = True; out = str(e)[:60]
        except BaseException as e: refused = True; out = type(e).__name__
        finally: os.chdir(here)
        check("%s | %s" % (label, name), refused, "" if refused else "READ the folder")

sys.path.insert(0, root if kind == "testing" else os.path.join(root, "esoctie"))
def mod(name, path=None):
    if path:
        spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
    return importlib.import_module(name)

if kind == "testing":
    k = mod("scorekit")
    run("scorekit.markets", lambda f: k.markets([f]))
    run("scorekit.candles", lambda f: k.candles([f]))
    run("scorekit.manifest", lambda f: k.manifest(f))
    run("scorekit.iter_answers", lambda f: k.iter_answers(f))
    if hasattr(k, "books"): run("scorekit.books", lambda f: k.books([f]))
    for name, attr in (("polcost", "rows_from"), ("poli2_count", "answers"), ("unrateround", "answers"), ("wxdayend", "answers")):
        try: m = mod(name); run("%s.%s (reads the manifest itself, not through scorekit)" % (name, attr), getattr(m, attr))
        except BaseException as e: print("%-96s SKIP (import: %s)" % (name, type(e).__name__))
    try:
        b = mod("bundle"); run("bundle.split (reads a landed bundle folder)", lambda f: b.split(f, tempfile.mkdtemp(prefix="hfo_")))
    except BaseException as e: print("%-96s SKIP (import: %s)" % ("bundle", type(e).__name__))
    try:
        e = mod("esoctie"); spec = e.load_cells()
        run("testing esoctie.events (lists)", lambda f: e.events(spec, [f]))
        run("testing esoctie.measure (lists and candles)", lambda f: e.measure(spec, [f], [f]))
    except BaseException as ex: print("%-96s SKIP (import: %s)" % ("esoctie", type(ex).__name__))
    try:
        mb = mod("mapbreak"); spec = mb.load_spec() if hasattr(mb, "load_spec") else None
        if spec is not None: run("mapbreak.matches (lists)", lambda f: mb.matches(spec, [f]))
    except BaseException as ex: print("%-96s SKIP (import: %s)" % ("mapbreak", type(ex).__name__))
else:
    E = mod("esoctie")
    run("history-miner esoctie.measure", lambda f: E.measure([f], [f]))
    run("history-miner esoctie.score", lambda f: E.score([f], [f]))
    run("history-miner esoctie.build_candles", lambda f: E.build_candles([f], os.path.join(tempfile.mkdtemp(prefix="hfo_"), "job.json")))
    ks = mod("hm_scorekit", os.path.join(root, "esoctie", "scorekit.py"))
    run("history-miner esoctie/scorekit.markets (the pinned copy, called directly)", lambda f: ks.markets([f]))
    rc = os.path.join(root, "rematch_count", "rematch_count.py")
    if os.path.exists(rc):
        import subprocess
        def rcount(f):
            p = subprocess.run([sys.executable, "-I", rc, f], capture_output=True, text=True, cwd=os.getcwd())
            if p.returncode != 0: raise SystemExit(p.stderr[-80:])
            return p.stdout
        run("history-miner rematch_count.py (a script, run on the folder)", rcount)
print("\n%d checks, %d FAIL" % (len(res), sum(1 for x in res if not x)))
