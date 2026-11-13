"""Standing rule (h): does a scorer or script ever OPEN a file inside a HELDOUT_ folder? (Forensics, 2026-11-13.)

Stricter than leak_heldout_folder.py: it does not rely on how the code fails. A Python audit hook records every file open and every directory listing; the verdict is
whether anything inside the made-up held-out folder (by its real path) was opened. Four shapes of the same folder are tried: typed, a sub-folder, an innocently named
symlink to it, and "." from inside it. For a script with several folder arguments each position is tried in turn, the others given an ordinary made-up folder.
CONTROL: each target is first run on the ordinary folder; if it opens nothing there, a clean result on the held-out folder proves nothing and is printed as UNPROVEN.
The folders hold one made-up market; no real data.
usage: python3 -I leak_heldout_audit.py <testing|miner|deska|deskb> <path to that desk's workers folder (testing: workers/testing; miner: workers/history_miner; deska and deskb: workers)>
       deska takes two more: <INPLAYJUMP_SERIES.json> <the Testing Desk's workers/testing folder (for scorekit)>
       python3 -I leak_heldout_audit.py frozen <Desk B's workers folder> <the History Miner's workers/history_miner folder>      (added 2026-11-13: voidsnap.py, polgaph.py, candlegap.py)
"""
import sys, os, json, gzip, tempfile, subprocess, importlib, importlib.util, shutil

RUNNER = r'''
import sys, os, runpy
held = os.path.realpath(sys.argv[1]); script = sys.argv[2]; sys.argv = [script] + sys.argv[3:]
sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
seen = {"open": 0, "list": 0}
def hook(ev, args):
    if ev not in ("open", "os.listdir", "os.scandir", "glob.glob", "glob.glob/2"): return
    p = args[0] if args else None
    if p is None or isinstance(p, int): return
    try:
        p = os.fspath(p); p = p.decode() if isinstance(p, bytes) else p
        if ev.startswith("glob"): p = os.path.dirname(p) or "."
        rp = os.path.realpath(p)
    except Exception: return
    if (rp + os.sep).startswith(held + os.sep) or rp == held: seen["open" if ev == "open" else "list"] += 1
sys.addaudithook(hook)
how = "ended"
try: runpy.run_path(script, run_name="__main__")
except SystemExit as e: how = "exit: " + str(e)[:70].replace("\n", " ")
except BaseException as e: how = "error: " + type(e).__name__
sys.stderr.write("\nHFAUDIT %d %d %s\n" % (seen["open"], seen["list"], how))
'''

res = []
def line(name, verdict, detail=""):
    res.append(verdict); print("%-78s %-9s %s" % (name, verdict, detail))


