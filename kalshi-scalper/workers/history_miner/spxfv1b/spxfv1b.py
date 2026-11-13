"""SPXFV1 SECOND BUILD (History Miner, Nov 13, 2026) for KXINX15M, written from the card text alone: kalshi-scalper/workers/DESK_A_SPX_CARDS_NOV13.md
at 94c4dfbc on claude/idea-desk-a (sha256 bb7e1e4a...), Card 1 plus the dated lines and D1 to D8, which govern where they differ from the body.
The Testing Desk's build was not read. Research only. Nothing Databento-derived is committed: the futures file is read from a private path, and the
output holds AGGREGATES only (counts, PF, mean, labels), never a per-window probability or a bar value (D8).

Inputs (this build's layout; the real rows are built by another script and audited):
  windows CSV: ticker, close_ts (epoch s), yes_bid, yes_ask (the Kalshi decision candle, end time close - 120 s), result (yes | no | void | empty)
  futures CSV: ts_event_s (bar START, epoch s, D7), instrument_id, close  - ES.c.0 1 minute bars only (D7)
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
READINGS = [
    "S1 fee: the card says 'Kalshi's quadratic schedule' and the Head's facts 'quadratic fee, multiplier 1'; the coefficient is not stated. Provisional: 0.07 x p x (1 - p) per contract (multiplier 1), unrounded for scoring, up-rounded to the cent per order for the stress line.",
    "S2 sd: the 10 one-minute log changes ending at the F_now bar are between consecutive bars ts_event close-780 ... close-180 (11 bars); a change counts only if both its bars exist and carry F_now's instrument id; at least 6 changes; sample standard deviation (n - 1); sd_1m of 0 gives no model (skipped, counted).",
    "S3 quotes: the decision candle's YES bid and ask closes; NO ask = 1 - YES bid; usable only if 0 < bid < ask < 1; a crossed or locked quote is no quote (standing rule 18).",
    "S4 cheaper side: the lower ask; a tie takes YES. Band 0.05 to 0.30 and spread 0.03 inclusive, edge (model chance of that side minus its ask) >= 0.05, all with 1e-9.",
    "S5 thirds: 'three equal date thirds of the held-out': the held-out span from 2026-12-01 to the latest traded close, cut into three equal time spans; PF 1.5 or better in each.",
    "S6 traded windows = windows where the rule buys; void results are fee-only losses and counted (the one void rule); an empty result stops the run.",
    "S7 kills printed in the held read: PF under 1.0 pooled at n >= 100; win rate within 3 points of the mean traded price at n >= 150; fewer than 150 traded: count only (NOT_ENOUGH_DATA).",
    "S8 development: closes before 2026-12-01; under 100 traded 'no evidence at n = x'; nothing is tuned on it. Held-out closes are ignored and counted in dev mode.",
]


class Stop(Exception):
    pass


def iso(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def fee(p):
    return 0.07 * p * (1 - p)


def load_futures(path):
    bars = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
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
    side = "yes" if asks["yes"] <= asks["no"] + EPS else "no"
    ask = asks[side]
    p_side = p_yes if side == "yes" else 1 - p_yes
    if not (BAND[0] - EPS <= ask <= BAND[1] + EPS) or p_side - ask < EDGE - EPS:
        return "no_trade", None
    res = w["result"]
    if res == "void":
        net, stress = -fee(ask), -math.ceil(100 * fee(ask) - 1e-9) / 100
    else:
        won = res == side
        net = (1 - ask - fee(ask)) if won else (-ask - fee(ask))
        rf = math.ceil(100 * fee(ask) - 1e-9) / 100
        stress = (1 - ask - rf) if won else (-ask - rf)
    return "traded", {"close": close, "side": side, "ask": ask, "won": res == side, "net": net, "stress": stress}


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
    return {"n": n, "pf": shown(pf(xs)), "pf_stress": shown(pf([t["stress"] for t in trades])), "mean_net": round(sum(xs) / n, 6) if n else None,
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
    with open(windows_path, newline="") as f:
        W = []
        for r in csv.DictReader(f):
            if r["result"] not in ("yes", "no", "void"):
                raise Stop("result %r refused (%s)" % (r["result"], r["ticker"]))
            W.append({"ticker": r["ticker"], "close_ts": int(r["close_ts"]), "yes_bid": float(r["yes_bid"]), "yes_ask": float(r["yes_ask"]), "result": r["result"]})
    bars = load_futures(futures_path)
    counts, trades = {}, []
    for w in sorted(W, key=lambda w: (w["close_ts"], w["ticker"])):
        held = w["close_ts"] >= cut
        if (mode == "dev" and held) or (mode == "held" and not held):
            counts["held_out_ignored" if mode == "dev" else "development_ignored"] = counts.get("held_out_ignored" if mode == "dev" else "development_ignored", 0) + 1
            continue
        st, t = decide(w, bars)
        counts[st] = counts.get(st, 0) + 1
        if t:
            trades.append(t)
    A = agg(trades)
    out = {"mode": mode, "card": "DESK_A_SPX_CARDS_NOV13.md 94c4dfbc", "counts": counts, "readings": READINGS}
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
            A.update({"thirds": th, "kills": kills, "verdict": "PASS" if passes else "NOT PASS"})
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
