#!/usr/bin/env python3
"""Run NBALADDER once: python3 -I nbaladder_run.py <root> <m_carried> [m_other_families].
m_carried is the single header value (6,290,660, the Head's ruling, via Auditor B); m_other_families is the other families' new rules in the same print
(0 for a development read). The header (m_carried, m_new, m_total) and the counts block print FIRST, then the rest; the sha256 of the whole print is committed before it is read."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbaladder as N


def main(root, carried, other=0):
    out = N.run(root, carried + other)
    m_new = N.N_RULES + other
    header = {"m_carried": carried, "m_new": m_new, "m_total": carried + m_new, "rules_this_spec": N.N_RULES}
    counts = out.pop("counts", None)
    for k in ("m_carried", "m_total", "rules_in_m"):
        out.pop(k, None)
    print(json.dumps(header, sort_keys=True))
    print(json.dumps({"counts": counts}, sort_keys=True, default=str))
    print(json.dumps(out, indent=1, sort_keys=True, default=str))
    return header


if __name__ == "__main__":
    a = sys.argv
    main(a[1], int(a[2]), int(a[3]) if len(a) > 3 else 0)
