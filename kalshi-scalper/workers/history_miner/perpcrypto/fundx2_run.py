"""fundx2_run.py: the FUNDX2 price steps (History Miner, Nov 16, 2026): GATE (decision counts only) and SCORE. Rules: FUNDX2_RUN_RULES_NOV16.md; card FUNDX2_CARD_NOV16.md.
  python3 -I fundx2_run.py gate  <out FUNDX2_GATE.json>  --funding F --snap S1 S2 ... --btc RUNFOLDER
  python3 -I fundx2_run.py score <FUNDX2_GATE.json> <its sha256> <m_total>  --funding F --snap S1 S2 ... --btc RUNFOLDER
It refuses unless ONE allow line carries the mark, 'fundx2_run.py', the sha256 of this script, perps_crypto_run.py, perps_crypto_load.py, perps_crypto_events.py, fundx2_events.py and EVERY source. No SEARCH trade is built (only VALIDATE prints trade).
GATE prints counts only; SCORE refuses unless the committed gate file's sha256 matches and scores only the cells that passed."""
import calendar, collections, hashlib, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import perps_crypto_load as L, perps_crypto_run as R, perps_crypto_events as E, fundx2_events as F
ALLOW_MARK = L.ALLOW_MARK
NAMES = ("KXBTCPERP", "KXETHPERP", "KXSOLPERP", "KXXRPPERP", "KXDOGEPERP", "KXHYPEPERP")
GATE_DAYS = [calendar.timegm((2026, 10, 21, 0, 0, 0)) + 86400 * i for i in range(7)]         # the first 7 calendar days of price coverage for all six names
GATE_RATE = 3.0
HEADER = ["many cuts are 0 because of the deadband: for those names 'extreme' means any non-zero print of that sign; DOGE and SOL have identical 5 and 10 percent cells (counted as registered in m)",
          "VALIDATE extremes run far above the nominal 5 or 10 percent (up to 94 of 189 for SOL): a regime shift, the cells are not tails there",
          "BTC is the only name with prices before 2026-10-21 and is printed APART; its candles were already read for CFRTI-K's lead/lag table (seen data before 2026-10-21)",
          "BH uses the all-six pooled cell of each gated cell (BTC apart and the other five are printed apart, not ranked); m_total is passed on the command line and refused unless it equals the Head's figure for the run date",
          "bar: PF 1.3+ at taker with the 0.02 percent haircut, both halves 1.0+, PF 1.0+ at 0.05 percent, n 100+, 10+ trade days, BH over 8 cells; a pass is a candidate only, forward data from 2026-11-17 is the confirmation"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def build_rows(out):
    """BTC: candle rows before 2026-10-21, snapshot rows from then; the other five: snapshots only."""
    rows = {tk: list(out["snapshots"].get(tk, [])) for tk in NAMES}
    rows["KXBTCPERP"] = sorted([r for r in out["btc"] if r[0] < L.SNAP_START] + [r for r in rows["KXBTCPERP"] if r[0] >= L.SNAP_START])
    return {tk: v for tk, v in rows.items() if v}


def decisions(rows, prints, cell):
    return F.fundx2_trades(rows, prints, cell, "validate")


def gate_counts(rows, prints):
    res = {}
    for cell in F.FUNDX2_CELLS:
        tr = decisions(rows, prints, cell)
        n = sum(1 for t in tr if GATE_DAYS[0] <= t["trade"]["entry_ts"] < GATE_DAYS[-1] + 86400)
        res["|".join(str(x) for x in cell)] = {"trades_first_7_days": n, "rate_a_day": n / 7.0, "passes": n / 7.0 >= GATE_RATE}
    return res


M_BEFORE, M_FROM, M_SWITCH = 6290676, 7492500, calendar.timegm((2026, 11, 17, 0, 0, 0))     # carried 6,290,660 or 7,492,484 plus the 16 own (Auditor B)
ALPHA = 0.05


def expected_m(now=None):
    return M_BEFORE if (time.time() if now is None else now) < M_SWITCH else M_FROM


def cluster_stats(tr):
    """Per trade return at taker, haircut 0.02 percent, funding booked (E.net). Day-clustered one-sided z and p, unit = the UTC entry day:
    mu = mean return; V = sum over days of (sum of (r - mu) in the day)^2; z = mu / (sqrt(V) / N); p = 1 - Phi(z) = 0.5 erfc(z / sqrt 2)."""
    rs = [(t["trade"]["entry_ts"] // 86400, E.net(t["trade"], E.FEE_TAKER, E.HAIRCUTS[0], t.get("funding", 0.0))) for t in tr]
    n = len(rs); days = {d for d, _ in rs}
    if n < 2 or len(days) < 2:
        return {"n": n, "trade_days": len(days), "mean_return": (sum(r for _, r in rs) / n) if n else None, "z": None, "p": 1.0}
    mu = sum(r for _, r in rs) / n; by = collections.defaultdict(float)
    for d, r in rs:
        by[d] += r - mu
    v = sum(x * x for x in by.values())
    if v <= 0:
        return {"n": n, "trade_days": len(days), "mean_return": mu, "z": None, "p": 1.0 if mu <= 0 else 0.0}
    z = mu / (math.sqrt(v) / n)
    return {"n": n, "trade_days": len(days), "mean_return": mu, "z": z, "p": 0.5 * math.erfc(z / math.sqrt(2))}


def bh_pass(pvals, m_total, alpha=ALPHA):
    """Standard BH step-up: rank the p values of the cells that have n >= 48 ascending; the largest k with p_(k) <= alpha k / m_total rejects ranks 1..k. -> set of keys that pass."""
    order = sorted(pvals, key=lambda k: pvals[k]); kmax = 0
    for i, k in enumerate(order, 1):
        if pvals[k] <= alpha * i / m_total:
            kmax = i
    return set(order[:kmax])


def bar_flags(summ, st, bh_ok):
    """The bar as written, unrounded: n >= 100, trade days >= 10, PF >= 1.3 at the 0.02 percent haircut with both halves >= 1.0, PF >= 1.0 at 0.05 percent, and a BH pass."""
    a, b = summ["taker_h2"], summ["taker_h5"]
    ge = lambda x, y: x is not None and x >= y
    f = {"n_ok": st["n"] >= 100, "days_ok": st["trade_days"] >= 10, "pf02_ok": ge(a["pf"], 1.3), "halves_ok": ge(a["half1"], 1.0) and ge(a["half2"], 1.0), "pf05_ok": ge(b["pf"], 1.0), "bh_ok": bh_ok}
    f["passes"] = all(f.values())
    return f


def score(rows, prints, gate, m_total):
    out = {}; res = {}
    for cell in F.FUNDX2_CELLS:
        key = "|".join(str(x) for x in cell)
        if not gate[key]["passes"]:
            out[key] = {"dropped": "below rate gate (counts only, outcomes not read)", "rate_a_day": gate[key]["rate_a_day"]}; continue
        tr = decisions(rows, prints, cell); btc = [t for t in tr if t["ticker"] == "KXBTCPERP"]; oth = [t for t in tr if t["ticker"] != "KXBTCPERP"]
        res[key] = {"tr": tr, "all": E.summarise(tr), "stats": cluster_stats(tr)}
        out[key] = {"all_six": res[key]["all"], "btc_apart": E.summarise(btc), "other_five": E.summarise(oth), "n_by_ticker": dict(collections.Counter(t["ticker"] for t in tr)),
                    "trade_days": len({t["trade"]["entry_ts"] // 86400 for t in tr}), "rate_a_day_gate": gate[key]["rate_a_day"], "z_p_all_six": res[key]["stats"]}
    ranked = {k: v["stats"]["p"] for k, v in res.items() if v["stats"]["n"] >= 48}
    ok = bh_pass(ranked, m_total)
    for k, v in res.items():
        out[k]["bh_ranked"] = k in ranked; out[k]["bar"] = bar_flags(v["all"], v["stats"], k in ok)
    out["_bh"] = {"m_total": m_total, "alpha": ALPHA, "ranked_cells": len(ranked), "rule": "BH step-up over the all-six pooled cells with n >= 48"}
    return out


def need_hashes(sources):
    return [sha(os.path.abspath(__file__)), R.self_sha(), L.self_sha(), sha(os.path.join(HERE, "perps_crypto_events.py")), sha(os.path.join(HERE, "fundx2_events.py"))] + \
           [sha(os.path.join(p, "manifest.json")) if k == "run" else sha(p) for k, p in sources]


def refuse_unless_allowed(sources):
    need = need_hashes(sources)
    try:
        text = open(L.ALLOW_FILE, encoding="utf-8").read()
    except OSError:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "fundx2_run.py" in line and all(h in line for h in need):
            return
    raise SystemExit("REFUSED: no allow line names fundx2_run.py with the sha256 set %s" % need)


def load(funding, snaps, btc):
    sources = [("csv", funding)] + [("csv", p) for p in snaps] + [("run", btc)]
    refuse_unless_allowed(sources)
    out, cnt = R.load_all(snap=snaps, btc=btc, funding=funding)
    return build_rows(out), out["funding"], cnt


def run(mode, args, a):
    if mode == "score":                                                  # the committed gate file is checked BEFORE any file is opened
        gp, gsha = args[0], args[1]
        if not os.path.exists(gp) or sha(gp) != gsha:
            raise SystemExit("REFUSED: the committed gate file is missing or its sha256 differs")
        if int(args[2].replace(",", "")) != expected_m():
            raise SystemExit("REFUSED: m_total %s is not the Head's figure for this run date (%d)" % (args[2], expected_m()))
    rows, prints, cnt = load(a["funding"][0], a["snap"], a["btc"][0])
    if mode == "gate":
        g = gate_counts(rows, prints)
        open(args[0], "w", encoding="utf-8").write(json.dumps({"gate_days": GATE_DAYS, "rate_gate": GATE_RATE, "cells": g, "load_counts": dict(cnt)}, indent=1, sort_keys=True) + "\n")
        return sha(args[0])
    if mode == "score":
        return json.dumps({"header": HEADER, "cells": score(rows, prints, json.load(open(args[0]))["cells"], int(args[2].replace(",", "")))}, indent=1, sort_keys=True)
    raise SystemExit("usage: gate|score")


if __name__ == "__main__":
    mode = sys.argv[1]; a = collections.defaultdict(list); pos = []; k = None
    for x in sys.argv[2:]:
        if x.startswith("--"): k = x[2:]
        elif k is None: pos.append(x)
        else: a[k].append(x)
    print(run(mode, pos, a))
