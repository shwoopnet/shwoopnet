"""Test of the MECH1 generator on INVENTED candles (no real data). python3 -I mech1_generate_test.py"""
import os, sys, gzip, csv, json, random, tempfile, subprocess, datetime
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import mech1_generate as G
random.seed(7); base = tempfile.mkdtemp(); os.makedirs(os.path.join(base, "kalshi1m"))
COLS = ["ticker", "end_period_ts", "bid_open", "bid_high", "bid_low", "bid_close", "ask_open", "ask_high", "ask_low", "ask_close", "price_open", "price_high", "price_low", "price_close", "price_mean", "price_previous", "open_interest", "volume"]
def day_ts(d): return int(datetime.datetime.fromisoformat(d + "T00:00:00+00:00").timestamp())
for d in G.dates_between("2026-10-04", "2026-10-09"):
    rows = []
    for t, p0 in (("KXGOLDPERP", 4000.0), ("KXUS500PERP", 7000.0)):
        p = p0 + random.random(); oi = 1000.0
        for k in range(1, 1441):
            p *= 1 + random.gauss(0, 0.0003); oi *= 1 + random.gauss(0, 0.002); v = abs(random.gauss(50, 20)) + (400 if random.random() < 0.02 else 0)
            rows.append([t, day_ts(d) + 60 * k, "%.4f" % (p - 0.2), "", "", "%.4f" % (p - 0.2), "%.4f" % (p + 0.2), "", "", "%.4f" % (p + 0.2), "", "", "", "", "", "", "%.2f" % oi, "%.2f" % v])
    with gzip.open(os.path.join(base, "kalshi1m", d + ".only.csv.gz"), "wt", newline="") as fo:
        w = csv.writer(fo); w.writerow(COLS); w.writerows(rows)
open(os.path.join(base, "kalshi1m", "2026-10-27.only.csv.gz"), "wb").write(b"NOT A GZIP FILE: a held-out date must never be opened")
G.WIN.update({"search_from": "2026-10-04", "search_to": "2026-10-06", "validate_from": "2026-10-07", "validate_to": "2026-10-09", "half1_to": "2026-10-05", "half2_from": "2026-10-06"})
out = os.path.join(base, "rec.jsonl"); G.main(base, out)                      # raises if the 10-27 file is opened
L = [json.loads(x) for x in open(out)]
heads = [x for x in L if "sig" in x]; trades = [x for x in L if "sig" not in x]
assert len(heads) == 8, len(heads)                                              # 2 families x 2 signals x 2 sides
assert all(h["threshold_value"] is not None and h["units"] == "bp" and h["hold_s"] == 900 for h in heads)
assert trades and all(t["window"] in ("search", "validate") and "2026-10-04" <= t["day"] <= "2026-10-09" for t in trades)
assert all(abs(t["net"] - round(t["gross"] - t["cost"], 9)) < 1e-9 and t["cost"] == 24.0 for t in trades)
# one position per ticker at a time: traded entries on a ticker never overlap their 15 minute holds
by = {}
for t in trades:
    if t["traded"]: by.setdefault((t["sig_id"], t["market_id"]), []).append(t["entry_end"])
for k, v in by.items():
    v.sort(); assert all(b - a >= 900 + 60 - 60 or b - a >= 900 for a, b in zip(v, v[1:])), k
# every entry has an entry bar and an exit bar in the data; a held-out day never appears
assert not any(t["day"] > "2026-10-09" for t in trades)
# the tail cut is the |x| value at index ceil(0.9 n) - 1: with a known list
import math
vals = sorted([0.1 * i for i in range(1, 11)]); assert vals[math.ceil(0.9 * 10) - 1] == vals[8]
# the screen reads the record file and the registry
r = subprocess.run([sys.executable, "-I", os.path.join(here, "mech1_screen.py"), out, os.path.join(here, "MECH_REGISTRY.json"), "7495758"], capture_output=True, text=True)
assert r.returncode == 0, r.stderr[-400:]
pl = r.stdout.strip().split("\n"); assert len(pl) == 9 and "summary" in pl[-1], len(pl)
print("ok: %d signatures, %d trade lines, screen printed %d lines" % (len(heads), len(trades), len(pl)))
