"""V1 (OICORE resting bid) and V2 (EVENT830 resting entry) SECOND BUILD (History Miner, Nov 13, 2026), written from the two registrations alone:
kalshi-scalper/refine_tools/V1_OICORE_RESTING_BID_REGISTRATION.md (fc528cd3) and V2_EVENT830_RESTING_ENTRY_REGISTRATION.md (4221ab37) on claude/refine-live
(at 243dd748: V1 64539074, V2 5e156f3e, with the dated amendments of Nov 13), and the recorder column lists in scripts/record_15m_book.py and scripts/record_nc_book.py on main. v1_resting_score.py was NOT read.
Invented rows only. Every reading below is now RULED by the registrations' dated amendments (R1 to R14, C1 to C4, the NOT_ENOUGH_DATA order).

Input:
  signals CSV: ticker, close_ts (epoch s) - one candidate window per line (V1: OICORE trigger windows; V2: listed release windows), built elsewhere
  one or more run folders, each with book.csv, trades.csv and coverage.csv in the recorders' columns (plain or .gz)
Usage: python3 -I resting2.py --version V1|V2 --block dev|fwd <signals.csv> <out.json> <run folder>... [--depth1-marker <file>] [--nc15depth1-record <file>]
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
           "dev": ("2026-11-12T00:00:00Z", "2026-12-04T23:59:59Z"), "fwd": ("2026-12-10T00:00:00Z", "2026-12-23T23:59:59Z"), "fwd_read": "2026-12-24T00:00:00Z",
           "dev_read": "2026-12-05T00:00:00Z"},
}
CANCEL_BEFORE = 120
T0_LATE_S = 10                       # C1: a t0 row more than 10 s after the target is no_t0_row
LABELS = {"V1": "not blind on Bitcoin windows to Nov 13: DEPTH1, CFRTI-B and CFRTI1-BTC read them (DEPTH1 on 2026-11-14)",
          "V2": "not blind on EVENT830's forward windows"}
MARKER_DIR = os.path.dirname(os.path.abspath(__file__))     # the read-once markers live at a fixed path
MIN_FILLS = 60
AMBIG = ["All readings ruled (V1 64539074 and V2 5e156f3e dated amendments): R1 best bids at level 1; R2/C2 a tie of the asks takes YES; R3 V2 spread on YES ask minus YES bid, 10c inclusive; R4 band inclusive; R5 rest open at both ends; C1 t0 row more than 10 s late is no_t0_row; R6 taker side from taker_outcome_side; R7 book ask at or below our price; R8 parent +1c fee at p + 0.01, version fee at our bid unrounded; R9 no result: counted, out of every PF; R10 blocks inclusive; R11/C4 halves by count, n // 2 first; R12 ceil weeks; C3 bar (2) against the parent at +0c and +1c, the stricter governs; R13 FALSIFIED = bar (2) fails OR missed windows' parent PF exceeds the VERSION PF by 0.10 or more; R14 a set with no bet fails; under 60 fills NOT_ENOUGH_DATA comes first and FALSIFIED is information only."]


def iso(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def iso_any(s):
    """created_time to epoch seconds, keeping every digit of the fraction (Python's parser stops at 6)."""
    s = s.strip().replace("Z", "+00:00")
    frac = 0.0
    if "." in s:
        head, rest = s.split(".", 1)
        digits = ""
        while rest and rest[0].isdigit():
            digits += rest[0]; rest = rest[1:]
        frac = float("0." + digits) if digits else 0.0
        s = head + rest
    return datetime.fromisoformat(s).timestamp() + frac


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


def pnl(p, won, fee_frac):
    """Per contract at paid price p (R8: the +1c parent pays p + 0.01 and its fee is taken at that price)."""
    fee = fee_frac * 0.07 * p * (1 - p)
    return (1 - p - fee) if won else (-p - fee)


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
    if t0 > (close - cfg["t0_before"] + T0_LATE_S) * 1000 or t0 >= (close - CANCEL_BEFORE) * 1000:   # C1
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
           "parent_p0": pnl(ask, won, 1.0), "parent_p1": pnl(ask + 0.01, won, 1.0)}
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
    P0 = [s["parent_p0"] for s in sigs]
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
        "net_per_week_not_lower": sum(V) / weeks >= sum(P0) / weeks - EPS and sum(V) / weeks >= sum(P1) / weeks - EPS,   # C3: +0c and +1c
        "second_half_not_worse": d1 is not None and d2 is not None and d2 >= d1 - EPS,
        "at_least_60_fills": len(fills) >= MIN_FILLS,
    }
    # R13: the missed windows' PARENT PF against the VERSION PF on its fills; inf on either side is compared as the larger
    gap_missed = (missed_parent is not None and vpf is not None and
                  (missed_parent - vpf >= 0.10 - EPS if not (math.isinf(missed_parent) or math.isinf(vpf)) else math.isinf(missed_parent) and not math.isinf(vpf)))
    falsified = (not bar["net_per_week_not_lower"]) or gap_missed
    if len(fills) < MIN_FILLS:                                    # NOT_ENOUGH_DATA first; FALSIFIED is information only
        verdict = "NOT_ENOUGH_DATA (FALSIFIED OR, information only: %s)" % ("true" if falsified else "false")
    else:
        verdict = "FALSIFIED" if falsified else ("PASSES the 7g bar" if all(bar.values()) else "does not pass the 7g bar")
    return {"signals": n, "orders": sum(1 for s in sigs if s.get("order")), "fills": len(fills),
            "fill_rate": shown(len(fills) / sum(1 for s in sigs if s.get("order"))) if any(s.get("order") for s in sigs) else None,
            "version_pf_25": shown(vpf), "version_pf_0": shown(pf([s["version"]["0"] for s in fills])), "version_pf_100": shown(pf([s["version"]["100"] for s in fills])),
            "parent_pf_p0": shown(pf([s["parent_p0"] for s in sigs])), "parent_pf_p1": shown(ppf),
            "parent_pf_p1_on_filled": shown(filled_parent), "parent_pf_p1_on_missed": shown(missed_parent),
            "weeks": weeks, "version_net_per_week": round(sum(V) / weeks, 6), "parent_net_per_week": round(sum(P1) / weeks, 6),
            "parent_net_per_week_p0": round(sum(P0) / weeks, 6), "missed_parent_minus_version_pf_ge_0_10": gap_missed,
            "half_diff_first": shown(d1), "half_diff_second": shown(d2), "bar": bar, "falsified": falsified, "verdict": verdict}


