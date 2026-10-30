"""REFINE-COUNTS: counts of L1 entries per price cell at the 6 minute look (gold, Dogecoin) and Dogecoin by Central hour. Counts only.
Reads candle bid/ask and market close_ts; never selects the market table's result or any outcome column. Not a try (N unchanged).
Usage: PYTHONPATH=src python -m scalper.refine_counts OUTDIR"""
import csv, glob, sqlite3, sys
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
from .analyze import valid_quote
from .paths import DATA_DIR

CT = ZoneInfo("America/Chicago")
LEFT = 360
SER = ["KXGOLD15M", "KXDOGE15M"]
E = 1e-9
# cell edges on the rounded (4 place) price of the bought side
CELLS = [("band_88_97", 0.88 - E, 0.97 + E), ("c_86_88", 0.86 - E, 0.88 - E), ("c_97_98", 0.97 + E, 0.98 + E)]


def pick_cell(bid, ask):
    """Live l1Pick order (YES at its ask first, else NO at 1-bid), applied to the live band first, then to the two outer cells."""
    ra = round(ask, 4); rn = round(1 - bid, 4)
    for name, lo, hi in CELLS:
        if lo <= ra <= hi or lo <= rn <= hi:
            return name
    return None


def load():
    by = {}
    for f in sorted(glob.glob(str(DATA_DIR / "*.sqlite"))):
        db = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
        try:
            q = ("SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, m.close_ts FROM candle c JOIN market m ON m.ticker = c.ticker "
                 "WHERE c.series IN (?,?)")
            for s, tk, end, bc, ac, close in db.execute(q, tuple(SER)):
                m = by.setdefault(tk, {"s": s, "close": close, "c": {}})
                if bc is not None and ac is not None and end not in m["c"]:
                    m["c"][end] = (bc, ac)
        except sqlite3.Error:
            pass
    return by


def main(out):
    by = load()
    day = defaultdict(lambda: defaultdict(int))
    hour = defaultdict(int)
    for tk, m in by.items():
        cl = m["close"]
        if not cl:
            continue
        d = datetime.fromtimestamp(cl, CT)
        k = (m["s"], d.strftime("%Y-%m-%d"))
        day[k]["windows"] += 1
        c = m["c"].get(cl - LEFT)
        if c is None:
            day[k]["no_candle"] += 1
            continue
        if not valid_quote(*c):
            day[k]["bad_quote"] += 1
            continue
        cell = pick_cell(*c)
        if cell is None:
            day[k]["no_entry"] += 1
            continue
        day[k][cell] += 1
        if m["s"] == "KXDOGE15M" and cell == "band_88_97":
            hour[(d.strftime("%Y-%m-%d"), d.hour)] += 1
    with open(f"{out}/REFINE_R1_counts.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["series", "date", "cell", "entries", "no_candle_windows", "windows_on_file", "bad_quote_windows"])
        for (s, dt) in sorted(day):
            v = day[(s, dt)]
            for name, _, _ in CELLS:
                w.writerow([s, dt, name, v[name], v["no_candle"], v["windows"], v["bad_quote"]])
    with open(f"{out}/REFINE_R3_counts.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "hour", "entries"])
        for (dt, h) in sorted(hour):
            w.writerow([dt, h, hour[(dt, h)]])


main(sys.argv[1])
