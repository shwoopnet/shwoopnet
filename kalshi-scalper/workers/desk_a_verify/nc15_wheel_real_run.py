"""WH-NC15 block read, step 1 and 2 (Desk A, Nov 15 2026): drop the 28 excluded tickers, then run the FROZEN scorer unchanged and write the per-signal records CSV for wheel_block_reader.py.
  WHEEL_BLOCK_READ=1 python3 -I nc15_wheel_real_run.py <nc15 root: the folder holding <date>/<HHMM>/> <now ISO> <out.csv> <staging dir (new, empty)>
Copies only book.csv.gz and coverage.csv.gz of each run folder into the staging dir with every row of an excluded ticker removed (list: ../desk_a_held/mmmap1_nc15_excluded_tickers.txt, Auditor B's 28, sha256 d55741e3...; HELDOUT_REGISTRY.md section 'VA gate-read exposure'), prints how many tickers and book rows were dropped, then calls nc15_wheel_replay.replay (8d1055df, imported unchanged) on the staging copy. Default-closed like the scorer (WHEEL_BLOCK_READ=1 and no HELDOUT_ path). Reads the result column only through the frozen scorer."""
import sys, os, csv, gzip, io, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
EXCL_FILE = os.path.join(here, "..", "desk_a_held", "mmmap1_nc15_excluded_tickers.txt")
def load_excluded(path=EXCL_FILE):
    return {l.strip() for l in open(path) if l.strip()}
def filter_tree(root, stage, excl):
    dropped_t, dropped_rows = set(), 0
    for date in sorted(os.listdir(root)):
        dp = os.path.join(root, date)
        if not os.path.isdir(dp): continue
        for run in sorted(os.listdir(dp)):
            rp = os.path.join(dp, run)
            if not os.path.isdir(rp): continue
            for name in ("book.csv.gz", "coverage.csv.gz"):
                src = os.path.join(rp, name)
                if not os.path.exists(src): continue
                os.makedirs(os.path.join(stage, date, run), exist_ok=True)
                with gzip.open(src, "rt", newline="") as f, gzip.open(os.path.join(stage, date, run, name), "wt", newline="") as g:
                    r = csv.DictReader(f); w = csv.DictWriter(g, r.fieldnames); w.writeheader()
                    for row in r:
                        if row.get("ticker") in excl:
                            dropped_t.add(row["ticker"]); dropped_rows += 1 if name == "book.csv.gz" else 0; continue
                        w.writerow(row)
    return dropped_t, dropped_rows
def main(a):
    root, now_s, out, stage = a
    if os.environ.get("WHEEL_BLOCK_READ") != "1": sys.exit("REFUSED: WHEEL_BLOCK_READ=1 is not set (a block read is on the Head's word)")
    import heldout_guard; heldout_guard.refuse_heldout(os.path.abspath(root), "nc15 wheel real run")
    if os.path.exists(stage) and os.listdir(stage): sys.exit("REFUSED: staging dir is not empty")
    os.makedirs(stage, exist_ok=True)
    excl = load_excluded(); import nc15_wheel_replay as N
    dt, dr = filter_tree(os.path.abspath(root), os.path.abspath(stage), excl)
    print("EXCLUDED TICKERS DROPPED: %d of the list's %d (book rows removed: %d); list sha256 %s" % (len(dt), len(excl), dr, hashlib.sha256(open(EXCL_FILE, "rb").read()).hexdigest()[:8]))
    recs, reasons = N.replay(os.path.abspath(stage), now=N._iso(now_s))
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ticker", "series", "signal_t", "limit", "side", "status", "result", "win", "cash"])
        for r in sorted(recs, key=lambda r: (r["signal_t"], r["ticker"])): w.writerow([r["ticker"], r["series"], "%.6f" % r["signal_t"], "%.4f" % r["limit"], r["side"], r["status"], r.get("result", ""), r.get("win", ""), ("%.6f" % r["cash"]) if "cash" in r else ""])
    print("\n".join(N.report(recs, reasons))); print("wrote", out, len(recs), "records")
if __name__ == "__main__":
    if len(sys.argv) != 5: sys.exit(__doc__)
    main(sys.argv[1:])
