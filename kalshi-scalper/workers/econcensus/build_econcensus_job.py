#!/usr/bin/env python3
"""Builds the ECONCENSUS_LISTS kalshi-pull job (Desk B, Nov 15, 2026, the Head's item 3). Settled-market lists only; no candle.
Held out by a FIXED date constant: no market that closes at or after 2026-10-17T00:00:00Z is asked for (max_close_ts below)."""
import json, os, sys
from datetime import datetime, timezone
HELDOUT_FROM = "2026-10-17T00:00:00Z"                 # closes from here on are never requested
MAX_CLOSE = int(datetime(2026, 10, 17, tzinfo=timezone.utc).timestamp()) - 1
TEMP_MIN_CLOSE = int(datetime(2026, 9, 17, tzinfo=timezone.utc).timestamp())    # hourly temperature: 30 days of development closes
BIG = ["KXCPI", "KXPAYROLLS", "KXJOBLESSCLAIMS", "KXCONTCLAIMS", "KXFED", "KXFEDDECISION", "KXMBAAPPS", "KXRATECUT", "KXRATECUTCOUNT", "TBILL"]
# every US macro release series named in Forensics' Economics rows (workers/forensics/extracts/CENSUS_LISTING_ECONOMICS_SERIES.tsv, 224 rows, a FLOOR),
# plus the ones the ECONLAG job already named; the /series?category=Economics request below catches the rest for a stage 2.
SMALL = ["KXCPICOMBO", "KXCPICOREA", "KXCPICOREGOODSMOM", "KXCPINDEX", "KXECONSTATCPI", "KXECONSTATU3", "KXEMPLOYMENTCOMBO", "PCECORE", "KXPCECORE",
         "KXFEDFUNDSYEAR", "KXFEDHIKE", "KXFEDMEET", "KXHOUSESTART", "KXHOME", "KXUSISMSERV", "KXUSMICHCSP", "KXUSPPIYOY", "KXNGDPQ", "KXLFPRATE", "KXEPOP",
         "KXPSAVERT", "KXREALWAGES", "KXTEMPHELP", "KXUSDEBT", "KXDEFICIT", "KXNFPDELAY", "KXGDP", "KXU3", "KXISMPMI", "KXRETAILSALES", "KXUE", "CPICOREYOY"]
TEMP = ["KXTEMPNYCHS", "KXTEMPMIAH", "KXTEMPLAXHS", "KXTEMPCHIHS"]
def job():
    req = [{"id": "series_economics", "path": "/series", "params": {"category": "Economics", "limit": 20000}}]
    for s in BIG: req.append({"id": "settled_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "max_close_ts": MAX_CLOSE, "limit": 1000}, "max_pages": 4})
    for s in SMALL: req.append({"id": "settled_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "max_close_ts": MAX_CLOSE, "limit": 1000}, "max_pages": 2})
    for s in TEMP: req.append({"id": "settled_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "min_close_ts": TEMP_MIN_CLOSE, "max_close_ts": MAX_CLOSE, "limit": 1000}, "max_pages": 8})
    cap = 1 + 4 * len(BIG) + 2 * len(SMALL) + 8 * len(TEMP)
    return {"job_id": "ECONCENSUS_LISTS", "owner": "DESK_B", "status": "active",
            "registration": "kalshi-scalper/workers/econcensus/ECONCENSUS_NOTE.md",
            "purpose": "Census: settled markets of US macro release series and four hourly temperature series before a fixed cut, plus one Economics series list, to count markets and release dates per series. No candle, no test.",
            "heldout": "FIXED date constant: closes at or after %s are never requested (every markets request carries max_close_ts = %d, one second before). The held-out window is therefore not read by this job; a later test of these families reads only from %s on, under its own registration." % (HELDOUT_FROM, MAX_CLOSE, HELDOUT_FROM),
            "allowed_endpoints": [{"name": "series_list", "method": "GET", "path_pattern": "/series", "params_allowed": ["limit", "category"]},
                                  {"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "min_close_ts", "max_close_ts", "limit", "cursor"]}],
            "series_allowlist": BIG + SMALL + TEMP, "ticker_allowlist": [], "max_requests": cap + 12,
            "notes": "Requests at most %d pages plus 12 for repeats after a 429; at 5 s that is about %d minutes. Hourly temperature: 30 days of closes (2026-09-17 to the cut). A series name that does not exist returns an empty list and costs one request." % (cap, (cap + 12) * 5 // 60 + 1),
            "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
            "requests": req}
if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "ECONCENSUS_LISTS.json"
    json.dump(job(), open(out, "w"), indent=1); print(out, "max_requests", job()["max_requests"], "requests", len(job()["requests"]))
