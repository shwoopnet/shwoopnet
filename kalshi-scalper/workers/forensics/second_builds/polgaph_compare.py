#!/usr/bin/env python3
"""Compares the first build's printed lines (Desk B, polgaph.py decide + score, a text file) with this second build's output (lines then JSON, as printed by polgaph_second.py),
figure by figure. usage: python3 -I polgaph_compare.py <their printed lines .txt> <my full output .txt>     It reads printed output only, never the first build's code."""
import sys, re, json
theirs = open(sys.argv[1]).read().split("\n"); t = open(sys.argv[2]).read(); M = json.loads(t[t.index("\n{\n") + 1:]); C = M["counts"]
tot = bad = 0
def cmp(name, a, b):
    """a: their printed tokens, b: my values (ints, or floats compared at the printed precision)"""
    global tot, bad
    for i, (x, y) in enumerate(zip(a, b)):
        tot += 1; x = str(x).rstrip(",;")
        if isinstance(y, int): ok = x.lstrip("+") == str(y)
        elif y is None: ok = x in ("n/a", "none", "None")
        elif y == float("inf"): ok = "inf" in x
        else:
            dp = len(x.split(".")[1]) if "." in x else 0; ok = abs(float(x) - round(y, dp)) < 1e-9
        if not ok: bad += 1; print("DIFFER", name, "item", i, "theirs", x, "mine", y)
    if len(a) != len(b): bad += 1; print("DIFFER", name, "lengths", len(a), len(b))
