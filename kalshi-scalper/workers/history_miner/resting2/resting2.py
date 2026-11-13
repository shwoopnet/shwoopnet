"""V1 (OICORE resting bid) and V2 (EVENT830 resting entry) SECOND BUILD (History Miner, Nov 13, 2026), written from the two registrations alone:
kalshi-scalper/refine_tools/V1_OICORE_RESTING_BID_REGISTRATION.md (fc528cd3) and V2_EVENT830_RESTING_ENTRY_REGISTRATION.md (4221ab37) on claude/refine-live
(564d1656 or later), and the recorder column lists in scripts/record_15m_book.py and scripts/record_nc_book.py on main. v1_resting_score.py was NOT read.
Invented rows only. Where the texts are silent a PROVISIONAL reading is built and listed in AMBIG for the Head of R&D's ruling.

Input:
  signals CSV: ticker, close_ts (epoch s) - one candidate window per line (V1: OICORE trigger windows; V2: listed release windows), built elsewhere
  one or more run folders, each with book.csv, trades.csv and coverage.csv in the recorders' columns (plain or .gz)
Usage: python3 -I resting2.py --version V1|V2 --block dev|fwd <signals.csv> <out.json> <run folder>... [--depth1-marker <file>] [--marker-dir <dir>]
(The clock is the real one; tests pass a clock to run() directly, never through the command line.)"""
import csv, gzip, json, math, os, sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

EPS = 1e-9
CFG = {
    "V1": {"t0_before": 178, "band": (0.05, 0.50), "spread_max": None,
           "dev": ("2026-10-29T22:15:00Z", "2026-11-13T23:59:59Z"), "fwd": ("2026-11-14T00:00:00Z", "2026-12-31T23:59:59Z"), "fwd_read": "2027-01-01T00:00:00Z"},
    "V2": {"t0_before": 180, "band": (0.05, 0.50), "spread_max": 0.10,
           "dev": ("2026-11-12T00:00:00Z", "2026-12-04T23:59:59Z"), "fwd": ("2026-12-10T00:00:00Z", "2026-12-23T23:59:59Z"), "fwd_read": "2026-12-24T00:00:00Z"},
}
CANCEL_BEFORE = 120
MIN_FILLS = 60
AMBIG = [
    "R1 levels: yes_bid_px_1 and no_bid_px_1 are read as each side's BEST bid (the recorder's parse order is not stated in the registrations). YES ask = 1 - no_bid_px_1; NO ask = 1 - yes_bid_px_1; a side's own bid is yes_bid_px_1 or no_bid_px_1. An empty or 0 bid means no bid; a side whose ask needs a missing opposite bid has no ask and is not a candidate.",
    "R2 cheaper side: the side with the lower own ask at t0; a tie (within 1e-9) is not stated: provisional YES.",
    "R3 V2 spread test: YES spread = YES ask - YES bid at t0, both needed; 10c or less inclusive (1e-9). V1 has no spread test.",
    "R4 band: the cheaper side's ask at t0 in [0.05, 0.50] inclusive (1e-9).",
    "R5 t0 and cancel: t0 = the first book row of that ticker with t_recv_ms at or after close minus 178 s (V1) or 180 s (V2); the cancel row = the first with t_recv_ms at or after close minus 120 s; the rest is the open interval (t0 recv, cancel recv). No cancel row: the rest runs to close minus 120 s.",
    "R6 fill (a), trades: created_time strictly after t0's recv and strictly before the cancel time. Buying YES at P fills on a trade with taker_outcome_side 'no' (a taker selling YES) at yes_price < P; buying NO at cost Q fills on taker_outcome_side 'yes' at yes_price > 1 - Q; strict, 1e-9. The registration says 'a taker sold YES' and 'a taker bought YES'; reading the taker side from taker_outcome_side is provisional.",
    "R7 fill (b), book: a book row of the ticker strictly after t0 and strictly before the cancel row whose ask for our side is at or below our price (1e-9).",
    "R8 parent price and fees: taker fill at the ask at t0; per contract pnl = (1 - p - fee) or (-p - fee), fee 0.07 p (1 - p) unrounded at p = the ask; +1c adds 0.01 to the cost (the fee stays at the ask). Version: fill at our bid, fee at 25% (primary), 0% and 100% of 0.07 p (1 - p) at our bid, unrounded.",
    "R9 results: the coverage.csv 'result' of the ticker (yes or no); a window with no such result is counted and left out of every PF (no void rule is stated in these registrations).",
    "R10 blocks: by close_ts, the registration's constants, both ends inclusive as written (through ...T23:59:59Z).",
    "R11 halves: the block's scored windows in close order, split by count, the first half floor(n/2) windows; the comparison in bar (3) is (version PF minus parent PF at +1c) in each half, second not below first.",
    "R12 net per contract-week: block net divided by the number of 7 day blocks from the block start to its end, rounded up; the same denominator for version and parent.",
    "R13 FALSIFIED's 'filled windows' PF' is read as the PARENT's PF on the windows the version filled (+1c), against the parent's PF on the missed windows (+1c).",
    "R14 PF: gross gain over gross loss; inf with no loss; tested unrounded; a set with no bet has no PF and fails any PF line.",
    "R15 guards: V1 dev refuses without the DEPTH1 marker file; each (version, block) runs once (a marker); forward refused before its read date; hm_guard on every path.",
]


