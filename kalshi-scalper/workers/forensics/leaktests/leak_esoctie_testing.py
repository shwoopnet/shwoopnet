"""Synthetic leak tests for the TESTING DESK's independent ESOCTIE build (Forensics, 2026-11-12). No real data: made-up events and candles
fed to the scorer's own functions (its two readers, scorekit.markets and scorekit.candles, are replaced by in-memory dicts).
The base-rate minimum is lowered from 300 to 20 in a COPY of the frozen spec so a small synthetic sample exercises the walk-forward path; nothing else is changed.
usage: python3 -I leak_esoctie_testing.py <path to workers/testing>
"""
import sys, random, copy
from datetime import datetime
sys.path.insert(0, sys.argv[1])
import esoctie as E
res = []
def check(name, ok, detail=""):
    res.append(ok); print("%-118s %s %s" % (name, "PASS" if ok else "FAIL", detail))
SPEC = copy.deepcopy(E.load_cells()); SPEC["base_rate_minimum_earlier_events"] = 20
DEV_FROM, DEV_TO = E.ts_of(SPEC["blocks"]["development_closes_from"]), E.ts_of(SPEC["blocks"]["development_closes_before"])
GAP = SPEC["settle_gap_seconds"]
T0 = DEV_FROM + 86400
def key(i, S): return "KXESOCCERGAME-" + datetime.fromtimestamp(S, E.NY).strftime("%y%b%d%H%M").upper() + "E%04d" % i
def build(n=400, flip=lambda i, ev: False, close_shift=None, after_px=None, void=None, open_back=1800, seed=3, p_yes=0.40):
    """-> (markets dict in scorekit.markets shape, candles dict in scorekit.candles shape). A game every 4 minutes, each closing 920 s after its start."""
    rng = random.Random(seed); mk, cd = {}, {}
    for i in range(n):
        S = T0 + 240 * i; close = S + 920 + (close_shift.get(i, 0) if close_shift else 0)
        e = key(i, S); tie = e + "-TIE"; teams = [e + "-AAA", e + "-BBB"]
        f = rng.choice([0.50, 0.60, 0.70]); tie_mid = 0.20 + 0.05 * rng.random()
        r = "yes" if rng.random() < p_yes else "no"
        if flip(i, dict(S=S, close=close)): r = "no" if r == "yes" else "yes"
        if void is not None and i in void: r = ""
        for t in [tie] + teams: mk[t] = {"ticker": t, "event": e, "series": "KXESOCCERGAME", "open": S - open_back, "close": close, "result": r if t == tie else "no"}
        c = lambda mid, ts: {"ts": ts, "bid": round(mid - 0.01, 4), "ask": round(mid + 0.01, 4)}
        pre = range(S - 660, S - 59, 60)
        cd[tie] = [c(tie_mid, ts) for ts in pre] + ([c(after_px, ts) for ts in range(S, S + 600, 60)] if after_px else [])
        cd[teams[0]] = [c(f, ts) for ts in pre]; cd[teams[1]] = [c(1 - f - tie_mid + 0.2, ts) for ts in pre]
    return mk, cd
def run(mk, cd):
    E.k.markets = lambda folders: mk; E.k.candles = lambda folders: cd
    evs, c = E.events(SPEC, ["x"]); idx = {t: {x["ts"]: x for x in v} for t, v in cd.items()}
    rows, nf = E.walk(SPEC, evs, idx); return evs, c, rows