def extra_rows(d):
    """added 2026-11-13 for the scorers frozen that night, so their control runs open real answer files and not only the manifest: made-up CS2 match rows (one void event,
    one played), a made-up politics market, one-minute and hourly candle answers, and the wheel book recorder's run-folder files. Nothing real."""
    import csv
    def cs2(ev, a, b, res):
        return [{"ticker": "%s-%s" % (ev, t), "event_ticker": ev, "close_time": "2026-10-20T18:00:00Z", "open_time": "2026-10-19T12:00:00Z", "result": r, "settlement_value_dollars": v, "status": "finalized"}
                for t, r, v in ((a, res[0], res[2]), (b, res[1], res[3]))]
    live = cs2("KXCS2GAME-26OCT201200AAABBB", "AAA", "BBB", ("scalar", "scalar", "0.5500", "0.4500")) + cs2("KXCS2GAME-26OCT201200CCCDDD", "CCC", "DDD", ("yes", "no", "1.0000", "0.0000"))
    hist = cs2("KXCS2GAME-26SEP011200EEEFFF", "EEE", "FFF", ("scalar", "scalar", "0.5000", "0.5000"))
    pol = [{"ticker": "KXEPSTEIN-26OCT20-Q1", "event_ticker": "KXEPSTEIN-26OCT20", "close_time": "2026-10-20T18:00:00Z", "open_time": "2026-10-10T12:00:00Z", "result": "no", "settlement_value_dollars": "0.0000", "status": "finalized"}]
    S = 1792512000; cd = lambda ts: {"end_period_ts": ts, "volume_fp": "5.00", "yes_bid": {"close_dollars": "0.4000"}, "yes_ask": {"close_dollars": "0.4200"}}
    tks = [m["ticker"] for m in live]
    files = [("live_KXCS2GAME", "/markets", {"series_ticker": "KXCS2GAME", "status": "settled"}, {"markets": live}), ("hist_KXCS2GAME", "/markets", {"series_ticker": "KXCS2GAME"}, {"markets": hist}),
             ("set_KXEPSTEIN", "/markets", {"series_ticker": "KXEPSTEIN", "status": "settled"}, {"markets": pol}),
             ("v001", "/markets/candlesticks", {"market_tickers": ",".join(tks), "start_ts": S - 11100, "end_ts": S + 28800, "period_interval": 1}, {"markets": [{"market_ticker": t, "candlesticks": [cd(S - 600), cd(S + 3660)]} for t in tks]}),
             ("h001", "/markets/candlesticks", {"market_tickers": pol[0]["ticker"], "start_ts": S - 864000, "end_ts": S, "period_interval": 60}, {"markets": [{"market_ticker": pol[0]["ticker"], "candlesticks": [cd(S - 7200), cd(S - 3600)]}]})]
    rows = []
    for n, (rid, path, params, body) in enumerate(files, 2):
        name = "%04d.json.gz" % n; gzip.open(os.path.join(d, name), "wt").write(json.dumps(body))
        rows.append({"id": rid, "status": 200, "file": name, "path": path, "params": params, "truncated": False})
    def w(name, cols, data):
        with gzip.open(os.path.join(d, name), "wt", newline="") as f: c = csv.writer(f); c.writerow(cols); c.writerows(data)
    w("coverage.csv.gz", ["series", "ticker", "first_seen_ms"], [["KXCS2GAME", tks[0], str(S * 1000)]])
    bc = ["t_recv_ms", "ticker", "yes_bid_px_1", "no_bid_px_1"]
    w("book_fast.csv.gz", bc, [[str(S * 1000 + 3000), tks[0], "0.4000", "0.5800"]]); w("book_slow.csv.gz", bc, []); w("polls.csv.gz", ["t_recv_ms", "tier"], [[str(S * 1000 + 3000), "fast"]])
    os.makedirs(os.path.join(d, "answers"), exist_ok=True); gzip.open(os.path.join(d, "answers", "0001.json.gz"), "wt").write(json.dumps({"markets": live}))
    json.dump({"files": [{"path": "/markets", "file": "0001.json.gz"}]}, open(os.path.join(d, "answers", "manifest.json"), "w"))
    return rows


def make(d):
    os.makedirs(d, exist_ok=True)
    mk = {"ticker": "KXESOCCERGAME-26OCT251200ZZZ-TIE", "event_ticker": "KXESOCCERGAME-26OCT251200ZZZ", "close_time": "2026-10-20T16:20:00Z", "open_time": "2026-10-20T15:00:00Z", "result": "yes",
          "market_ticker": "KXESOCCERGAME-26OCT251200ZZZ-TIE", "candlesticks": [{"end_period_ts": 1792943940, "yes_bid": {"close_dollars": "0.2000"}, "yes_ask": {"close_dollars": "0.2200"}}]}
    gzip.open(os.path.join(d, "0001.json.gz"), "wt").write(json.dumps({"markets": [mk]}))
    json.dump({"job": {"job_id": "X", "requests": [{"id": "r1", "path": "/markets", "params": {"series_ticker": "KXESOCCERGAME"}}]},
               "rows": [{"id": "r1", "status": 200, "file": "0001.json.gz", "path": "/markets", "params": {"series_ticker": "KXESOCCERGAME"}}] + extra_rows(d), "requests_sent": 1}, open(os.path.join(d, "manifest.json"), "w"))


