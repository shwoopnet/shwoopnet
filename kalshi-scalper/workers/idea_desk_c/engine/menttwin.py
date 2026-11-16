#!/usr/bin/env python3
"""MENTTWIN plugin (Idea Desk C, Nov 16, 2026), build 1: the same Trump mention word listed in two events with the same ticker date.
Event builder, decision and entries for engine1_core. Card: ../allkalshi/menttwin/MENTTWIN_CARD.md. Data through deskc_kp_load only."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL

SERIES = ("KXTRUMPMENTION", "KXTRUMPMENTIONB")
LIST_JOBS = ("MENTDRIFT_LISTS_A",)
CANDLE_JOBS = ("MENTTWIN_CANDLES_P1", "MENTTWIN_CANDLES_P2")
DEV = (KL.iso("2026-04-17T00:00:00"), KL.iso("2026-08-06T00:00:00"))   # own occurrence window
ENTRY_AFTER_OPEN_S, LOOKBACK_S = 1800, 180
GAP, BAND, N = 0.15, (0.30, 0.70), 10


def word(rec):
    return (rec["yes_sub_title"] or "").strip().lower()


def pairs(mk):
    """(D, cheap-candidate tickers a, b) per twin set: the same word, the same ticker date code, different events, both open at D.
    A word in more than two events gives one pair: the two events whose markets opened first (ties by ticker)."""
    groups = {}
    for t, r in mk.items():
        w = word(r)
        if not w or "does not qualify" in (w + " " + r["title"].lower()):
            continue
        parts = t.split("-")
        if len(parts) < 3:
            continue
        groups.setdefault((parts[1][:7], w), []).append(r)
    out = []
    for (dcode, w), rs in sorted(groups.items()):
        by_ev = {}
        for r in sorted(rs, key=lambda r: (r["open_time"] or 0, r["ticker"])):
            by_ev.setdefault(r["event"], r)
        if len(by_ev) < 2:
            continue
        a, b = sorted(by_ev.values(), key=lambda r: (r["open_time"] or 0, r["ticker"]))[:2]
        if a["open_time"] is None or b["open_time"] is None:
            continue
        D = max(a["open_time"], b["open_time"]) + ENTRY_AFTER_OPEN_S
        if a["close_time"] <= D or b["close_time"] <= D:
            continue
        out.append((D, a, b))
    return out


def decide(D, qa, qb, a, b):
    """-> entry dict or (None, reason). qa, qb: two-sided (yes_bid, yes_ask) at D."""
    ma, mb = (qa[0] + qa[1]) / 2, (qb[0] + qb[1]) / 2
    if abs(ma - mb) < GAP - KL.EPS:
        return None, "small_gap"
    r, q = (a, qa) if ma < mb else (b, qb)            # buy YES on the cheaper twin
    ask = round(q[1], 6)
    if not (BAND[0] - KL.EPS <= ask <= BAND[1] + KL.EPS):
        return None, "out_of_band"
    return {"id": r["ticker"], "close_ts": r["close_time"], "day": time.strftime("%Y-%m-%d", time.gmtime(D)), "series": r["series"],
            "side": "yes", "ask": ask, "n": N, "entry_end": D, "path": [], "event": r["event"]}, "ok"


def build(root):
    mk = KL.markets(root, LIST_JOBS, SERIES, "occurrence", *DEV)
    return mk, pairs(mk)


def list_ok(root):
    """Auditor B (Nov 16): refuse a cut list. Every list request's last stored page must have no cursor, or reach before the window."""
    return not any(KL.truncated(root, "MENTDRIFT_LISTS_A", rid, DEV[0]) for rid in ("hist_KXTRUMPMENTION", "hist_KXTRUMPMENTIONB"))


def entries(root):
    if not list_ok(root):
        raise SystemExit("list truncated: not scored")
    mk, ps = build(root)
    cut = {}
    for D, a, b in ps:
        cut[a["ticker"]] = D
        cut[b["ticker"]] = D
    q = KL.quotes(root, CANDLE_JOBS, cut)
    out, why = [], {}
    for D, a, b in ps:
        qa, qb = KL.quote_at(q.get(a["ticker"], {}), D, LOOKBACK_S), KL.quote_at(q.get(b["ticker"], {}), D, LOOKBACK_S)
        if qa is None or qb is None:
            why["no_two_sided_quote"] = why.get("no_two_sided_quote", 0) + 1
            continue
        e, r = decide(D, qa, qb, a, b)
        why[r] = why.get(r, 0) + 1
        if e:
            out.append(e)
    res = KL.results(root, LIST_JOBS, {e["id"] for e in out})      # LAST
    for e in out:
        e["result"] = res.get(e["id"], "")
    return [e for e in out if e["result"] in ("yes", "no", "void")], why, len(ps)
