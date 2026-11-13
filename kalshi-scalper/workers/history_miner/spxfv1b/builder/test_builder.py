"""Builds the made-up runs of EXPECTED_BY_HAND.md, runs build_windows.py and compares with the hand file. Prints MISMATCHES [] when all agree."""
import gzip, hashlib, json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_windows as B

C0 = 1793901600
T = ["KXINX15M-26NOV051300-00", "KXINX15M-26NOV051315-15", "KXINX15M-26NOV051330-30", "KXINX15M-26NOV051345-45"]
CL = [C0 + 900 * i for i in range(4)]
ISO = ["2026-11-05T18:%02d:00Z" % (15 * i) for i in range(4)]
RES = ["yes", "no", "void", ""]


def mk(i):
    return {"ticker": T[i], "event_ticker": T[i].rsplit("-", 1)[0], "close_time": ISO[i], "result": RES[i], "status": "settled"}


def cd(end, b, a):
    c = {"end_period_ts": end, "yes_ask": {"close_dollars": "%.4f" % a}}
    c["yes_bid"] = {"close_dollars": "%.4f" % b} if b is not None else {}
    return c


def write_run(folder, requests, answers, status="complete", bad_sha=None):
    os.makedirs(folder)
    rows = []
    for (rid, page), body in answers:
        raw = json.dumps(body).encode()
        fn = "%s_p%d.json.gz" % (rid, page)
        with gzip.open(os.path.join(folder, fn), "wb") as f:
            f.write(raw)
        sha = hashlib.sha256(raw).hexdigest()
        if bad_sha == fn:
            sha = "0" * 64
        rows.append({"id": rid, "page": page, "status": 200, "file": fn, "sha256": sha, "bytes": len(raw)})
    json.dump({"status": status, "job": {"requests": [{"id": r} for r in requests]}, "rows": rows}, open(os.path.join(folder, "manifest.json"), "w"))


def lists(folder, drop_p2=False, status="complete", extra=None):
    p1 = {"markets": [mk(0), mk(1)], "cursor": "abc"}
    p2 = {"markets": [mk(2), mk(3)] + ([extra] if extra else []), "cursor": ""}
    ans = [(("settled_KXINX15M", 1), p1)] + ([] if drop_p2 else [(("settled_KXINX15M", 2), p2)])
    write_run(folder, ["settled_KXINX15M"], ans, status)


def candles(folder, bad_sha=None):
    cs = [[cd(CL[0] - 180, .38, .41), cd(CL[0] - 120, .40, .43)], [cd(CL[1] - 120, None, .55)], [cd(CL[2] - 180, .20, .25)], [cd(CL[3] - 120, .10, .12)]]
    ans = [(("c%03d" % (i + 1), 1), {"markets": [{"market_ticker": T[i], "candlesticks": cs[i]}]}) for i in range(4)]
    write_run(folder, ["c%03d" % (i + 1) for i in range(4)], ans, bad_sha=bad_sha)


bad = []
d = tempfile.mkdtemp()
lists(os.path.join(d, "L")); candles(os.path.join(d, "C"))
out = os.path.join(d, "w.csv")
counts = B.build(os.path.join(d, "L"), os.path.join(d, "C"), out)
exp_csv = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "EXPECTED_BY_HAND.md")).read().split("```\n")[1].split("```")[0]
if open(out).read() != exp_csv:
    bad.append(("csv", open(out).read()))
if counts != {"rows": 4, "quoted": 2, "missing_side": 1, "no_candle": 1}:
    bad.append(("counts", counts))


def refused(fn, what):
    try:
        fn()
    except (B.Stop, SystemExit) as e:
        print("refused", what, "->", e)
        return
    bad.append(("not refused", what))


def case(name, lkw=None, ckw=None, base=None):
    e = tempfile.mkdtemp(dir=base) if base else tempfile.mkdtemp()
    lists(os.path.join(e, "L"), **(lkw or {})); candles(os.path.join(e, "C"), **(ckw or {}))
    return lambda: B.build(os.path.join(e, "L"), os.path.join(e, "C"), os.path.join(e, "w.csv"))


refused(case("partial", {"status": "partial"}), "partial list run")
refused(case("sha", ckw={"bad_sha": "c002_p1.json.gz"}), "candle sha256")
refused(case("p2", {"drop_p2": True}), "missing page 2")
held = dict(mk(3)); held.update({"ticker": "KXINX15M-26DEC021115-15", "event_ticker": "KXINX15M-26DEC021115", "close_time": "2026-12-02T16:15:00Z"})
refused(case("held", {"extra": held}), "held-out market")
hd = os.path.join(tempfile.mkdtemp(), "HELDOUT_x"); os.makedirs(hd)
refused(case("guard", base=hd), "HELDOUT_ path")
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
