"""SPXFV1 SECOND BUILD (History Miner, Nov 13, 2026) for KXINX15M, written from the card text alone: kalshi-scalper/workers/DESK_A_SPX_CARDS_NOV13.md
at 94c4dfbc on claude/idea-desk-a (sha256 bb7e1e4a...), Card 1 plus the dated lines and D1 to D8, which govern where they differ from the body.
The Testing Desk's build was not read. Research only. Nothing Databento-derived is committed: the futures file is read from a private path, and the
output holds AGGREGATES only (counts, PF, mean, labels), never a per-window probability or a bar value (D8).

Inputs (this build's layout; the real rows are built by another script and audited):
  windows CSV: ticker, close_ts (epoch s), yes_bid, yes_ask (the Kalshi decision candle, end time close - 120 s), result (yes | no | void | empty)
  futures CSV: ts_event_s (bar START, epoch s, D7), symbol, instrument_id, close  - ES.c.0 1 minute bars only (D7); any other symbol stops the run (F2)
Usage: python3 -I spxfv1b.py dev|held <windows.csv> <futures.csv> <out.json>"""
import csv, json, math, os, statistics, sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

EPS = 1e-9
HELDOUT_FIRST = "2026-12-01T00:00:00Z"
READ_DATE = "2027-02-26T00:00:00Z"          # D4
MIN_READ = 150
H_FACTOR = math.sqrt(119 / 60)               # D1
EDGE, SPREAD_MAX, BAND = 0.05, 0.03, (0.05, 0.30)
MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SPXFV1_HELD_READ_DONE")
RULINGS = {   # the Head of R&D's rulings of Nov 13, 2026 (16:47Z), printed as constants in every run header
    "S1_fee": "0.07 x C x p x (1 - p), rounded UP to the cent per order, C = 1 (quadratic, multiplier 1, standard schedule); the unrounded figure is information only",
    "S2_sd": "consecutive bar pairs both present on F_now's instrument id, at least 6 of the 10, sample (n - 1) sd, times sqrt(119/60)",
    "S3_quote": "the decision candle's YES bid and ask closes; YES bid + NO bid >= 1 - 1e-9 (crossed or locked) is no quote (rule 18)",
    "S4_tie": "a tie of the two asks goes to YES; the tie count is printed",
    "S5_thirds": "three equal time spans from 2026-12-01T00:00Z to the last traded close at or before READ_DATE",
    "S6_void": "a void is a fee-only loss; an empty result stops the run",
}


class Stop(Exception):
    pass


