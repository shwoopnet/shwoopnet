"""VOLFAIR1 loader (Desk A, Nov 16 2026), written to Auditor B's four conditions. Offline; reads only the VOLFAIR1 pull runs NAMED ON THE ALLOW LINE, only through the order below.
REFUSES unless HELDOUT_PULL_RUNS.md carries a line with the mark, "volfair1_load.py" and this file's own sha256 (no flag, no env var); the runs it opens are the ones that line names (VOLFAIR1_LISTS/<stamp> and VOLFAIR1_CANDLES_NN/<stamp>), nothing else.
Order: (1) lists: ticker and close_time ONLY; a close outside [DEV_FROM, VAL_TO) is dropped and counted before any other key is touched (closes at or after VAL_TO 1789948800 are EVM1's and HRSEAS1's held thirds, HOLDS H18 and H19, never parsed further); (2) kept markets: floor_strike only (no result yet); (3) candles: market_ticker first, a market not kept is never parsed further; for kept ones only the candle ENDING exactly 55 minutes and exactly 15 minutes before the close is opened (every other candle is discarded by its end_period_ts before any price is read); (4) per close the 7 strikes whose YES mid at the -55 candle is nearest 0.50 (ties to the lower strike) are chosen from that candle alone; (5) `result` is read for the chosen strikes only.
  python3 -I volfair1_load.py <dir holding the pull run folders>   prints the drop counts and the window counts."""
import os, sys, json, gzip, hashlib, collections, calendar, time
HERE = os.path.dirname(os.path.abspath(__file__))
DEV_FROM, DEV_TO, VAL_TO = 1780272000, 1788220800, 1789948800        # 2026-06-01, 2026-09-01, 2026-09-21 (date -u checked); development is labelled development
SERIES = "KXBTCD"; LOOK_SELECT, LOOK_ENTRY, NEAREST = 55 * 60, 15 * 60, 7
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md")
ALLOW_MARK = "readable ONLY by Desk A's VOLFAIR1 loader"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def allowed_runs():
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "volfair1_load.py" in line and self_sha() in line:
            toks = [t.strip(" ,;()") for t in line.replace("\\", "/").split()]
            lists = sorted({t for t in toks if t.startswith("VOLFAIR1_LISTS/")}); cands = sorted({t for t in toks if t.startswith("VOLFAIR1_CANDLES_") and "/" in t})
            if not lists or not cands: raise SystemExit("REFUSED: the allow-list line names no VOLFAIR1_LISTS run or no VOLFAIR1_CANDLES run")
            return lists, cands
    raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md has no allow-list line naming volfair1_load.py with this file's sha256 %s (the Head's written acceptance, merged by Main)" % self_sha())
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
def load(base, runs=None):
    """-> (closes, counts). closes: [{"close": epoch, "window": "development"|"validation", "strikes": [{"strike", "mid55", "bid15", "ask15", "result"}]}] sorted by close. runs = (lists, candles) is for the tests only; the real call reads them from the allow line."""
    lists, cands = runs if runs is not None else allowed_runs()
    c = collections.Counter(); kept = {}
    for run in lists:                                                        # (1) ticker and close_time ONLY
        for b in run_bodies(base, run):
            for m in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk = m.get("ticker"); ct = m.get("close_time")
                cl = iso(ct) if isinstance(ct, str) else None
                if not isinstance(tk, str) or tk.split("-")[0] != SERIES or cl is None: c["unknown series or no close"] += 1; continue
                if cl >= VAL_TO: c["dropped: at or after 2026-09-21 (held thirds H18 and H19)"] += 1; continue
                if cl < DEV_FROM: c["dropped: before 2026-06-01"] += 1; continue
                kept[tk] = [cl, m]                                           # the market object is held; its other keys are read only in steps (2) and (5)
    strike = {}
    for tk, (cl, m) in kept.items():                                         # (2) floor_strike only
        try: strike[tk] = float(m["floor_strike"])
        except (KeyError, TypeError, ValueError): c["no strike (dropped)"] += 1
    want = {}                                                                # ticker -> {end ts: slot} for the two candle ends
    for tk in strike: want[tk] = {kept[tk][0] - LOOK_SELECT: "55", kept[tk][0] - LOOK_ENTRY: "15"}
    got = collections.defaultdict(dict)
    for run in cands:                                                        # (3) market_ticker first; only the two candle ends
        for b in run_bodies(base, run):
            for mk in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk = mk.get("market_ticker")
                if tk not in want: c["candle market not kept (not parsed)"] += 1; continue
                for k in mk.get("candlesticks", []):
                    try: e = int(k["end_period_ts"])
                    except (KeyError, TypeError, ValueError): c["candle unreadable"] += 1; continue
                    slot = want[tk].get(e)
                    if slot is None: c["candle at another time (discarded unread)"] += 1; continue
                    try: bid = float(k["yes_bid"]["close_dollars"]); ask = float(k["yes_ask"]["close_dollars"])
                    except (KeyError, TypeError, ValueError): c["candle unreadable"] += 1; continue
                    if slot in got[tk] and got[tk][slot] != (bid, ask): c["duplicate candle differs (first kept)"] += 1
                    got[tk].setdefault(slot, (bid, ask))
    byclose = collections.defaultdict(list)
    for tk in strike:
        g = got.get(tk, {}); a = g.get("55")
        if a is None or not (0 < a[0] < a[1] < 1): c["no two-sided -55 candle (not a candidate)"] += 1; continue
        byclose[kept[tk][0]].append((round(abs((a[0] + a[1]) / 2 - 0.5), 9), strike[tk], tk, (a[0] + a[1]) / 2))
    out = []
    for cl in sorted(byclose):                                               # (4) the 7 nearest 0.50, ties to the lower strike, from the -55 candle alone
        rows = sorted(byclose[cl])
        if len(rows) < NEAREST: c["close with fewer than 7 strikes quoted at -55 (skipped)"] += 1; continue
        ch = []
        for d, k, tk, mid in rows[:NEAREST]:                                 # (5) result for the chosen only
            r = kept[tk][1].get("result")
            e = got[tk].get("15")
            if r not in ("yes", "no"): c["chosen strike without a result (dropped)"] += 1; continue
            ch.append({"strike": k, "mid55": mid, "bid15": e[0] if e else None, "ask15": e[1] if e else None, "result": r})
        out.append({"close": cl, "window": "development" if cl < DEV_TO else "validation", "strikes": ch})
    return out, dict(c)
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    w, c = load(sys.argv[1]); print(json.dumps({"dropped": c, "closes": collections.Counter(x["window"] for x in w), "loader_sha256": self_sha()}, indent=1))
