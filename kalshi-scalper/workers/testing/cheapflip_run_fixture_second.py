#!/usr/bin/env python3
"""python3 -B cheapflip_run_fixture_second.py fixture.json -> the driver's lines."""
import json, sys
import cheapflip_driver_second as D
fx = json.load(open(sys.argv[1]))
mk = {t: (v[0], v[1], [(p[0], t, v[1], [tuple(x) for x in p[1]], [tuple(x) for x in p[2]]) for p in v[2]]) for t, v in fx["markets"].items()}
print("\n".join(D.print_lines(mk, fx["results"])))