def iso(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def fee(p):
    """S1: per order, C = 1, rounded up to the cent."""
    return math.ceil(100 * 0.07 * p * (1 - p) - 1e-9) / 100


def fee_raw(p):
    return 0.07 * p * (1 - p)


def load_futures(path):
    bars = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if r.get("symbol") != "ES.c.0":                                     # F2
                raise Stop("futures row with symbol %r refused: ES.c.0 only (D7)" % r.get("symbol"))
            ts = int(r["ts_event_s"])
            if ts in bars:
                raise Stop("two futures bars with ts_event %d (ES.c.0 only, D7)" % ts)
            bars[ts] = (r["instrument_id"], float(r["close"]))
    return bars


def decide(w, bars):
    close = w["close_ts"]
    now, opn = bars.get(close - 180), bars.get(close - 960)                     # D7
    if now is None or opn is None:
        return "no_bar", None
    if now[0] != opn[0]:
        return "roll_skipped", None
    ch = []
    for k in range(10):
        a, b = bars.get(close - 780 + 60 * k), bars.get(close - 720 + 60 * k)
        if a and b and a[0] == now[0] and b[0] == now[0]:
            ch.append(math.log(b[1] / a[1]))
    if len(ch) < 6:
        return "too_few_changes", None
    sd1 = statistics.stdev(ch)
    if sd1 <= 0:
        return "zero_sd", None
    p_yes = phi(math.log(now[1] / opn[1]) / (sd1 * H_FACTOR))                  # D1
    b, a = w["yes_bid"], w["yes_ask"]
    if not (0 < b < 1 and 0 < a < 1) or b >= a - EPS:                         # S3, rule 18: crossed or locked is no quote
        return "no_quote", None
    if a - b > SPREAD_MAX + EPS:
        return "no_trade", None
    asks = {"yes": a, "no": 1 - b}
    tie = abs(asks["yes"] - asks["no"]) <= EPS
    side = "yes" if asks["yes"] <= asks["no"] + EPS else "no"                  # S4
    ask = asks[side]
    p_side = p_yes if side == "yes" else 1 - p_yes
    if not (BAND[0] - EPS <= ask <= BAND[1] + EPS) or p_side - ask < EDGE - EPS:
        return "no_trade", None
    res = w["result"]
    if res == "void":                                                           # S6
        net, raw = -fee(ask), -fee_raw(ask)
    else:
        won = res == side
        net = (1 - ask - fee(ask)) if won else (-ask - fee(ask))
        raw = (1 - ask - fee_raw(ask)) if won else (-ask - fee_raw(ask))
    return "traded", {"close": close, "side": side, "ask": ask, "won": res == side, "net": net, "net_unrounded": raw, "tie": tie}


def pf(xs):
    if not xs:
        return None
    g = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return math.inf if l == 0 else g / l


def shown(x):
    return None if x is None else ("inf" if x == math.inf else round(x, 6))


def agg(trades):
    xs = [t["net"] for t in trades]
    n = len(xs)
    return {"n": n, "pf": shown(pf(xs)), "pf_unrounded_info": shown(pf([t["net_unrounded"] for t in trades])), "ties": sum(t["tie"] for t in trades),
            "mean_net": round(sum(xs) / n, 6) if n else None,
            "win_rate": round(sum(t["won"] for t in trades) / n, 6) if n else None, "mean_price": round(sum(t["ask"] for t in trades) / n, 6) if n else None}


def run(mode, windows_path, futures_path, now=None, marker=MARKER, out_path=None):
    hm_guard.refuse_all([windows_path, futures_path] + ([out_path] if out_path else []))
    if mode not in ("dev", "held"):
        raise Stop("mode is dev or held")
    if mode == "held":
        now = datetime.now(timezone.utc).timestamp() if now is None else now
        if now < iso(READ_DATE):
            raise Stop("held read refused before %s" % READ_DATE)
        if os.path.exists(marker):
            raise Stop("held read refused: read-once marker %s exists" % marker)
    cut = iso(HELDOUT_FIRST)
    bars = load_futures(futures_path)
    counts, trades = {}, []
    rd = iso(READ_DATE)
    W = []
    with open(windows_path, newline="") as f:
        for r in csv.DictReader(f):
            close = int(r["close_ts"])                                          # F1: drop by block FIRST; no other field of a dropped row is read
            held = close >= cut
            if mode == "held" and close > rd:                                   # S5
                counts["after_read_date_ignored"] = counts.get("after_read_date_ignored", 0) + 1
                continue
            if (mode == "dev" and held) or (mode == "held" and not held):
                k = "held_out_ignored" if mode == "dev" else "development_ignored"
                counts[k] = counts.get(k, 0) + 1
                continue
            if r["result"] not in ("yes", "no", "void"):                        # S6, only rows of the block being read
                raise Stop("result %r refused (%s)" % (r["result"], r["ticker"]))
            W.append({"ticker": r["ticker"], "close_ts": close, "yes_bid": float(r["yes_bid"]), "yes_ask": float(r["yes_ask"]), "result": r["result"]})
    for w in sorted(W, key=lambda w: (w["close_ts"], w["ticker"])):
        st, t = decide(w, bars)
        counts[st] = counts.get(st, 0) + 1
        if t:
            trades.append(t)
    A = agg(trades)
    out = {"mode": mode, "card": "DESK_A_SPX_CARDS_NOV13.md 94c4dfbc", "rulings": RULINGS, "counts": counts}
    if mode == "dev":
        A["label"] = "no evidence at n = %d" % A["n"] if A["n"] < 100 else "development (not a verdict)"
        out["aggregate"] = A
    else:
        if A["n"] < MIN_READ:
            out["aggregate"] = {"n": A["n"], "verdict": "NOT_ENOUGH_DATA (count only)"}
        else:
            last = max(t["close"] for t in trades); span = (last - cut) / 3
            thirds = [[t for t in trades if cut + i * span <= t["close"] < cut + (i + 1) * span or (i == 2 and t["close"] == last)] for i in range(3)]
            th = [agg(x) for x in thirds]
            raw = [pf([t["net"] for t in x]) for x in thirds]
            kills = {"pf_under_1_at_100": pf([t["net"] for t in trades]) < 1.0,
                     "win_rate_within_3_points": abs(A["win_rate"] - A["mean_price"]) < 0.03 + EPS}
            passes = all(r is not None and r >= 1.5 - EPS for r in raw) and not any(kills.values())
            A.update({"thirds": th, "kills": kills, "verdict": "BAR MET (not a research-bar pass)" if passes else "BAR NOT MET"})   # F3
            out["aggregate"] = A
        with open(marker, "w") as f:
            f.write("SPXFV1 held read done\n")
    return out


if __name__ == "__main__":
    try:
        res = run(sys.argv[1], sys.argv[2], sys.argv[3], out_path=sys.argv[4])
    except Stop as e:
        sys.exit("STOPPED: %s" % e)
    with open(sys.argv[4], "w") as f:
        json.dump(res, f, indent=1, sort_keys=True); f.write("\n")
    print(json.dumps(res["aggregate"], sort_keys=True))
