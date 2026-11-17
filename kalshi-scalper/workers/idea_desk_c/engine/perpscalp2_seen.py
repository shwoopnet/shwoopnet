#!/usr/bin/env python3
"""PERPSCALP2 SEEN-days lister (Idea Desk C, Nov 17, 2026). NOT the scorer. Reads, per file, ONLY the ticker column and the timestamp column (candles: end_period_ts; funding:
funding_time) of the perp-data files the Nov 16 print read (kalshi1m and funding, <date>[.only].csv.gz), never a bid, ask, price, volume or rate, and prints the sorted (name, UTC day)
pairs, counts per name, files_read and the same manifest sha as the Nov 16 print. It REFUSES (exit 2, nothing printed but the reason) unless files_read, the manifest sha and the dropped
short-history names equal the values it is given from the Nov 16 print. Usage: python3 -I perpscalp2_seen.py <root> <expected_files> <expected_manifest_sha> <dropped names comma separated> """
import csv, glob, gzip, hashlib, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perpscalp2 as P


def seen(root):
    manifest, days, funding_days, counts, skipped = [], {}, {}, {}, {}
    st = {}
    for sub, col in (("kalshi1m", "end_period_ts"), ("funding", "funding_time")):
        for f in P._files(root, sub, st):
            manifest.append((os.path.relpath(f, root), P._sha(f)))
            with gzip.open(f, "rt", newline="") as fh:
                rd = csv.reader(fh)
                hdr = next(rd)
                it, ct = hdr.index("ticker"), hdr.index(col)
                for row in rd:
                    n = row[it]
                    if n not in P.NAMES:
                        continue
                    if sub == "kalshi1m":
                        ts = int(row[ct])
                        if ts >= P.H16_START:
                            skipped["h16_rows"] = skipped.get("h16_rows", 0) + 1
                            continue
                        if ts > P.END_EPOCH:
                            skipped["after_development_end"] = skipped.get("after_development_end", 0) + 1
                            continue
                        days.setdefault(n, set()).add(time.strftime("%Y-%m-%d", time.gmtime(ts)))
                        reg = P.et_min(ts)
                        if reg[0] < 5 and P.sess_end(reg[2]) is not None and 9 * 60 + 35 <= reg[1] <= P.sess_end(reg[2]):
                            counts[n] = counts.get(n, 0) + 1
                    else:
                        funding_days.setdefault(n, set()).add(time.strftime("%Y-%m-%d", time.gmtime(P.iso(row[ct]))))
    return {"files_read": len(manifest), "manifest_sha256": hashlib.sha256(repr(sorted(manifest)).encode()).hexdigest(), "files_skipped": st.get("files_skipped", 0),
            "candle_days": {n: sorted(d) for n, d in sorted(days.items())}, "funding_days": {n: sorted(d) for n, d in sorted(funding_days.items())},
            "regular_candles_by_timestamp": dict(sorted(counts.items())), "rows_not_used": skipped,
            "dropped_short_history": sorted(n for n in P.NAMES if counts.get(n, 0) < 600)}


def main(root, exp_files, exp_sha, exp_dropped):
    out = seen(root)
    bad = [k for k, ok in (("files_read", out["files_read"] == exp_files), ("manifest_sha256", out["manifest_sha256"] == exp_sha),
                           ("dropped_short_history", out["dropped_short_history"] == sorted(x for x in exp_dropped.split(",") if x))) if not ok]
    if bad:
        print("REFUSED: does not reproduce the Nov 16 print: " + ",".join(bad))
        return 2
    # Auditor B's ruling: a name the Nov 16 print dropped before scoring has no result in it, so its days are NOT SEEN; they are listed apart and never used to exclude
    out["loaded_not_dropped_not_scored"] = {n: out["candle_days"].pop(n) for n in list(out["candle_days"]) if n in out["dropped_short_history"]}
    out["counts_per_name"] = {n: len(d) for n, d in out["candle_days"].items()}
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else ""))
