"""OIVER-DEPTH book-size builder (History Miner, Nov 13, 2026), from the Head of R&D's rulings of 21:10Z to 21:14Z (the R6 guard is the Head's ruling,
being added to card 3 by Desk A). Rules and the hand case in EXPECTED_BY_HAND.md (2becf882), committed first. Adds yes_bid_size and yes_ask_size from R6
book.csv.gz files (layout of scripts/record_15m_book.py) to the OIVER rows closing in [2026-10-29, 2026-11-09). No R6 folder dated 2026-11-09 or later is
opened; such a path stops the build. Governing card: Desk A's 23b5bd9b (sha256 ae1f1ee6), 21:13Z amendment; the poll time is EXCHANGE time by the
offset formula of the frozen sheet DESK_A_FROZEN_OIVER_SHADOW_DEFINITIONS_NOV13.md (61fb9854, sha256 cb45e79b, section 1 = the wheel sheet's section 0):
offset = median over the 120 most recent readable-header rows of the same run folder at or before the poll of (Date s + 0.5 - t_recv_ms / 1000);
exchange time = t_recv_ms / 1000 + offset (dated line of 21:30Z in EXPECTED_BY_HAND.md). Each book.csv.gz is one run folder. Adds r6_poll (1 or 0).
Usage: python3 -I oiver_r6sizes.py <oiver rows.csv> <out.csv> <book.csv.gz> [<book.csv.gz> ...]"""
import csv, gzip, io, json, math, os, re, statistics, sys
from datetime import datetime
from email.utils import parsedate_to_datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

R6_START = 1793232000                # 2026-10-29T00:00:00Z
R6_HELDOUT_FROM = 1794182400         # 2026-11-09T00:00:00Z
LO_S, HI_S = 190, 180                # the decision poll: exchange time in [close - 190 s, close - 180 s], inclusive
OFFSET_ROWS = 120                    # the offset window (open (a): fewer rows use all there are, at least 1; open (b): an even count takes the mean of the two middle)
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
    for p in book_paths:                                                      # one file = one run folder
        with gzip.open(p, "rt", newline="") as f:
            run = []
            for b in csv.DictReader(f):
                try:
                    run.append((int(float(b["t_recv_ms"])), b))
                except (KeyError, TypeError, ValueError):
                    continue
        run.sort(key=lambda x: x[0])                                            # by receive time, stable in file order
        terms = []                                                              # (Date s + 0.5 - t_recv s) of readable-header rows so far
        for tr, b in run:
            d = exch_s(b.get("server_date_header"))
            if d is not None:
                terms.append(d + 0.5 - tr / 1000.0)
            if not terms:
                continue                                                        # no readable row yet: no exchange time
            off = statistics.median(terms[-OFFSET_ROWS:])
            te = tr / 1000.0 + off
            try:
                key = (b["ticker"], iso(b["close_time"]))
            except (KeyError, TypeError, ValueError):
                continue
            if key not in want or key[1] >= R6_HELDOUT_FROM:
                continue
            if not (key[1] - LO_S - 1e-9 <= te <= key[1] - HI_S + 1e-9):
                continue
            if want[key] is None or te >= want[key][0] - 1e-12:                 # the last by exchange time; a tie goes to the later row
                want[key] = (te, b)
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
