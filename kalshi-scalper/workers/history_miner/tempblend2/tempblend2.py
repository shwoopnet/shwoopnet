"""TEMPBLEND second build (History Miner, Nov 13, 2026), written from the card text alone: kalshi-scalper/workers/idea_desk_c/TEMPBLEND_CARD.md on
claude/idea-desk-c at 515421f6 (sha256 85d8f455..., with Amendment 1, A1 to A18, and Amendment 2, F1 to F6 and Q1 to Q3). Desk C's scorer was not
read. Invented rows only: no Kalshi request, no data. First built at 66483872 (9c112b9f); aligned to Amendment 1 (848fd4ae), then to Amendment 2.

Input (this build's own invented layout, one JSON object per city-hour, one per line):
  city, S (settlement minute, epoch s), member (true if the watched station is one of the five), source ("A" or "B"),
  index: [[t, v], ...] canonical index points (t = the point's minute, epoch s; v in F),
  station: [[t, s, code, obs_time], ...] the watched station's readings: Source A rows are keyed by the index point minute t they belong to
           (the stations[] of point t) and carry the station's obs_time (omitted = t); Source B rows are keyed by their own obs_time and carry code null,
  cal_effective_ms: effective_at_ms of the city's config_version in force at the decision,
  strikes: [{"K": strike F, "yes_bid": dollars, "yes_ask": dollars, "result": "yes" | "no" | null}, ...] the decision candle's close, "K or above"
  Every strike's result must be "yes", "no" or "void" (F6); one row per (city, S) (F5); otherwise the run stops.
Usage: python3 -I tempblend2.py dev <rows.jsonl> <out.json>
       python3 -I tempblend2.py held <rows.jsonl> <out.json>     (refused before 2026-12-10T00:00:00Z; writes HELD_READ_DONE beside this file, refused if present)"""
import datetime, json, math, os, statistics, sys
from zoneinfo import ZoneInfo

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
BAR_PF, BAR_Z = 1.5, 5.46
HELD_OPEN = "2026-12-10T00:00:00Z"
MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HELD_READ_DONE")
CENTRAL = ZoneInfo("America/Chicago")


class Stop(Exception):
    pass
AMBIG = ["Amendments 1 and 2 of TEMPBLEND_CARD.md (515421f6) rule A1 to A18, F1 to F6 and Q1 to Q3; this build follows them line by line.",
         "OPEN B1 (not ruled by the text): the bar 'cash PF 1.5 in each of three windows' does not name the three windows. Provisional: development first half, development second half, held-out.",
         "OPEN B2 (not ruled): the z of 5.46 is not tied to a sample. Provisional: the held-out bets' day-clustered z (Q1); the development z is printed for information.",
         "OPEN B3 (not ruled): Q1's standard deviation is not said to be the sample one; provisional: the sample standard deviation (n - 1); days without a bet are not days; under 2 days or a zero deviation gives no z, which fails the bar."]


def iso(s):
    from datetime import datetime, timezone
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def fee(p):
    return math.ceil(100 * 0.07 * p * (1 - p) - 1e-9) / 100


def pf_raw(xs):
    """F1: the unrounded PF used by every bar test; inf with no loss, None with no bet."""
    if not xs:
        return None
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return math.inf if l == 0 else g / l


def shown(x):
    return None if x is None else ("inf" if x == math.inf else round(x, 6))


def zday(bets):
    """Q1: day-clustered z, the unit the US Central calendar date of S; None if under 2 days or no spread."""
    day = {}
    for b in bets:
        d = datetime.datetime.fromtimestamp(b["S"], datetime.timezone.utc).astimezone(CENTRAL).date().isoformat()
        day[d] = day.get(d, 0.0) + b["pnl"]
    vals = list(day.values())
    if len(vals) < 2:
        return None, len(vals)
    sd = statistics.stdev(vals)
    if sd == 0:
        return None, len(vals)
    return (sum(vals) / len(vals)) / (sd / math.sqrt(len(vals))), len(vals)


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
        if obs > t:                                                     # Q2: look-ahead
            return "obs_after_point", None
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
    d0 = min(abs(k["K"] - mid) for k in ok)                             # F4: explicit tie test
    k = min((k for k in ok if abs(k["K"] - mid) <= d0 + EPS), key=lambda k: k["K"])
    b, a = k["yes_bid"], k["yes_ask"]
    ask = side_ask(k)
    p = ask                                                           # A10: fill at the ask seen, no +1c
    cost = p + fee(p)
    res = k["result"]
    if res == "void":                                                 # A12, F6
        pnl, void = -fee(p), True
    else:
        pnl, void = (1 - cost) if res == side else -cost, False
    return "bet", {"city": row["city"], "S": S, "K": k["K"], "side": side, "v": v, "s": s, "gap": round(g, 6), "ask": round(ask, 6),
                   "pnl": round(pnl, 6), "void": void, "member": bool(row.get("member")),
                   "day2": (dec * 1000 - row["cal_effective_ms"]) >= 2 * 86400 * 1000}


