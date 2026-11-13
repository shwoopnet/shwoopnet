"""Checks spxfv1b.py against expected_by_hand.json (committed first, 4335655c; re-worked for S1 to S6 before the change) on the invented rows in inv/, plus the refusals. Exit 1 on any mismatch."""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spxfv1b as S
E = json.load(open(os.path.join(HERE, "expected_by_hand.json")))
inv = os.path.join(HERE, "inv")
W, F = os.path.join(inv, "windows.csv"), os.path.join(inv, "futures_ohlcv1m.csv")
bad = []
o = S.run("dev", W, F)
for k, v in E["dev"]["counts"].items():
    if o["counts"].get(k, 0) != v: bad.append(("count", k, o["counts"].get(k), v))
a = o["aggregate"]
if o["counts"].get("asks_tie", 0) != E["dev"]["ties"]: bad.append(("asks_tie", o["counts"].get("asks_tie", 0)))
for k in ("pf", "mean_net", "label"):
    want = E["dev"][k]; got = a[k]
    if (isinstance(want, float) and abs(got - want) > 1e-6) or (not isinstance(want, float) and got != want): bad.append((k, got, want))
if a["n"] != E["dev"]["traded_n"]: bad.append(("n", a["n"]))
# the one traded window, checked through decide() (the output itself carries aggregates only, D8)
import csv
bars = S.load_futures(F)
w = [r for r in csv.DictReader(open(W)) if r["ticker"] == "KXINX15M-A"][0]
st, t = S.decide({"ticker": w["ticker"], "event_ticker": w["event_ticker"], "close_ts": int(w["close_ts"]), "yes_bid": float(w["yes_bid"]), "yes_ask": float(w["yes_ask"]), "result": w["result"]}, bars)
x = E["dev"]["windows_A"]
if st != "traded" or t["side"] != x["side"] or abs(t["ask"] - x["ask"]) > 1e-9 or abs(t["net"] - x["net"]) > 1e-9 or abs(t["net_unrounded"] - x["net_unrounded_info"]) > 1e-9:
    bad.append(("window A", st, t))
def refused(fn, tag):
    try:
        fn()
    except (S.Stop, SystemExit):
        return
    bad.append(("not refused", tag))
refused(lambda: S.run("held", W, F, now=S.iso("2027-02-25T23:59:59Z"), marker=os.path.join(tempfile.mkdtemp(), "M")), "held before READ_DATE")
m = os.path.join(tempfile.mkdtemp(), "M")
o2 = S.run("held", W, F, now=S.iso("2027-02-26T00:00:00Z"), marker=m)
if o2["aggregate"] != {"n": 1, "verdict": "NOT_ENOUGH_DATA (count only)"}: bad.append(("held count only", o2["aggregate"]))
refused(lambda: S.run("held", W, F, now=S.iso("2027-02-26T00:00:00Z"), marker=m), "second held read")
held = os.path.join(tempfile.mkdtemp(), "pull", "POLGAPH_LISTS", "2026-11-13T0627Z_43378777252"); os.makedirs(held)
refused(lambda: S.run("dev", os.path.join(held, "w.csv"), F), "listed run via hm_guard")
o3 = S.run("dev", os.path.join(inv, "windows_heldempty.csv"), F)
for k, v in E["dev_heldempty"]["counts"].items():
    if o3["counts"].get(k, 0) != v: bad.append(("F1 count", k, o3["counts"].get(k), v))
refused(lambda: S.run("dev", W, os.path.join(inv, "futures_mes.csv")), "a non-ES futures row (F2)")
if a["z_event"] is not None: bad.append(("dev z should be none", a["z_event"]))
oz = S.run("dev", os.path.join(inv, "windows_z.csv"), os.path.join(inv, "futures_z.csv"))
az = oz["aggregate"]
if az["n"] != E["z_set"]["traded"] or az["events"] != E["z_set"]["events"] or abs(az["z_event"] - E["z_set"]["z_event"]) > 1e-6:
    bad.append(("z set", az["n"], az["events"], az["z_event"], E["z_set"]))
ot = S.run("dev", os.path.join(inv, "windows_tie.csv"), os.path.join(inv, "futures_z.csv"))
for k, v in E["tie_set"]["counts"].items():
    if ot["counts"].get(k, 0) != v: bad.append(("tie set", k, ot["counts"].get(k), v))
odd = os.path.join(tempfile.mkdtemp(), "w.csv")
open(odd, "w").write(open(W).read().replace(",no\n", ",NO\n", 1))
refused(lambda: S.run("dev", odd, F), "odd result text")
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
