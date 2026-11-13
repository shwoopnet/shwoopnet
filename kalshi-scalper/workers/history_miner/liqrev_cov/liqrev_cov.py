"""LIQREV R15 coverage-interval row builder (History Miner, Nov 13, 2026), from Desk C's card LIQREV_CARD.md at d2822839 (sha256 f0257cce),
Amendment 3 R15, and the Head of R&D's order of 21:15Z; Desk C's and the Testing Desk's code were not read. Rules and the hand case in
EXPECTED_BY_HAND.md (1c7ea0be), committed first. Reads ONLY coverage.csv files: the OKX recorder's (t_start_ms, uly, oldest_ts_ms) and R6's
(close_time, series, ticker); never a liquidation, a price, a size or R6's result column. Writes ticker, close_ts, liq_covered. No real run before
2026-11-30 (the read dates are enforced).
Usage: python3 -I liqrev_cov.py dev|held <out.csv> --okx <coverage.csv.gz> ... --r6 <coverage.csv.gz> ..."""
import csv, gzip, json, os, re, sys, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

DAY = 86400
BLOCKS = {"dev": (1794873600, 1795996800, 1795996800),     # closes [2026-11-17, 2026-11-30); read on or after 2026-11-30
          "held": (1795996800, 1798761600, 1798848000)}    # closes [2026-11-30, 2027-01-01); read on or after 2027-01-02
ULYS = ("BTC-USDT", "BTC-USD")
SPAN_LO, SPAN_HI = 900, 180          # R15: [close - 720 - 180 s, close - 180 s)
SERIES = "KXBTC15M"
DATE_DIR = re.compile(r"^(\d{4})-(\d\d)-(\d\d)$")
COVER_NAMES = ("coverage.csv", "coverage.csv.gz")


class Stop(Exception):
    pass


def iso(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def rows_of(path, cols):
    """Yield, for each data row, ONLY the named columns (read by index; no other column is kept)."""
    if os.path.basename(path) not in COVER_NAMES:
        raise Stop("%s is not a coverage file" % path)
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", newline="") as f:
        rd = csv.reader(f)
        head = next(rd)
        idx = [head.index(c) for c in cols]
        for r in rd:
            yield [r[i] if i < len(r) else "" for i in idx]


def folder_date(path):
    for part in os.path.abspath(path).split(os.sep):
        g = DATE_DIR.match(part)
        if g:
            return iso("%s-%s-%sT00:00:00Z" % g.groups())
    return None


def merge(iv):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def intersect(x, y):
    out, i, j = [], 0, 0
    while i < len(x) and j < len(y):
        a, b = max(x[i][0], y[j][0]), min(x[i][1], y[j][1])
        if a <= b:
            out.append([a, b])
        if x[i][1] < y[j][1]:
            i += 1
        else:
            j += 1
    return out


def build(mode, out_path, okx_paths, r6_paths, now=None):
    if mode not in BLOCKS:
        raise Stop("mode is dev or held")
    lo, hi, read_on = BLOCKS[mode]
    now = time.time() if now is None else now
    if now < read_on:
        raise Stop("%s run refused before %s" % (mode, time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(read_on))))
    hm_guard.refuse_all([out_path] + list(okx_paths) + list(r6_paths))
    for p in r6_paths:
        d = folder_date(p)
        if d is None or not (lo - DAY <= d <= hi - DAY):
            raise Stop("R6 coverage file %s is outside the %s block's folders" % (p, mode))
    counts = {"windows": 0, "covered": 0, "no_liq_coverage": 0, "outside_block": 0, "other_series": 0, "duplicate": 0, "okx_rows": 0, "okx_no_interval": 0}
    per = {u: [] for u in ULYS}
    for p in okx_paths:
        for t_start, uly, oldest in rows_of(p, ["t_start_ms", "uly", "oldest_ts_ms"]):
            if uly not in ULYS:
                raise Stop("OKX coverage row with uly %r" % uly)
            counts["okx_rows"] += 1
            if oldest.strip() == "":
                counts["okx_no_interval"] += 1
                continue
            per[uly].append((int(float(oldest)), int(float(t_start))))
    joint = intersect(merge(per[ULYS[0]]), merge(per[ULYS[1]]))
    wins = {}
    for p in r6_paths:
        for close_time, series, ticker in rows_of(p, ["close_time", "series", "ticker"]):
            if series != SERIES:
                counts["other_series"] += 1
                continue
            c = iso(close_time)
            if not (lo <= c < hi):
                counts["outside_block"] += 1
                continue
            if ticker in wins:
                counts["duplicate"] += 1
                continue
            wins[ticker] = c
    rows = []
    for t, c in wins.items():
        a_need, b_need = (c - SPAN_LO) * 1000, (c - SPAN_HI) * 1000
        cov = any(a <= a_need and b >= b_need for a, b in joint)
        counts["windows"] += 1
        counts["covered" if cov else "no_liq_coverage"] += 1
        rows.append((c, t, 1 if cov else 0))
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ticker", "close_ts", "liq_covered"])
        w.writerows([t, c, v] for c, t, v in sorted(rows))
    return counts


if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        i, j = a.index("--okx"), a.index("--r6")
        print(json.dumps(build(a[0], a[1], a[i + 1:j], a[j + 1:])), file=sys.stderr)
    except Stop as e:
        raise SystemExit("STOP: %s" % e)
