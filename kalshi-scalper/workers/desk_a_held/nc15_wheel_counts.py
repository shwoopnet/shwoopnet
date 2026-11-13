"""NC15 depth cell as a wheel place: COUNTS ONLY (Desk A, Nov 13 2026). Reads book columns only; reads NO result, trade or outcome column. Definition = workers/DESK_A_FROZEN_WHEEL_DEFINITIONS_NOV13.md.
  python3 -I nc15_wheel_counts.py <folder holding nc15/>
Per series: windows seen, windows with a signal poll, in the cell (|imb5| >= 0.50), in the cell with the implied ask 0.10 to 0.90 ('entering'), and FILL-CHECKED (the signal poll AND the next poll, at most 6 s later, each show >= 10 contracts summed over the recorded levels at or under touch + 1c)."""
import sys, glob, gzip, csv, statistics, collections, datetime, bisect
from email.utils import parsedate_to_datetime
SC = ["KXSILVER15M","KXCOPPER15M","KXWTI15M","KXEURUSD15M","KXGBPUSD15M","KXUSDJPY15M","KXHYPE15M","KXBNB15M","KXAUDUSD15M","KXUSDCAD15M","KXNATGAS15M"]
SIZE, LOOK, WINDOW, NEXTMAX = 10.0, 600, 10.0, 6.0
def f(x):
    try: return float(x) if x not in ("", None) else None
    except ValueError: return None
def ladder(p, side):
    """asks of the implied side as (price, size) sorted by price: a YES buy meets the NO bids (ask = 1 - NO bid), a NO buy meets the YES bids"""
    pre = "no_bid" if side == "yes" else "yes_bid"; out = []
    for i in range(1, 6):
        px, sz = f(p.get(f"{pre}_px_{i}")), f(p.get(f"{pre}_sz_{i}"))
        if px is not None and sz is not None: out.append((1 - px, sz))
    return sorted(out)
def depth_at(lad, limit): return sum(sz for a, sz in lad if a <= limit + 1e-9)
def main(root):
    st = {s: collections.Counter() for s in SC}; closes = {s: [] for s in SC}
    for fn in sorted(glob.glob(root + "/nc15/*/*/book.csv.gz")):
        rows = list(csv.DictReader(gzip.open(fn, "rt"))); rows.sort(key=lambda r: int(r["t_recv_ms"]))
        offs = []
        for r in rows:                                                  # per-row offset from the Date header; the exchange-time offset at a poll uses ONLY polls up to it
            try: offs.append(parsedate_to_datetime(r["server_date_header"]).timestamp() + 0.5 - int(r["t_recv_ms"]) / 1000)
            except Exception: offs.append(None)
        by = collections.defaultdict(list)
        for i, r in enumerate(rows):
            if r["series"] in st: by[r["ticker"]].append(i)
        for tk, idx in by.items():
            ser = rows[idx[0]]["series"]; cl = parsedate_to_datetime  # placeholder to keep names local
            ct = datetime.datetime.strptime(rows[idx[0]]["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()
            st[ser]["windows"] += 1; closes[ser].append(ct)
            L = ct - LOOK; sig = None
            for k, i in enumerate(idx):
                o = [x for x in offs[max(0, i - 119): i + 1] if x is not None]
                if not o: continue
                t = int(rows[i]["t_recv_ms"]) / 1000 + statistics.median(o)
                if t <= L and t >= L - WINDOW: sig = (k, i, t)
                if t > L: break
            if not sig: continue
            k, i, t = sig; p = rows[i]; st[ser]["signal poll"] += 1
            ys = sum(f(p[f"yes_bid_sz_{j}"]) or 0 for j in range(1, 6)); ns = sum(f(p[f"no_bid_sz_{j}"]) or 0 for j in range(1, 6))
            if ys + ns <= 0: continue
            imb = (ys - ns) / (ys + ns)
            if abs(imb) < 0.5 - 1e-12: continue
            st[ser]["cell"] += 1; side = "yes" if imb > 0 else "no"; lad = ladder(p, side)
            if not lad: continue
            ask = lad[0][0]
            if not (0.10 - 1e-9 <= ask <= 0.90 + 1e-9): continue
            st[ser]["entering"] += 1; limit = round(ask + 0.01, 6)
            if depth_at(lad, limit) < SIZE: continue
            if k + 1 >= len(idx): continue
            j = idx[k + 1]; q = rows[j]; o2 = [x for x in offs[max(0, j - 119): j + 1] if x is not None]
            if not o2: continue
            t2 = int(q["t_recv_ms"]) / 1000 + statistics.median(o2)
            if t2 - t > NEXTMAX + 1e-9: st[ser]["next poll later than 6 s"] += 1; continue
            if depth_at(ladder(q, side), limit) >= SIZE: st[ser]["fill-checked"] += 1
    span = {s: ((max(c) - min(c)) / 86400.0 if len(c) > 1 else 0.0) for s, c in closes.items()}
    print("series          days   windows signal  cell entering fill-chk | fill-checked per day | per 21 days")
    for s in SC:
        c = st[s]; d = span[s] or float("nan"); fc = c["fill-checked"]
        print("%-15s %5.2f %7d %6d %5d %8d %8d | %6.2f | %6.1f" % (s, d, c["windows"], c["signal poll"], c["cell"], c["entering"], fc, fc / d, 21 * fc / d))
    print("(next poll later than 6 s, not counted:", {s: st[s]["next poll later than 6 s"] for s in SC if st[s]["next poll later than 6 s"]}, ")")
if __name__ == "__main__": main(sys.argv[1])
