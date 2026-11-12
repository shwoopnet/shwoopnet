#!/usr/bin/env python3
"""breakplay: the GENERIC break-in-play engine (Testing Desk, Nov 12, 2026; Head's 18:24Z request). A new venue of the break-in-play family is a series file plus a small `discover` function and config, not a new program.
Family: a state change read from a sibling market's OWN close and result while play is stopped; a model value from the PRE-MATCH price; a look a fixed time after the state market closes; a placebo at the pre-match instant;
cost and share kill lines; the held-out never requested. Research only: reads files, sends nothing.

A venue supplies RECORDS (one per match), each a dict:
  cell, key, S (scheduled start, epoch), state_close (epoch: when the state market closed), up, down (team ids: `up` is ahead after the state change), 
  match {team: ticker} (the contracts bought and sold), placebo {team: ticker} (contracts that price the SAME single-state number at the pre-match instant),
  and OPTIONALLY `result_up` (True if `up` won the match) added ONLY by the venue's scoring path, never by the measurement path.
and a CONFIG (VenueConfig): model name, pre-match offsets, look offsets, thresholds. Models in MODELS map the pre-match mid of the `up` team's match contract to (value_up, value_down, placebo_up, placebo_down).

Engine pieces:  pre_match_minute | look_minute | measure (zero-try gap measurement, no result) | candle_job (packs by start) | score_rule (a registered RULE: development read only; cash PF with n by window, event-clustered z, the haircut line)
Conditions enforced here: two-sided minute-end candles only (0 < bid < ask < 1), nothing filled from another minute; the look moves FORWARD only; the pre-match search moves BACK only; held-out records are refused by a date constant;
the measurement path never touches `result_up`; score_rule refuses a record whose state_close is on or after the venue's held-out constant unless `heldout_go` is True (the Head's go, default False).
"""
import statistics as st, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
import tie3

EDGE, SPREAD_MAX, COST_MAX, EDGE_SHARE, MIN_FILLED = 0.08, 0.04, 0.05, 0.10, 150


class VenueConfig:
    def __init__(self, name, model, pre_back=600, pre_max_back=2400, look_after=120, look_max=300, heldout_from=None, freshness="candle freshness measured on Bitcoin 15 minute only, not on this venue",
                 edge=EDGE, spread_max=SPREAD_MAX, cost_max=COST_MAX, edge_share=EDGE_SHARE, min_filled=MIN_FILLED, pack_limit=9000, max_tickers=100):
        self.__dict__.update(locals()); del self.__dict__["self"]


def solve_q(p, f):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if f(mid) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def model_bo3(p):
    """Best of three: the pre-match match price p of the team that went on to win map 1 gives the single-map chance q (p = q*q*(3-2q)); one map up is worth V = 1-(1-q)^2. Placebo: q and 1-q."""
    q = solve_q(p, lambda x: x * x * (3 - 2 * x)); V = 1 - (1 - q) ** 2
    return V, 1 - V, q, 1 - q


def model_bo5_after_map1(p):
    """Best of five, one map up (first to three): single-map chance q from p = P(win >= 3 of 5 maps at q); one map up is worth P(win >= 2 of the remaining 4 maps at q)."""
    from math import comb
    f = lambda x: sum(comb(5, j) * x ** j * (1 - x) ** (5 - j) for j in range(3, 6))
    q = solve_q(p, f); V = sum(comb(4, j) * q ** j * (1 - q) ** (4 - j) for j in range(2, 5))
    return V, 1 - V, q, 1 - q


MODELS = {"bo3": model_bo3, "bo5_after_map1": model_bo5_after_map1}


def two(idx, t, ts):
    c = idx.get(t, {}).get(ts)
    if not c or c["bid"] is None or c["ask"] is None or not (0 < c["bid"] < c["ask"] < 1): return None
    return c["bid"], c["ask"]


def rt(b, a):
    mid = (a + b) / 2
    return (a - b) + 2 * 0.07 * mid * (1 - mid)


def pre_match_minute(idx, rec, cfg):
    """The candle ending at S - pre_back, stepping BACK a minute at a time to S - pre_max_back, first minute at which the match contract of `up` and BOTH placebo contracts are two-sided. None if none."""
    need = [rec["match"][rec["up"]], rec["placebo"][rec["up"]], rec["placebo"][rec["down"]]]
    for back in range(cfg.pre_back, cfg.pre_max_back + 1, 60):
        if all(two(idx, t, rec["S"] - back) for t in need): return rec["S"] - back
    return None


def pre_match_dropped_match_ok(idx, rec, cfg):
    """Desk B's added count: dropped although the match contract of `up` was two-sided at some minute of the window."""
    return any(two(idx, rec["match"][rec["up"]], rec["S"] - b) for b in range(cfg.pre_back, cfg.pre_max_back + 1, 60))


