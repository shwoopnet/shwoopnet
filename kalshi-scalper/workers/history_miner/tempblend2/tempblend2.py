"""TEMPBLEND second build (History Miner, Nov 13, 2026), written from the card text alone: kalshi-scalper/workers/idea_desk_c/TEMPBLEND_CARD.md on
claude/idea-desk-c at 658817e9 (sha256 32112a10..., with Amendment 1, A1 to A18). Desk C's scorer was not read. Invented rows only: no Kalshi request,
no data. First built at 66483872 (9c112b9f) with provisional readings; aligned to Amendment 1 by changing only those lines.

Input (this build's own invented layout, one JSON object per city-hour, one per line):
  city, S (settlement minute, epoch s), member (true if the watched station is one of the five), source ("A" or "B"),
  index: [[t, v], ...] canonical index points (t = the point's minute, epoch s; v in F),
  station: [[t, s, code, obs_time], ...] the watched station's readings: Source A rows are keyed by the index point minute t they belong to
           (the stations[] of point t) and carry the station's obs_time (omitted = t); Source B rows are keyed by their own obs_time and carry code null,
  cal_effective_ms: effective_at_ms of the city's config_version in force at the decision,
  strikes: [{"K": strike F, "yes_bid": dollars, "yes_ask": dollars, "result": "yes" | "no" | null}, ...] the decision candle's close, "K or above"
Usage: python3 -I tempblend2.py <rows.jsonl> <out.json>"""
import json, math, sys

EPS = 1e-9
LOOK_S = 15 * 60
LAG_S = 300
STALE_S = 10 * 60            # A3 and A17 (Amendment 1)
GAP_F = 0.5
BAND = (0.20, 0.80)
SPREAD_MAX = 0.04
DEV = ("2026-09-13T00:00:00Z", "2026-11-05T00:00:00Z")
HALF = "2026-10-09T00:00:00Z"
HELD = ("2026-11-12T00:00:00Z", "2026-12-10T00:00:00Z")
MIN_BETS = 200
MIN_DAY2 = 30
AMBIG = ["Amendment 1 of TEMPBLEND_CARD.md (658817e9) rules A1 to A18; this build follows it line by line (see the card)."]


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
    pts = [p for p in row["index"] if p[0] <= dec - LAG_S]            # A1
    if not pts:
        return "no index point", None
    t, v = max(pts, key=lambda p: p[0])
    if dec - t > STALE_S + EPS:                                        # A17: no point within 10 minutes before the decision
        return "no index point", None
    if row["source"] == "A":
        rd = [r for r in row["station"] if r[0] == t]                   # A3: the stations[] of point t itself
        if not rd:
            return "no station reading", None
        r = rd[0]
        obs = r[3] if len(r) > 3 and r[3] is not None else r[0]
        if t - obs > STALE_S + EPS:
            return "no station reading", None
        if row.get("member") and r[2] != "ok":                          # A16: a missing code skips too
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
    elig = [k for k in row["strikes"] if lo < k["K"] <= hi]           # A5: raw decimals
    if not elig:
        return "no strike between", None
    def side_ask(k):
        return k["yes_ask"] if side == "yes" else 1 - k["yes_bid"]
    ok = [k for k in elig if k["yes_bid"] is not None and k["yes_ask"] is not None and 0 < k["yes_bid"] < k["yes_ask"] < 1   # A2, A8
          and BAND[0] - EPS <= side_ask(k) <= BAND[1] + EPS and k["yes_ask"] - k["yes_bid"] <= SPREAD_MAX + EPS]          # A6, A9: filters FIRST
    if not ok:
        return "no strike passes band and spread", None
    mid = (v + s) / 2
    k = min(ok, key=lambda k: (round(abs(k["K"] - mid), 9), k["K"]))   # A6 then A7: nearest, ties to the lower K
    b, a = k["yes_bid"], k["yes_ask"]
    ask = side_ask(k)
    p = ask                                                           # A10: fill at the ask seen, no +1c
    cost = p + fee(p)
    res = k["result"]
    if res not in ("yes", "no"):                                      # A12
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
