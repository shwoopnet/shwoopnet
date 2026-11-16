"""ENGINE1 shadow rescore (Desk A, Nov 16 2026): REPORT ONLY. Takes the 190 rules of run 2's validate_bar_list (no new rule is tried, m is unchanged) and re-scores each one on its VALIDATE phase with the audited driver code, to add what the listing lacked: the validate entries, calendar days of the validate window, signals per day, and the net cash at 2c in cents per contract.
Same loader (the Line B1 archive extract) and the same driver functions as run 2; it refuses unless every rescored n, PF at 1c and 2c reproduce the listing to 1e-9.
  python3 -I engine1_shadow_rescore.py <dir holding the two .sqlite.xz extracts> <run2.json> <out.json>"""
import sys, os, json, math, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_extract_load as L, engine1_driver as D, engine1_enum as N, engine1_split as S
def main(base, listing, out):
    lst = json.load(open(listing))["validate_bar_list"]; wa, ca, wp, cp, wn, cn = L.load(base)
    prep = {}
    for series in {x["series"] for x in lst}:
        mk = wa[series]; sh = D.short(series)
        sm = [m for m in mk if S.phase(sh, m["close"]) == "search"]; vm = [m for m in mk if S.phase(sh, m["close"]) == "validate"]
        cuts = {}
        for b in N.BUCKETS:
            sp = [N.cents(c[2] - c[1]) for m in sm for c in m["candles"] if c[0] == m["close"] - b and 0 < c[1] < c[2] < 1]
            cuts[b] = N.spread_cuts(sp) if sp else None
        d0 = S.LAST_SEARCH[sh]; closes = [m["close"] for m in vm]
        import calendar, time
        first = calendar.timegm(time.strptime(d0, "%Y-%m-%d")) + 86400                      # the day after the last SEARCH date
        wdays = (max(closes) - first) / 86400.0 if closes else 0.0                         # calendar days from that day's start to the last validate close
        sclose = [m["close"] for m in sm]; s0 = min(sclose) if sclose else 0; sdays = (max(sclose) - s0) / 86400.0 + 1 if sclose else 0.0       # SEARCH window days: first to last close, inclusive
        prep[series] = (D.groups(vm, cuts), wdays, len(vm), D.groups(sm, cuts), sdays)
    rows = []
    for x in lst:
        g, wdays, nm, gs, sdays = prep[x["series"]]
        filt = tuple(x["filter"]) if x["filter"] else None
        items = g.get((x["bucket"], x["band"], x["side"], filt), [])
        agg, p = D.score_group(items, x["exit"]); a1, a2 = agg[0.01], agg[0.02]
        ok = a1["n"] == x["n"] and abs(a1["pf"] - x["pf_1c"]) < 1e-9 and abs(a2["pf"] - x["pf_2c"]) < 1e-9
        if not ok: sys.exit("REFUSED: the rescore of %s does not reproduce the listing (n %s vs %s)" % (x, a1["n"], x["n"]))
        sitems = gs.get((x["bucket"], x["band"], x["side"], filt), []); sagg, _ = D.score_group(sitems, x["exit"]); sn = sagg[0.01]["n"]
        n = a2["n"]; n1 = a1["n"]; rows.append(dict(x, search_n=sn, search_window_days=round(sdays, 3), search_signals_per_day=(sn / sdays if sdays else 0.0), edge_1c_cents_per_contract=a1["net"] / (n1 * D.CONTRACTS) * 100, net_1c_dollars=a1["net"], dollars_week_5c_1c=(n1 / wdays) * (a1["net"] / (n1 * D.CONTRACTS)) * 5 * 7, dollars_week_5c_2c=(n / wdays) * (a2["net"] / (n * D.CONTRACTS)) * 5 * 7, validate_window_days=round(wdays, 3), signals_per_day=n / wdays, net_2c_dollars=a2["net"], edge_2c_cents_per_contract=a2["net"] / (n * D.CONTRACTS) * 100, pf_2c_check=a2["pf"], whole_cent_entries_note="entries priced at the raw ask"))
    json.dump({"n": len(rows), "rows": rows, "note": "report only; no new rule tried; reproduces run 2's listing to 1e-9"}, open(out, "w"), indent=1)
    print("wrote", out, len(rows))
if __name__ == "__main__":
    if len(sys.argv) != 4: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
