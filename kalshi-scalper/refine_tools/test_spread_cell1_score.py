"""Synthetic test for spread_cell1_score.py. Run: python3 -I test_spread_cell1_score.py
Uses only synthetic files in a temp dir; no network, no real candles."""
import os, sys, json, subprocess, tempfile, shutil, calendar, time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "spread_cell1_score.py")
CT = calendar.timegm((2026, 10, 1, 0, 0, 0))


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def build(d, wins, losses, extra=False):
    """Each event: one market, ask 0.10, bid 0.09, candle exactly 48h+1h before close."""
    ev, cand, mk = [], [], []
    n = wins + losses
    for i in range(n):
        e = "KXMLBSPREAD-E%d" % i
        t = e + "-A"
        ev.append(["KXMLBSPREAD", e, CT])
        cand.append({"_e": e, "s": "KXMLBSPREAD", "c": CT,
                     "h": {t: [[CT - 48 * 3600 - 3600, "0.1000", "0.0900", None, "0.00"],
                               [CT - 47 * 3600, "0.9000", "0.8900", None, "0.00"]]}})
        mk.append({"_m": 1, "s": "KXMLBSPREAD", "t": t, "e": e, "ct": iso(CT), "res": "yes" if i < wins else "no"})
    if extra:
        # decoys that must not count: event not in list; stale candle; ask out of bucket
        cand.append({"_e": "KXMLBSPREAD-NOTLISTED", "s": "KXMLBSPREAD", "c": CT,
                     "h": {"X-A": [[CT - 49 * 3600, "0.1000", "0.0900", None, "0"]]}})
        mk.append({"_m": 1, "s": "KXMLBSPREAD", "t": "X-A", "e": "KXMLBSPREAD-NOTLISTED", "ct": iso(CT), "res": "yes"})
        ev.append(["KXMLBSPREAD", "KXMLBSPREAD-STALE", CT])
        cand.append({"_e": "KXMLBSPREAD-STALE", "s": "KXMLBSPREAD", "c": CT,
                     "h": {"S-A": [[CT - 52 * 3600, "0.1000", "0.0900", None, "0"]]}})
        mk.append({"_m": 1, "s": "KXMLBSPREAD", "t": "S-A", "e": "KXMLBSPREAD-STALE", "ct": iso(CT), "res": "yes"})
        ev.append(["KXMLBSPREAD", "KXMLBSPREAD-OUT", CT])
        cand.append({"_e": "KXMLBSPREAD-OUT", "s": "KXMLBSPREAD", "c": CT,
                     "h": {"O-A": [[CT - 49 * 3600, "0.1500", "0.1400", None, "0"]]}})
        mk.append({"_m": 1, "s": "KXMLBSPREAD", "t": "O-A", "e": "KXMLBSPREAD-OUT", "ct": iso(CT), "res": "yes"})
        # nearest-0.5 choice: two markets in one event, the 0.14 ask (mid .135) must be chosen, it loses
        ev.append(["KXMLBSPREAD", "KXMLBSPREAD-TWO", CT])
        cand.append({"_e": "KXMLBSPREAD-TWO", "s": "KXMLBSPREAD", "c": CT,
                     "h": {"T-A": [[CT - 49 * 3600, "0.0600", "0.0500", None, "0"]],
                           "T-B": [[CT - 49 * 3600, "0.1400", "0.1300", None, "0"]]}})
        mk.append({"_m": 1, "s": "KXMLBSPREAD", "t": "T-A", "e": "KXMLBSPREAD-TWO", "ct": iso(CT), "res": "yes"})
        mk.append({"_m": 1, "s": "KXMLBSPREAD", "t": "T-B", "e": "KXMLBSPREAD-TWO", "ct": iso(CT), "res": "no"})
    json.dump({"events": ev}, open(os.path.join(d, "ev.json"), "w"))
    with open(os.path.join(d, "candles.jsonl"), "w") as f:
        for c in cand:
            f.write(json.dumps(c) + "\n")
    with open(os.path.join(d, "markets.jsonl"), "w") as f:
        f.write(json.dumps({"_series": "KXMLBSPREAD", "n": 1}) + "\n")
        for m in mk:
            f.write(json.dumps(m) + "\n")


