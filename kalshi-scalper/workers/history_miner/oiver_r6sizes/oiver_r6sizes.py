"""OIVER-DEPTH book-size builder (History Miner, Nov 13, 2026), from the Head of R&D's rulings of 21:10Z to 21:14Z (the R6 guard is the Head's ruling,
being added to card 3 by Desk A). Rules and the hand case in EXPECTED_BY_HAND.md (2becf882), committed first. Adds yes_bid_size and yes_ask_size from R6
book.csv.gz files (layout of scripts/record_15m_book.py) to the OIVER rows closing in [2026-10-29, 2026-11-09). No R6 folder dated 2026-11-09 or later is
opened; such a path stops the build. Governing card: Desk A's 23b5bd9b (sha256 ae1f1ee6), 21:13Z amendment; the poll time is EXCHANGE time, the
book row's HTTP Date header (dated line of 21:17Z in EXPECTED_BY_HAND.md). Adds r6_poll (1 or 0). Prints counts only.
Usage: python3 -I oiver_r6sizes.py <oiver rows.csv> <out.csv> <book.csv.gz> [<book.csv.gz> ...]"""
import csv, gzip, io, json, math, os, re, sys
from datetime import datetime
from email.utils import parsedate_to_datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

R6_START = 1793232000                # 2026-10-29T00:00:00Z
R6_HELDOUT_FROM = 1794182400         # 2026-11-09T00:00:00Z
LO_S, HI_S = 190, 180                # the decision poll: the exchange Date in [close - 190 s, close - 180 s], inclusive
DATE_DIR = re.compile(r"^(\d{4})-(\d\d)-(\d\d)$")


class Stop(Exception):
    pass


def iso(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def guard_path(p):
    hm_guard.refuse_all([p])
    for part in os.path.abspath(p).split(os.sep) + os.path.realpath(p).split(os.sep):
        g = DATE_DIR.match(part)
        if g and iso("%s-%s-%sT00:00:00Z" % g.groups()) >= R6_HELDOUT_FROM:
            raise Stop("R6 folder dated %s is on or after 2026-11-09 and is not opened" % part)


def exch_s(v):
    try:
        d = parsedate_to_datetime(v)
    except (TypeError, ValueError, IndexError):
        return None
    if d is None or d.tzinfo is None:
        return None
    return int(d.timestamp())


def size(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def build(rows_path, out_path, book_paths):
    hm_guard.refuse_all([rows_path, out_path])
    for p in book_paths:
        guard_path(p)
    with open(rows_path, newline="") as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames
        rows = list(rd)
    counts = {"rows_in": len(rows), "before_r6": 0, "written": 0, "no_poll": 0, "missing_size": 0}
    want = {}
    keep = []
    for r in rows:
        close = int(r["close_ts"])
        if close >= R6_HELDOUT_FROM:
            raise Stop("input row %s closes on or after 2026-11-09" % r["ticker"])
        if close < R6_START:
            counts["before_r6"] += 1
            continue
        keep.append(r)
        want[(r["ticker"], close)] = None
    for p in book_paths:
        with gzip.open(p, "rt", newline="") as f:
            for b in csv.DictReader(f):
                try:
                    key = (b["ticker"], iso(b["close_time"]))
                    tr = int(float(b["t_recv_ms"]))
                except (KeyError, TypeError, ValueError):
                    continue
                if key not in want or key[1] >= R6_HELDOUT_FROM:
                    continue
                te = exch_s(b.get("server_date_header"))
                if te is None or not (key[1] - LO_S <= te <= key[1] - HI_S):
                    continue
                if want[key] is None or (te, tr) >= want[key][0]:              # the latest Date, then the latest t_recv_ms, then the later file row
                    want[key] = ((te, tr), b)
    out = []
    for r in keep:
        hit = want[(r["ticker"], int(r["close_ts"]))]
        ybs = yas = None
        if hit is None:
            counts["no_poll"] += 1
        else:
            ybs, yas = size(hit[1].get("yes_bid_sz_1")), size(hit[1].get("no_bid_sz_1"))
            if ybs is None or yas is None:
                counts["missing_size"] += 1
        out.append([r[c] for c in cols] + ["" if ybs is None else repr(ybs), "" if yas is None else repr(yas), "0" if hit is None else "1"])
        counts["written"] += 1
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols + ["yes_bid_size", "yes_ask_size", "r6_poll"])
        w.writerows(out)
    return counts


if __name__ == "__main__":
    try:
        print(json.dumps(build(sys.argv[1], sys.argv[2], sys.argv[3:])), file=sys.stderr)
    except Stop as e:
        raise SystemExit("STOP: %s" % e)
