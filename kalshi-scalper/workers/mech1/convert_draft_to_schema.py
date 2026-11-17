#!/usr/bin/env python3
"""Converts build_mech_registry_draft.py's entries to Desk A's schema (mech_schema.py), EXCLUDING ids already hand-read in batches 1 and 2 and the parser artefacts. Every row here is keyword-inferred from a registration paragraph or heading and carries confidence from_title (not hand read) until a human reviews it. Usage: convert_draft_to_schema.py <entries.json> <batch1.json> <batch2.json> <out.json>"""
import json, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mech_schema_desk_a_copy as S
MAP = {"market_family": {"15 min crypto": "15m_crypto", "15 min non-crypto": "15m_noncrypto", "hourly ladder": "hourly_ladder", "combo": "combo", "politics": "politics", "sports": "sports", "weather": "weather"},
       "signal_field": {"price level": "price_level", "price change": "price_change", "spread": "spread", "book depth or imbalance": "book_depth_imbalance", "open interest": "open_interest", "volume": "volume", "funding rate": "funding_rate", "settlement mark": "settlement_mark",
                        "trade-tape flow": "tape_flow", "a spot price elsewhere": "spot_elsewhere", "an event calendar": "event_calendar", "a cross-market residual": "cross_market_residual"},
       "clock": {"fixed time to close": "fixed_time_to_close", "time of day": "time_of_day", "a scheduled event": "scheduled_event", "a print or reopen": "print", "any minute": "any_minute"},
       "entry_type": {"taker": "taker", "maker at the touch": "maker_touch"}, "exit_type": {"hold to settle": "hold_to_settle", "fixed time": "fixed_time", "take profit as a multiple": "take_profit_multiple", "stop": "stop", "the next print": "next_print"},
       "side_rule": {"favourite": "favourite", "cheap side": "cheap", "fade": "fade", "follow": "follow"}}
ARTEFACTS = {"FLAT", "DEV", "OKX", "KXTORNADO", "KXMLBHR", "KXRAIN", "P06", "MECH1S", "MECH2S"}
def market(m, label):
    if m.startswith("perp"):
        t = (label or "").lower()
        return "stock_perp" if re.search(r"stock|equit|aapl|nvda", t) else "index_perp" if re.search(r"index|us 500|tech 100|s&p", t) else "metal_perp" if re.search(r"gold|silver|copper|wti|oil", t) else "crypto_perp"
    return MAP["market_family"].get(m, "other")
def main():
    ents = json.load(open(sys.argv[1]))["entries"]; done = {e["id"] for f in sys.argv[2:4] for e in json.load(open(f))["entries"]}
    out = []
    for e in ents:
        i = e["id"]
        if i in ARTEFACTS or i in done: continue
        if i == "CARRY1": i = "CARRY1_OCT28"
        r = {"id": i, "status": "falsified" if e["status"] == "FALSIFIED" else "idea", "market": market(e["market_family"], e.get("label")), "signal": MAP["signal_field"][e["signal_field"]], "clock": MAP["clock"][e["clock"]], "entry": MAP["entry_type"][e["entry_type"]],
             "exit": MAP["exit_type"][e["exit_type"]], "side": MAP["side_rule"][e["side_rule"]], "source": e["source"] + ("; pre-registration at line %s" % e["prereg_line"] if e.get("prereg_line") else "; no pre-registration paragraph found"), "confidence": "from_title", "kind": "signature",
             "verdict": e["status"], "fields_keyword_matched": e["inferred"]}
        if S.validate_entry(r): raise SystemExit("invalid %s %r" % (i, S.validate_entry(r)))
        out.append(r)
    json.dump({"note": "Desk B keyword-inferred rows, Nov 17 2026, NOT hand read: confidence from_title. fields_keyword_matched lists the fields where a keyword matched (the others are defaults). Review before use.", "entries": out}, open(sys.argv[4], "w"), indent=1)
    print("rows %d (excluded %d done or artefacts); keyword fully matched %d" % (len(out), len(ents) - len(out), sum(1 for r in out if len(r["fields_keyword_matched"]) == 6)))
if __name__ == "__main__": main()