def run(d, expected=None):
    args = [os.path.join(d, "candles.jsonl"), os.path.join(d, "ev.json"), os.path.join(d, "markets.jsonl")]
    if expected:
        args.append(expected)
    r = subprocess.run([sys.executable, "-I", SCRIPT] + args, capture_output=True, text=True)
    return r.stdout.strip()


def mark(d, v="274"):
    open(os.path.join(d, "SPREADCELL1_PULL_COMPLETE"), "w").write(v + "\n")


def scenario(wins, losses, extra=False):
    d = tempfile.mkdtemp()
    build(d, wins, losses, extra)
    return d


ok = True


def check(name, cond, info=""):
    global ok
    ok &= bool(cond)
    print(("ok   " if cond else "FAIL ") + name + (" | " + info if info and not cond else ""))


# (a) before the marker: only 'pull incomplete'; wrong marker value too
d = scenario(2, 8, extra=True)
check("a1 no marker prints only 'pull incomplete'", run(d) == "pull incomplete", run(d))
mark(d, "273")
check("a2 marker with 273 still 'pull incomplete'", run(d) == "pull incomplete")
check("a3 no READ_DONE written while incomplete", not os.path.exists(os.path.join(d, "SPREADCELL1_READ_DONE")))

# (b) hand calculation. 10 events at p=0.10, 2 win; the decoys add one losing event at p=0.14
# (nearest 0.5 rule, event TWO). Not counted: unlisted, stale, out-of-bucket events.
fee10 = 0.07 * 0.10 * 0.90
fee14 = 0.07 * 0.14 * 0.86
w0 = 1 - 0.10 - fee10
l0 = -0.10 - fee10
l14 = -0.14 - fee14
xs0 = [w0] * 2 + [l0] * 8 + [l14]
pf0 = sum(x for x in xs0 if x > 0) / -sum(x for x in xs0 if x < 0)
xs1 = [x - 0.01 for x in xs0]
pf1 = sum(x for x in xs1 if x > 0) / -sum(x for x in xs1 if x < 0)
m0 = sum(xs0) / 11
mark(d)
out = run(d)
exp_n = "n = 11"
check("b1 n is 11", exp_n in out, out)
check("b2 PF hidden under n 100", "PF" not in out, out)
check("b3 no z or bound under n 100", "z:" not in out and "lower bound" not in out, out)
check("b4 no mean under n 100", "mean" not in out, out)
check("b5 label UNDERPOWERED at n 11", "UNDERPOWERED: no evidence at n = 11" in out, out)
# (c) second run
check("c1 second run prints 'already read'", run(d) == "already read")
check("c2 READ_DONE exists", os.path.exists(os.path.join(d, "SPREADCELL1_READ_DONE")))
shutil.rmtree(d)

# (d) one scenario per label. Win at p=0.10 nets +0.8937-sl, loss -0.1063-sl.
for name, wins, losses, want in [
    ("d1 PASS (80 wins of 400)", 80, 320, "LABEL: PASS"),
    ("d2 FAIL (20 wins of 200, win rate 10%)", 20, 180, "LABEL: FAIL"),
    ("d3 LEAD (30 wins of 150: PF high, z about 2.6)", 30, 120, "LABEL: LEAD"),
    ("d4 UNDERPOWERED (n 50)", 10, 40, "UNDERPOWERED: no evidence at n = 50"),
]:
    d = scenario(wins, losses)
    mark(d)
    out = run(d)
    n = wins + losses
    xs = [(1 if i < wins else 0) - 0.10 - 0.01 - fee10 for i in range(n)]
    pf = sum(x for x in xs if x > 0) / -sum(x for x in xs if x < 0)
    if n < 100:
        check(name, want in out and "PF" not in out and "mean" not in out, out)
    else:
        check(name, want in out and ("n = %d" % n) in out and ("PF %.3f" % pf) in out, out)
    print("     " + out.replace("\n", "\n     "))
    shutil.rmtree(d)