sig = lambda rows: {r["event"]: (r["ts"], r["bk"], r["n_base"], r["b"], r["ask"]) for r in rows}
mk, cd = build(); evs, c0, rows = run(mk, cd); base = sig(rows)
check("build sanity: every synthetic event kept, one row per event", c0["kept"] == 400 and len(rows) == 400 and len({r["event"] for r in rows}) == 400, str(c0))
target = next(r for r in rows[300:] if r["b"] is not None and any(o["bk"] == r["bk"] and r["ts"] < o["close"] < r["S"] for o in rows))
tS, tts, te = target["S"], target["ts"], target["event"]
def again(**kw): return sig(run(*build(**kw))[2])
r1 = again(flip=lambda i, ev: ev["close"] >= tS)
check("results of events closing at or after a bet's start flipped (its own included) -> that bet's base rate unchanged", r1[te] == base[te], "base n %d" % target["n_base"])
r2 = again(flip=lambda i, ev: tts < ev["close"] < tS)
check("results of events closing AFTER the decision minute but before the start flipped -> base rate unchanged", r2[te] == base[te])
r3 = again(flip=lambda i, ev: tts - GAP < ev["close"] <= tts)
check("results of games that closed before the decision minute but inside the %d s settlement allowance flipped -> unchanged" % GAP, r3[te] == base[te])
r4 = again(flip=lambda i, ev: ev["close"] + GAP <= tts)
check("CONTROL: results of games settled before the decision flipped -> the base rate MOVES (the test bites)", r4[te][3] != base[te][3] and r4[te][2] == base[te][2], "b %.4f -> %.4f" % (base[te][3], r4[te][3]))
allb = lambda s: {e: v for e, v in s.items()}
r5 = again(flip=lambda i, ev: ev["close"] >= tS)
check("same flip: every bet decided before the target is identical too (no later result reaches any earlier decision)", all(r5[r["event"]] == base[r["event"]] for r in rows if r["ts"] <= tts))
ti = next(i for i in range(400) if key(i, T0 + 240 * i) == te)
_, c6, rows6 = run(*build(close_shift={ti: 1500}))
check("ONE event's close moved 25 minutes later (a time after the bet) -> it is still in the universe with the same decision", c6["kept"] == 400 and sig(rows6)[te] == base[te])
_, c7, _ = run(*build(open_back=300))
check("the Tie's OPEN time decides the universe: opened 5 minutes before S -> every event refused", c7["kept"] == 0 and c7["start_not_derivable"] == 400)
check("Tie candles AFTER the pre-match minute changed -> same rows", again(after_px=0.60) == base)
E.k.markets = lambda folders: mk; E.k.candles = lambda folders: cd
out = E.score(SPEC, ["x"], ["y"]); rule = out["rule"]
fired = [r for r in rows if r["b"] is not None and r["gap"] >= SPEC["gap_line"] - 1e-9 and r["spread"] <= SPEC["spread_line"] + 1e-9]
ok_rule = isinstance(rule, dict) and rule.get("bets") == len(fired) and len(fired) > 30
check("the rule scores exactly the rows that fired, one bet an event", ok_rule, "bets %s, fired rows %d" % (rule.get("bets") if isinstance(rule, dict) else rule, len(fired)))
if ok_rule:
    mp = sum(r["ask"] + 0.01 for r in fired) / len(fired)
    net = sum((1 - (r["ask"] + 0.01) - E.fee_up(round(r["ask"] + 0.01, 4))) if r["result"] == "yes" else (-(r["ask"] + 0.01) - E.fee_up(round(r["ask"] + 0.01, 4))) for r in fired)
    check("price paid = the Tie's ASK plus 1c (not a mid), fee rounded up to the cent, net booked to match", abs(rule["mean_price_paid"] - round(mp, 4)) < 1e-4 and E.fee_up(0.25) == 0.02 and abs(rule["all"]["net"] - net) < 0.011, "mean price %.4f, net %.2f vs %.2f" % (rule["mean_price_paid"], rule["all"]["net"], net))
    fi = next(i for i in range(400) if key(i, T0 + 240 * i) == fired[-1]["event"])
    mkv, cdv = build(void={fi}); E.k.markets = lambda folders: mkv; E.k.candles = lambda folders: cdv
    rv = E.score(SPEC, ["x"], ["y"])["rule"]
    check("a fired bet whose Tie has no yes or no result is still COUNTED (booked as a fee-only loss), not dropped", rv["bets"] == len(fired) and rv["void_bets_booked_as_fee_loss"] == 1, "bets %d, void %d" % (rv["bets"], rv["void_bets_booked_as_fee_loss"]))
    check("the verdict line carries 'selected on development'", "selected on development" in rule["registered_verdict"])
    days = len({datetime.utcfromtimestamp(r["S"]).strftime("%Y-%m-%d") for r in fired})
    check("z is computed over UTC-day clusters, not over bets (clusters = distinct days of the fired bets)", rule["cluster_z"]["clusters"] == days and days < len(fired), "%d bets in %d day clusters" % (len(fired), days))
mkh, cdh = build()
for m in mkh.values(): m["close"] = DEV_TO + 600
_, ch, _ = run(mkh, cdh)
check("an event closing at or after the held-out date is refused", ch["kept"] == 0 and ch["held_out_refused"] == 400)
print("\n%d checks, %d FAIL" % (len(res), sum(1 for x in res if not x)))