def look_minute(idx, rec, cfg):
    """The candle ending at the first whole minute at or after state_close + look_after, stepping FORWARD to state_close + look_max until both match contracts are two-sided."""
    t0 = -(-(rec["state_close"] + cfg.look_after) // 60) * 60
    for ts in range(t0, rec["state_close"] + cfg.look_max + 1, 60):
        if all(two(idx, rec["match"][x], ts) for x in (rec["up"], rec["down"])): return ts
    return None


def prepare(idx, rec, cfg):
    """-> dict(pre, look, V, placebo gaps, per-side candidate gaps) or a reason string. No result is touched."""
    pre = pre_match_minute(idx, rec, cfg)
    if pre is None: return "no_pre"
    pm = sum(two(idx, rec["match"][rec["up"]], pre)) / 2
    Vu, Vd, qu, qd = MODELS[cfg.model](pm)
    plc = {}
    for side, team, val in (("up", rec["up"], qu), ("down", rec["down"], qd)):
        b, a = two(idx, rec["placebo"][team], pre); plc[side] = {"gap": val - a, "spread": a - b, "side": side}
    best_p = max(plc, key=lambda s: plc[s]["gap"])
    look = look_minute(idx, rec, cfg)
    out = {"pre": pre, "placebo": plc[best_p], "look": None}
    if look is None: return dict(out, reason="no_look")
    cand = {}
    for side, team, val in (("up", rec["up"], Vu), ("down", rec["down"], Vd)):
        b, a = two(idx, rec["match"][team], look)
        cand[side] = {"gap": val - a, "spread": a - b, "side": side, "ask": a, "team": team, "rt": rt(b, a)}
    return dict(out, look=look, cand=cand, best=max(cand, key=lambda s: cand[s]["gap"]))


def stat(rows):
    if not rows: return None
    g = [r["gap"] for r in rows]; q = st.quantiles(g, n=4, method="inclusive") if len(g) > 2 else None; d = st.quantiles(g, n=10, method="inclusive") if len(g) > 2 else None
    fire = [r for r in rows if r["gap"] >= EDGE and r["spread"] <= SPREAD_MAX]
    return {"n": len(rows), "gap_median": round(st.median(g), 4), "gap_quartiles": None if not q else [round(q[0], 4), round(q[2], 4)], "gap_p90": None if not d else round(d[8], 4),
            "share_gap_ge_8c_spread_le_4c": round(len(fire) / len(rows), 3), "share_when_team_up": round(sum(1 for r in fire if r.get("side") == "up") / len(rows), 3), "share_when_team_down": round(sum(1 for r in fire if r.get("side") == "down") / len(rows), 3)}


def measure(records, candle_folders, cfg):
    """The zero-try gap measurement. Touches no result."""
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candle_folders).items()}
    per = {}
    for rec in records:
        assert "result_up" not in rec, "the measurement path must not carry a result"
        P = per.setdefault(rec["cell"], {"sampled": 0, "pre": 0, "look": [], "placebo": [], "minutes": [], "rts": [], "spreads": [], "pre_dropped_match_ok": 0, "look_filled": 0})
        P["sampled"] += 1
        r = prepare(idx, rec, cfg)
        if r == "no_pre":
            if pre_match_dropped_match_ok(idx, rec, cfg): P["pre_dropped_match_ok"] += 1
            continue
        P["pre"] += 1; P["placebo"].append(r["placebo"])
        if r["look"] is None: continue
        P["look_filled"] += 1; P["minutes"].append((r["look"] - rec["state_close"]) / 60)
        for s in ("up", "down"): P["rts"].append(r["cand"][s]["rt"]); P["spreads"].append(r["cand"][s]["spread"])
        P["look"].append(r["cand"][r["best"]])
    titles, verdicts = {}, []
    for cell, P in sorted(per.items()):
        s_l, s_p = stat(P["look"]), stat(P["placebo"]); n = P["look_filled"]; medrt = None if not P["rts"] else round(st.median(P["rts"]), 4)
        if n < cfg.min_filled: v = "no evidence at n = %d filled at the look" % n
        elif medrt > cfg.cost_max: v = "CLOSED on cost: median round trip %.1fc at the look is above 5c" % (100 * medrt)
        elif s_l["share_gap_ge_8c_spread_le_4c"] >= cfg.edge_share and s_l["share_gap_ge_8c_spread_le_4c"] >= 2 * (s_p["share_gap_ge_8c_spread_le_4c"] if s_p else 0): v = "SURVIVES the measurement (share at least 10 percent and at least twice the placebo's): a separate registration and the Head's go"
        else: v = "CLOSED: efficient, move on. The one number: the 90th percentile gap %s" % s_l["gap_p90"]
        verdicts.append(v)
        titles[cell] = {"sampled": P["sampled"], "filled_pre_match": P["pre"], "dropped_pre_match_with_match_contract_ok_but_placebo_contracts_not_in_the_same_minute": P["pre_dropped_match_ok"], "filled_at_the_look": n,
                        "median_minutes_state_close_to_look": None if not P["minutes"] else round(st.median(P["minutes"]), 2), "median_spread_at_look": None if not P["spreads"] else round(st.median(P["spreads"]), 4),
                        "median_round_trip_at_look": medrt, "look": s_l, "placebo": s_p, "verdict": v}
    return {"titles": titles, "tries_added": 0, "rule_scored": False, "result_read": False, "freshness": cfg.freshness,
            "card": "CLOSED: every cell is closed or has no evidence" if verdicts and all(not v.startswith("SURVIVES") for v in verdicts) else ("a cell survives the measurement" if verdicts else "no cell measured")}


