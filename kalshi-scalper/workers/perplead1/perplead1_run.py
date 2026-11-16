#!/usr/bin/env python3
"""PERPLEAD1 part (b) adapter (Desk B, Nov 16 2026; DRAFT, unrun, unsigned): events from perplead1_load, scale step on the first recorded day, the 20 rules, the gates (card specs/PERPLEAD1_CARD.md) and BH over m.
Every figure is 'upper bound, zero latency'. Taker 24 bps round trip is the primary; maker 10 bps is secondary; the next-minute fill is a robustness column (information, not a rule, not in m).
Usage: python3 perplead1_run.py <quote-data checkout> <quote-data commit hash> <PERPETH1M_W8 run> <PERPETH1M_W11 run>  (the loader refuses unless Main's allow lines name both runs)."""
import os, sys, math, statistics, collections, hashlib, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SCORE_SHA = "854b9835ef898e943d48bf1c677acf21b8b6ba1c33a8afd68384867567f10d6d"      # the scorer Auditor B signed
def _pinned_scorer():
    got = hashlib.sha256(open(os.path.join(HERE, "perplead1_score.py"), "rb").read()).hexdigest()
    if got != SCORE_SHA: raise SystemExit("REFUSED: perplead1_score.py has sha256 %s, not the pinned %s" % (got, SCORE_SHA))
_pinned_scorer()
import perplead1_score as P
M_CARRIED = None                       # the Head's single carried number on the day of the read (6,290,660 on Nov 16 print, 7,492,484 from Nov 17); run refuses while None
THETAS = (2, 4, 6, 8, 10); EXITS = ("m60", "m0"); DIRS = ("convergence", "fade"); TAKER, MAKER = 24.0, 10.0
MIN_N, PF_MIN, HALF_MIN, MIN_DAYS, MIN_SPD, MIN_EVENTS, ALPHA, SCALE_TOL, DROP_BPS = 100, 1.3, 1.0, 10, 3.0, 40, 0.05, 0.05, 500.0
RULES = [(t, x, d) for t in THETAS for x in EXITS for d in DIRS]
def scale_step(events):
    """the power of ten s with perp_mid * s close to the implied median, fixed from the FIRST recorded day only; REFUSES if the day's median ratio does not agree within 5% after the scale."""
    day = min(e["day"] for e in events); rs = []
    for e in events:
        if e["day"] != day: continue
        med = P.implied_median(e["strikes"].get("m120", [])); p = e["perp"].get("m120")
        if med is not None and p: rs.append(med / ((p[0] + p[1]) / 2))
    if not rs: raise SystemExit("REFUSED: no event with a median and a perp mid on the first day %s" % day)
    r = statistics.median(rs); s = 10.0 ** round(math.log10(r))
    if abs(r / s - 1) > SCALE_TOL: raise SystemExit("REFUSED: the first day's median ratio %.4f is not within %.0f%% of a power of ten" % (r, 100 * SCALE_TOL))
    return day, s
def day_z(trades):
    by = collections.defaultdict(float)
    for d, n in trades: by[d] += n
    xs = list(by.values())
    if len(xs) < 2: return float("nan")
    sd = statistics.stdev(xs)
    return statistics.mean(xs) / (sd / math.sqrt(len(xs))) if sd > 0 else (float("inf") if statistics.mean(xs) > 0 else float("-inf"))
def pval(z): return 1.0 if z != z else 0.5 * math.erfc(z / math.sqrt(2))
def bh(pvals, m, alpha=ALPHA):
    items = sorted(pvals.items(), key=lambda kv: kv[1]); k = 0
    for i, (_, p) in enumerate(items, 1):
        if p <= alpha * i / m: k = i
    return {key for key, _ in items[:k]}
def halves_pf(trades):
    nets = [n for _, n in sorted(trades, key=lambda t: t[0])]; h = len(nets) // 2
    return P.summary([("x", n) for n in nets[:h]])["pf"], P.summary([("x", n) for n in nets[h:]])["pf"]