def summary(bets):
    xs = [b["pnl"] for b in bets]
    p = pf_raw(xs)
    return {"n": len(xs), "pf": shown(p), "pf_raw": p, "net": round(sum(xs), 6), "voids": sum(b["void"] for b in bets)}


def public(x):
    return {k: v for k, v in x.items() if k != "pf_raw"}


def load(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    seen = set()
    for r in rows:
        key = (r["city"], r["S"])
        if key in seen:                                                 # F5
            raise Stop("duplicate row for city %s and S %s" % key)
        seen.add(key)
        for k in r["strikes"]:
            if k.get("result") not in ("yes", "no", "void"):            # F6
                raise Stop("result %r refused (city %s, S %s, K %s)" % (k.get("result"), r["city"], r["S"], k.get("K")))
    return rows


def development(rows, out):
    d0, d1, h, ho0, ho1 = iso(DEV[0]), iso(DEV[1]), iso(HALF), iso(HELD[0]), iso(HELD[1])
    dev, held, decisions = [], [], []
    out["statuses"], out["outside_windows"], out["held_rows"] = {}, 0, 0
    for row in rows:
        S = row["S"]
        win = "dev" if d0 <= S < d1 else ("held" if ho0 <= S < ho1 else None)
        if win is None:
            out["outside_windows"] += 1
            continue
        if win == "held" and out["mode"] == "dev":                     # F3: the development read ignores and counts held-out rows
            out["held_rows"] += 1
            continue
        st, bet = decide(row)
        out["statuses"][st] = out["statuses"].get(st, 0) + 1
        decisions.append({"city": row["city"], "S": S, "window": win, "status": st, "bet": bet})
        if bet:
            (dev if win == "dev" else held).append(bet)
    first = [b for b in dev if b["S"] < h]
    second = [b for b in dev if b["S"] >= h]
    D, F, L = summary(dev), summary(first), summary(second)
    def half_fails(x):
        return x["n"] == 0 or x["pf_raw"] < 1.2                         # F1: unrounded; inf passes, no bet fails (A14)
    kills = {"fewer_than_200": D["n"] < MIN_BETS, "pooled_pf_under_1": D["n"] > 0 and D["pf_raw"] < 1.0,
             "a_half_under_1_2": half_fails(F) or half_fails(L)}
    z, nd = zday(dev)
    out["development"] = {"pooled": public(D), "first_half": public(F), "second_half": public(L),
                          "member": public(summary([b for b in dev if b["member"]])), "non_member": public(summary([b for b in dev if not b["member"]])),
                          "days_0_1_info": public(summary([b for b in dev if not b["day2"]])), "day_2_on_info": public(summary([b for b in dev if b["day2"]])),
                          "z_day_info": shown(z), "days": nd, "kills": kills, "verdict": "CLOSED" if any(kills.values()) else "CONTINUE"}
    out["decisions"] = decisions
    return F, L, held


def run(mode, path, now=None, marker=MARKER):
    out = {"card": "TEMPBLEND_CARD.md 515421f6 (85d8f455)", "mode": mode, "ambiguities": AMBIG}
    if mode not in ("dev", "held"):
        raise Stop("mode must be dev or held")
    if mode == "held":
        now = datetime.datetime.now(datetime.timezone.utc).timestamp() if now is None else now
        if now < iso(HELD_OPEN):                                        # F3
            raise Stop("held-out read refused before %s" % HELD_OPEN)
        if os.path.exists(marker):
            raise Stop("held-out read refused: the read-once marker %s exists" % marker)
    rows = load(path)
    F, L, held = development(rows, out)
    if mode == "held":
        H = summary(held)
        d2 = [b for b in held if b["day2"]]
        H2 = summary(d2)
        if H2["n"] < MIN_DAY2:
            cal = "no evidence at n = %d" % H2["n"]
        else:
            cal = "FAIL" if H2["pf_raw"] < 1.0 else "passes"
        z, nd = zday(held)
        windows_ok = all(x["n"] > 0 and x["pf_raw"] >= BAR_PF for x in (F, L, H))       # B1 provisional, F1 unrounded
        verdict = ("PASS" if out["development"]["verdict"] == "CONTINUE" and windows_ok and z is not None and z >= BAR_Z and cal == "passes"
                   else "NOT PASS")                                                      # F2
        out["held_out"] = {"pooled": public(H), "days_0_1": public(summary([b for b in held if not b["day2"]])), "day_2_on": public(H2),
                           "calibration_kill": cal, "z_day": shown(z), "days": nd, "windows_pf_ok": windows_ok, "verdict": verdict}
        with open(marker, "w") as f:
            f.write("TEMPBLEND held-out read done\n")
    return out


if __name__ == "__main__":
    try:
        res = run(sys.argv[1], sys.argv[2])
    except Stop as e:
        sys.exit("STOPPED: %s" % e)
    with open(sys.argv[3], "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps({k: res[k] for k in ("statuses", "outside_windows", "held_rows")}, sort_keys=True))
    print(json.dumps(res["development"]["kills"]), res["development"]["verdict"], res.get("held_out", {}).get("verdict"))
