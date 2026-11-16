#!/usr/bin/env python3
"""POOL1 real-data run with the Testing Desk's second build (needs the allow line). Prints the pool, the counts and then the driver's 218 rule lines. Output goes to scratch only; its sha256 is committed BEFORE it is read.
  python3 -I pool1_second_run.py <dir with the two xz extracts>"""
import sys, hashlib
import pool1_second_load as L, pool1_driver_second as D


def run(directory, allow_file=None, xz_sha=None):
    data, funding, counts = L.load(directory, allow_file, xz_sha)
    names = [n for n in sorted(data) if data[n]]
    lines = ["counts " + repr(sorted(counts.items())), "names with candles %d, with prints %d" % (len(names), sum(1 for n in names if funding[n]))] + D.run({n: data[n] for n in names}, {n: funding[n] for n in names})
    return lines


if __name__ == "__main__":
    lines = run(sys.argv[1]); text = "\n".join(lines) + "\n"
    sys.stdout.write(text); sys.stderr.write("print sha256 %s\n" % hashlib.sha256(text.encode()).hexdigest())
