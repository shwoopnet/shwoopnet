#!/usr/bin/env python3
"""MECH1 batch 6, Desk B, Nov 17 2026: the VA's absent parents, read against their README text and cards (where my reading differs from the VA's expected signature, `note` says so). Usage: rows_batch6_priority.py <out.json>"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mech_schema_desk_a_copy as S
from rows_batch1_perps import R
RG = "kalshi-scalper/README.md (research branch) "
C, N, H, T, F = "15m_crypto", "15m_noncrypto", "hold_to_settle", "taker", "fixed_time_to_close"
ROWS = [
 R("SCALP1", C, "spot_elsewhere", F, T, "take_profit_multiple", "follow", "UNKNOWN", RG + "line 7135 SCALP1 card: fair probability from spot against the ask, buy the side 8c or more below fair (ask 15c to 70c), 10 to 5 minutes left, target +8c, stop -6c, flat by 120 seconds left", note="Bitcoin and Ethereum; never held to settlement"),
 R("SCALP2", N, "price_change", F, T, "take_profit_multiple", "fade", "FALSIFIED", RG + "line 7135 SCALP2 card: buy the side whose bid fell 15c or more in 2 minutes, ask 15c to 40c, 10 to 5 minutes left, target +8c, stop -6c, flat by 120 seconds left", note="gold is the main market (contract only), Bitcoin and Ethereum reported too; verdict FALSIFIED as stated by Desk A and the VA, not read by me"),
 R("LADFADE", C, "cross_market_residual", F, T, "hold_to_settle", "fade", "FALSIFIED", RG + "line 7816 LADFADE rule: KXBTC15M windows opening :15 and :30, ladder lean 5c or more at the first minute, buy the side the 15 minute book overshot away from when its ask is 3c or more under the ladder's chance, at the next candle's ask (30c to 70c), held", note="README says 'held' (to settlement), so exit is hold_to_settle, not fixed_time as the VA expected"),
 R("TODSEAS1", N, "price_level", "time_of_day", T, H, "cheap", "FALSIFIED", RG + "line 8321 TODSEAS1 registration: clock time slots on FX, metals and energy 15 minute series, cheap side ask 5c to 30c, held", note="the family; slot rows below"),
 R("TODSEAS1_S1", N, "price_level", "scheduled_event", T, H, "cheap", "FALSIFIED", RG + "line 8321 slot S1 HALT_IN 17:00 ET (daily CME halt)", conf="from_ledger_row"),
 R("TODSEAS1_S2", N, "price_level", "reopen", T, H, "cheap", "FALSIFIED", RG + "line 8321 slot S2 HALT_OUT 18:15 ET (daily CME reopen, Monday to Thursday)", conf="from_ledger_row"),
 R("PUB20_P01", N, "price_change", F, T, H, "cheap", "FALSIFIED", RG + "line 8287 PUB20 P01 NR7 compression breakout (Crabel 1990), FX, metals and energy 15 minute", conf="from_ledger_row", note="rule details are in workers/PUB20_REGISTRATION.md, only the name and universe were read"),
 R("PUB20_P02", N, "price_change", F, T, H, "cheap", "FALSIFIED", RG + "line 8287 P02 VOLEXP volatility clustering (Engle 1982)", conf="from_ledger_row"),
 R("PUB20_P03", N, "none", "time_of_day", T, H, "cheap", "FALSIFIED", RG + "line 8287 P03 DOWFRI Friday afternoon", conf="from_ledger_row"),
 R("PUB20_P04", N, "cross_market_residual", F, T, H, "cheap", "FALSIFIED", RG + "line 8287 P04 XSREV cross-sectional reversal", conf="from_ledger_row"),
 R("PUB20_P05", "hourly_ladder", "cross_market_residual", F, T, H, "cheap", "FALSIFIED", RG + "line 8287 P05 NDXLEAD S&P and Nasdaq ladder lead-lag (KXINXU and KXNASDAQ100U)", conf="from_ledger_row"),
 R("PUB20_P06", N, "none", "scheduled_event", T, H, "cheap", "FALSIFIED", RG + "line 8287 P06 FIXES benchmark fix windows (16:00 London, 10:00 ET, silver 12:00 London)", conf="from_ledger_row"),
 R("PUB20_P07", N, "none", "scheduled_event", T, H, "cheap", "FALSIFIED", RG + "line 8287 P07 MONTHEND month end flows", conf="from_ledger_row"),
 R("PUB20_P08", "hourly_ladder", "cross_market_residual", F, T, H, "cheap", "FALSIFIED", RG + "line 8287 P08 SMILE strike ladder interpolation residual (Breeden and Litzenberger 1978)", conf="from_ledger_row"),
 R("PUB20_P09", N, "none", "scheduled_event", T, H, "cheap", "FALSIFIED", RG + "line 8287 P09 SETTLE futures settlement windows", conf="from_ledger_row"),
 R("PUB20_P10", N, "none", "reopen", T, H, "cheap", "FALSIFIED", RG + "line 8287 P10 REOPEN first hour after a halt", conf="from_ledger_row"),
 R("FXUSD", N, "cross_market_residual", "time_of_day", T, H, "follow", "UNKNOWN", RG + "line 8017 FXUSD registration: five FX 15 minute series pooled by USD direction, moments fixed from the calendar before any data (the 4 PM London fix window buys USD up; 07:30 and 08:00 Central and the first window after the Sunday open are count only)"),
 R("XLADDER1", "hourly_ladder", "cross_market_residual", F, T, H, "any", "UNKNOWN", RG + "line 8414 XLADDER1 registration: S&P 500 and Nasdaq 100 daily range brackets against the 4 pm above K ladder; LOCK (3 leg identity, 1c after fees) and CHEAP (single leg, 4c against the sister ladder)", note="registered prediction FALSIFIED; frozen holdout unread; a lock scan in part (declined D_LOCK_PARITY)"),
 R("LEADLAG1", C, "cross_market_residual", "any_minute", T, "fixed_time", "follow", "CLOSED", "kalshi-scalper/workers/LEADLAG1_PROTOCOL.md (research branch): a leader series' yes-mid move of m over L minutes, buy the follower in the same close window aligned with it, sell at the bid k minutes later (19 pairs; Bitcoin, Ethereum and Dogecoin are leaders only)", note="Kalshi series leading other Kalshi series; closed per Desk A"),
 R("PERPCRYPTO1_BASIS", "crypto_perp", "cross_market_residual", "any_minute", T, "fixed_time", "both", "UNKNOWN", "cheapflip-update:kalshi-scalper/workers/history_miner/perpcrypto/PERPCRYPTO1_CARD_NOV16.md BASIS: b = (price - reference_price) / reference_price at each snapshot, |b| at least 5 or 10 bps, converge or follow, hold 1 h or 4 h (8 cells)", note="the VA expected signal settlement_mark and clock time_of_day; the card shows a snapshot rule on any snapshot (clock any_minute) with the basis to the reference index, so I used cross_market_residual"),
]
for r in ROWS:
    if r["id"] == "LEADLAG1": r["status"] = "closed_by_evidence"
def main():
    bad = {r["id"]: S.validate_entry(r) for r in ROWS if S.validate_entry(r)}
    if bad: raise SystemExit("schema errors: %r" % bad)
    json.dump({"note": "Desk B batch 6 (priority list from Desk A), Nov 17 2026. LIQREV not found anywhere I can read.", "entries": ROWS}, open(sys.argv[1], "w"), indent=1); print("rows %d valid" % len(ROWS))
if __name__ == "__main__": main()