tmp = tempfile.mkdtemp(prefix="ha_"); held = os.path.join(tmp, "HELDOUT_X"); make(held); make(os.path.join(held, "part1")); os.symlink(held, os.path.join(tmp, "innocent"))
ordinary = os.path.join(tmp, "DEV_X"); make(ordinary); outdir = os.path.join(tmp, "out"); os.makedirs(outdir)
runner = os.path.join(tmp, "_runner.py"); open(runner, "w").write(RUNNER)
SHAPES = [("typed", held, None), ("sub-folder", os.path.join(held, "part1"), None), ("symlink", os.path.join(tmp, "innocent"), None), ("relative", ".", held)]
# a fifth shape, added 2026-11-13, on request only (argv ends with --parent): the PARENT of the held-out folder is typed. A reader that walks or globs below the folder it is given
# would then reach the held-out files although no typed path names them. A reader that opens only <folder>/manifest.json and the files it lists cannot.
if sys.argv[-1] == "--parent":
    sys.argv.pop(); par = os.path.join(tmp, "PARENT"); os.makedirs(par); shutil.copytree(held, os.path.join(par, "HELDOUT_X")); held_parent = os.path.join(par, "HELDOUT_X")
    SHAPES = [("parent", par, None)]


def run_script(script, argv, cwd=None, target=held):
    p = subprocess.run([sys.executable, "-I", runner, target, script] + argv, capture_output=True, text=True, cwd=cwd or tmp, timeout=120)
    last = [l for l in p.stderr.splitlines() if l.startswith("HFAUDIT ")]
    if not last: return None, None, "runner died: " + p.stderr[-80:].replace("\n", " ")
    _, o, l, how = last[-1].split(" ", 3)
    return int(o), int(l), how


def script_target(label, script, template):
    """template: argv list; 'H' marks a folder position to attack, any other string is passed as is."""
    if not os.path.exists(script): line(label, "ABSENT", script[-60:]); return
    pos = [i for i, a in enumerate(template) if a == "H"]
    o, l, how = run_script(script, [ordinary if a == "H" else a for a in template], target=ordinary)
    proven = bool(o)
    leaks, notes = [], []
    for i in pos:
        for shape, path, cwd in SHAPES:
            argv = [(path if j == i else ordinary) if a == "H" else a for j, a in enumerate(template)]
            oo, ll, hw = run_script(script, argv, cwd=cwd, target=(held_parent if shape == "parent" else held))
            if oo is None: notes.append("%s arg %d: %s" % (shape, i + 1, hw)); continue
            if oo: leaks.append("%s arg %d: %d file(s) opened (%s)" % (shape, i + 1, oo, hw))
            elif ll: notes.append("%s arg %d: folder listed, no file opened" % (shape, i + 1))
    if leaks: line(label, "HOLE", "; ".join(leaks)[:400])
    elif not proven: line(label, "UNPROVEN", "the control run opened no file in an ordinary folder (%s), so a clean result proves nothing%s" % (how, ("; " + "; ".join(notes[:2])) if notes else ""))
    else: line(label, "REFUSES", "all %d cases; control opened %d file(s)%s" % (len(pos) * len(SHAPES), o, ("; note: " + "; ".join(sorted(set(notes))[:2])) if notes else ""))


# in-process functions: the same hook, in this process
_state = {"armed": None, "open": 0, "list": 0}
def _hook(ev, args):
    t = _state["armed"]
    if t is None or ev not in ("open", "os.listdir", "os.scandir", "glob.glob", "glob.glob/2"): return
    p = args[0] if args else None
    if p is None or isinstance(p, int): return
    try:
        p = os.fspath(p); p = p.decode() if isinstance(p, bytes) else p
        if ev.startswith("glob"): p = os.path.dirname(p) or "."
        rp = os.path.realpath(p)
    except Exception: return
    if (rp + os.sep).startswith(t + os.sep) or rp == t: _state["open" if ev == "open" else "list"] += 1
sys.addaudithook(_hook)


