"""Runs the lanes 1 and 6 engine on the Testing Desk's invented fixture (lanes16_fixture_second.json.gz, sha256 4d300f7b...: 13 names, minute candles, funding every 8 h, page max 10.0 for every name) and writes my lines in the same column order as my own fixtures (without opening the Testing Desk's lines). Carried m 6,290,660; baskets are the engine's own three (semis, megacap, energy) on the 13 names.
  python3 -I engine1_perps_lanes_on_testing_fixture.py <fixture.json.gz> <out.json>"""
import sys, os, json, gzip, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_perps_lanes as L
def main(src, out):
    d = json.load(gzip.open(src)); cand = {n: {int(t): tuple(c) for t, c in v.items()} for n, v in d["data"].items()}; fund = {n: {int(t): r for t, r in v.items()} for n, v in d["funding"].items()}
    rep = L.evaluate_lanes(cand, fund, lambda n: 10.0, 6290660); lines = []
    for o in rep["rules"]:
        for c, v in sorted(o["columns"].items()):
            ex = o["exit"]; lines.append([o["signal"], ex["kt"], ex["ks"], ex["T"], c, v["n"], v["signals"], v["filled"], v["pf_primary"], v["pf_second"], v["price_terms"]["net_bp_per_trade"], v["margin_view"]["50%"]["mean_pct_of_margin_per_trade"], v["margin_view"]["50%"]["trades_without_page_max_not_shown"], v["gate"], v["maker_only_flag"], v["candidate_blocked_no_page_max"], (o["bh_survivor_taker"] if c == "TT" else None)])
    json.dump({"fixture_sha256": hashlib.sha256(open(src, "rb").read()).hexdigest(), "header": rep["header"], "kept_baskets": rep["kept_baskets"], "dropped": rep["dropped"], "trading_days": rep["trading_days"], "ticks": rep["ticks"], "columns": ["signal", "kt", "ks", "T", "column", "n", "signals", "filled", "pf_h0.0002", "pf_h0.0005", "net_bp_per_trade", "pct_margin_50", "trades_without_page_max", "gate", "maker_only", "candidate_blocked", "bh_survivor_TT"], "lines": lines}, open(out, "w"), default=str)
    print(hashlib.sha256(open(out, "rb").read()).hexdigest(), len(lines), "lines;", rep["kept_baskets"], rep["dropped"][:2], "days", len(rep["trading_days"]))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])
