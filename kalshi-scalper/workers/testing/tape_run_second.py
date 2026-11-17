#!/usr/bin/env python3
"""python3 -B tape_run_second.py <root with tape/> <tickers comma list> <allow file> <out prefix> -> writes <prefix>.bars.csv and <prefix>.summary.csv, prints their sha256 and the manifest sha256 (repr of the sorted (relpath, sha256) tuples)."""
import hashlib, sys
import tape_bars_second as T
def main(root, tickers, allow, prefix):
    bars, summ, ticks, man = T.build_from_files(root, tickers.split(","), allow); bt = T.bar_text(bars); st = "\n".join(T.summary_lines(summ, ticks)) + "\n"
    open(prefix + ".bars.csv", "w").write(bt); open(prefix + ".summary.csv", "w").write(st)
    print("bars", len(bars), "sha256", T.sha(bt)); print("summary sha256", T.sha(open(prefix + ".summary.csv").read())); print("manifest sha256", hashlib.sha256(repr(man).encode()).hexdigest(), "files", len(man))
if __name__ == "__main__": main(*sys.argv[1:5])