def probe(fn, path, target, cwd=None):
    here = os.getcwd(); _state.update(armed=os.path.realpath(target), open=0, list=0); how = "ended"
    try:
        if cwd: os.chdir(cwd)
        x = fn(path)
        if x is not None and not isinstance(x, (dict, list, tuple, str, int, float)):
            try: list(x)
            except TypeError: pass
    except SystemExit as e: how = "exit: " + str(e)[:60]
    except BaseException as e: how = "error: " + type(e).__name__
    finally: os.chdir(here); o, l = _state["open"], _state["list"]; _state["armed"] = None
    return o, l, how


def func_target(label, fn):
    o, l, how = probe(fn, ordinary, ordinary); leaks, notes = [], []
    for shape, path, cwd in SHAPES:
        oo, ll, hw = probe(fn, path, (held_parent if shape == "parent" else held), cwd)
        if oo: leaks.append("%s: %d file(s) opened (%s)" % (shape, oo, hw))
        elif ll: notes.append("%s: folder listed, no file opened" % shape)
    if leaks: line(label, "HOLE", "; ".join(leaks)[:400])
    elif not o: line(label, "UNPROVEN", "the control call opened no file in an ordinary folder (%s)" % how)
    else: line(label, "REFUSES", "all 4 cases; control opened %d file(s)%s" % (o, ("; note: " + notes[0]) if notes else ""))


def mod(name, path=None):
    if path:
        spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
    return importlib.import_module(name)


kind, root = sys.argv[1], os.path.abspath(sys.argv[2])
if kind == "testing":
    sys.path.insert(0, root); k = mod("scorekit")
    for nm in ("markets", "candles", "books"): func_target("scorekit.%s" % nm, lambda f, nm=nm: getattr(k, nm)([f]))
    func_target("scorekit.manifest", lambda f: k.manifest(f)); func_target("scorekit.iter_answers", lambda f: k.iter_answers(f))
    try:
        mb = mod("mapbreak"); sp = mb.load_cells()
        func_target("MAPBREAK mapbreak.matches (lists)", lambda f: mb.matches(sp, [f]))
        func_target("MAPBREAK mapbreak.build_candles (lists)", lambda f: mb.build_candles(sp, [f]))
        func_target("MAPBREAK mapbreak.measure (lists and candles)", lambda f: mb.measure(sp, [f], [f]))
        func_target("MAPBREAK mapbreak.measure (candles only held out)", lambda f: mb.measure(sp, [ordinary], [f]))
        func_target("MAPBREAK mapbreak.result_lookup (lists)", lambda f: mb.result_lookup([f]))
        func_target("MAPBREAK mapbreak.score (lists and candles)", lambda f: mb.score(sp, [f], [f]))
        func_target("MAPBREAK mapbreak.score (candles only held out)", lambda f: mb.score(sp, [ordinary], [f]))
        func_target("MAPBREAK mapbreak.history_count (lists)", lambda f: mb.history_count(sp, [f]))
    except BaseException as e: line("MAPBREAK mapbreak (import)", "UNPROVEN", type(e).__name__ + ": " + str(e)[:80])
    try:
        t3 = mod("tie3"); sp3 = t3.load_cells()
        func_target("TIE3 tie3.events (lists)", lambda f: t3.events(sp3, [f]))
        func_target("TIE3 tie3.build_candles (lists)", lambda f: t3.build_candles(sp3, [f]))
        func_target("TIE3 tie3.measure (lists and candles)", lambda f: t3.measure(sp3, [f], [f]))
        func_target("TIE3 tie3.measure (candles only held out)", lambda f: t3.measure(sp3, [ordinary], [f]))
    except BaseException as e: line("TIE3 tie3 (import)", "UNPROVEN", type(e).__name__ + ": " + str(e)[:80])
    try:
        es = mod("esoctie"); spe = es.load_cells()
        func_target("ESOCTIE (Testing build) esoctie.events", lambda f: es.events(spe, [f]))
        func_target("ESOCTIE (Testing build) esoctie.measure (lists and candles)", lambda f: es.measure(spe, [f], [f]))
        func_target("ESOCTIE (Testing build) esoctie.measure (candles only held out)", lambda f: es.measure(spe, [ordinary], [f]))
        func_target("ESOCTIE (Testing build) esoctie.score (candles only held out)", lambda f: es.score(spe, [ordinary], [f]))
    except BaseException as e: line("ESOCTIE testing esoctie (import)", "UNPROVEN", type(e).__name__ + ": " + str(e)[:80])
    for nm, attr in (("polcost", "rows_from"), ("poli2_count", "answers"), ("unrateround", "answers"), ("wxdayend", "answers")):
        try: m = mod(nm); func_target("%s.%s" % (nm, attr), getattr(m, attr))
        except BaseException as e: line(nm, "UNPROVEN", "import: " + type(e).__name__)
    try: b = mod("bundle"); func_target("bundle.split", lambda f: b.split(f, tempfile.mkdtemp(prefix="hao_")))
    except BaseException as e: line("bundle", "UNPROVEN", "import: " + type(e).__name__)
    for sc in sorted(f for f in os.listdir(root) if f.startswith("wheel0_second") and f.endswith(".py")):
        try:
            w = mod(sc[:-3])
            for fn in ("read_markets", "read_lists", "markets_from"):
                if hasattr(w, fn): func_target("WHEEL0 second build %s.%s" % (sc[:-3], fn), lambda f, fn=fn: getattr(w, fn)([f]))
        except BaseException as e: line(sc, "UNPROVEN", "import: " + type(e).__name__)
