#!/usr/bin/env python3
"""MAPBREAK state-observability count (Testing Desk, Nov 13, 2026; Head's request 00:04Z). COUNTS ONLY, no match result, no bet, no rule. Imports the frozen mapbreak.py and breakplay.py without changing them.
For each record (a best-of-three whose map-1 result is the state) and look: the FINAL candle of the winner's own map contract at or before the map market's close (one-sided books allowed): did it show the state, by (a) best bid 0.90 or more, (b) last trade price 0.90 or more, (c) either. Reported by title and look, with how many records had no candle at all at or before close.
Usage: mapbreak_statecheck.py <lists folders...> --candles <candle folders...>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
import mapbreak as m


def run(list_folders, candle_folders):
    spec = m.load_cells(); recs, _ = m.matches(spec, list_folders)
    ser = {t: sorted(v, key=lambda c: c["ts"]) for t, v in k.candles(candle_folders).items()}
    out = {}
    for r in recs:
        for look, tk, sc in ((1, r["placebo"][r["up"]], r["state_close"]), (2, r.get("state_ticker2"), r.get("state_close2"))):
            if not tk: continue
            P = out.setdefault((r["cell"], look), {"records": 0, "no_candle_pulled_or_before_close": 0, "bid_ge_90": 0, "trade_ge_90": 0, "either": 0, "both_none": 0, "last_candle_minutes_before_close": []})
            cs = [c for c in ser.get(tk, []) if c["ts"] <= sc]
            if tk not in ser: continue                                           # that request was not pulled: not counted as a record
            P["records"] += 1
            if not cs: P["no_candle_pulled_or_before_close"] += 1; continue
            c = cs[-1]; b = c["bid"] is not None and c["bid"] >= 0.90 - 1e-9; t = c.get("price") is not None and c["price"] >= 0.90 - 1e-9
            P["bid_ge_90"] += b; P["trade_ge_90"] += t; P["either"] += (b or t); P["both_none"] += (c["bid"] is None and c.get("price") is None)
            P["last_candle_minutes_before_close"].append((sc - c["ts"]) / 60)
    res = {}
    for (cell, look), P in sorted(out.items()):
        n = P["records"] - P["no_candle_pulled_or_before_close"]; mins = sorted(P.pop("last_candle_minutes_before_close"))
        res["%s|look%d" % (cell, look)] = dict(P, with_a_candle=n, share_bid_ge_90=None if not n else round(P["bid_ge_90"] / n, 3), share_trade_ge_90=None if not n else round(P["trade_ge_90"] / n, 3), share_either=None if not n else round(P["either"] / n, 3),
                                                median_minutes_final_candle_before_close=None if not mins else round(mins[len(mins) // 2], 1))
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--candles" not in a: print(__doc__)
    else: i = a.index("--candles"); print(json.dumps(run(a[:i], a[i + 1:]), indent=1))
