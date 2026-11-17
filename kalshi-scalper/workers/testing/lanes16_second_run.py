#!/usr/bin/env python3
"""Lanes 1 and 6 real-data run, second build. python3 -B lanes16_second_run.py <dir with the two xz extracts> <page max tsv> <m_carried> [allow file]
Reads through lanes16_second_load.py (allow line, wall, window), pins the page-max table by sha256, runs the 144 rules x columns, writes the driver's JSON lines to stdout (print sha256 to stderr: commit it BEFORE reading the print)."""
import hashlib, sys
import lanes16_second_load as L, lanes16_driver_second as D

def main(directory, pm_path, m_carried, allow=None):
    data, funding, counts = L.load(directory, allow); pm = L.page_max(pm_path)
    names = [n for n in sorted(data) if data[n]]
    head = ["loader counts " + repr(sorted(counts.items())), "page max table sha256 %s, names with a page max %s, without %s" % (L.PAGE_MAX_SHA, sorted(pm), sorted(set(L.WALL) - set(pm)))]
    return head + D.run({n: data[n] for n in names}, {n: funding[n] for n in names}, pm, m_carried)

if __name__ == "__main__":
    a = sys.argv[1:]; text = "\n".join(main(a[0], a[1], int(a[2]), a[3] if len(a) > 3 else None)) + "\n"
    sys.stdout.write(text); sys.stderr.write("print sha256 %s\n" % hashlib.sha256(text.encode()).hexdigest())
