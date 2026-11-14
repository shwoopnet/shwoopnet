"""Synthetic dry run of mmmap1_nc15.py: made-up books and trades in a temp dir, 5 s polls, no outcome column at all in the fixture's coverage (proves none is needed).
  python3 -I mmmap1_nc15_dryrun.py"""
import os, sys, gzip, csv, json, random, subprocess, tempfile
rng = random.Random(3); d = tempfile.mkdtemp(); run = os.path.join(d, "2026-11-12", "0000"); os.makedirs(run)
SER = ["KXSILVER15M", "KXEURUSD15M", "KXNATGAS15M"]; base = 1_790_000_100
bk, tr, cv = [], [], []
for si, ser in enumerate(SER):
    for w in range(12):
        close = base + 900 * (w + 1); tk = "KXSILVER15M-26NOV121700-00" if (si, w) == (0, 0) else f"{ser}-W{w}"; iso = lambda t: __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(t))
        mid = rng.uniform(0.3, 0.7); n = 0
        for k in range(0, 180):
            t = close - 900 + 5 * k; mid += rng.uniform(-0.005, 0.005); yb = round(mid - 0.01, 2)
            r = {"t_send_ms": t * 1000 - 50, "t_recv_ms": t * 1000, "server_date_header": "", "ticker": tk, "series": ser, "close_time": iso(close)}
            for L in range(1, 6): r[f"yes_bid_px_{L}"] = round(yb - 0.01 * (L - 1), 2); r[f"yes_bid_sz_{L}"] = rng.randint(5, 60); r[f"no_bid_px_{L}"] = round(1 - yb - 0.02 - 0.01 * (L - 1), 2); r[f"no_bid_sz_{L}"] = rng.randint(5, 60)
            bk.append(r); n += 1
        for k in range(40):
            tt = close - 800 + rng.randint(0, 700); tr.append({"ticker": tk, "created_time": iso(tt) + "", "yes_price_dollars": round(mid + rng.choice([-0.01, 0.01]), 2), "count_fp": rng.choice([1, 2, 5, 10, 2.5]), "taker_outcome_side": rng.choice(["yes", "no"])})
        cv.append({"close_time": iso(close), "series": ser, "ticker": tk, "max_gap_ms": 5000})
for name, rows in (("book", bk), ("trades", tr), ("coverage", cv)):
    with gzip.open(os.path.join(run, name + ".csv.gz"), "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
out = os.path.join(d, "out.json")
r = subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "mmmap1_nc15.py"), d, out], capture_output=True, text=True)
print(r.stdout[-600:], r.stderr[-800:])
res = json.load(open(out)); assert set(k for k in res if k.startswith("KX")) == set(SER), list(res)
assert "result" not in json.dumps(res).lower().replace("resampling", ""), "an outcome field leaked into the output"
assert res["excluded_windows_dropped_here"] == 1 and res["excluded_windows_in_list"] == 28, (res["excluded_windows_dropped_here"], res["excluded_windows_in_list"])
assert res["KXSILVER15M"]["windows"] == 11, res["KXSILVER15M"]["windows"]
s = res["KXSILVER15M"]; print("silver trades", s["trades"], "windows", s["windows"], "e_c", s["e_c"], "quoted half spread c", s["quoted_half_spread_c"]); print("DRY RUN OK: no outcome loaded, 3 series, 36 windows")
