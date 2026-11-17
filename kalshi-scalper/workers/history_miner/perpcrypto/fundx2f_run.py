"""fundx2f_run.py: FUNDX2-F forward GATE and SCORE (History Miner, 2026-11-17). Card FUNDX2F_CARD_NOV17.md. Same steps and statistics as fundx2_run.py 44a07e96 (imported: cluster_stats, bh_pass, bar_flags, expected_m, HEADER);
differences: forward loader and runner (perps_crypto_load_f.py, perps_crypto_run_f.py), hourly snapshot rows only (no BTC candle run), the cut points from the committed FUNDX2_THRESHOLDS.json (its sha256 is pinned), the gate days Nov 17 to 23.
  python3 -I fundx2f_run.py gate  <out FUNDX2F_GATE.json>  --thresholds T.json --funding F1 F2 ... --snap S1 S2 ...
  python3 -I fundx2f_run.py score <FUNDX2F_GATE.json> <its sha256> <m_total>  --thresholds T.json --funding F1 F2 ... --snap S1 S2 ...
Refuses unless ONE allow line carries the mark, 'fundx2f_run.py', 'perps_crypto_run_f.py' and the sha256 of this script, perps_crypto_run_f.py, perps_crypto_load_f.py, perps_crypto_events.py, fundx2_events.py, fundx2f_events.py, fundx2_run.py, the thresholds file and EVERY source."""
import calendar, collections, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import perps_crypto_load_f as L, perps_crypto_run_f as R, perps_crypto_events as E, fundx2_events as F, fundx2f_events as FF, fundx2_run as X
NAMES = X.NAMES
GATE_DAYS = [calendar.timegm((2026, 11, 17, 0, 0, 0)) + 86400 * i for i in range(7)]


def sha(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def build_rows(out):
    return {tk: v for tk, v in ((tk, list(out["snapshots"].get(tk, []))) for tk in NAMES) if v}


def gate_counts(rows, prints, doc):
    res = {}
    for cell in FF.FUNDX2F_CELLS:
        tr = FF.fundx2f_trades(rows, prints, doc, cell)
        n = sum(1 for t in tr if GATE_DAYS[0] <= t["trade"]["entry_ts"] < GATE_DAYS[-1] + 86400)
        res["|".join(str(x) for x in cell)] = {"trades_first_7_days": n, "rate_a_day": n / 7.0, "passes": n / 7.0 >= X.GATE_RATE}
    return res


def score(rows, prints, doc, gate, m_total):
    out = {}; res = {}
    for cell in FF.FUNDX2F_CELLS:
        key = "|".join(str(x) for x in cell)
        if not gate[key]["passes"]:
            out[key] = {"dropped": "below rate gate (counts only, outcomes not read)", "rate_a_day": gate[key]["rate_a_day"]}; continue
        tr = FF.fundx2f_trades(rows, prints, doc, cell); btc = [t for t in tr if t["ticker"] == "KXBTCPERP"]; oth = [t for t in tr if t["ticker"] != "KXBTCPERP"]
        res[key] = {"all": E.summarise(tr), "stats": X.cluster_stats(tr)}
        out[key] = {"all_six": res[key]["all"], "btc_apart": E.summarise(btc), "other_five": E.summarise(oth), "n_by_ticker": dict(collections.Counter(t["ticker"] for t in tr)),
                    "trade_days": len({t["trade"]["entry_ts"] // 86400 for t in tr}), "rate_a_day_gate": gate[key]["rate_a_day"], "z_p_all_six": res[key]["stats"]}
    ranked = {k: v["stats"]["p"] for k, v in res.items() if v["stats"]["n"] >= 48}
    ok = X.bh_pass(ranked, m_total)
    for k, v in res.items():
        out[k]["bh_ranked"] = k in ranked; out[k]["bar"] = X.bar_flags(v["all"], v["stats"], k in ok)
    out["_bh"] = {"m_total": m_total, "alpha": X.ALPHA, "ranked_cells": len(ranked), "rule": "BH step-up over the all-six pooled cells with n >= 48"}
    return out


def need_hashes(sources):
    base = [sha(os.path.abspath(__file__)), R.self_sha(), L.self_sha()] + [sha(os.path.join(HERE, f)) for f in ("perps_crypto_events.py", "fundx2_events.py", "fundx2f_events.py", "fundx2_run.py")]
    return base + [sha(p) for k, p in sources]


def refuse_unless_allowed(sources):
    need = need_hashes(sources)
    try:
        text = open(L.ALLOW_FILE, encoding="utf-8").read()
    except OSError:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if L.ALLOW_MARK in line and "fundx2f_run.py" in line and "perps_crypto_run_f.py" in line and all(h in line for h in need):
            return
    raise SystemExit("REFUSED: no allow line names fundx2f_run.py with the sha256 set %s" % need)


def load(thresholds, fundings, snaps):
    if sha(thresholds) != FF.THRESHOLDS_SHA256:
        raise SystemExit("REFUSED: the thresholds file is not the committed FUNDX2_THRESHOLDS.json")
    sources = [("csv", thresholds)] + [("csv", p) for p in fundings] + [("csv", p) for p in snaps]
    refuse_unless_allowed(sources)
    out, cnt = R.load_all(snap=snaps, funding=fundings)
    return build_rows(out), out["funding"], json.load(open(thresholds)), cnt


def run(mode, args, a):
    if mode == "score":
        gp, gsha = args[0], args[1]
        if not os.path.exists(gp) or sha(gp) != gsha:
            raise SystemExit("REFUSED: the committed gate file is missing or its sha256 differs")
        if int(args[2].replace(",", "")) != X.expected_m():
            raise SystemExit("REFUSED: m_total %s is not the Head's figure for this run date (%d)" % (args[2], X.expected_m()))
    rows, prints, doc, cnt = load(a["thresholds"][0], a["funding"], a["snap"])
    if mode == "gate":
        g = gate_counts(rows, prints, doc)
        open(args[0], "w", encoding="utf-8").write(json.dumps({"gate_days": GATE_DAYS, "rate_gate": X.GATE_RATE, "cells": g, "load_counts": dict(cnt)}, indent=1, sort_keys=True) + "\n")
        return sha(args[0])
    if mode == "score":
        return json.dumps({"header": X.HEADER, "cells": score(rows, prints, doc, json.load(open(args[0]))["cells"], int(args[2].replace(",", "")))}, indent=1, sort_keys=True)
    raise SystemExit("usage: gate|score")


if __name__ == "__main__":
    mode = sys.argv[1]; a = collections.defaultdict(list); pos = []; k = None
    for x in sys.argv[2:]:
        if x.startswith("--"): k = x[2:]
        elif k is None: pos.append(x)
        else: a[k].append(x)
    print(run(mode, pos, a))
