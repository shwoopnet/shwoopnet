#!/usr/bin/env python3
"""LIQREV scorer, build 1 (Idea Desk C, Nov 13, 2026). Research only. [research]

Written before any OKX liquidation row or Kalshi row was read, tested only on the hand case
(hand_case_rows.json, hand_case_expected.json, committed first at ee15f5c9). The rule is
LIQREV_CARD.md (claude/idea-desk-c, a16c8e3c); where they differ the card is right. Readings this
build had to fix are R1 to R15 in LIQREV_READINGS.md, for the Head of R&D to rule into the card.
No network request. H (the 99th percentile) is NOT computed here: it is an input, and it stays
uncomputed until Auditor B is CLEAN on the card.

Usage:
  python3 -I liqrev_score.py dev  CASE.json            (refused before 2026-11-30T00:00:00Z)
  python3 -I liqrev_score.py held CASE.json MARKER     (refused before 2027-01-02T00:00:00Z; runs once)
CASE.json: {"H_btc", "coverage": [[start_ms, end_ms], ...] (OKX recorder coverage),
            "liquidations": [{inst_id, ts_ms, side, pos_side, sz, bk_px}, ...],
            "windows": [{ticker, close (ISO UTC), result "yes"|"no"|"void"}, ...],
            "polls": {ticker: [{t_recv_ms, yes_bid_px_1, no_bid_px_1}, ...]}}
"""
import json, math, os, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def ms(iso): return int(datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000)
def iso(m): return datetime.fromtimestamp(m / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

DEV_START, DEV_SPLIT, DEV_END = ms("2026-11-17T00:00:00Z"), ms("2026-11-23T12:00:00Z"), ms("2026-11-30T00:00:00Z")
HELD_START, HELD_END = ms("2026-11-30T00:00:00Z"), ms("2027-01-01T00:00:00Z")
DEV_READ_FROM, HELD_READ_FROM = ms("2026-11-30T00:00:00Z"), ms("2027-01-02T00:00:00Z")
MIN, LOOKBACK = 60000, 180000
SPAN_LO, SPAN_HI = 180000, 720000          # trigger minutes from 12 to 3 minutes before the close, inclusive (R4)
POLL_MAX_WAIT = 10000                      # first poll after t, at most 10 s later (R6)
ASK_LO, ASK_HI, SPREAD_MAX, EPS = 0.20, 0.80, 0.04, 1e-9
CT_VAL = {"BTC-USDT-SWAP": ("btc", 0.01), "BTC-USD-SWAP": ("usd", 100.0)}   # R2
DEV_MIN, NO_EVIDENCE_UNDER, BAR_PF, BAR_Z = 60, 30, 1.5, 5.46
CENTRAL = ZoneInfo("America/Chicago")
RESULTS = ("yes", "no", "void")

def fee(p): return math.ceil(0.07 * p * (1 - p) * 100 - EPS) / 100

def btc(r):
    kind, v = CT_VAL[r["inst_id"]]
    sz = float(r["sz"])
    return sz * v if kind == "btc" else sz * v / float(r["bk_px"])

def dedupe(rows):                          # R12: the recorder's own key
    seen, out = set(), []
    for r in rows:
        k = (r["inst_id"], int(r["ts_ms"]), r["side"], r.get("pos_side", ""), str(r["bk_px"]), str(r["sz"]))
        if k not in seen:
            seen.add(k); out.append(r)
    return out

def covered(cov, a, b):                    # R15: [a, b) inside one recorded interval
    return any(s <= a and b <= e for s, e in cov)

def L(rows, side, t):                      # R1, R3: side "sell" = long positions liquidated
    return sum(btc(r) for r in rows if r["side"] == side and t - LOOKBACK <= int(r["ts_ms"]) < t)

def window_of(close):
    if DEV_START <= close < DEV_SPLIT: return "dev1"
    if DEV_SPLIT <= close < DEV_END: return "dev2"
    if HELD_START <= close < HELD_END: return "held"
    return None

def decide(w, rows, polls, H, cov):
    close = ms(w["close"])
    wn = window_of(close)
    if wn is None: return None, "outside_windows"
    if not covered(cov, close - SPAN_HI - LOOKBACK, close - SPAN_LO):
        return None, "no_liq_coverage"
    for t in range(close - SPAN_HI, close - SPAN_LO + 1, MIN):        # 12 to 3 minutes before, in order
        ls, ss = L(rows, "sell", t), L(rows, "buy", t)
        if ls < H - EPS and ss < H - EPS: continue
        if ls >= H - EPS and ss >= H - EPS:                             # R5b: both sides at once: no bet
            return None, "both_sides"
        side, lv = ("yes", ls) if ls >= H - EPS else ("no", ss)
        after = [p for p in polls.get(w["ticker"], []) if t < p["t_recv_ms"] <= t + POLL_MAX_WAIT]
        if not after: return None, "no_quote"
        p = min(after, key=lambda x: x["t_recv_ms"])
        yb, nb = p.get("yes_bid_px_1"), p.get("no_bid_px_1")
        if yb is None or nb is None: return None, "no_quote"
        ya = round(1 - nb, 6)
        if not (0 < yb < ya < 1): return None, "no_quote"
        ask = ya if side == "yes" else round(1 - yb, 6)
        if not (ASK_LO - EPS <= ask <= ASK_HI + EPS) or ya - yb > SPREAD_MAX + EPS:
            return None, "band_or_spread"                               # R7: the window is used
        f = fee(ask); res = w["result"]
        pnl = round(-f if res == "void" else ((1 - ask - f) if res == side else -(ask + f)), 4)
        day = datetime.fromtimestamp(close / 1000, timezone.utc).astimezone(CENTRAL).date().isoformat()
        return {"ticker": w["ticker"], "trigger_minute": iso(t), "side": side, "L_btc": round(lv, 6),
                "ask": ask, "fee": f, "pnl": pnl, "won": res == side, "void": res == "void",
                "window": wn, "day": day}, None
    return None, "no_trigger"

def stats(bets):
    n = len(bets)
    w = sum(b["pnl"] for b in bets if b["pnl"] > 0); l = -sum(b["pnl"] for b in bets if b["pnl"] < 0)
    pf = None if n == 0 else (math.inf if l == 0 else w / l)
    days = {}
    for b in bets: days[b["day"]] = days.get(b["day"], 0.0) + b["pnl"]
    D, z = len(days), None
    if D >= 2:
        m = sum(days.values()) / D
        sd = math.sqrt(sum((x - m) ** 2 for x in days.values()) / (D - 1))
        z = None if sd == 0 else m / (sd / math.sqrt(D))
    return {"n": n, "won": sum(b["won"] for b in bets), "void": sum(b["void"] for b in bets), "days": D,
            "pf": pf, "net": sum(b["pnl"] for b in bets), "z": z}

def shown(s):
    o = dict(s); pf = s["pf"]
    o["pf"] = None if pf is None else ("inf" if pf == math.inf else round(pf, 4))
    o["net"] = round(s["net"], 4); o["z"] = None if s["z"] is None else round(s["z"], 4)
    return o

def pfv(s): return 0.0 if s["pf"] is None else s["pf"]

def check(case):
    seen = set()
    for w in case["windows"]:
        if w["ticker"] in seen: raise ValueError("duplicate window %s" % w["ticker"])
        seen.add(w["ticker"])
        if w.get("result") not in RESULTS: raise ValueError("result %r for %s" % (w.get("result"), w["ticker"]))
    for r in case["liquidations"]:
        if r["inst_id"] not in CT_VAL: raise ValueError("unknown instrument %r" % r["inst_id"])
        if r["side"] not in ("buy", "sell"): raise ValueError("unknown side %r" % r["side"])

def score(case, mode="dev"):
    check(case)
    H, cov = float(case["H_btc"]), case["coverage"]
    rows = dedupe(case["liquidations"])
    bets, skips = [], {}
    for w in case["windows"]:
        b, why = decide(w, rows, case["polls"], H, cov)
        if b and mode == "dev" and b["window"] == "held": b, why = None, "held_window_ignored"
        if b is None and why != "outside_windows" and mode == "dev" and window_of(ms(w["close"])) == "held":
            why = "held_window_ignored"
        if b: bets.append(b)
        else: skips[why] = skips.get(why, 0) + 1
    dev = [b for b in bets if b["window"] in ("dev1", "dev2")]
    d, d1, d2 = stats(dev), stats([b for b in dev if b["window"] == "dev1"]), stats([b for b in dev if b["window"] == "dev2"])
    triggered = len(bets) + skips.get("band_or_spread", 0)
    out = {"mode": mode, "bets": bets, "skips": dict(sorted(skips.items())), "dev": shown(d), "dev1": shown(d1), "dev2": shown(d2)}
    if triggered - (len([b for b in bets if b["window"] == "held"])) < DEV_MIN:
        out["dev_verdict"] = "CLOSED (zero-try count: under %d triggered windows with a two-sided quote)" % DEV_MIN
    elif d["n"] < DEV_MIN or pfv(d) < 1.0 or pfv(d1) < 1.2 or pfv(d2) < 1.2:
        out["dev_verdict"] = "CLOSED"
    else:
        out["dev_verdict"] = "CONTINUE"
    if d["n"] < NO_EVIDENCE_UNDER: out["dev_label"] = "no evidence at n = %d" % d["n"]
    if mode == "held":
        h = stats([b for b in bets if b["window"] == "held"])
        out["held"] = shown(h)
        if h["n"] < NO_EVIDENCE_UNDER: out["held_verdict"] = "NO_EVIDENCE at n = %d" % h["n"]
        elif out["dev_verdict"] == "CONTINUE" and all(pfv(x) >= BAR_PF for x in (d1, d2, h)) and (h["z"] or 0) >= BAR_Z:
            out["held_verdict"] = "PASS"
        else:
            out["held_verdict"] = "FALSIFIED (the liquidation-fade family closes for good)"
    return out

def guard(mode, now, marker=None):
    if mode == "dev" and now < DEV_READ_FROM: raise SystemExit("refused: the development read opens at 2026-11-30T00:00:00Z")
    if mode == "held":
        if now < HELD_READ_FROM: raise SystemExit("refused: the held-out read opens at 2027-01-02T00:00:00Z")
        if os.path.exists(marker): raise SystemExit("refused: the held-out read already ran (%s)" % marker)

if __name__ == "__main__":
    mode, case = sys.argv[1], json.load(open(sys.argv[2]))
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    guard(mode, now, sys.argv[3] if mode == "held" else None)
    out = score(case, mode)
    if mode == "held":
        with open(sys.argv[3], "x") as f: f.write("LIQREV held-out read at %s\n" % iso(now))
    out["bets"] = [{k: v for k, v in b.items() if k not in ("won", "void", "window", "day")} for b in out["bets"]]
    print(json.dumps(out, indent=1, sort_keys=True))