def first_line(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.readline()
    except (OSError, TypeError):
        return ""


def run(version, block, signals_path, folders, depth1_marker=None, marker_dir=None, now=None, nc15_record=None, out_path=None):
    hm_guard.refuse_all([signals_path] + list(folders) + ([out_path] if out_path else []))   # book roots, signals and out
    cfg = CFG[version]
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    if version == "V1" and block == "dev" and not first_line(depth1_marker).startswith("DEPTH1 READ MADE:"):
        raise SystemExit("REFUSED: V1 development needs the DEPTH1 marker file starting 'DEPTH1 READ MADE:'")
    if version == "V2" and block == "dev":
        if now < iso(cfg["dev_read"]):
            raise SystemExit("REFUSED: V2 development is read on or after %s" % cfg["dev_read"])
        if not first_line(nc15_record).startswith("NC15DEPTH1 SCORER HASH: "):
            raise SystemExit("REFUSED: V2 development needs the NC15DEPTH1 scorer hash record")
    if block == "fwd" and now < iso(cfg["fwd_read"]):
        raise SystemExit("REFUSED: the forward block is read on or after %s" % cfg["fwd_read"])
    marker = os.path.join(marker_dir or MARKER_DIR, "%s_%s_READ_DONE" % (version, block))
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
    out = {"version": version, "block": block, "label": LABELS[version], "registrations": "V1 64539074, V2 5e156f3e", "counts": counts,
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
    dm, nc = opt("--depth1-marker"), opt("--nc15depth1-record")
    res = run(version, block, a[0], a[2:], dm, None, None, nc, a[1])
    with open(a[1], "w") as f:
        json.dump(res, f, indent=1, sort_keys=True); f.write("\n")
    print(json.dumps(res["counts"], sort_keys=True)); print(res["report"]["verdict"])
