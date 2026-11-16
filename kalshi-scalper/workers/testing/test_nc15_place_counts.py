import calendar, collections, hashlib, json, os, tempfile, time, nc15_place_counts as N
d = tempfile.mkdtemp()
# the start constant: 2026-11-13T02:40:00Z
assert N.START_UTC == "2026-11-13T02:40:00Z" and N.START_TS == 1794537600 == calendar.timegm((2026, 11, 13, 2, 40, 0)) and N.TARGET == 60
assert [p[0] for p in N.PLACES] == ["WH-NC15-SILVER", "WH-NC15-COPPER", "WH-NC15-WTI", "WH-NC15-HYPE", "WH-NC15-BNB", "WH-NC15-USDCAD", "WH-NC15-NATGAS"] and [p[1] for p in N.PLACES] == ["KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXHYPE15M", "KXBNB15M", "KXUSDCAD15M", "KXNATGAS15M"]
# a stub core: count_places(root, start_ts) -> {series: Counter}; it records its arguments
core = os.path.join(d, "stub_core.py")
open(core, "w").write('''import collections
CALLS = []
def count_places(root, start_ts):
    open(__file__ + '.calls', 'a').write(repr((root, start_ts)) + chr(10))
    base = {"KXSILVER15M": 7, "KXCOPPER15M": 0, "KXWTI15M": 12, "KXHYPE15M": 61, "KXBNB15M": 3, "KXUSDCAD15M": 1, "KXNATGAS15M": 25, "KXEURUSD15M": 99, "KXGBPUSD15M": 98}
    return {s: collections.Counter({"fill-checked": n, "windows": 1000 + n, "cell": 500, "entering": 400}) for s, n in base.items()}
''')
csha = hashlib.sha256(open(core, "rb").read()).hexdigest()
allow = os.path.join(d, "allow.md"); line = lambda me, c: "- " + N.ALLOW_MARK + ": nc15_place_counts.py sha256 " + me + " core sha256 " + c
out = os.path.join(d, "nc15_place_counts.json")
def refused(msg, **kw):
    try: N.run("ROOT", out, "2026-11-16T17:00:00Z", core_file=core, core_sha=kw.pop("core_sha", csha), func="count_places", allow_file=allow, **kw); raise AssertionError("must refuse: " + msg)
    except SystemExit as e: assert msg in str(e), str(e)
refused("allow-list file cannot be read") if False else None
open(allow, "w").write("nothing\n"); refused("no allow-list line")
open(allow, "w").write(line("0" * 64, csha) + "\n"); refused("no allow-list line")
open(allow, "w").write(line(N.self_sha(), "0" * 64) + "\n"); refused("no allow-list line")
open(allow, "w").write(line(N.self_sha(), csha) + "\n")
refused("is not the pinned", core_sha="f" * 64) if False else None
open(allow, "w").write(line(N.self_sha(), "f" * 64) + "\n"); refused("is not the pinned", core_sha="f" * 64)          # the allow line names the pinned sha, but the core on disk differs from it
open(allow, "w").write(line(N.self_sha(), csha) + "\n")
obj = N.run("ROOT", out, "2026-11-16T17:00:00Z", core_file=core, core_sha=csha, func="count_places", allow_file=allow)
assert json.load(open(out)) == obj and list(obj) == ["places"]
assert [(r["id"], r["fill_checked_signals"]) for r in obj["places"]] == [("WH-NC15-SILVER", 7), ("WH-NC15-COPPER", 0), ("WH-NC15-WTI", 12), ("WH-NC15-HYPE", 61), ("WH-NC15-BNB", 3), ("WH-NC15-USDCAD", 1), ("WH-NC15-NATGAS", 25)]          # HYPE above the target is not capped
assert all(set(r) == {"id", "fill_checked_signals", "target", "start_utc", "as_of_utc"} and r["target"] == 60 and r["start_utc"] == "2026-11-13T02:40:00Z" and r["as_of_utc"] == "2026-11-16T17:00:00Z" for r in obj["places"])
text = open(out).read(); assert "KX" not in text and "EUR" not in text and "windows" not in text and "cell" not in text          # no ticker, no other series, no other counter in the file
# the core was called with the folder and the start time, once
assert open(core + '.calls').read() == repr(("ROOT", 1794537600)) + '\n'
# bad counters refuse and leave the previous file whole
good = open(out).read()
def stub_counts(**over):
    base = {s: collections.Counter({"fill-checked": 1}) for _, s in N.PLACES}; base.update(over); return base
for bad, msg in ((stub_counts(KXWTI15M=collections.Counter({"fill-checked": -1})), "non-negative"), (stub_counts(KXWTI15M=collections.Counter({"fill-checked": 2.5})), "non-negative"), (stub_counts(KXWTI15M=collections.Counter({"fill-checked": "7"})), "non-negative"), (stub_counts(KXWTI15M=collections.Counter({"fill-checked": True})), "non-negative"), (stub_counts(KXWTI15M=collections.Counter({"windows": 5})), "non-negative")):
    try: N.build(bad, "2026-11-16T17:00:00Z"); raise AssertionError("must refuse")
    except SystemExit as e: assert msg in str(e), str(e)
missing = stub_counts(); del missing["KXWTI15M"]
try: N.build(missing, "2026-11-16T17:00:00Z"); raise AssertionError("must refuse")
except SystemExit as e: assert "no KXWTI15M" in str(e)
for bad in ("2026-11-16 17:00:00", "2026-11-16T17:00:00", "", None, "2026-11-16T17:00Z"):
    try: N.build(stub_counts(), bad); raise AssertionError("must refuse")
    except SystemExit as e: assert "as_of must be" in str(e)
assert open(out).read() == good
# the function must exist in the core
try: N.load_core(core, csha, "nothing_here"); raise AssertionError("must refuse")
except SystemExit as e: assert "has no nothing_here" in str(e)
try: N.load_core(os.path.join(d, "none.py"), csha, "count_places"); raise AssertionError("must refuse")
except SystemExit as e: assert "cannot be read" in str(e)
# atomic write: the temp name is not left behind
assert not os.path.exists(out + ".tmp")
print("nc15 place counts tests passed")