ST = r"n (\d+), wins (\d+), cash PF (\S+), net (\S+), mean (\S+), event-clustered z (\S+)"
def st(d): return [d["n"], d["wins"], d["pf"] if d["pf"] is not None else None, d["net"], d["mean"], d["z_event_clustered"]]
ints = lambda g: [int(x) for x in g.groups()]
fam = None; seen = set()
for l in theirs:
    l = l.strip()
    g = re.match(r"series answered (\d+) \| markets (\d+) \| with any hourly candle (\d+)", l)
    if g: cmp("lists", g.groups(), [C["series with any settled market in the window"], C["markets"], C["markets with any hourly candle"]]); seen.add("lists"); continue
    g = re.match(r"market-mornings (\d+) \| no look \(a candle missing\) (\d+) \| a candle not two-sided (\d+) \| three two-sided candles (\d+) \| gap of 5c or more (\d+)", l)
    if g: cmp("mornings", g.groups(), [C["market-mornings"], C["no look (an hourly candle missing)"], C["not two-sided at one of the three candles"], C["1. three two-sided candles"], C["2. gap of 5c or more"]]); seen.add("mornings"); continue
    g = re.match(r"left after steady (\d+) \| after band (\d+) \| after spread (\d+) \| after liquid \(qualifying market-mornings\) (\d+) \| decisions, one per event and morning (\d+)", l)
    if g: cmp("steps", g.groups(), [C["left after 3. steady"], C["left after 4. band"], C["left after 5. spread"], C["left after 6. liquid"], C["left after 7. one per event and morning (the event's pick)"]]); seen.add("steps"); continue
    g = re.match(r"(.+?): three two-sided candles (\d+) \| gap of 5c or more (\d+) \| qualifying market-mornings (\d+) \| decisions (\d+)", l)
    if g: d = M["decide_counts_by_family"][g.group(1)]; cmp("decide " + g.group(1), g.groups()[1:], [d.get(k, 0) for k in ("three two-sided candles", "gap of 5c or more", "qualifying market-mornings", "decisions")]); continue
    if l.startswith("counts from the decide step:"):
        d = json.loads(l.split(":", 1)[1]); cmp("fails", [d[k] for k in ("fail_steady", "fail_band", "fail_spread", "fail_liquid")], [C.get("failed " + k, 0) for k in ("3. steady", "4. band", "5. spread", "6. liquid")]); continue
    g = re.match(r"one-way cost, median over (\d+) market-mornings.*?: (\S+) \(the kill line reads this\); cost as paid at the limit, information only: (\S+)", l)
    if g: c = M["one_way_cost"]; cmp("cost", g.groups(), [c["market_mornings"], c["median_ask_minus_mid_plus_fee_at_the_limit"], c["cost_as_paid_at_the_limit_information_only"]]); seen.add("cost"); continue
    g = re.match(r"(.+?): (\d+) market-mornings, (\S+)$", l)
    if g and g.group(1) in M["one_way_cost"]["by_family"]: c = M["one_way_cost"]["by_family"][g.group(1)]; cmp("cost " + g.group(1), g.groups()[1:], [c["market_mornings"], c["median"]]); continue
    g = re.match(r"decisions, one per event and morning (\d+) \| blocked by an open bet on the event (\d+) \| fired (\d+) \| no fill data (\d+) \| not filled (\d+) \| filled on a present candle (\d+) \| filled on an unchanged minute (\d+) \| voids among filled (\d+)", l)
    if g: cmp("fills", g.groups(), [C["left after 7. one per event and morning (the event's pick)"], C.get("blocked: the event holds an earlier filled, unsettled bet", 0), C.get("fired", 0), C.get("no fill data (the minute request was not answered)", 0), C.get("not filled", 0),
                                    C.get("filled on a present candle", 0), C.get("filled on an unchanged minute (no 07:01 candle)", 0), M.get("voids_among_filled", 0)]); seen.add("fills"); continue
    g = re.match(r"(first|second) half: filled (\d+) \| distinct events (\d+) \| series (\d+) \| mornings (\d+)", l)
    if g: k = g.group(1) + " half"; d = M["distinct_among_filled"][k]; cmp("distinct " + k, g.groups()[1:], [M["filled_bets"][k.replace(" ", "_")], d["events"], d["series"], d["mornings"]]); continue
    g = re.match(r"largest number of bets open at once: (\d+)", l)
    if g: cmp("open", g.groups(), [M["largest_number_open_at_once"]]); seen.add("open"); continue
    g = re.match(r"POOLED development: " + ST, l)
    if g: fam = "filled"; cmp("pooled development", g.groups(), st(M["filled"]["development"])); seen.add("pooled"); continue
    g = re.match(r"FAMILY (.+?): decisions (\d+) \| " + ST, l)
    if g: fam = ("by_family", g.group(1)); cmp("family " + g.group(1), g.groups()[1:], [M["decide_counts_by_family"][g.group(1)].get("decisions", 0)] + st(M["by_family"][g.group(1)]["development"])); continue
    if l.startswith("first half:") or l.startswith("second half:"):
        src = M["filled"] if fam == "filled" else M["by_family"][fam[1]]
        for part in l.split(" | "):
            g = re.match(r"(first|second) half: " + ST, part.strip())
            if g: cmp("%s %s half" % (fam, g.group(1)), g.groups()[1:], st(src[g.group(1) + "_half"]))
        continue
    for key, pat in (("filled_on_a_present_candle_only", "fills on a present candle"), ("optimistic_same_candle_fill_information_only", "optimistic, same-candle fill"), ("baseline_gap_under_2c_information_only", "price-matched baseline")):
        g = re.match(r"information only, " + re.escape(pat) + r".*?: " + ST, l)
        if g: cmp(pat, g.groups(), st(M[key]["development"])); seen.add(pat)
    g = re.match(r"information only, voids paid at their settlement value instead: " + ST, l)
    if g: cmp("voids at value", g.groups(), st(M["filled_with_the_settlement_value_paid_for_voids_information_only"])); seen.add("voids at value"); continue
    if l.startswith("POOLING CONDITION:"):
        tot += 1; ok = "does not count" in M["verdict"] and re.search(r"POOLING CONDITION: (.+?) supplies", l).group(1) in M["verdict"]; bad += 0 if ok else 1; seen.add("pooling")
        if not ok: print("DIFFER pooling condition:", l[:120], "| mine:", M["verdict"][:120])
    if l.startswith("VERDICT:"):
        tot += 1; word = next((w for w in ("FALSIFIED", "survives development", "no evidence", "CLOSED on cost") if w in l), None); ok = word is not None and word in M["verdict"]; bad += 0 if ok else 1; seen.add("verdict")
        if "pooled pass does not count" in M["verdict"] and "pooling" not in seen: bad += 1; print("DIFFER: mine applies the pooling condition, theirs does not print it")
        if not ok: print("DIFFER verdict: theirs", l, "| mine", M["verdict"])
missing = {"lists", "mornings", "steps", "cost", "fills", "open", "pooled", "fills on a present candle", "optimistic, same-candle fill", "price-matched baseline", "voids at value", "verdict"} - seen
print("%s: %d figures compared, %d differ%s" % (sys.argv[1].split("/")[-1], tot, bad, "; LINES NOT FOUND in theirs: %s" % sorted(missing) if missing else ""))
