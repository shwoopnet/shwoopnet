"""Compares the first build's printed lines (Desk B, voidsnap.py, a text file) with this second build's output (lines then JSON, as printed by voidsnap_second.py measure), figure by figure.
usage: python3 -I voidsnap_compare.py <their printed lines .txt> <my full output .txt>     It reads printed output only, never the first build's code."""
import sys, re, json
theirs = open(sys.argv[1]).read().split("\n"); t = open(sys.argv[2]).read(); mine = json.loads(t[t.index("\n{\n") + 1:])
T = []; sec = None
def add(k, v): T.append((k, v))
names = {"REGISTERED": "registered carry", "carry of at most 60": "60 minute carry", "no carry": "no carry"}
for l in theirs:
    l = l.strip()
    g = re.match(r"events in the window (\d+) \| void (\d+) \| played (\d+) \| pairs made (\d+) \| dropped: not_two_contracts (\d+), no_close_time (\d+), no_ticker_clock (\d+), outside_window (\d+), neither_void_nor_played (\d+)", l)
    if g: add("head", [int(x) for x in g.groups()]); continue
    g = re.match(r"sampled voids (\d+) \| matched played events (\d+) \| base rate of voids in the window (\S+) \((\d+) of (\d+)\)", l)
    if g: add("base", [int(g.group(1)), int(g.group(2)), g.group(3), int(g.group(4)), int(g.group(5))]); continue
    g = re.match(r"voids with no settlement value listed (\d+) \| voids with no window (\d+) \| voids with any candle (\d+) \| played with any candle (\d+)", l)
    if g: add("cov", [int(x) for x in g.groups()]); continue
    if l.startswith("---"): sec = next(v for k, v in names.items() if k in l); continue
    g = re.match(r"Q1 reference (.+?): available in (\d+) of (\d+) voids \| within 1c of the settlement value (\d+) \| within 3c (\d+)", l)
    if g: add((sec, "Q1", g.group(1).replace(" mid", "")), [int(g.group(i)) for i in (2, 4, 5)]); continue
    g = re.match(r"Q2 voids with a run of 5 buyable minutes or more: (\d+) of \d+ \(with the ask also at 15c to 64c: (\d+)\) \| first minute of the first run against the start, quartiles: (.+?) \| buyable minutes in all (\d+) \| median shortfall (\S+) \| one-way cost, median (\S+)", l)
    if g: add((sec, "Q2"), [int(g.group(1)), int(g.group(2)), g.group(3).replace(" ", ""), int(g.group(4)), g.group(5), g.group(6)]); continue
    g = re.match(r"(D\d): flags (\d+) of \d+ voids and (\d+) of \d+ matched played events \| implied share of voids among flagged (\S+) \(line 2, 0.30 or more: (\w+)\)", l)
    if g: det = g.group(1); add((sec, det, "flags"), [int(g.group(2)), int(g.group(3)), g.group(4), g.group(5) == "met"]); continue
    g = re.match(r"line 1: flagged voids with 5 buyable minutes in a row at or after its minute: (\d+) \(40 or more: (\w+)\); with the ask at 15c to 64c, information only: (\d+)", l)
    if g: add((sec, det, "line1"), [int(g.group(1)), g.group(2) == "met", int(g.group(3))]); continue
    g = re.match(r"line 3: best allowed reference (\S+) \(the best of (\d)\), within 3c in (\S+) of all sampled voids \(0.70 or more: (\w+)\)", l)
    if g: add((sec, det, "line3"), [int(g.group(2)), g.group(3), g.group(4) == "met"]); add((sec, det, "line3 name (may differ on a tie)"), [g.group(1)]); continue
    g = re.match(r"(D\d) passes its three lines under: (.+?) \[", l + " [")
    if g: add(("passes", g.group(1)), [g.group(2).strip()]); continue
    if l.startswith("READING:"): add("reading", [next(x for x in ("worth a rule", "depends on the carry", "CLOSED") if x in l)])
