"""CLI: python -I -m stocks_desk.run_card CARD --daily FILE [--minute FILE] [--heldout]
Reads CSV/parquet from SCRATCH (never from the repo). Prints a report; writes nothing except the
held-out read-once marker. Default is DEVELOPMENT ONLY (dates before 2024-07-01).
"""
import argparse, json, sys
import pandas as pd
from . import common as C, scorers as S

JUDGED = {"S1", "S2", "S7"}

def load(p, dates):
    df = pd.read_parquet(p) if p.endswith(".parquet") else pd.read_csv(p)
    for c in dates:
        df[c] = pd.to_datetime(df[c])
    return df

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("card"); ap.add_argument("--daily"); ap.add_argument("--minute")
    ap.add_argument("--heldout", action="store_true"); a = ap.parse_args(argv)
    daily = load(a.daily, ["date"]); minute = load(a.minute, ["ts"]) if a.minute else None
    if a.heldout:
        C.read_heldout_once(a.card)
        # Keep earlier rows as lookback (signals need history, all of it is in the past); the PNL is cut to W3 below.
    else:
        daily = daily[daily["date"] < C.HELDOUT_START]
        if minute is not None: minute = minute[minute["ts"] < C.HELDOUT_START]
    spy = daily[daily["symbol"] == "SPY"]
    runs = {"S1": lambda: S.s1_overnight_etf(daily), "S2": lambda: S.s2_clientele(daily, long_only=False),
            "S3": lambda: S.s3_reversal(daily), "S4": lambda: S.s4_gap_fade(daily), "S5": lambda: S.s5_post_gap(daily),
            "S6": lambda: S.s6_lev_etf(minute, spy), "S7": lambda: S.s7_first30_last30(minute, spy)}
    pnl, meta = runs[a.card]()
    if a.heldout:
        pnl = pnl[pnl.index >= C.HELDOUT_START]     # score ONLY the held-out window
    win = C.per_window(pnl.values, pnl.index)
    print(json.dumps(C.report(a.card, win, a.card in JUDGED, meta), default=str, indent=1))

if __name__ == "__main__":
    main()
