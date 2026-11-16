"""Second compare fixture for lanes 1 and 6 (Desk A, Nov 16 2026), built so that the GATE, BH, MAKER_ONLY and candidate_blocked_no_page_max are exercised: same four invented names as fixture 1 (two page-max tables on the same candles: all4 pins all four names, no_ddd leaves KXDDDPERP unpinned) but a stronger mean-reverting idiosyncratic part (phi 0.9, sd 0.004 a minute), seed 1, so some rules pass the gate in TT, some only in a maker column, and some trade the name without a page max. Same procedure: INPUT first; with 'mine' also my output lines (held under a sha).
  python3 -I engine1_perps_lanes_fixture2.py <out dir> [mine]"""
import sys, os, json, math, random, calendar, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import engine1_perps as P, engine1_perps_lanes as L
NAMES = ("KXAAAPERP", "KXBBBPERP", "KXCCCPERP", "KXDDDPERP"); LEV3 = {"KXAAAPERP": 4.0, "KXBBBPERP": 8.0, "KXCCCPERP": 20.0}; LEV4 = dict(LEV3, KXDDDPERP=5.0)      # two page-max tables on the SAME candles: "all4" (every name pinned) and "no_ddd" (KXDDDPERP unpinned)
def build():
    rnd = random.Random(1); cand = {n: {} for n in NAMES}; fund = {n: {} for n in NAMES}
    days = [P.et_day0(calendar.timegm((2026, 11, 9 + i, 17, 0, 0))) for i in range(5)]
    f = 0.0; idio = {n: 0.0 for n in NAMES}; px = {n: 100.0 * (1 + 0.1 * i) for i, n in enumerate(NAMES)}
    for d in days:
        for k in range(9 * 60 + 31, 16 * 60 + 1):
            f += rnd.gauss(0, 0.0004)
            for n in NAMES:
                idio[n] = 0.9 * idio[n] + rnd.gauss(0, 0.004)
                p = px[n] * math.exp(f * 0.5 + idio[n] * 1.0); t = d + k * 60; h = max(0.2e-4 * p, 0.005)
                cand[n][t] = (round(p - h, 4), round(p + h, 4))
        for n in NAMES: fund[n][d + 16 * 3600] = 0.0
    return cand, fund
def main(out, mine=False):
    cand, fund = build()
    inp = {"names": NAMES, "basket": "b", "candles": {n: {str(t): list(c) for t, c in sorted(cand[n].items())} for n in NAMES}, "funding": {n: {str(t): r for t, r in sorted(fund[n].items())} for n in NAMES}, "page_max_tables": {"all4": LEV4, "no_ddd": LEV3}, "m_carried": 6290660, "min_days": 5, "rules": "ENGPERPS_LANES_1_6_SPEC_NOV16.md (A1 to A3)"}
    p = os.path.join(out, "LANES_FIXTURE2_INPUT.json"); json.dump(inp, open(p, "w")); print("input", hashlib.sha256(open(p, "rb").read()).hexdigest())
    if mine:
        lines = []; summ = []
        for tab, lev in (("all4", LEV4), ("no_ddd", LEV3)):
            rep = L.evaluate_lanes(cand, fund, lambda n, lev=lev: lev.get(n), 6290660, baskets={"b": NAMES}, min_days=5); ls = []
            for o in rep["rules"]:
                for c, v in sorted(o["columns"].items()):
                    ex = o["exit"]; ls.append([tab, o["signal"], ex["kt"], ex["ks"], ex["T"], c, v["n"], v["signals"], v["filled"], v["pf_primary"], v["pf_second"], v["price_terms"]["net_bp_per_trade"], v["margin_view"]["50%"]["mean_pct_of_margin_per_trade"], v["margin_view"]["50%"]["trades_without_page_max_not_shown"], v["gate"], v["maker_only_flag"], v["candidate_blocked_no_page_max"], (o["bh_survivor_taker"] if c == "TT" else None)])
            lines += ls; summ.append((tab, sum(1 for l in ls if l[14]), sum(1 for l in ls if l[14] and l[5] == "TT"), sum(1 for l in ls if l[15]), sum(1 for l in ls if l[16]), sum(1 for l in ls if l[17])))
        q = os.path.join(out, "LANES_FIXTURE2_MINE.json"); json.dump({"header": rep["header"], "columns": ["table", "signal", "kt", "ks", "T", "column", "n", "signals", "filled", "pf_h0.0002", "pf_h0.0005", "net_bp_per_trade", "pct_margin_50", "trades_without_page_max", "gate", "maker_only", "candidate_blocked", "bh_survivor_TT"], "lines": lines}, open(q, "w"), default=str)
        print("mine", hashlib.sha256(open(q, "rb").read()).hexdigest(), len(lines), "lines"); print("(table, gate passes, TT passes, maker only, blocked, bh survivors):", summ)
if __name__ == "__main__":
    if len(sys.argv) not in (2, 3): sys.exit(__doc__)
    main(sys.argv[1], len(sys.argv) == 3)
