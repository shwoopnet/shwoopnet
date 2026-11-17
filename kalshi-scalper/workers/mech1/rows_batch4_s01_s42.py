#!/usr/bin/env python3
"""MECH1 batch 4, Desk B, Nov 17 2026: S01 to S42 (the strategy search registered 2026-10-08, README table at line 1119 of the research branch; the mechanism text and entry rule were read, the verdict word is only the last column of the results table) plus POOL1 (Desk A's description). Usage: rows_batch4_s01_s42.py <out.json>"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mech_schema_desk_a_copy as S
from rows_batch1_perps import R
V = dict(zip("S01 S02 S03 S04 S05 S06 S07 S08 S09 S10 S11 S12 S13 S14 S15 S16 S17 S18 S19 S20 S21 S22 S23 S24 S25 S26 S27 S28 S29 S30 S31 S32 S33 S34 S35 S36 S37 S38 S39 S40 S41 S42".split(), "F F F F F F F F F N F N F N F N N N N F F N N N F N F F F N F N N N N F F F F F F F".split()))
V = {k: ("FALSIFIED" if v == "F" else "NOT_ENOUGH_DATA") for k, v in V.items()}
# id: (market, signal, clock, exit, side, one line)
T = {
 "S01": ("15m_crypto", "cross_market_residual", "fixed_time_to_close", "hold_to_settle", "follow", "gold's 4 minute move leads Bitcoin"),
 "S02": ("15m_noncrypto", "cross_market_residual", "fixed_time_to_close", "hold_to_settle", "follow", "Bitcoin's 4 minute move leads gold"),
 "S03": ("15m_crypto", "cross_market_residual", "fixed_time_to_close", "hold_to_settle", "follow", "laggard catch-up when both move the same way"),
 "S04": ("15m_noncrypto", "cross_market_residual", "fixed_time_to_close", "hold_to_settle", "follow", "the last Bitcoin window's outcome carries into gold"),
 "S05": ("15m_crypto", "cross_market_residual", "fixed_time_to_close", "hold_to_settle", "follow", "the last gold window's outcome carries into Bitcoin"),
 "S06": ("15m_crypto", "price_change", "fixed_time_to_close", "hold_to_settle", "follow", "persistence: previous market's outcome"),
 "S07": ("15m_crypto", "price_change", "fixed_time_to_close", "hold_to_settle", "fade", "streak exhaustion after 3 identical outcomes"),
 "S08": ("15m_crypto", "price_change", "fixed_time_to_close", "hold_to_settle", "follow", "regime majority of the previous 12 outcomes"),
 "S09": ("15m_crypto", "price_change", "fixed_time_to_close", "hold_to_settle", "fade", "shock reversal after a move of twice the typical one"),
 "S10": ("15m_crypto", "price_change", "fixed_time_to_close", "hold_to_settle", "cheap", "surprise clustering: lower priced side after an upset"),
 "S11": ("15m_crypto", "price_change", "fixed_time_to_close", "hold_to_settle", "both", "autocorrelation regime: follow if rho positive, fade if negative"),
 "S12": ("15m_crypto", "event_calendar", "scheduled_event", "hold_to_settle", "cheap", "US cash open 13:30 UTC, lower priced side"),
 "S13": ("15m_crypto", "none", "time_of_day", "hold_to_settle", "favourite", "weekend quiet, higher priced side 0.60 to 0.90"),
 "S14": ("15m_noncrypto", "price_change", "reopen", "hold_to_settle", "fade", "gold reopen gap fade"),
 "S15": ("15m_crypto", "price_change", "time_of_day", "hold_to_settle", "follow", "London open breakout of the Asian range"),
 "S16": ("15m_crypto", "spot_elsewhere", "fixed_time_to_close", "hold_to_settle", "follow", "spot acceleration"),
 "S17": ("15m_crypto", "spot_elsewhere", "fixed_time_to_close", "hold_to_settle", "fade", "5 minute spot move over 2 sigma fades"),
 "S18": ("15m_crypto", "spot_elsewhere", "fixed_time_to_close", "hold_to_settle", "fade", "stretch from the hour's mean reverts"),
 "S19": ("15m_crypto", "spot_elsewhere", "fixed_time_to_close", "hold_to_settle", "follow", "compression breakout after a quiet 20 minutes"),
 "S20": ("15m_crypto", "spot_elsewhere", "fixed_time_to_close", "hold_to_settle", "follow", "5, 15 and 60 minute trends agree"),
 "S21": ("15m_crypto", "spot_elsewhere", "fixed_time_to_close", "hold_to_settle", "fade", "3 sigma one minute jump reversal"),
 "S22": ("15m_crypto", "spot_elsewhere", "fixed_time_to_close", "hold_to_settle", "fade", "capitulation bounce after a 1 percent drawdown"),
 "S23": ("15m_crypto", "spot_elsewhere", "fixed_time_to_close", "hold_to_settle", "fade", "run exhaustion after five same sign minutes"),
 "S24": ("15m_crypto", "spot_elsewhere", "fixed_time_to_close", "hold_to_settle", "fade", "prior day extreme rejection"),
 "S25": ("15m_crypto", "spot_elsewhere", "fixed_time_to_close", "hold_to_settle", "both", "minute autocorrelation regime"),
 "S26": ("15m_crypto", "spot_elsewhere", "time_of_day", "hold_to_settle", "fade", "hourly open anchor"),
 "S27": ("15m_crypto", "price_change", "any_minute", "fixed_time", "fade", "spike fade scalp after a 12c one minute mid jump"),
 "S28": ("15m_crypto", "price_change", "fixed_time_to_close", "hold_to_settle", "cheap", "choppy market underdog"),
 "S29": ("15m_crypto", "price_change", "any_minute", "fixed_time", "fade", "wick rejection scalp"),
 "S30": ("15m_crypto", "tape_flow", "fixed_time_to_close", "hold_to_settle", "follow", "last trade price against the mid as a flow proxy"),
 "S31": ("15m_crypto", "price_change", "fixed_time_to_close", "hold_to_settle", "fade", "dwell reversion: a dip in a persistent state"),
 "S32": ("15m_crypto", "book_depth_imbalance", "fixed_time_to_close", "hold_to_settle", "follow", "one sided quote pull"),
 "S33": ("15m_crypto", "price_change", "fixed_time_to_close", "hold_to_settle", "follow", "market mid compression breakout"),
 "S34": ("15m_crypto", "spread", "fixed_time_to_close", "hold_to_settle", "follow", "spread shock"),
 "S35": ("15m_crypto", "volume", "fixed_time_to_close", "hold_to_settle", "follow", "volume surge follow through"),
 "S36": ("15m_crypto", "open_interest", "fixed_time_to_close", "hold_to_settle", "follow", "new money continuation, open interest rising with price"),
 "S37": ("15m_crypto", "volume", "any_minute", "fixed_time", "fade", "thin move reversion scalp"),
 "S38": ("15m_crypto", "volume", "fixed_time_to_close", "hold_to_settle", "cheap", "volume event underdog"),
 "S39": ("15m_crypto", "volume", "fixed_time_to_close", "hold_to_settle", "follow", "opening burst lean from first minute volume"),
 "S40": ("15m_crypto", "price_level", "fixed_time_to_close", "hold_to_settle", "fade", "channel extreme fade (strike highest of 4 hours)"),
 "S41": ("15m_crypto", "price_change", "fixed_time_to_close", "hold_to_settle", "follow", "efficiency ratio trend over 2 hours"),
 "S42": ("15m_crypto", "cross_market_residual", "fixed_time_to_close", "hold_to_settle", "follow", "common factor trend: Bitcoin and gold moved together"),
}
ROWS = [R(k, m, s, c, "taker", x, sd, V[k], "kalshi-scalper/README.md (research branch) line 1119 table, S01 to S42 registered 2026-10-08; " + t, note="Bitcoin and gold 15 minute series, pooled") for k, (m, s, c, x, sd, t) in T.items()]
ROWS.append(R("POOL1", "stock_perp", "price_change", "any_minute", "taker", "fixed_time", "follow", "UNKNOWN", "Desk A's description of ENGPERPS_POOL1_SPEC_NOV16.md (claude/idea-desk-a), relayed by message: a stock perp pool of basket and relative strength rules", conf="from_ledger_row"))
def main():
    bad = {r["id"]: S.validate_entry(r) for r in ROWS if S.validate_entry(r)}
    if bad: raise SystemExit("schema errors: %r" % bad)
    json.dump({"note": "Desk B batch 4 (S01 to S42 and POOL1), Nov 17 2026.", "entries": ROWS}, open(sys.argv[1], "w"), indent=1); print("rows %d valid" % len(ROWS))
if __name__ == "__main__": main()
