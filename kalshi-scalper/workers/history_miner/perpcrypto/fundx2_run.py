"""fundx2_run.py: the FUNDX2 price steps (History Miner, Nov 16, 2026): GATE (decision counts only) and SCORE. Rules: FUNDX2_RUN_RULES_NOV16.md; card FUNDX2_CARD_NOV16.md.
  python3 -I fundx2_run.py gate  <out FUNDX2_GATE.json>  --funding F --snap S1 S2 ... --btc RUNFOLDER
  python3 -I fundx2_run.py score <FUNDX2_GATE.json> <its sha256>  --funding F --snap S1 S2 ... --btc RUNFOLDER
It refuses unless ONE allow line carries the mark, 'fundx2_run.py', the sha256 of this script, perps_crypto_run.py, perps_crypto_load.py, perps_crypto_events.py, fundx2_events.py and EVERY source. No SEARCH trade is built (only VALIDATE prints trade).
GATE prints counts only; SCORE refuses unless the committed gate file's sha256 matches and scores only the cells that passed."""
import calendar, collections, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import perps_crypto_load as L, perps_crypto_run as R, perps_crypto_events as E, fundx2_events as F
ALLOW_MARK = L.ALLOW_MARK
NAMES = ("KXBTCPERP", "KXETHPERP", "KXSOLPERP", "KXXRPPERP", "KXDOGEPERP", "KXHYPEPERP")
GATE_DAYS = [calendar.timegm((2026, 10, 21, 0, 0, 0)) + 86400 * i for i in range(7)]         # the first 7 calendar days of price coverage for all six names
GATE_RATE = 3.0
HEADER = ["many cuts are 0 because of the deadband: for those names 'extreme' means any non-zero print of that sign; DOGE and SOL have identical 5 and 10 percent cells (counted as registered in m)",
          "VALIDATE extremes run far above the nominal 5 or 10 percent (up to 94 of 189 for SOL): a regime shift, the cells are not tails there",
          "BTC is the only name with prices before 2026-10-21 and is printed APART; its candles were already read for CFRTI-K's lead/lag table (seen data before 2026-10-21)",
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


def score(rows, prints, gate):
    out = {}
    for cell in F.FUNDX2_CELLS:
        key = "|".join(str(x) for x in cell)
        if not gate[key]["passes"]:
            out[key] = {"dropped": "below rate gate (counts only, outcomes not read)", "rate_a_day": gate[key]["rate_a_day"]}; continue
        tr = decisions(rows, prints, cell); btc = [t for t in tr if t["ticker"] == "KXBTCPERP"]; oth = [t for t in tr if t["ticker"] != "KXBTCPERP"]
        out[key] = {"all_six": E.summarise(tr), "btc_apart": E.summarise(btc), "other_five": E.summarise(oth), "n_by_ticker": dict(collections.Counter(t["ticker"] for t in tr)),
                    "trade_days": len({t["trade"]["entry_ts"] // 86400 for t in tr}), "rate_a_day_gate": gate[key]["rate_a_day"]}
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
    rows, prints, cnt = load(a["funding"][0], a["snap"], a["btc"][0])
    if mode == "gate":
        g = gate_counts(rows, prints)
        open(args[0], "w", encoding="utf-8").write(json.dumps({"gate_days": GATE_DAYS, "rate_gate": GATE_RATE, "cells": g, "load_counts": dict(cnt)}, indent=1, sort_keys=True) + "\n")
        return sha(args[0])
    if mode == "score":
        return json.dumps({"header": HEADER, "cells": score(rows, prints, json.load(open(args[0]))["cells"])}, indent=1, sort_keys=True)
    raise SystemExit("usage: gate|score")


if __name__ == "__main__":
    mode = sys.argv[1]; a = collections.defaultdict(list); pos = []; k = None
    for x in sys.argv[2:]:
        if x.startswith("--"): k = x[2:]
        elif k is None: pos.append(x)
        else: a[k].append(x)
    print(run(mode, pos, a))