def rule_trades(records, candle_folders, cfg, heldout_go=False):
    """REGISTERED RULE (development read): at the look buy 1 contract of the cheaper side's own match contract at its ask when its gap is 8c or more and its spread 4c or less; hold to the end of the match.
    `records` here MAY carry result_up (added by the venue's scoring path). Held-out records (state_close at or after cfg.heldout_from) are refused unless heldout_go. Returns (trades, counts)."""
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candle_folders).items()}
    trades, counts = [], {"records": 0, "held_out_refused": 0, "no_pre": 0, "no_look": 0, "no_signal": 0, "traded": 0, "no_result": 0}
    for rec in records:
        counts["records"] += 1
        if cfg.heldout_from is not None and rec["state_close"] >= cfg.heldout_from and not heldout_go:
            counts["held_out_refused"] += 1; continue
        r = prepare(idx, rec, cfg)
        if r == "no_pre": counts["no_pre"] += 1; continue
        if r["look"] is None: counts["no_look"] += 1; continue
        c = r["cand"][r["best"]]
        if not (c["gap"] >= cfg.edge and c["spread"] <= cfg.spread_max): counts["no_signal"] += 1; continue
        if "result_up" not in rec: counts["no_result"] += 1; continue
        win = rec["result_up"] if r["best"] == "up" else (not rec["result_up"])
        trades.append({"event": rec["key"], "cluster": rec["key"], "day": rec["S"] // 86400, "ts": r["look"], "price": c["ask"], "win": bool(win), "side": r["best"], "gap": c["gap"], "cell": rec["cell"]}); counts["traded"] += 1
    return trades, counts


def score_rule(records, candle_folders, cfg, heldout_go=False, name="break-in-play rule"):
    """Cash PF with n by window (three chronological windows), event-clustered z (one trade per match), day-clustered z beside it, the haircut line; labels per the standing rules. Development read only unless heldout_go."""
    trades, counts = rule_trades(records, candle_folders, cfg, heldout_go)
    out = k.score(trades, {"name": name, "price_source": "1 minute candle ask close at the look (a minute-end candle, two-sided, not a list quote)", "freshness": cfg.freshness,
                           "book_replay": "NOT PROVIDED: no order book exists for these markets; the haircut table stands in (an ask two minutes into a break may be one contract deep)"}) if trades else {"n": 0, "label": "no evidence at n = 0"}
    if trades:
        out["day_clustered_z"] = k.cluster_z([dict(t, cluster=str(t["day"])) for t in trades])
        out["by_side"] = {s: {"n": sum(1 for t in trades if t["side"] == s)} for s in ("up", "down")}
    return {"counts": counts, "result": out, "development_read_only": not heldout_go, "tries": "the one registered try of the card (the measurement stage itself is zero tries)"}


def candle_job(records, cfg, series, job_id, registration, window_start_back=2400, window_end_after=300):
    """Pack records by scheduled start: per record the match and placebo contracts from S - window_start_back to state_close + window_end_after; matches in one request share its window; minutes x tickers <= pack_limit, tickers <= max_tickers."""
    ms = sorted(records, key=lambda m: (m["S"], m["key"])); packs, cur = [], []
    tk = lambda m: list(m["match"].values()) + list(m["placebo"].values())
    def win(g): return (max(m["state_close"] for m in g) + window_end_after) - (min(m["S"] for m in g) - window_start_back)
    for m in ms:
        trial = cur + [m]
        if cur and (win(trial) / 60 * sum(len(tk(x)) for x in trial) > cfg.pack_limit or sum(len(tk(x)) for x in trial) > cfg.max_tickers): packs.append(cur); cur = [m]
        else: cur = trial
    if cur: packs.append(cur)
    reqs = [{"id": "c%04d" % i, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for m in g for t in tk(m)), "start_ts": min(m["S"] for m in g) - window_start_back - 60,
             "end_ts": max(m["state_close"] for m in g) + window_end_after, "period_interval": 1}} for i, g in enumerate(packs)]
    eps = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}]
    j = tie3.job(job_id, "break-in-play measurement stage 2: one minute candles of the match and placebo contracts of the sampled matches.", eps, reqs, series, [t for m in ms for t in tk(m)])
    j["registration"] = registration; return j
