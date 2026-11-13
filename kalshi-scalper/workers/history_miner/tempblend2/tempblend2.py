"""TEMPBLEND second build (History Miner, Nov 13, 2026), written from the card text alone: kalshi-scalper/workers/idea_desk_c/TEMPBLEND_CARD.md on
claude/idea-desk-c at 66483872 (sha256 f07129e1...). Desk C's scorer was not read. Invented rows only: no Kalshi request, no data.

Where the card is silent this build takes a PROVISIONAL reading, named in AMBIG (A1 to A18) and printed in every output; the Head of R&D rules each one
and Desk C amends the card before any data. A provisional reading is not a choice of the card's meaning.

Input (this build's own invented layout, one JSON object per city-hour, one per line):
  city, S (settlement minute, epoch s), member (true if the watched station is one of the five), source ("A" or "B"),
  index: [[t, v], ...] canonical index points (t = the point's minute, epoch s; v in F),
  station: [[t, s, code], ...] the watched station's readings (code "ok" or another word; Source B rows carry code null),
  cal_effective_ms: effective_at_ms of the city's config_version in force at the decision,
  strikes: [{"K": strike F, "yes_bid": dollars, "yes_ask": dollars, "result": "yes" | "no" | null}, ...] the decision candle's close, "K or above"
Usage: python3 -I tempblend2.py <rows.jsonl> <out.json>"""
import json, math, sys

EPS = 1e-9
LOOK_S = 15 * 60
LAG_S = 300
STALE_S = 10 * 60
GAP_F = 0.5
BAND = (0.20, 0.80)
SPREAD_MAX = 0.04
SLIP = 0.01
DEV = ("2026-09-13T00:00:00Z", "2026-11-05T00:00:00Z")
HALF = "2026-10-09T00:00:00Z"
HELD = ("2026-11-12T00:00:00Z", "2026-12-10T00:00:00Z")
MIN_BETS = 200
MIN_DAY2 = 30
AMBIG = [
    "A1 index point v: card says 'the latest canonical index point (v at minute t, about S minus 20 minutes given the 300 second lag)'. Provisional: the latest point with t <= decision time minus 300 s, decision time = S minus 15 min (so normally t = S minus 20 min). Not provisional alternatives: exactly S minus 20, or the last point published by the decision time using its own publish stamp.",
    "A2 decision candle: 'the 1 minute candle ending 15 minutes before S'. Provisional: the strike quotes are that candle's close (end_period_ts = S minus 900 s).",
    "A3 station reading s: Source A 'at the same minute t'; Source B 'the latest report at or before t'. Provisional: Source A needs a reading at exactly minute t; Source B takes the latest at or before t. Skip if the reading used is more than 10 minutes from t; 'within 10 minutes' read as <= 600 s (inclusive).",
    "A4 gap threshold: '|g| under 0.5F no bet', '+0.5F or more'. Provisional: bet when |g| >= 0.5 - 1e-9.",
    "A5 strike set: 's < K <= v' (YES) and 'v < K <= s' (NO), compared as written on raw decimals (no rounding of v or s to whole degrees). The card does not say whether v and s are rounded first; the settlement rounding of the index is not stated.",
    "A6 ORDER OF FILTERS (the main one): 'Only the strike nearest the midpoint (v + s) / 2, with its ask at 20c to 80c and a spread of 4c or less'. Provisional: take the strike nearest the midpoint among the eligible strikes FIRST, then require its ask and spread; if it fails, NO BET (no fallback to the next strike). The other reading: filter by band and spread first, then take the nearest.",
    "A7 tie for nearest: two strikes equally near the midpoint (within 1e-9). Provisional: the LOWER strike.",
    "A8 side's ask: YES ask = yes_ask; NO ask = 1 - yes_bid; spread = yes_ask - yes_bid for both. A quote is usable only if 0 < yes_bid < yes_ask < 1.",
    "A9 band: '20c to 80c' on the side's ask BEFORE the 1c slip, inclusive at both ends (1e-9). Spread '4c or less' inclusive.",
    "A10 fee: the card says 'cash PF after fees' but names no fee. Provisional: one contract, fee = 0.07 x p x (1 - p) rounded UP to the next cent at p = ask + 1c (the house formula used by the other cards). Cost = p + fee; win pays 1.",
    "A11 PF: gross gain / gross loss over bets; 'inf' if no loss; n printed. Cash = per-contract dollars after fee.",
    "A12 void: a bet whose strike result is neither yes nor no. The card is silent. Provisional: the Head's one void rule for hold-to-settlement cards (price refunded, fee kept, a fee-only loss, counted in n and PF), and the count is printed.",
    "A13 windows: by S, development [2026-09-13, 2026-11-05), halves split at S < 2026-10-09 / S >= 2026-10-09; held-out [2026-11-12, 2026-12-10); S in neither is ignored and counted.",
    "A14 kill lines applied to the development read as written: closed if bets < 200, or pooled cash PF < 1.0, or either half's PF < 1.2. Whether 'PF under 1.2 in either half' applies when a half has no loss (inf) or no bet: provisional, a half with no bet fails the line, a half with no loss passes.",
    "A15 day split: 'time since the latest calibration change (effective_at_ms)'. Provisional: measured at the decision time; 'days 0 to 1' = under 2 x 86400 s, 'day 2 onward' = 2 x 86400 s or more. The card does not say whether a calibration change after the decision but before S counts.",
    "A16 member skip: 'its own code at minute t is anything but ok' applies to member cities (Source A). Provisional: a missing code also skips. Non-member (Source B) rows carry no code and are not skipped for it.",
    "A17 one bet per city-hour; the card does not say what happens if the index has no point in the 10 minutes before the decision. Provisional: skip, counted ('no index point').",
    "A18 member and non-member rows (report rule): descriptive PF and n of each; the verdict is pooled. Membership is taken from the row as given (it can change with a calibration; the card fixes it per city, not per hour).",
]


