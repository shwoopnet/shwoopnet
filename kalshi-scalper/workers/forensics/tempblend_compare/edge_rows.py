#!/usr/bin/env python3
"""TEMPBLEND third invented row set: one row on each edge of the card (658817e9, A1 to A18), built from the card text alone (Forensics desk, Nov 13, 2026). No data, no Kalshi request.
Base row: watched station "W" is one of the five (member), index point t = S - 1200 s (published exactly at the decision, the oldest-allowed lag), v 71.0, the station reads 70.0 at t (gap 1.0F),
one strike K = 71 with yes_bid 0.48, yes_ask 0.50 (spread 2c), result "yes", calibration effective 5 days before the decision.
usage: python3 -I edge_rows.py <out dir>   -> edge_rows_build1_layout.json, edge_watched.json (and the mapped build 2 layout through map_and_compare.c_to_m)"""
import sys, os, json
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import map_and_compare as MC

def S(iso): return int(datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())

def base(rid, s_iso="2026-09-20T12:00:00Z", v=71.0, s=70.0, strikes=None, code="ok", idx_back=1200, obs_back=None, calib_back=5 * 86400, external=None):
    Sx = S(s_iso); dec = Sx - 900; t = Sx - idx_back; obs = t - (obs_back or 0)
    row = {"city": rid, "S": s_iso, "t_ms": t * 1000, "v": v, "calib_effective_ms": (dec - calib_back) * 1000, "strikes": strikes or [{"K": 71, "yes_bid": 0.48, "yes_ask": 0.50, "result": "yes"}]}
    row["stations"] = [] if external else [{"station_id": "W", "temp_f": s, "code": code, "obs_time_ms": obs * 1000}]
    if external: row["external"] = {"W": {"temp_f": s, "obs_time_ms": obs * 1000}}
    return row

def k(K, yb, ya, res="yes"): return {"K": K, "yes_bid": yb, "yes_ask": ya, "result": res}

rows = [
 base("E01_gap_exactly_0.5", v=70.5, s=70.0, strikes=[k(70.5, 0.48, 0.50)]),                  # g = 0.5 exactly (binary exact); K = v is allowed (K <= v)
 base("E02_gap_0.49", v=70.49, s=70.0, strikes=[k(70.49, 0.48, 0.50)]),
 base("E03_ask_exactly_0.20", strikes=[k(71, 0.17, 0.20, "no")]),
 base("E04_ask_0.19", strikes=[k(71, 0.16, 0.19)]),
 base("E05_ask_exactly_0.80", strikes=[k(71, 0.77, 0.80)]),
 base("E06_ask_0.81", strikes=[k(71, 0.78, 0.81)]),
 base("E07_spread_exactly_0.04", strikes=[k(71, 0.46, 0.50, "no")]),
 base("E08_spread_0.05", strikes=[k(71, 0.45, 0.50)]),
 base("E09_reading_exactly_600s_old", obs_back=600),
 base("E10_reading_601s_old", obs_back=601),
 base("E11_calibration_exactly_172800s", calib_back=172800),
 base("E12_calibration_172799s", calib_back=172799),
 base("W01_S_2026-09-12T23:59:59Z", s_iso="2026-09-12T23:59:59Z"),
 base("W02_S_2026-09-13T00:00:00Z_dev_first_half", s_iso="2026-09-13T00:00:00Z"),
 base("W03_S_2026-10-08T23:59:59Z_dev_first_half", s_iso="2026-10-08T23:59:59Z"),
 base("W04_S_2026-10-09T00:00:00Z_dev_second_half", s_iso="2026-10-09T00:00:00Z"),
 base("W05_S_2026-11-04T23:59:59Z_dev_second_half", s_iso="2026-11-04T23:59:59Z"),
 base("W06_S_2026-11-05T00:00:00Z", s_iso="2026-11-05T00:00:00Z"),
 base("W07_S_2026-11-11T23:59:59Z", s_iso="2026-11-11T23:59:59Z"),
 base("W08_S_2026-11-12T00:00:00Z_held", s_iso="2026-11-12T00:00:00Z"),
 base("W09_S_2026-12-09T23:59:59Z_held", s_iso="2026-12-09T23:59:59Z"),
 base("W10_S_2026-12-10T00:00:00Z", s_iso="2026-12-10T00:00:00Z"),
 base("T01_midpoint_tie_exact", v=72.0, s=70.0, strikes=[k(70.5, 0.43, 0.45), k(71.5, 0.53, 0.55)]),   # mid 71.0, both 0.5 away
 base("T02_midpoint_tie_in_floating_point_only", v=72.3, s=70.1, strikes=[k(70.7, 0.43, 0.45), k(71.7, 0.53, 0.55)]),   # mid 71.2, both 0.5 away on paper, 71.2 - 70.7 is 0.5000000000000142
 base("V01_void", strikes=[k(71, 0.48, 0.50, "void")]),
 base("M01_member_code_missing", code=None),
 base("M02_member_code_degraded", code="degraded"),
 base("B01_source_B_non_member", external=True),
 base("N01_gap_exactly_minus_0.5_NO", v=69.5, s=70.0, strikes=[k(70.0, 0.52, 0.54, "no")]),
 base("N02_NO_ask_exactly_0.20", v=69.0, s=70.0, strikes=[k(70.0, 0.80, 0.83, "no")]),
 base("N03_NO_ask_exactly_0.80", v=69.0, s=70.0, strikes=[k(70.0, 0.20, 0.23, "yes")]),
 base("E13_gap_exactly_0.5_on_paper_under_0.5_in_floating_point", v=64.1, s=63.6, strikes=[k(64.1, 0.48, 0.50)]),   # 64.1 - 63.6 = 0.4999999999999929
 base("E14_spread_exactly_0.04_on_paper_over_0.04_in_floating_point", strikes=[k(71, 0.50, 0.54)]),                    # 0.54 - 0.50 = 0.040000000000000036
 base("T03_midpoint_tie_with_the_HIGHER_strike_nearer_in_floating_point", v=70.7, s=69.1, strikes=[k(69.5, 0.43, 0.45), k(70.3, 0.53, 0.55)]),   # mid 69.9; 0.4000000000000057 against 0.3999999999999915
 base("I01_index_point_exactly_600s_before_decision", idx_back=1500),
 base("I02_index_point_601s_before_decision", idx_back=1501),
 base("I03_index_point_299s_before_decision_too_new", idx_back=1199),
]

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True); watched = {r["city"]: "W" for r in rows}
    json.dump(rows, open(os.path.join(out, "edge_rows_build1_layout.json"), "w"), indent=1, sort_keys=True); json.dump(watched, open(os.path.join(out, "edge_watched.json"), "w"))
    m, notes = MC.c_to_m(rows, watched)
    with open(os.path.join(out, "edge_rows_build2_layout.jsonl"), "w") as f:
        for r in m: f.write(json.dumps(r, sort_keys=True) + "\n")
    print("%d rows written to %s; mapping notes: %s" % (len(rows), out, "; ".join(notes) or "none"))
