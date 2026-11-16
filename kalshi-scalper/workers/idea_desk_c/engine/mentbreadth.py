#!/usr/bin/env python3
"""MENTBREADTH plugin (Idea Desk C, Nov 16, 2026), build 1: words in Trump mention events that list many words.
Breadth of a word at its decision time D (its own open + 30 min) = the words of its event already open at D. Wide (breadth >= 27, the
development median of breadth over all 2,768 words, from open times only): buy NO when the NO ask (1 - YES bid) is 0.30 to 0.70.
Read sample: the first 460 wide words by md5("MENTBREADTH-2026-11-16" + ticker). Card: ../allkalshi/mentbreadth/MENTBREADTH_CARD.md."""
import hashlib, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL

SERIES = ("KXTRUMPMENTION", "KXTRUMPMENTIONB")
LIST_JOBS = ("MENTDRIFT_LISTS_A",)
CANDLE_JOBS = ("MENTBREADTH_CANDLES_P1",)
DEV = (KL.iso("2026-04-17T00:00:00"), KL.iso("2026-08-06T00:00:00"))
ENTRY_AFTER_OPEN_S, LOOKBACK_S = 1800, 180
WIDE, BAND, N, SEED, N_READ = 27, (0.30, 0.70), 10, "MENTBREADTH-2026-11-16", 460


def wide_words(mk):
    ev = {}
    for t, r in mk.items():
        if "does not qualify" in (r["yes_sub_title"] + " " + r["title"]).lower() or r["open_time"] is None:
            continue
        ev.setdefault(r["event"], []).append(r)
    out = []
    for e, L in ev.items():
        for r in L:
            D = r["open_time"] + ENTRY_AFTER_OPEN_S
            if r["close_time"] <= D:
                continue
            if sum(1 for x in L if x["open_time"] <= D) >= WIDE:
                out.append((D, r))
    out.sort(key=lambda x: (hashlib.md5((SEED + x[1]["ticker"]).encode("ascii")).hexdigest(), x[1]["ticker"]))
    return out[:N_READ], len(out)


def build(root):
    mk = KL.markets(root, LIST_JOBS, SERIES, "occurrence", *DEV)
    return wide_words(mk)


def entries(root):
    ws, nwide = build(root)
    q = KL.quotes(root, CANDLE_JOBS, {r["ticker"]: D for D, r in ws})
    out, why = [], {}
    for D, r in ws:
        qt = KL.quote_at(q.get(r["ticker"], {}), D, LOOKBACK_S)
        if qt is None:
            why["no_two_sided_quote"] = why.get("no_two_sided_quote", 0) + 1
            continue
        ask = round(1 - qt[0], 6)
        if not (BAND[0] - KL.EPS <= ask <= BAND[1] + KL.EPS):
            why["out_of_band"] = why.get("out_of_band", 0) + 1
            continue
        why["ok"] = why.get("ok", 0) + 1
        out.append({"id": r["ticker"], "close_ts": r["close_time"], "day": r["event"], "series": r["series"], "side": "no", "ask": ask,
                    "n": N, "entry_end": D, "path": [], "event": r["event"]})
    res = KL.results(root, LIST_JOBS, {e["id"] for e in out})      # LAST
    for e in out:
        e["result"] = res.get(e["id"], "")
    return [e for e in out if e["result"] in ("yes", "no", "void")], why, nwide