def iso(s):
    from datetime import datetime, timezone
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def fee(p):
    return math.ceil(100 * 0.07 * p * (1 - p) - 1e-9) / 100


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return "inf" if l == 0 and xs else (round(g / l, 6) if xs else None)


def decide(row):
    """One city-hour: returns (status, bet or None). status names why there is no bet."""
    S = row["S"]
    dec = S - LOOK_S
    pts = [p for p in row["index"] if p[0] <= dec - LAG_S]
    if not pts:
        return "no index point", None
    t, v = max(pts, key=lambda p: p[0])
    if dec - LAG_S - t > STALE_S:
        return "no index point", None
    if row["source"] == "A":
        rd = [r for r in row["station"] if r[0] == t]
        if not rd:
            return "no station reading", None
        r = rd[0]
        if row.get("member") and r[2] != "ok":
            return "member station not ok", None
    else:
        rd = [r for r in row["station"] if r[0] <= t]
        if not rd:
            return "no station reading", None
        r = max(rd, key=lambda x: x[0])
        if t - r[0] > STALE_S:
            return "no station reading", None
    s = r[1]
    g = v - s
    if abs(g) < GAP_F - EPS:
        return "gap under 0.5F", None
    side = "yes" if g > 0 else "no"
    lo, hi = (s, v) if side == "yes" else (v, s)
    elig = [k for k in row["strikes"] if lo < k["K"] <= hi]
    if not elig:
        return "no strike between", None
    mid = (v + s) / 2
    k = min(elig, key=lambda k: (round(abs(k["K"] - mid), 9), k["K"]))
    b, a = k["yes_bid"], k["yes_ask"]
    if b is None or a is None or not (0 < b < a < 1):
        return "nearest strike not two-sided", None
    ask = a if side == "yes" else 1 - b
    if not (BAND[0] - EPS <= ask <= BAND[1] + EPS):
        return "nearest strike ask outside 20c to 80c", None
    if a - b > SPREAD_MAX + EPS:
        return "nearest strike spread over 4c", None
    p = ask + SLIP
    cost = p + fee(p)
    res = k["result"]
    if res not in ("yes", "no"):
        pnl, void = -fee(p), True
    else:
        pnl, void = (1 - cost) if res == side else -cost, False
    return "bet", {"city": row["city"], "S": S, "K": k["K"], "side": side, "v": v, "s": s, "gap": round(g, 6), "ask": round(ask, 6),
                   "pnl": round(pnl, 6), "void": void, "member": bool(row.get("member")),
                   "day2": (dec * 1000 - row["cal_effective_ms"]) >= 2 * 86400 * 1000}


def summary(bets):
    xs = [b["pnl"] for b in bets]
    return {"n": len(xs), "pf": pf(xs), "net": round(sum(xs), 6), "voids": sum(b["void"] for b in bets)}


def run(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    d0, d1, h, ho0, ho1 = iso(DEV[0]), iso(DEV[1]), iso(HALF), iso(HELD[0]), iso(HELD[1])
    out = {"card": "TEMPBLEND_CARD.md 66483872 (f07129e1)", "statuses": {}, "outside_windows": 0, "ambiguities": AMBIG}
    dev, held, decisions = [], [], []
    for row in rows:
        S = row["S"]
        win = "dev" if d0 <= S < d1 else ("held" if ho0 <= S < ho1 else None)
        if win is None:
            out["outside_windows"] += 1
            continue
        st, bet = decide(row)
        out["statuses"][st] = out["statuses"].get(st, 0) + 1
        decisions.append({"city": row["city"], "S": S, "window": win, "status": st, "bet": bet})
        if bet:
            (dev if win == "dev" else held).append(bet)
    first = [b for b in dev if b["S"] < h]
    second = [b for b in dev if b["S"] >= h]
    D = summary(dev); F = summary(first); L = summary(second)
    def half_fails(x):
        return x["n"] == 0 or (x["pf"] != "inf" and x["pf"] < 1.2 - EPS)
    kills = {"fewer_than_200": D["n"] < MIN_BETS,
             "pooled_pf_under_1": D["n"] > 0 and D["pf"] != "inf" and D["pf"] < 1.0 - EPS,
             "a_half_under_1_2": half_fails(F) or half_fails(L)}
    out["development"] = {"pooled": D, "first_half": F, "second_half": L,
                          "member": summary([b for b in dev if b["member"]]), "non_member": summary([b for b in dev if not b["member"]]),
                          "days_0_1_info": summary([b for b in dev if not b["day2"]]), "day_2_on_info": summary([b for b in dev if b["day2"]]),
                          "kills": kills, "verdict": "CLOSED" if any(kills.values()) else "passes the development kill lines"}
    d2 = [b for b in held if b["day2"]]
    H2 = summary(d2)
    out["held_out"] = {"pooled": summary(held), "days_0_1": summary([b for b in held if not b["day2"]]), "day_2_on": H2,
                       "calibration_kill": ("no evidence at n = %d" % H2["n"]) if H2["n"] < MIN_DAY2 else
                       ("FAIL" if H2["pf"] != "inf" and H2["pf"] < 1.0 - EPS else "passes")}
    out["decisions"] = decisions
    return out


if __name__ == "__main__":
    res = run(sys.argv[1])
    with open(sys.argv[2], "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps({k: res[k] for k in ("statuses", "outside_windows")}, sort_keys=True))
    print(json.dumps(res["development"]["kills"]), res["development"]["verdict"], res["held_out"]["calibration_kill"])