elif kind == "miner":
    sys.path.insert(0, os.path.join(root, "esoctie")); E = mod("esoctie")
    func_target("ESOCTIE (History Miner) esoctie.measure (lists and candles)", lambda f: E.measure([f], [f]))
    func_target("ESOCTIE (History Miner) esoctie.measure (candles only held out)", lambda f: E.measure([ordinary], [f]))
    func_target("ESOCTIE (History Miner) esoctie.score (lists and candles)", lambda f: E.score([f], [f]))
    func_target("ESOCTIE (History Miner) esoctie.score (candles only held out)", lambda f: E.score([ordinary], [f]))
    func_target("ESOCTIE (History Miner) esoctie.build_candles", lambda f: E.build_candles([f], os.path.join(tempfile.mkdtemp(prefix="hao_"), "job.json")))
    for dp, _, fs in os.walk(root):
        for f in sorted(fs):
            if f.endswith(".py") and f not in ("esoctie.py", "scorekit.py") and not f.startswith("test_") and "manifest.json" in open(os.path.join(dp, f), errors="replace").read():
                script_target("History Miner script %s" % os.path.relpath(os.path.join(dp, f), root), os.path.join(dp, f), ["H"])
elif kind == "frozen":
    # the three scorers frozen on the night of Nov 12 to 13 that had no leak test: Desk B's voidsnap.py and polgaph.py, the History Miner's candlegap.py. Every folder argument of
    # every command that takes one. The files a command needs beside its folders (a sample file, a decisions file) are made first by the scorer's own command on the ordinary folder.
    miner = os.path.abspath(sys.argv[3]); VS = os.path.join(root, "voidsnap", "voidsnap.py"); PG = os.path.join(root, "polgap", "polgaph.py"); CG = os.path.join(miner, "candlegap", "candlegap.py")
    import hashlib
    for f in (VS, PG, CG): print("target %s sha256 %s" % (os.path.relpath(f, os.path.dirname(root)) if f != CG else os.path.relpath(f, os.path.dirname(miner)), hashlib.sha256(open(f, "rb").read()).hexdigest()[:16]))
    smp = os.path.join(tmp, "sample.json"); dec = os.path.join(tmp, "dec.json")
    r1 = subprocess.run([sys.executable, "-I", VS, "sample", ordinary, smp], capture_output=True, text=True, cwd=tmp)
    r2 = subprocess.run([sys.executable, "-I", PG, "decide", ordinary, ordinary, dec], capture_output=True, text=True, cwd=tmp)
    print("helper files made by the scorers' own commands on the ordinary folder: sample.json %s, dec.json %s" % ("yes" if os.path.exists(smp) else "NO (" + r1.stderr[-90:].replace("\n", " ") + ")", "yes" if os.path.exists(dec) else "NO (" + r2.stderr[-90:].replace("\n", " ") + ")"))
    script_target("VOIDSNAP voidsnap.py sample <lists> <out>", VS, ["sample", "H", os.path.join(outdir, "s.json")])
    script_target("VOIDSNAP voidsnap.py measure <lists> <candles> <sample>", VS, ["measure", "H", "H", smp])
    script_target("POLGAPH polgaph.py hourly-job <lists> <out>", PG, ["hourly-job", "H", os.path.join(outdir, "hj.json")])
    script_target("POLGAPH polgaph.py decide <lists> <hourly> <out>", PG, ["decide", "H", "H", os.path.join(outdir, "d.json")])
    script_target("POLGAPH polgaph.py score <lists> <hourly> <minute> <decisions>", PG, ["score", "H", "H", "H", dec])
    script_target("CANDLEGAP candlegap.py <recorder run> <pull>", CG, ["H", "H"])
