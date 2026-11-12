"""Synthetic leak test for Desk B's REMATCH stage 1 scripts (Forensics, 2026-11-12). No real data: made-up e-soccer lists and candles
written as a pull run folder, then Desk B's own build_stage1_job.py and stage1_measure.py are run on them as they would be run.
usage: python3 -I leak_rematch_stage1.py <path to workers/rematch>
"""
import sys, os, json, gzip, random, subprocess, tempfile
from datetime import datetime, timezone
R = os.path.abspath(sys.argv[1]); sys.path.insert(0, R)
import common as C
res = []
def check(name, ok, detail=""):
    res.append(ok); print("%-112s %s %s" % (name, "PASS" if ok else "FAIL", detail))
T0 = C.ts("2026-10-16T12:00:00Z")
iso = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def key(S): return datetime.fromtimestamp(S, C.ET).strftime("%y%b%d%H%M").upper()

def build(root, flip_b=False, flip_a=False, after_px=None, a_close_late=None, drop_ref=False, drop_entry=False, heldout=False, seed=5, n_pairs=120):
    """n_pairs pairs of players; each pair meets twice, B 40 minutes after A. Returns (lists run, candles run)."""
    rng = random.Random(seed); mk, cd = [], {}
    for i in range(n_pairs):
        p1, p2 = "P%03dA" % i, "P%03dB" % i
        SA = T0 + 600 * i; SB = SA + 2400
        if heldout: SA += 8 * 86400; SB += 8 * 86400
        a_win = p1 if rng.random() < 0.5 else p2
        lose0 = p2 if a_win == p1 else p1          # the candles are planted on the UNFLIPPED loser, so flipping A's result leaves every candle as it was
        if flip_a: a_win = p2 if a_win == p1 else p1
        b_win = p1 if rng.random() < 0.5 else p2
        if flip_b: b_win = p2 if b_win == p1 else p1
        fell = rng.random() < 0.4
        for S, win, tag in ((SA, a_win, "A"), (SB, b_win, "B")):
            ev = "%s-%s%s%s" % (C.SERIES, key(S), p1, p2)
            close = S + 780 + (a_close_late or 0 if tag == "A" else 0)
            for c in (p1, p2, "TIE"):
                mk.append({"ticker": ev + "-" + c, "event_ticker": ev, "close_time": iso(close), "open_time": iso(SA - 7200), "result": "yes" if c == win else "no"})
            if tag == "B":
                lose = lose0
                for c in (p1, p2):
                    cs = []
                    for t in range(SA - 240, SB - 179, 60):
                        mid = 0.50
                        if c == lose and fell and t > SA + 600: mid = 0.42
                        if drop_ref and t == SA - C.BEFORE_S: continue
                        if drop_entry and t == SB - C.ENTRY_S: continue
                        cs.append({"end_period_ts": t, "yes_bid": {"close_dollars": "%.4f" % (mid - 0.01)}, "yes_ask": {"close_dollars": "%.4f" % (mid + 0.01)}})
                    if after_px is not None:
                        for t in range(SB - 240, SB + 900, 60):          # everything AFTER the entry candle (S_B minus 5 minutes)
                            px = after_px if c == b_win else 1 - after_px
                            cs.append({"end_period_ts": t, "yes_bid": {"close_dollars": "%.4f" % max(0.01, px - 0.01)}, "yes_ask": {"close_dollars": "%.4f" % min(0.99, px + 0.01)}})
                    cd[ev + "-" + c] = cs
    L = os.path.join(root, "lists"); K = os.path.join(root, "candles"); os.makedirs(L); os.makedirs(K)
    gzip.open(os.path.join(L, "0001.json.gz"), "wt").write(json.dumps({"markets": mk}))
    json.dump({"rows": [{"id": "l1", "status": 200, "file": "0001.json.gz", "params": {"series_ticker": C.SERIES}}]}, open(os.path.join(L, "manifest.json"), "w"))
    gzip.open(os.path.join(K, "0001.json.gz"), "wt").write(json.dumps({"markets": [{"market_ticker": t, "candlesticks": c} for t, c in cd.items()]}))
    json.dump({"rows": [{"id": "c1", "status": 200, "file": "0001.json.gz"}]}, open(os.path.join(K, "manifest.json"), "w"))
    return L, K