def run(events, m_carried=None):
    m_carried = M_CARRIED if m_carried is None else m_carried
    if m_carried is None: raise SystemExit("REFUSED: m_carried is not set (the Head's single carried number)")
    m_total = m_carried + len(RULES)
    day, s = scale_step(events); rep = {"m_total": m_total, "scale_day": day, "scale": s, "rules": {}, "counts": collections.Counter(), "labels": "upper bound, zero latency"}
    kept = []
    for e in events:
        med = P.implied_median(e["strikes"].get("m120", [])); p = e["perp"].get("m120")
        if med is not None and p and abs(P.gap_bps(med, (p[0] + p[1]) / 2, s)) > DROP_BPS: rep["counts"]["scale drop (gap over 500 bps)"] += 1; continue
        e = dict(e); e["scale"] = s; kept.append(e)
    se, va = P.split_dates([e["day"] for e in kept])
    sev = [e for e in kept if e["day"] in se]; vev = [e for e in kept if e["day"] in va]
    rep["search_dates"], rep["validate_dates"], rep["search_events"], rep["validate_events"] = len(se), len(va), len(sev), len(vev)
    s_pass, v_res, v_p = {}, {}, {}
    for (t, x, d) in RULES:
        c = collections.Counter(); st = P.score_rule(sev, t, x, d, TAKER, c); vt = P.score_rule(vev, t, x, d, TAKER, c)
        ss, sv = P.summary(st), P.summary(vt); h1, h2 = halves_pf(st)
        rob = P.summary(P.score_rule(sev, t, x, d, TAKER, collections.Counter(), shift=1))
        mk = P.summary(P.score_rule(sev, t, x, d, MAKER, collections.Counter()))
        sdays = len(se) or 1
        ok_s = ss["n"] >= MIN_N and ss["pf"] >= PF_MIN and h1 >= HALF_MIN and h2 >= HALF_MIN and ss["n"] / sdays >= MIN_SPD and ss["n"] >= MIN_EVENTS
        rep["rules"][(t, x, d)] = {"search": ss, "validate": sv, "h1": h1, "h2": h2, "robust_next_minute": rob, "maker_pf": mk["pf"], "gross_edge_bps": ss["mean"] + TAKER if ss["n"] else float("nan"), "margin": P.margin_print(ss["mean"]) if ss["n"] else None, "search_pass": ok_s}
        if ok_s: s_pass[(t, x, d)] = (st, vt)
    for k, (st, vt) in s_pass.items():
        sv = P.summary(vt); days = len({dd for dd, _ in st} | {dd for dd, _ in vt})
        if sv["n"] >= MIN_N and sv["pf"] >= PF_MIN and days >= MIN_DAYS and sv["n"] >= MIN_EVENTS: v_res[k] = sv; v_p[k] = pval(day_z(vt))
    keep = bh(v_p, m_total)
    rep["search_passes"], rep["validate_passes"], rep["survivors"] = len(s_pass), len(v_res), sorted(keep)
    return rep
def header(rep): return "quote-data %s | runs %s | m_total %d | scale %g (first day %s) | rules %d | search events %d validate events %d | %s" % (rep.get("quote_data", "unset"), ", ".join(rep.get("runs", [])) or "unset", rep["m_total"], rep["scale"], rep["scale_day"], len(RULES), rep["search_events"], rep["validate_events"], rep["labels"])
def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    import perplead1_load as L
    if not re.fullmatch(r"[0-9a-f]{7,40}", a[1]): raise SystemExit("REFUSED: the second argument must be the quote-data commit hash")
    ev, cnt = L.load(a[0], a[2:])
    rep = run(ev); rep["quote_data"] = a[1]; rep["runs"] = [os.path.basename(os.path.dirname(os.path.abspath(r))) + "/" + L.check_run_name(r) for r in a[2:]]
    print(header(rep)); print("loader counts:", dict(cnt)); print("scorer counts:", dict(rep["counts"]))
    for k in sorted(rep["rules"]):
        r = rep["rules"][k]; print("theta %d exit %s %s | S n %d days %d mean %.2f pf %.3f | h1 %.3f h2 %.3f | V n %d pf %.3f | gross %.2f | maker pf %.3f | next-minute n %d pf %.3f | pass %s" % (
            k[0], k[1], k[2], r["search"]["n"], r["search"]["days"], r["search"]["mean"], r["search"]["pf"], r["h1"], r["h2"], r["validate"]["n"], r["validate"]["pf"], r["gross_edge_bps"], r["maker_pf"], r["robust_next_minute"]["n"], r["robust_next_minute"]["pf"], r["search_pass"]))
    print("search passes %d, validate bar passes %d, survivors %s" % (rep["search_passes"], rep["validate_passes"], rep["survivors"] or "none"))
if __name__ == "__main__": main()