def iso(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def iso_any(s):
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s).timestamp()


def rd(folder, name):
    for fn in (name + ".csv", name + ".csv.gz"):
        p = os.path.join(folder, fn)
        if os.path.exists(p):
            op = gzip.open if fn.endswith(".gz") else open
            with op(p, "rt", newline="") as f:
                return list(csv.DictReader(f))
    return []


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v


def quotes(row):
    yb, nb = num(row.get("yes_bid_px_1")), num(row.get("no_bid_px_1"))
    yb = yb if yb is not None and yb > EPS else None
    nb = nb if nb is not None and nb > EPS else None
    return {"yes": {"bid": yb, "ask": (1 - nb) if nb is not None else None}, "no": {"bid": nb, "ask": (1 - yb) if yb is not None else None}}


def pnl(p, won, fee_frac, slip=0.0):
    fee = fee_frac * 0.07 * p * (1 - p)
    return (1 - p - slip - fee) if won else (-p - slip - fee)


def pf(xs):
    if not xs:
        return None
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return math.inf if l == 0 else g / l


def shown(x):
    return None if x is None else ("inf" if x == math.inf else round(x, 6))


def window(sig, book, trades, result, cfg):
    tk, close = sig["ticker"], sig["close_ts"]
    rows = sorted((r for r in book if r["ticker"] == tk), key=lambda r: int(r["t_recv_ms"]))
    t0r = next((r for r in rows if int(r["t_recv_ms"]) >= (close - cfg["t0_before"]) * 1000), None)
    if t0r is None:
        return {"status": "no t0 row"}
    t0 = int(t0r["t_recv_ms"])
    if t0 >= (close - CANCEL_BEFORE) * 1000:
        return {"status": "no t0 row"}
    q = quotes(t0r)
    cands = [s for s in ("yes", "no") if q[s]["ask"] is not None]
    if not cands:
        return {"status": "no ask on either side"}
    side = min(cands, key=lambda s: (q[s]["ask"], 0 if s == "yes" else 1))           # R2
    if cfg["spread_max"] is not None:                                                  # R3
        if q["yes"]["ask"] is None or q["yes"]["bid"] is None or q["yes"]["ask"] - q["yes"]["bid"] > cfg["spread_max"] + EPS:
            return {"status": "spread test fails"}
    ask = q[side]["ask"]
    if not (cfg["band"][0] - EPS <= ask <= cfg["band"][1] + EPS):                       # R4
        return {"status": "band test fails"}
    if result not in ("yes", "no"):                                                    # R9
        return {"status": "no result"}
    won = result == side
    out = {"status": "signal", "ticker": tk, "close_ts": close, "side": side, "ask": ask, "won": won,
           "parent_p0": pnl(ask, won, 1.0), "parent_p1": pnl(ask, won, 1.0, 0.01)}
    bid = q[side]["bid"]
    if bid is None:
        out["order"] = False
        return out
    out["order"], out["limit"] = True, bid
    cr = next((r for r in rows if int(r["t_recv_ms"]) >= (close - CANCEL_BEFORE) * 1000), None)
    cancel = int(cr["t_recv_ms"]) if cr is not None else (close - CANCEL_BEFORE) * 1000
    filled = False
    for t in trades:                                                                  # R6
        if t["ticker"] != tk:
            continue
        ct = iso_any(t["created_time"]) * 1000
        if not (t0 < ct < cancel):
            continue
        yp = num(t["yes_price_dollars"])
        if yp is None:
            continue
        if side == "yes" and t["taker_outcome_side"] == "no" and yp < bid - EPS:
            filled = True
        if side == "no" and t["taker_outcome_side"] == "yes" and yp > 1 - bid + EPS:
            filled = True
    for r in rows:                                                                    # R7
        if t0 < int(r["t_recv_ms"]) < cancel:
            a = quotes(r)[side]["ask"]
            if a is not None and a <= bid + EPS:
                filled = True
    out["filled"] = filled
    if filled:
        out["version"] = {"25": pnl(bid, won, 0.25), "0": pnl(bid, won, 0.0), "100": pnl(bid, won, 1.0)}
    return out


