"""CORRECTION run (Desk A, Nov 17 2026, the Head's order): the ENGINE1 scorer drops an M60 or M180 trade when the mark candle is missing or not two sided ('no mark'), which removes total losses on a collapsed cheap side. This wrapper re-runs the held-out evaluators (190, batch B, batch C) UNCHANGED apart from that one case, in three modes, and records per rule call: base (as read), floor (a no-mark trade is sold at 0.01, no haircut below the floor, fee at both ends), hold (a no-mark trade is held to settlement), and the count of no-mark trades by kind (candle absent, not two sided). No rule, window, feature or bar changes. Label every output 'correction'.
  python3 -I engine1_nomark_correction.py <mode base|floor|hold> <which 190|B|C> <args of that evaluator ...>"""
import sys, os, json, collections, runpy
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_core as K, engine1_driver as D
mode, which = sys.argv[1], sys.argv[2]; args = sys.argv[3:]
KINDS = collections.Counter(); CALLS = []
orig = K.score
def patched(e, exit_, h, n):
    r = orig(e, exit_, h, n)
    if r[0] is None and r[1] == "no mark" and exit_ in ("M60", "M180"):
        mark = e["close_ts"] - (180 if exit_ == "M180" else 60); c = [c for c in e["path"] if c[0] == mark]
        KINDS["absent" if not c else "not_two_sided"] += 1
        if mode == "floor":
            paid = min(e["ask"] + h, 0.99); cost = paid * n + K.fee_up_order(paid, n)
            return round(0.01 * n - cost - K.fee_up_order(0.01, n), 9), "floor"
        if mode == "hold": return orig(e, "H", h, n)
    return r
K.score = patched
og = D.score_group
def sg(items, exit_):
    KINDS.clear(); out, p = og(items, exit_)
    CALLS.append({"exit": exit_, "n_items": len(items), "kinds_2c_pass": dict(KINDS), "agg": {str(h): {"n": a["n"], "net": a["net"], "pf": a["pf"], "reasons": a.get("reasons")} for h, a in out.items()}})
    return out, p
D.score_group = sg
out_path = args[-1]; args[-1] = out_path + ".evaluator_out.json"
if which == "190": mod = "engine1_heldout_run"
elif which == "B": mod = "engine1_heldout_run_b"
else: mod = "engine1_heldout_run_c"
sys.argv = [mod + ".py"] + args
m = __import__(mod)
if which == "190": m.main(*args)
else: m.main(args)
json.dump({"label": "correction (no-mark trades), mode " + mode, "mode": mode, "which": which, "calls": CALLS}, open(out_path, "w"))
print("wrote", out_path, len(CALLS), "calls")