# (e) LINE 2. 300 events, the first 60 win. Per-event expected time chosen by index.
def expected_file(d, n, kind):
    exp = {}
    for i in range(n):
        e = "KXMLBSPREAD-E%d" % i
        k = kind(i)
        if k == "same":
            exp[e] = {"close_time": iso(CT), "expected_expiration_time": iso(CT), "occurrence_datetime": None}
        elif k == "occ":   # expected absent, occurrence used
            exp[e] = {"close_time": iso(CT), "expected_expiration_time": None, "occurrence_datetime": iso(CT)}
        elif k == "later":  # look lands on the 0.90 candle: observed but out of bucket
            exp[e] = {"expected_expiration_time": iso(CT + 3 * 3600), "occurrence_datetime": None}
        elif k == "null":
            exp[e] = {"close_time": iso(CT), "expected_expiration_time": None, "occurrence_datetime": None}
        elif k == "far":    # look before every pulled candle
            exp[e] = {"expected_expiration_time": iso(CT - 10 * 86400), "occurrence_datetime": None}
    p = os.path.join(d, "EXPECTED.json")
    json.dump(exp, open(p, "w"))
    return p


# e1 line 2 differs from line 1; probe eligible yes (line 1 PASS, line 2 n 150 with PF high)
d = scenario(60, 240)
mark(d)
def kind1(i):
    return "same" if i < 100 else "occ" if i < 150 else "later" if i < 200 else "null" if i < 250 else "far"
out = run(d, expected_file(d, 300, kind1))
l1, l2 = out.split("\nLINE 2 (")[0], out.split("\nLINE 2 (")[1]
check("e1 line 1 unchanged (n = 300, PASS)", "n = 300 events in the cell" in l1 and "LABEL: PASS" in l1, out)
check("e2 line 2 differs (n = 150)", "n = 150 events in the cell" in l2, out)
check("e3 missing count 100 (50 null + 50 far)", "Line 2 observation (no time, or look outside the pulled candles): 100" in l2, out)
check("e4 probe-eligible YES", "with n 100 or more: YES" in l2, out)
print("     " + out.replace("\n", "\n     "))
shutil.rmtree(d)

# e5 probe NO: line 2 n under 100 (only the label, no PF), even though line 1 is PASS
d = scenario(60, 240)
mark(d)
out = run(d, expected_file(d, 300, lambda i: "same" if i < 70 else "null"))
l2 = out.split("\nLINE 2 (")[1]
check("e5 line 2 n 70 prints only the label", "n = 70 events" in l2 and "UNDERPOWERED: no evidence at n = 70" in l2 and "PF" not in l2.split("probe-eligible")[0], out)
check("e6 probe-eligible NO when line 2 n under 100", "with n 100 or more: NO" in l2, out)
shutil.rmtree(d)

# e7 probe NO: line 2 n 200 but all losses (PF under 1.3) while line 1 is PASS
d = scenario(60, 240)
mark(d)
out = run(d, expected_file(d, 300, lambda i: "same" if i >= 60 and i < 260 else "null"))
l2 = out.split("\nLINE 2 (")[1]
check("e7 line 2 n 200 and PF below 1.3", "n = 200 events" in l2 and "PF 0.000" in l2, out)
check("e8 probe-eligible NO when line 2 PF under 1.3", "with n 100 or more: NO" in l2, out)
shutil.rmtree(d)

# e9 missing times file: line 2 not available and nothing else for line 2
d = scenario(60, 240)
mark(d)
out = run(d, os.path.join(d, "NOPE.json"))
check("e9 missing file prints 'line 2 not available' only", out.endswith("line 2 not available") and "LINE 2 (" not in out and "probe-eligible" not in out, out)
d2 = scenario(60, 240)
mark(d2)
check("e10 no 4th argument same", run(d2).endswith("line 2 not available"))
shutil.rmtree(d); shutil.rmtree(d2)

print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
