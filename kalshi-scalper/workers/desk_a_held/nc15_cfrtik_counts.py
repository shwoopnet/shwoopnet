"""CFRTI-K on the NC15 markets: COUNTS ONLY (Desk A, Nov 13 2026). Book columns only; no result, trade or outcome column is read; no perp data (so the model edge is NOT counted here).
  python3 -I nc15_cfrtik_counts.py <folder holding nc15/>
Per series: windows seen, windows with a signal poll (the FIRST poll at or after close minus 110 s, at most 10 s later), and the cheap side (YES ask 0.05 to 0.30, else NO ask 0.05 to 0.30) with spread 0.03 or less ('cheap-and-tight')."""
import sys, glob, gzip, csv, statistics, collections, datetime
from email.utils import parsedate_to_datetime
SC = ["KXSILVER15M","KXCOPPER15M","KXWTI15M","KXHYPE15M","KXBNB15M"]
def f(x):
    try: return float(x) if x not in ("", None) else None
    except ValueError: return None
def main(root):
    st = {s: collections.Counter() for s in SC}; closes = {s: [] for s in SC}
    for fn in sorted(glob.glob(root + "/nc15/*/*/book.csv.gz")):
        rows = list(csv.DictReader(gzip.open(fn, "rt"))); rows.sort(key=lambda r: int(r["t_recv_ms"]))
        offs = []
        for r in rows:
            try: offs.append(parsedate_to_datetime(r["server_date_header"]).timestamp() + 0.5 - int(r["t_recv_ms"]) / 1000)
            except Exception: offs.append(None)
        by = collections.defaultdict(list)
        for i, r in enumerate(rows):
            if r["series"] in st: by[r["ticker"]].append(i)
        for tk, idx in by.items():
            ser = rows[idx[0]]["series"]; ct = datetime.datetime.strptime(rows[idx[0]]["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()
            st[ser]["windows"] += 1; closes[ser].append(ct); D = ct - 120; sig = None
            for i in idx:
                o = [x for x in offs[max(0, i - 119): i + 1] if x is not None]
                if not o: continue
                t = int(rows[i]["t_recv_ms"]) / 1000 + statistics.median(o)
                if D + 10 <= t <= D + 20: sig = i; break                  # Head's ruling Nov 13: the decision poll is the FIRST poll at or after D + 10 s (a stated allowance for the perp candle to be published), at most 10 s later
            if sig is None: continue
            p = rows[sig]; st[ser]["signal poll"] += 1
            yb, nb = f(p["yes_bid_px_1"]), f(p["no_bid_px_1"])
            if yb is None or nb is None: continue
            ya, na = 1 - nb, 1 - yb; spread = ya - yb
            if spread <= 0 or spread > 0.03 + 1e-9: continue
            if 0.05 - 1e-9 <= ya <= 0.30 + 1e-9 or 0.05 - 1e-9 <= na <= 0.30 + 1e-9: st[ser]["cheap and tight"] += 1
    print("series          days  windows signal-poll cheap-and-tight | per day | per 21 days (weekday-only series x 15/21)")
    for s in SC:
        c = st[s]; d = ((max(closes[s]) - min(closes[s])) / 86400.0) if len(closes[s]) > 1 else float("nan"); n = c["cheap and tight"]
        wk = 15 / 21 if s not in ("KXHYPE15M", "KXBNB15M") else 1.0
        print("%-15s %5.2f %7d %11d %14d | %6.2f | %6.1f" % (s, d, c["windows"], c["signal poll"], n, n / d, 21 * n / d * wk))
if __name__ == "__main__": main(sys.argv[1])
