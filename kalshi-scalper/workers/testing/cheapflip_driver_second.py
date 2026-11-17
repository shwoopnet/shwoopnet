#!/usr/bin/env python3
"""CHEAPFLIP driver (build 2): JSON lines in Desk C's layout. print_lines(markets, results, manifest=None) -> list of strings."""
import json
import cheapflip_second as c

def print_lines(markets, results, manifest=None, counts_extra=None):
    ents, cnt = c.collect(markets, results); rows = c.table(ents, cnt)
    out = [json.dumps({"kind": "header", "m_carried": c.M_CARRIED, "m_new": c.M_NEW, "m_total": c.M_CARRIED + c.M_NEW, "label": "descriptive read, not a strategy path; upper bound, not fill-checked; development, no evidence at small n"}, sort_keys=True)]
    out.append(json.dumps({"kind": "stats", "entries": len(ents), "markets": len(markets), **cnt, **(counts_extra or {})}, sort_keys=True))
    out.append(json.dumps({"kind": "manifest", **(manifest or {})}, sort_keys=True))
    for band, k, cells in rows: out.append(json.dumps({"kind": "cell", "band": band, "k": k, "cells": cells}, sort_keys=True, default=str))
    return out
