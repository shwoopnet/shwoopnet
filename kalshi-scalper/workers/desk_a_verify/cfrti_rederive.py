"""Independent re-derivation of CFRTI1 (development days only) from the protocol TEXT.
Written by Idea Desk A without reading src/scalper/cfrti1.py. Usage: python3 -I cfrti_rederive.py <data_dir>
"""
import sys, os, gzip, csv, glob, calendar, math, json, itertools
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime

DATA = sys.argv[1]
DEV_BEFORE = "2026-11-05"      # development = closes on UTC days before this
ASSET = {"KXBTC15M": "BTC", "KXETH15M": "ETH", "KXSOL15M": "SOL", "KXXRP15M": "XRP", "KXDOGE15M": "DOGE"}

def iso_ms(s):
    s = s.strip().replace("Z", "")
    if "." in s:
        a, b = s.split("."); b = (b + "000000")[:6]
    else:
        a, b = s, "000000"
    return calendar.timegm(datetime.strptime(a, "%Y-%m-%dT%H:%M:%S").timetuple()) * 1000 + int(b) // 1000

# results (close time and outcome); held-out days dropped at load
res = {}
dropped = 0
for path in sorted(glob.glob(os.path.join(DATA, "quotes", "*", "*", "results.csv.gz"))):
    with gzip.open(path, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            ser = r["ticker"].split("-")[0]
            if ser not in ASSET or r["result"] not in ("yes", "no"):
                continue
            if r["close_time"][:10] >= DEV_BEFORE:
                dropped += 1
                continue
            res[r["ticker"]] = (iso_ms(r["close_time"]), r["result"])

# quotes: keep, per ticker, rows within [close-123 s, close-120 s]
cand = defaultdict(list)
for path in sorted(glob.glob(os.path.join(DATA, "quotes", "*", "*", "quotes.csv.gz"))):
    with gzip.open(path, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            t = r["ticker"]
            if t not in res:
                continue
            c = res[t][0]
            tr = int(r["t_recv_ms"])
            if c - 123000 <= tr <= c - 120000:
                cand[t].append((tr, r["yes_bid"], r["yes_ask"], r["strike"], r["status"]))

# spot: per asset, per venue, arrays of (time, price) for both clocks
sp = {"exchange": defaultdict(lambda: defaultdict(list)), "recv": defaultdict(lambda: defaultdict(list))}
for path in sorted(glob.glob(os.path.join(DATA, "quotes", "*", "*", "spot.csv.gz"))):
    with gzip.open(path, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            a = r["asset"]
            try:
                px = float(r["price"]); tr = int(r["t_recv_ms"]); et = r["exchange_time"]
                if "T" in et:
                    te = iso_ms(et)                 # coinbase: ISO
                elif "." in et:
                    te = int(float(et) * 1000)      # kraken: epoch seconds
                else:
                    te = int(et) // 1000            # bitstamp: epoch microseconds
                if abs(te - tr) > 600000:
                    raise ValueError("clock")
            except Exception:
                continue
            sp["recv"][a][r["exchange"]].append((tr, px))
            sp["exchange"][a][r["exchange"]].append((te, px))
for ck in sp:
    for a in sp[ck]:
        for v in sp[ck][a]:
            sp[ck][a][v].sort()
keys = {ck: {a: {v: [x[0] for x in sp[ck][a][v]] for v in sp[ck][a]} for a in sp[ck]} for ck in sp}

def index_at(ck, a, t):
    vals = []
    for v, arr in sp[ck][a].items():
        i = bisect_right(keys[ck][a][v], t) - 1
        if i >= 0 and arr[i][0] > t - 10000:
            vals.append(arr[i][1])
    return sum(vals) / len(vals) if vals else None

def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def run(ck, ddof, td_mode, base_spread):
    rows = []
    for t, c in cand.items():
        close, result = res[t]
        tr, yb, ya, strike, status = max(c)
        try:
            yb = float(yb); ya = float(ya); strike = float(strike)
        except Exception:
            continue
        if not (strike > 0):
            continue
        na = 1 - yb
        side = None
        if 0.03 <= ya <= 0.30:
            side, ask = "yes", ya
        elif 0.03 <= na <= 0.30:
            side, ask = "no", na
        if side is None:
            continue
        a = ASSET[t.split("-")[0]]
        td = tr if td_mode == "quote" else close - 120000
        p0 = index_at(ck, a, td)
        grid = [index_at(ck, a, td - k * 10000) for k in range(60, -1, -1)]
        ch = [math.log(y / x) for x, y in zip(grid, grid[1:]) if x and y]
        edge = None
        if p0 and len(ch) >= 6:
            m = sum(ch) / len(ch)
            var = sum((x - m) ** 2 for x in ch) / (len(ch) - ddof)
            sig = math.sqrt(var) * math.sqrt(8)
            if sig > 0:
                py = phi(math.log(p0 / strike) / sig)
                edge = (py if side == "yes" else 1 - py) - ask
        win = (result == side)
        pnl = (1 - ask if win else -ask) - 0.07 * ask * (1 - ask)
        rows.append(dict(t=t, ser=t.split("-")[0], ask=ask, spread=ya - yb, edge=edge, win=win, pnl=pnl, day=t.split("-")[1][:7]))
    def stat(rs):
        n = len(rs)
        if not n:
            return dict(n=0)
        pos = sum(r["pnl"] for r in rs if r["pnl"] > 0); neg = -sum(r["pnl"] for r in rs if r["pnl"] < 0)
        return dict(n=n, pf=round(pos / neg, 3) if neg else None, mean_c=round(100 * sum(r["pnl"] for r in rs) / n, 2), win=round(sum(r["win"] for r in rs) / n, 3))
    base = [r for r in rows if (not base_spread or r["spread"] <= 0.03 + 1e-9)]
    trig = [r for r in rows if r["edge"] is not None and r["edge"] >= 0.05 and r["spread"] <= 0.03 + 1e-9]
    out = dict(variant=f"{ck}/ddof{ddof}/{td_mode}", cheap_rows=len(rows), no_model=sum(1 for r in rows if r["edge"] is None), baseline=stat(base), edge_all=stat(trig))
    for s in ASSET:
        out[s] = stat([r for r in trig if r["ser"] == s])
    return out

print("markets with a dev result:", len(res), "| with a quote at T-120s:", len(cand), "| held-out result rows dropped at load:", dropped)
for ck, ddof, td in itertools.product(("exchange", "recv"), (1, 0), ("quote", "fixed")):
    print(json.dumps(run(ck, ddof, td, False)))
