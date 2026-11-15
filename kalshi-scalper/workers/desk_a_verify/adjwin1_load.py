"""ADJWIN1 loader (Desk A, Nov 15 2026), written to Auditor B's ruling. Offline; reads only the NC15 runs named below, only through the order below.
REFUSES unless HELDOUT_PULL_RUNS.md carries the named allow-list line for this loader AND that line names this file's own sha256 (no flag, no env var). Opens no other run.
Order (1) lists: ticker and close_time ONLY; rows at or after the cut are dropped and counted before any other key is touched. (2) lists: `result` only for kept rows. (3) candles: market_ticker first; a market not on the kept list is never parsed further; for kept ones end_period_ts and the yes_bid and yes_ask close_dollars only; candles ending after the market's close dropped and counted.
  python3 -I adjwin1_load.py <dir holding the pull run folders, e.g. .../pull>   prints the drop counts and per-series window counts."""
import os, sys, json, gzip, hashlib, collections, calendar, time
HERE = os.path.dirname(os.path.abspath(__file__))
CUT = 1791043200                                  # 2026-10-03T16:00Z
SERIES = ("KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M", "KXAUDUSD15M", "KXUSDCAD15M", "KXNATGAS15M")
LISTS = ("NC15_LISTS_A/2026-11-14T0639Z_43567362760", "NC15_LISTS_B/2026-11-14T0710Z_43569819335")
CANDLES = ("NC15_CANDLES_A1/2026-11-14T0742Z_43572344399", "NC15_CANDLES_A2/2026-11-14T0822Z_43575507647", "NC15_CANDLES_A3/2026-11-14T0902Z_43578620866", "NC15_CANDLES_B1/2026-11-14T0940Z_43581645588", "NC15_CANDLES_B2/2026-11-14T1020Z_43584771195", "NC15_CANDLES_B3/2026-11-14T1101Z_43588018609", "NC15_CANDLES_B4/2026-11-14T1141Z_43591230490")
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by Desk A's ADJWIN1 loader"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def refuse_unless_allowed():
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    line = [l for l in text.splitlines() if ALLOW_MARK in l]
    if not line or "adjwin1_load.py" not in line[0] or self_sha() not in line[0]:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md has no allow-list line naming adjwin1_load.py with this file's sha256 %s (the Head's written acceptance, merged by Main)" % self_sha())
    for r in LISTS + CANDLES:
        if r not in line[0]: raise SystemExit("REFUSED: the allow-list line does not name run %s" % r)
def run_bodies(base, run):
    folder = os.path.join(base, *run.split("/"))
    try: man = json.load(open(os.path.join(folder, "manifest.json")))
    except Exception as e: raise SystemExit("REFUSED: %s has no readable manifest.json (%s)" % (run, e))
    if man.get("status") != "complete" or not isinstance(man.get("rows"), list) or not man["rows"]: raise SystemExit("REFUSED: %s is not a complete run" % run)
    ids = collections.defaultdict(list)
    for r in man["rows"]: ids[r.get("id")].append(r)
    for rid, rs in ids.items():
        if not any(r.get("status") == 200 for r in rs) or any(r.get("status") not in (200, 429) for r in rs): raise SystemExit("REFUSED: request %r of %s was not answered 200" % (rid, run))
    for r in man["rows"]:
        if r.get("status") == 200 and "file" in r: yield json.load(gzip.open(os.path.join(folder, r["file"])))
def iso(s):
    try: return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception: return None
def load(base):
    refuse_unless_allowed()
    c = collections.Counter(); kept = {}
    for run in LISTS:                                                       # (1) ticker and close_time only
        for b in run_bodies(base, run):
            for m in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk, ct = m["ticker"], m["close_time"]
                s = tk.split("-")[0] if isinstance(tk, str) else None
                cl = iso(ct) if isinstance(ct, str) else None
                if s not in SERIES or cl is None: c["unknown series or no close"] += 1; continue
                if cl >= CUT: c["dropped by the cut"] += 1; continue
                kept[tk] = [s, cl, m]                                       # the market object is held but its other keys are read only in step (2)
    res = {}
    for tk, v in kept.items():                                              # (2) result for kept rows only
        r = v[2]["result"] if "result" in v[2] else None
        if r in ("yes", "no"): res[tk] = r
        else: c["no result (dropped)"] += 1
    cand = collections.defaultdict(dict)
    for run in CANDLES:                                                     # (3) candles for kept markets only
        for b in run_bodies(base, run):
            for mk in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk = mk["market_ticker"]
                if tk not in res: c["candle market not kept (not parsed)"] += 1; continue
                cl = kept[tk][1]
                for k in mk["candlesticks"]:
                    try: e = int(k["end_period_ts"]); bid = float(k["yes_bid"]["close_dollars"]); ask = float(k["yes_ask"]["close_dollars"])
                    except (KeyError, TypeError, ValueError): c["candle unreadable"] += 1; continue
                    if e > cl: c["candle after close (dropped)"] += 1; continue
                    if e in cand[tk] and cand[tk][e] != (bid, ask): c["duplicate candle differs (first kept)"] += 1
                    cand[tk].setdefault(e, (bid, ask))
    out = collections.defaultdict(list)
    for tk, r in res.items():
        s, cl, _ = kept[tk]
        out[s].append({"series": s, "close": cl, "result": r, "candles": sorted((e, b, a) for e, (b, a) in cand[tk].items())})
    return dict(out), dict(c)
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    w, c = load(sys.argv[1]); print(json.dumps({"dropped": c, "windows": {s: len(v) for s, v in w.items()}, "loader_sha256": self_sha()}, indent=1))
