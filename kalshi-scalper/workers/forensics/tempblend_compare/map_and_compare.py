#!/usr/bin/env python3
"""TEMPBLEND: run Desk C's scorer (build 1, tempblend_score.py 90227da8) and the History Miner's (build 2, tempblend2.py 3fab82b3) on BOTH invented row sets, with the rows
mapped to each script's own input layout WITHOUT changing a value (Forensics desk, Nov 13, 2026; research only; no data; no Kalshi request).
usage: python3 -I map_and_compare.py <build 1 dir> <build 2 dir> <out dir>   (dirs hold the files at the named commits: c/{tempblend_score.py,test_rows.json,test_watched.json}, m/{tempblend2.py,rows_madeup.jsonl})
Mapping choices, where a layout holds less or more than the other (each is printed with the result):
 C -> M: index = [[t_ms/1000, v]] (build 1's row carries ONE canonical point); station = the watched station's reading keyed by that point (Source A) or by its own obs_time (Source B, from external);
         member = the watched station is in stations[]; source = "A" if member else "B"; a city with no watched station in the map cannot be said in build 2's layout (counted, row kept with an unreadable station).
 M -> C: the point chosen for t_ms is the latest point at or before S - 900 - 300 (the card's A1); with none, the earliest point (so build 1's own lag check rejects it). A Source A reading goes into stations[] with
         station_id "W" and obs_time_ms (omitted = t); a Source B reading is the latest at or before t (none: the earliest) and goes into external["W"]. A row with member false but source A cannot be said in build 1's layout
         (membership is the presence in stations[]): its reading goes into external["W"] with the same obs time, and the row is listed as a mapping difference. watched = {city: "W"} for every city.
Every figure of both outputs is compared row by row (the decision of each city-hour: skip reason class, side, strike, ask, fee, pnl, void, member, calibration day) and in aggregate."""
import sys, os, json, importlib.util, math
from datetime import datetime, timezone


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def iso_s(s): return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
def s_iso(x): return datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def c_to_m(rows, watched):
    out, notes = [], []
    for r in rows:
        sid = watched.get(r["city"]); S = iso_s(r["S"]); t = r["t_ms"] / 1000; st = None
        for x in r.get("stations", []):
            if x.get("station_id") == sid: st = x
        ext = (r.get("external") or {}).get(sid)
        if sid is None: notes.append("%s %s: no watched station in the map; build 2 cannot say it, the row is mapped with no reading" % (r["city"], r["S"]))
        if st is not None:
            source, member = "A", True; station = [[t, st["temp_f"], st.get("code"), (st["obs_time_ms"] / 1000) if st.get("obs_time_ms") is not None else None]]
        elif ext is not None:
            source, member = "B", False; station = [[(ext["obs_time_ms"] / 1000) if ext.get("obs_time_ms") is not None else t, ext["temp_f"], None]]
        else: source, member, station = "B", False, []
        out.append({"city": r["city"], "S": S, "member": member, "source": source, "index": [[t, r["v"]]], "station": station, "cal_effective_ms": r["calib_effective_ms"],
                    "strikes": [{"K": k["K"], "yes_bid": k.get("yes_bid"), "yes_ask": k.get("yes_ask"), "result": k.get("result")} for k in r.get("strikes", [])]})
    return out, notes


def m_to_c(rows):
    out, notes = [], []
    for r in rows:
        S = r["S"]; dec = S - 900; pts = sorted(r["index"], key=lambda p: p[0]); ok = [p for p in pts if p[0] <= dec - 300]
        t, v = (ok[-1] if ok else pts[0])
        row = {"city": r["city"], "S": s_iso(S), "t_ms": int(round(t * 1000)), "v": v, "calib_effective_ms": r["cal_effective_ms"], "stations": [], "strikes": []}
        if r["source"] == "A":
            rd = [x for x in r["station"] if x[0] == t]
            if rd:
                x = rd[0]; obs = x[3] if len(x) > 3 and x[3] is not None else x[0]; reading = {"station_id": "W", "temp_f": x[1], "code": x[2], "obs_time_ms": int(round(obs * 1000))}
                if r.get("member"): row["stations"].append(reading)
                else:
                    row["external"] = {"W": {"temp_f": x[1], "obs_time_ms": reading["obs_time_ms"]}}; notes.append("%s S=%s: member false with source A; the reading is passed as external (build 1 reads membership from stations[])" % (r["city"], S))
        else:
            rd = [x for x in r["station"] if x[0] <= t]; x = max(rd, key=lambda a: a[0]) if rd else (min(r["station"], key=lambda a: a[0]) if r["station"] else None)
            if x is not None: row["external"] = {"W": {"temp_f": x[1], "obs_time_ms": int(round(x[0] * 1000))}}
        row["strikes"] = [{"K": k["K"], "yes_bid": k.get("yes_bid"), "yes_ask": k.get("yes_ask"), "result": k.get("result")} for k in r["strikes"]]
        out.append(row)
    return out, notes


def cls(reason):
    if reason is None: return "bet"
    return {"no_index_point": "no index point", "no index point": "no index point", "no_watched_station": "no station reading", "no_reading": "no station reading", "stale_reading": "no station reading", "no station reading": "no station reading",
            "member_not_ok": "member not ok", "member station not ok": "member not ok", "gap_small": "gap small", "gap under 0.5F": "gap small", "no_strike": "no strike", "no strike between": "no strike",
            "no strike passes band and spread": "no strike", "outside_windows": "outside windows"}.get(reason, reason)


