"""Synthetic leak tests for the History Miner's ESOCTIE scorer (Forensics, 2026-11-12). No real data: made-up events and candles fed to the scorer's own functions.
usage: python3 -I leak_esoctie.py <path to history_miner/esoctie>
"""
import sys, os, random, copy
sys.path.insert(0, sys.argv[1])
import esoctie as E
res = []
def check(name, ok, detail=""):
    res.append(ok); print("%-104s %s %s" % (name, "PASS" if ok else "FAIL", detail))
E.MIN_BASE = 20
T0 = E.DEV_FROM + 86400
def build(n=400, flip=lambda i, ev: False, close_shift=None, after_px=None, seed=3):
    rng = random.Random(seed); evs, cd = {}, {}
    for i in range(n):
        S = T0 + 240 * i                     # a game every 4 minutes, each closing about 15 minutes after its start: closes overlap later games' decision minutes
        close = S + 920 + (close_shift.get(i, 0) if close_shift else 0)   # ends 40 s before a later game starts: after that game's decision minute
        e = "KXESOCCERGAME-E%04d" % i; tie = e + "-TIE"; teams = [e + "-AAA", e + "-BBB"]
        f = rng.choice([0.50, 0.60, 0.70]); tie_mid = 0.20 + 0.05 * rng.random()
        r = "yes" if rng.random() < 0.3 else "no"
        if flip(i, dict(S=S, close=close)): r = "no" if r == "yes" else "yes"
        evs[e] = {"event": e, "S": S, "close": close, "tie": tie, "teams": teams, "tie_result": r}
        mk = lambda mid, ts: {"ts": ts, "bid": round(mid - 0.01, 4), "ask": round(mid + 0.01, 4)}
        pre = range(S - 660, S - 59, 60)
        cd[tie] = [mk(tie_mid, ts) for ts in pre] + ([mk(after_px, ts) for ts in range(S, S + 600, 60)] if after_px else [])
        cd[teams[0]] = [mk(f, ts) for ts in pre]; cd[teams[1]] = [mk(1 - f - tie_mid + 0.2, ts) for ts in pre]
    return evs, cd
sig = lambda rows: {r["event"]: (r["ts"], r["k"], r["n_base"], r["b"], r["ask"]) for r in rows}
evs, cd = build(); rows, nf = E.walk(evs, cd); base = sig(rows)
byev = {r["event"]: r for r in rows}
target = next(r for r in rows[300:] if any(o["k"] == r["k"] and r["ts"] < o["close"] < r["S"] for o in rows))     # a bet with an earlier game in ITS bucket closing between its decision minute and its start
tS, tts = target["S"], target["ts"]
# 1. results of events that closed AFTER the target's scheduled start
e1, c1 = build(flip=lambda i, ev: ev["close"] >= tS); r1 = sig(E.walk(e1, c1)[0])
check("ESOCTIE: results of events closing at or after a bet's start flipped -> that bet's base rate unchanged", r1[target["event"]] == base[target["event"]], "base n %d" % target["n_base"])
# 2. results of events that closed after the target's DECISION minute but before its start
late = [o for o in rows if o["k"] == target["k"] and tts < o["close"] < tS]
e2, c2 = build(flip=lambda i, ev: tts < ev["close"] < tS); r2 = sig(E.walk(e2, c2)[0])
check("ESOCTIE: results of events closing AFTER the decision minute (but before the start) flipped -> base rate unchanged", r2[target["event"]] == base[target["event"]],
      "%d such event(s) in its bucket; decision at S-%d s; b %.4f -> %.4f" % (len(late), tS - tts, base[target["event"]][3], r2[target["event"]][3]))
# 3. a later value decides the universe: the event's own close time
import calendar
mkts = lambda evs_: {t: {"ticker": t, "event": e["event"], "series": "KXESOCCERGAME", "close": e["close"], "result": e["tie_result"]} for e in evs_.values() for t in [e["tie"]] + e["teams"]}
def key_event(i, S):
    import time; return "KXESOCCERGAME-" + time.strftime("%y%b%d%H%M", time.gmtime(S - E.us_eastern_offset(*time.gmtime(S)[:5]))).upper() + "X%d" % i
def listed(shift):
    out = {}
    for i in range(3):
        S = T0 + 3600 * i; e = key_event(i, S); close = S + 720 + (shift if i == 1 else 0)
        for suf in ("TIE", "AAA", "BBB"): out[e + "-" + suf] = {"ticker": e + "-" + suf, "event": e, "series": "KXESOCCERGAME", "close": close, "result": "no"}
    return out
k0, d0 = E.events(listed(0)); k1, d1 = E.events(listed(1500))
check("ESOCTIE: ONE event's close moved to 37 minutes after its start (a time after the bet) -> the event is still in the universe", len(k1) == len(k0), "events %d -> %d, 'start not derivable' %d" % (len(k0), len(k1), d1["start not derivable"]))
# 4. candles after the pre-match minute
e4, c4 = build(after_px=0.60); check("ESOCTIE: Tie candles AFTER the pre-match minute changed -> same rows", sig(E.walk(e4, c4)[0]) == base)
# 5. price paid
check("ESOCTIE: the bet pays the Tie's ask close plus 1c, fee rounded up to the cent", abs(round(min(target["ask"] + 0.01, 0.99), 4) - (target["ask"] + 0.01)) < 1e-9 and E.fee_up(0.25) == 0.02 and target["ask"] > target["bid"])
# 6. held-out refusal
ho = listed(0); 
for m in ho.values(): m["close"] = E.DEV_BEFORE + 600
check("ESOCTIE: an event closing at or after the held-out date is refused", len(E.events(ho)[0]) == 0 and E.events(ho)[1]["held-out (refused)"] == 3)
print("\n%d checks, %d FAIL" % (len(res), sum(1 for x in res if not x)))