def run(**kw):
    root = tempfile.mkdtemp(prefix="rm_"); L, K = build(root, **kw); out = os.path.join(root, "out")
    b = subprocess.run([sys.executable, "-I", os.path.join(R, "build_stage1_job.py"), L, out], capture_output=True, text=True)
    if not os.path.exists(os.path.join(out, "pairs.json")): return {"build": b.stdout + b.stderr, "measure": "", "rc": b.returncode, "job": None}
    m = subprocess.run([sys.executable, "-I", os.path.join(R, "stage1_measure.py"), L, K, os.path.join(out, "pairs.json")], capture_output=True, text=True)
    return {"build": b.stdout, "measure": m.stdout + m.stderr, "rc": m.returncode, "job": json.load(open(os.path.join(out, "REMATCH_STAGE1_CANDLES.json"))), "pairs": json.load(open(os.path.join(out, "pairs.json")))}

def counts(text):
    return [l for l in text.splitlines() if ":" in l and not l.startswith("diagnostic")]

base = run()
state = [l for l in base["measure"].splitlines() if l.startswith("STATE")]
check("sanity: the scripts run on the made-up folder and find the planted falls", base["rc"] == 0 and state and int(state[0].rsplit(":", 1)[1]) > 20, state[0] if state else base["measure"][-200:])
check("the LATER match's result flipped everywhere -> every printed count and the cost line are identical", counts(run(flip_b=True)["measure"]) == counts(base["measure"]))
check("candles AFTER the entry candle changed (the later match's price run to 0.97 or 0.03) -> identical counts and cost", counts(run(after_px=0.97)["measure"]) == counts(base["measure"]))
check("CONTROL: the EARLIER match's result flipped -> the STATE count changes (the test bites; that result is the registered state)", counts(run(flip_a=True)["measure"]) != counts(base["measure"]))
late = run(a_close_late=1300)      # A now closes 2,080 s after its start: close + 300 s is after B's decision minute (S_B - 360 s = S_A + 2,040 s)
lc = [l for l in late["measure"].splitlines() if l.startswith("earlier match closed")]
check("an earlier match whose close plus 300 s is after the decision minute never sets the state", bool(lc) and int(lc[0].rsplit(":", 1)[1]) == 0, lc[0] if lc else "")
ho = run(heldout=True)
check("lists holding a market closing on or after the held-out date: the builder writes no job or the reader refuses", ho["job"] is None or ho["rc"] != 0 or "REFUSED" in ho["measure"], (ho["build"] + ho["measure"])[-90:].replace("\n", " "))
j = base["job"]
ends = max(r["params"]["end_ts"] for r in j["requests"]); last_entry = max(p["S_B"] for p in base["pairs"]) - C.ENTRY_S
over = sum(1 for r in j["requests"] for p in base["pairs"] if p["tickers"][0] in r["params"]["market_tickers"] and r["params"]["end_ts"] > p["S_B"] + 600)
check("NOTE (not a leak in the reader): how many pairs sit in a request whose time range runs past their own match's start plus 10 minutes", True, "%d of %d pairs: the landed candle file shows those matches' prices during play" % (over, len(base["pairs"])))
miss = run(drop_ref=True)
ms = [l for l in miss["measure"].splitlines() if l.startswith("loser's contract two-sided")]
check("NOTE: with the candle at the reference minute MISSING for every pair, the count of pairs two-sided there (120 = all carried, 0 = all dropped)", True, ms[0] if ms else "")
# the carried-candle path (Desk B's Amendment 4, quote_at): only ever a candle at or before the instant, at most CARRY_S earlier
if hasattr(C, "quote_at"):
    t = 1_000_000 * 60; X = (0.40, 0.42); cs = getattr(C, "CARRY_S", 300)
    check("quote_at: a candle exactly CARRY_S earlier is carried; one minute older is not; a LATER candle is never used",
          C.quote_at({t - cs: X}, t) == (X, "carried") and C.quote_at({t - cs - 60: X}, t)[0] is None and C.quote_at({t + 60: X}, t)[0] is None and C.quote_at({t + 60: (0.9, 0.92), t - 60: X}, t) == (X, "carried"))
    d0 = run(drop_entry=True); d1 = run(drop_entry=True, after_px=0.97)
    se = [l for l in d0["measure"].splitlines() if l.strip().startswith("entries that pass")]
    check("entry candle MISSING for every pair, and the next candles run to 0.97 or 0.03 -> identical counts and cost (the carry looks back, never forward)", counts(d0["measure"]) == counts(d1["measure"]) and d0["rc"] == 0, se[0].strip() if se else "")
    car = [l for l in d0["measure"].splitlines() if "from an earlier candle" in l]
    check("the reader prints how many instants were exact and how many carried", bool(car), car[0][:150] if car else "no such line")
print("\n%d checks, %d FAIL" % (len(res), sum(1 for x in res if not x)))
