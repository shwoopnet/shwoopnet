"""Boundary fixture (made-up quotes, no Kalshi data): two builds on the same folders, buckets compared per event."""
import calendar, gzip, json, os, sys, tempfile, time, importlib.util
MINE, THEIRS = sys.argv[1], sys.argv[2]
def load(name, d):
    sys.path.insert(0, d)
    for m in ("scorekit", "tie3", "esoctie"): sys.modules.pop(m, None)
    spec = importlib.util.spec_from_file_location(name, os.path.join(d, "esoctie.py")); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    sys.path.remove(d); return mod
def folder(bodies):
    d = tempfile.mkdtemp(); rows = []
    for i, b in enumerate(bodies, 1):
        fn = "%04d.json.gz" % i; gzip.open(os.path.join(d, fn), "wt").write(json.dumps(b)); rows.append({"id": "r%d" % i, "status": 200, "file": fn})
    json.dump({"rows": rows}, open(os.path.join(d, "manifest.json"), "w")); return d
E = load("mine", MINE)
def key(ts):
    t = time.gmtime(ts); off = E.us_eastern_offset(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min); l = time.gmtime(ts - off)
    return "%02d%s%02d%02d%02d" % (l.tm_year % 100, ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"][l.tm_mon-1], l.tm_mday, l.tm_hour, l.tm_min)
iso = lambda ts: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
pairs = [(0.43,0.47),(0.42,0.48),(0.41,0.49),(0.61,0.69),(0.60,0.70),(0.44,0.46),(0.64,0.66),(0.54,0.56),(0.74,0.76)]
mk, cd = [], []; S0 = calendar.timegm((2026, 9, 14, 12, 0, 0)); names = {}
for i, (b, a) in enumerate(pairs):
    S = S0 + i * 1200; ev = "KXESOCCERGAME-%sB%04d" % (key(S), i); names[ev] = (b, a)
    for suf in ("TIE", "AAA", "BBB"):
        mk.append({"ticker": "%s-%s" % (ev, suf), "event_ticker": ev, "close_time": iso(S + 720), "open_time": iso(S - 3600), "result": "no"})
    for suf, (bb, aa) in (("TIE", (.25, .27)), ("AAA", (b, a)), ("BBB", (round(1 - a - .2, 2), round(1 - b - .2, 2)))):
        cd.append({"market_ticker": "%s-%s" % (ev, suf), "candlesticks": [{"end_period_ts": S - 60, "yes_bid": {"close_dollars": "%.2f" % bb}, "yes_ask": {"close_dollars": "%.2f" % aa}}]})
L = folder([{"markets": mk}]); C = folder([{"markets": cd}])
_, rows_m = E.measure([L], [C])
T = load("theirs", THEIRS)
spec = T.load_cells(); rt = T.measure(spec, [L], [C])
rows_t = None
for x in (rt if isinstance(rt, (list, tuple)) else [rt]):
    if isinstance(x, list) and x and isinstance(x[0], dict) and "bk" in x[0]: rows_t = x
if rows_t is None and isinstance(rt, tuple):
    for x in rt:
        if isinstance(x, dict):
            for v in x.values():
                if isinstance(v, list) and v and isinstance(v[0], dict) and "bk" in v[0]: rows_t = v
bm = {r["event"]: r["k"] for r in rows_m}; bt = {r["event"]: r["bk"] for r in (rows_t or [])}
diff = 0
for ev, (b, a) in names.items():
    s = "same" if bm.get(ev) == bt.get(ev) else "DIFFERENT"; diff += s != "same"
    print("%.2f/%.2f mid %r  mine %s  theirs %s  %s" % (b, a, (b + a) / 2, bm.get(ev), bt.get(ev), s))
print("edges", E.EDGES, "differences", diff)
