"""LADDERSTATE1: does the quote recorder's ladder.csv (hourly ladder strikes, read from the market list) show the same cached copy as quotes.csv?

A measurement on the recorder's own rows: no rule, no settlement result, no order book needed, zero tries. No network, no account data.
usage: python3 -I ladderstate1.py <quotes_root> <out_json>
"""
import sys, glob, os, json
import numpy as np
import pandas as pd

QROOT, OUT = sys.argv[1], sys.argv[2]
out = {"test": "LADDERSTATE1", "note": "a 'state' is a run of consecutive polls of one ticker with the same bid, ask and sizes; gaps are seconds between state changes inside one run folder"}
parts = []
for f in sorted(glob.glob(os.path.join(QROOT, "quotes", "*", "*", "ladder.csv.gz"))):
    d = pd.read_csv(f, dtype={"ticker": str, "status": str})
    d["run"] = os.path.dirname(f)
    parts.append(d)
L = pd.concat(parts, ignore_index=True)
L = L[L["status"].str.lower().isin(["active", "open"])].sort_values(["run", "ticker", "t_recv_ms"])
L["series"] = L["ticker"].str.split("-").str[0]
key = ["yes_bid", "yes_ask", "bid_size", "ask_size"]
g = L.groupby(["run", "ticker"], sort=False)
prev = g[key].shift(1)
first = prev["yes_bid"].isna() & prev["yes_ask"].isna()
L["chg"] = (~first) & (L[key].fillna(-1).to_numpy() != prev.fillna(-1).to_numpy()).any(axis=1)
L["dt"] = (L["t_recv_ms"] - g["t_recv_ms"].shift(1)) / 1000.0
out["files"] = len(parts)
for s, G in L.groupby("series"):
    polls = int((~first.loc[G.index]).sum()); changes = int(G["chg"].sum())
    c = G[G["chg"]]
    gaps = (c["t_recv_ms"] - c.groupby(["run", "ticker"])["t_recv_ms"].shift(1)).dropna() / 1000.0
    gaps = gaps[gaps < 60]
    out[s] = {"polls": polls, "state_changes": changes, "polls_per_state": round(polls / max(changes, 1), 2),
              "poll_spacing_s_median": round(float(G["dt"].dropna()[G["dt"].dropna() < 30].median()), 2),
              "seconds_between_changes_p25_p50_p75": [round(float(v), 2) for v in np.percentile(gaps, [25, 50, 75])] if len(gaps) else None,
              "share_of_gaps_9_to_14s": round(float(((gaps >= 9) & (gaps <= 14)).mean()), 4) if len(gaps) else None}
# do the tickers of one poll cycle refresh together? group rows of a series into cycles by send time (within 1.5 s)
L = L.sort_values(["run", "series", "t_send_ms"])
newc = (L.groupby(["run", "series"])["t_send_ms"].diff().fillna(1e9) > 1500)
L["cycle"] = newc.cumsum()
cy = L[~first.reindex(L.index)].groupby("cycle")["chg"].agg(["sum", "count"])
cy = cy[cy["count"] >= 5]
out["within_one_poll_cycle"] = {"cycles_with_5_or_more_strikes": int(len(cy)), "none_changed": round(float((cy["sum"] == 0).mean()), 4),
                                "all_changed": round(float((cy["sum"] == cy["count"]).mean()), 4), "some_changed": round(float(((cy["sum"] > 0) & (cy["sum"] < cy["count"])).mean()), 4)}
json.dump(out, open(OUT, "w"), indent=1)
print(json.dumps(out, indent=1))
