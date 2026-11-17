#!/usr/bin/env python3
"""MECH1 batch 2 (perps lane, rest), Desk B, Nov 17 2026: hand-read rows from the cards and specs on the other desks' branches (testing-desk PERPSLANE4.spec.json and OPENGAP1_REGISTRATION.md, idea-desk-a PERPSCALP1_HAND_CASE_NOV15.md, cheapflip-update PERPCRYPTO1_CARD_NOV16.md, research branch LL1_REGISTRATION.md). `verdict` UNKNOWN means I did not read a result (and read none on purpose). Usage: rows_batch2_perps.py <out.json>"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mech_schema_desk_a_copy as S
from rows_batch1_perps import R, WK
T = "claude/testing-desk:kalshi-scalper/workers/testing/specs/PERPSLANE4.spec.json rules."
ROWS = [
 R("LL1", "index_perp", "cross_market_residual", "any_minute", "taker", "fixed_time", "follow", "NOT_ENOUGH_DATA", WK % "LL1" + ": BTC and ETH perps' 2 to 8 hour move of 0.5 percent or more leads the US Tech 100 and US 500 perps (trade in the sign to the next sample); control opposite sign", note="a perp leading another perp: the declined lead-lag territory"),
 R("OPENGAP1", "index_perp", "cross_market_residual", "scheduled_event", "taker", "take_profit_multiple", "follow", "UNKNOWN", "claude/testing-desk:kalshi-scalper/workers/testing/OPENGAP1_REGISTRATION.md Rule (card, as amended): at the candle ending 09:31 ET the gap g between the cash open and the perp's 09:25 print beyond 2 x half spread, buy if g above 0, exit when half the gap has closed or by 09:45 ET", note="a forward variant OPENGAP1F is registered beside it"),
 R("PERPSCALP1", "stock_perp", "price_change", "time_of_day", "taker", "take_profit_multiple", "both", "UNKNOWN", "claude/idea-desk-a:kalshi-scalper/workers/PERPSCALP1_HAND_CASE_NOV15.md Rule: 5 minute move of 3 sigma5 or more between 14:35Z and 20:45Z, spread 0.3 percent or less; arm T follows, arm R reverses; target sigma5, stop sigma5, time exit at 600 s", note="two arms in one registration (trend and reversion)"),
 R("PERPSLANE4_A", "stock_perp", "none", "time_of_day", "taker", "fixed_time", "both", "UNKNOWN", T + "A_overnight: long or short from the 16:00 ET candle to the 09:31 ET candle, weekend or weeknight classes (4 rules)"),
 R("PERPSLANE4_A2", "stock_perp", "cross_market_residual", "scheduled_event", "taker", "fixed_time", "both", "UNKNOWN", T + "A2_gap: the OPENGAP gap g at 09:31 ET, 40 or 100 bp threshold, follow or fade, exits T30, T60 or the 16:00 candle (24 rules)", note="same entry rule as OPENGAP1 with a grid"),
 R("PERPSLANE4_B1", "stock_perp", "price_change", "scheduled_event", "taker", "fixed_time", "both", "UNKNOWN", T + "B1_open: the move over N minutes after the 09:31 ET open (N 5, 15, 30), 20 or 40 bp, follow or fade (36 rules)"),
 R("PERPSLANE4_B2", "stock_perp", "price_change", "scheduled_event", "taker", "fixed_time", "both", "UNKNOWN", T + "B2_close: the 15:00 to 15:30 ET move of 20 or 40 bp, follow or fade, exit 16:01 ET or the next open (8 rules)"),
 R("PERPSLANE4_B3", "stock_perp", "none", "scheduled_event", "taker", "fixed_time", "both", "UNKNOWN", T + "B3_closedrift: unconditional long or short from the 15:30 to the 16:01 ET candle (2 rules)"),
 R("PERPSLANE4_C", "stock_perp", "funding_rate", "print", "taker", "fixed_time", "both", "UNKNOWN", T + "C_funding: enter 60, 30 or 15 minutes before the scheduled funding print, exit 15, 30 or 60 minutes after, long, short or the side that receives the print (27 rules)"),
 R("PERPCRYPTO1", "crypto_perp", "funding_rate", "print", "taker", "fixed_time", "fade", "UNKNOWN", "cheapflip-update:kalshi-scalper/workers/history_miner/perpcrypto/PERPCRYPTO1_CARD_NOV16.md (header and data section read; the rules section was not read)", conf="from_ledger_row", note="funding extremes and the perp versus reference basis on six crypto perps; card says funding cannot be tied to a ticker yet"),
]
def main():
    bad = {r["id"]: S.validate_entry(r) for r in ROWS if S.validate_entry(r)}
    if bad: raise SystemExit("schema errors: %r" % bad)
    json.dump({"note": "Desk B batch 2 (perps lane, rest), Nov 17 2026.", "entries": ROWS}, open(sys.argv[1], "w"), indent=1)
    print("rows %d valid" % len(ROWS))
if __name__ == "__main__": main()