def block_report(sigs, start, end):
    n = len(sigs)
    fills = [s for s in sigs if s.get("filled")]
    missed = [s for s in sigs if not s.get("filled")]
    weeks = max(1, math.ceil((end - start + 1) / (7 * 86400)))                         # R12
    P1 = [s["parent_p1"] for s in sigs]
    V = [s["version"]["25"] for s in fills]
    vpf, ppf = pf(V), pf(P1)
    half = n // 2                                                                      # R11
    def diff(ss):
        v = pf([s["version"]["25"] for s in ss if s.get("filled")]); p = pf([s["parent_p1"] for s in ss])
        return None if v is None or p is None else (v - p if not (math.isinf(v) or math.isinf(p)) else (math.inf if math.isinf(v) and not math.isinf(p) else (-math.inf if math.isinf(p) and not math.isinf(v) else 0.0)))
    d1, d2 = diff(sigs[:half]), diff(sigs[half:])
    filled_parent = pf([s["parent_p1"] for s in fills]); missed_parent = pf([s["parent_p1"] for s in missed])
    bar = {
        "pf_beats_parent_by_0_10": vpf is not None and ppf is not None and (vpf - ppf >= 0.10 - EPS if not (math.isinf(vpf) or math.isinf(ppf)) else math.isinf(vpf) and not math.isinf(ppf)),
        "net_per_week_not_lower": sum(V) / weeks >= sum(P1) / weeks - EPS,
        "second_half_not_worse": d1 is not None and d2 is not None and d2 >= d1 - EPS,
        "at_least_60_fills": len(fills) >= MIN_FILLS,
    }
    falsified = (not bar["net_per_week_not_lower"]) or (missed_parent is not None and filled_parent is not None and missed_parent - filled_parent >= 0.10 - EPS)
    verdict = ("FALSIFIED" if falsified else ("PASSES the 7g bar" if all(bar.values()) else
               ("NOT_ENOUGH_DATA" if len(fills) < MIN_FILLS else "does not pass the 7g bar")))
    return {"signals": n, "orders": sum(1 for s in sigs if s.get("order")), "fills": len(fills),
            "fill_rate": shown(len(fills) / sum(1 for s in sigs if s.get("order"))) if any(s.get("order") for s in sigs) else None,
            "version_pf_25": shown(vpf), "version_pf_0": shown(pf([s["version"]["0"] for s in fills])), "version_pf_100": shown(pf([s["version"]["100"] for s in fills])),
            "parent_pf_p0": shown(pf([s["parent_p0"] for s in sigs])), "parent_pf_p1": shown(ppf),
            "parent_pf_p1_on_filled": shown(filled_parent), "parent_pf_p1_on_missed": shown(missed_parent),
            "weeks": weeks, "version_net_per_week": round(sum(V) / weeks, 6), "parent_net_per_week": round(sum(P1) / weeks, 6),
            "half_diff_first": shown(d1), "half_diff_second": shown(d2), "bar": bar, "falsified": falsified, "verdict": verdict}


def run(version, block, signals_path, folders, depth1_marker=None, marker_dir=None, now=None):
    hm_guard.refuse_all([signals_path] + list(folders))
    cfg = CFG[version]
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    if version == "V1" and block == "dev" and not (depth1_marker and os.path.exists(depth1_marker)):
        raise SystemExit("REFUSED: V1 development needs the DEPTH1 marker file")
    if block == "fwd" and now < iso(cfg["fwd_read"]):
        raise SystemExit("REFUSED: the forward block is read on or after %s" % cfg["fwd_read"])
    marker = os.path.join(marker_dir or os.path.dirname(os.path.abspath(__file__)), "%s_%s_READ_DONE" % (version, block))
    if os.path.exists(marker):
        raise SystemExit("REFUSED: %s %s already read (%s)" % (version, block, marker))
    start, end = iso(cfg[block][0]), iso(cfg[block][1])
    with open(signals_path, newline="") as f:
        sigs = [{"ticker": r["ticker"], "close_ts": int(r["close_ts"])} for r in csv.DictReader(f)]
    book, trades, results = [], [], {}
    for d in folders:
        book += rd(d, "book"); trades += rd(d, "trades")
        for c in rd(d, "coverage"):
            if c.get("result"):
                results[c["ticker"]] = c["result"]
    counts, scored = {"outside_block": 0}, []
    for s in sorted(sigs, key=lambda s: (s["close_ts"], s["ticker"])):
        if not (start <= s["close_ts"] <= end):                                       # R10
            counts["outside_block"] += 1
            continue
        w = window(s, book, trades, results.get(s["ticker"]), cfg)
        st = w["status"] if w["status"] != "signal" else ("filled" if w.get("filled") else ("no order (no bid)" if not w.get("order") else "not filled"))
        counts[st] = counts.get(st, 0) + 1
        if w["status"] == "signal":
            scored.append(w)
    out = {"version": version, "block": block, "registrations": "V1 fc528cd3, V2 4221ab37", "counts": counts,
           "report": block_report(scored, start, end), "windows": [{k: (shown(v) if isinstance(v, float) else v) for k, v in w.items() if k != "version"} for w in scored],
           "ambiguities": AMBIG}
    with open(marker, "w") as f:
        f.write("read\n")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(name):
        if name in a:
            i = a.index(name); v = a[i + 1]; del a[i:i + 2]; return v
        return None
    version, block = opt("--version"), opt("--block")
    dm, md = opt("--depth1-marker"), opt("--marker-dir")
    res = run(version, block, a[0], a[2:], dm, md)
    with open(a[1], "w") as f:
        json.dump(res, f, indent=1, sort_keys=True); f.write("\n")
    print(json.dumps(res["counts"], sort_keys=True)); print(res["report"]["verdict"])