elif kind == "deskb":
    R = os.path.join(root, "rematch"); pairs = os.path.join(tmp, "pairs.json"); json.dump([], open(pairs, "w"))
    script_target("REMATCH stage 1 rematch/build_stage1_job.py <lists> <out>", os.path.join(R, "build_stage1_job.py"), ["H", outdir])
    script_target("REMATCH stage 1 rematch/stage1_measure.py <lists> <candles> <pairs>", os.path.join(R, "stage1_measure.py"), ["H", "H", pairs])
    script_target("REMATCH rematch/count_listing.py <lists>", os.path.join(R, "count_listing.py"), ["H"])
    script_target("MAPBREAK (Desk B counting) mapbreak/count_lists.py <lists>", os.path.join(root, "mapbreak", "count_lists.py"), ["H"])
    script_target("NHLOT nhlot/build_candles_job.py <lists> <out>", os.path.join(root, "nhlot", "build_candles_job.py"), ["H", outdir])
    script_target("NHLOT nhlot/measure_prices.py <candles> <games.json>", os.path.join(root, "nhlot", "measure_prices.py"), ["H", os.path.join(root, "nhlot", "games.json")])
    for sub in ("hourlytemp", "pol_i2", "census"):
        d = os.path.join(root, sub)
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if f.endswith(".py") and not f.startswith("test_") and f != "count_gaps.py" and "manifest.json" in open(os.path.join(d, f), errors="replace").read():
                script_target("Desk B other %s/%s <folder> <out>" % (sub, f), os.path.join(d, f), ["H", outdir])
    # added 2026-11-13 (the Head's order: make econlag reachable): each stage of econlag.py by its own command line, and Desk B's remaining readers
    EC = os.path.join(root, "econlag", "econlag.py"); plan = os.path.join(tmp, "plan.json"); json.dump({}, open(plan, "w")); empty = os.path.join(tmp, "empty.json"); json.dump([], open(empty, "w"))
    script_target("ECONLAG econlag.py calendar <run> <out>", EC, ["calendar", "H", outdir])
    script_target("ECONLAG econlag.py build-b <out> <run>", EC, ["build-b", outdir, "H"])
    script_target("ECONLAG econlag.py scan <out> <run>", EC, ["scan", outdir, "H"])
    script_target("ECONLAG econlag.py fade-count <out> <run>", EC, ["fade-count", outdir, "H"])
    script_target("ECONLAG econlag.py score <out> <plan> <run>", EC, ["score", outdir, plan, "H"])
    script_target("Desk B other breaksweep/sweep_listing.py <run> <out>", os.path.join(root, "breaksweep", "sweep_listing.py"), ["H", outdir])
    script_target("Desk B other census/settle_speed.py <run> <out>", os.path.join(root, "census", "settle_speed.py"), ["H", outdir])
    script_target("Desk B other census/first_cut.py <dir> <out>", os.path.join(root, "census", "first_cut.py"), ["H", outdir])
    script_target("Desk B other ingame_m1/measure.py <games> <run>", os.path.join(root, "ingame_m1", "measure.py"), [empty, "H"])
    script_target("Desk B other ingame_m1/drift_addition.py <games> <run>", os.path.join(root, "ingame_m1", "drift_addition.py"), [empty, "H"])
    script_target("Desk B other pol_i2/count_gaps.py <markets> <run>", os.path.join(root, "pol_i2", "count_gaps.py"), [empty, "H"])
    script_target("Desk B other polcount/count_families.py <folder>", os.path.join(root, "polcount", "count_families.py"), ["H"])
    script_target("Desk B other polcount/count_polrec.py <folder>", os.path.join(root, "polcount", "count_polrec.py"), ["H"])
    script_target("Desk B other combo_s3/s3_score.py <checkout> <time>", os.path.join(root, "combo_s3", "s3_score.py"), ["H", "2026-11-13T00:00:00Z"])
