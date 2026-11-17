#!/usr/bin/env python3
"""MECH1 batch 5, Desk B, Nov 17 2026: the idea ledger L1 to L14 (README 'Idea ledger', written 2026-10-07, research branch; the idea, counterparty and prediction columns were read, the status word is the last column). Ids are LEDGER_L1 to LEDGER_L14 because 'L1' is the live strategy. Usage: rows_batch5_ledger.py <out.json>"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mech_schema_desk_a_copy as S
from rows_batch1_perps import R
C, N, H, T, A, F = "15m_crypto", "15m_noncrypto", "hold_to_settle", "taker", "any_minute", "fixed_time_to_close"
X = {  # id: (market, signal, clock, entry, exit, side, verdict, line)
 "LEDGER_L1": (C, "price_level", F, T, H, "cheap", "FALSIFIED", "favourite-longshot bias in Bitcoin and gold 15 minute"),
 "LEDGER_L2": (C, "spot_elsewhere", F, T, "take_profit_multiple", "any", "FALSIFIED", "H2 entered only when the first 30 seconds put spot within reach of the strike"),
 "LEDGER_L3": (C, "price_level", F, T, H, "favourite", "FALSIFIED", "buy the side already far from the strike at 90c or more in the last 2 to 3 minutes (favourite and hold family)"),
 "LEDGER_L4": (C, "spot_elsewhere", A, "maker_touch", H, "any", "NOT_RUNNABLE", "maker entry that rests only when distance says cheap"),
 "LEDGER_L5": (C, "cross_market_residual", A, T, "fixed_time", "any", "NOT_RUNNABLE", "quote staleness: list price lags the single market read by about 2c"),
 "LEDGER_L6": (C, "cross_market_residual", A, T, H, "any", "NOT_RUNNABLE", "Bitcoin and gold on the same window or related ladders priced inconsistently (lock scan, declined D15)"),
 "LEDGER_L7": (C, "spread", F, T, H, "favourite", "OPEN", "volatility regime gate set by spread and liquidity"),
 "LEDGER_L8": (C, "spot_elsewhere", F, T, H, "follow", "PRE-REGISTERED", "averaged strike at the open: the strike is a lagging 60 second average"),
 "LEDGER_L9": (C, "price_level", F, T, H, "any", "PRE-REGISTERED", "final minute averaging: prices should be more extreme near the end"),
 "LEDGER_L10": (C, "event_calendar", "scheduled_event", T, H, "any", "OPEN", "scheduled release windows (CPI, jobs, FOMC) for gold and Bitcoin"),
 "LEDGER_L11": (C, "tape_flow", F, T, H, "follow", "OPEN", "taker flow momentum in the last few minutes (declined D10)"),
 "LEDGER_L12": (C, "book_depth_imbalance", A, T, "fixed_time", "follow", "NOT_RUNNABLE", "book depth imbalance predicts the next move"),
 "LEDGER_L13": (C, "price_change", F, T, H, "any", "OPEN", "volatility surprise: H7 conditioned by volatility regime, a likely duplicate"),
 "LEDGER_L14": (C, "cross_market_residual", A, T, H, "both", "NOT_RUNNABLE", "locked or crossed books: buy both sides when the asks sum below 1 minus fees (declined D15)"),
}
ROWS = [R(k, m, s, c, e, x, sd, ("FALSIFIED" if v == "FALSIFIED" else v), "kalshi-scalper/README.md (research branch) line 670 Idea ledger, row " + k[7:] + ": " + t, note="ledger idea; Bitcoin and gold 15 minute series") for k, (m, s, c, e, x, sd, v, t) in X.items()]
def main():
    bad = {r["id"]: S.validate_entry(r) for r in ROWS if S.validate_entry(r)}
    if bad: raise SystemExit("schema errors: %r" % bad)
    json.dump({"note": "Desk B batch 5 (idea ledger L1 to L14), Nov 17 2026.", "entries": ROWS}, open(sys.argv[1], "w"), indent=1); print("rows %d valid" % len(ROWS))
if __name__ == "__main__": main()