def main(cdir, mdir, out):
    os.makedirs(out, exist_ok=True)
    C = load(os.path.join(cdir, "tempblend_score.py"), "tb1"); M = load(os.path.join(mdir, "tempblend2.py"), "tb2")
    watched = json.load(open(os.path.join(cdir, "test_watched.json")))
    c_rows = json.load(open(os.path.join(cdir, "test_rows.json"))); m_rows = [json.loads(l) for l in open(os.path.join(mdir, "rows_madeup.jsonl")) if l.strip()]
    report = []
    for label, rows_c, rows_m, notes, w in (("SET 1 (Desk C's rows)", c_rows, *c_to_m(c_rows, watched), watched), ("SET 2 (History Miner's rows)", *(lambda a: (a[0], m_rows, a[1]))(m_to_c(m_rows)), {r["city"]: "W" for r in m_rows})):
        tag = label.split()[1]
        json.dump(rows_c, open(os.path.join(out, "set%s_rows_build1_layout.json" % tag), "w"), indent=1, sort_keys=True)
        with open(os.path.join(out, "set%s_rows_build2_layout.jsonl" % tag), "w") as f:
            for r in rows_m: f.write(json.dumps(r, sort_keys=True) + "\n")
        json.dump(w, open(os.path.join(out, "set%s_watched.json" % tag), "w"))
        o1 = C.score(rows_c, w); o2 = M.run(os.path.join(out, "set%s_rows_build2_layout.jsonl" % tag))
        json.dump(o1, open(os.path.join(out, "set%s_build1_output.json" % tag), "w"), indent=1, sort_keys=True); json.dump(o2, open(os.path.join(out, "set%s_build2_output.json" % tag), "w"), indent=1, sort_keys=True)
        diffs = []
        # per-row decisions (the rows are in the same order in both layouts)
        for i, (rc, rm) in enumerate(zip(rows_c, rows_m)):
            b1, why1 = C.decide(rc, w); st2, b2 = M.decide(rm); S2 = rm["S"]
            win2 = "outside windows" if not ((M.iso(M.DEV[0]) <= S2 < M.iso(M.DEV[1])) or (M.iso(M.HELD[0]) <= S2 < M.iso(M.HELD[1]))) else None
            c1 = cls(why1) if b1 is None else "bet"; c2 = win2 or cls(st2 if b2 is None else None)
            if c1 != c2: diffs.append("row %d (%s S=%s): build 1 %s (%s); build 2 %s (%s)" % (i, rc["city"], rc["S"], c1, why1, c2, st2))
            elif b1 and b2:
                for name, x, y in (("side", b1["side"], b2["side"]), ("K", b1["K"], b2["K"]), ("ask", b1["ask"], b2["ask"]), ("pnl", b1["pnl"], b2["pnl"]), ("void", b1["void"], b2["void"]), ("member", b1["member"], b2["member"]), ("day2", b1["calib"] == "day2_on", b2["day2"])):
                    if (abs(x - y) > 1e-12 if isinstance(x, float) and isinstance(y, float) else x != y): diffs.append("row %d (%s S=%s) bet field %s: build 1 %r, build 2 %r" % (i, rc["city"], rc["S"], name, x, y))
        # aggregates in common
        def agg(o1, o2):
            pairs = []
            a1 = {"dev": o1["dev"], "dev1": o1["dev1"], "dev2": o1["dev2"], "dev_member": o1["descriptive"]["dev_member"], "dev_nonmember": o1["descriptive"]["dev_nonmember"], "dev_calib_day0_1": o1["descriptive"]["dev_calib_day0_1"],
                  "dev_calib_day2_on": o1["descriptive"]["dev_calib_day2_on"], "held": o1["held"], "held_calib_day0_1": o1["held_calib_day0_1"], "held_calib_day2_on": o1["held_calib_day2_on"]}
            d, h = o2["development"], o2["held_out"]
            a2 = {"dev": d["pooled"], "dev1": d["first_half"], "dev2": d["second_half"], "dev_member": d["member"], "dev_nonmember": d["non_member"], "dev_calib_day0_1": d["days_0_1_info"], "dev_calib_day2_on": d["day_2_on_info"],
                  "held": h["pooled"], "held_calib_day0_1": h["days_0_1"], "held_calib_day2_on": h["day_2_on"]}
            for k in a1:
                x, y = a1[k], a2[k]
                for fld, fx, fy in (("n", x["n"], y["n"]), ("voids", x["void"], y["voids"]), ("pf", x["pf"], y["pf"]), ("net", x["net"], y["net"])):
                    same = (fx == fy) or (isinstance(fx, (int, float)) and isinstance(fy, (int, float)) and abs(fx - fy) < 5e-5)
                    if not same: pairs.append("%s.%s: build 1 %r, build 2 %r" % (k, fld, fx, fy))
            v1 = o1["dev_verdict"]; v2 = "CLOSED" if any(d["kills"].values()) else "CONTINUE"
            if v1 != v2: pairs.append("development verdict: build 1 %s, build 2 %s" % (v1, v2))
            hv1 = o1["held_verdict"]; hv2 = h["calibration_kill"]
            if not (hv1.startswith("NO_EVIDENCE") and hv2.startswith("no evidence") and hv1.split("= ")[-1] == hv2.split("= ")[-1]) and not (hv1.startswith("FAIL") and hv2 == "FAIL") and not (hv1 in ("PASS", "FAIL") and hv2 == "passes"):
                pairs.append("held-out calibration verdict: build 1 %s, build 2 %s" % (hv1, hv2))
            return pairs
        diffs += agg(o1, o2)
        report.append("%s: %d rows. mapping notes: %s\n  differences: %s" % (label, len(rows_c), "; ".join(notes) or "none", "NONE" if not diffs else "\n    " + "\n    ".join(diffs)))
    print("\n".join(report))


if __name__ == "__main__": main(*sys.argv[1:4])
