#!/usr/bin/env python3
"""End to end check of econlag.py on MADE-UP data (no real market data, no network).
Two worlds: one where the fast market jumps on half the prints and the slow market catches up
half an hour late (the card should be listed), one where nothing jumps (the scan must stop it).
Usage: python3 test_synthetic.py
"""
import gzip
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ECON = os.path.join(HERE, "econlag.py")


def h(*parts):
    return int(hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:8], 16)


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def write_run(folder, answers):
    os.makedirs(folder, exist_ok=True)
    rows = []
    for i, (req, body) in enumerate(answers, 1):
        name = "%04d.json.gz" % i
        json.dump(body, gzip.open(os.path.join(folder, name), "wt"))
        rows.append({"index": i, "id": req["id"], "path": req["path"], "params": req.get("params", {}), "page": 1, "status": 200, "file": name})
    json.dump({"status": "complete", "rows": rows}, open(os.path.join(folder, "manifest.json"), "w"))


def quote(v, half=0.005):
    return {"yes_bid": {"close_dollars": "%.4f" % max(0.0001, v - half)}, "yes_ask": {"close_dollars": "%.4f" % min(1.0, v + half)}}


def factor(day_index):
    return sum(((h("g", k) % 2001) - 1000) / 1000.0 * 0.02 for k in range(day_index + 1))


EPOCH = datetime(2024, 6, 1, tzinfo=timezone.utc)


def daily(ticker, start, end):
    out, d = [], datetime.fromtimestamp(start, timezone.utc).replace(hour=0, minute=0, second=0)
    base = 0.45 + (h("b", ticker) % 10) / 100.0
    while d.timestamp() <= end:
        k = (d - EPOCH).days
        v = min(0.9, max(0.1, base + factor(k) + ((h("n", ticker, k) % 21) - 10) / 4000.0))
        out.append(dict(end_period_ts=int(d.timestamp()) + 86400, **quote(v)))
        d += timedelta(days=1)
    return out


def minute(ticker, start, end, jumps, slow):
    t_print = start + 600
    j = (0.12 if h("s", t_print) % 2 else -0.12) if (jumps and h("j", t_print) % 2 == 0) else 0.0
    fail = h("f", t_print) % 8 == 0                       # one in eight: the slow market goes the other way
    out = []
    for e in range(start - start % 60 + 60, end + 1, 60):
        if not slow:
            v = 0.55 + (j if e > t_print + 30 else 0.0)
        else:
            v = 0.50 + (0.0 if e <= t_print + 1800 else (-0.3 * j if fail else j))
        out.append(dict(end_period_ts=e, **quote(v)))
    return out


def answer(req, jumps, slow=False):
    tk = req["path"].split("/markets/")[1].split("/")[0]
    p = req["params"]
    cs = daily(tk, p["start_ts"], p["end_ts"]) if p["period_interval"] == 1440 else minute(tk, p["start_ts"], p["end_ts"], jumps, slow)
    return {"ticker": tk, "candlesticks": cs}


def world(jumps):
    root = tempfile.mkdtemp()
    out = os.path.join(root, "out")
    cut = datetime(2026, 9, 12, tzinfo=timezone.utc)
    lists = {s: {"live": [], "hist": []} for s in ("KXCPI", "KXPAYROLLS", "KXPCECORE", "KXFEDDECISION")}
    d = datetime(2024, 10, 1, tzinfo=timezone.utc)
    while d < datetime(2026, 11, 1, tzinfo=timezone.utc):
        for s, dom in (("KXCPI", 12), ("KXPAYROLLS", 5), ("KXPCECORE", 27)):
            t = d.replace(day=dom, hour=12, minute=30)
            ev = "%s-%s" % (s, t.strftime("%y%b").upper())
            for k in ("T1", "T2"):
                lists[s]["hist" if t < cut else "live"].append({"ticker": ev + "-" + k, "event_ticker": ev, "open_time": iso(t - timedelta(days=30)), "close_time": iso(t)})
        d = (d.replace(day=1) + timedelta(days=32)).replace(day=1)
    m = datetime(2024, 11, 7, 19, 0, tzinfo=timezone.utc)
    while m < datetime(2026, 11, 1, tzinfo=timezone.utc):
        ev = "KXFEDDECISION-%s" % m.strftime("%y%b%d").upper()
        for k in ("H0", "C25", "C26"):
            lists["KXFEDDECISION"]["hist" if m < cut else "live"].append({"ticker": ev + "-" + k, "event_ticker": ev, "open_time": iso(m - timedelta(days=200)), "close_time": iso(m)})
        m += timedelta(days=45)
    stage1 = []
    for s, v in lists.items():
        stage1.append(({"id": "live_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "limit": 1000}}, {"markets": v["live"], "cursor": ""}))
        stage1.append(({"id": "hist_" + s, "path": "/historical/markets", "params": {"series_ticker": s, "limit": 1000}}, {"markets": v["hist"], "cursor": ""}))
    write_run(os.path.join(root, "s1"), stage1)
    log = []

    def run(*args):
        r = subprocess.run([sys.executable, ECON] + list(args), capture_output=True, text=True)
        log.append(r.stdout.strip() + (("\nERR " + r.stderr.strip()) if r.stderr.strip() else ""))
    run("calendar", os.path.join(root, "s1"), out)
    ja = json.load(open(os.path.join(out, "ECONLAG_A.json")))
    write_run(os.path.join(root, "a"), [(q, answer(q, jumps)) for q in ja["requests"]])
    run("build-b", out, os.path.join(root, "a"))
    jb = json.load(open(os.path.join(out, "ECONLAG_B.json")))
    write_run(os.path.join(root, "b"), [(q, answer(q, jumps)) for q in jb["requests"]])
    run("scan", out, os.path.join(root, "b"))
    import csv
    trigs = list(csv.DictReader(open(os.path.join(out, "triggers.csv"))))
    meets = sorted({(int(r["t_meeting"]), r["event"]) for r in csv.DictReader(open(os.path.join(out, "meetings.csv")))})
    plan, creqs = {}, []
    for tr in trigs:
        later = [ev for t, ev in meets if ev > "" and t > [t2 for t2, e2 in meets if e2 == tr["f_meeting"]][0]]
        if not later:
            continue
        tk = later[0] + "-H0"
        plan[tr["print"]] = [{"label": "S1", "ticker": tk}]
        t = int(tr["t"])
        creqs.append({"id": "c_" + tr["print"], "path": "/historical/markets/%s/candlesticks" % tk, "params": {"start_ts": t - 600, "end_ts": t + 86400 + 600, "period_interval": 1}})
    json.dump(plan, open(os.path.join(out, "plan.json"), "w"))
    write_run(os.path.join(root, "c"), [(q, answer(q, jumps, slow=True)) for q in creqs])
    run("score", out, os.path.join(out, "plan.json"), os.path.join(root, "a"), os.path.join(root, "b"), os.path.join(root, "c"))
    run("score", out, os.path.join(out, "plan.json"), os.path.join(root, "a"), os.path.join(root, "b"), os.path.join(root, "c"))
    return log


if __name__ == "__main__":
    for name, jumps in (("WORLD 1: jumps on half the prints, slow market half an hour late", True), ("WORLD 2: no jumps", False)):
        print("=====", name)
        print("\n".join(world(jumps)))
