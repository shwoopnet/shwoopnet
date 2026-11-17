#!/usr/bin/env python3
"""MECH1 batch 1 (perps lane), Desk B, Nov 17 2026: hand-read rows in Desk A's schema (mech_schema.py, copied here as mech_schema_desk_a_copy.py at claude/idea-desk-a 9386981db's version). Each row was read from the test's REGISTRATION text (the README registration section or workers/<ID>_REGISTRATION.md on the research branch), never a result paragraph. `verdict` is the status word of the result heading or RESULT file (FALSIFIED, NOT_ENOUGH_DATA, NOT_YET_FALSIFIED, PASSED_AS_REGISTERED); Desk A's STATUS vocabulary has no NOT_ENOUGH_DATA, so `status` is 'falsified' for FALSIFIED and 'idea' otherwise (to be revised by Desk A).
confidence: hand_read = rule text read; from_ledger_row = only a one-line description read. Usage: rows_batch1_perps.py <out.json>"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mech_schema_desk_a_copy as S
def R(id, market, signal, clock, entry, exit, side, verdict, src, conf="hand_read", note=None):
    status = "falsified" if verdict == "FALSIFIED" else ("retired" if verdict in ("PASSED_AS_REGISTERED", "NOT_YET_FALSIFIED") else "idea")
    e = {"id": id, "status": status, "market": market, "signal": signal, "clock": clock, "entry": entry, "exit": exit, "side": side, "source": src, "confidence": conf, "kind": "signature", "verdict": verdict}
    if note: e["note"] = note
    return e
RG = "kalshi-scalper/README.md (research branch epic-ptolemy-0amjd9) "
WK = "kalshi-scalper/workers/%s_REGISTRATION.md (research branch)"
ROWS = [
 R("PERP1", "crypto_perp", "price_change", "time_of_day", "taker", "stop", "follow", "PASSED_AS_REGISTERED", RG + "line 3934: daily 20 day close breakout, 1.5 ATR stop, next open fill, gold, S&P, BTC, ETH daily bars as proxies", note="passed as registered only on Bitcoin and Ethereum's early years; the owner moved on. Proxies are four markets, filed under crypto_perp"),
 R("PERP2", "crypto_perp", "price_change", "time_of_day", "taker", "stop", "fade", "FALSIFIED", RG + "line 3994: long after three down closes above the 100 day average, 2 ATR stop, exit on a 5 day high or 20 bars"),
 R("PERP3", "metal_perp", "cross_market_residual", "time_of_day", "taker", "stop", "both", "FALSIFIED", RG + "line 3994: gold against silver pairs trade on daily bars"),
 R("FUND1", "crypto_perp", "funding_rate", "print", "taker", "none", "both", "NOT_YET_FALSIFIED", RG + "line 4321: long spot short perpetual, collect funding, always on; owner dropped carry Oct 21", note="holds the carry; side both = long spot and short perp"),
 R("FUNDP1", "metal_perp", "funding_rate", "any_minute", "taker", "fixed_time", "fade", "NOT_ENOUGH_DATA", RG + "line 8918 and workers/FUNDP1_REGISTRATION.md: fade |premium| over 0.10% for 7 to 12 hours on gold, US500, US Tech 100, silver, WTI, copper; funding is a premium proxy"),
 R("CARRY1_PERP", "metal_perp", "funding_rate", "any_minute", "taker", "fixed_time", "both", "NOT_ENOUGH_DATA", RG + "line 8918: long lowest premium and short highest premium", note="id CARRY1 appears twice in the README: this one (Nov 6, perps) and an Oct 28 discovery-lane CARRY1 on dated crypto futures basis (FALSIFIED as deployable now); use CARRY1_OCT28 for that one"),
 R("BASIS1", "metal_perp", "funding_rate", "print", "taker", "next_print", "both", "NOT_ENOUGH_DATA", RG + "line 8918: asks whether funding alone beats the round trip cost"),
 R("FUNDX1", "crypto_perp", "funding_rate", "print", "taker", "fixed_time", "both", "NOT_ENOUGH_DATA", RG + "line 7094 result heading; rule text not read (code src/scalper/fundx1.py)", conf="from_ledger_row"),
 R("SPLAG1", "stock_perp", "spot_elsewhere", "any_minute", "taker", "fixed_time", "follow", "NOT_ENOUGH_DATA", RG + "line 9030 (STOCKPERP1 to 6 registration one liners): perp lags the cash tape", conf="from_ledger_row", note="STOCKPERP1"),
 R("SPAUCT1", "stock_perp", "cross_market_residual", "scheduled_event", "taker", "fixed_time", "fade", "NOT_ENOUGH_DATA", RG + "line 9030: convergence to the 09:30 and 16:00 auction prints", conf="from_ledger_row", note="STOCKPERP2"),
 R("SPLIQ1", "stock_perp", "price_change", "any_minute", "taker", "fixed_time", "fade", "NOT_ENOUGH_DATA", RG + "line 9030: perp only jump with cash flat", conf="from_ledger_row", note="STOCKPERP3"),
 R("SPFUND1", "stock_perp", "funding_rate", "print", "taker", "fixed_time", "any", "NOT_ENOUGH_DATA", RG + "line 9030: after the daily 21:00Z funding stamp", conf="from_ledger_row", note="STOCKPERP4"),
 R("SPW1", "stock_perp", "cross_market_residual", "reopen", "taker", "fixed_time", "any", "NOT_ENOUGH_DATA", RG + "line 9030: Sunday reopening gap to Monday 09:25 ET", conf="from_ledger_row", note="STOCKPERP5"),
 R("SPHALT1", "stock_perp", "price_change", "reopen", "taker", "fixed_time", "any", "NOT_ENOUGH_DATA", RG + "line 9030: cash print gap and resumption", conf="from_ledger_row", note="STOCKPERP6"),
 R("OVN1", "stock_perp", "cross_market_residual", "time_of_day", "taker", "fixed_time", "fade", "NOT_ENOUGH_DATA", WK % "OVN1" + ": premium q to the last cash close, |q| 5 bps or more, fade t0 to t1"),
 R("OVN2", "stock_perp", "price_change", "time_of_day", "taker", "fixed_time", "follow", "NOT_ENOUGH_DATA", WK % "OVN2" + ": follow the overnight perp move d, |d| 5 bps or more"),
 R("OVN3", "stock_perp", "cross_market_residual", "reopen", "taker", "fixed_time", "both", "NOT_ENOUGH_DATA", WK % "OVN3" + ": Friday close premium q_w against the Monday cash open gap; fade and follow companions"),
 R("OVN4", "stock_perp", "spread", "time_of_day", "maker_touch", "none", "any", "FALSIFIED", WK % "OVN4" + ": spread by session bucket (cash, after, night, weekend); a measurement of who earns the wide overnight spread"),
 R("PBOOK1", "stock_perp", "book_depth_imbalance", "any_minute", "taker", "fixed_time", "follow", "FALSIFIED", WK % "PBOOK1" + ": touch size imbalance 0.5 or more, go with the heavy side to the next sample"),
 R("PBOOK2", "stock_perp", "spread", "any_minute", "taker", "fixed_time", "fade", "NOT_ENOUGH_DATA", WK % "PBOOK2" + ": spread 3 times the ticker's median, fade the mid displacement"),
 R("PBOOK3", "stock_perp", "cross_market_residual", "any_minute", "taker", "fixed_time", "fade", "NOT_ENOUGH_DATA", WK % "PBOOK3" + ": |mid / reference - 1| 10 bps and 3 times the ticker's median, fade the gap"),
 R("RO1", "metal_perp", "cross_market_residual", "any_minute", "taker", "fixed_time", "any", "NOT_ENOUGH_DATA", WK % "RO1" + ": gold long after a Tech 100 fall of 0.5 percent or more (cross asset lead), short as control", note="a perp leading another perp: the declined lead-lag pattern territory"),
 R("RV1", "stock_perp", "cross_market_residual", "any_minute", "taker", "fixed_time", "fade", "NOT_ENOUGH_DATA", WK % "RV1" + ": single stock perps against the index perp and each other, mean reversion of the spread"),
 R("RV2", "index_perp", "cross_market_residual", "any_minute", "taker", "fixed_time", "fade", "NOT_ENOUGH_DATA", WK % "RV2" + ": z of ln(Tech 100) - ln(US 500) over 20 snapshots, |z| 1 or more, exit 4 to 8 hours"),
 R("RV3", "stock_perp", "cross_market_residual", "any_minute", "taker", "fixed_time", "fade", "NOT_ENOUGH_DATA", WK % "RV3" + ": premium to reference z over 20 snapshots, |z| 1 or more, single leg, exit 4 to 8 hours"),
 R("CASHSPREAD1", "stock_perp", "spread", "time_of_day", "taker", "none", "any", "NOT_ENOUGH_DATA", WK % "CASHSPREAD1" + ": perp spread by cash session and the first minutes after the open (a measurement)"),
 R("CASHOPEN1", "stock_perp", "cross_market_residual", "scheduled_event", "taker", "fixed_time", "follow", "NOT_ENOUGH_DATA", WK % "CASHOPEN1" + ": cash return since the 09:30 open against the perp return at 09:31 and 09:33"),
 R("CASHCLOSE1", "stock_perp", "price_change", "scheduled_event", "taker", "fixed_time", "follow", "NOT_ENOUGH_DATA", WK % "CASHCLOSE1" + ": day return to 15:39 sets the direction, perp 15:40 to 15:59:30"),
 R("CASHGAP1", "stock_perp", "cross_market_residual", "scheduled_event", "taker", "fixed_time", "fade", "NOT_ENOUGH_DATA", WK % "CASHGAP1" + ": fade the cash open gap of 30 bps or more, 09:30 to 09:40"),
 R("XS1", "stock_perp", "price_change", "time_of_day", "taker", "fixed_time", "follow", "NOT_ENOUGH_DATA", WK % "XS1" + ": once a day at 14:00 UTC rank 24h return, long top 2 short bottom 2, exit 24h later"),
 R("PERPOI1", "hourly_ladder", "open_interest", "fixed_time_to_close", "taker", "hold_to_settle", "cheap", "NOT_ENOUGH_DATA", WK % "PERPOI1" + ": perp open interest surge to a cheap tail trade on the hourly Bitcoin ladder"),
]
def main():
    errs = {r["id"]: S.validate_entry(r) for r in ROWS}; bad = {k: v for k, v in errs.items() if v}
    if bad: raise SystemExit("schema errors: %r" % bad)
    json.dump({"note": "Desk B batch 1 (perps lane), Nov 17 2026. See rows_batch1_perps.py docstring.", "entries": ROWS}, open(sys.argv[1], "w"), indent=1)
    print("rows %d valid against Desk A's schema; verdicts %s" % (len(ROWS), {v: sum(1 for r in ROWS if r["verdict"] == v) for v in set(r["verdict"] for r in ROWS)}))
if __name__ == "__main__": main()