elif kind == "deska":
    V, J = os.path.join(root, "desk_a_verify"), os.path.join(root, "desk_a_jobs")
    ser = None
    for cand in (os.path.join(root, "inplayjump", "INPLAYJUMP_SERIES.json"), os.path.join(os.path.dirname(root), "workers", "inplayjump", "INPLAYJUMP_SERIES.json")):
        if os.path.exists(cand): ser = cand
    ser = ser or (sys.argv[3] if len(sys.argv) > 3 else os.path.join(tmp, "series.json"))
    if not os.path.exists(ser): json.dump({"families_ranked_by_events": []}, open(ser, "w"))
    script_target("INPLAYJUMP pilot desk_a_jobs/build_inplayjump_pilot.py <series> <lists> <out>", os.path.join(J, "build_inplayjump_pilot.py"), [ser, "H", outdir])
    script_target("INPLAYJUMP pilot desk_a_jobs/build_inplayjump_pilotval.py <series> <lists> <out>", os.path.join(J, "build_inplayjump_pilotval.py"), [ser, "H", outdir])
    script_target("INPLAYJUMP desk_a_jobs/build_inplayjump_candles.py clock <series> <lists> <out>", os.path.join(J, "build_inplayjump_candles.py"), ["clock", ser, "H", outdir])
    script_target("INPLAYJUMP engine desk_a_verify/inplayjump.py dev <series> ESOCCER <lists> -- <candles> <scorekit>", os.path.join(V, "inplayjump.py"), ["dev", ser, "ESOCCER", "H", "--", "H", (sys.argv[4] if len(sys.argv) > 4 else ordinary)])      # the last argument is the Testing Desk's scorekit folder
    script_target("CFRTI-K desk_a_verify/cfrti_k.py dev <lists> <binary candles> <perp candles>", os.path.join(V, "cfrti_k.py"), ["dev", "H", "H", "H"])      # added 2026-11-13: its own command line
    script_target("CFRTI-K desk_a_verify/cfrti_k.py rows <lists> <binary candles> <perp candles> <out.csv>", os.path.join(V, "cfrti_k.py"), ["rows", "H", "H", "H", os.path.join(outdir, "rows.csv")])
    for f in sorted(os.listdir(V)):
        if f.endswith(".py") and f not in ("inplayjump.py", "heldout_guard.py", "cfrti_k.py") and "manifest.json" in open(os.path.join(V, f), errors="replace").read():
            script_target("Desk A other desk_a_verify/%s <folder> <folder>" % f, os.path.join(V, f), ["H", "H"])
    for f in sorted(os.listdir(J)):
        if f.endswith(".py") and not f.startswith("build_inplayjump") and "manifest.json" in open(os.path.join(J, f), errors="replace").read():
            script_target("Desk A other desk_a_jobs/%s <folder> <arg>" % f, os.path.join(J, f), ["H", "live"])
print("\n%d targets: %d REFUSES, %d HOLE, %d UNPROVEN, %d ABSENT" % (len(res), res.count("REFUSES"), res.count("HOLE"), res.count("UNPROVEN"), res.count("ABSENT")))
shutil.rmtree(tmp, ignore_errors=True)