M = {}
b = mine["base"]; d = mine["drops"]
M["head"] = [b["void"] + b["played"], b["void"], b["played"], mine["sampled_voids"]] + [d[k] for k in ("not_two_contracts", "no_close_time", "no_ticker_clock", "outside_window", "neither_void_nor_played")]
M["base"] = [mine["sampled_voids"], mine["sampled_played"], "%.4f" % mine["base_rate"], b["void"], b["void"] + b["played"]]
q2r = mine["carries"]["registered carry"]["question_2"]
M["cov"] = [mine["void_contracts_with_no_settlement_value"], mine["events_with_no_window"]["voids"], q2r["voids_with_any_candle_in_the_window"], q2r["played_with_any_candle_in_the_window"]]
M["cov_alt"] = [mine["void_contracts_with_no_settlement_value"], mine["events_with_no_window"]["voids"], q2r["voids_with_any_candle_returned"], q2r["played_with_any_candle_returned"]]
passes = {}
for cn, c in mine["carries"].items():
    for k, v in c["question_1"].items(): M[(cn, "Q1", k)] = [v["voids_with_it"], v["within_1c"], v["within_3c"]]
    q = c["question_2"]; fr = q["first_run_minute_vs_S"]["quartiles_by_position"]
    M[(cn, "Q2")] = [q["voids_with_a_run_of_5_or_more"], q["voids_with_a_run_of_5_or_more_with_the_ask_15c_to_64c"], ",".join(str(x) for x in fr) if fr else "n/a", q["buyable_side_minutes"],
                     "n/a" if q["median_shortfall"] is None else "%.4f" % q["median_shortfall"], "n/a" if q["one_way_cost_median"] is None else "%.4f" % q["one_way_cost_median"]]
    for n, x in c["detectors"].items():
        M[(cn, n, "flags")] = [x["voids_flagged"], x["played_flagged"], "%.3f" % x["implied_share_of_voids"], x["line_2"]]
        M[(cn, n, "line1")] = [x["line_1_count"], x["line_1"], x["line_1_count_with_ask_15c_to_64c_information_only"]]
        M[(cn, n, "line3")] = [x["line_3_best_of"], "%.3f" % x["line_3_share"], x["line_3"]]; M[(cn, n, "line3 name (may differ on a tie)")] = [x["line_3_best_reference"]]
        if x["all_three"]: passes.setdefault(n, []).append(cn)
M["reading"] = [next(x for x in ("worth a rule", "depends on the carry", "CLOSED") if x in mine["verdict"])]
tot = bad = 0; soft = 0
for k, v in T:
    if k[0] == "passes": 
        mm = passes.get(k[1], []); tt = v[0]
        tl = tt.lower(); theirs_set = set() if tl == "no carry rule" else {n for n, w in (("registered carry", "registered"), ("60 minute carry", "at most 60"), ("no carry", "only, no carry")) if w in tl or (n == "no carry" and tl.endswith("no carry") and "registered" not in tl and "60" not in tl)}
        ok = theirs_set == set(mm)
        tot += 1; bad += 0 if ok else 1
        if not ok: print("DIFFER", k, "theirs", tt, "mine", mm)
        continue
    m = M.get(k)
    if k == "cov" and m != v and M["cov_alt"] == v: m = M["cov_alt"]; print("note: 'any candle' matches on candles RETURNED, not candles inside the window")
    if isinstance(k, tuple) and "name" in k[-1]:
        soft += 0 if m == v else 1; continue
    for i, (x, y) in enumerate(zip(v, m if m is not None else [None] * len(v))):
        tot += 1
        if x != y: bad += 1; print("DIFFER", k, "item", i, "theirs", x, "mine", y)
print("%s: %d figures compared, %d differ; reference names that differ on a tie: %d; theirs %d parsed entries" % (sys.argv[1].split("/")[-1], tot, bad, soft, len(T)))
