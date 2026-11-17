#!/usr/bin/env python3
"""CHEAPFLIP real run, second build. python3 -B cheapflip_second_run.py <nc15 base dir> [allow file]: loader (allow line, series wall, cut), driver; stdout = the print (sha256 to stderr: commit it BEFORE reading the print)."""
import hashlib, sys
import cheapflip_second_load as LD, cheapflip_driver_second as D
def main(base, allow=None):
    mk, res, counts, man = LD.load(base, allow); return D.print_lines(mk, res, man, {"loader_counts": counts})
if __name__ == "__main__":
    text = "\n".join(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)) + "\n"; sys.stdout.write(text); sys.stderr.write("print sha256 %s\n" % hashlib.sha256(text.encode()).hexdigest())
