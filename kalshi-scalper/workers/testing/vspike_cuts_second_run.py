#!/usr/bin/env python3
"""python3 -B vspike_cuts_second_run.py <dir holding ENGINE1_archive_extract.sqlite.xz> [allow file]: loader (allow line, wall) then the table as JSON (keys sorted, floats unrounded) to stdout; sha256 to stderr, committed BEFORE reading the table."""
import hashlib, json, sys
import vspike_cuts_second as V, vspike_cuts_second_load as L
def main(d, allow=None):
    mk, cd, counts = L.load(d, allow); return json.dumps({"loader_counts": counts, "all_series_buckets": V.table(mk, cd)}, sort_keys=True, indent=1) + "\n"
if __name__ == "__main__":
    text = main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None); sys.stdout.write(text); sys.stderr.write("print sha256 %s\n" % hashlib.sha256(text.encode()).hexdigest())
