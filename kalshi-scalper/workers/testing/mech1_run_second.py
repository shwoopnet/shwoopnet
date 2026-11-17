#!/usr/bin/env python3
"""python3 -B mech1_run_second.py <records.jsonl> <MECH_REGISTRY.json> <m_carried> [A|B] -> the section 9 print on stdout (sha256 to stderr, committed BEFORE reading a print of real records). Windows are the date constants of 12.6."""
import hashlib, json, sys
import mech1_second as m
WINDOWS = {"search": ["2026-09-02", "2026-10-06"], "validate": ["2026-10-07", "2026-10-26"]}
def main(rec, reg, carried, option="A"):
    registry = json.load(open(reg))["entries"]; lines = open(rec).read().splitlines()
    return m.run(lines, registry, WINDOWS, carried, option_a=(option == "A"), data_file_shas={"records": hashlib.sha256(open(rec, "rb").read()).hexdigest(), "registry": hashlib.sha256(open(reg, "rb").read()).hexdigest()}, rule_hashes={"mech1_second.py": hashlib.sha256(open(m.__file__, "rb").read()).hexdigest()})
if __name__ == "__main__":
    a = sys.argv[1:]; text = "\n".join(main(a[0], a[1], int(a[2]), a[3] if len(a) > 3 else "A")) + "\n"; sys.stdout.write(text); sys.stderr.write("print sha256 %s\n" % hashlib.sha256(text.encode()).hexdigest())
